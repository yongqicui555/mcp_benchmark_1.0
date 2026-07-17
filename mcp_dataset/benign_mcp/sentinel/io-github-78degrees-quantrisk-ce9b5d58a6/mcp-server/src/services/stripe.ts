/**
 * StripeService — manages customers, checkout sessions, subscription status,
 * and webhook processing for QuantRisk billing.
 *
 * Uses the Stripe npm SDK (stripe ^15.0.0) with the Cloudflare Workers
 * runtime adapter (httpClient: Stripe.createFetchHttpClient()).
 *
 * Constructor takes raw environment bindings; no global singletons.
 */

import Stripe from "stripe";

// ---------------------------------------------------------------------------
// Env bindings
// ---------------------------------------------------------------------------

export interface StripeEnv {
  STRIPE_SECRET_KEY: string;
  STRIPE_WEBHOOK_SECRET: string;
}

// ---------------------------------------------------------------------------
// Domain types
// ---------------------------------------------------------------------------

export type UserTier = "free" | "paid";

export interface SubscriptionStatus {
  active: boolean;
  tier: UserTier;
  /** Stripe subscription ID, if one exists. */
  subscriptionId: string | null;
  /** Unix timestamp of the next billing cycle, if known. */
  currentPeriodEnd: number | null;
}

// ---------------------------------------------------------------------------
// Service class
// ---------------------------------------------------------------------------

export class StripeService {
  private readonly stripe: Stripe;
  private readonly webhookSecret: string;

  constructor(env: StripeEnv) {
    // Use Stripe's built-in fetch client — required for Cloudflare Workers
    this.stripe = new Stripe(env.STRIPE_SECRET_KEY, {
      apiVersion: "2024-04-10",
      httpClient: Stripe.createFetchHttpClient(),
    });
    this.webhookSecret = env.STRIPE_WEBHOOK_SECRET;
  }

  // -------------------------------------------------------------------------
  // Customer management
  // -------------------------------------------------------------------------

  /**
   * Create a new Stripe customer record.
   * Returns the Stripe customer ID.
   */
  async createCustomer(email: string): Promise<string> {
    const customer = await this.stripe.customers.create({
      email,
      metadata: { source: "quantrisk-mcp" },
    });
    return customer.id;
  }

  /**
   * Retrieve an existing Stripe customer by ID.
   * Returns null if the customer does not exist or has been deleted.
   */
  async getCustomer(customerId: string): Promise<Stripe.Customer | null> {
    try {
      const customer = await this.stripe.customers.retrieve(customerId);
      if (customer.deleted) return null;
      return customer as Stripe.Customer;
    } catch (err) {
      if (err instanceof Stripe.errors.StripeError && err.statusCode === 404) {
        return null;
      }
      throw err;
    }
  }

  // -------------------------------------------------------------------------
  // Checkout
  // -------------------------------------------------------------------------

  /**
   * Create a Stripe Checkout Session for the $29/month paid plan.
   *
   * The `apiKey` is propagated to the Subscription via `subscription_data.metadata`
   * so the webhook handler can find the right UserState DO to update when the
   * subscription's status changes. It is also stored on the session itself so
   * the success page can read it back.
   *
   * If `customerId` is null, Stripe creates a new customer at checkout.
   *
   * Returns the full Checkout Session (caller uses .url and .id).
   */
  async createCheckoutSession(args: {
    customerId?: string | null;
    priceId: string;
    apiKey: string;
    successUrl: string;
    cancelUrl: string;
    customerEmail?: string | null;
  }): Promise<Stripe.Checkout.Session> {
    const params: Stripe.Checkout.SessionCreateParams = {
      mode:        "subscription",
      line_items:  [{ price: args.priceId, quantity: 1 }],
      success_url: args.successUrl,
      cancel_url:  args.cancelUrl,
      metadata: {
        source:  "quantrisk-mcp",
        api_key: args.apiKey,
      },
      subscription_data: {
        metadata: {
          source:  "quantrisk-mcp",
          api_key: args.apiKey,
        },
      },
    };

    if (args.customerId) {
      params.customer = args.customerId;
    } else if (args.customerEmail) {
      params.customer_email = args.customerEmail;
    }

    const session = await this.stripe.checkout.sessions.create(params);

    if (!session.url) {
      throw new Error("Stripe Checkout Session created but returned no URL");
    }

    return session;
  }

  /**
   * Retrieve a Checkout Session by ID. Used by /checkout/success to read the
   * api_key + customer + subscription off the completed session.
   */
  async retrieveCheckoutSession(
    sessionId: string
  ): Promise<Stripe.Checkout.Session | null> {
    try {
      return await this.stripe.checkout.sessions.retrieve(sessionId, {
        expand: ["subscription", "customer"],
      });
    } catch (err) {
      if (err instanceof Stripe.errors.StripeError && err.statusCode === 404) {
        return null;
      }
      throw err;
    }
  }

  /**
   * Create a Stripe Billing Portal session so the user can manage their
   * subscription (cancel, update payment method, etc.).
   * Returns the portal URL.
   */
  async createPortalSession(
    customerId: string,
    returnUrl = "https://quantrisk.dev/account"
  ): Promise<string> {
    const session = await this.stripe.billingPortal.sessions.create({
      customer: customerId,
      return_url: returnUrl,
    });
    return session.url;
  }

  // -------------------------------------------------------------------------
  // Subscription status
  // -------------------------------------------------------------------------

  /**
   * Look up the subscription status for a customer.
   * Returns `{ active: false, tier: "free" }` if no active subscription is found.
   */
  async getSubscriptionStatus(customerId: string): Promise<SubscriptionStatus> {
    const subscriptions = await this.stripe.subscriptions.list({
      customer: customerId,
      status: "active",
      limit: 1,
    });

    if (subscriptions.data.length === 0) {
      return { active: false, tier: "free", subscriptionId: null, currentPeriodEnd: null };
    }

    const sub = subscriptions.data[0];

    return {
      active: true,
      tier: "paid",
      subscriptionId: sub.id,
      currentPeriodEnd: sub.current_period_end,
    };
  }

  // -------------------------------------------------------------------------
  // Webhook processing
  // -------------------------------------------------------------------------

  /**
   * Verify the webhook signature and parse the event.
   * Returns a typed `Stripe.Event` on success.
   * Throws on invalid signature.
   */
  async verifyWebhook(body: string, signature: string): Promise<Stripe.Event> {
    // Stripe.webhooks.constructEventAsync works in edge/Workers runtimes
    return this.stripe.webhooks.constructEventAsync(
      body,
      signature,
      this.webhookSecret
    );
  }

  /**
   * Process a Stripe webhook event and return the resulting tier change (if any).
   *
   * Handles:
   *   - customer.subscription.created / updated: set tier based on status
   *   - customer.subscription.deleted: downgrade to free
   *   - invoice.payment_failed: optionally handle grace periods
   *
   * Returns null if the event type is not one we act on.
   */
  async handleWebhook(
    body: string,
    signature: string
  ): Promise<WebhookResult | null> {
    const event = await this.verifyWebhook(body, signature);

    switch (event.type) {
      case "customer.subscription.created":
      case "customer.subscription.updated": {
        const sub = event.data.object as Stripe.Subscription;
        const customerId = typeof sub.customer === "string"
          ? sub.customer
          : sub.customer.id;

        const isActive =
          sub.status === "active" || sub.status === "trialing";

        return {
          eventType: event.type,
          customerId,
          subscriptionId: sub.id,
          apiKey: subscriptionApiKey(sub),
          newTier: isActive ? "paid" : "free",
          currentPeriodEnd: sub.current_period_end,
        };
      }

      case "customer.subscription.deleted": {
        const sub = event.data.object as Stripe.Subscription;
        const customerId = typeof sub.customer === "string"
          ? sub.customer
          : sub.customer.id;

        return {
          eventType: event.type,
          customerId,
          subscriptionId: sub.id,
          apiKey: subscriptionApiKey(sub),
          newTier: "free",
          currentPeriodEnd: null,
        };
      }

      case "invoice.payment_failed": {
        const invoice = event.data.object as Stripe.Invoice;
        const customerId = typeof invoice.customer === "string"
          ? invoice.customer
          : invoice.customer?.id ?? null;

        if (!customerId) return null;

        // On payment failure we do NOT immediately downgrade — Stripe will
        // retry and eventually mark the subscription as past_due/cancelled,
        // which fires subscription.updated/deleted. Log only.
        return {
          eventType: event.type,
          customerId,
          subscriptionId:
            typeof invoice.subscription === "string"
              ? invoice.subscription
              : invoice.subscription?.id ?? null,
          apiKey: null,
          newTier: null, // no tier change yet
          currentPeriodEnd: null,
        };
      }

      default:
        return null;
    }
  }
}

/** Pull our `api_key` field out of a subscription's metadata. */
function subscriptionApiKey(sub: Stripe.Subscription): string | null {
  const v = sub.metadata?.api_key;
  return typeof v === "string" && v.length > 0 ? v : null;
}

// ---------------------------------------------------------------------------
// Webhook result type
// ---------------------------------------------------------------------------

export interface WebhookResult {
  eventType: string;
  customerId: string;
  subscriptionId: string | null;
  /**
   * The QuantRisk API key associated with this subscription, taken from
   * `subscription.metadata.api_key`. Null when the subscription was created
   * outside our checkout flow (e.g., manually in the Stripe dashboard) or
   * for events that don't carry a subscription (invoice.payment_failed).
   */
  apiKey: string | null;
  /** null means "no tier change" (e.g. payment_failed — not yet downgraded) */
  newTier: UserTier | null;
  currentPeriodEnd: number | null;
}

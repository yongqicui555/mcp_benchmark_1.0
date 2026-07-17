/**
 * UserState — Cloudflare Durable Object.
 *
 * Single source of truth for per-user auth + billing + usage state.
 *
 * Stored fields:
 *   userId               — API key (used as the DO name) or assigned UUID
 *   apiKey               — the issued API key string (mirror of userId for issued keys);
 *                          null if this DO has never been claimed via checkout
 *   apiKeyIssuedAt       — Unix ms timestamp when the key was issued; null if unissued
 *   email                — user's email address (set on first Stripe interaction)
 *   tier                 — "free" | "paid"
 *   stripeCustomerId     — Stripe customer ID
 *   stripeSubscriptionId — active Stripe subscription ID
 *   callCount            — total calls today
 *   callCountResetAt     — Unix timestamp (ms) when callCount resets (midnight UTC)
 *   minuteCallCount      — calls in the current 60-second window
 *   minuteResetAt        — Unix timestamp (ms) when minuteCallCount resets
 *   invalidated          — if true, the API key has been revoked
 *
 * Internal HTTP routes (called by middleware via DO stub.fetch):
 *   GET  /get               → returns full UserStateData
 *   GET  /validate-key      → 200 { valid: bool, tier, email } (valid only if apiKey set + not invalidated)
 *   POST /increment         → atomically increments counters, checks limits, returns IncrementResponse
 *   POST /set-key           → claims this DO with an apiKey + Stripe identity + tier (called from /checkout/success)
 *   POST /update-tier       → sets tier + stripeSubscriptionId
 *   POST /update-stripe-ids → sets stripeCustomerId + stripeSubscriptionId
 *   POST /invalidate        → marks key as revoked
 *
 * Daily counter reset is scheduled via the DO alarm API (setAlarm at midnight UTC).
 */

import { DurableObject } from "cloudflare:workers";
import type { UserTier } from "../services/stripe.js";
import type { Env } from "../server.js";

// ---------------------------------------------------------------------------
// Stored state shape
// ---------------------------------------------------------------------------

interface UserStateData {
  userId: string | null;
  apiKey: string | null;
  apiKeyIssuedAt: number | null;   // Unix ms
  email: string | null;
  tier: UserTier;
  stripeCustomerId: string | null;
  stripeSubscriptionId: string | null;
  callCount: number;
  callCountResetAt: number;   // Unix ms
  minuteCallCount: number;
  minuteResetAt: number;       // Unix ms
  invalidated: boolean;
}

// ---------------------------------------------------------------------------
// Rate limit config expected by /increment
// ---------------------------------------------------------------------------

interface RateLimitConfig {
  perMinute: number;
  perDay: number;
}

// ---------------------------------------------------------------------------
// Durable Object class
// ---------------------------------------------------------------------------

export class UserState extends DurableObject<Env> {
  private data: UserStateData | null = null;

  // -------------------------------------------------------------------------
  // Durable Object entry point — route internal HTTP requests
  // -------------------------------------------------------------------------

  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);

    switch (url.pathname) {
      case "/get":
        return this.handleGet();

      case "/validate-key":
        return this.handleValidateKey();

      case "/increment":
        return this.handleIncrement(request);

      case "/set-key":
        return this.handleSetKey(request);

      case "/update-tier":
        return this.handleUpdateTier(request);

      case "/update-stripe-ids":
        return this.handleUpdateStripeIds(request);

      case "/invalidate":
        return this.handleInvalidate();

      default:
        return new Response("Not Found", { status: 404 });
    }
  }

  // -------------------------------------------------------------------------
  // Alarm — fires at midnight UTC to reset daily counters
  // -------------------------------------------------------------------------

  async alarm(): Promise<void> {
    const d = await this.getState();
    d.callCount        = 0;
    d.callCountResetAt = nextMidnightUtcMs();
    await this.saveState(d);

    // Schedule the next midnight reset
    await this.ctx.storage.setAlarm(d.callCountResetAt);
  }

  // -------------------------------------------------------------------------
  // Route handlers
  // -------------------------------------------------------------------------

  private async handleGet(): Promise<Response> {
    const d = await this.getState();
    return json(d);
  }

  private async handleValidateKey(): Promise<Response> {
    const d = await this.getState();
    const valid = d.apiKey !== null && !d.invalidated;
    return json<ValidateKeyResponse>({
      valid,
      tier: valid ? d.tier : null,
      email: valid ? d.email : null,
      stripeCustomerId: valid ? d.stripeCustomerId : null,
    });
  }

  private async handleSetKey(request: Request): Promise<Response> {
    const body = await request.json<{
      apiKey: string;
      tier?: UserTier;
      email?: string | null;
      stripeCustomerId?: string | null;
      stripeSubscriptionId?: string | null;
    }>();
    const d = await this.getState();

    // Idempotent: re-claiming the same key with the same identity is a no-op.
    d.apiKey               = body.apiKey;
    d.userId               = body.apiKey;
    d.apiKeyIssuedAt       = d.apiKeyIssuedAt ?? Date.now();
    if (body.tier !== undefined)                 d.tier                 = body.tier;
    if (body.email !== undefined)                d.email                = body.email ?? null;
    if (body.stripeCustomerId !== undefined)     d.stripeCustomerId     = body.stripeCustomerId ?? null;
    if (body.stripeSubscriptionId !== undefined) d.stripeSubscriptionId = body.stripeSubscriptionId ?? null;
    // Re-issuing should clear any prior invalidation flag.
    d.invalidated = false;

    await this.saveState(d);
    return json({ ok: true, apiKeyIssuedAt: d.apiKeyIssuedAt });
  }

  private async handleIncrement(request: Request): Promise<Response> {
    const { limits } = await request.json<{ limits: RateLimitConfig }>();
    const d = await this.getState();
    const now = Date.now();

    // --- Reset minute window if expired ---
    if (now >= d.minuteResetAt) {
      d.minuteCallCount = 0;
      d.minuteResetAt   = now + 60_000;
    }

    // --- Reset daily window if expired ---
    if (now >= d.callCountResetAt) {
      d.callCount        = 0;
      d.callCountResetAt = nextMidnightUtcMs();
      // Ensure alarm is scheduled for next reset
      await this.ctx.storage.setAlarm(d.callCountResetAt);
    }

    // --- Check limits BEFORE incrementing ---
    if (d.minuteCallCount >= limits.perMinute) {
      return json<IncrementResponse>({
        allowed:        false,
        exceededWindow: "minute",
        minuteCount:    d.minuteCallCount,
        dayCount:       d.callCount,
        minuteResetAt:  Math.floor(d.minuteResetAt / 1000),
        dayResetAt:     Math.floor(d.callCountResetAt / 1000),
      });
    }

    if (d.callCount >= limits.perDay) {
      return json<IncrementResponse>({
        allowed:        false,
        exceededWindow: "day",
        minuteCount:    d.minuteCallCount,
        dayCount:       d.callCount,
        minuteResetAt:  Math.floor(d.minuteResetAt / 1000),
        dayResetAt:     Math.floor(d.callCountResetAt / 1000),
      });
    }

    // --- Increment ---
    d.minuteCallCount += 1;
    d.callCount       += 1;
    await this.saveState(d);

    return json<IncrementResponse>({
      allowed:        true,
      exceededWindow: null,
      minuteCount:    d.minuteCallCount,
      dayCount:       d.callCount,
      minuteResetAt:  Math.floor(d.minuteResetAt / 1000),
      dayResetAt:     Math.floor(d.callCountResetAt / 1000),
    });
  }

  private async handleUpdateTier(request: Request): Promise<Response> {
    const body = await request.json<{
      tier: UserTier;
      stripeSubscriptionId?: string | null;
    }>();
    const d = await this.getState();
    d.tier = body.tier;
    if (body.stripeSubscriptionId !== undefined) {
      d.stripeSubscriptionId = body.stripeSubscriptionId ?? null;
    }
    await this.saveState(d);
    return json({ ok: true });
  }

  private async handleUpdateStripeIds(request: Request): Promise<Response> {
    const body = await request.json<{
      stripeCustomerId?: string | null;
      stripeSubscriptionId?: string | null;
      email?: string | null;
    }>();
    const d = await this.getState();
    if (body.stripeCustomerId  !== undefined) d.stripeCustomerId  = body.stripeCustomerId  ?? null;
    if (body.stripeSubscriptionId !== undefined) d.stripeSubscriptionId = body.stripeSubscriptionId ?? null;
    if (body.email !== undefined) d.email = body.email ?? null;
    await this.saveState(d);
    return json({ ok: true });
  }

  private async handleInvalidate(): Promise<Response> {
    const d = await this.getState();
    d.invalidated = true;
    await this.saveState(d);
    return json({ ok: true });
  }

  // -------------------------------------------------------------------------
  // State persistence helpers
  // -------------------------------------------------------------------------

  private async getState(): Promise<UserStateData> {
    if (this.data !== null) return this.data;

    const stored = await this.ctx.storage.get<UserStateData>("state");

    if (stored) {
      this.data = stored;
    } else {
      // First-ever access — initialise with free-tier defaults
      const now = Date.now();
      this.data = {
        userId:              null,
        apiKey:              null,
        apiKeyIssuedAt:      null,
        email:               null,
        tier:                "free",
        stripeCustomerId:    null,
        stripeSubscriptionId: null,
        callCount:           0,
        callCountResetAt:    nextMidnightUtcMs(),
        minuteCallCount:     0,
        minuteResetAt:       now + 60_000,
        invalidated:         false,
      };

      // Schedule the first daily alarm
      await this.ctx.storage.setAlarm(this.data.callCountResetAt);
    }

    return this.data;
  }

  private async saveState(d: UserStateData): Promise<void> {
    this.data = d;
    await this.ctx.storage.put("state", d);
  }
}

// ---------------------------------------------------------------------------
// Response shape from /increment
// ---------------------------------------------------------------------------

interface IncrementResponse {
  allowed: boolean;
  exceededWindow: "minute" | "day" | null;
  minuteCount: number;
  dayCount: number;
  minuteResetAt: number;
  dayResetAt: number;
}

interface ValidateKeyResponse {
  valid: boolean;
  tier: UserTier | null;
  email: string | null;
  stripeCustomerId: string | null;
}

// ---------------------------------------------------------------------------
// Utility helpers
// ---------------------------------------------------------------------------

/** Returns Unix milliseconds for the next midnight UTC. */
function nextMidnightUtcMs(): number {
  const d = new Date();
  d.setUTCHours(24, 0, 0, 0);
  return d.getTime();
}

function json<T>(data: T): Response {
  return new Response(JSON.stringify(data), {
    headers: { "Content-Type": "application/json" },
  });
}

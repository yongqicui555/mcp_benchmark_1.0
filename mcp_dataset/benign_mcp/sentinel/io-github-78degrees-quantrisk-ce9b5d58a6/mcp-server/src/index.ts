/**
 * index.ts — Cloudflare Worker entry point for QuantRisk MCP.
 *
 * Routes:
 *   POST /mcp                → MCP Streamable HTTP transport
 *   POST /stripe-webhook     → Stripe webhook handler (tier upgrades/downgrades)
 *   GET  /upgrade            → HTML page with "Subscribe to Pro" CTA
 *   GET  /checkout           → 303 redirect to Stripe-hosted Checkout
 *   GET  /checkout/success   → claims the API key, displays it to the user
 *   GET  /checkout/cancel    → cancel landing page
 *   GET  /health             → health check
 *   GET  /                   → service summary (JSON)
 *
 * Key flow (subscription → API key → tier upgrade):
 *
 *   1. /checkout generates a fresh `qr_<uuidhex>` API key and embeds it in the
 *      Checkout Session's `subscription_data.metadata.api_key`. Stripe copies
 *      that metadata onto the Subscription, so every subsequent webhook event
 *      for that subscription carries the same key.
 *
 *   2. After payment, Stripe redirects the user to /checkout/success with
 *      `?session_id=cs_…`. The handler reads the api_key + customer +
 *      subscription off the session and calls the UserState DO's POST /set-key
 *      to mark the DO as claimed (tier=paid, key valid).
 *
 *   3. In parallel, Stripe sends `customer.subscription.created` to
 *      /stripe-webhook. The handler reads `metadata.api_key` from the
 *      subscription and routes the tier change to the same DO. The two paths
 *      are idempotent — whoever wins, the end state is the same.
 *
 * Durable Object export:
 *   UserState                — re-exported so Cloudflare can locate the class
 *                              when resolving the USER_STATE binding.
 */

import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { createServer, type Env }        from "./server.js";
import { StripeService }                 from "./services/stripe.js";

// Re-export the UserState Durable Object class.
export { UserState } from "./auth/user-state.js";

// ---------------------------------------------------------------------------
// Worker default export
// ---------------------------------------------------------------------------

export default {
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // ── GET /mcp-test — diagnostic echo ────────────────────────────────
    if (request.method === "GET" && url.pathname === "/mcp-test") {
      return jsonResponse({ test: "route works", timestamp: Date.now() }, 200);
    }

    // ── /mcp — MCP Streamable HTTP transport ───────────────────────────
    if (
      url.pathname === "/mcp" &&
      (request.method === "POST" || request.method === "GET" || request.method === "DELETE")
    ) {
      try {
        return await handleMcp(request, env);
      } catch (outerErr: unknown) {
        const msg = outerErr instanceof Error ? `${outerErr.message}\n${outerErr.stack}` : String(outerErr);
        console.error("[OUTER MCP ERROR]", msg);
        return jsonResponse({ error: "OUTER_MCP_ERROR", message: msg }, 500);
      }
    }

    // ── POST /stripe-webhook ───────────────────────────────────────────
    if (request.method === "POST" && url.pathname === "/stripe-webhook") {
      return handleStripeWebhook(request, env);
    }

    // ── GET /upgrade ───────────────────────────────────────────────────
    if (request.method === "GET" && url.pathname === "/upgrade") {
      return htmlResponse(renderUpgradePage(env), 200);
    }

    // ── GET /checkout ──────────────────────────────────────────────────
    if (request.method === "GET" && url.pathname === "/checkout") {
      return handleCheckout(request, env);
    }

    // ── GET /checkout/success ──────────────────────────────────────────
    if (request.method === "GET" && url.pathname === "/checkout/success") {
      return handleCheckoutSuccess(request, env);
    }

    // ── GET /checkout/cancel ───────────────────────────────────────────
    if (request.method === "GET" && url.pathname === "/checkout/cancel") {
      return htmlResponse(renderCancelPage(), 200);
    }

    // ── GET /health ────────────────────────────────────────────────────
    if (request.method === "GET" && url.pathname === "/health") {
      return jsonResponse({ status: "ok", service: "quantrisk-mcp", version: "1.0.0" }, 200);
    }

    // ── GET / ──────────────────────────────────────────────────────────
    if (request.method === "GET" && url.pathname === "/") {
      return jsonResponse({
        name: "QuantRisk MCP",
        description:
          "Portfolio risk analytics engine for quant traders — VaR, Monte Carlo, optimization, stress testing, and more.",
        version: "1.0.0",
        mcp_endpoint: "/mcp",
        upgrade: "/upgrade",
        docs: "https://quantrisk.dev/docs",
        tools: [
          "analyze_risk", "monte_carlo_simulation", "stress_test",
          "optimize_portfolio", "correlation_matrix", "performance_attribution",
          "sector_exposure", "price_history", "compare_portfolios", "calculate_greeks",
        ],
      }, 200);
    }

    return jsonResponse(
      { error: "NOT_FOUND", message: `No route for ${request.method} ${url.pathname}` },
      404
    );
  },
} satisfies ExportedHandler<Env>;

// ---------------------------------------------------------------------------
// MCP route handler
// ---------------------------------------------------------------------------

async function handleMcp(request: Request, env: Env): Promise<Response> {
  const server = createServer(env, request);

  const transport = new WebStandardStreamableHTTPServerTransport({
    sessionIdGenerator: undefined,
    enableJsonResponse: true,
  });

  await server.connect(transport);

  try {
    return await transport.handleRequest(request);
  } finally {
    transport.close().catch(() => {});
  }
}

// ---------------------------------------------------------------------------
// Checkout — initiate a Stripe Checkout Session
// ---------------------------------------------------------------------------

async function handleCheckout(request: Request, env: Env): Promise<Response> {
  const url       = new URL(request.url);
  const baseUrl   = env.PUBLIC_BASE_URL || `${url.protocol}//${url.host}`;
  const apiKey    = generateApiKey();

  const stripe = new StripeService(env);

  let session;
  try {
    session = await stripe.createCheckoutSession({
      priceId:     env.STRIPE_PRO_PRICE_ID,
      apiKey,
      successUrl:  `${baseUrl}/checkout/success?session_id={CHECKOUT_SESSION_ID}`,
      cancelUrl:   `${baseUrl}/checkout/cancel`,
    });
  } catch (err) {
    const msg = err instanceof Error ? err.message : "Unknown error";
    console.error("[checkout] createCheckoutSession failed:", msg);
    return htmlResponse(
      renderErrorPage(
        "Couldn't start checkout",
        "We had trouble creating a Stripe Checkout Session. Please try again in a moment.",
        msg,
      ),
      502,
    );
  }

  // 303 keeps the browser on a GET when following the redirect.
  return Response.redirect(session.url!, 303);
}

// ---------------------------------------------------------------------------
// Checkout success — claim the API key
// ---------------------------------------------------------------------------

async function handleCheckoutSuccess(request: Request, env: Env): Promise<Response> {
  const sessionId = new URL(request.url).searchParams.get("session_id");

  if (!sessionId || !sessionId.startsWith("cs_")) {
    return htmlResponse(
      renderErrorPage(
        "Missing checkout session",
        "This page must be opened with a `session_id` from Stripe. Start over from /upgrade.",
      ),
      400,
    );
  }

  const stripe  = new StripeService(env);
  const session = await stripe.retrieveCheckoutSession(sessionId);

  if (!session) {
    return htmlResponse(
      renderErrorPage(
        "Checkout session not found",
        "Stripe could not find that session. It may have expired. Please start checkout again.",
      ),
      404,
    );
  }

  const apiKey = (session.metadata?.api_key as string | undefined) ?? null;
  if (!apiKey) {
    return htmlResponse(
      renderErrorPage(
        "Session missing API key",
        "This checkout session has no api_key metadata — it was likely created outside our flow.",
      ),
      400,
    );
  }

  const customerId = typeof session.customer === "string"
    ? session.customer
    : session.customer?.id ?? null;
  const subscriptionId = typeof session.subscription === "string"
    ? session.subscription
    : session.subscription?.id ?? null;
  const customerObj =
    typeof session.customer === "object" && session.customer && !("deleted" in session.customer && session.customer.deleted)
      ? session.customer
      : null;
  const email = session.customer_details?.email
    ?? customerObj?.email
    ?? null;

  // Was the payment actually completed?
  const paid =
    session.payment_status === "paid" ||
    session.payment_status === "no_payment_required" ||
    session.status === "complete";

  // Claim the DO. Idempotent — webhook may have already done this.
  try {
    await setKeyOnDo(env, apiKey, {
      tier:                 paid ? "paid" : "free",
      email,
      stripeCustomerId:     customerId,
      stripeSubscriptionId: subscriptionId,
    });
  } catch (err) {
    console.error("[checkout/success] set-key DO call failed:", err);
    return htmlResponse(
      renderErrorPage(
        "Could not save your API key",
        "Your payment went through, but we hit a snag saving the key. Email hello@quantrisk.dev with your Stripe receipt and we'll sort it out.",
      ),
      500,
    );
  }

  return htmlResponse(renderSuccessPage(apiKey, paid), 200);
}

// ---------------------------------------------------------------------------
// Stripe webhook handler
// ---------------------------------------------------------------------------

async function handleStripeWebhook(request: Request, env: Env): Promise<Response> {
  const signature = request.headers.get("Stripe-Signature");

  if (!signature) {
    return jsonResponse(
      { error: "MISSING_SIGNATURE", message: "Stripe-Signature header is required." },
      400
    );
  }

  let body: string;
  try {
    body = await request.text();
  } catch {
    return jsonResponse({ error: "INVALID_BODY", message: "Could not read request body." }, 400);
  }

  const stripe = new StripeService(env);

  let result: Awaited<ReturnType<StripeService["handleWebhook"]>>;
  try {
    result = await stripe.handleWebhook(body, signature);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Webhook verification failed.";
    return jsonResponse({ error: "WEBHOOK_VERIFICATION_FAILED", message }, 400);
  }

  if (!result) {
    return jsonResponse({ received: true }, 200);
  }

  // We can only update the user's DO when we know which API key the event is
  // for. The api_key arrives via subscription metadata — set by /checkout.
  // Subscriptions created outside our flow (manual dashboard, imports) will
  // come through with apiKey=null. We log and ack so Stripe doesn't retry.
  if (result.newTier !== null && result.apiKey) {
    try {
      await setKeyOnDo(env, result.apiKey, {
        tier:                 result.newTier,
        stripeCustomerId:     result.customerId,
        stripeSubscriptionId: result.subscriptionId,
      });
    } catch (err) {
      console.error("[stripe-webhook] DO update failed:", err);
      // 500 → Stripe retries with exponential backoff.
      return jsonResponse({ error: "INTERNAL_ERROR", message: "Failed to update user tier." }, 500);
    }
  } else if (result.newTier !== null && !result.apiKey) {
    console.warn(
      `[stripe-webhook] ${result.eventType} for sub=${result.subscriptionId} cust=${result.customerId} ` +
      `has no api_key metadata — skipping DO update.`
    );
  }

  return jsonResponse({ received: true }, 200);
}

// ---------------------------------------------------------------------------
// UserState DO calls
// ---------------------------------------------------------------------------

interface SetKeyArgs {
  tier:                 "free" | "paid";
  email?:               string | null;
  stripeCustomerId:     string | null;
  stripeSubscriptionId: string | null;
}

async function setKeyOnDo(env: Env, apiKey: string, args: SetKeyArgs): Promise<void> {
  const stub = env.USER_STATE.get(env.USER_STATE.idFromName(apiKey));
  const response = await stub.fetch(
    new Request("https://user-state/set-key", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body:    JSON.stringify({ apiKey, ...args }),
    })
  );
  if (!response.ok) {
    throw new Error(`UserState DO returned ${response.status} for /set-key`);
  }
}

// ---------------------------------------------------------------------------
// API key generation
// ---------------------------------------------------------------------------

/**
 * Generate a fresh QuantRisk API key.
 *   format: `qr_` + 32 lowercase hex chars (128 bits of randomness from
 *   crypto.randomUUID's random part — RFC 4122 v4 minus the 6 fixed bits,
 *   which still gives 122 bits, well above what we need to avoid collisions).
 */
function generateApiKey(): string {
  return "qr_" + crypto.randomUUID().replace(/-/g, "");
}

// ---------------------------------------------------------------------------
// HTML pages
// ---------------------------------------------------------------------------

const PAGE_HEAD = /* html */ `
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;500;600&family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
<style>
  :root {
    --bg:        #0a0a0f;
    --surface:   #14141c;
    --surface-2: #1c1c28;
    --border:    #2a2a38;
    --text:      #e8e8ee;
    --muted:     #8a8a9a;
    --accent:    #6366f1;
    --accent-2:  #818cf8;
    --success:   #22c55e;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    background: var(--bg);
    color: var(--text);
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    line-height: 1.55;
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    padding: 4rem 1.5rem;
  }
  .wrap { width: 100%; max-width: 640px; }
  h1 {
    font-size: 2.25rem;
    line-height: 1.15;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 0.5rem;
  }
  h1 span { color: var(--accent-2); }
  h2 { font-size: 1.05rem; font-weight: 600; margin: 2rem 0 0.75rem; }
  p { color: var(--muted); margin-bottom: 1rem; }
  .lead { font-size: 1.05rem; color: var(--text); margin-bottom: 2rem; }
  code, pre, .mono { font-family: 'JetBrains Mono', ui-monospace, monospace; }
  .card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 0.75rem;
    padding: 1.75rem;
  }
  .price-row {
    display: flex;
    align-items: baseline;
    gap: 0.5rem;
    margin: 0.75rem 0 1.5rem;
  }
  .price { font-size: 2.5rem; font-weight: 700; letter-spacing: -0.02em; }
  .price-period { color: var(--muted); font-size: 1rem; }
  ul.features {
    list-style: none;
    margin: 1.25rem 0 1.75rem;
    padding: 0;
  }
  ul.features li {
    color: var(--text);
    padding: 0.4rem 0;
    padding-left: 1.5rem;
    position: relative;
    font-size: 0.95rem;
  }
  ul.features li::before {
    content: "✓";
    position: absolute;
    left: 0;
    color: var(--accent-2);
    font-weight: 600;
  }
  .btn {
    display: inline-block;
    background: var(--accent);
    color: white;
    border: none;
    padding: 0.875rem 1.5rem;
    border-radius: 0.5rem;
    font-family: 'Inter', sans-serif;
    font-size: 1rem;
    font-weight: 600;
    text-decoration: none;
    cursor: pointer;
    transition: background 0.15s;
    width: 100%;
    text-align: center;
  }
  .btn:hover { background: var(--accent-2); }
  .btn-ghost {
    background: transparent;
    border: 1px solid var(--border);
    color: var(--text);
  }
  .btn-ghost:hover { background: var(--surface-2); border-color: var(--accent); }
  .key-box {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    padding: 1rem;
    margin: 0.5rem 0 1rem;
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  .key-box code {
    flex: 1;
    word-break: break-all;
    font-size: 0.9rem;
    color: var(--accent-2);
  }
  .copy-btn {
    flex-shrink: 0;
    background: var(--accent);
    color: white;
    border: none;
    padding: 0.5rem 0.875rem;
    border-radius: 0.375rem;
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    font-family: 'Inter', sans-serif;
  }
  .copy-btn.copied { background: var(--success); }
  pre {
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 0.5rem;
    padding: 1rem;
    overflow-x: auto;
    font-size: 0.85rem;
    color: var(--text);
    margin: 0.5rem 0 1rem;
  }
  .badge {
    display: inline-block;
    background: rgba(99, 102, 241, 0.15);
    color: var(--accent-2);
    border: 1px solid rgba(99, 102, 241, 0.4);
    padding: 0.25rem 0.625rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    text-transform: uppercase;
    margin-bottom: 1rem;
  }
  footer {
    margin-top: 3rem;
    padding-top: 2rem;
    border-top: 1px solid var(--border);
    color: var(--muted);
    font-size: 0.85rem;
    width: 100%;
    text-align: center;
  }
  footer a { color: var(--muted); text-decoration: underline; }
  .stack > * + * { margin-top: 0.875rem; }
</style>
`;

function renderUpgradePage(env: Env): string {
  const _price = env.STRIPE_PRO_PRICE_ID; // referenced for clarity; price is the same value rendered below
  void _price;
  return /* html */ `<!doctype html>
<html lang="en">
<head>
  <title>QuantRisk Pro — Upgrade</title>
  ${PAGE_HEAD}
</head>
<body>
  <div class="wrap">
    <span class="badge">QuantRisk Pro</span>
    <h1>Unlock the full <span>quant analytics</span> stack.</h1>
    <p class="lead">Optimisation. Greeks. Custom stress scenarios. Higher Monte Carlo budgets. All inside your AI assistant.</p>

    <div class="card">
      <div class="price-row">
        <span class="price">$29</span>
        <span class="price-period">/ month</span>
      </div>

      <ul class="features">
        <li>500 positions per call (free: 20)</li>
        <li>100,000 Monte Carlo paths (free: 1,000)</li>
        <li>20 tickers, 5 years of price history</li>
        <li>All 10 tools, including <code>optimize_portfolio</code>, <code>compare_portfolios</code>, <code>calculate_greeks</code></li>
        <li>Custom stress scenarios + factor attribution</li>
        <li>5,000 calls/day, 60/min</li>
      </ul>

      <a href="/checkout" class="btn">Subscribe to Pro &rarr;</a>
    </div>

    <h2>What you get back</h2>
    <p>After payment we generate a fresh <code>qr_…</code> API key, link it to your subscription, and show it on the next screen with copy-paste install instructions.</p>

    <h2>Cancel any time</h2>
    <p>One-click cancel from the Stripe billing portal. We don't ask why.</p>

    <footer>
      <p>Already have a key? Use it with the <a href="https://www.npmjs.com/package/@quantrisk/mcp-server">@quantrisk/mcp-server</a> CLI in Claude Desktop or Cursor.</p>
    </footer>
  </div>
</body>
</html>`;
}

function renderSuccessPage(apiKey: string, paid: boolean): string {
  const safeKey = escapeHtml(apiKey);
  const headline = paid
    ? `Welcome to <span>QuantRisk Pro</span>.`
    : `Your account is set up.`;
  const subhead = paid
    ? "Your API key is ready. Add it to your environment and your AI assistant will start hitting paid-tier endpoints immediately."
    : "Your subscription isn't active yet, but your key is reserved. Check Stripe to confirm the payment.";

  return /* html */ `<!doctype html>
<html lang="en">
<head>
  <title>QuantRisk — Your API Key</title>
  ${PAGE_HEAD}
</head>
<body>
  <div class="wrap">
    <span class="badge">${paid ? "Subscription active" : "Pending"}</span>
    <h1>${headline}</h1>
    <p class="lead">${subhead}</p>

    <h2>Your API key</h2>
    <div class="key-box">
      <code id="apiKey">${safeKey}</code>
      <button class="copy-btn" id="copyBtn" onclick="copyKey()">Copy</button>
    </div>
    <p style="font-size: 0.85rem;">Save this somewhere safe. We can show it again from /checkout/success?session_id=… while the session is fresh, but treat it like a password.</p>

    <h2>Install instructions</h2>
    <p>Set the environment variable in your shell:</p>
    <pre>export QUANTRISK_API_KEY=${safeKey}</pre>

    <p>The CLI bridge (<code>@quantrisk/mcp-server</code>) reads <code>QUANTRISK_API_KEY</code> automatically and forwards it as <code>Authorization: Bearer …</code> to every MCP request.</p>

    <h2>Claude Desktop config</h2>
    <p>Add this to <code>~/Library/Application Support/Claude/claude_desktop_config.json</code>:</p>
    <pre>{
  "mcpServers": {
    "quantrisk": {
      "command": "quantrisk-mcp",
      "env": {
        "QUANTRISK_API_KEY": "${safeKey}"
      }
    }
  }
}</pre>

    <p style="margin-top: 2rem;">
      <a href="https://billing.stripe.com/p/login/test_xxxxx" class="btn btn-ghost">Manage subscription</a>
    </p>

    <footer>
      <p>Questions? Email hello@quantrisk.dev with your Stripe receipt — we'll respond same day.</p>
    </footer>
  </div>

  <script>
    function copyKey() {
      const key = document.getElementById('apiKey').textContent;
      const btn = document.getElementById('copyBtn');
      navigator.clipboard.writeText(key).then(() => {
        btn.textContent = 'Copied ✓';
        btn.classList.add('copied');
        setTimeout(() => {
          btn.textContent = 'Copy';
          btn.classList.remove('copied');
        }, 2000);
      }).catch(() => {
        btn.textContent = 'Press ⌘C';
        const range = document.createRange();
        range.selectNode(document.getElementById('apiKey'));
        window.getSelection().removeAllRanges();
        window.getSelection().addRange(range);
      });
    }
  </script>
</body>
</html>`;
}

function renderCancelPage(): string {
  return /* html */ `<!doctype html>
<html lang="en">
<head>
  <title>QuantRisk — Checkout cancelled</title>
  ${PAGE_HEAD}
</head>
<body>
  <div class="wrap">
    <span class="badge">Cancelled</span>
    <h1>No charge made.</h1>
    <p class="lead">You backed out of checkout — totally fine. Whenever you're ready, you can pick up where you left off.</p>

    <div class="stack">
      <a href="/upgrade" class="btn">Try again &rarr;</a>
      <a href="/" class="btn btn-ghost">Back to QuantRisk</a>
    </div>

    <footer>
      <p>Stuck on something? Email hello@quantrisk.dev.</p>
    </footer>
  </div>
</body>
</html>`;
}

function renderErrorPage(title: string, message: string, detail?: string): string {
  const safeTitle  = escapeHtml(title);
  const safeMsg    = escapeHtml(message);
  const detailHtml = detail
    ? `<pre>${escapeHtml(detail)}</pre>`
    : "";
  return /* html */ `<!doctype html>
<html lang="en">
<head>
  <title>QuantRisk — ${safeTitle}</title>
  ${PAGE_HEAD}
</head>
<body>
  <div class="wrap">
    <span class="badge">Error</span>
    <h1>${safeTitle}</h1>
    <p class="lead">${safeMsg}</p>
    ${detailHtml}
    <a href="/upgrade" class="btn">Back to upgrade page</a>
    <footer>
      <p>If this keeps happening, email hello@quantrisk.dev with the URL above.</p>
    </footer>
  </div>
</body>
</html>`;
}

function escapeHtml(s: string): string {
  return s
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

// ---------------------------------------------------------------------------
// Response helpers
// ---------------------------------------------------------------------------

function jsonResponse(body: unknown, status: number): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "Content-Type": "application/json; charset=utf-8" },
  });
}

function htmlResponse(body: string, status: number): Response {
  return new Response(body, {
    status,
    headers: {
      "Content-Type":            "text/html; charset=utf-8",
      // Don't cache: pages are user-specific (success page) or get updated.
      "Cache-Control":           "no-store",
      "X-Content-Type-Options":  "nosniff",
      "Referrer-Policy":         "strict-origin-when-cross-origin",
    },
  });
}

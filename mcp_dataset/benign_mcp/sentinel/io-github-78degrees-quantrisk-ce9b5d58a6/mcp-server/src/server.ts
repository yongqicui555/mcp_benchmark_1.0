/**
 * server.ts — MCP server configuration for QuantRisk.
 *
 * Creates and configures the McpServer instance with all 10 tools.
 * Each tool registration wraps the handler in the shared middleware pipeline:
 *
 *   auth → tier-gate → rate-limit → handler
 *
 * The `Request` object is threaded into `createServer` because the MCP SDK's
 * `RequestHandlerExtra` (passed as the second argument to tool callbacks) does
 * not expose the raw HTTP request. Auth middleware needs the Authorization
 * header and CF-Connecting-IP, so the Request is captured in a closure at
 * server-creation time. Since `createServer` is called once per incoming HTTP
 * request (stateless Workers pattern), this is safe and correct.
 *
 * Usage (from src/index.ts):
 *   const server = createServer(env, request);
 */

import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";

// ── Schemas ──────────────────────────────────────────────────────────────────
import { analyzeRiskSchema }            from "./schemas/analyze-risk.js";
import { monteCarloSchema }             from "./schemas/monte-carlo.js";
import { stressTestSchema }             from "./schemas/stress-test.js";
import { optimizePortfolioBaseSchema }   from "./schemas/optimize-portfolio.js";
import { correlationMatrixSchema }      from "./schemas/correlation-matrix.js";
import { performanceAttributionSchema } from "./schemas/performance-attribution.js";
import { sectorExposureSchema }         from "./schemas/sector-exposure.js";
import { priceHistorySchema }           from "./schemas/price-history.js";
import { comparePortfoliosSchema }      from "./schemas/compare-portfolios.js";
import { calculateGreeksSchema }        from "./schemas/calculate-greeks.js";

// ── Tool handlers ─────────────────────────────────────────────────────────────
import { handleAnalyzeRisk }            from "./tools/analyze-risk.js";
import { handleMonteCarlo }             from "./tools/monte-carlo.js";
import { handleStressTest }             from "./tools/stress-test.js";
import { handleOptimizePortfolio }      from "./tools/optimize-portfolio.js";
import { handleCorrelationMatrix }      from "./tools/correlation-matrix.js";
import { handlePerformanceAttribution } from "./tools/performance-attribution.js";
import { handleSectorExposure }         from "./tools/sector-exposure.js";
import { handlePriceHistory }           from "./tools/price-history.js";
import { handleComparePortfolios }      from "./tools/compare-portfolios.js";
import { handleCalculateGreeks }        from "./tools/calculate-greeks.js";

// ── Middleware ────────────────────────────────────────────────────────────────
import { authenticateRequest, type AuthContext } from "./middleware/auth.js";
import { checkTierAccess }              from "./middleware/tier-gate.js";
import { checkRateLimit }               from "./middleware/rate-limit.js";

// ── Error helpers ─────────────────────────────────────────────────────────────
import { toMcpError }                   from "./utils/errors.js";

// ---------------------------------------------------------------------------
// Env interface — full set of Worker bindings
// ---------------------------------------------------------------------------

/**
 * All Cloudflare Worker environment bindings used by the QuantRisk server.
 * Must match the bindings declared in wrangler.toml.
 */
export interface Env {
  /** Stripe secret key (sk_live_... or sk_test_...). Set as a Worker secret. */
  STRIPE_SECRET_KEY: string;
  /** Stripe webhook signing secret (whsec_...). Set as a Worker secret. */
  STRIPE_WEBHOOK_SECRET: string;
  /** Stripe Price ID for the $29/mo Pro plan. Set in wrangler.toml [vars]. */
  STRIPE_PRO_PRICE_ID: string;
  /** Public base URL for this worker (used to build success/cancel URLs). */
  PUBLIC_BASE_URL: string;
  /** KV namespace for caching price data (TTL 24h) and metadata (TTL 7d). */
  PRICE_CACHE: KVNamespace;
  /** Durable Object namespace for per-user auth, billing, and rate-limit state. */
  USER_STATE: DurableObjectNamespace;
}

// ---------------------------------------------------------------------------
// Shared MCP ToolResult type
// ---------------------------------------------------------------------------

export interface ToolResult {
  [key: string]: unknown;
  content: [{ type: "text"; text: string }];
  isError?: boolean;
}

// ---------------------------------------------------------------------------
// Middleware pipeline helper
// ---------------------------------------------------------------------------

/**
 * Generically-typed handler signature shared across all tool wrappers.
 * Matches the pattern `(input, env, authContext) => Promise<ToolResult>`
 * used by every handler in src/tools/.
 */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
type AnyHandler = (input: any, env: any, authContext: any) => Promise<any>;

/**
 * Wraps a tool handler with the full middleware pipeline.
 *
 * Pipeline: auth → tier-gate → rate-limit → handler
 *
 * The `request` parameter is the original incoming HTTP request, captured
 * once when `createServer` is called. Auth middleware reads the Authorization
 * header and CF-Connecting-IP from it.
 *
 * Any error thrown by middleware or the handler is caught and serialised into
 * a structured MCP error response (Appendix C format) so the MCP transport
 * always sees a valid return value rather than an uncaught exception.
 *
 * @param toolName  Snake-case MCP tool name, e.g. "analyze_risk"
 * @param handler   The tool's async handler function
 * @param env       Cloudflare Worker env bindings (captured in closure)
 * @param request   The raw incoming HTTP request (captured in closure)
 */
function withMiddleware(
  toolName: string,
  handler: AnyHandler,
  env: Env,
  request: Request
) {
  // Return a function matching McpServer.tool()'s ToolCallback signature:
  //   (args: ZodInferred, extra: RequestHandlerExtra) => Promise<ToolResult>
  return async (params: Record<string, unknown>): Promise<ToolResult> => {
    try {
      // 1. Auth — validate API key or assign anonymous free-tier identity
      const authContext = await authenticateRequest(request, env);

      // 2. Tier gate — enforce tool access and numeric input limits
      checkTierAccess(toolName, params, authContext.tier);

      // 3. Rate limit — check + atomically increment per-user counters
      await checkRateLimit(authContext.userId, authContext.tier, env);

      // 4. Execute the tool handler with validated input and resolved context
      return await handler(params, env, authContext);
    } catch (err) {
      return toMcpError(err) as ToolResult;
    }
  };
}

// ---------------------------------------------------------------------------
// Server factory
// ---------------------------------------------------------------------------

/**
 * Create and return a fully-configured QuantRisk McpServer.
 *
 * Called once per Worker request. The `request` is captured in each tool
 * handler's closure so auth middleware can read the Authorization header.
 *
 * All 10 tools are registered here. Tool name → file mapping follows the
 * spec's naming rule: `snake_case_name` → `src/tools/kebab-case-name.ts`.
 */
export function createServer(env: Env, request: Request): McpServer {
  const server = new McpServer({
    name: "quantrisk",
    version: "1.0.0",
  });

  // ── Tool 1: analyze_risk ──────────────────────────────────────────────────
  server.tool(
    "analyze_risk",
    "Calculate core risk metrics for a portfolio — Value at Risk (VaR), Conditional VaR (CVaR), volatility, beta, and max drawdown.",
    analyzeRiskSchema.shape,
    withMiddleware("analyze_risk", handleAnalyzeRisk, env, request)
  );

  // ── Tool 2: monte_carlo_simulation ───────────────────────────────────────
  server.tool(
    "monte_carlo_simulation",
    "Run Monte Carlo simulation on a portfolio to model the distribution of future returns, including percentile outcomes and probability of loss.",
    monteCarloSchema.shape,
    withMiddleware("monte_carlo_simulation", handleMonteCarlo, env, request)
  );

  // ── Tool 3: stress_test ───────────────────────────────────────────────────
  server.tool(
    "stress_test",
    "Stress test a portfolio against historical crisis scenarios (GFC 2008, COVID 2020, etc.) or custom shocks (paid tier).",
    stressTestSchema.shape,
    withMiddleware("stress_test", handleStressTest, env, request)
  );

  // ── Tool 4: optimize_portfolio ────────────────────────────────────────────
  server.tool(
    "optimize_portfolio",
    "Find the optimal portfolio allocation using mean-variance optimization. Supports max Sharpe, min variance, and target return objectives. Paid tier only.",
    optimizePortfolioBaseSchema.shape,
    withMiddleware("optimize_portfolio", handleOptimizePortfolio, env, request)
  );

  // ── Tool 5: correlation_matrix ────────────────────────────────────────────
  server.tool(
    "correlation_matrix",
    "Compute the pairwise correlation matrix for a set of assets. Identifies highly correlated pairs and diversification opportunities.",
    correlationMatrixSchema.shape,
    withMiddleware("correlation_matrix", handleCorrelationMatrix, env, request)
  );

  // ── Tool 6: performance_attribution ──────────────────────────────────────
  server.tool(
    "performance_attribution",
    "Break down portfolio performance into factor exposures, sector allocation, and position contributions. Computes Sharpe, Sortino, Treynor, Calmar, and Information ratios.",
    performanceAttributionSchema.shape,
    withMiddleware("performance_attribution", handlePerformanceAttribution, env, request)
  );

  // ── Tool 7: sector_exposure ───────────────────────────────────────────────
  server.tool(
    "sector_exposure",
    "Break down portfolio exposure by GICS sector, market cap, and asset class. Returns concentration metrics including the Herfindahl-Hirschman Index.",
    sectorExposureSchema.shape,
    withMiddleware("sector_exposure", handleSectorExposure, env, request)
  );

  // ── Tool 8: price_history ─────────────────────────────────────────────────
  server.tool(
    "price_history",
    "Fetch historical OHLCV price data for one or more tickers. Free tier: 1 ticker, 252 days. Paid tier: up to 20 tickers, 1260 days.",
    priceHistorySchema.shape,
    withMiddleware("price_history", handlePriceHistory, env, request)
  );

  // ── Tool 9: compare_portfolios ────────────────────────────────────────────
  server.tool(
    "compare_portfolios",
    "Compare two or more portfolio allocations head-to-head across all key risk and return metrics. Paid tier only.",
    comparePortfoliosSchema.shape,
    withMiddleware("compare_portfolios", handleComparePortfolios, env, request)
  );

  // ── Tool 10: calculate_greeks ─────────────────────────────────────────────
  server.tool(
    "calculate_greeks",
    "Calculate option Greeks (delta, gamma, theta, vega, rho) for individual options or an options portfolio. Uses Black-Scholes for European, binomial for American style. Paid tier only.",
    calculateGreeksSchema.shape,
    withMiddleware("calculate_greeks", handleCalculateGreeks, env, request)
  );

  return server;
}

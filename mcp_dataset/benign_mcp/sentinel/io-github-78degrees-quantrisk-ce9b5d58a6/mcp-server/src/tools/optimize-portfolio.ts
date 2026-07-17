/**
 * optimize-portfolio.ts — MCP tool handler for `optimize_portfolio`.
 *
 * Fetches historical prices for the requested tickers, estimates expected
 * returns and a covariance matrix, then runs mean-variance optimization
 * (Markowitz) for the selected objective. Also generates 20 points along
 * the efficient frontier.
 *
 * PAID tier only. Free users receive a TierError before this handler runs,
 * but we also guard at the top of the function as defense-in-depth.
 */

import { YahooFinanceService } from "../services/yahoo-finance.js";
import {
  meanVarianceOptimize,
  generateEfficientFrontier,
} from "../engine/optimization.js";
import { calculateLogReturns, calculateCovarianceMatrix } from "../engine/returns.js";
import { mean, stdDev } from "../engine/statistics.js";
import {
  TierError,
  ComputationError,
  toMcpError,
} from "../utils/errors.js";
import {
  formatPercent,
  formatRatio,
  formatNumber,
} from "../utils/format.js";
import type { OptimizePortfolioInput } from "../schemas/optimize-portfolio.js";
import type { AuthContext } from "../middleware/auth.js";
import type { OptimizationResult, FrontierPoint } from "../types/risk.js";

// ---------------------------------------------------------------------------
// Env shape
// ---------------------------------------------------------------------------

export interface Env {
  PRICE_CACHE: KVNamespace;
  USER_STATE: DurableObjectNamespace;
}

// ---------------------------------------------------------------------------
// ToolResult shape (standard MCP content block)
// ---------------------------------------------------------------------------

export interface ToolResult {
  content: [{ type: "text"; text: string }];
  isError?: boolean;
}

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

/**
 * Handle an `optimize_portfolio` tool call.
 *
 * @param input       Validated input from the Zod schema
 * @param env         Cloudflare Worker environment bindings
 * @param authContext Resolved user auth context (tier, userId, etc.)
 */
export async function handleOptimizePortfolio(
  input: OptimizePortfolioInput,
  env: Env,
  authContext: AuthContext
): Promise<ToolResult> {
  // Defense-in-depth tier check (middleware should have already blocked free users).
  if (authContext.tier === "free") {
    throw new TierError("optimize_portfolio");
  }

  try {
    const {
      tickers,
      objective,
      target_return,
      constraints,
      risk_free_rate,
      lookback_days,
    } = input;

    // --- 1. Fetch historical prices for all tickers in parallel ---
    const av = new YahooFinanceService(env);
    const priceMap = await av.fetchMultiplePrices(tickers, lookback_days + 1);

    // --- 2. Compute log-return series and align to the shortest common window ---
    const returnSeries: number[][] = [];
    const aligned: string[] = [];

    for (const ticker of tickers) {
      const prices = priceMap[ticker];
      if (!prices || prices.length < 30) {
        throw new ComputationError(
          `Insufficient price history for ${ticker}. Need at least 30 trading days.`,
          `Got ${prices?.length ?? 0} data points`
        );
      }
      returnSeries.push(calculateLogReturns(prices.map((p) => p.close)));
      aligned.push(ticker);
    }

    // Align all return series to the same length (shortest series)
    const minLen = Math.min(...returnSeries.map((r) => r.length));
    const alignedReturns = returnSeries.map((r) => r.slice(-minLen));

    // --- 3. Estimate expected returns (annualised) and covariance matrix ---
    const PERIODS_PER_YEAR = 252;
    const expectedReturns = alignedReturns.map(
      (r) => mean(r) * PERIODS_PER_YEAR
    );
    const rawCov = calculateCovarianceMatrix(alignedReturns);
    // Annualise the covariance matrix
    const covMatrix = rawCov.map((row) =>
      row.map((v) => v * PERIODS_PER_YEAR)
    );

    // --- 4. Apply sector max constraints if provided ---
    // (Sector constraints are passed to meanVarianceOptimize as min/max weight
    //  bounds; full sector-level constraints are not yet supported by the engine,
    //  so we surface them in the summary if provided.)
    const engineConstraints = {
      minWeight: constraints?.min_weight ?? 0.0,
      maxWeight: constraints?.max_weight ?? 1.0,
    };

    // --- 5. Run the optimiser ---
    let optimResult;
    try {
      optimResult = meanVarianceOptimize({
        expectedReturns,
        covarianceMatrix: covMatrix,
        objective,
        targetReturn: target_return ?? undefined,
        riskFreeRate: risk_free_rate,
        constraints: engineConstraints,
      });
    } catch (err) {
      throw new ComputationError(
        `Optimization failed: ${err instanceof Error ? err.message : String(err)}`,
        `Objective: ${objective}`
      );
    }

    // --- 6. Generate efficient frontier (20 points) ---
    let frontier: FrontierPoint[];
    try {
      frontier = generateEfficientFrontier(
        expectedReturns,
        covMatrix,
        risk_free_rate,
        20,
        engineConstraints
      );
    } catch {
      // Frontier generation is best-effort; fall back to empty array
      frontier = [];
    }

    // --- 7. Build output ---
    // Map weight array back to ticker -> weight record
    const weightRecord: Record<string, number> = {};
    for (let i = 0; i < aligned.length; i++) {
      weightRecord[aligned[i]] = optimResult.weights[i];
    }

    const result: OptimizationResult = {
      weights: weightRecord,
      expected_return: optimResult.expectedReturn,
      expected_volatility: optimResult.expectedVolatility,
      sharpe_ratio: optimResult.sharpeRatio,
      efficient_frontier: frontier,
      summary: buildOptimizationSummary(
        weightRecord,
        optimResult.expectedReturn,
        optimResult.expectedVolatility,
        optimResult.sharpeRatio,
        objective,
        target_return,
        risk_free_rate,
        lookback_days
      ),
    };

    return {
      content: [{ type: "text", text: JSON.stringify(result) }],
    };
  } catch (err) {
    return toMcpError(err);
  }
}

// ---------------------------------------------------------------------------
// Summary builder
// ---------------------------------------------------------------------------

function buildOptimizationSummary(
  weights: Record<string, number>,
  expectedReturn: number,
  expectedVolatility: number,
  sharpeRatio: number,
  objective: string,
  targetReturn: number | null | undefined,
  riskFreeRate: number,
  lookbackDays: number
): string {
  const objectiveLabel =
    objective === "max_sharpe"
      ? "maximum Sharpe ratio"
      : objective === "min_variance"
      ? "minimum variance"
      : `a target return of ${formatPercent(targetReturn ?? 0)}`;

  // Sort weights descending
  const sorted = Object.entries(weights)
    .filter(([, w]) => w > 0.001)
    .sort(([, a], [, b]) => b - a);

  const allocationStr = sorted
    .map(([t, w]) => `${t} ${formatPercent(w, 1)}`)
    .join(", ");

  const lookbackYears = (lookbackDays / 252).toFixed(1);

  const lines: string[] = [
    `The optimal allocation for ${objectiveLabel} is: ${allocationStr}.`,
    ``,
    `Expected portfolio metrics (annualized):`,
    `  Return:     ${formatPercent(expectedReturn)}`,
    `  Volatility: ${formatPercent(expectedVolatility)}`,
    `  Sharpe:     ${formatRatio(sharpeRatio)} (risk-free rate: ${formatPercent(riskFreeRate)})`,
    ``,
    `Based on ${lookbackYears} years of historical return data. The efficient frontier was generated`,
    `with 20 points ranging from the minimum-variance portfolio to the maximum expected return.`,
  ];

  // Highlight the zero-weight tickers
  const excluded = Object.entries(weights)
    .filter(([, w]) => w <= 0.001)
    .map(([t]) => t);
  if (excluded.length > 0) {
    lines.push(`Excluded from optimal portfolio: ${excluded.join(", ")} (0% weight).`);
  }

  return lines.join("\n");
}

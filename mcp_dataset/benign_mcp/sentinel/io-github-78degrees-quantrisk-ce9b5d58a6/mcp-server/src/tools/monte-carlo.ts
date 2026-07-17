/**
 * monte-carlo.ts — Tool handler for the `monte_carlo_simulation` MCP tool.
 *
 * Given a portfolio of positions:
 *   1. Fetches historical prices for all tickers
 *   2. Computes portfolio weights and current value
 *   3. Estimates drift (mu) and volatility (sigma) from the portfolio return series
 *   4. Runs GBM or jump-diffusion simulation for the requested number of paths
 *   5. Computes percentile distribution, probability of loss, expected shortfall,
 *      best/worst path, and std dev of terminal values
 *   6. Returns MonteCarloResult with a human-readable summary string
 *
 * Auth and tier gating are handled upstream — this handler receives
 * pre-validated input and an already-resolved AuthContext.
 */

import type { MonteCarloInput } from "../schemas/monte-carlo.js";
import type { AuthContext } from "../middleware/auth.js";
import type { MonteCarloResult, MonteCarloPercentiles } from "../types/risk.js";
import { YahooFinanceService } from "../services/yahoo-finance.js";
import { generateGBMPaths, generateJumpDiffusionPaths } from "../engine/monte-carlo.js";
import { calculateLogReturns, calculatePortfolioReturns } from "../engine/returns.js";
import { mean, stdDev, percentile } from "../engine/statistics.js";
import { formatCurrency, formatPercent, formatNumber } from "../utils/format.js";
import { toMcpError, ComputationError } from "../utils/errors.js";

// ---------------------------------------------------------------------------
// Env bindings required by this tool
// ---------------------------------------------------------------------------

export interface MonteCarloEnv {
  PRICE_CACHE: KVNamespace;
}

// ---------------------------------------------------------------------------
// MCP ToolResult shape
// ---------------------------------------------------------------------------

export interface ToolResult {
  content: [{ type: "text"; text: string }];
  isError?: boolean;
}

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

export async function handleMonteCarlo(
  input: MonteCarloInput,
  env: MonteCarloEnv,
  _authContext: AuthContext
): Promise<ToolResult> {
  try {
    const { positions, num_paths, horizon_days, model, lookback_days, seed } = input;

    // ------------------------------------------------------------------
    // 1. Fetch prices
    // ------------------------------------------------------------------
    const tickers = positions.map((p) => p.ticker.toUpperCase());
    const av = new YahooFinanceService(env);
    const priceMap = await av.fetchMultiplePrices(tickers, lookback_days + 1);

    // ------------------------------------------------------------------
    // 2. Portfolio value and weights
    // ------------------------------------------------------------------
    const positionValues: number[] = positions.map((pos) => {
      const ticker = pos.ticker.toUpperCase();
      const series = priceMap[ticker];
      if (!series || series.length === 0) {
        throw new ComputationError(
          `No price data available for ${ticker}. Cannot run simulation.`
        );
      }
      return series[series.length - 1].close * pos.quantity;
    });

    const portfolioValue = positionValues.reduce((sum, v) => sum + v, 0);

    if (portfolioValue <= 0) {
      throw new ComputationError(
        "Portfolio value must be positive to run Monte Carlo simulation. " +
          "Ensure at least some long positions are present."
      );
    }

    const weights = positionValues.map((v) => v / portfolioValue);

    // ------------------------------------------------------------------
    // 3. Build portfolio return series for parameter estimation
    // ------------------------------------------------------------------
    const returnSeries: number[][] = positions.map((pos) => {
      const ticker = pos.ticker.toUpperCase();
      const prices = priceMap[ticker].map((p) => p.close);
      return calculateLogReturns(prices);
    });

    const minLen = Math.min(...returnSeries.map((r) => r.length));
    const alignedReturns = returnSeries.map((r) => r.slice(r.length - minLen));
    const portfolioReturns = calculatePortfolioReturns(weights, alignedReturns);

    if (portfolioReturns.length < 2) {
      throw new ComputationError(
        "Insufficient price history to estimate simulation parameters. " +
          "Try increasing lookback_days or use a longer-traded asset."
      );
    }

    // ------------------------------------------------------------------
    // 4. Run the simulation
    // ------------------------------------------------------------------
    const simParams = {
      returnSeries: portfolioReturns,
      numPaths: num_paths,
      horizonDays: horizon_days,
      initialValue: portfolioValue,
      seed: seed ?? undefined,
    };

    const simResult =
      model === "jump_diffusion"
        ? generateJumpDiffusionPaths(simParams)
        : generateGBMPaths(simParams);

    const { terminalValues } = simResult;

    // ------------------------------------------------------------------
    // 5. Compute statistics on terminal values
    // ------------------------------------------------------------------
    const pctls: MonteCarloPercentiles = {
      p1:  percentile(terminalValues, 0.01),
      p5:  percentile(terminalValues, 0.05),
      p10: percentile(terminalValues, 0.10),
      p25: percentile(terminalValues, 0.25),
      p50: percentile(terminalValues, 0.50),
      p75: percentile(terminalValues, 0.75),
      p90: percentile(terminalValues, 0.90),
      p95: percentile(terminalValues, 0.95),
      p99: percentile(terminalValues, 0.99),
    };

    const expectedValue = mean(terminalValues);
    const stdDevTerminal = stdDev(terminalValues);
    const bestPath = Math.max(...terminalValues);
    const worstPath = Math.min(...terminalValues);

    // Probability of loss: fraction of paths that end below initial value
    const lossCount = terminalValues.filter((v) => v < portfolioValue).length;
    const probabilityOfLoss = lossCount / terminalValues.length;

    // Expected shortfall in worst 5% of paths
    const threshold5 = percentile(terminalValues, 0.05);
    const tailValues = terminalValues.filter((v) => v <= threshold5);
    const avgTail = tailValues.length > 0 ? mean(tailValues) : pctls.p5;
    const expectedShortfall5 = portfolioValue - avgTail;

    // ------------------------------------------------------------------
    // 6. Build summary and return
    // ------------------------------------------------------------------
    const summary = buildSummary({
      portfolioValue,
      expectedValue,
      probabilityOfLoss,
      expectedShortfall5,
      pctls,
      bestPath,
      worstPath,
      stdDevTerminal,
      horizonDays: horizon_days,
      numPaths: num_paths,
      model,
      mu: simResult.mu,
      sigma: simResult.sigma,
    });

    const result: MonteCarloResult = {
      percentiles: roundPercentiles(pctls),
      expected_value: round(expectedValue, 2),
      probability_of_loss: round(probabilityOfLoss, 4),
      expected_shortfall_5: round(Math.max(0, expectedShortfall5), 2),
      best_path: round(bestPath, 2),
      worst_path: round(worstPath, 2),
      std_dev: round(stdDevTerminal, 2),
      initial_value: round(portfolioValue, 2),
      paths_run: terminalValues.length,
      summary,
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

interface SummaryParams {
  portfolioValue: number;
  expectedValue: number;
  probabilityOfLoss: number;
  expectedShortfall5: number;
  pctls: MonteCarloPercentiles;
  bestPath: number;
  worstPath: number;
  stdDevTerminal: number;
  horizonDays: number;
  numPaths: number;
  model: string;
  mu: number;
  sigma: number;
}

function buildSummary(p: SummaryParams): string {
  const modelLabel = p.model === "jump_diffusion" ? "Jump-Diffusion" : "GBM";

  const horizonLabel =
    p.horizonDays === 1
      ? "1 trading day"
      : p.horizonDays === 21
      ? "1 month (21 days)"
      : p.horizonDays === 63
      ? "1 quarter (63 days)"
      : p.horizonDays === 252
      ? "1 year (252 days)"
      : `${p.horizonDays} trading days`;

  const expectedReturn = (p.expectedValue - p.portfolioValue) / p.portfolioValue;
  const returnSign = expectedReturn >= 0 ? "+" : "";

  const lines: string[] = [
    `${p.numPaths.toLocaleString()} ${modelLabel} paths over ${horizonLabel}. ` +
      `Starting value: ${formatCurrency(p.portfolioValue)}.`,

    `Estimated annual drift: ${formatPercent(p.mu)}, ` +
      `annual volatility: ${formatPercent(p.sigma)}.`,

    `Median outcome: ${formatCurrency(p.pctls.p50)} ` +
      `(${returnSign}${formatPercent(expectedReturn)} expected return).`,

    `Probability of loss: ${formatPercent(p.probabilityOfLoss)}. ` +
      `Average loss in worst 5% of paths: ${formatCurrency(Math.max(0, p.expectedShortfall5))}.`,

    `Range: ${formatCurrency(p.worstPath)} (worst) to ${formatCurrency(p.bestPath)} (best). ` +
      `Std dev of terminal values: ${formatCurrency(p.stdDevTerminal)}.`,

    `5th / 25th / 75th / 95th percentiles: ` +
      `${formatCurrency(p.pctls.p5)} / ${formatCurrency(p.pctls.p25)} / ` +
      `${formatCurrency(p.pctls.p75)} / ${formatCurrency(p.pctls.p95)}.`,
  ];

  return lines.join(" ");
}

// ---------------------------------------------------------------------------
// Utilities
// ---------------------------------------------------------------------------

function round(n: number, decimals: number): number {
  const factor = 10 ** decimals;
  return Math.round(n * factor) / factor;
}

function roundPercentiles(p: MonteCarloPercentiles): MonteCarloPercentiles {
  return {
    p1:  round(p.p1,  2),
    p5:  round(p.p5,  2),
    p10: round(p.p10, 2),
    p25: round(p.p25, 2),
    p50: round(p.p50, 2),
    p75: round(p.p75, 2),
    p90: round(p.p90, 2),
    p95: round(p.p95, 2),
    p99: round(p.p99, 2),
  };
}

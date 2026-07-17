/**
 * performance-attribution.ts — MCP tool handler for `performance_attribution`.
 *
 * Fetches prices for all positions and the benchmark, computes portfolio- and
 * benchmark-level return series, calculates the full set of risk-adjusted
 * performance ratios, breaks down sector exposure, and identifies the top/bottom
 * contributors by P&L contribution.
 *
 * Tier behaviour (authContext.tier drives this, NOT middleware gating):
 *   FREE  — returns basic ratios (Sharpe, Sortino, total_return, annualized_return)
 *            plus sector_exposure. top/bottom contributors are included but
 *            factor-level attribution fields are omitted.
 *   PAID  — returns all fields including Treynor, Calmar, Information Ratio,
 *            tracking error, and full top/bottom contributor detail.
 *
 * Handler signature:
 *   handlePerformanceAttribution(input, env, authContext) -> ToolResult
 */

import type { PerformanceAttributionInput } from "../schemas/performance-attribution.js";
import type { AuthContext } from "../middleware/auth.js";
import type {
  PerformanceAttributionResult,
  PositionContribution,
} from "../types/risk.js";
import type { Position } from "../types/portfolio.js";

import { YahooFinanceService } from "../services/yahoo-finance.js";
import {
  sharpeRatio,
  sortinoRatio,
  treynorRatio,
  calmarRatio,
  informationRatio,
  trackingError,
} from "../engine/ratios.js";
import { calculateSimpleReturns, calculatePortfolioReturns } from "../engine/returns.js";
import { maxDrawdown } from "../engine/drawdown.js";
import { getSectorForTicker } from "../data/sector-map.js";
import { toMcpError } from "../utils/errors.js";
import { formatPercent, formatRatio, formatNumber } from "../utils/format.js";
import { UserTier } from "../types/tiers.js";

// ---------------------------------------------------------------------------
// Env shape required by this tool
// ---------------------------------------------------------------------------

export interface Env {
  PRICE_CACHE: KVNamespace;
  USER_STATE: DurableObjectNamespace;
}

// ---------------------------------------------------------------------------
// ToolResult type
// ---------------------------------------------------------------------------

export interface ToolResult {
  content: [{ type: "text"; text: string }];
  isError?: boolean;
}

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

/**
 * Handle the `performance_attribution` MCP tool.
 *
 * @param input        Validated input (parsed by Zod schema upstream).
 * @param env          Cloudflare Worker environment bindings.
 * @param authContext  Resolved auth/tier context from middleware.
 * @returns            ToolResult with JSON-serialised PerformanceAttributionResult.
 */
export async function handlePerformanceAttribution(
  input: PerformanceAttributionInput,
  env: Env,
  authContext: AuthContext
): Promise<ToolResult> {
  try {
    const { positions, period_days, benchmark, risk_free_rate } = input;
    const isPaid = authContext.tier === UserTier.PAID;

    // ------------------------------------------------------------------
    // 1. Collect unique tickers (positions + benchmark)
    // ------------------------------------------------------------------
    const positionTickers = positions.map((p) => p.ticker);
    const allTickers = [...new Set([...positionTickers, benchmark])];

    // ------------------------------------------------------------------
    // 2. Fetch price data
    // ------------------------------------------------------------------
    const svc = new YahooFinanceService({
      PRICE_CACHE: env.PRICE_CACHE,
    });

    // +1 so differencing gives us `period_days` return observations
    const priceMap = await svc.fetchMultiplePrices(allTickers, period_days + 1);

    // ------------------------------------------------------------------
    // 3. Validate data availability and compute per-ticker return series
    // ------------------------------------------------------------------
    const returnsByTicker: Record<string, number[]> = {};

    for (const ticker of allTickers) {
      const series = priceMap[ticker] ?? [];
      if (series.length < 2) {
        throw new Error(
          `Insufficient price data for ${ticker}: need at least 2 days, got ${series.length}`
        );
      }
      returnsByTicker[ticker] = calculateSimpleReturns(
        series.map((p) => p.close)
      );
    }

    // ------------------------------------------------------------------
    // 4. Align all return series to the shortest available window
    // ------------------------------------------------------------------
    const minLen = Math.min(
      ...allTickers.map((t) => returnsByTicker[t].length)
    );

    const alignedReturns: Record<string, number[]> = {};
    for (const ticker of allTickers) {
      alignedReturns[ticker] = returnsByTicker[ticker].slice(-minLen);
    }

    const benchmarkReturns = alignedReturns[benchmark];

    // ------------------------------------------------------------------
    // 5. Compute current portfolio value and position weights
    // ------------------------------------------------------------------
    // Use the most recent close price to value each position
    const latestPrices: Record<string, number> = {};
    for (const ticker of positionTickers) {
      const series = priceMap[ticker];
      latestPrices[ticker] = series[series.length - 1].close;
    }

    const positionValues: Record<string, number> = {};
    let totalValue = 0;
    for (const pos of positions) {
      const val = pos.quantity * latestPrices[pos.ticker];
      positionValues[pos.ticker] = val;
      totalValue += Math.abs(val); // use absolute value for weight computation
    }

    const weights: Record<string, number> =
      totalValue > 0
        ? Object.fromEntries(
            positions.map((p) => [
              p.ticker,
              Math.abs(positionValues[p.ticker]) / totalValue,
            ])
          )
        : Object.fromEntries(
            positions.map((p) => [p.ticker, 1 / positions.length])
          );

    // ------------------------------------------------------------------
    // 6. Build portfolio return series (value-weighted)
    // ------------------------------------------------------------------
    const weightArray = positions.map((p) => weights[p.ticker]);
    const returnSeriesArray = positions.map(
      (p) => alignedReturns[p.ticker]
    );

    const portfolioReturns = calculatePortfolioReturns(
      weightArray,
      returnSeriesArray
    );

    // ------------------------------------------------------------------
    // 7. Compute performance metrics
    // ------------------------------------------------------------------
    const T = portfolioReturns.length;
    const periodsPerYear = 252;

    // Total return: compound the daily returns
    const totalReturn =
      portfolioReturns.reduce((acc, r) => acc * (1 + r), 1) - 1;

    // Annualised return
    const annualizedReturn =
      Math.pow(1 + totalReturn, periodsPerYear / T) - 1;

    // Sharpe ratio
    const sharpe = sharpeRatio(portfolioReturns, risk_free_rate, periodsPerYear);

    // Sortino ratio
    const sortino = sortinoRatio(
      portfolioReturns,
      risk_free_rate,
      periodsPerYear
    );

    // Paid-only ratios
    const treynor = isPaid
      ? treynorRatio(portfolioReturns, benchmarkReturns, risk_free_rate, periodsPerYear)
      : 0;

    const calmar = isPaid
      ? calmarRatio(portfolioReturns, periodsPerYear)
      : 0;

    const infoRatio = isPaid
      ? informationRatio(portfolioReturns, benchmarkReturns, periodsPerYear)
      : 0;

    const te = isPaid
      ? trackingError(portfolioReturns, benchmarkReturns, periodsPerYear)
      : 0;

    // ------------------------------------------------------------------
    // 8. Sector exposure
    // ------------------------------------------------------------------
    const sectorExposure: Record<string, number> = {};
    for (const pos of positions) {
      const sector = getSectorForTicker(pos.ticker);
      sectorExposure[sector] = (sectorExposure[sector] ?? 0) + weights[pos.ticker];
    }
    // Round to 6dp for clean JSON
    for (const s of Object.keys(sectorExposure)) {
      sectorExposure[s] = round6(sectorExposure[s]);
    }

    // ------------------------------------------------------------------
    // 9. Top / bottom contributors by P&L contribution
    //    contribution = weight * position_return
    // ------------------------------------------------------------------
    const contributors: PositionContribution[] = positions.map((pos) => {
      const posReturns = alignedReturns[pos.ticker];
      const posReturn =
        posReturns.reduce((acc, r) => acc * (1 + r), 1) - 1;
      const contribution = weights[pos.ticker] * posReturn;
      return {
        ticker: pos.ticker,
        weight: round6(weights[pos.ticker]),
        return: round6(posReturn),
        contribution: round6(contribution),
      };
    });

    contributors.sort((a, b) => b.contribution - a.contribution);

    const topContributors = contributors.slice(0, 5);
    const bottomContributors = [...contributors]
      .sort((a, b) => a.contribution - b.contribution)
      .slice(0, 5);

    // ------------------------------------------------------------------
    // 10. Build summary text
    // ------------------------------------------------------------------
    const tierNote = isPaid
      ? ""
      : " (Treynor, Calmar, Information Ratio, and Tracking Error require a paid subscription — upgrade at https://quantrisk.dev/upgrade)";

    const topStr = topContributors
      .map((c) => `${c.ticker} (${formatPercent(c.contribution)})`)
      .join(", ");
    const bottomStr = bottomContributors
      .map((c) => `${c.ticker} (${formatPercent(c.contribution)})`)
      .join(", ");

    const sectorStr = Object.entries(sectorExposure)
      .sort(([, a], [, b]) => b - a)
      .map(([sector, w]) => `${sector}: ${formatPercent(w)}`)
      .join("; ");

    const summary =
      `Performance attribution over ${T} trading days (benchmark: ${benchmark}).\n` +
      `Total return: ${formatPercent(totalReturn)} | Annualised: ${formatPercent(annualizedReturn)} | ` +
      `Sharpe: ${formatRatio(sharpe)} | Sortino: ${formatRatio(sortino)}.` +
      (isPaid
        ? ` Treynor: ${formatRatio(treynor)} | Calmar: ${formatRatio(calmar)} | ` +
          `Information Ratio: ${formatRatio(infoRatio)} | Tracking Error: ${formatPercent(te)}.`
        : tierNote + ".") +
      `\nTop contributors: ${topStr}.` +
      `\nBottom contributors: ${bottomStr}.` +
      `\nSector exposure: ${sectorStr}.`;

    // ------------------------------------------------------------------
    // 11. Assemble result
    // ------------------------------------------------------------------
    const result: PerformanceAttributionResult = {
      total_return: round6(totalReturn),
      annualized_return: round6(annualizedReturn),
      sharpe_ratio: round6(sharpe),
      sortino_ratio: round6(sortino),
      treynor_ratio: isPaid ? round6(treynor) : 0,
      calmar_ratio: isPaid ? round6(calmar) : 0,
      information_ratio: isPaid ? round6(infoRatio) : 0,
      tracking_error: isPaid ? round6(te) : 0,
      sector_exposure: sectorExposure,
      top_contributors: topContributors,
      bottom_contributors: bottomContributors,
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
// Private helpers
// ---------------------------------------------------------------------------

function round6(n: number): number {
  return Math.round(n * 1_000_000) / 1_000_000;
}

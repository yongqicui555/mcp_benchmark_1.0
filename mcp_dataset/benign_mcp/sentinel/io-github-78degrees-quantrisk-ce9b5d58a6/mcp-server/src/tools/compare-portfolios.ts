/**
 * compare-portfolios.ts — MCP tool handler for `compare_portfolios`.
 *
 * Runs a full risk/return analysis on each named portfolio and compares
 * them side-by-side. Identifies the winner by Sharpe ratio and by VaR.
 *
 * PAID tier only. Free users receive a TierError before this handler runs,
 * but we also guard at the top of the function as defense-in-depth.
 */

import { YahooFinanceService } from "../services/yahoo-finance.js";
import { calculateLogReturns, calculatePortfolioReturns } from "../engine/returns.js";
import { historicalVaR, conditionalVaR } from "../engine/var.js";
import {
  sharpeRatio,
  sortinoRatio,
  treynorRatio,
  calmarRatio,
  informationRatio,
  trackingError,
} from "../engine/ratios.js";
import { maxDrawdownFromReturns } from "../engine/drawdown.js";
import { mean, stdDev } from "../engine/statistics.js";
import {
  TierError,
  ComputationError,
  toMcpError,
} from "../utils/errors.js";
import {
  formatCurrency,
  formatPercent,
  formatRatio,
} from "../utils/format.js";
import type { ComparePortfoliosInput } from "../schemas/compare-portfolios.js";
import type { AuthContext } from "../middleware/auth.js";
import type {
  ComparePortfoliosResult,
  PortfolioMetrics,
} from "../types/risk.js";

// ---------------------------------------------------------------------------
// Env / ToolResult (mirrors optimize-portfolio.ts)
// ---------------------------------------------------------------------------

export interface Env {
  PRICE_CACHE: KVNamespace;
  USER_STATE: DurableObjectNamespace;
}

export interface ToolResult {
  content: [{ type: "text"; text: string }];
  isError?: boolean;
}

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

const PERIODS_PER_YEAR = 252;
const BENCHMARK_TICKER = "SPY";

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

/**
 * Handle a `compare_portfolios` tool call.
 *
 * @param input       Validated input from the Zod schema
 * @param env         Cloudflare Worker environment bindings
 * @param authContext Resolved user auth context
 */
export async function handleComparePortfolios(
  input: ComparePortfoliosInput,
  env: Env,
  authContext: AuthContext
): Promise<ToolResult> {
  // Defense-in-depth tier check.
  if (authContext.tier === "free") {
    throw new TierError("compare_portfolios");
  }

  try {
    const { portfolios, period_days, confidence_level } = input;

    // --- 1. Collect all unique tickers across all portfolios ---
    const allTickers = new Set<string>();
    for (const p of portfolios) {
      for (const pos of p.positions) {
        allTickers.add(pos.ticker);
      }
    }
    allTickers.add(BENCHMARK_TICKER);

    // --- 2. Fetch prices for all tickers in parallel ---
    const av = new YahooFinanceService(env);
    const priceMap = await av.fetchMultiplePrices(
      [...allTickers],
      period_days + 1
    );

    // --- 3. Build return series for each ticker ---
    const returnSeriesMap: Record<string, number[]> = {};
    for (const ticker of allTickers) {
      const prices = priceMap[ticker];
      if (!prices || prices.length < 10) {
        throw new ComputationError(
          `Insufficient price history for ${ticker}.`,
          `Got ${prices?.length ?? 0} data points`
        );
      }
      returnSeriesMap[ticker] = calculateLogReturns(
        prices.map((p) => p.close)
      );
    }

    // Align all series to the shortest window
    const minLen = Math.min(
      ...Object.values(returnSeriesMap).map((r) => r.length)
    );
    for (const ticker of allTickers) {
      returnSeriesMap[ticker] = returnSeriesMap[ticker].slice(-minLen);
    }

    const benchmarkReturns = returnSeriesMap[BENCHMARK_TICKER];

    // --- 4. Analyse each portfolio ---
    const comparisonMetrics: PortfolioMetrics[] = [];

    for (const portfolio of portfolios) {
      const { name, positions } = portfolio;

      // Compute current portfolio value and weights
      const latestPrices: Record<string, number> = {};
      for (const pos of positions) {
        const prices = priceMap[pos.ticker];
        if (prices && prices.length > 0) {
          latestPrices[pos.ticker] = prices[prices.length - 1].close;
        }
      }

      const positionValues = positions.map((pos) => {
        const price = latestPrices[pos.ticker] ?? 0;
        return Math.abs(pos.quantity) * price;
      });
      const portfolioValue = positionValues.reduce((s, v) => s + v, 0);

      if (portfolioValue === 0) {
        throw new ComputationError(
          `Portfolio "${name}" has zero market value. Check ticker symbols and quantities.`
        );
      }

      // Portfolio weights (by market value)
      const weights = positionValues.map((v) => v / portfolioValue);

      // Per-ticker return series for this portfolio's tickers
      const tickerReturnSeries = positions.map(
        (pos) => returnSeriesMap[pos.ticker] ?? new Array(minLen).fill(0)
      );

      // Handle sign for short positions
      const signedWeights = positions.map((pos, i) => {
        const sign = pos.quantity < 0 ? -1 : 1;
        return sign * weights[i];
      });

      // Portfolio daily return series
      const portfolioReturns = calculatePortfolioReturns(
        signedWeights,
        tickerReturnSeries
      );

      // VaR and CVaR
      const varResult = historicalVaR(portfolioReturns, confidence_level, 1);
      const cvarResult = conditionalVaR(portfolioReturns, confidence_level, 1);

      const varAbsolute = varResult.var * portfolioValue;
      const varPercent = varResult.var;
      const cvarAbsolute = cvarResult.cvar * portfolioValue;
      const cvarPercent = cvarResult.cvar;

      // Volatility
      const dailyVol = stdDev(portfolioReturns);
      const annualVol = dailyVol * Math.sqrt(PERIODS_PER_YEAR);

      // Beta vs SPY
      const beta = computeBeta(portfolioReturns, benchmarkReturns);

      // Max drawdown
      const ddResult = maxDrawdownFromReturns(portfolioReturns);
      const maxDD = ddResult.maxDrawdown;

      // Performance ratios
      const totalReturn = portfolioReturns.reduce(
        (acc, r) => acc * (1 + r),
        1
      ) - 1;
      const annualizedReturn = mean(portfolioReturns) * PERIODS_PER_YEAR;
      const sharpe = sharpeRatio(portfolioReturns, 0.05, PERIODS_PER_YEAR);
      const sortino = sortinoRatio(portfolioReturns, 0.05, PERIODS_PER_YEAR);
      const treynor = treynorRatio(
        portfolioReturns,
        benchmarkReturns,
        0.05,
        PERIODS_PER_YEAR
      );
      const calmar = calmarRatio(portfolioReturns, PERIODS_PER_YEAR);
      const infoRatio = informationRatio(
        portfolioReturns,
        benchmarkReturns,
        PERIODS_PER_YEAR
      );
      const trackErr = trackingError(
        portfolioReturns,
        benchmarkReturns,
        PERIODS_PER_YEAR
      );

      comparisonMetrics.push({
        name,
        var_absolute: varAbsolute,
        var_percent: varPercent,
        cvar_absolute: cvarAbsolute,
        cvar_percent: cvarPercent,
        annual_volatility: annualVol,
        daily_volatility: dailyVol,
        beta,
        max_drawdown: maxDD,
        portfolio_value: portfolioValue,
        parameters: {
          confidence_level,
          horizon_days: 1,
          method: "historical",
          lookback_days: period_days,
        },
        total_return: totalReturn,
        annualized_return: annualizedReturn,
        sharpe_ratio: sharpe,
        sortino_ratio: sortino,
        treynor_ratio: treynor,
        calmar_ratio: calmar,
        information_ratio: infoRatio,
        tracking_error: trackErr,
        summary: "", // per-portfolio summary is not surfaced individually
      });
    }

    // --- 5. Determine winners ---
    const winnerBySharpe = comparisonMetrics.reduce((best, m) =>
      m.sharpe_ratio > best.sharpe_ratio ? m : best
    ).name;

    const winnerByRisk = comparisonMetrics.reduce((best, m) =>
      m.var_absolute < best.var_absolute ? m : best
    ).name;

    // --- 6. Build result ---
    const result: ComparePortfoliosResult = {
      comparison: comparisonMetrics,
      winner_by_sharpe: winnerBySharpe,
      winner_by_risk: winnerByRisk,
      summary: buildComparisonSummary(
        comparisonMetrics,
        winnerBySharpe,
        winnerByRisk,
        confidence_level,
        period_days
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

function buildComparisonSummary(
  metrics: PortfolioMetrics[],
  winnerBySharpe: string,
  winnerByRisk: string,
  confidenceLevel: number,
  periodDays: number
): string {
  const periodYears = (periodDays / 252).toFixed(1);
  const clPct = formatPercent(confidenceLevel, 0);

  const lines: string[] = [
    `Portfolio Comparison — ${metrics.length} portfolios | ${periodYears}-year lookback | ${clPct} VaR`,
    ``,
  ];

  // Build comparison table header
  const colW = 14;
  const namePad = Math.max(12, ...metrics.map((m) => m.name.length));
  const header = [
    "Portfolio".padEnd(namePad),
    "Value".padStart(colW),
    "Ann. Return".padStart(colW),
    "Volatility".padStart(colW),
    "Sharpe".padStart(colW),
    "Sortino".padStart(colW),
    "Max DD".padStart(colW),
    `VaR(${clPct})`.padStart(colW),
  ].join("  ");

  const separator = "-".repeat(header.length);
  lines.push(header);
  lines.push(separator);

  for (const m of metrics) {
    const row = [
      m.name.padEnd(namePad),
      formatCurrency(m.portfolio_value).padStart(colW),
      formatPercent(m.annualized_return).padStart(colW),
      formatPercent(m.annual_volatility).padStart(colW),
      formatRatio(m.sharpe_ratio).padStart(colW),
      formatRatio(m.sortino_ratio).padStart(colW),
      formatPercent(-m.max_drawdown).padStart(colW),
      formatCurrency(m.var_absolute).padStart(colW),
    ].join("  ");
    lines.push(row);
  }

  lines.push(separator);
  lines.push("");

  // Winners
  if (winnerBySharpe === winnerByRisk) {
    lines.push(
      `Winner: "${winnerBySharpe}" dominates on both risk-adjusted return (highest Sharpe) and absolute risk (lowest VaR).`
    );
  } else {
    lines.push(
      `Best risk-adjusted return: "${winnerBySharpe}" (highest Sharpe ratio).`
    );
    lines.push(`Lowest absolute risk: "${winnerByRisk}" (lowest ${clPct} VaR).`);
  }

  // Sharpe narrative
  const sharpeSorted = [...metrics].sort(
    (a, b) => b.sharpe_ratio - a.sharpe_ratio
  );
  const best = sharpeSorted[0];
  const worst = sharpeSorted[sharpeSorted.length - 1];
  const sharpeGap = best.sharpe_ratio - worst.sharpe_ratio;

  if (sharpeGap > 0.1) {
    lines.push(
      `The Sharpe spread of ${formatRatio(sharpeGap)} between "${best.name}" and "${worst.name}" suggests meaningful differences in risk efficiency.`
    );
  }

  return lines.join("\n");
}

// ---------------------------------------------------------------------------
// Internal: beta calculation
// ---------------------------------------------------------------------------

function computeBeta(portfolio: number[], benchmark: number[]): number {
  const n = Math.min(portfolio.length, benchmark.length);
  if (n < 2) return 1;

  let meanP = 0;
  let meanB = 0;
  for (let i = 0; i < n; i++) {
    meanP += portfolio[i];
    meanB += benchmark[i];
  }
  meanP /= n;
  meanB /= n;

  let cov = 0;
  let varB = 0;
  for (let i = 0; i < n; i++) {
    const dp = portfolio[i] - meanP;
    const db = benchmark[i] - meanB;
    cov += dp * db;
    varB += db * db;
  }

  return varB === 0 ? 0 : cov / varB;
}

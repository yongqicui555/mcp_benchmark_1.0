/**
 * analyze-risk.ts — Tool handler for the `analyze_risk` MCP tool.
 *
 * Workhorse risk tool. Given a portfolio of positions:
 *   1. Fetches daily prices for all tickers + benchmark
 *   2. Calculates portfolio weights from current market values
 *   3. Computes portfolio log returns
 *   4. Runs VaR (historical / parametric / cornish_fisher) and CVaR
 *   5. Computes annualised volatility, beta vs benchmark, max drawdown
 *   6. Returns RiskMetrics with a human-readable summary string
 *
 * Auth and tier gating are handled upstream — this handler receives
 * pre-validated input and an already-resolved AuthContext.
 */

import type { AnalyzeRiskInput } from "../schemas/analyze-risk.js";
import type { AuthContext } from "../middleware/auth.js";
import type { RiskMetrics } from "../types/risk.js";
import { YahooFinanceService } from "../services/yahoo-finance.js";
import {
  historicalVaR,
  parametricVaR,
  cornishFisherVaR,
  conditionalVaR,
} from "../engine/var.js";
import { calculateLogReturns, calculatePortfolioReturns } from "../engine/returns.js";
import { stdDev, covariance } from "../engine/statistics.js";
import { maxDrawdown } from "../engine/drawdown.js";
import { formatCurrency, formatPercent, formatNumber } from "../utils/format.js";
import { toMcpError, ComputationError } from "../utils/errors.js";

// ---------------------------------------------------------------------------
// Env bindings required by this tool
// ---------------------------------------------------------------------------

export interface AnalyzeRiskEnv {
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

export async function handleAnalyzeRisk(
  input: AnalyzeRiskInput,
  env: AnalyzeRiskEnv,
  _authContext: AuthContext
): Promise<ToolResult> {
  try {
    const {
      positions,
      confidence_level,
      horizon_days,
      method,
      benchmark,
      lookback_days,
    } = input;

    // ------------------------------------------------------------------
    // 1. Collect unique tickers (positions + benchmark)
    // ------------------------------------------------------------------
    const positionTickers = positions.map((p) => p.ticker.toUpperCase());
    const benchmarkTicker = benchmark.toUpperCase();
    const allTickers = [...new Set([...positionTickers, benchmarkTicker])];

    // ------------------------------------------------------------------
    // 2. Fetch prices in parallel
    // ------------------------------------------------------------------
    const av = new YahooFinanceService(env);
    const priceMap = await av.fetchMultiplePrices(allTickers, lookback_days + 1);

    // ------------------------------------------------------------------
    // 3. Determine current prices and portfolio weights
    // ------------------------------------------------------------------
    const positionValues: number[] = positions.map((pos) => {
      const ticker = pos.ticker.toUpperCase();
      const series = priceMap[ticker];
      if (!series || series.length === 0) {
        throw new ComputationError(
          `No price data available for ${ticker}. Cannot compute portfolio value.`
        );
      }
      const latestPrice = series[series.length - 1].close;
      return latestPrice * pos.quantity; // negative for short positions
    });

    // Portfolio value uses absolute values of position values (gross exposure)
    // but retains sign for weighted return calculations
    const portfolioValue = positionValues.reduce((sum, v) => sum + v, 0);

    if (portfolioValue === 0) {
      throw new ComputationError("Portfolio value is zero. Check quantities and prices.");
    }

    const weights = positionValues.map((v) => v / portfolioValue);

    // ------------------------------------------------------------------
    // 4. Build return series for each position and the benchmark
    // ------------------------------------------------------------------
    const returnSeries: number[][] = positions.map((pos) => {
      const ticker = pos.ticker.toUpperCase();
      const prices = priceMap[ticker].map((p) => p.close);
      return calculateLogReturns(prices);
    });

    // Align return series lengths (in case different tickers have different data depth)
    const minLen = Math.min(...returnSeries.map((r) => r.length));
    const alignedReturns = returnSeries.map((r) => r.slice(r.length - minLen));

    // ------------------------------------------------------------------
    // 5. Portfolio returns = weighted sum of individual log returns
    // ------------------------------------------------------------------
    const portfolioReturns = calculatePortfolioReturns(weights, alignedReturns);

    // ------------------------------------------------------------------
    // 6. VaR — dispatch to the requested method
    // ------------------------------------------------------------------
    let varAbsolute: number;
    let cvarAbsolute: number;

    const absPortfolioValue = Math.abs(portfolioValue);

    if (method === "historical") {
      const cvarResult = conditionalVaR(portfolioReturns, confidence_level, horizon_days);
      varAbsolute = cvarResult.var * absPortfolioValue;
      cvarAbsolute = cvarResult.cvar * absPortfolioValue;
    } else if (method === "parametric") {
      const varResult = parametricVaR(portfolioReturns, confidence_level, horizon_days);
      const cvarResult = conditionalVaR(portfolioReturns, confidence_level, horizon_days);
      varAbsolute = varResult.var * absPortfolioValue;
      cvarAbsolute = cvarResult.cvar * absPortfolioValue;
    } else {
      // cornish_fisher
      const varResult = cornishFisherVaR(portfolioReturns, confidence_level, horizon_days);
      const cvarResult = conditionalVaR(portfolioReturns, confidence_level, horizon_days);
      varAbsolute = varResult.var * absPortfolioValue;
      cvarAbsolute = cvarResult.cvar * absPortfolioValue;
    }

    const varPercent = varAbsolute / absPortfolioValue;
    const cvarPercent = cvarAbsolute / absPortfolioValue;

    // ------------------------------------------------------------------
    // 7. Volatility
    // ------------------------------------------------------------------
    const dailyVol = stdDev(portfolioReturns);
    const annualVol = dailyVol * Math.sqrt(252);

    // ------------------------------------------------------------------
    // 8. Beta vs benchmark
    // ------------------------------------------------------------------
    let beta = 1.0;
    const benchmarkSeries = priceMap[benchmarkTicker];
    if (benchmarkSeries && benchmarkSeries.length >= 2) {
      const benchmarkPrices = benchmarkSeries.map((p) => p.close);
      const benchmarkReturns = calculateLogReturns(benchmarkPrices);
      const alignLen = Math.min(portfolioReturns.length, benchmarkReturns.length);
      const portSlice = portfolioReturns.slice(portfolioReturns.length - alignLen);
      const benchSlice = benchmarkReturns.slice(benchmarkReturns.length - alignLen);

      const benchVar = stdDev(benchSlice) ** 2; // variance of benchmark
      if (benchVar > 0) {
        const covPB = covariance(portSlice, benchSlice);
        beta = covPB / benchVar;
      }
    }

    // ------------------------------------------------------------------
    // 9. Max drawdown — computed on cumulative portfolio equity curve
    // ------------------------------------------------------------------
    // Build equity curve from portfolio returns starting at portfolio value
    const equityCurve: number[] = [absPortfolioValue];
    for (const r of portfolioReturns) {
      equityCurve.push(equityCurve[equityCurve.length - 1] * Math.exp(r));
    }
    const ddResult = maxDrawdown(equityCurve);
    const maxDD = ddResult.maxDrawdown;

    // ------------------------------------------------------------------
    // 10. Assemble output
    // ------------------------------------------------------------------
    const horizonLabel =
      horizon_days === 1
        ? "1-day"
        : horizon_days === 21
        ? "1-month"
        : `${horizon_days}-day`;

    const summary = buildSummary({
      portfolioValue,
      varAbsolute,
      varPercent,
      cvarAbsolute,
      cvarPercent,
      annualVol,
      dailyVol,
      beta,
      maxDD,
      confidenceLevel: confidence_level,
      horizonLabel,
      method,
      positionCount: positions.length,
      benchmark: benchmarkTicker,
    });

    const result: RiskMetrics = {
      var_absolute: round(varAbsolute, 2),
      var_percent: round(varPercent, 6),
      cvar_absolute: round(cvarAbsolute, 2),
      cvar_percent: round(cvarPercent, 6),
      annual_volatility: round(annualVol, 6),
      daily_volatility: round(dailyVol, 6),
      beta: round(beta, 4),
      max_drawdown: round(maxDD, 6),
      portfolio_value: round(portfolioValue, 2),
      parameters: {
        confidence_level,
        horizon_days,
        method,
        lookback_days,
      },
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
  varAbsolute: number;
  varPercent: number;
  cvarAbsolute: number;
  cvarPercent: number;
  annualVol: number;
  dailyVol: number;
  beta: number;
  maxDD: number;
  confidenceLevel: number;
  horizonLabel: string;
  method: string;
  positionCount: number;
  benchmark: string;
}

function buildSummary(p: SummaryParams): string {
  const methodLabel: Record<string, string> = {
    historical: "historical simulation",
    parametric: "parametric (normal)",
    cornish_fisher: "Cornish-Fisher (skew/kurtosis-adjusted)",
  };

  const lines: string[] = [
    `Portfolio of ${p.positionCount} position${p.positionCount !== 1 ? "s" : ""}, ` +
      `current value ${formatCurrency(p.portfolioValue)}.`,

    `${Math.round(p.confidenceLevel * 100)}% ${p.horizonLabel} Value at Risk ` +
      `(${methodLabel[p.method] ?? p.method}): ` +
      `${formatCurrency(p.varAbsolute)} (${formatPercent(p.varPercent)}).`,

    `Conditional VaR (Expected Shortfall): ` +
      `${formatCurrency(p.cvarAbsolute)} (${formatPercent(p.cvarPercent)}).`,

    `Annualised volatility: ${formatPercent(p.annualVol)} ` +
      `(daily: ${formatPercent(p.dailyVol)}).`,

    `Beta vs ${p.benchmark}: ${formatNumber(p.beta, 2)}.`,

    `Maximum drawdown over lookback: -${formatPercent(p.maxDD)}.`,
  ];

  return lines.join(" ");
}

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

function round(n: number, decimals: number): number {
  const factor = 10 ** decimals;
  return Math.round(n * factor) / factor;
}

/**
 * ratios.ts — Performance and risk-adjusted return ratios.
 * All functions are pure and operate on return arrays.
 * Zero external dependencies beyond the engine's statistics module.
 */

import { mean, stdDev } from './statistics.js';

/**
 * Sharpe Ratio — excess return per unit of total risk.
 * Sharpe = (annualized portfolio return - risk-free rate) / annualized std dev
 *
 * @param returns - Array of periodic (e.g. daily) portfolio returns
 * @param riskFreeRate - Annualized risk-free rate (e.g. 0.05 for 5%)
 * @param periodsPerYear - Number of return periods per year. Default 252 (daily).
 * @returns The annualized Sharpe ratio
 */
export function sharpeRatio(
  returns: number[],
  riskFreeRate: number = 0.05,
  periodsPerYear: number = 252
): number {
  if (returns.length < 2) throw new Error('Need at least 2 return observations');
  const annReturn = mean(returns) * periodsPerYear;
  const annVol = stdDev(returns) * Math.sqrt(periodsPerYear);
  if (annVol === 0) return 0;
  return (annReturn - riskFreeRate) / annVol;
}

/**
 * Sortino Ratio — excess return per unit of downside risk.
 * Uses downside deviation (std dev of negative returns only) instead of total std dev.
 * More appropriate when return distributions are asymmetric.
 *
 * @param returns - Array of periodic portfolio returns
 * @param riskFreeRate - Annualized risk-free rate. Default 0.05.
 * @param periodsPerYear - Periods per year. Default 252.
 * @param mar - Minimum acceptable return per period. Default 0 (zero threshold).
 * @returns The annualized Sortino ratio
 */
export function sortinoRatio(
  returns: number[],
  riskFreeRate: number = 0.05,
  periodsPerYear: number = 252,
  mar: number = 0
): number {
  if (returns.length < 2) throw new Error('Need at least 2 return observations');
  const annReturn = mean(returns) * periodsPerYear;

  // Downside deviation: sqrt of mean of squared negative deviations from MAR
  let sumSqDown = 0;
  let count = 0;
  for (const r of returns) {
    const diff = r - mar;
    if (diff < 0) {
      sumSqDown += diff * diff;
    }
    count++;
  }

  const downsideVar = sumSqDown / count; // population-style for downside
  const downsideDev = Math.sqrt(downsideVar) * Math.sqrt(periodsPerYear);

  if (downsideDev === 0) return 0;
  return (annReturn - riskFreeRate) / downsideDev;
}

/**
 * Treynor Ratio — excess return per unit of systematic (beta) risk.
 * Treynor = (annualized portfolio return - risk-free rate) / beta
 *
 * @param portfolioReturns - Array of periodic portfolio returns
 * @param benchmarkReturns - Array of periodic benchmark returns (same length)
 * @param riskFreeRate - Annualized risk-free rate. Default 0.05.
 * @param periodsPerYear - Periods per year. Default 252.
 * @returns The annualized Treynor ratio
 */
export function treynorRatio(
  portfolioReturns: number[],
  benchmarkReturns: number[],
  riskFreeRate: number = 0.05,
  periodsPerYear: number = 252
): number {
  if (portfolioReturns.length !== benchmarkReturns.length) {
    throw new Error('Portfolio and benchmark return arrays must have the same length');
  }
  if (portfolioReturns.length < 2) throw new Error('Need at least 2 return observations');

  const beta = computeBeta(portfolioReturns, benchmarkReturns);
  if (beta === 0) return 0;
  const annReturn = mean(portfolioReturns) * periodsPerYear;
  return (annReturn - riskFreeRate) / beta;
}

/**
 * Calmar Ratio — annualized return divided by maximum drawdown.
 * Measures return per unit of drawdown risk. Higher is better.
 *
 * @param returns - Array of periodic portfolio returns
 * @param periodsPerYear - Periods per year. Default 252.
 * @returns The Calmar ratio. Returns 0 if max drawdown is 0.
 */
export function calmarRatio(
  returns: number[],
  periodsPerYear: number = 252
): number {
  if (returns.length < 2) throw new Error('Need at least 2 return observations');
  const annReturn = mean(returns) * periodsPerYear;
  const mdd = computeMaxDrawdownFromReturns(returns);
  if (mdd === 0) return 0;
  return annReturn / mdd;
}

/**
 * Information Ratio — active return per unit of tracking error.
 * Measures a portfolio manager's ability to generate excess returns relative
 * to a benchmark, adjusted for the consistency of those excess returns.
 *
 * @param portfolioReturns - Array of periodic portfolio returns
 * @param benchmarkReturns - Array of periodic benchmark returns (same length)
 * @param periodsPerYear - Periods per year. Default 252.
 * @returns The annualized Information ratio
 */
export function informationRatio(
  portfolioReturns: number[],
  benchmarkReturns: number[],
  periodsPerYear: number = 252
): number {
  if (portfolioReturns.length !== benchmarkReturns.length) {
    throw new Error('Portfolio and benchmark return arrays must have the same length');
  }
  if (portfolioReturns.length < 2) throw new Error('Need at least 2 return observations');

  const te = trackingError(portfolioReturns, benchmarkReturns, periodsPerYear);
  if (te === 0) return 0;

  const activeReturn =
    (mean(portfolioReturns) - mean(benchmarkReturns)) * periodsPerYear;
  return activeReturn / te;
}

/**
 * Tracking Error — annualized standard deviation of the difference between
 * portfolio returns and benchmark returns (active returns).
 *
 * @param portfolioReturns - Array of periodic portfolio returns
 * @param benchmarkReturns - Array of periodic benchmark returns (same length)
 * @param periodsPerYear - Periods per year. Default 252.
 * @returns The annualized tracking error
 */
export function trackingError(
  portfolioReturns: number[],
  benchmarkReturns: number[],
  periodsPerYear: number = 252
): number {
  if (portfolioReturns.length !== benchmarkReturns.length) {
    throw new Error('Portfolio and benchmark return arrays must have the same length');
  }
  if (portfolioReturns.length < 2) throw new Error('Need at least 2 return observations');

  const activeReturns = portfolioReturns.map((r, i) => r - benchmarkReturns[i]);
  return stdDev(activeReturns) * Math.sqrt(periodsPerYear);
}

// ─── Internal helpers ──────────────────────────────────────────────────────

/**
 * Compute portfolio beta against a benchmark.
 * Beta = Cov(portfolio, benchmark) / Var(benchmark)
 */
function computeBeta(portfolio: number[], benchmark: number[]): number {
  const n = portfolio.length;
  const mp = mean(portfolio);
  const mb = mean(benchmark);
  let covSum = 0;
  let varSum = 0;
  for (let i = 0; i < n; i++) {
    const dp = portfolio[i] - mp;
    const db = benchmark[i] - mb;
    covSum += dp * db;
    varSum += db * db;
  }
  if (varSum === 0) return 0;
  return covSum / varSum;
}

/**
 * Compute max drawdown from a return series.
 * Reconstructs a cumulative equity curve, then finds the largest peak-to-trough decline.
 * Returns the drawdown as a positive decimal (e.g. 0.20 for 20% drawdown).
 */
function computeMaxDrawdownFromReturns(returns: number[]): number {
  let cumulative = 1;
  let peak = 1;
  let maxDD = 0;
  for (const r of returns) {
    cumulative *= 1 + r;
    if (cumulative > peak) peak = cumulative;
    const dd = (peak - cumulative) / peak;
    if (dd > maxDD) maxDD = dd;
  }
  return maxDD;
}

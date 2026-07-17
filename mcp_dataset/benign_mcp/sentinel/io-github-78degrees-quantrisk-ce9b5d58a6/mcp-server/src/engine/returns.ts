/**
 * returns.ts — Return calculations and covariance matrix construction.
 * Pure functions operating on number arrays. Zero external dependencies.
 */

import { mean, covariance } from './statistics.js';

/**
 * Compute log (continuously compounded) returns from a price series.
 * logReturn[i] = ln(prices[i+1] / prices[i])
 *
 * @param prices - Array of prices in chronological order (oldest first).
 *                 Must have at least 2 elements.
 * @returns Array of log returns with length = prices.length - 1
 */
export function calculateLogReturns(prices: number[]): number[] {
  if (prices.length < 2) throw new Error('Need at least 2 prices to compute returns');
  const returns: number[] = new Array(prices.length - 1);
  for (let i = 0; i < prices.length - 1; i++) {
    if (prices[i] <= 0) throw new Error(`Price at index ${i} is non-positive: ${prices[i]}`);
    returns[i] = Math.log(prices[i + 1] / prices[i]);
  }
  return returns;
}

/**
 * Compute simple (arithmetic) returns from a price series.
 * simpleReturn[i] = (prices[i+1] - prices[i]) / prices[i]
 *
 * @param prices - Array of prices in chronological order (oldest first).
 *                 Must have at least 2 elements.
 * @returns Array of simple returns with length = prices.length - 1
 */
export function calculateSimpleReturns(prices: number[]): number[] {
  if (prices.length < 2) throw new Error('Need at least 2 prices to compute returns');
  const returns: number[] = new Array(prices.length - 1);
  for (let i = 0; i < prices.length - 1; i++) {
    if (prices[i] === 0) throw new Error(`Price at index ${i} is zero`);
    returns[i] = (prices[i + 1] - prices[i]) / prices[i];
  }
  return returns;
}

/**
 * Build a covariance matrix from multiple return series.
 * Returns a 2D array where matrix[i][j] = Cov(returns_i, returns_j).
 *
 * @param returnSeries - Array of return arrays. Each inner array is one asset's
 *                       return series. All must have the same length.
 * @returns A square covariance matrix (n x n) where n = returnSeries.length
 */
export function calculateCovarianceMatrix(returnSeries: number[][]): number[][] {
  const n = returnSeries.length;
  if (n === 0) throw new Error('Need at least one return series');
  const len = returnSeries[0].length;
  for (let i = 1; i < n; i++) {
    if (returnSeries[i].length !== len) {
      throw new Error(`Return series have mismatched lengths: series 0 has ${len}, series ${i} has ${returnSeries[i].length}`);
    }
  }

  const matrix: number[][] = Array.from({ length: n }, () => new Array(n));

  for (let i = 0; i < n; i++) {
    for (let j = i; j < n; j++) {
      const cov = covariance(returnSeries[i], returnSeries[j]);
      matrix[i][j] = cov;
      matrix[j][i] = cov; // symmetric
    }
  }

  return matrix;
}

/**
 * Calculate portfolio returns over time given asset weights and their return series.
 * portfolioReturn[t] = sum(weights[i] * returnSeries[i][t]) for all assets i.
 *
 * @param weights - Array of portfolio weights for each asset.
 *                  Should sum to 1.0 (not enforced, but expected).
 * @param returnSeries - Array of return arrays, one per asset.
 *                        All must have the same length.
 *                        weights.length must equal returnSeries.length.
 * @returns Array of portfolio returns with the same length as each return series
 */
export function calculatePortfolioReturns(
  weights: number[],
  returnSeries: number[][]
): number[] {
  const nAssets = weights.length;
  if (nAssets === 0) throw new Error('Need at least one asset');
  if (nAssets !== returnSeries.length) {
    throw new Error(`Weights length (${nAssets}) must match number of return series (${returnSeries.length})`);
  }
  const T = returnSeries[0].length;
  for (let i = 1; i < nAssets; i++) {
    if (returnSeries[i].length !== T) {
      throw new Error(`Return series have mismatched lengths`);
    }
  }

  const portfolioReturns: number[] = new Array(T);
  for (let t = 0; t < T; t++) {
    let r = 0;
    for (let i = 0; i < nAssets; i++) {
      r += weights[i] * returnSeries[i][t];
    }
    portfolioReturns[t] = r;
  }
  return portfolioReturns;
}

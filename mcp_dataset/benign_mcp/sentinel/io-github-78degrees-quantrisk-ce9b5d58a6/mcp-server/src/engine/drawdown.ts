/**
 * drawdown.ts — Maximum drawdown calculation from price or return series.
 * Pure functions, zero external dependencies.
 */

/** Result of a max drawdown calculation */
export interface DrawdownResult {
  /** Maximum drawdown as a positive decimal (e.g. 0.20 = 20% decline) */
  maxDrawdown: number;
  /** Index in the input array where the peak occurred (before the drawdown) */
  peakIndex: number;
  /** Index in the input array where the trough occurred (bottom of the drawdown) */
  troughIndex: number;
  /** Value at the peak */
  peakValue: number;
  /** Value at the trough */
  troughValue: number;
}

/**
 * Compute the maximum drawdown from a price series.
 *
 * A drawdown is the decline from a historical peak to a subsequent trough.
 * Max drawdown is the largest such decline over the entire series, expressed
 * as a fraction of the peak value.
 *
 * @param prices - Array of prices in chronological order (oldest first).
 *                 Must have at least 2 elements.
 * @returns DrawdownResult with the max drawdown value and the peak/trough indices
 */
export function maxDrawdown(prices: number[]): DrawdownResult {
  if (prices.length < 2) throw new Error('Need at least 2 price observations');

  let peak = prices[0];
  let peakIdx = 0;
  let maxDD = 0;
  let resultPeakIdx = 0;
  let resultTroughIdx = 0;
  let resultPeakValue = prices[0];
  let resultTroughValue = prices[0];

  for (let i = 1; i < prices.length; i++) {
    if (prices[i] > peak) {
      peak = prices[i];
      peakIdx = i;
    }

    const dd = (peak - prices[i]) / peak;
    if (dd > maxDD) {
      maxDD = dd;
      resultPeakIdx = peakIdx;
      resultTroughIdx = i;
      resultPeakValue = peak;
      resultTroughValue = prices[i];
    }
  }

  return {
    maxDrawdown: maxDD,
    peakIndex: resultPeakIdx,
    troughIndex: resultTroughIdx,
    peakValue: resultPeakValue,
    troughValue: resultTroughValue,
  };
}

/**
 * Compute the maximum drawdown from a return series.
 * First reconstructs a cumulative equity curve (starting at 1.0),
 * then computes the max drawdown on that curve.
 *
 * @param returns - Array of periodic returns (e.g. daily simple returns)
 * @returns DrawdownResult with the max drawdown and peak/trough indices
 *          (indices refer to positions in the returns array; the equity curve
 *          has length returns.length + 1, with index 0 being the starting value)
 */
export function maxDrawdownFromReturns(returns: number[]): DrawdownResult {
  if (returns.length < 1) throw new Error('Need at least 1 return observation');

  // Build equity curve: equity[0] = 1, equity[i] = equity[i-1] * (1 + returns[i-1])
  const equity = new Array(returns.length + 1);
  equity[0] = 1;
  for (let i = 0; i < returns.length; i++) {
    equity[i + 1] = equity[i] * (1 + returns[i]);
  }

  return maxDrawdown(equity);
}

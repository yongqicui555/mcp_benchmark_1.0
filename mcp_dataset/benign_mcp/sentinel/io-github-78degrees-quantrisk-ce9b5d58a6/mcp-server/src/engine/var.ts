/**
 * var.ts — Value at Risk (VaR) and Conditional VaR (Expected Shortfall) calculations.
 * Supports historical, parametric (normal), and Cornish-Fisher methods.
 * Pure functions, zero external dependencies beyond the engine's own statistics module.
 */

import {
  mean,
  stdDev,
  percentile,
  skewness,
  kurtosis,
  normalInverseCDF,
} from './statistics.js';

/** Result returned by all VaR functions */
export interface VaRResult {
  /** The VaR value (a positive number representing potential loss) */
  var: number;
  /** The confidence level used (e.g. 0.95) */
  confidenceLevel: number;
  /** The horizon in days */
  horizonDays: number;
  /** The method used */
  method: string;
}

/** Result returned by CVaR / Expected Shortfall */
export interface CVaRResult extends VaRResult {
  /** Conditional VaR (average loss beyond the VaR threshold) */
  cvar: number;
}

/**
 * Historical VaR — directly reads the loss quantile from the empirical distribution.
 * No distributional assumptions.
 *
 * @param returns - Array of historical portfolio returns (e.g. daily log returns).
 *                  Negative values represent losses.
 * @param confidenceLevel - Confidence level in (0, 1). E.g. 0.95 for 95% VaR.
 * @param horizonDays - Holding period in trading days. VaR is scaled by sqrt(horizon).
 *                      Default 1.
 * @returns VaR as a positive number (the loss threshold that is exceeded with
 *          probability 1 - confidenceLevel)
 */
export function historicalVaR(
  returns: number[],
  confidenceLevel: number,
  horizonDays: number = 1
): VaRResult {
  validateInputs(returns, confidenceLevel);
  // VaR is the negative of the (1 - confidence) percentile of returns
  const pctile = percentile(returns, 1 - confidenceLevel);
  const dailyVaR = -pctile;
  const scaledVaR = dailyVaR * Math.sqrt(horizonDays);
  return {
    var: scaledVaR,
    confidenceLevel,
    horizonDays,
    method: 'historical',
  };
}

/**
 * Parametric (variance-covariance) VaR — assumes returns are normally distributed.
 * VaR = -mu + sigma * z_alpha, scaled by sqrt(horizon).
 *
 * @param returns - Array of historical portfolio returns
 * @param confidenceLevel - Confidence level in (0, 1)
 * @param horizonDays - Holding period in trading days. Default 1.
 * @returns VaR as a positive number
 */
export function parametricVaR(
  returns: number[],
  confidenceLevel: number,
  horizonDays: number = 1
): VaRResult {
  validateInputs(returns, confidenceLevel);
  const mu = mean(returns);
  const sigma = stdDev(returns);
  // z_alpha is the quantile for the confidence level (e.g. 1.645 for 95%)
  const zAlpha = normalInverseCDF(confidenceLevel);
  const dailyVaR = -(mu - zAlpha * sigma);
  const scaledVaR = dailyVaR * Math.sqrt(horizonDays);
  return {
    var: Math.max(0, scaledVaR),
    confidenceLevel,
    horizonDays,
    method: 'parametric',
  };
}

/**
 * Cornish-Fisher VaR — adjusts the normal quantile for skewness and excess kurtosis.
 * More accurate than parametric VaR for non-normal return distributions.
 *
 * The Cornish-Fisher expansion modifies the z-score:
 *   z_cf = z + (z^2 - 1)*S/6 + (z^3 - 3*z)*K/24 - (2*z^3 - 5*z)*S^2/36
 * where S = skewness, K = excess kurtosis, z = normal quantile.
 *
 * @param returns - Array of historical portfolio returns (at least 4 for kurtosis)
 * @param confidenceLevel - Confidence level in (0, 1)
 * @param horizonDays - Holding period in trading days. Default 1.
 * @returns VaR as a positive number, adjusted for higher moments
 */
export function cornishFisherVaR(
  returns: number[],
  confidenceLevel: number,
  horizonDays: number = 1
): VaRResult {
  validateInputs(returns, confidenceLevel);
  if (returns.length < 4) throw new Error('Cornish-Fisher requires at least 4 data points');

  const mu = mean(returns);
  const sigma = stdDev(returns);
  const S = skewness(returns);
  const K = kurtosis(returns);
  const z = normalInverseCDF(confidenceLevel);

  // Cornish-Fisher expansion
  const zCF =
    z +
    ((z * z - 1) * S) / 6 +
    ((z * z * z - 3 * z) * K) / 24 -
    ((2 * z * z * z - 5 * z) * S * S) / 36;

  const dailyVaR = -(mu - zCF * sigma);
  const scaledVaR = dailyVaR * Math.sqrt(horizonDays);
  return {
    var: Math.max(0, scaledVaR),
    confidenceLevel,
    horizonDays,
    method: 'cornish_fisher',
  };
}

/**
 * Conditional VaR (CVaR), also called Expected Shortfall (ES).
 * This is the expected loss given that the loss exceeds VaR.
 * CVaR is always >= VaR and is a more conservative risk measure.
 *
 * Uses the historical method: average of all returns that fall below the VaR threshold.
 *
 * @param returns - Array of historical portfolio returns
 * @param confidenceLevel - Confidence level in (0, 1)
 * @param horizonDays - Holding period in trading days. Default 1.
 * @returns Object containing both VaR and CVaR as positive numbers
 */
export function conditionalVaR(
  returns: number[],
  confidenceLevel: number,
  horizonDays: number = 1
): CVaRResult {
  validateInputs(returns, confidenceLevel);

  const threshold = percentile(returns, 1 - confidenceLevel);
  const tailReturns = returns.filter((r) => r <= threshold);

  // If no returns fall below threshold (unlikely), CVaR = VaR
  let cvarDaily: number;
  if (tailReturns.length === 0) {
    cvarDaily = -threshold;
  } else {
    cvarDaily = -mean(tailReturns);
  }

  const varDaily = -threshold;
  const sqrtH = Math.sqrt(horizonDays);

  return {
    var: varDaily * sqrtH,
    cvar: cvarDaily * sqrtH,
    confidenceLevel,
    horizonDays,
    method: 'historical',
  };
}

/** Validate common inputs for VaR functions */
function validateInputs(returns: number[], confidenceLevel: number): void {
  if (returns.length < 2) throw new Error('Need at least 2 return observations');
  if (confidenceLevel <= 0 || confidenceLevel >= 1) {
    throw new Error('Confidence level must be in (0, 1)');
  }
}

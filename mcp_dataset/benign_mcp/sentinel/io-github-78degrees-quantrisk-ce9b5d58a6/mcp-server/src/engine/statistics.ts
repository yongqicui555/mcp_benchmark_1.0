/**
 * statistics.ts — Foundational statistical functions used across the engine.
 * Pure functions, zero dependencies, zero side effects.
 */

/**
 * Compute the arithmetic mean of a numeric array.
 * @param values - Array of numbers
 * @returns The arithmetic mean
 * @throws Error if the array is empty
 */
export function mean(values: number[]): number {
  if (values.length === 0) throw new Error('Cannot compute mean of empty array');
  let sum = 0;
  for (let i = 0; i < values.length; i++) sum += values[i];
  return sum / values.length;
}

/**
 * Compute the sample variance (Bessel-corrected, divides by n-1).
 * @param values - Array of numbers
 * @returns The sample variance
 * @throws Error if the array has fewer than 2 elements
 */
export function variance(values: number[]): number {
  if (values.length < 2) throw new Error('Variance requires at least 2 values');
  const m = mean(values);
  let sumSq = 0;
  for (let i = 0; i < values.length; i++) {
    const d = values[i] - m;
    sumSq += d * d;
  }
  return sumSq / (values.length - 1);
}

/**
 * Compute the sample standard deviation (square root of sample variance).
 * @param values - Array of numbers
 * @returns The sample standard deviation
 */
export function stdDev(values: number[]): number {
  return Math.sqrt(variance(values));
}

/**
 * Compute a percentile from sorted or unsorted data using linear interpolation.
 * @param values - Array of numbers (will not be mutated)
 * @param p - Percentile in [0, 1] (e.g. 0.05 for 5th percentile)
 * @returns The interpolated percentile value
 */
export function percentile(values: number[], p: number): number {
  if (values.length === 0) throw new Error('Cannot compute percentile of empty array');
  if (p < 0 || p > 1) throw new Error('Percentile must be between 0 and 1');
  const sorted = [...values].sort((a, b) => a - b);
  if (p === 0) return sorted[0];
  if (p === 1) return sorted[sorted.length - 1];
  const index = p * (sorted.length - 1);
  const lower = Math.floor(index);
  const upper = Math.ceil(index);
  if (lower === upper) return sorted[lower];
  const frac = index - lower;
  return sorted[lower] * (1 - frac) + sorted[upper] * frac;
}

/**
 * Compute the sample skewness (Fisher's definition, bias-adjusted).
 * Measures asymmetry of the distribution.
 * @param values - Array of numbers (at least 3)
 * @returns The sample skewness
 */
export function skewness(values: number[]): number {
  const n = values.length;
  if (n < 3) throw new Error('Skewness requires at least 3 values');
  const m = mean(values);
  const s = stdDev(values);
  if (s === 0) return 0;
  let m3 = 0;
  for (let i = 0; i < n; i++) {
    const d = (values[i] - m) / s;
    m3 += d * d * d;
  }
  // Fisher's bias-adjusted skewness
  return (n * m3) / ((n - 1) * (n - 2));
}

/**
 * Compute the excess kurtosis (Fisher's definition, bias-adjusted).
 * Normal distribution has excess kurtosis of 0.
 * @param values - Array of numbers (at least 4)
 * @returns The sample excess kurtosis
 */
export function kurtosis(values: number[]): number {
  const n = values.length;
  if (n < 4) throw new Error('Kurtosis requires at least 4 values');
  const m = mean(values);
  const s = stdDev(values);
  if (s === 0) return 0;
  let m4 = 0;
  for (let i = 0; i < n; i++) {
    const d = (values[i] - m) / s;
    m4 += d * d * d * d;
  }
  // Fisher's bias-adjusted excess kurtosis
  const raw = (n * (n + 1) * m4) / ((n - 1) * (n - 2) * (n - 3));
  const correction = (3 * (n - 1) * (n - 1)) / ((n - 2) * (n - 3));
  return raw - correction;
}

/**
 * Compute the sample covariance between two arrays (Bessel-corrected).
 * @param x - First array of numbers
 * @param y - Second array of numbers (same length as x)
 * @returns The sample covariance
 */
export function covariance(x: number[], y: number[]): number {
  if (x.length !== y.length) throw new Error('Arrays must have the same length');
  if (x.length < 2) throw new Error('Covariance requires at least 2 values');
  const mx = mean(x);
  const my = mean(y);
  let sum = 0;
  for (let i = 0; i < x.length; i++) {
    sum += (x[i] - mx) * (y[i] - my);
  }
  return sum / (x.length - 1);
}

/**
 * Standard normal cumulative distribution function (CDF).
 * Uses the Abramowitz & Stegun rational approximation (formula 26.2.17).
 * Accuracy: |error| < 7.5e-8.
 * @param x - The z-score
 * @returns P(Z <= x) for standard normal Z
 */
export function normalCDF(x: number): number {
  // Uses the relationship: normalCDF(z) = 0.5 * (1 + erf(z / sqrt(2)))
  // where erf is approximated via Abramowitz & Stegun formula 7.1.26.
  const a1 = 0.254829592;
  const a2 = -0.284496736;
  const a3 = 1.421413741;
  const a4 = -1.453152027;
  const a5 = 1.061405429;
  const p = 0.3275911;

  const sign = x < 0 ? -1 : 1;
  // erf argument: |x| / sqrt(2)
  const erfArg = Math.abs(x) / Math.SQRT2;
  const t = 1.0 / (1.0 + p * erfArg);
  const t2 = t * t;
  const t3 = t2 * t;
  const t4 = t3 * t;
  const t5 = t4 * t;
  // erf approximation: 1 - poly(t) * exp(-erfArg^2)
  const y = 1.0 - (a1 * t + a2 * t2 + a3 * t3 + a4 * t4 + a5 * t5) * Math.exp(-erfArg * erfArg);
  return 0.5 * (1.0 + sign * y);
}

/**
 * Standard normal probability density function (PDF).
 * @param x - The z-score
 * @returns phi(x) = (1/sqrt(2*pi)) * exp(-x^2/2)
 */
export function normalPDF(x: number): number {
  return Math.exp(-0.5 * x * x) / Math.sqrt(2 * Math.PI);
}

/**
 * Inverse of the standard normal CDF (quantile function).
 * Uses the rational approximation from Abramowitz & Stegun (formula 26.2.23)
 * with refinement via Halley's method for improved accuracy.
 * @param p - Probability in (0, 1)
 * @returns z such that P(Z <= z) = p
 * @throws Error if p is not in (0, 1)
 */
export function normalInverseCDF(p: number): number {
  if (p <= 0 || p >= 1) throw new Error('Probability must be in (0, 1)');

  // Rational approximation constants (Abramowitz & Stegun 26.2.23)
  const a0 = -3.969683028665376e1;
  const a1 = 2.209460984245205e2;
  const a2 = -2.759285104469687e2;
  const a3 = 1.383577518672690e2;
  const a4 = -3.066479806614716e1;
  const a5 = 2.506628277459239e0;

  const b0 = -5.447609879822406e1;
  const b1 = 1.615858368580409e2;
  const b2 = -1.556989798598866e2;
  const b3 = 6.680131188771972e1;
  const b4 = -1.328068155288572e1;

  const c0 = -7.784894002430293e-3;
  const c1 = -3.223964580411365e-1;
  const c2 = -2.400758277161838e0;
  const c3 = -2.549732539343734e0;
  const c4 = 4.374664141464968e0;
  const c5 = 2.938163982698783e0;

  const d0 = 7.784695709041462e-3;
  const d1 = 3.224671290700398e-1;
  const d2 = 2.445134137142996e0;
  const d3 = 3.754408661907416e0;

  const pLow = 0.02425;
  const pHigh = 1 - pLow;

  let q: number;
  let r: number;
  let x: number;

  if (p < pLow) {
    // Rational approximation for lower region
    q = Math.sqrt(-2 * Math.log(p));
    x = (((((c0 * q + c1) * q + c2) * q + c3) * q + c4) * q + c5) /
        ((((d0 * q + d1) * q + d2) * q + d3) * q + 1);
  } else if (p <= pHigh) {
    // Rational approximation for central region
    q = p - 0.5;
    r = q * q;
    x = (((((a0 * r + a1) * r + a2) * r + a3) * r + a4) * r + a5) * q /
        (((((b0 * r + b1) * r + b2) * r + b3) * r + b4) * r + 1);
  } else {
    // Rational approximation for upper region
    q = Math.sqrt(-2 * Math.log(1 - p));
    x = -(((((c0 * q + c1) * q + c2) * q + c3) * q + c4) * q + c5) /
         ((((d0 * q + d1) * q + d2) * q + d3) * q + 1);
  }

  // Halley's rational method refinement for extra precision
  const e = 0.5 * erfc(-x / Math.SQRT2) - p;
  const u = e * Math.sqrt(2 * Math.PI) * Math.exp(x * x / 2);
  x = x - u / (1 + x * u / 2);

  return x;
}

/**
 * Complementary error function approximation.
 * Used internally by normalInverseCDF for refinement.
 * @param x - Input value
 * @returns erfc(x) = 1 - erf(x)
 */
function erfc(x: number): number {
  // Use the relationship: erfc(x) = 2 * normalCDF(-x * sqrt(2))
  // But we need to avoid circular dependency, so use a direct approximation
  const z = Math.abs(x);
  const t = 1.0 / (1.0 + 0.5 * z);
  const tau = t * Math.exp(
    -z * z
    - 1.26551223
    + 1.00002368 * t
    + 0.37409196 * t * t
    + 0.09678418 * t * t * t
    - 0.18628806 * t * t * t * t
    + 0.27886807 * t * t * t * t * t
    - 1.13520398 * t * t * t * t * t * t
    + 1.48851587 * t * t * t * t * t * t * t
    - 0.82215223 * t * t * t * t * t * t * t * t
    + 0.17087277 * t * t * t * t * t * t * t * t * t
  );
  return x >= 0 ? tau : 2 - tau;
}

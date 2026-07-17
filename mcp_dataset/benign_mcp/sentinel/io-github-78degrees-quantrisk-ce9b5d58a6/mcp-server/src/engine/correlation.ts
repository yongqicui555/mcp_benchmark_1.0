/**
 * correlation.ts — Pairwise correlation calculations and matrix construction.
 * Implements Pearson, Spearman (rank), and Kendall (concordance) correlations,
 * plus eigenvalue decomposition for PCA-style risk analysis.
 * Pure functions, zero external dependencies.
 */

import { mean, stdDev, covariance } from './statistics.js';

/** Supported correlation methods */
export type CorrelationMethod = 'pearson' | 'spearman' | 'kendall';

/**
 * Pearson product-moment correlation coefficient between two arrays.
 * Measures linear dependence. Range: [-1, 1].
 *
 * @param x - First array of observations
 * @param y - Second array of observations (same length as x)
 * @returns Pearson correlation coefficient
 */
export function pearsonCorrelation(x: number[], y: number[]): number {
  if (x.length !== y.length) throw new Error('Arrays must have the same length');
  if (x.length < 2) throw new Error('Need at least 2 observations');
  const sx = stdDev(x);
  const sy = stdDev(y);
  if (sx === 0 || sy === 0) return 0; // constant series has zero correlation
  return covariance(x, y) / (sx * sy);
}

/**
 * Spearman rank correlation coefficient between two arrays.
 * Measures monotonic (not necessarily linear) dependence.
 * Computed as Pearson correlation of the rank-transformed data.
 *
 * @param x - First array of observations
 * @param y - Second array of observations (same length as x)
 * @returns Spearman rank correlation coefficient in [-1, 1]
 */
export function spearmanCorrelation(x: number[], y: number[]): number {
  if (x.length !== y.length) throw new Error('Arrays must have the same length');
  if (x.length < 2) throw new Error('Need at least 2 observations');
  const rankX = computeRanks(x);
  const rankY = computeRanks(y);
  return pearsonCorrelation(rankX, rankY);
}

/**
 * Kendall's tau-b rank correlation coefficient between two arrays.
 * Measures ordinal association (concordance vs discordance of pairs).
 * Handles ties via the tau-b correction.
 *
 * @param x - First array of observations
 * @param y - Second array of observations (same length as x)
 * @returns Kendall's tau-b in [-1, 1]
 */
export function kendallCorrelation(x: number[], y: number[]): number {
  if (x.length !== y.length) throw new Error('Arrays must have the same length');
  const n = x.length;
  if (n < 2) throw new Error('Need at least 2 observations');

  let concordant = 0;
  let discordant = 0;
  let tiesX = 0;
  let tiesY = 0;

  for (let i = 0; i < n - 1; i++) {
    for (let j = i + 1; j < n; j++) {
      const dx = x[i] - x[j];
      const dy = y[i] - y[j];
      const product = dx * dy;

      if (product > 0) {
        concordant++;
      } else if (product < 0) {
        discordant++;
      } else {
        if (dx === 0) tiesX++;
        if (dy === 0) tiesY++;
      }
    }
  }

  const nPairs = (n * (n - 1)) / 2;
  const denominator = Math.sqrt((nPairs - tiesX) * (nPairs - tiesY));
  if (denominator === 0) return 0;
  return (concordant - discordant) / denominator;
}

/**
 * Build a full pairwise correlation matrix from multiple return series.
 *
 * @param returnSeries - Array of return arrays, one per asset. All must have the same length.
 * @param method - Correlation method: 'pearson', 'spearman', or 'kendall'. Default 'pearson'.
 * @returns A symmetric n x n correlation matrix where n = returnSeries.length.
 *          Diagonal elements are 1.0.
 */
export function buildCorrelationMatrix(
  returnSeries: number[][],
  method: CorrelationMethod = 'pearson'
): number[][] {
  const n = returnSeries.length;
  if (n === 0) throw new Error('Need at least one return series');
  const len = returnSeries[0].length;
  for (let i = 1; i < n; i++) {
    if (returnSeries[i].length !== len) {
      throw new Error('All return series must have the same length');
    }
  }

  const corrFn = method === 'spearman'
    ? spearmanCorrelation
    : method === 'kendall'
      ? kendallCorrelation
      : pearsonCorrelation;

  const matrix: number[][] = Array.from({ length: n }, () => new Array(n));

  for (let i = 0; i < n; i++) {
    matrix[i][i] = 1.0;
    for (let j = i + 1; j < n; j++) {
      const corr = corrFn(returnSeries[i], returnSeries[j]);
      matrix[i][j] = corr;
      matrix[j][i] = corr;
    }
  }

  return matrix;
}

/**
 * Compute eigenvalues of a real symmetric matrix using the QR algorithm
 * with implicit shifts (Wilkinson shift). Returns eigenvalues sorted descending.
 *
 * Eigenvalues of the correlation matrix are useful for PCA-style analysis:
 * - A dominant first eigenvalue means a strong common factor (market risk).
 * - If the first eigenvalue explains 80%+ of total variance, the portfolio
 *   is poorly diversified.
 *
 * @param matrix - A real symmetric n x n matrix
 * @returns Array of eigenvalues sorted in descending order
 */
export function computeEigenvalues(matrix: number[][]): number[] {
  const n = matrix.length;
  if (n === 0) return [];
  for (let i = 0; i < n; i++) {
    if (matrix[i].length !== n) throw new Error('Matrix must be square');
  }

  // For small matrices, use a direct formula
  if (n === 1) return [matrix[0][0]];
  if (n === 2) {
    return eigenvalues2x2(matrix);
  }

  // For larger matrices, use the iterative QR algorithm.
  // First reduce to tridiagonal form using Householder reflections,
  // then apply QR iteration on the tridiagonal matrix.
  const { diag, offDiag } = tridiagonalize(matrix);
  const eigenvalues = qrAlgorithmTridiagonal(diag, offDiag);
  eigenvalues.sort((a, b) => b - a);
  return eigenvalues;
}

// ─── Internal helpers ──────────────────────────────────────────────────────

/**
 * Compute ranks with average-rank tie breaking.
 */
function computeRanks(values: number[]): number[] {
  const n = values.length;
  const indexed = values.map((v, i) => ({ value: v, index: i }));
  indexed.sort((a, b) => a.value - b.value);

  const ranks = new Array(n);
  let i = 0;
  while (i < n) {
    let j = i;
    while (j < n - 1 && indexed[j + 1].value === indexed[j].value) j++;
    const avgRank = (i + j) / 2 + 1; // 1-based
    for (let k = i; k <= j; k++) {
      ranks[indexed[k].index] = avgRank;
    }
    i = j + 1;
  }
  return ranks;
}

/**
 * Eigenvalues of a 2x2 symmetric matrix via the quadratic formula.
 */
function eigenvalues2x2(m: number[][]): number[] {
  const a = m[0][0];
  const b = m[0][1];
  const d = m[1][1];
  const trace = a + d;
  const det = a * d - b * b;
  const disc = Math.sqrt(Math.max(0, trace * trace - 4 * det));
  return [(trace + disc) / 2, (trace - disc) / 2].sort((x, y) => y - x);
}

/**
 * Reduce a symmetric matrix to tridiagonal form using Householder reflections.
 * Returns the diagonal and off-diagonal elements.
 */
function tridiagonalize(matrix: number[][]): { diag: number[]; offDiag: number[] } {
  const n = matrix.length;
  // Deep copy
  const A: number[][] = matrix.map((row) => [...row]);
  const diag = new Array(n).fill(0);
  const offDiag = new Array(n).fill(0);

  for (let k = 0; k < n - 2; k++) {
    // Compute the Householder vector for column k below the diagonal
    let sigma = 0;
    for (let i = k + 1; i < n; i++) sigma += A[i][k] * A[i][k];
    sigma = Math.sqrt(sigma);

    if (sigma < 1e-15) {
      offDiag[k + 1] = A[k + 1][k];
      continue;
    }

    if (A[k + 1][k] < 0) sigma = -sigma;
    const v = new Array(n).fill(0);
    v[k + 1] = A[k + 1][k] + sigma;
    for (let i = k + 2; i < n; i++) v[i] = A[i][k];

    const beta = 2.0 / dotVec(v, v, k + 1, n);

    // A = A - beta * v * (v' * A) - beta * (A * v) * v'
    // Compute p = beta * A * v
    const p = new Array(n).fill(0);
    for (let i = 0; i < n; i++) {
      for (let j = k + 1; j < n; j++) {
        p[i] += A[i][j] * v[j];
      }
      p[i] *= beta;
    }

    // Compute K = beta/2 * (p' * v)
    let pv = 0;
    for (let i = k + 1; i < n; i++) pv += p[i] * v[i];
    const K = (beta / 2) * pv;

    // q = p - K * v
    const q = new Array(n).fill(0);
    for (let i = 0; i < n; i++) q[i] = p[i] - K * v[i];

    // A = A - v*q' - q*v'
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        A[i][j] -= v[i] * q[j] + q[i] * v[j];
      }
    }

    offDiag[k + 1] = -sigma;
  }

  for (let i = 0; i < n; i++) diag[i] = A[i][i];
  if (n >= 2) offDiag[n - 1] = A[n - 1][n - 2];

  return { diag, offDiag };
}

/** Partial dot product from index lo to hi (exclusive) */
function dotVec(a: number[], b: number[], lo: number, hi: number): number {
  let s = 0;
  for (let i = lo; i < hi; i++) s += a[i] * b[i];
  return s;
}

/**
 * QR algorithm on a symmetric tridiagonal matrix to find all eigenvalues.
 * Implements the implicit symmetric QR step with Wilkinson shift.
 *
 * Uses the standard "bulge chase" approach:
 * d[] = diagonal, e[] = sub-diagonal (e[1..n-1], e[0] unused).
 * Deflates from the bottom: when |e[hi]| is small, d[hi] is an eigenvalue.
 */
function qrAlgorithmTridiagonal(diagIn: number[], offDiagIn: number[]): number[] {
  const n = diagIn.length;
  if (n <= 1) return [...diagIn];

  // Work on copies. Convention: d[0..n-1] diagonal, e[1..n-1] sub-diagonal.
  const d = [...diagIn];
  const e = new Array(n).fill(0);
  for (let i = 1; i < n; i++) e[i] = offDiagIn[i];

  const maxIter = 30 * n * n;

  for (let iter = 0; iter < maxIter; iter++) {
    // Find the lowest unreduced sub-diagonal entry from the bottom
    let m = n - 1;
    while (m > 0) {
      const eps = 1e-14 * (Math.abs(d[m - 1]) + Math.abs(d[m]));
      if (Math.abs(e[m]) <= eps) break;
      m--;
    }
    // If m == n-1, the whole matrix is diagonal — done
    // Actually we need to find the active block differently.
    // Let's use the standard deflation loop.

    // Find the largest index where e[i] is negligible (scanning from bottom)
    let hi = n - 1;
    while (hi > 0 && Math.abs(e[hi]) <= 1e-14 * (Math.abs(d[hi - 1]) + Math.abs(d[hi]))) {
      hi--;
    }
    if (hi === 0) break; // all off-diagonals negligible

    // Find the start of the active block
    let lo = hi - 1;
    while (lo > 0 && Math.abs(e[lo]) > 1e-14 * (Math.abs(d[lo - 1]) + Math.abs(d[lo]))) {
      lo--;
    }

    // Wilkinson shift: eigenvalue of trailing 2x2 block closer to d[hi]
    const p = (d[hi - 1] - d[hi]) / 2;
    const q = e[hi] * e[hi];
    const signP = p >= 0 ? 1 : -1;
    const shift = d[hi] - q / (p + signP * Math.sqrt(p * p + q));

    // Implicit QR step: chase the bulge
    let g = d[lo] - shift;
    let s2 = e[lo + 1]; // sub-diagonal below d[lo]

    let cos: number, sin: number;

    for (let k = lo; k < hi; k++) {
      // Givens rotation to zero out s2 (the bulge)
      const r = Math.sqrt(g * g + s2 * s2);
      if (r === 0) {
        cos = 1;
        sin = 0;
      } else {
        cos = g / r;
        sin = s2 / r;
      }

      // Apply rotation to the tridiagonal matrix
      if (k > lo) {
        e[k] = r;
      }

      const d0 = d[k];
      const d1 = d[k + 1];
      const ek1 = e[k + 1];

      const h = d0 - d1;
      const t = (h * sin + 2 * cos * ek1) * sin;
      d[k] = d0 - t;
      d[k + 1] = d1 + t;
      e[k + 1] = h * cos * sin + ek1 * (cos * cos - sin * sin);

      if (k < hi - 1) {
        g = e[k + 1];
        s2 = sin * e[k + 2];
        e[k + 2] = cos * e[k + 2];
      }
    }
  }

  return d;
}

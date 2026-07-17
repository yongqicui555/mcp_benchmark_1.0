/**
 * optimization.ts — Mean-variance portfolio optimization (Markowitz).
 * Implements gradient-projection optimization for max_sharpe, min_variance,
 * and target_return objectives. No external solver dependencies.
 * Pure functions, zero side effects.
 */

/** Objective types for portfolio optimization */
export type OptimizationObjective = 'max_sharpe' | 'min_variance' | 'target_return';

/** Constraints for portfolio weights */
export interface OptimizationConstraints {
  /** Minimum weight per asset. Default 0.0 (long-only). */
  minWeight?: number;
  /** Maximum weight per asset. Default 1.0. */
  maxWeight?: number;
}

/** Input parameters for the optimizer */
export interface OptimizationParams {
  /** Expected return vector (annualized) for each asset. Length n. */
  expectedReturns: number[];
  /** Covariance matrix (annualized) of asset returns. n x n. */
  covarianceMatrix: number[][];
  /** Optimization objective */
  objective: OptimizationObjective;
  /** Required if objective is 'target_return'. Annualized target return. */
  targetReturn?: number;
  /** Annualized risk-free rate. Default 0.05. */
  riskFreeRate?: number;
  /** Constraints on individual weights */
  constraints?: OptimizationConstraints;
}

/** Result of portfolio optimization */
export interface OptimizationResult {
  /** Optimal weights for each asset (same order as input) */
  weights: number[];
  /** Expected portfolio return (annualized) */
  expectedReturn: number;
  /** Expected portfolio volatility (annualized) */
  expectedVolatility: number;
  /** Expected Sharpe ratio */
  sharpeRatio: number;
}

/** A point on the efficient frontier */
export interface FrontierPoint {
  /** Annualized return */
  return: number;
  /** Annualized volatility */
  volatility: number;
  /** Sharpe ratio */
  sharpe: number;
}

/**
 * Mean-variance portfolio optimization using projected gradient descent.
 *
 * Finds optimal portfolio weights that:
 * - max_sharpe: maximize (E[R] - Rf) / sigma
 * - min_variance: minimize portfolio variance w'*Sigma*w
 * - target_return: minimize variance subject to E[R] >= target
 *
 * Constraints: weights sum to 1, each weight in [minWeight, maxWeight].
 *
 * @param params - Optimization parameters including expected returns,
 *                 covariance matrix, objective, and constraints
 * @returns Optimal weights, expected return, volatility, and Sharpe ratio
 */
export function meanVarianceOptimize(params: OptimizationParams): OptimizationResult {
  const {
    expectedReturns,
    covarianceMatrix,
    objective,
    targetReturn,
    riskFreeRate = 0.05,
    constraints = {},
  } = params;

  const n = expectedReturns.length;
  validateInputs(n, covarianceMatrix, objective, targetReturn);

  const minW = constraints.minWeight ?? 0.0;
  const maxW = constraints.maxWeight ?? 1.0;

  if (objective === 'target_return' && targetReturn == null) {
    throw new Error('targetReturn is required when objective is target_return');
  }

  // Initialize with equal weights
  let weights = new Array(n).fill(1 / n);

  if (objective === 'min_variance') {
    weights = optimizeMinVariance(covarianceMatrix, n, minW, maxW);
  } else if (objective === 'max_sharpe') {
    weights = optimizeMaxSharpe(expectedReturns, covarianceMatrix, riskFreeRate, n, minW, maxW);
  } else {
    // target_return: minimize variance s.t. return >= target
    weights = optimizeTargetReturn(
      expectedReturns,
      covarianceMatrix,
      targetReturn!,
      n,
      minW,
      maxW
    );
  }

  const expRet = dotProduct(weights, expectedReturns);
  const expVol = Math.sqrt(quadraticForm(weights, covarianceMatrix));
  const sharpe = expVol > 0 ? (expRet - riskFreeRate) / expVol : 0;

  return {
    weights,
    expectedReturn: expRet,
    expectedVolatility: expVol,
    sharpeRatio: sharpe,
  };
}

/**
 * Generate points along the efficient frontier.
 * Solves min-variance for a range of target returns from the global minimum
 * variance portfolio to the maximum attainable return.
 *
 * @param expectedReturns - Expected return vector (annualized)
 * @param covarianceMatrix - Covariance matrix (annualized)
 * @param riskFreeRate - Risk-free rate. Default 0.05.
 * @param numPoints - Number of frontier points. Default 20.
 * @param constraints - Weight constraints
 * @returns Array of FrontierPoint objects
 */
export function generateEfficientFrontier(
  expectedReturns: number[],
  covarianceMatrix: number[][],
  riskFreeRate: number = 0.05,
  numPoints: number = 20,
  constraints?: OptimizationConstraints
): FrontierPoint[] {
  const n = expectedReturns.length;
  const minW = constraints?.minWeight ?? 0.0;
  const maxW = constraints?.maxWeight ?? 1.0;

  // Find the min-variance portfolio to get the lower bound return
  const minVarWeights = optimizeMinVariance(covarianceMatrix, n, minW, maxW);
  const minVarReturn = dotProduct(minVarWeights, expectedReturns);

  // Upper bound: the max single-asset return (respecting constraints)
  const maxReturn = Math.max(...expectedReturns);

  const frontier: FrontierPoint[] = [];
  for (let i = 0; i < numPoints; i++) {
    const t = i / (numPoints - 1);
    const target = minVarReturn + t * (maxReturn - minVarReturn);

    const weights = optimizeTargetReturn(
      expectedReturns,
      covarianceMatrix,
      target,
      n,
      minW,
      maxW
    );

    const ret = dotProduct(weights, expectedReturns);
    const vol = Math.sqrt(quadraticForm(weights, covarianceMatrix));
    const sharpe = vol > 0 ? (ret - riskFreeRate) / vol : 0;

    frontier.push({ return: ret, volatility: vol, sharpe });
  }

  return frontier;
}

// ─── Internal optimization routines ────────────────────────────────────────

/**
 * Minimize portfolio variance using projected gradient descent.
 * Gradient of w'*Sigma*w with respect to w is 2*Sigma*w.
 */
function optimizeMinVariance(
  cov: number[][],
  n: number,
  minW: number,
  maxW: number
): number[] {
  let w = new Array(n).fill(1 / n);
  let lr = 0.5;
  const maxIter = 5000;
  const tol = 1e-10;

  for (let iter = 0; iter < maxIter; iter++) {
    // Gradient: 2 * Sigma * w
    const grad = matVecMul(cov, w);
    for (let i = 0; i < n; i++) grad[i] *= 2;

    // Gradient step
    const wNew = new Array(n);
    for (let i = 0; i < n; i++) {
      wNew[i] = w[i] - lr * grad[i];
    }

    // Project onto feasible set (simplex + box constraints)
    projectOntoConstraints(wNew, minW, maxW);

    // Check convergence
    let maxDiff = 0;
    for (let i = 0; i < n; i++) {
      maxDiff = Math.max(maxDiff, Math.abs(wNew[i] - w[i]));
    }

    w = wNew;
    if (maxDiff < tol) break;

    // Adaptive learning rate decay
    if (iter > 0 && iter % 500 === 0) lr *= 0.5;
  }

  return w;
}

/**
 * Maximize Sharpe ratio.
 * We reformulate: maximize (w'*mu - Rf) / sqrt(w'*Sigma*w).
 * Approach: for each candidate target return on a fine grid, solve min-variance
 * subject to that return, then pick the weights with the best Sharpe.
 * This avoids the non-convex Sharpe objective directly.
 */
function optimizeMaxSharpe(
  mu: number[],
  cov: number[][],
  rf: number,
  n: number,
  minW: number,
  maxW: number
): number[] {
  const minVarW = optimizeMinVariance(cov, n, minW, maxW);
  const minVarRet = dotProduct(minVarW, mu);
  const maxRet = Math.max(...mu);

  let bestSharpe = -Infinity;
  let bestWeights = minVarW;

  // Search over 50 target returns
  const numSearch = 50;
  for (let i = 0; i < numSearch; i++) {
    const t = i / (numSearch - 1);
    const target = minVarRet + t * (maxRet - minVarRet);
    const w = optimizeTargetReturn(mu, cov, target, n, minW, maxW);
    const ret = dotProduct(w, mu);
    const vol = Math.sqrt(quadraticForm(w, cov));
    const sharpe = vol > 0 ? (ret - rf) / vol : -Infinity;
    if (sharpe > bestSharpe) {
      bestSharpe = sharpe;
      bestWeights = w;
    }
  }

  return bestWeights;
}

/**
 * Minimize variance subject to a target return constraint.
 * Uses projected gradient descent with a penalty term for the return constraint.
 *
 * L(w) = w'*Sigma*w + lambda * max(0, targetReturn - w'*mu)^2
 */
function optimizeTargetReturn(
  mu: number[],
  cov: number[][],
  target: number,
  n: number,
  minW: number,
  maxW: number
): number[] {
  let w = new Array(n).fill(1 / n);
  let lr = 0.3;
  const maxIter = 5000;
  const tol = 1e-10;
  const penalty = 100; // penalty multiplier for return constraint

  for (let iter = 0; iter < maxIter; iter++) {
    // Gradient of variance: 2 * Sigma * w
    const gradVar = matVecMul(cov, w);
    for (let i = 0; i < n; i++) gradVar[i] *= 2;

    // Penalty gradient for return constraint
    const currentReturn = dotProduct(w, mu);
    const returnDeficit = target - currentReturn;

    const grad = new Array(n);
    if (returnDeficit > 0) {
      // Need more return: gradient of penalty is -2 * penalty * deficit * mu
      for (let i = 0; i < n; i++) {
        grad[i] = gradVar[i] - 2 * penalty * returnDeficit * mu[i];
      }
    } else {
      for (let i = 0; i < n; i++) {
        grad[i] = gradVar[i];
      }
    }

    const wNew = new Array(n);
    for (let i = 0; i < n; i++) {
      wNew[i] = w[i] - lr * grad[i];
    }

    projectOntoConstraints(wNew, minW, maxW);

    let maxDiff = 0;
    for (let i = 0; i < n; i++) {
      maxDiff = Math.max(maxDiff, Math.abs(wNew[i] - w[i]));
    }

    w = wNew;
    if (maxDiff < tol) break;
    if (iter > 0 && iter % 500 === 0) lr *= 0.5;
  }

  return w;
}

// ─── Linear algebra helpers ────────────────────────────────────────────────

/**
 * Project weights onto the feasible set: sum to 1, each in [minW, maxW].
 * Uses iterative clipping and renormalization (Michelot's algorithm variant).
 * Modifies the array in place.
 */
function projectOntoConstraints(w: number[], minW: number, maxW: number): void {
  const n = w.length;
  const maxIter = 100;

  for (let iter = 0; iter < maxIter; iter++) {
    // Clip to box constraints
    for (let i = 0; i < n; i++) {
      w[i] = Math.max(minW, Math.min(maxW, w[i]));
    }

    // Normalize to sum to 1
    let sum = 0;
    for (let i = 0; i < n; i++) sum += w[i];

    if (Math.abs(sum - 1) < 1e-12) return;

    // Distribute the deficit/surplus evenly among non-clamped weights
    const deficit = 1 - sum;
    let numFree = 0;
    for (let i = 0; i < n; i++) {
      if (
        (deficit > 0 && w[i] < maxW - 1e-12) ||
        (deficit < 0 && w[i] > minW + 1e-12)
      ) {
        numFree++;
      }
    }

    if (numFree === 0) {
      // All clamped; just scale uniformly
      for (let i = 0; i < n; i++) w[i] /= sum;
      return;
    }

    const adjust = deficit / numFree;
    for (let i = 0; i < n; i++) {
      if (
        (deficit > 0 && w[i] < maxW - 1e-12) ||
        (deficit < 0 && w[i] > minW + 1e-12)
      ) {
        w[i] += adjust;
      }
    }
  }

  // Final normalization as safety net
  let sum = 0;
  for (let i = 0; i < n; i++) sum += w[i];
  if (sum > 0) {
    for (let i = 0; i < n; i++) w[i] /= sum;
  }
}

/** Dot product of two vectors */
function dotProduct(a: number[], b: number[]): number {
  let sum = 0;
  for (let i = 0; i < a.length; i++) sum += a[i] * b[i];
  return sum;
}

/** Matrix-vector multiplication: result = M * v */
function matVecMul(M: number[][], v: number[]): number[] {
  const n = M.length;
  const result = new Array(n).fill(0);
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < v.length; j++) {
      result[i] += M[i][j] * v[j];
    }
  }
  return result;
}

/** Quadratic form: v' * M * v */
function quadraticForm(v: number[], M: number[][]): number {
  const n = v.length;
  let sum = 0;
  for (let i = 0; i < n; i++) {
    for (let j = 0; j < n; j++) {
      sum += v[i] * M[i][j] * v[j];
    }
  }
  return sum;
}

/** Validate optimization inputs */
function validateInputs(
  n: number,
  cov: number[][],
  objective: OptimizationObjective,
  targetReturn?: number
): void {
  if (n < 2) throw new Error('Need at least 2 assets');
  if (cov.length !== n) throw new Error('Covariance matrix rows must match number of assets');
  for (let i = 0; i < n; i++) {
    if (cov[i].length !== n) {
      throw new Error(`Covariance matrix row ${i} has wrong length`);
    }
  }
  if (objective === 'target_return' && targetReturn == null) {
    throw new Error('targetReturn required for target_return objective');
  }
}

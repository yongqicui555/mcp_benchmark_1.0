/**
 * monte-carlo.ts — Monte Carlo path generation for portfolio simulation.
 * Implements Geometric Brownian Motion (GBM) and Merton Jump-Diffusion models.
 * Uses a seedable PRNG (Mulberry32) for reproducible simulations.
 * Pure functions, zero external dependencies.
 */

import { mean, stdDev, normalInverseCDF } from './statistics.js';

/** Parameters for Geometric Brownian Motion path generation */
export interface GBMParams {
  /** Annualized drift (expected return). If not provided, estimated from returnSeries. */
  mu?: number;
  /** Annualized volatility. If not provided, estimated from returnSeries. */
  sigma?: number;
  /** Historical return series used to estimate mu and sigma if not directly provided */
  returnSeries?: number[];
  /** Number of simulation paths to generate */
  numPaths: number;
  /** Simulation horizon in trading days */
  horizonDays: number;
  /** Initial portfolio or asset value */
  initialValue: number;
  /** Trading days per year for annualization. Default 252. */
  tradingDaysPerYear?: number;
  /** Optional seed for reproducibility. If null/undefined, uses Math.random. */
  seed?: number | null;
}

/** Parameters for Merton Jump-Diffusion path generation */
export interface JumpDiffusionParams extends GBMParams {
  /** Average number of jumps per year (Poisson intensity lambda). Default 1.0. */
  jumpIntensity?: number;
  /** Mean of the jump size (log-normal). Default -0.05 (5% drop). */
  jumpMean?: number;
  /** Standard deviation of the jump size. Default 0.10. */
  jumpStdDev?: number;
}

/** Result of a Monte Carlo simulation */
export interface MonteCarloResult {
  /** Array of terminal (end-of-horizon) values, one per path */
  terminalValues: number[];
  /** Number of paths actually generated */
  numPaths: number;
  /** Horizon in days */
  horizonDays: number;
  /** The drift used */
  mu: number;
  /** The volatility used */
  sigma: number;
}

/**
 * Mulberry32 — a fast 32-bit seedable PRNG.
 * Returns a function that produces uniform random numbers in [0, 1).
 *
 * @param seed - 32-bit integer seed
 * @returns A function that returns the next random number in [0, 1)
 */
function mulberry32(seed: number): () => number {
  let state = seed | 0;
  return function (): number {
    state = (state + 0x6d2b79f5) | 0;
    let t = Math.imul(state ^ (state >>> 15), 1 | state);
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

/**
 * Generate a standard normal random variate using the Box-Muller transform.
 * @param rng - A uniform random number generator returning values in [0, 1)
 * @returns A standard normal random variate
 */
function boxMuller(rng: () => number): number {
  let u1 = rng();
  // Avoid log(0)
  while (u1 === 0) u1 = rng();
  const u2 = rng();
  return Math.sqrt(-2.0 * Math.log(u1)) * Math.cos(2.0 * Math.PI * u2);
}

/**
 * Generate a Poisson-distributed random variate using Knuth's algorithm.
 * @param lambda - Expected number of events (rate parameter)
 * @param rng - Uniform random number generator
 * @returns A non-negative integer drawn from Poisson(lambda)
 */
function poissonRandom(lambda: number, rng: () => number): number {
  const L = Math.exp(-lambda);
  let k = 0;
  let p = 1;
  do {
    k++;
    p *= rng();
  } while (p > L);
  return k - 1;
}

/**
 * Generate terminal portfolio values using Geometric Brownian Motion (GBM).
 *
 * The GBM model: dS = mu*S*dt + sigma*S*dW
 * Discrete-time: S(t+dt) = S(t) * exp((mu - sigma^2/2)*dt + sigma*sqrt(dt)*Z)
 * where Z ~ N(0,1).
 *
 * For efficiency, since we only need terminal values (not full paths),
 * we use the closed-form: S(T) = S(0) * exp((mu - sigma^2/2)*T + sigma*sqrt(T)*Z)
 * when horizonDays == 1 step. For multi-day horizons, we step daily to capture
 * path-dependent effects if needed in the future.
 *
 * @param params - GBM simulation parameters
 * @returns MonteCarloResult with terminal values for each path
 */
export function generateGBMPaths(params: GBMParams): MonteCarloResult {
  const {
    numPaths,
    horizonDays,
    initialValue,
    tradingDaysPerYear = 252,
    seed,
  } = params;

  if (numPaths <= 0) throw new Error('numPaths must be positive');
  if (horizonDays <= 0) throw new Error('horizonDays must be positive');
  if (initialValue <= 0) throw new Error('initialValue must be positive');

  const { mu, sigma } = resolveParams(params, tradingDaysPerYear);
  const rng = seed != null ? mulberry32(seed) : Math.random;

  const dt = 1 / tradingDaysPerYear; // one trading day as fraction of year
  const drift = (mu - 0.5 * sigma * sigma) * dt;
  const diffusion = sigma * Math.sqrt(dt);

  const terminalValues: number[] = new Array(numPaths);

  for (let p = 0; p < numPaths; p++) {
    let value = initialValue;
    for (let d = 0; d < horizonDays; d++) {
      const z = boxMuller(rng);
      value *= Math.exp(drift + diffusion * z);
    }
    terminalValues[p] = value;
  }

  return { terminalValues, numPaths, horizonDays, mu, sigma };
}

/**
 * Generate terminal portfolio values using Merton's Jump-Diffusion model.
 *
 * Extends GBM by adding random jumps (modeled as a compound Poisson process
 * with log-normally distributed jump sizes). This captures fat tails and
 * sudden market crashes better than pure GBM.
 *
 * dS/S = (mu - lambda*k)*dt + sigma*dW + J*dN
 * where N ~ Poisson(lambda*dt), J ~ LogNormal(jumpMean, jumpStdDev)
 * and k = E[e^J - 1] is the compensator.
 *
 * @param params - Jump-diffusion simulation parameters
 * @returns MonteCarloResult with terminal values for each path
 */
export function generateJumpDiffusionPaths(params: JumpDiffusionParams): MonteCarloResult {
  const {
    numPaths,
    horizonDays,
    initialValue,
    tradingDaysPerYear = 252,
    seed,
    jumpIntensity = 1.0,
    jumpMean = -0.05,
    jumpStdDev = 0.10,
  } = params;

  if (numPaths <= 0) throw new Error('numPaths must be positive');
  if (horizonDays <= 0) throw new Error('horizonDays must be positive');
  if (initialValue <= 0) throw new Error('initialValue must be positive');

  const { mu, sigma } = resolveParams(params, tradingDaysPerYear);
  const rng = seed != null ? mulberry32(seed) : Math.random;

  const dt = 1 / tradingDaysPerYear;
  // Compensator: expected jump contribution per unit time
  const k = Math.exp(jumpMean + 0.5 * jumpStdDev * jumpStdDev) - 1;
  const drift = (mu - 0.5 * sigma * sigma - jumpIntensity * k) * dt;
  const diffusion = sigma * Math.sqrt(dt);
  const lambdaDt = jumpIntensity * dt;

  const terminalValues: number[] = new Array(numPaths);

  for (let p = 0; p < numPaths; p++) {
    let value = initialValue;
    for (let d = 0; d < horizonDays; d++) {
      const z = boxMuller(rng);
      let logJump = 0;
      // Number of jumps in this time step
      const numJumps = poissonRandom(lambdaDt, rng);
      for (let j = 0; j < numJumps; j++) {
        logJump += jumpMean + jumpStdDev * boxMuller(rng);
      }
      value *= Math.exp(drift + diffusion * z + logJump);
    }
    terminalValues[p] = value;
  }

  return { terminalValues, numPaths, horizonDays, mu, sigma };
}

/**
 * Resolve drift (mu) and volatility (sigma) from either explicit params
 * or by estimating from a return series.
 */
function resolveParams(
  params: GBMParams,
  tradingDaysPerYear: number
): { mu: number; sigma: number } {
  let mu = params.mu;
  let sigma = params.sigma;

  if (mu == null || sigma == null) {
    if (!params.returnSeries || params.returnSeries.length < 2) {
      throw new Error(
        'Must provide either (mu, sigma) or a returnSeries with at least 2 observations'
      );
    }
    const dailyMean = mean(params.returnSeries);
    const dailyStd = stdDev(params.returnSeries);
    if (mu == null) mu = dailyMean * tradingDaysPerYear;
    if (sigma == null) sigma = dailyStd * Math.sqrt(tradingDaysPerYear);
  }

  return { mu, sigma };
}

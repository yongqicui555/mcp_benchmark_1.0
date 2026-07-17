/**
 * greeks.ts — Option pricing and Greeks using Black-Scholes and binomial tree models.
 * Implements European option pricing (Black-Scholes closed-form) and
 * American option pricing (Cox-Ross-Rubinstein binomial tree with early exercise).
 * Also includes implied volatility solver via Newton-Raphson.
 * Pure functions, zero external dependencies.
 */

import { normalCDF, normalPDF } from './statistics.js';

/** Option type: call or put */
export type OptionType = 'call' | 'put';

/** Parameters for Black-Scholes pricing */
export interface BSParams {
  /** Current price of the underlying asset */
  spot: number;
  /** Strike price of the option */
  strike: number;
  /** Time to expiration in years (e.g. 0.25 for 3 months) */
  timeToExpiry: number;
  /** Annualized risk-free interest rate (e.g. 0.05 for 5%) */
  riskFreeRate: number;
  /** Annualized volatility of the underlying (e.g. 0.20 for 20%) */
  volatility: number;
  /** Option type: 'call' or 'put' */
  optionType: OptionType;
  /** Continuous dividend yield (annualized). Default 0. */
  dividendYield?: number;
}

/** Full set of option Greeks */
export interface GreeksResult {
  /** Theoretical option price */
  price: number;
  /** Delta: rate of change of price w.r.t. underlying price */
  delta: number;
  /** Gamma: rate of change of delta w.r.t. underlying price */
  gamma: number;
  /** Theta: rate of change of price w.r.t. time (per calendar day) */
  theta: number;
  /** Vega: rate of change of price w.r.t. 1% change in volatility */
  vega: number;
  /** Rho: rate of change of price w.r.t. 1% change in interest rate */
  rho: number;
}

/** Parameters for binomial tree pricing */
export interface BinomialParams {
  /** Current price of the underlying asset */
  spot: number;
  /** Strike price */
  strike: number;
  /** Time to expiration in years */
  timeToExpiry: number;
  /** Annualized risk-free rate */
  riskFreeRate: number;
  /** Annualized volatility */
  volatility: number;
  /** Option type: 'call' or 'put' */
  optionType: OptionType;
  /** Number of time steps in the tree. Default 100. */
  steps?: number;
  /** Continuous dividend yield. Default 0. */
  dividendYield?: number;
}

// ─── d1, d2 helpers ────────────────────────────────────────────────────────

function d1(S: number, K: number, T: number, r: number, sigma: number, q: number): number {
  return (Math.log(S / K) + (r - q + 0.5 * sigma * sigma) * T) / (sigma * Math.sqrt(T));
}

function d2(S: number, K: number, T: number, r: number, sigma: number, q: number): number {
  return d1(S, K, T, r, sigma, q) - sigma * Math.sqrt(T);
}

// ─── Black-Scholes pricing ─────────────────────────────────────────────────

/**
 * Black-Scholes option price for European calls and puts.
 *
 * Call: S * e^(-qT) * N(d1) - K * e^(-rT) * N(d2)
 * Put:  K * e^(-rT) * N(-d2) - S * e^(-qT) * N(-d1)
 *
 * @param params - Black-Scholes parameters
 * @returns The theoretical option price
 */
export function blackScholesPrice(params: BSParams): number {
  validateBSParams(params);
  const { spot: S, strike: K, timeToExpiry: T, riskFreeRate: r, volatility: sigma, optionType } = params;
  const q = params.dividendYield ?? 0;

  if (T <= 0) {
    // At expiry: intrinsic value
    return optionType === 'call' ? Math.max(S - K, 0) : Math.max(K - S, 0);
  }

  const dd1 = d1(S, K, T, r, sigma, q);
  const dd2 = d2(S, K, T, r, sigma, q);

  if (optionType === 'call') {
    return S * Math.exp(-q * T) * normalCDF(dd1) - K * Math.exp(-r * T) * normalCDF(dd2);
  } else {
    return K * Math.exp(-r * T) * normalCDF(-dd2) - S * Math.exp(-q * T) * normalCDF(-dd1);
  }
}

// ─── Individual Greeks ─────────────────────────────────────────────────────

/**
 * Black-Scholes Delta — sensitivity of option price to underlying price.
 * Call delta is in [0, 1], put delta is in [-1, 0].
 *
 * @param params - Black-Scholes parameters
 * @returns Delta value
 */
export function blackScholesDelta(params: BSParams): number {
  validateBSParams(params);
  const { spot: S, strike: K, timeToExpiry: T, riskFreeRate: r, volatility: sigma, optionType } = params;
  const q = params.dividendYield ?? 0;
  if (T <= 0) {
    if (optionType === 'call') return S > K ? 1 : S === K ? 0.5 : 0;
    return S < K ? -1 : S === K ? -0.5 : 0;
  }
  const dd1 = d1(S, K, T, r, sigma, q);
  if (optionType === 'call') {
    return Math.exp(-q * T) * normalCDF(dd1);
  } else {
    return Math.exp(-q * T) * (normalCDF(dd1) - 1);
  }
}

/**
 * Black-Scholes Gamma — rate of change of delta w.r.t. underlying price.
 * Gamma is the same for calls and puts.
 *
 * @param params - Black-Scholes parameters
 * @returns Gamma value (always non-negative)
 */
export function blackScholesGamma(params: BSParams): number {
  validateBSParams(params);
  const { spot: S, strike: K, timeToExpiry: T, riskFreeRate: r, volatility: sigma } = params;
  const q = params.dividendYield ?? 0;
  if (T <= 0) return 0;
  const dd1 = d1(S, K, T, r, sigma, q);
  return Math.exp(-q * T) * normalPDF(dd1) / (S * sigma * Math.sqrt(T));
}

/**
 * Black-Scholes Theta — rate of change of option price w.r.t. time.
 * Returned as the daily rate of decay (negative for long options).
 *
 * @param params - Black-Scholes parameters
 * @returns Theta per calendar day (typically negative)
 */
export function blackScholesTheta(params: BSParams): number {
  validateBSParams(params);
  const { spot: S, strike: K, timeToExpiry: T, riskFreeRate: r, volatility: sigma, optionType } = params;
  const q = params.dividendYield ?? 0;
  if (T <= 0) return 0;

  const dd1 = d1(S, K, T, r, sigma, q);
  const dd2 = d2(S, K, T, r, sigma, q);
  const sqrtT = Math.sqrt(T);

  const term1 = -(S * Math.exp(-q * T) * normalPDF(dd1) * sigma) / (2 * sqrtT);

  let theta: number;
  if (optionType === 'call') {
    theta = term1
      + q * S * Math.exp(-q * T) * normalCDF(dd1)
      - r * K * Math.exp(-r * T) * normalCDF(dd2);
  } else {
    theta = term1
      - q * S * Math.exp(-q * T) * normalCDF(-dd1)
      + r * K * Math.exp(-r * T) * normalCDF(-dd2);
  }

  // Convert from per-year to per-calendar-day
  return theta / 365;
}

/**
 * Black-Scholes Vega — sensitivity of option price to a 1% change in volatility.
 * Vega is the same for calls and puts.
 *
 * @param params - Black-Scholes parameters
 * @returns Vega (price change per 0.01 increase in volatility)
 */
export function blackScholesVega(params: BSParams): number {
  validateBSParams(params);
  const { spot: S, strike: K, timeToExpiry: T, riskFreeRate: r, volatility: sigma } = params;
  const q = params.dividendYield ?? 0;
  if (T <= 0) return 0;
  const dd1 = d1(S, K, T, r, sigma, q);
  // Raw vega is per 1.0 vol change; divide by 100 for per 1% change
  return S * Math.exp(-q * T) * normalPDF(dd1) * Math.sqrt(T) / 100;
}

/**
 * Black-Scholes Rho — sensitivity of option price to a 1% change in interest rate.
 *
 * @param params - Black-Scholes parameters
 * @returns Rho (price change per 0.01 increase in risk-free rate)
 */
export function blackScholesRho(params: BSParams): number {
  validateBSParams(params);
  const { spot: S, strike: K, timeToExpiry: T, riskFreeRate: r, volatility: sigma, optionType } = params;
  const q = params.dividendYield ?? 0;
  if (T <= 0) return 0;
  const dd2 = d2(S, K, T, r, sigma, q);

  if (optionType === 'call') {
    return K * T * Math.exp(-r * T) * normalCDF(dd2) / 100;
  } else {
    return -K * T * Math.exp(-r * T) * normalCDF(-dd2) / 100;
  }
}

// ─── Implied Volatility ────────────────────────────────────────────────────

/**
 * Compute implied volatility from a market price using Newton-Raphson iteration.
 * Finds the volatility sigma such that BS(sigma) = marketPrice.
 *
 * @param marketPrice - Observed market price of the option
 * @param spot - Current underlying price
 * @param strike - Strike price
 * @param timeToExpiry - Time to expiration in years
 * @param riskFreeRate - Risk-free rate
 * @param optionType - 'call' or 'put'
 * @param dividendYield - Continuous dividend yield. Default 0.
 * @param maxIter - Maximum Newton-Raphson iterations. Default 100.
 * @param tol - Convergence tolerance. Default 1e-8.
 * @returns The implied volatility (annualized)
 * @throws Error if the solver does not converge
 */
export function impliedVolatility(
  marketPrice: number,
  spot: number,
  strike: number,
  timeToExpiry: number,
  riskFreeRate: number,
  optionType: OptionType,
  dividendYield: number = 0,
  maxIter: number = 100,
  tol: number = 1e-8
): number {
  if (marketPrice <= 0) throw new Error('Market price must be positive');
  if (timeToExpiry <= 0) throw new Error('Time to expiry must be positive');

  // Initial guess using Brenner-Subrahmanyam approximation
  let sigma = Math.sqrt((2 * Math.PI) / timeToExpiry) * (marketPrice / spot);
  sigma = Math.max(0.01, Math.min(sigma, 5.0)); // clamp to reasonable range

  for (let i = 0; i < maxIter; i++) {
    const params: BSParams = {
      spot,
      strike,
      timeToExpiry,
      riskFreeRate,
      volatility: sigma,
      optionType,
      dividendYield,
    };

    const price = blackScholesPrice(params);
    const diff = price - marketPrice;

    if (Math.abs(diff) < tol) return sigma;

    // Vega (raw, not per 1%): dPrice/dSigma
    const dd1 = d1(spot, strike, timeToExpiry, riskFreeRate, sigma, dividendYield);
    const rawVega = spot * Math.exp(-dividendYield * timeToExpiry) * normalPDF(dd1) * Math.sqrt(timeToExpiry);

    if (rawVega < 1e-15) {
      // Vega too small; fall back to bisection step
      sigma = diff > 0 ? sigma * 0.5 : sigma * 1.5;
      continue;
    }

    sigma -= diff / rawVega;
    sigma = Math.max(0.001, Math.min(sigma, 10.0)); // keep in bounds
  }

  throw new Error(`Implied volatility did not converge after ${maxIter} iterations`);
}

// ─── Binomial Tree (American options) ──────────────────────────────────────

/**
 * Price an option using the Cox-Ross-Rubinstein (CRR) binomial tree.
 * Supports early exercise for American-style options.
 *
 * At each node, the option value is max(exercise_value, continuation_value).
 * For European style, early exercise is not checked (but this function still works).
 *
 * @param params - Binomial tree parameters
 * @param american - Whether to allow early exercise. Default true.
 * @returns The option price at time 0
 */
export function binomialTreePrice(params: BinomialParams, american: boolean = true): number {
  const {
    spot: S,
    strike: K,
    timeToExpiry: T,
    riskFreeRate: r,
    volatility: sigma,
    optionType,
    steps: N = 100,
    dividendYield: q = 0,
  } = params;

  if (T <= 0) return optionType === 'call' ? Math.max(S - K, 0) : Math.max(K - S, 0);
  if (N < 1) throw new Error('Steps must be at least 1');

  const dt = T / N;
  const u = Math.exp(sigma * Math.sqrt(dt)); // up factor
  const dFactor = 1 / u;                      // down factor
  const discount = Math.exp(-r * dt);
  const pUp = (Math.exp((r - q) * dt) - dFactor) / (u - dFactor); // risk-neutral prob of up move

  // Build the terminal payoff array
  const values = new Array(N + 1);
  for (let j = 0; j <= N; j++) {
    const spotAtNode = S * Math.pow(u, 2 * j - N);
    values[j] =
      optionType === 'call'
        ? Math.max(spotAtNode - K, 0)
        : Math.max(K - spotAtNode, 0);
  }

  // Step backward through the tree
  for (let step = N - 1; step >= 0; step--) {
    for (let j = 0; j <= step; j++) {
      // Continuation value
      values[j] = discount * (pUp * values[j + 1] + (1 - pUp) * values[j]);

      // Early exercise check (American only)
      if (american) {
        const spotAtNode = S * Math.pow(u, 2 * j - step);
        const exerciseValue =
          optionType === 'call'
            ? Math.max(spotAtNode - K, 0)
            : Math.max(K - spotAtNode, 0);
        values[j] = Math.max(values[j], exerciseValue);
      }
    }
  }

  return values[0];
}

// ─── Validation ────────────────────────────────────────────────────────────

function validateBSParams(params: BSParams): void {
  if (params.spot <= 0) throw new Error('Spot price must be positive');
  if (params.strike <= 0) throw new Error('Strike price must be positive');
  if (params.volatility < 0) throw new Error('Volatility cannot be negative');
}

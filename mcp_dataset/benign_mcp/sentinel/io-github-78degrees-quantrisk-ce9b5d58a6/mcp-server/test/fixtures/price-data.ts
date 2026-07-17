/**
 * price-data.ts — Generates realistic mock price data for testing.
 *
 * Uses a seeded pseudo-random number generator (simple LCG) so tests are
 * deterministic. Produces 252 trading days of OHLCV data per ticker.
 */

import type { PricePoint } from "../../src/services/yahoo-finance.js";

// ---------------------------------------------------------------------------
// Seeded PRNG (Linear Congruential Generator)
// ---------------------------------------------------------------------------

function createRng(seed: number) {
  let state = seed;
  return function next(): number {
    // Park-Miller LCG
    state = (state * 16807) % 2147483647;
    return (state - 1) / 2147483646;
  };
}

/**
 * Box-Muller transform — convert two uniform [0,1) draws into a standard
 * normal variate.
 */
function normalRandom(rng: () => number): number {
  const u1 = rng();
  const u2 = rng();
  return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
}

// ---------------------------------------------------------------------------
// Generator
// ---------------------------------------------------------------------------

export interface MockTickerConfig {
  ticker: string;
  startPrice: number;
  /** Annualised volatility (decimal). 0.25 = 25%. */
  annualVol: number;
  /** Annualised drift (decimal). 0.08 = 8%. */
  annualDrift: number;
  /** PRNG seed — different per ticker for variety. */
  seed: number;
}

/**
 * Generate `days` trading days of OHLCV data using geometric Brownian motion.
 * Prices are in chronological order (oldest first).
 */
export function generatePriceSeries(
  config: MockTickerConfig,
  days: number = 253 // 253 prices => 252 returns
): PricePoint[] {
  const { startPrice, annualVol, annualDrift, seed } = config;
  const rng = createRng(seed);

  const dailyDrift = annualDrift / 252;
  const dailyVol = annualVol / Math.sqrt(252);

  const points: PricePoint[] = [];
  let price = startPrice;

  // Build a base date sequence (go back `days` trading days from a fixed date)
  const baseDate = new Date("2025-12-31");

  for (let i = 0; i < days; i++) {
    // Generate intraday OHLC around the close
    const z = normalRandom(rng);
    const logReturn = dailyDrift + dailyVol * z;
    const newPrice = price * Math.exp(logReturn);

    // Simulate realistic OHLC: high/low spread around the close
    const spread = Math.abs(newPrice * dailyVol * (0.5 + rng()));
    const open = price + (newPrice - price) * (0.3 + 0.4 * rng());
    const high = Math.max(open, newPrice) + spread * rng();
    const low = Math.min(open, newPrice) - spread * rng();
    const volume = Math.round(5_000_000 + 10_000_000 * rng());

    // Compute the date (skip weekends naively by going back calendar days)
    const date = new Date(baseDate);
    date.setDate(date.getDate() - (days - 1 - i));
    const isoDate = date.toISOString().slice(0, 10);

    points.push({
      date: isoDate,
      open: round4(Math.max(0.01, open)),
      high: round4(Math.max(0.01, high)),
      low: round4(Math.max(0.01, low)),
      close: round4(Math.max(0.01, newPrice)),
      volume,
    });

    price = newPrice;
  }

  return points;
}

function round4(n: number): number {
  return Math.round(n * 10000) / 10000;
}

// ---------------------------------------------------------------------------
// Pre-built configs for common test tickers
// ---------------------------------------------------------------------------

export const TICKER_CONFIGS: Record<string, MockTickerConfig> = {
  AAPL: {
    ticker: "AAPL",
    startPrice: 150,
    annualVol: 0.28,
    annualDrift: 0.10,
    seed: 42,
  },
  MSFT: {
    ticker: "MSFT",
    startPrice: 380,
    annualVol: 0.25,
    annualDrift: 0.12,
    seed: 137,
  },
  NVDA: {
    ticker: "NVDA",
    startPrice: 800,
    annualVol: 0.45,
    annualDrift: 0.20,
    seed: 256,
  },
  SPY: {
    ticker: "SPY",
    startPrice: 500,
    annualVol: 0.16,
    annualDrift: 0.09,
    seed: 999,
  },
};

/**
 * Generate a full mock price map for the given tickers (defaults to all four).
 * Returns the same shape as AlphaVantageService.fetchMultiplePrices().
 */
export function generateMockPriceMap(
  tickers: string[] = ["AAPL", "MSFT", "NVDA", "SPY"],
  days: number = 253
): Record<string, PricePoint[]> {
  const map: Record<string, PricePoint[]> = {};
  for (const ticker of tickers) {
    const config = TICKER_CONFIGS[ticker];
    if (!config) {
      throw new Error(`No mock config for ticker: ${ticker}`);
    }
    map[ticker] = generatePriceSeries(config, days);
  }
  return map;
}

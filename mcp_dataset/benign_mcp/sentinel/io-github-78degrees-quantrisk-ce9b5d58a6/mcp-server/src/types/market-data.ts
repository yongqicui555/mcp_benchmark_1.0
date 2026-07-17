/**
 * Market data types.
 * Plain TypeScript interfaces — not Zod-dependent.
 */

export interface PricePoint {
  /** ISO date string, e.g. "2026-05-07". */
  date: string;
  /** Opening price. */
  open: number;
  /** Intraday high price. */
  high: number;
  /** Intraday low price. */
  low: number;
  /** Adjusted closing price (split- and dividend-adjusted). */
  close: number;
  /** Daily trading volume. */
  volume: number;
}

/** A named series of daily price points for a single ticker. */
export interface PriceSeries {
  ticker: string;
  points: PricePoint[];
}

/**
 * Asset metadata fetched from the Alpha Vantage OVERVIEW endpoint.
 * Cached in KV under key `meta:{ticker}` with a 7-day TTL.
 */
export interface AssetMetadata {
  ticker: string;
  /** Full company name. */
  name: string;
  /** GICS sector, e.g. "Technology". */
  sector: string;
  /** GICS industry group. */
  industry: string;
  /**
   * Market capitalisation tier.
   * mega: >$200B, large: $10B-$200B, mid: $2B-$10B,
   * small: $300M-$2B, micro: <$300M.
   */
  market_cap_tier: "mega" | "large" | "mid" | "small" | "micro";
  /** Raw market cap in USD. */
  market_cap: number;
  /** Two-letter ISO 3166-1 country code for primary listing. */
  country: string;
  /** Asset class, e.g. "equity", "etf", "reit". */
  asset_class: string;
}

/** price_history tool output. */
export interface PriceHistoryResult {
  /** Ticker -> array of price points. */
  data: Record<string, PricePoint[]>;
  /** Human-readable summary. */
  summary: string;
}

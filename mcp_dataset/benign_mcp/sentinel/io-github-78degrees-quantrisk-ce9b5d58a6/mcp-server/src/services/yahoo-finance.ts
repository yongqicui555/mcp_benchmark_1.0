/**
 * YahooFinanceService — fetches daily price data and asset metadata from
 * Yahoo Finance via the `yahoo-finance2` npm package, caching results in
 * Cloudflare KV.
 *
 * Cache key patterns (unchanged from the previous Alpha Vantage backend so
 * already-warm cache entries remain valid):
 *   price:{TICKER}:{YYYY-MM-DD}  — full daily OHLCV series, TTL 24h
 *   meta:{TICKER}                — sector, market cap, name, TTL 7 days
 *
 * Public surface mirrors the old AlphaVantageService so call sites in
 * src/tools/ are drop-in compatible: fetchDailyPrices, fetchAssetMetadata,
 * fetchMultiplePrices.
 *
 * Errors propagate as DataFetchError; callers handle fallbacks.
 */

import YahooFinance from "yahoo-finance2";
import { DataFetchError } from "../utils/errors.js";

// ---------------------------------------------------------------------------
// Env bindings (injected via constructor)
// ---------------------------------------------------------------------------

export interface YahooFinanceEnv {
  PRICE_CACHE: KVNamespace;
}

// ---------------------------------------------------------------------------
// Domain types — identical to the old service so consumers don't change
// ---------------------------------------------------------------------------

export interface PricePoint {
  date: string;   // ISO YYYY-MM-DD
  open: number;
  high: number;
  low: number;
  close: number;  // adjusted close
  volume: number;
}

export interface AssetMetadata {
  ticker: string;
  name: string;
  sector: string;       // GICS sector name, or "Unknown" if unavailable
  marketCap: number;    // in USD; 0 if unavailable
  exchange: string;
  currency: string;
  description: string;
}

// ---------------------------------------------------------------------------
// TTLs and constants
// ---------------------------------------------------------------------------

const PRICE_TTL_SECONDS = 60 * 60 * 24;          // 24 hours
const META_TTL_SECONDS  = 60 * 60 * 24 * 7;       // 7 days

// Yahoo's chart API serves daily bars from `period1` (inclusive) to `period2`
// (exclusive). Trading-day count is roughly 252/year, so 1.6× gives plenty of
// calendar buffer for the ~70% of days that are trading days.
const CALENDAR_DAY_BUFFER = 1.6;

// ---------------------------------------------------------------------------
// Service class
// ---------------------------------------------------------------------------

type QuoteRow = {
  date:      Date;
  open:      number | null;
  high:      number | null;
  low:       number | null;
  close:     number | null;
  adjclose?: number | null;
  volume?:   number | null;
};

export class YahooFinanceService {
  private readonly kv: KVNamespace;
  private readonly client: InstanceType<typeof YahooFinance>;

  constructor(env: YahooFinanceEnv) {
    this.kv     = env.PRICE_CACHE;
    this.client = new YahooFinance({
      // Suppress the "yahoo-finance2 has a new survey notice" log line
      // and the runtime version-check log on cold start.
      suppressNotices: ["yahooSurvey", "ripHistorical"],
    });
  }

  // -------------------------------------------------------------------------
  // Public API
  // -------------------------------------------------------------------------

  /**
   * Fetch daily adjusted close prices for `ticker` going back `days` trading
   * days. Returns an array sorted oldest-first.
   */
  async fetchDailyPrices(ticker: string, days: number): Promise<PricePoint[]> {
    const todayKey = todayIso();
    const cacheKey = `price:${ticker}:${todayKey}`;

    const cached = await this.kv.get<PricePoint[]>(cacheKey, "json");
    if (cached !== null && cached.length >= days) {
      return cached.slice(-days);
    }

    const period2 = new Date();
    const period1 = new Date(
      period2.getTime() - Math.ceil(days * CALENDAR_DAY_BUFFER) * 24 * 60 * 60 * 1000
    );

    let result;
    try {
      result = await this.client.chart(ticker, {
        period1,
        period2,
        interval: "1d",
        return: "array",
      });
    } catch (err) {
      throw new DataFetchError(
        ticker,
        `Yahoo Finance error: ${err instanceof Error ? err.message : String(err)}`
      );
    }

    const quotes: QuoteRow[] = (result as { quotes?: QuoteRow[] } | undefined)?.quotes ?? [];
    if (quotes.length === 0) {
      throw new DataFetchError(ticker, "Empty time series returned by Yahoo Finance");
    }

    const points: PricePoint[] = quotes
      .filter((q: QuoteRow) => q.close !== null && q.open !== null && q.high !== null && q.low !== null)
      .map((q: QuoteRow) => ({
        date:   isoDate(q.date),
        open:   q.open  as number,
        high:   q.high  as number,
        low:    q.low   as number,
        // Prefer adjusted close (handles splits/dividends) — the original
        // AlphaVantageService also used adjusted close.
        close:  (q.adjclose ?? q.close) as number,
        volume: (q.volume ?? 0) as number,
      }));

    if (points.length === 0) {
      throw new DataFetchError(ticker, "All Yahoo Finance bars had null prices");
    }

    await this.kv.put(cacheKey, JSON.stringify(points), {
      expirationTtl: PRICE_TTL_SECONDS,
    });

    return points.slice(-days);
  }

  /**
   * Fetch sector, market cap, and name for `ticker`.
   * Pulls the `assetProfile`, `summaryDetail`, and `price` modules from
   * Yahoo's quoteSummary endpoint. Cache TTL 7 days.
   *
   * Yahoo's metadata endpoint requires a crumb cookie; if that lookup fails
   * (network, geo-block, schema drift) we fall back to a minimal record so
   * sector-exposure can still report "Unknown" without taking the whole
   * tool down.
   */
  async fetchAssetMetadata(ticker: string): Promise<AssetMetadata> {
    const cacheKey = `meta:${ticker}`;

    const cached = await this.kv.get<AssetMetadata>(cacheKey, "json");
    if (cached !== null) {
      return cached;
    }

    let meta: AssetMetadata;
    try {
      const summary = await this.client.quoteSummary(ticker, {
        modules: ["assetProfile", "summaryDetail", "price"],
      });

      const profile = summary?.assetProfile;
      const price   = summary?.price;
      const detail  = summary?.summaryDetail;

      meta = {
        ticker,
        name:        price?.longName ?? price?.shortName ?? ticker,
        sector:      profile?.sector ?? "Unknown",
        marketCap:   typeof price?.marketCap === "number"
                       ? price.marketCap
                       : (typeof detail?.marketCap === "number" ? detail.marketCap : 0),
        exchange:    price?.exchangeName ?? "Unknown",
        currency:    price?.currency ?? "USD",
        description: profile?.longBusinessSummary ?? "",
      };
    } catch (err) {
      // Don't block tools that don't strictly need metadata.
      meta = {
        ticker,
        name:        ticker,
        sector:      "Unknown",
        marketCap:   0,
        exchange:    "Unknown",
        currency:    "USD",
        description: "",
      };
    }

    await this.kv.put(cacheKey, JSON.stringify(meta), {
      expirationTtl: META_TTL_SECONDS,
    });

    return meta;
  }

  /**
   * Fetch prices for multiple tickers in parallel.
   * Returns a map of ticker -> PricePoint[].
   */
  async fetchMultiplePrices(
    tickers: string[],
    days: number
  ): Promise<Record<string, PricePoint[]>> {
    const unique = [...new Set(tickers)];
    const results = await Promise.all(
      unique.map(async (t) => [t, await this.fetchDailyPrices(t, days)] as const)
    );
    return Object.fromEntries(results);
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function todayIso(): string {
  return new Date().toISOString().slice(0, 10);
}

function isoDate(d: Date): string {
  return d.toISOString().slice(0, 10);
}

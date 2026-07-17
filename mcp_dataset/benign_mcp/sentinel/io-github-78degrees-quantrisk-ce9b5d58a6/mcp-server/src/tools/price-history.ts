/**
 * price-history.ts — MCP tool handler for `price_history`.
 *
 * Fetches raw OHLCV price data for one or more tickers and returns it
 * in the canonical PricePoint format.  Optionally aggregates daily bars
 * to weekly or monthly intervals.
 *
 * Tier gates (enforced by middleware BEFORE this handler is called):
 *   FREE  — max 1 ticker, max 252 days
 *   PAID  — up to 20 tickers, up to 1260 days
 *
 * Handler signature:
 *   handlePriceHistory(input, env, authContext) -> ToolResult
 */

import type { PriceHistoryInput } from "../schemas/price-history.js";
import type { AuthContext } from "../middleware/auth.js";
import type { PriceHistoryResult } from "../types/market-data.js";
import type { PricePoint } from "../types/market-data.js";

import { YahooFinanceService } from "../services/yahoo-finance.js";
import { toMcpError } from "../utils/errors.js";
import { formatCurrency } from "../utils/format.js";

// ---------------------------------------------------------------------------
// Env shape required by this tool
// ---------------------------------------------------------------------------

export interface Env {
  PRICE_CACHE: KVNamespace;
  USER_STATE: DurableObjectNamespace;
}

// ---------------------------------------------------------------------------
// ToolResult type
// ---------------------------------------------------------------------------

export interface ToolResult {
  content: [{ type: "text"; text: string }];
  isError?: boolean;
}

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

/**
 * Handle the `price_history` MCP tool.
 *
 * @param input        Validated input (parsed by Zod schema upstream).
 * @param env          Cloudflare Worker environment bindings.
 * @param authContext  Resolved auth/tier context from middleware.
 * @returns            ToolResult with JSON-serialised PriceHistoryResult.
 */
export async function handlePriceHistory(
  input: PriceHistoryInput,
  env: Env,
  _authContext: AuthContext
): Promise<ToolResult> {
  try {
    const { tickers, days, interval } = input;

    // ------------------------------------------------------------------
    // 1. Fetch daily price data for all requested tickers in parallel
    // ------------------------------------------------------------------
    const svc = new YahooFinanceService({
      PRICE_CACHE: env.PRICE_CACHE,
    });

    const priceMap = await svc.fetchMultiplePrices(tickers, days);

    // ------------------------------------------------------------------
    // 2. Aggregate to weekly / monthly if requested
    //    Daily interval: pass through as-is.
    // ------------------------------------------------------------------
    const data: Record<string, PricePoint[]> = {};

    for (const ticker of tickers) {
      const raw = priceMap[ticker] ?? [];

      if (raw.length === 0) {
        data[ticker] = [];
        continue;
      }

      switch (interval) {
        case "weekly":
          data[ticker] = aggregateToWeekly(raw);
          break;
        case "monthly":
          data[ticker] = aggregateToMonthly(raw);
          break;
        default:
          // "daily" — return as-is; YahooFinanceService already returns
          // PricePoint[] sorted oldest-first.
          data[ticker] = raw;
      }
    }

    // ------------------------------------------------------------------
    // 3. Build human-readable summary
    // ------------------------------------------------------------------
    const summary = buildSummary(tickers, data, interval, days);

    // ------------------------------------------------------------------
    // 4. Assemble and return result
    // ------------------------------------------------------------------
    const result: PriceHistoryResult = { data, summary };

    return {
      content: [{ type: "text", text: JSON.stringify(result) }],
    };
  } catch (err) {
    return toMcpError(err);
  }
}

// ---------------------------------------------------------------------------
// Aggregation helpers
// ---------------------------------------------------------------------------

/**
 * Group daily bars into ISO week buckets (Monday–Friday).
 * Each weekly bar uses:
 *   open  = first day's open
 *   high  = max high across the week
 *   low   = min low across the week
 *   close = last day's close
 *   volume = sum of daily volumes
 *   date  = date of the last day in the week
 */
function aggregateToWeekly(daily: PricePoint[]): PricePoint[] {
  const weeks = groupByKey(daily, (p) => isoWeekKey(p.date));
  return buildAggregatedBars(weeks);
}

/**
 * Group daily bars into calendar-month buckets (YYYY-MM).
 * Same OHLCV aggregation rules as weekly.
 */
function aggregateToMonthly(daily: PricePoint[]): PricePoint[] {
  const months = groupByKey(daily, (p) => p.date.slice(0, 7));
  return buildAggregatedBars(months);
}

/** Generic group-by that preserves insertion order. */
function groupByKey(
  points: PricePoint[],
  keyFn: (p: PricePoint) => string
): Map<string, PricePoint[]> {
  const map = new Map<string, PricePoint[]>();
  for (const p of points) {
    const k = keyFn(p);
    const bucket = map.get(k);
    if (bucket) {
      bucket.push(p);
    } else {
      map.set(k, [p]);
    }
  }
  return map;
}

/** Collapse a map of grouped bars into a single PricePoint per bucket. */
function buildAggregatedBars(
  groups: Map<string, PricePoint[]>
): PricePoint[] {
  const result: PricePoint[] = [];
  for (const bucket of groups.values()) {
    if (bucket.length === 0) continue;
    result.push({
      date: bucket[bucket.length - 1].date,           // last day
      open: bucket[0].open,                            // first open
      high: Math.max(...bucket.map((p) => p.high)),
      low: Math.min(...bucket.map((p) => p.low)),
      close: bucket[bucket.length - 1].close,          // last close
      volume: bucket.reduce((s, p) => s + p.volume, 0),
    });
  }
  return result;
}

/**
 * Derive a sortable ISO week key (YYYY-Www) from an ISO date string.
 * This groups Mon-Sun into the same bucket.
 */
function isoWeekKey(dateStr: string): string {
  const d = new Date(dateStr);
  // Get Monday of the week
  const day = d.getUTCDay(); // 0 = Sunday
  const diff = (day === 0 ? -6 : 1 - day); // adjust to Monday
  d.setUTCDate(d.getUTCDate() + diff);
  const year = d.getUTCFullYear();
  const startOfYear = new Date(Date.UTC(year, 0, 1));
  const weekNo = Math.ceil(
    ((d.getTime() - startOfYear.getTime()) / 86_400_000 + startOfYear.getUTCDay() + 1) / 7
  );
  return `${year}-W${String(weekNo).padStart(2, "0")}`;
}

// ---------------------------------------------------------------------------
// Summary builder
// ---------------------------------------------------------------------------

function buildSummary(
  tickers: string[],
  data: Record<string, PricePoint[]>,
  interval: "daily" | "weekly" | "monthly",
  requestedDays: number
): string {
  const parts: string[] = [];

  for (const ticker of tickers) {
    const series = data[ticker];
    if (!series || series.length === 0) {
      parts.push(`${ticker}: no data available`);
      continue;
    }

    const first = series[0];
    const last = series[series.length - 1];
    const periodReturn = (last.close - first.open) / first.open;
    const direction = periodReturn >= 0 ? "gained" : "lost";
    const barLabel =
      interval === "daily"
        ? `${series.length} day`
        : interval === "weekly"
          ? `${series.length} week`
          : `${series.length} month`;

    parts.push(
      `${ticker}: ${barLabel} history from ${first.date} to ${last.date}. ` +
      `Latest close: ${formatCurrency(last.close)}. ` +
      `Period ${direction} ${Math.abs(periodReturn * 100).toFixed(2)}%.`
    );
  }

  return (
    `Price history (${interval}, ~${requestedDays} trading days requested).\n` +
    parts.join("\n")
  );
}

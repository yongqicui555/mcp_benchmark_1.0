/**
 * sector-exposure.ts — Tool handler for the `sector_exposure` MCP tool.
 *
 * Breaks down portfolio exposure by GICS sector and market cap tier:
 *   1. Fetches current prices to establish position values
 *   2. Maps each ticker to its GICS sector (sector-map.ts first, then
 *      Alpha Vantage OVERVIEW for any unknowns)
 *   3. Maps each ticker to a market cap tier using Alpha Vantage OVERVIEW
 *      (mega/large/mid/small/micro), falling back to "unknown" if unavailable
 *   4. Computes weights, dollar values, and HHI concentration index
 *   5. Returns SectorExposureResult with summary
 *
 * This tool is FREE tier — no tier gating beyond position count (handled upstream).
 * Auth and tier gating are handled upstream — this handler receives
 * pre-validated input and an already-resolved AuthContext.
 */

import type { SectorExposureInput } from "../schemas/sector-exposure.js";
import type { AuthContext } from "../middleware/auth.js";
import type { SectorExposureResult, ExposureBucket } from "../types/risk.js";
import { YahooFinanceService } from "../services/yahoo-finance.js";
import { getSectorForTicker } from "../data/sector-map.js";
import { formatCurrency, formatPercent, formatNumber } from "../utils/format.js";
import { toMcpError, ComputationError } from "../utils/errors.js";

// ---------------------------------------------------------------------------
// Env bindings required by this tool
// ---------------------------------------------------------------------------

export interface SectorExposureEnv {
  PRICE_CACHE: KVNamespace;
}

// ---------------------------------------------------------------------------
// MCP ToolResult shape
// ---------------------------------------------------------------------------

export interface ToolResult {
  content: [{ type: "text"; text: string }];
  isError?: boolean;
}

// ---------------------------------------------------------------------------
// Market cap tier thresholds (USD)
// ---------------------------------------------------------------------------

const MARKET_CAP_TIERS: Array<{ label: string; minUsd: number }> = [
  { label: "mega",  minUsd: 200_000_000_000 },   // >$200B
  { label: "large", minUsd:  10_000_000_000 },   // $10B – $200B
  { label: "mid",   minUsd:   2_000_000_000 },   // $2B – $10B
  { label: "small", minUsd:     300_000_000 },   // $300M – $2B
  { label: "micro", minUsd:               0 },   // <$300M
];

function classifyMarketCap(marketCapUsd: number): string {
  if (marketCapUsd <= 0) return "unknown";
  for (const tier of MARKET_CAP_TIERS) {
    if (marketCapUsd >= tier.minUsd) return tier.label;
  }
  return "micro";
}

// ---------------------------------------------------------------------------
// Handler
// ---------------------------------------------------------------------------

export async function handleSectorExposure(
  input: SectorExposureInput,
  env: SectorExposureEnv,
  _authContext: AuthContext
): Promise<ToolResult> {
  try {
    const { positions } = input;

    // ------------------------------------------------------------------
    // 1. Fetch current prices
    // ------------------------------------------------------------------
    const tickers = positions.map((p) => p.ticker.toUpperCase());
    const av = new YahooFinanceService(env);
    const priceMap = await av.fetchMultiplePrices(tickers, 2);

    // ------------------------------------------------------------------
    // 2. Compute position values
    // ------------------------------------------------------------------
    const positionData = positions.map((pos) => {
      const ticker = pos.ticker.toUpperCase();
      const series = priceMap[ticker];
      if (!series || series.length === 0) {
        throw new ComputationError(
          `No price data for ${ticker}. Cannot compute sector exposure.`
        );
      }
      const price = series[series.length - 1].close;
      const value = Math.abs(price * pos.quantity); // use absolute value for exposure
      return { ticker, value };
    });

    const totalValue = positionData.reduce((sum, p) => sum + p.value, 0);

    if (totalValue === 0) {
      throw new ComputationError("Total portfolio value is zero. Check position quantities.");
    }

    // Find the largest single position (by absolute weight)
    const largestPosition = positionData.reduce((a, b) => (a.value > b.value ? a : b));
    const largestPositionWeight = largestPosition.value / totalValue;

    // ------------------------------------------------------------------
    // 3. Resolve sectors and market cap tiers
    //    Sector: sector-map.ts (static) → Alpha Vantage OVERVIEW (dynamic)
    //    Market cap: Alpha Vantage OVERVIEW (dynamic) → "unknown" on failure
    // ------------------------------------------------------------------
    const sectorForTicker: Record<string, string> = {};
    const marketCapTierForTicker: Record<string, string> = {};

    // First pass: static sector map (no I/O)
    for (const pos of positionData) {
      const staticSector = getSectorForTicker(pos.ticker);
      if (staticSector !== "Unknown") {
        sectorForTicker[pos.ticker] = staticSector;
      }
    }

    // Determine which tickers still need metadata (sector unknown OR market cap needed)
    // We always want market cap, so we fetch metadata for all tickers
    // Use Promise.allSettled so a single failure doesn't abort the whole call
    const metaResults = await Promise.allSettled(
      positionData.map(async (pos) => {
        const meta = await av.fetchAssetMetadata(pos.ticker);
        return { ticker: pos.ticker, meta };
      })
    );

    for (const result of metaResults) {
      if (result.status === "fulfilled") {
        const { ticker, meta } = result.value;
        // Fill in sector if still unknown
        if (!sectorForTicker[ticker]) {
          sectorForTicker[ticker] = meta.sector ?? "Unknown";
        }
        // Market cap tier
        marketCapTierForTicker[ticker] = classifyMarketCap(meta.marketCap ?? 0);
      } else {
        // Metadata fetch failed — keep whatever sector we have (or "Unknown")
        // market cap tier will remain unset → handled below as "unknown"
      }
    }

    // Fill in any remaining unknowns
    for (const pos of positionData) {
      if (!sectorForTicker[pos.ticker]) sectorForTicker[pos.ticker] = "Unknown";
      if (!marketCapTierForTicker[pos.ticker]) marketCapTierForTicker[pos.ticker] = "unknown";
    }

    // ------------------------------------------------------------------
    // 4. Aggregate by sector
    // ------------------------------------------------------------------
    const sectorBuckets: Record<string, ExposureBucket> = {};

    for (const pos of positionData) {
      const sector = sectorForTicker[pos.ticker];
      if (!sectorBuckets[sector]) {
        sectorBuckets[sector] = { weight: 0, value: 0, tickers: [] };
      }
      sectorBuckets[sector].value += pos.value;
      sectorBuckets[sector].tickers.push(pos.ticker);
    }

    // Compute weights
    for (const sector of Object.keys(sectorBuckets)) {
      sectorBuckets[sector].weight = sectorBuckets[sector].value / totalValue;
    }

    // ------------------------------------------------------------------
    // 5. Aggregate by market cap tier
    // ------------------------------------------------------------------
    const marketCapBuckets: Record<string, ExposureBucket> = {};

    for (const pos of positionData) {
      const tier = marketCapTierForTicker[pos.ticker];
      if (!marketCapBuckets[tier]) {
        marketCapBuckets[tier] = { weight: 0, value: 0, tickers: [] };
      }
      marketCapBuckets[tier].value += pos.value;
      marketCapBuckets[tier].tickers.push(pos.ticker);
    }

    for (const tier of Object.keys(marketCapBuckets)) {
      marketCapBuckets[tier].weight = marketCapBuckets[tier].value / totalValue;
    }

    // ------------------------------------------------------------------
    // 6. HHI (Herfindahl-Hirschman Index) for sector concentration
    //    HHI = sum of squared market share weights (expressed as %, 0-10000)
    //    Higher = more concentrated
    // ------------------------------------------------------------------
    const hhiSector = Object.values(sectorBuckets).reduce((sum, bucket) => {
      const sharePercent = bucket.weight * 100;
      return sum + sharePercent * sharePercent;
    }, 0);

    // ------------------------------------------------------------------
    // 7. Round bucket values for output
    // ------------------------------------------------------------------
    const roundBuckets = (buckets: Record<string, ExposureBucket>) => {
      const out: Record<string, ExposureBucket> = {};
      for (const [key, b] of Object.entries(buckets)) {
        out[key] = {
          weight: round(b.weight, 4),
          value: round(b.value, 2),
          tickers: b.tickers.sort(),
        };
      }
      return out;
    };

    // ------------------------------------------------------------------
    // 8. Build summary and return
    // ------------------------------------------------------------------
    const summary = buildSummary({
      totalValue,
      sectorBuckets,
      marketCapBuckets,
      hhiSector,
      largestTicker: largestPosition.ticker,
      largestWeight: largestPositionWeight,
      positionCount: positions.length,
    });

    const result: SectorExposureResult = {
      by_sector: roundBuckets(sectorBuckets),
      by_market_cap: roundBuckets(marketCapBuckets),
      hhi_sector: round(hhiSector, 1),
      largest_single_position: {
        ticker: largestPosition.ticker,
        weight: round(largestPositionWeight, 4),
      },
      summary,
    };

    return {
      content: [{ type: "text", text: JSON.stringify(result) }],
    };
  } catch (err) {
    return toMcpError(err);
  }
}

// ---------------------------------------------------------------------------
// Summary builder
// ---------------------------------------------------------------------------

interface SummaryParams {
  totalValue: number;
  sectorBuckets: Record<string, ExposureBucket>;
  marketCapBuckets: Record<string, ExposureBucket>;
  hhiSector: number;
  largestTicker: string;
  largestWeight: number;
  positionCount: number;
}

function buildSummary(p: SummaryParams): string {
  const sectorCount = Object.keys(p.sectorBuckets).length;

  // Sort sectors by weight descending for the summary
  const sortedSectors = Object.entries(p.sectorBuckets)
    .sort(([, a], [, b]) => b.weight - a.weight)
    .slice(0, 3); // top 3 sectors

  const topSectorStr = sortedSectors
    .map(([name, b]) => `${name} (${formatPercent(b.weight)})`)
    .join(", ");

  // HHI interpretation
  let hhiLabel: string;
  if (p.hhiSector < 1000) {
    hhiLabel = "well-diversified";
  } else if (p.hhiSector < 2500) {
    hhiLabel = "moderately concentrated";
  } else {
    hhiLabel = "highly concentrated";
  }

  // Largest market cap tier
  const sortedCapTiers = Object.entries(p.marketCapBuckets)
    .sort(([, a], [, b]) => b.weight - a.weight);
  const dominantCapTier = sortedCapTiers[0];

  const lines: string[] = [
    `Sector exposure for ${p.positionCount} position${p.positionCount !== 1 ? "s" : ""}, ` +
      `total value ${formatCurrency(p.totalValue)}.`,

    `Spread across ${sectorCount} GICS sector${sectorCount !== 1 ? "s" : ""}. ` +
      `Top sectors: ${topSectorStr}.`,

    `Sector HHI: ${formatNumber(p.hhiSector, 0)} — ${hhiLabel}. ` +
      `(HHI < 1,000 = diversified, 1,000–2,500 = moderate, > 2,500 = concentrated.)`,

    `Largest single position: ${p.largestTicker} at ${formatPercent(p.largestWeight)} of portfolio.`,
  ];

  if (dominantCapTier) {
    lines.push(
      `Dominant market cap tier: ${dominantCapTier[0]} ` +
        `(${formatPercent(dominantCapTier[1].weight)}).`
    );
  }

  return lines.join(" ");
}

// ---------------------------------------------------------------------------
// Utility
// ---------------------------------------------------------------------------

function round(n: number, decimals: number): number {
  const factor = 10 ** decimals;
  return Math.round(n * factor) / factor;
}

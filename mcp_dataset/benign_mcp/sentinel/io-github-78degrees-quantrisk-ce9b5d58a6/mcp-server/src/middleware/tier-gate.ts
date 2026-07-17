/**
 * Tier-gate middleware for QuantRisk MCP.
 *
 * Checks:
 *   1. Is the tool available on the user's tier?
 *   2. Does the input exceed the tier's numeric limits (positions, paths, tickers, days)?
 *
 * Throws TierError (tool access) or TierLimitError (numeric limit) on violation.
 * Returns void on success — the caller proceeds to the tool handler.
 *
 * Import TIER_CONFIG from src/config/tiers.ts (written by Agent A).
 * If that file is not yet present, the fallback inline config below is used.
 */

import { TierError, TierLimitError } from "../utils/errors.js";
import type { UserTier } from "../services/stripe.js";

// ---------------------------------------------------------------------------
// Tier config — inline fallback so this file compiles stand-alone.
// When src/config/tiers.ts exists it should be imported instead.
// ---------------------------------------------------------------------------

const UPGRADE_URL = "https://quantrisk.dev/upgrade";

interface TierLimits {
  maxPositions: number;
  maxTickers: number;
  maxMonteCarloPaths: number;
  maxPriceHistoryTickers: number;
  maxPriceHistoryDays: number;
}

const FREE_LIMITS: TierLimits = {
  maxPositions:              20,
  maxTickers:                10,
  maxMonteCarloPaths:      1000,
  maxPriceHistoryTickers:     1,
  maxPriceHistoryDays:      252,
};

const PAID_LIMITS: TierLimits = {
  maxPositions:             500,
  maxTickers:                50,
  maxMonteCarloPaths:   100_000,
  maxPriceHistoryTickers:    20,
  maxPriceHistoryDays:     1260,
};

/** Tools that are ONLY available on the paid tier. */
const PAID_ONLY_TOOLS = new Set([
  "optimize_portfolio",
  "compare_portfolios",
  "calculate_greeks",
]);

/**
 * Free-tier tools that have feature restrictions beyond numeric limits.
 * Map: toolName -> list of blocked feature flags.
 */
const FREE_TIER_FEATURE_BLOCKS: Record<string, string[]> = {
  stress_test:             ["custom_shocks"],
  performance_attribution: ["factor_attribution"],  // full factor model = paid
};

// ---------------------------------------------------------------------------
// Input shapes we need to inspect (minimal — avoid importing heavy tool types)
// ---------------------------------------------------------------------------

type AnyToolInput = Record<string, unknown>;

// ---------------------------------------------------------------------------
// Main function
// ---------------------------------------------------------------------------

/**
 * Check whether the given tool + input combination is permitted for `userTier`.
 *
 * @param toolName  MCP tool name (e.g. "analyze_risk", "optimize_portfolio")
 * @param input     Raw parsed tool input object
 * @param userTier  The user's subscription tier
 * @throws TierError if the tool is paid-only and user is on free tier
 * @throws TierLimitError if a numeric input exceeds the tier limit
 */
export function checkTierAccess(
  toolName: string,
  input: AnyToolInput,
  userTier: UserTier
): void {
  const limits = userTier === "paid" ? PAID_LIMITS : FREE_LIMITS;

  // ------------------------------------------------------------------
  // 1. Is the tool paid-only?
  // ------------------------------------------------------------------
  if (PAID_ONLY_TOOLS.has(toolName) && userTier === "free") {
    throw new TierError(toolName, UPGRADE_URL);
  }

  // ------------------------------------------------------------------
  // 2. Numeric limits — positions
  // ------------------------------------------------------------------
  const positions = input.positions;
  if (Array.isArray(positions)) {
    if (positions.length > limits.maxPositions) {
      throw new TierLimitError(
        "positions",
        positions.length,
        limits.maxPositions,
        UPGRADE_URL
      );
    }
  }

  // ------------------------------------------------------------------
  // 3. Numeric limits — tickers (correlation_matrix, price_history, optimize_portfolio)
  // ------------------------------------------------------------------
  const tickers = input.tickers;
  if (Array.isArray(tickers)) {
    const limitForTool = toolName === "price_history"
      ? limits.maxPriceHistoryTickers
      : limits.maxTickers;

    if (tickers.length > limitForTool) {
      throw new TierLimitError(
        "tickers",
        tickers.length,
        limitForTool,
        UPGRADE_URL
      );
    }
  }

  // ------------------------------------------------------------------
  // 4. Numeric limits — Monte Carlo paths
  // ------------------------------------------------------------------
  if (toolName === "monte_carlo_simulation") {
    const numPaths = typeof input.num_paths === "number"
      ? input.num_paths
      : 10_000; // default

    if (numPaths > limits.maxMonteCarloPaths) {
      throw new TierLimitError(
        "Monte Carlo paths (num_paths)",
        numPaths,
        limits.maxMonteCarloPaths,
        UPGRADE_URL
      );
    }
  }

  // ------------------------------------------------------------------
  // 5. Numeric limits — price_history days
  // ------------------------------------------------------------------
  if (toolName === "price_history") {
    const days = typeof input.days === "number" ? input.days : 252; // default
    if (days > limits.maxPriceHistoryDays) {
      throw new TierLimitError(
        "price history days",
        days,
        limits.maxPriceHistoryDays,
        UPGRADE_URL
      );
    }
  }

  // ------------------------------------------------------------------
  // 6. Numeric limits — compare_portfolios (check each portfolio's positions)
  // ------------------------------------------------------------------
  if (toolName === "compare_portfolios") {
    const portfolios = input.portfolios;
    if (Array.isArray(portfolios)) {
      for (const p of portfolios) {
        if (
          p &&
          typeof p === "object" &&
          Array.isArray((p as AnyToolInput).positions)
        ) {
          const pos = (p as AnyToolInput).positions as unknown[];
          if (pos.length > limits.maxPositions) {
            throw new TierLimitError(
              `positions in portfolio "${String((p as AnyToolInput).name ?? "")}"`,
              pos.length,
              limits.maxPositions,
              UPGRADE_URL
            );
          }
        }
      }
    }
  }

  // ------------------------------------------------------------------
  // 7. Feature flags — blocked features within partially-available tools
  // ------------------------------------------------------------------
  if (userTier === "free") {
    const blockedFeatures = FREE_TIER_FEATURE_BLOCKS[toolName];
    if (blockedFeatures) {
      for (const feature of blockedFeatures) {
        // If the feature field is present and non-null/non-empty, block it
        const val = input[feature];
        const isProvided =
          val !== undefined &&
          val !== null &&
          !(Array.isArray(val) && val.length === 0);

        if (isProvided) {
          throw new TierLimitError(
            feature,
            1,       // "you sent this feature"
            0,       // "free tier allows 0 of this"
            UPGRADE_URL
          );
        }
      }
    }
  }
}

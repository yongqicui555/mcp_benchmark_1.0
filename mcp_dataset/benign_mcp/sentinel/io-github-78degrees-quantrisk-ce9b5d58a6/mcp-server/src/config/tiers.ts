import { TierConfig, TierLimits, UserTier } from "../types/tiers.js";

// ─── Tool name constants ─────────────────────────────────────────────────────

/** All 10 MCP tool names. */
export const ALL_TOOLS = new Set([
  "analyze_risk",
  "monte_carlo_simulation",
  "stress_test",
  "optimize_portfolio",
  "correlation_matrix",
  "performance_attribution",
  "sector_exposure",
  "price_history",
  "compare_portfolios",
  "calculate_greeks",
]);

/** Tools available on the free tier. */
export const FREE_TOOLS = new Set([
  "analyze_risk",
  "monte_carlo_simulation",
  "stress_test",
  "correlation_matrix",
  "performance_attribution",
  "sector_exposure",
  "price_history",
]);

/** Tools that require a paid subscription. */
export const PAID_ONLY_TOOLS = new Set([
  "optimize_portfolio",
  "compare_portfolios",
  "calculate_greeks",
]);

// ─── Position / path hard caps (absolute maximums regardless of tier) ────────

export const MAX_POSITIONS = 500 as const;
export const MAX_MONTE_CARLO_PATHS = 100_000 as const;
export const MAX_CORRELATION_TICKERS = 50 as const;
export const MAX_PRICE_HISTORY_TICKERS = 20 as const;
export const MAX_PRICE_HISTORY_DAYS = 1260 as const;

// ─── Free tier ───────────────────────────────────────────────────────────────

export const freeTierLimits: TierLimits = {
  maxPositions: 20,
  maxCorrelationTickers: 10,
  maxMonteCarloPaths: 1_000,
  maxPriceHistoryTickers: 1,
  maxPriceHistoryDays: 252,
  rateLimitPerMinute: 10,
  rateLimitPerDay: 100,
  customStressScenarios: false,
  fullFactorAttribution: false,
  availableTools: FREE_TOOLS,
};

export const FREE_TIER_CONFIG: TierConfig = {
  tier: UserTier.FREE,
  priceUsdCents: 0,
  limits: freeTierLimits,
};

// ─── Paid tier ($29/month) ───────────────────────────────────────────────────

export const paidTierLimits: TierLimits = {
  maxPositions: 500,
  maxCorrelationTickers: 50,
  maxMonteCarloPaths: 100_000,
  maxPriceHistoryTickers: 20,
  maxPriceHistoryDays: 1260,
  rateLimitPerMinute: 60,
  rateLimitPerDay: 5_000,
  customStressScenarios: true,
  fullFactorAttribution: true,
  availableTools: ALL_TOOLS,
};

export const PAID_TIER_CONFIG: TierConfig = {
  tier: UserTier.PAID,
  priceUsdCents: 2_900, // $29.00 / month
  limits: paidTierLimits,
};

// ─── Lookup helper ───────────────────────────────────────────────────────────

/** Returns the TierConfig for a given UserTier value. */
export function getTierConfig(tier: UserTier): TierConfig {
  switch (tier) {
    case UserTier.PAID:
      return PAID_TIER_CONFIG;
    case UserTier.FREE:
    default:
      return FREE_TIER_CONFIG;
  }
}

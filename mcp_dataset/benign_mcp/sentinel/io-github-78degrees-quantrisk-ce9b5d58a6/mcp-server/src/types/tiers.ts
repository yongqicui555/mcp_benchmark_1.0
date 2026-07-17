/**
 * Tier system types.
 * Plain TypeScript — no Zod dependency.
 */

// ─── Enums ───────────────────────────────────────────────────────────────────

export enum UserTier {
  FREE = "free",
  PAID = "paid",
}

// ─── Limit shapes ────────────────────────────────────────────────────────────

export interface TierLimits {
  /** Maximum positions allowed per tool call. */
  maxPositions: number;
  /** Maximum tickers allowed for correlation_matrix. */
  maxCorrelationTickers: number;
  /** Maximum Monte Carlo paths. */
  maxMonteCarloPaths: number;
  /** Maximum tickers for price_history. */
  maxPriceHistoryTickers: number;
  /** Maximum lookback days for price_history. */
  maxPriceHistoryDays: number;
  /** Calls allowed per minute. */
  rateLimitPerMinute: number;
  /** Calls allowed per day. */
  rateLimitPerDay: number;
  /** Whether custom stress-test shocks are permitted. */
  customStressScenarios: boolean;
  /** Whether full factor attribution is available in performance_attribution. */
  fullFactorAttribution: boolean;
  /** Set of tool names that are accessible. All tools accessible on paid. */
  availableTools: Set<string>;
}

// ─── Full tier config (limits + metadata) ────────────────────────────────────

export interface TierConfig {
  tier: UserTier;
  /** Monthly price in USD cents (0 for free). */
  priceUsdCents: number;
  limits: TierLimits;
}

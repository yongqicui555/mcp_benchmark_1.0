import { UserTier } from "../types/tiers.js";

// ─── Shape ───────────────────────────────────────────────────────────────────

export interface RateLimitConfig {
  /** Maximum calls allowed in any 60-second rolling window. */
  callsPerMinute: number;
  /** Maximum calls allowed per calendar day (resets midnight UTC). */
  callsPerDay: number;
  /**
   * Burst allowance: how many extra calls are permitted in a 10-second window
   * before throttling kicks in. Helps absorb short spikes without rejecting legit requests.
   */
  burstWindow10s: number;
  /**
   * Retry-After header value (seconds) to return when the per-minute limit is hit.
   * Tells the client how long to wait before retrying.
   */
  retryAfterSeconds: number;
}

// ─── Per-tier configs ────────────────────────────────────────────────────────

export const FREE_RATE_LIMIT_CONFIG: RateLimitConfig = {
  callsPerMinute: 10,
  callsPerDay: 100,
  burstWindow10s: 3,
  retryAfterSeconds: 60,
};

export const PAID_RATE_LIMIT_CONFIG: RateLimitConfig = {
  callsPerMinute: 60,
  callsPerDay: 5_000,
  burstWindow10s: 15,
  retryAfterSeconds: 10,
};

// ─── Lookup helper ───────────────────────────────────────────────────────────

/** Returns the RateLimitConfig for a given UserTier. */
export function getRateLimitConfig(tier: UserTier): RateLimitConfig {
  switch (tier) {
    case UserTier.PAID:
      return PAID_RATE_LIMIT_CONFIG;
    case UserTier.FREE:
    default:
      return FREE_RATE_LIMIT_CONFIG;
  }
}

// ─── Durable Object alarm interval ──────────────────────────────────────────

/**
 * Milliseconds until midnight UTC from the given timestamp.
 * Used to schedule the Durable Object alarm that resets daily call counters.
 */
export function msUntilMidnightUtc(nowMs: number = Date.now()): number {
  const now = new Date(nowMs);
  const midnight = new Date(
    Date.UTC(now.getUTCFullYear(), now.getUTCMonth(), now.getUTCDate() + 1, 0, 0, 0, 0)
  );
  return midnight.getTime() - nowMs;
}

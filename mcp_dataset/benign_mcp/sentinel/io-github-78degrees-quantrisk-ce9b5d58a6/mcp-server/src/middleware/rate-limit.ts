/**
 * Rate-limiting middleware for QuantRisk MCP.
 *
 * Enforces two windows per user:
 *   - Per-minute:  burstable, resets every 60 seconds
 *   - Per-day:     total daily budget, resets at midnight UTC (via DO alarm)
 *
 * Limits by tier:
 *   Free  — 10 calls/minute, 100 calls/day
 *   Paid  — 60 calls/minute, 5,000 calls/day
 *
 * State is stored in the UserState Durable Object, which owns the counters
 * and the alarm for daily resets. This file delegates the actual counter
 * mutation to the DO via internal HTTP.
 *
 * Throws RateLimitError with retry-after information on violation.
 */

import { RateLimitError } from "../utils/errors.js";
import type { UserTier } from "../services/stripe.js";

// ---------------------------------------------------------------------------
// Env bindings
// ---------------------------------------------------------------------------

export interface RateLimitEnv {
  USER_STATE: DurableObjectNamespace;
}

// ---------------------------------------------------------------------------
// Tier rate limits — duplicated inline so this file is self-contained.
// The canonical definition lives in src/config/rate-limits.ts (Agent A).
// ---------------------------------------------------------------------------

interface RateLimitConfig {
  perMinute: number;
  perDay: number;
}

const RATE_LIMITS: Record<UserTier, RateLimitConfig> = {
  free: { perMinute: 10,  perDay:    100 },
  paid: { perMinute: 60,  perDay:  5_000 },
};

// ---------------------------------------------------------------------------
// Response from the Durable Object's increment endpoint
// ---------------------------------------------------------------------------

interface IncrementResponse {
  allowed: boolean;
  /** "minute" or "day" — which window was exceeded, if any */
  exceededWindow: "minute" | "day" | null;
  minuteCount: number;
  dayCount: number;
  minuteResetAt: number;   // Unix timestamp (seconds)
  dayResetAt: number;      // Unix timestamp (seconds) — midnight UTC
}

// ---------------------------------------------------------------------------
// Main function
// ---------------------------------------------------------------------------

/**
 * Check and increment the rate limit counters for a user.
 *
 * Must be called AFTER auth (so we have `userId` and `userTier`).
 * Must be called BEFORE the tool handler.
 *
 * @param userId   Stable user identifier (API key hash or "anon:<ip>")
 * @param userTier The user's subscription tier
 * @param env      Environment bindings (USER_STATE DO namespace)
 * @throws RateLimitError if any window is exceeded
 */
export async function checkRateLimit(
  userId: string,
  userTier: UserTier,
  env: RateLimitEnv
): Promise<void> {
  const limits = RATE_LIMITS[userTier];

  // Locate the UserState DO for this user
  const doId = env.USER_STATE.idFromName(userId);
  const stub = env.USER_STATE.get(doId);

  // Ask the DO to increment counters and report whether the request is allowed.
  // The DO performs the check + increment atomically, so there's no TOCTOU race.
  const response = await stub.fetch(
    new Request("https://user-state/increment", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ limits }),
    })
  );

  if (!response.ok) {
    // If the DO itself errors, fail open to avoid blocking legitimate users.
    // This is a deliberate tradeoff — a DO crash should not bring down the service.
    console.error(
      `[rate-limit] UserState DO returned ${response.status} for userId=${userId}. Failing open.`
    );
    return;
  }

  const result = await response.json<IncrementResponse>();

  if (!result.allowed && result.exceededWindow) {
    const retryAfter =
      result.exceededWindow === "minute"
        ? result.minuteResetAt
        : result.dayResetAt;

    const limit =
      result.exceededWindow === "minute"
        ? limits.perMinute
        : limits.perDay;

    throw new RateLimitError(result.exceededWindow, limit, retryAfter);
  }
}

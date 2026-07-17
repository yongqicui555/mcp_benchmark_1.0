/**
 * Authentication middleware for QuantRisk MCP.
 *
 * Two code paths:
 *
 * 1. Authenticated — request carries a Bearer token in the Authorization header.
 *    The token is looked up against the UserState Durable Object.
 *    Returns { userId, email, tier, stripeCustomerId }.
 *
 * 2. Unauthenticated — no Authorization header present.
 *    Treated as a free-tier anonymous user, identified by client IP.
 *    Rate limiting still applies (via IP-keyed Durable Object lookup).
 *
 * Throws AuthError for malformed or invalid tokens.
 */

import { AuthError } from "../utils/errors.js";
import type { UserTier } from "../services/stripe.js";

// ---------------------------------------------------------------------------
// Env shape expected by this middleware
// ---------------------------------------------------------------------------

export interface AuthEnv {
  /** Durable Object namespace for UserState. */
  USER_STATE: DurableObjectNamespace;
}

// ---------------------------------------------------------------------------
// Result type returned to the tool handler
// ---------------------------------------------------------------------------

export interface AuthContext {
  /** Internal user ID (same as the API key for simplicity, or a separate UUID). */
  userId: string;
  email: string | null;
  tier: UserTier;
  stripeCustomerId: string | null;
  /** True for IP-based anonymous users (no API key supplied). */
  isAnonymous: boolean;
}

// ---------------------------------------------------------------------------
// Main function
// ---------------------------------------------------------------------------

/**
 * Authenticate the incoming MCP request.
 *
 * @param request  The incoming Cloudflare Workers Request.
 * @param env      Environment bindings (needs USER_STATE DO namespace).
 * @returns        Resolved AuthContext.
 * @throws         AuthError if the token is malformed or not found.
 */
export async function authenticateRequest(
  request: Request,
  env: AuthEnv
): Promise<AuthContext> {
  const authHeader = request.headers.get("Authorization");

  // ------------------------------------------------------------------
  // Path 1: Unauthenticated / anonymous
  // ------------------------------------------------------------------
  if (!authHeader) {
    return buildAnonymousContext(request);
  }

  // ------------------------------------------------------------------
  // Path 2: Bearer token present
  // ------------------------------------------------------------------
  if (!authHeader.startsWith("Bearer ")) {
    throw new AuthError(
      "Malformed Authorization header. Expected format: \"Authorization: Bearer <api-key>\""
    );
  }

  const apiKey = authHeader.slice("Bearer ".length).trim();

  if (!apiKey || apiKey.length < 20) {
    throw new AuthError("API key is too short or missing. Generate a key at https://quantrisk.dev/keys");
  }

  // Derive a stable Durable Object ID from the API key.
  const doId  = env.USER_STATE.idFromName(apiKey);
  const stub  = env.USER_STATE.get(doId);

  // Ask the DO whether this key has actually been issued (and not revoked).
  // /validate-key returns valid=false for any DO that was auto-initialised on
  // first access — i.e., for any key the user invented but never paid for.
  const validateResponse = await stub.fetch(
    new Request("https://user-state/validate-key", { method: "GET" })
  );

  if (!validateResponse.ok) {
    throw new AuthError("Failed to validate API key. Please try again.");
  }

  const validation = await validateResponse.json<ValidateKeyResponse>();

  if (!validation.valid) {
    throw new AuthError(
      "Invalid or revoked API key. Subscribe to QuantRisk Pro at https://quantrisk.dev/upgrade to get a key."
    );
  }

  return {
    userId:           apiKey,
    email:            validation.email,
    tier:             validation.tier ?? "free",
    stripeCustomerId: validation.stripeCustomerId,
    isAnonymous:      false,
  };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Build an anonymous AuthContext keyed by client IP address.
 * All anonymous users are treated as free-tier with no Stripe identity.
 */
function buildAnonymousContext(request: Request): AuthContext {
  // CF-Connecting-IP is set by Cloudflare's edge for every real request.
  const ip =
    request.headers.get("CF-Connecting-IP") ??
    request.headers.get("X-Forwarded-For")?.split(",")[0].trim() ??
    "unknown";

  return {
    userId:           `anon:${ip}`,
    email:            null,
    tier:             "free",
    stripeCustomerId: null,
    isAnonymous:      true,
  };
}

// ---------------------------------------------------------------------------
// Minimal snapshot type from UserState DO
// ---------------------------------------------------------------------------

/**
 * The shape returned by the UserState DO's GET /validate-key endpoint.
 * Defined here to avoid a circular import from src/auth/user-state.ts.
 */
interface ValidateKeyResponse {
  valid: boolean;
  tier: UserTier | null;
  email: string | null;
  stripeCustomerId: string | null;
}

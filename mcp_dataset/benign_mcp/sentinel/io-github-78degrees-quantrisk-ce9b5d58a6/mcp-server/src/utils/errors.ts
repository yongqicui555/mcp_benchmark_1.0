/**
 * Typed error classes for QuantRisk MCP.
 * All errors carry a machine-readable `code` matching the spec's error code enum,
 * a human-readable `message`, and an optional `upgradeUrl` for tier-related errors.
 *
 * Error codes (per Appendix C):
 *   TIER_LIMIT_EXCEEDED   — input exceeds a free-tier numeric limit
 *   TIER_REQUIRED         — tool is paid-only, user is on free tier
 *   RATE_LIMITED          — per-minute or per-day call budget exhausted
 *   INVALID_INPUT         — request fails validation (bad ticker, bad date, etc.)
 *   DATA_FETCH_FAILED     — external data source (Alpha Vantage) unavailable
 *   COMPUTATION_ERROR     — internal math/engine failure
 *   AUTH_REQUIRED         — missing or invalid API key
 */

export type QuantRiskErrorCode =
  | "TIER_LIMIT_EXCEEDED"
  | "TIER_REQUIRED"
  | "RATE_LIMITED"
  | "INVALID_INPUT"
  | "DATA_FETCH_FAILED"
  | "COMPUTATION_ERROR"
  | "AUTH_REQUIRED";

/** Serialised shape placed inside MCP error content. */
export interface QuantRiskErrorPayload {
  error: QuantRiskErrorCode;
  message: string;
  upgrade_url?: string;
  [key: string]: unknown;
}

/** Base class — all QuantRisk errors extend this. */
export class QuantRiskError extends Error {
  readonly code: QuantRiskErrorCode;
  readonly upgradeUrl?: string;

  constructor(code: QuantRiskErrorCode, message: string, upgradeUrl?: string) {
    super(message);
    this.name = "QuantRiskError";
    this.code = code;
    this.upgradeUrl = upgradeUrl;
    // Maintain correct prototype chain for `instanceof` checks in Workers runtime.
    Object.setPrototypeOf(this, new.target.prototype);
  }

  /** Produces the structured payload consumed by MCP error responses (Appendix C). */
  toPayload(): QuantRiskErrorPayload {
    const payload: QuantRiskErrorPayload = {
      error: this.code,
      message: this.message,
    };
    if (this.upgradeUrl) {
      payload.upgrade_url = this.upgradeUrl;
    }
    return payload;
  }
}

// ---------------------------------------------------------------------------
// Concrete error classes
// ---------------------------------------------------------------------------

/**
 * Thrown when the user's tier does not permit a specific tool.
 *
 * @example
 *   throw new TierError("optimize_portfolio");
 */
export class TierError extends QuantRiskError {
  readonly tool: string;

  constructor(tool: string, upgradeUrl = "https://quantrisk.dev/upgrade") {
    super(
      "TIER_REQUIRED",
      `The tool "${tool}" requires a paid subscription. Upgrade at ${upgradeUrl}`,
      upgradeUrl
    );
    this.name = "TierError";
    this.tool = tool;
  }

  toPayload(): QuantRiskErrorPayload {
    return { ...super.toPayload(), tool: this.tool };
  }
}

/**
 * Thrown when a numeric input (positions count, path count, etc.) exceeds
 * what the user's tier allows.
 *
 * @example
 *   throw new TierLimitError("positions", 45, 20);
 */
export class TierLimitError extends QuantRiskError {
  readonly limitName: string;
  readonly actual: number;
  readonly limit: number;

  constructor(
    limitName: string,
    actual: number,
    limit: number,
    upgradeUrl = "https://quantrisk.dev/upgrade"
  ) {
    super(
      "TIER_LIMIT_EXCEEDED",
      `Free tier allows max ${limit} ${limitName}. You sent ${actual}. Upgrade at ${upgradeUrl}`,
      upgradeUrl
    );
    this.name = "TierLimitError";
    this.limitName = limitName;
    this.actual = actual;
    this.limit = limit;
  }

  toPayload(): QuantRiskErrorPayload {
    return {
      ...super.toPayload(),
      limit_name: this.limitName,
      actual: this.actual,
      limit: this.limit,
    };
  }
}

/**
 * Thrown when a user has exceeded their per-minute or per-day call budget.
 *
 * @example
 *   throw new RateLimitError("minute", 10, 60);
 */
export class RateLimitError extends QuantRiskError {
  readonly window: "minute" | "day";
  readonly limit: number;
  /** Unix timestamp (seconds) after which the budget resets. */
  readonly retryAfter: number;

  constructor(window: "minute" | "day", limit: number, retryAfter: number) {
    const windowLabel = window === "minute" ? "per-minute" : "daily";
    super(
      "RATE_LIMITED",
      `${windowLabel} call limit of ${limit} reached. Retry after ${new Date(retryAfter * 1000).toISOString()}`
    );
    this.name = "RateLimitError";
    this.window = window;
    this.limit = limit;
    this.retryAfter = retryAfter;
  }

  toPayload(): QuantRiskErrorPayload {
    return {
      ...super.toPayload(),
      window: this.window,
      limit: this.limit,
      retry_after: this.retryAfter,
    };
  }
}

/**
 * Thrown when an external data source (Alpha Vantage) fails or is unavailable.
 *
 * @example
 *   throw new DataFetchError("AAPL", "API rate limit exceeded");
 */
export class DataFetchError extends QuantRiskError {
  readonly ticker?: string;

  constructor(tickerOrContext: string, detail?: string) {
    const msg = detail
      ? `Failed to fetch data for ${tickerOrContext}: ${detail}. Please try again in a few minutes.`
      : `Failed to fetch market data: ${tickerOrContext}. Please try again in a few minutes.`;
    super("DATA_FETCH_FAILED", msg);
    this.name = "DataFetchError";
    // If the first arg looks like a ticker (short, uppercase) treat it as one.
    if (/^[A-Z]{1,10}$/.test(tickerOrContext)) {
      this.ticker = tickerOrContext;
    }
  }

  toPayload(): QuantRiskErrorPayload {
    const base = super.toPayload();
    if (this.ticker) {
      return { ...base, ticker: this.ticker };
    }
    return base;
  }
}

/**
 * Thrown when an internal computation fails (e.g., singular covariance matrix,
 * optimizer convergence failure, etc.).
 */
export class ComputationError extends QuantRiskError {
  readonly detail?: string;

  constructor(message: string, detail?: string) {
    super("COMPUTATION_ERROR", message);
    this.name = "ComputationError";
    this.detail = detail;
  }

  toPayload(): QuantRiskErrorPayload {
    const base = super.toPayload();
    if (this.detail) {
      return { ...base, detail: this.detail };
    }
    return base;
  }
}

/**
 * Thrown when the API key is missing, expired, or invalid.
 */
export class AuthError extends QuantRiskError {
  constructor(message = "Authentication required. Provide a valid API key in the Authorization header as a Bearer token.") {
    super("AUTH_REQUIRED", message);
    this.name = "AuthError";
  }
}

/**
 * Thrown when user input fails validation (bad ticker format, invalid date, etc.).
 *
 * @example
 *   throw new InvalidInputError("ticker", "aapl", "Must be uppercase 1-10 chars");
 */
export class InvalidInputError extends QuantRiskError {
  readonly field?: string;
  readonly received?: unknown;

  constructor(field: string, received?: unknown, detail?: string) {
    const msg = detail
      ? `Invalid value for "${field}": ${detail}`
      : `Invalid value for "${field}"${received !== undefined ? `: received ${JSON.stringify(received)}` : ""}`;
    super("INVALID_INPUT", msg);
    this.name = "InvalidInputError";
    this.field = field;
    this.received = received;
  }

  toPayload(): QuantRiskErrorPayload {
    return {
      ...super.toPayload(),
      field: this.field,
      received: this.received,
    };
  }
}

// ---------------------------------------------------------------------------
// Helper: convert any error to a structured MCP error content block
// ---------------------------------------------------------------------------

/**
 * Normalises any thrown value into a structured MCP error response body.
 * Preserves typed payload for QuantRiskError subclasses; wraps unknown errors
 * in a generic COMPUTATION_ERROR envelope.
 */
export function toMcpError(err: unknown): { isError: true; content: [{ type: "text"; text: string }] } {
  let payload: QuantRiskErrorPayload;

  if (err instanceof QuantRiskError) {
    payload = err.toPayload();
  } else if (err instanceof Error) {
    payload = {
      error: "COMPUTATION_ERROR",
      message: err.message,
    };
  } else {
    payload = {
      error: "COMPUTATION_ERROR",
      message: "An unexpected error occurred.",
    };
  }

  return {
    isError: true,
    content: [{ type: "text", text: JSON.stringify(payload) }],
  };
}

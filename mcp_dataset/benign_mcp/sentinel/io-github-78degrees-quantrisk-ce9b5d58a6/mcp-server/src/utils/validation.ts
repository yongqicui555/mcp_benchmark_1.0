/**
 * Lightweight validation helpers for QuantRisk MCP.
 *
 * These are NOT Zod schemas — they are plain boolean/throwing helpers
 * used in service and middleware code where we want typed errors rather
 * than Zod parse errors. The canonical Zod schemas live in src/schemas/.
 */

import { InvalidInputError } from "./errors.js";

// ---------------------------------------------------------------------------
// Ticker validation
// ---------------------------------------------------------------------------

/** Regex: uppercase letters only, 1–10 characters. */
const TICKER_RE = /^[A-Z]{1,10}$/;

/**
 * Returns true if `s` is a valid ticker symbol.
 * Valid: uppercase letters only, 1–10 chars (e.g. "AAPL", "BRK.A" is NOT valid here).
 * The spec explicitly says uppercase 1-10 chars — no dots, no hyphens.
 */
export function isValidTicker(s: string): boolean {
  return TICKER_RE.test(s);
}

/**
 * Assert that `s` is a valid ticker symbol.
 * Throws `InvalidInputError` if not.
 */
export function validateTicker(s: string, fieldName = "ticker"): void {
  if (!isValidTicker(s)) {
    throw new InvalidInputError(
      fieldName,
      s,
      "Must be uppercase letters only, 1-10 characters (e.g. \"AAPL\", \"SPY\")"
    );
  }
}

// ---------------------------------------------------------------------------
// Date validation
// ---------------------------------------------------------------------------

/** Regex: strict ISO 8601 date — YYYY-MM-DD. Does not validate calendar correctness. */
const ISO_DATE_RE = /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/;

/**
 * Returns true if `s` is a valid ISO date string in YYYY-MM-DD format.
 * Also verifies the date is a real calendar date (no Feb 30, etc.).
 */
export function isValidDate(s: string): boolean {
  if (!ISO_DATE_RE.test(s)) return false;
  // Verify calendar validity via Date parse
  const d = new Date(s);
  return !isNaN(d.getTime());
}

/**
 * Assert that `s` is a valid ISO date string.
 * Throws `InvalidInputError` if not.
 */
export function validateDate(s: string, fieldName = "date"): void {
  if (!isValidDate(s)) {
    throw new InvalidInputError(
      fieldName,
      s,
      "Must be a valid ISO date in YYYY-MM-DD format (e.g. \"2026-01-15\")"
    );
  }
}

/**
 * Assert that `s` is a valid ISO date AND is in the future relative to now.
 * Used for option expiry validation.
 * Throws `InvalidInputError` if not valid or not future.
 */
export function validateFutureDate(s: string, fieldName = "expiry"): void {
  validateDate(s, fieldName);
  const d = new Date(s);
  const today = new Date();
  today.setUTCHours(0, 0, 0, 0);
  if (d <= today) {
    throw new InvalidInputError(
      fieldName,
      s,
      "Must be a future date (after today)"
    );
  }
}

// ---------------------------------------------------------------------------
// Numeric validation
// ---------------------------------------------------------------------------

/**
 * Returns true if `n` is a finite, positive number (> 0).
 */
export function isPositiveNumber(n: number): boolean {
  return typeof n === "number" && isFinite(n) && n > 0;
}

/**
 * Assert that `n` is a finite, positive number (> 0).
 * Throws `InvalidInputError` if not.
 */
export function validatePositiveNumber(n: number, fieldName = "value"): void {
  if (!isPositiveNumber(n)) {
    throw new InvalidInputError(
      fieldName,
      n,
      "Must be a finite positive number greater than 0"
    );
  }
}

/**
 * Assert that `n` is a finite number in the range [min, max] (inclusive).
 * Throws `InvalidInputError` if out of range or non-finite.
 */
export function validateNumberInRange(
  n: number,
  min: number,
  max: number,
  fieldName = "value"
): void {
  if (!isFinite(n) || n < min || n > max) {
    throw new InvalidInputError(
      fieldName,
      n,
      `Must be a finite number between ${min} and ${max} (inclusive)`
    );
  }
}

/**
 * Assert that `n` is a non-zero finite number (allows negative — useful for quantities).
 * Throws `InvalidInputError` if zero or non-finite.
 */
export function validateNonZeroNumber(n: number, fieldName = "quantity"): void {
  if (!isFinite(n) || n === 0) {
    throw new InvalidInputError(
      fieldName,
      n,
      "Must be a finite non-zero number (negative values indicate short positions)"
    );
  }
}

// ---------------------------------------------------------------------------
// Array validation
// ---------------------------------------------------------------------------

/**
 * Assert that `arr` has between `min` and `max` elements.
 * Throws `InvalidInputError` if not.
 */
export function validateArrayLength<T>(
  arr: T[],
  min: number,
  max: number,
  fieldName = "array"
): void {
  if (arr.length < min || arr.length > max) {
    throw new InvalidInputError(
      fieldName,
      arr.length,
      `Must have between ${min} and ${max} items (received ${arr.length})`
    );
  }
}

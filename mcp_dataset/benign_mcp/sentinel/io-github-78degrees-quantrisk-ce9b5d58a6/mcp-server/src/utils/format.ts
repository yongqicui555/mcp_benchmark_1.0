/**
 * Formatting utilities for QuantRisk MCP.
 * These functions convert raw numeric results into display-ready strings
 * suitable for inclusion in tool `summary` fields.
 *
 * None of these functions throw — they return a fallback string on bad input.
 */

// ---------------------------------------------------------------------------
// Currency
// ---------------------------------------------------------------------------

/**
 * Format a dollar amount with thousands separators and two decimal places.
 * Handles negative values (shown with a leading minus, not parentheses).
 *
 * @example
 *   formatCurrency(1234567.89)  // "$1,234,567.89"
 *   formatCurrency(-5000)       // "-$5,000.00"
 *   formatCurrency(0.5)         // "$0.50"
 */
export function formatCurrency(n: number): string {
  if (!isFinite(n)) return "N/A";
  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";
  return `${sign}$${abs.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  })}`;
}

// ---------------------------------------------------------------------------
// Percentages
// ---------------------------------------------------------------------------

/**
 * Format a decimal fraction as a percentage string.
 * The input is a decimal (0.1234 = 12.34%). `decimals` controls
 * the number of digits after the decimal point (default 2).
 *
 * @example
 *   formatPercent(0.1234)      // "12.34%"
 *   formatPercent(-0.05, 1)   // "-5.0%"
 *   formatPercent(1.5, 0)     // "150%"
 */
export function formatPercent(n: number, decimals = 2): string {
  if (!isFinite(n)) return "N/A";
  const pct = n * 100;
  const sign = pct < 0 ? "-" : "";
  return `${sign}${Math.abs(pct).toFixed(decimals)}%`;
}

// ---------------------------------------------------------------------------
// Generic numbers
// ---------------------------------------------------------------------------

/**
 * Format a plain number with optional decimal precision and thousands separators.
 * Defaults to 4 decimal places — appropriate for ratios and factors.
 *
 * @example
 *   formatNumber(1234567.89123, 2)  // "1,234,567.89"
 *   formatNumber(0.8532, 4)         // "0.8532"
 *   formatNumber(-1.23456789, 6)    // "-1.234568"
 */
export function formatNumber(n: number, decimals = 4): string {
  if (!isFinite(n)) return "N/A";
  return n.toLocaleString("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

// ---------------------------------------------------------------------------
// Composite helpers used by tool summary builders
// ---------------------------------------------------------------------------

/**
 * Format a ratio (Sharpe, Sortino, etc.) — 2 decimal places, no units.
 */
export function formatRatio(n: number): string {
  return formatNumber(n, 2);
}

/**
 * Produce a sign-aware description of a P&L change.
 * Returns e.g. "gained $1,234.56 (+2.34%)" or "lost $5,000.00 (-4.12%)".
 */
export function formatPnlDescription(dollarPnl: number, pctPnl: number): string {
  const verb = dollarPnl >= 0 ? "gained" : "lost";
  return `${verb} ${formatCurrency(Math.abs(dollarPnl))} (${formatPercent(pctPnl)})`;
}

/**
 * Compact number abbreviation for large values in summary prose.
 * Renders millions as "M" and billions as "B".
 *
 * @example
 *   formatCompact(1_250_000)     // "$1.25M"
 *   formatCompact(3_400_000_000) // "$3.40B"
 *   formatCompact(450_000)       // "$450,000"
 */
export function formatCompact(n: number): string {
  if (!isFinite(n)) return "N/A";
  const abs = Math.abs(n);
  const sign = n < 0 ? "-" : "";
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(2)}B`;
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(2)}M`;
  return formatCurrency(n);
}

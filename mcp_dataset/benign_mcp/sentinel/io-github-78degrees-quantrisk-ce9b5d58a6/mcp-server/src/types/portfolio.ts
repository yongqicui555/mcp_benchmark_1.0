/**
 * Portfolio domain types.
 * Plain TypeScript interfaces — not Zod-dependent.
 * Source of truth for runtime shapes is src/schemas/position.ts.
 */

export interface Position {
  /** Ticker symbol. Uppercase, 1-10 chars. e.g. "AAPL", "MSFT" */
  ticker: string;
  /** Shares held. Negative value indicates a short position. */
  quantity: number;
  /** Per-share cost basis. Optional — used for P&L calculations only. */
  cost_basis?: number | null;
}

export interface NamedPortfolio {
  /** Human-readable label for this portfolio allocation. 1-50 chars. */
  name: string;
  /** Positions in this portfolio. 1-500 entries. */
  positions: Position[];
}

export interface OptionPosition {
  /** Underlying ticker symbol. */
  underlying: string;
  /** Option strike price. Must be positive. */
  strike: number;
  /** Option expiry date in ISO format YYYY-MM-DD. Must be a future date. */
  expiry: string;
  /** Option type: call or put. */
  option_type: "call" | "put";
  /** Option exercise style. Defaults to "european". */
  style: "european" | "american";
  /** Number of contracts. Negative = short. Defaults to 1. */
  quantity: number;
  /**
   * Implied volatility as a decimal (e.g. 0.25 = 25%).
   * If null, it is computed from market_price.
   */
  implied_volatility: number | null;
  /**
   * Current market price of the option.
   * Required if implied_volatility is null.
   */
  market_price: number | null;
}

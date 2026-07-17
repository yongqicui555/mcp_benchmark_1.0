import { z } from "zod";

/**
 * Input schema for the `price_history` MCP tool.
 *
 * Fetches historical OHLCV price data for one or more tickers.
 * Free tier: 1 ticker, max 252 days.
 * Paid tier: up to 20 tickers, max 1260 days.
 */
export const priceHistorySchema = z.object({
  tickers: z
    .array(
      z
        .string()
        .min(1)
        .max(10)
        .regex(/^[A-Z0-9.^-]{1,10}$/, "Ticker must be uppercase alphanumeric")
    )
    .min(1)
    .max(20)
    .describe(
      "Ticker symbols to fetch price history for. " +
        "Free tier: max 1 ticker. Paid tier: up to 20 tickers."
    ),

  days: z
    .number()
    .int()
    .min(1)
    .max(1260)
    .default(252)
    .describe(
      "Number of historical trading days to return. " +
        "Free tier: max 252 days (~1 year). Paid tier: up to 1260 days (~5 years). Default: 252."
    ),

  interval: z
    .enum(["daily", "weekly", "monthly"])
    .default("daily")
    .describe(
      'Price interval. "daily" returns one OHLCV row per trading day, ' +
        '"weekly" aggregates to weekly bars, ' +
        '"monthly" aggregates to monthly bars. Default: "daily".'
    ),
});

export type PriceHistoryInput = z.infer<typeof priceHistorySchema>;

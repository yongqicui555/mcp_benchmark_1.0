import { z } from "zod";
import { positionSchema } from "./position.js";

/**
 * Schema for a named portfolio (used in compare_portfolios).
 */
export const namedPortfolioSchema = z.object({
  name: z
    .string()
    .min(1)
    .max(50)
    .describe("Human-readable label for this portfolio, e.g. 'Current' or 'Rebalanced'. 1-50 chars."),

  positions: z
    .array(positionSchema)
    .min(1)
    .max(500)
    .describe("Positions in this portfolio. 1-500 entries."),
});

export type NamedPortfolioInput = z.infer<typeof namedPortfolioSchema>;

/**
 * Input schema for the `compare_portfolios` MCP tool.
 *
 * Compares two or more portfolio allocations across all key risk/return metrics.
 * PAID tier only.
 */
export const comparePortfoliosSchema = z.object({
  portfolios: z
    .array(namedPortfolioSchema)
    .min(2)
    .max(5)
    .describe(
      "Two to five named portfolios to compare head-to-head. " +
        "Each needs a unique name and a list of positions. Min: 2, max: 5."
    ),

  period_days: z
    .number()
    .int()
    .min(30)
    .max(1260)
    .default(252)
    .describe(
      "Lookback period in trading days used for return and risk calculations. " +
        "252 = ~1 year. Range: 30-1260. Default: 252."
    ),

  confidence_level: z
    .number()
    .min(0.01)
    .max(0.99)
    .default(0.95)
    .describe(
      "VaR confidence level as a decimal, e.g. 0.95 = 95%. Range: 0.01-0.99. Default: 0.95."
    ),
});

export type ComparePortfoliosInput = z.infer<typeof comparePortfoliosSchema>;

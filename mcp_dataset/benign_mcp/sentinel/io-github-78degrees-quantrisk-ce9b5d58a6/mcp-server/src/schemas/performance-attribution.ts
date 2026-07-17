import { z } from "zod";
import { positionSchema } from "./position.js";

/**
 * Input schema for the `performance_attribution` MCP tool.
 *
 * Computes Sharpe, Sortino, Treynor, Calmar, and Information ratios
 * along with sector exposure and top/bottom contributors.
 */
export const performanceAttributionSchema = z.object({
  positions: z
    .array(positionSchema)
    .min(1)
    .max(500)
    .describe(
      "Array of portfolio positions. Free tier: max 20 positions (basic ratios only). " +
        "Paid tier: up to 500 positions with full factor attribution."
    ),

  period_days: z
    .number()
    .int()
    .min(30)
    .max(1260)
    .default(252)
    .describe(
      "Measurement period in trading days. 252 = ~1 year. Range: 30-1260. Default: 252."
    ),

  benchmark: z
    .string()
    .min(1)
    .max(10)
    .default("SPY")
    .describe(
      "Benchmark ticker for relative performance metrics (Information Ratio, Tracking Error, Beta). " +
        "Default: SPY."
    ),

  risk_free_rate: z
    .number()
    .min(0)
    .max(1)
    .default(0.05)
    .describe(
      "Annualized risk-free rate as a decimal, e.g. 0.05 = 5%. " +
        "Used in Sharpe, Sortino, and Treynor ratios. Default: 0.05."
    ),
});

export type PerformanceAttributionInput = z.infer<typeof performanceAttributionSchema>;

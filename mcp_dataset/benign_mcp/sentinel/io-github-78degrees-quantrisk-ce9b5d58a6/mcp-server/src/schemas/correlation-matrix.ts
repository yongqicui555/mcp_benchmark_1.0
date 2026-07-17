import { z } from "zod";

/**
 * Input schema for the `correlation_matrix` MCP tool.
 *
 * Computes pairwise correlations between assets and identifies
 * highly correlated pairs and diversification opportunities.
 */
export const correlationMatrixSchema = z.object({
  tickers: z
    .array(
      z
        .string()
        .min(1)
        .max(10)
        .regex(/^[A-Z0-9.^-]{1,10}$/, "Ticker must be uppercase alphanumeric")
    )
    .min(2)
    .max(50)
    .describe(
      "Tickers to include in the correlation matrix. Minimum 2, maximum 50. " +
        "Free tier: max 10 tickers. Paid tier: up to 50."
    ),

  lookback_days: z
    .number()
    .int()
    .min(30)
    .max(1260)
    .default(252)
    .describe(
      "Historical window for computing correlations in trading days. " +
        "30 = ~6 weeks, 252 = ~1 year. Range: 30-1260. Default: 252."
    ),

  method: z
    .enum(["pearson", "spearman", "kendall"])
    .default("pearson")
    .describe(
      'Correlation method. "pearson" = linear correlation (standard), ' +
        '"spearman" = rank-based (robust to outliers), ' +
        '"kendall" = concordance-based. Default: "pearson".'
    ),
});

export type CorrelationMatrixInput = z.infer<typeof correlationMatrixSchema>;

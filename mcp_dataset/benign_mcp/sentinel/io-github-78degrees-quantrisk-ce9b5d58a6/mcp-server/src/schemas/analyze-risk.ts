import { z } from "zod";
import { positionSchema } from "./position.js";

/**
 * Input schema for the `analyze_risk` MCP tool.
 *
 * Calculates VaR, CVaR, volatility, beta, and max drawdown for a portfolio.
 */
export const analyzeRiskSchema = z.object({
  positions: z
    .array(positionSchema)
    .min(1)
    .max(500)
    .describe(
      "Array of portfolio positions. Each entry needs a ticker and quantity. " +
        "Free tier: max 20 positions. Paid tier: up to 500."
    ),

  confidence_level: z
    .number()
    .min(0.01)
    .max(0.99)
    .default(0.95)
    .describe(
      "VaR confidence level as a decimal, e.g. 0.95 = 95%. Range: 0.01-0.99. Default: 0.95."
    ),

  horizon_days: z
    .number()
    .int()
    .min(1)
    .max(252)
    .default(1)
    .describe(
      "Risk horizon in trading days. 1 = overnight, 21 ≈ 1 month, 252 ≈ 1 year. Default: 1."
    ),

  method: z
    .enum(["historical", "parametric", "cornish_fisher"])
    .default("historical")
    .describe(
      "VaR calculation method. " +
        '"historical" uses empirical return distribution, ' +
        '"parametric" assumes normality, ' +
        '"cornish_fisher" adjusts for skew and kurtosis. Default: "historical".'
    ),

  benchmark: z
    .string()
    .min(1)
    .max(10)
    .default("SPY")
    .describe(
      "Benchmark ticker for beta calculation, e.g. SPY or QQQ. Default: SPY."
    ),

  lookback_days: z
    .number()
    .int()
    .min(30)
    .max(1260)
    .default(252)
    .describe(
      "Number of historical trading days to use. 252 ≈ 1 year, 756 ≈ 3 years. " +
        "Range: 30-1260. Default: 252."
    ),
});

export type AnalyzeRiskInput = z.infer<typeof analyzeRiskSchema>;

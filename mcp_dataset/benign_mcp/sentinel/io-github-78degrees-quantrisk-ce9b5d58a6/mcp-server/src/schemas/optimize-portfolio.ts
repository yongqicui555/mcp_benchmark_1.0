import { z } from "zod";

/**
 * Portfolio optimization constraints.
 */
export const constraintsSchema = z.object({
  min_weight: z
    .number()
    .min(0)
    .max(1)
    .default(0.0)
    .describe(
      "Minimum allocation weight per asset as a decimal. 0.0 = no minimum (asset may be excluded). " +
        "Range: 0.0-1.0. Default: 0.0."
    ),

  max_weight: z
    .number()
    .min(0)
    .max(1)
    .default(1.0)
    .describe(
      "Maximum allocation weight per asset as a decimal. 0.1 = max 10% in any single asset. " +
        "Range: 0.0-1.0. Default: 1.0."
    ),

  sector_max: z
    .record(z.string(), z.number().min(0).max(1))
    .nullable()
    .optional()
    .describe(
      "Maximum total portfolio weight per sector, e.g. { Technology: 0.30 } = max 30% in tech. " +
        "Keys should be GICS sector names."
    ),
});

export type ConstraintsInput = z.infer<typeof constraintsSchema>;

/**
 * Input schema for the `optimize_portfolio` MCP tool.
 *
 * Finds optimal portfolio weights using mean-variance optimization (Markowitz).
 * PAID tier only.
 */
/** Base object shape — used by server.ts for MCP tool registration (needs .shape). */
export const optimizePortfolioBaseSchema = z.object({
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
      "Universe of tickers to optimize across. Must be 2-50 tickers. " +
        "The optimizer will determine the best weights within this set."
    ),

  objective: z
    .enum(["max_sharpe", "min_variance", "target_return"])
    .default("max_sharpe")
    .describe(
      'Optimization objective. "max_sharpe" = maximize risk-adjusted return, ' +
        '"min_variance" = minimize portfolio volatility, ' +
        '"target_return" = hit a specific return with minimum risk. Default: "max_sharpe".'
    ),

  target_return: z
    .number()
    .positive()
    .nullable()
    .optional()
    .describe(
      'Required when objective is "target_return". Annualized return as a decimal, ' +
        "e.g. 0.12 = 12% annual return target."
    ),

  constraints: constraintsSchema
    .optional()
    .describe("Optional weight constraints. See ConstraintsInput for details."),

  risk_free_rate: z
    .number()
    .min(0)
    .max(1)
    .default(0.05)
    .describe(
      "Annualized risk-free rate as a decimal, e.g. 0.05 = 5%. " +
        "Used in Sharpe ratio calculation. Default: 0.05."
    ),

  lookback_days: z
    .number()
    .int()
    .min(252)
    .max(1260)
    .default(756)
    .describe(
      "Historical window for estimating return and covariance. " +
        "252 = 1 year, 756 = 3 years, 1260 = 5 years. Range: 252-1260. Default: 756."
    ),
});

/** Full schema with cross-field validation — used for runtime input validation. */
export const optimizePortfolioSchema = optimizePortfolioBaseSchema.refine(
  (data) => {
    if (data.objective === "target_return" && data.target_return == null) {
      return false;
    }
    return true;
  },
  {
    message: 'target_return is required when objective is "target_return"',
    path: ["target_return"],
  }
);

export type OptimizePortfolioInput = z.infer<typeof optimizePortfolioSchema>;

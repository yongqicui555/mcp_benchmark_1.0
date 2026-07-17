import { z } from "zod";
import { positionSchema } from "./position.js";

/**
 * Input schema for the `monte_carlo_simulation` MCP tool.
 *
 * Runs Monte Carlo simulation to model the distribution of future portfolio returns.
 */
export const monteCarloSchema = z.object({
  positions: z
    .array(positionSchema)
    .min(1)
    .max(500)
    .describe(
      "Array of portfolio positions. Free tier: max 20 positions. Paid tier: up to 500."
    ),

  num_paths: z
    .number()
    .int()
    .min(100)
    .max(100_000)
    .default(10_000)
    .describe(
      "Number of simulation paths to run. More paths = more accurate but slower. " +
        "Free tier: max 1,000. Paid tier: up to 100,000. Default: 10,000."
    ),

  horizon_days: z
    .number()
    .int()
    .min(1)
    .max(252)
    .default(21)
    .describe(
      "Simulation horizon in trading days. 21 ≈ 1 month, 63 ≈ 1 quarter, 252 ≈ 1 year. " +
        "Default: 21."
    ),

  model: z
    .enum(["gbm", "jump_diffusion"])
    .default("gbm")
    .describe(
      'Stochastic process model. "gbm" = Geometric Brownian Motion (standard), ' +
        '"jump_diffusion" = adds jump risk for fat-tail scenarios. Default: "gbm".'
    ),

  lookback_days: z
    .number()
    .int()
    .min(30)
    .max(1260)
    .default(252)
    .describe(
      "Historical window used to estimate drift and volatility parameters. " +
        "Range: 30-1260 trading days. Default: 252."
    ),

  seed: z
    .number()
    .int()
    .positive()
    .nullable()
    .optional()
    .describe(
      "Random seed for reproducible results. Omit for a fresh random run each time."
    ),
});

export type MonteCarloInput = z.infer<typeof monteCarloSchema>;

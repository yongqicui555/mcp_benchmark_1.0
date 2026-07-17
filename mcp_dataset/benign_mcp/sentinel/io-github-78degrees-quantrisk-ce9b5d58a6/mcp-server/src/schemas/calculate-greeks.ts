import { z } from "zod";

/**
 * Schema for a single option position.
 */
export const optionPositionSchema = z.object({
  underlying: z
    .string()
    .min(1)
    .max(10)
    .regex(/^[A-Z0-9.^-]{1,10}$/, "Ticker must be uppercase alphanumeric")
    .describe("Ticker symbol of the underlying asset, e.g. AAPL."),

  strike: z
    .number()
    .positive()
    .describe("Option strike price in USD. Must be a positive number."),

  expiry: z
    .string()
    .regex(/^\d{4}-\d{2}-\d{2}$/, "Expiry must be in YYYY-MM-DD format")
    .describe(
      "Option expiry date in ISO 8601 format, e.g. 2026-12-19. Must be a future date."
    ),

  option_type: z
    .enum(["call", "put"])
    .describe('Option type: "call" gives the right to buy, "put" gives the right to sell.'),

  style: z
    .enum(["european", "american"])
    .default("european")
    .describe(
      'Option exercise style. "european" can only be exercised at expiry (Black-Scholes). ' +
        '"american" can be exercised any time (binomial model). Default: "european".'
    ),

  quantity: z
    .number()
    .int()
    .refine((v) => v !== 0, { message: "Quantity must be non-zero" })
    .default(1)
    .describe(
      "Number of contracts. Positive = long, negative = short. Default: 1."
    ),

  implied_volatility: z
    .number()
    .positive()
    .nullable()
    .optional()
    .describe(
      "Implied volatility as a decimal, e.g. 0.25 = 25%. " +
        "If omitted or null, it is computed from market_price."
    ),

  market_price: z
    .number()
    .positive()
    .nullable()
    .optional()
    .describe(
      "Current market price of the option in USD. " +
        "Required when implied_volatility is not provided."
    ),
}).refine(
  (data) => {
    // At least one of implied_volatility or market_price must be provided
    return data.implied_volatility != null || data.market_price != null;
  },
  {
    message: "Either implied_volatility or market_price must be provided",
    path: ["market_price"],
  }
);

export type OptionPositionInput = z.infer<typeof optionPositionSchema>;

/**
 * Input schema for the `calculate_greeks` MCP tool.
 *
 * Calculates delta, gamma, theta, vega, and rho for individual options
 * or an options portfolio. PAID tier only.
 */
export const calculateGreeksSchema = z.object({
  options: z
    .array(optionPositionSchema)
    .min(1)
    .max(100)
    .describe(
      "Array of option positions to calculate Greeks for. 1-100 options. " +
        "Results include per-option Greeks and aggregated portfolio Greeks."
    ),

  risk_free_rate: z
    .number()
    .min(0)
    .max(1)
    .default(0.05)
    .describe(
      "Annualized risk-free rate as a decimal, e.g. 0.05 = 5%. " +
        "Used in Black-Scholes and binomial pricing models. Default: 0.05."
    ),
});

export type CalculateGreeksInput = z.infer<typeof calculateGreeksSchema>;

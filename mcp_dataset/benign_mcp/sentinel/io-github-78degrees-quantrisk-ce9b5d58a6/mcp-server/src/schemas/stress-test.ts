import { z } from "zod";
import { positionSchema } from "./position.js";

/** Supported historical scenario identifiers. */
export const SCENARIO_VALUES = [
  "gfc_2008",
  "covid_2020",
  "dot_com_2000",
  "black_monday_1987",
  "taper_tantrum_2013",
  "rate_hike_2022",
  "volmageddon_2018",
  "euro_crisis_2011",
] as const;

export type ScenarioId = (typeof SCENARIO_VALUES)[number];

/**
 * Schema for a custom shock scenario.
 * Available on PAID tier only.
 */
export const customShockSchema = z.object({
  name: z
    .string()
    .min(1)
    .max(50)
    .describe("Name for this custom scenario, e.g. 'Rate spike +300bps'. 1-50 characters."),

  ticker_shocks: z
    .record(z.string(), z.number().min(-1).max(1))
    .optional()
    .describe(
      "Per-ticker price shocks as decimals, e.g. { AAPL: -0.20 } = AAPL drops 20%. " +
        "Range: -1.0 to 1.0."
    ),

  sector_shocks: z
    .record(z.string(), z.number().min(-1).max(1))
    .optional()
    .describe(
      "Per-sector shocks applied to all positions in that sector. " +
        'e.g. { Technology: -0.15 }. Range: -1.0 to 1.0.'
    ),

  market_shock: z
    .number()
    .min(-1)
    .max(1)
    .optional()
    .describe(
      "Broad market shock applied to all positions not covered by ticker_shocks " +
        "or sector_shocks. e.g. -0.10 = market down 10%. Range: -1.0 to 1.0."
    ),
});

export type CustomShockInput = z.infer<typeof customShockSchema>;

/**
 * Input schema for the `stress_test` MCP tool.
 *
 * Tests portfolio performance against historical crisis scenarios
 * or custom shock definitions.
 */
export const stressTestSchema = z.object({
  positions: z
    .array(positionSchema)
    .min(1)
    .max(500)
    .describe(
      "Array of portfolio positions. Free tier: max 20 positions and historical scenarios only. " +
        "Paid tier: up to 500 positions plus custom shocks."
    ),

  scenarios: z
    .array(z.enum([...SCENARIO_VALUES] as [string, ...string[]]))
    .default(["gfc_2008", "covid_2020"])
    .describe(
      "Historical scenarios to run. Available values: " +
        SCENARIO_VALUES.join(", ") +
        ". Default: [gfc_2008, covid_2020]."
    ),

  custom_shocks: z
    .array(customShockSchema)
    .nullable()
    .optional()
    .describe(
      "Custom shock definitions. PAID tier only. Each shock specifies ticker-level, " +
        "sector-level, or market-wide price changes."
    ),
});

export type StressTestInput = z.infer<typeof stressTestSchema>;

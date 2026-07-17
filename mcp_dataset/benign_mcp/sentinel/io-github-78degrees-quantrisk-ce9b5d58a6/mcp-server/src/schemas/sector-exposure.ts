import { z } from "zod";
import { positionSchema } from "./position.js";

/**
 * Input schema for the `sector_exposure` MCP tool.
 *
 * Breaks down portfolio exposure by GICS sector, market cap, geography,
 * and asset class. Available on FREE tier.
 */
export const sectorExposureSchema = z.object({
  positions: z
    .array(positionSchema)
    .min(1)
    .max(500)
    .describe(
      "Array of portfolio positions to analyze. " +
        "Returns GICS sector weights, market cap breakdown, and concentration metrics."
    ),
});

export type SectorExposureInput = z.infer<typeof sectorExposureSchema>;

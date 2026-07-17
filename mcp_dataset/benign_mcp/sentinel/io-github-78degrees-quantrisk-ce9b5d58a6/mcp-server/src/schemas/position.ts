import { z } from "zod";

/**
 * Zod schema for a single portfolio position.
 * Reused by every tool schema that accepts a positions array.
 */
export const positionSchema = z.object({
  ticker: z
    .string()
    .min(1)
    .max(10)
    .regex(/^[A-Z0-9.^-]{1,10}$/, "Ticker must be uppercase alphanumeric (e.g. AAPL, BRK.B)")
    .describe("Ticker symbol, e.g. AAPL or MSFT. Must be uppercase, 1-10 characters."),
  quantity: z
    .number()
    .refine((v) => v !== 0, { message: "Quantity must be non-zero" })
    .describe("Number of shares held. Use a negative value to represent a short position."),
  cost_basis: z
    .number()
    .positive("Cost basis must be a positive number")
    .nullable()
    .optional()
    .describe("Per-share cost basis in USD. Optional — used only for P&L calculations."),
});

export type PositionInput = z.infer<typeof positionSchema>;

// @deprecated — ADR-0062 (2026-04-26): canonical 5-tool 채택으로 `create_order`
// 가 `submit_intent` 로 흡수되었다. 본 모듈은 backward-compat 만 위해
// re-export 한다. 신규 코드는 `../submit-intent.js` 의 `submitIntentTool` 사용.
//
// REMOVAL TIMELINE: 0.3.0 (FU-0062-2 land 후 2 minor versions).

import { z } from "zod";
import { AddressSchema } from "./cart.js";

export const CreateOrderInput = z.object({
  cartId: z.string().min(1),
  buyerDid: z.string().min(1).optional(),
  shippingAddress: AddressSchema,
  contactEmail: z.string().email().optional(),
  idempotencyKey: z.string().min(8).max(128),
  /** Optional AP2 payment mandate VC id for chain linkage. */
  paymentMandateId: z.string().optional(),
});

export type CreateOrderInput = z.infer<typeof CreateOrderInput>;

export const CreateOrderOutput = z.object({
  orderId: z.string(),
  checkoutUrl: z.string().url(),
  status: z.enum(["pending", "requires_payment", "confirmed"]),
  createdAt: z.number().int(),
});

export type CreateOrderOutput = z.infer<typeof CreateOrderOutput>;

export const createOrderTool = {
  name: "create_order" as const,
  description: "Convert a priced cart into an order. Returns a checkout URL for payment.",
  inputSchema: CreateOrderInput,
  outputSchema: CreateOrderOutput,
  handler: async (input: CreateOrderInput): Promise<CreateOrderOutput> => ({
    orderId: `ord_skeleton_${input.idempotencyKey.slice(0, 8)}`,
    checkoutUrl: "https://shop.example/checkout/skeleton",
    status: "requires_payment",
    createdAt: Math.floor(Date.now() / 1000),
  }),
};

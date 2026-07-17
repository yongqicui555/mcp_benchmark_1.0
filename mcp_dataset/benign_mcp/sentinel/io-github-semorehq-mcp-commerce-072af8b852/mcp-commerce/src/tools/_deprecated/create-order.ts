// @deprecated — ADR-0062 (2026-04-26): canonical 5-tool 채택으로 `create_order` 제거.
//
// 본 tool 은 `submit_intent` 로 흡수되었다. AP2 mandate 체인 (intent →
// cart → submit) 표면이 `quote_checkout` + `submit_intent` 2-step 으로
// 분리됨. legacy caller (apps/api/test/openapi-route.test.ts 등) backward
// compat 만 위해 export 유지.
//
// REMOVAL TIMELINE: FU-0062-2 land 후 2 minor versions (0.3.x) 까지 유지.

import { z } from "zod";
import { AddressSchema } from "../create-cart.js";

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

let warned = false;
function warnOnce(): void {
  if (warned) return;
  warned = true;
  // Workers + Node both expose console.warn — safe in either runtime.
  console.warn(
    "[@semore/mcp-commerce] create_order is DEPRECATED (ADR-0062). " +
      "Use submit_intent (canonical 5-tool). This shim will be removed in 0.3.0.",
  );
}

/**
 * @deprecated Use `submitIntentTool` from `../submit-intent.js` instead.
 */
export const createOrderTool = {
  name: "create_order" as const,
  description:
    "[DEPRECATED — use submit_intent] Convert a priced cart into an order. Returns a checkout URL for payment.",
  inputSchema: CreateOrderInput,
  outputSchema: CreateOrderOutput,
  handler: async (input: CreateOrderInput): Promise<CreateOrderOutput> => {
    warnOnce();
    return {
      orderId: `ord_skeleton_${input.idempotencyKey.slice(0, 8)}`,
      checkoutUrl: "https://shop.example/checkout/skeleton",
      status: "requires_payment",
      createdAt: Math.floor(Date.now() / 1000),
    };
  },
};

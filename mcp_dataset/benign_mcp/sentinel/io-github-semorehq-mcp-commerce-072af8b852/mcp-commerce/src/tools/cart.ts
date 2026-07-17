// @deprecated — ADR-0062 (2026-04-26): `build_cart` 가 canonical `create_cart`
// 로 rename. 본 모듈은 backward-compat re-export 만 제공.
// 신규 코드는 `../tools/create-cart.js` 의 `createCartTool` 사용.
//
// REMOVAL TIMELINE: 0.3.0.

import { z } from "zod";

export const CartItemSchema = z.object({
  skuId: z.string().min(1),
  qty: z.number().int().min(1).max(99),
});

export const AddressSchema = z.object({
  country: z.string().length(2), // ISO 3166-1 alpha-2
  region: z.string().optional(),
  city: z.string().optional(),
  postalCode: z.string().optional(),
  line1: z.string().optional(),
  line2: z.string().optional(),
});

export const BuildCartInput = z.object({
  items: z.array(CartItemSchema).min(1).max(50),
  address: AddressSchema,
  language: z.enum(["en", "ja", "de", "fr", "es", "ko"]).default("en"),
  currency: z.enum(["USD", "JPY", "EUR", "KRW"]).default("USD"),
});

export type BuildCartInput = z.infer<typeof BuildCartInput>;

export const BuildCartLineSchema = z.object({
  skuId: z.string(),
  qty: z.number().int(),
  unitPrice: z.string(),
  lineTotal: z.string(),
});
export type BuildCartLine = z.infer<typeof BuildCartLineSchema>;

export const BuildCartOutput = z.object({
  cartId: z.string(),
  subtotal: z.string(),
  shipping: z.string(),
  dutyTax: z.string(),
  total: z.string(),
  currency: z.string(),
  lines: z.array(BuildCartLineSchema),
});

export type BuildCartOutput = z.infer<typeof BuildCartOutput>;

/**
 * External pricer contract. Apps that distribute this MCP package (notably
 * `apps/api/src/routes/mcp.ts`) inject a real implementation backed by the
 * shared `lib/commerce.ts#priceCart` (D1 SKU lookup + HS tariff + de minimis
 * + IOSS rules). The OSS default below is a deterministic stub used by
 * tests and offline demos so the package stays self-contained — never relied
 * on for real settlement.
 */
export interface CartPricer {
  (input: BuildCartInput): Promise<BuildCartOutput>;
}

const fmt = (n: number): string => (Math.round(n * 100) / 100).toFixed(2);

const DEFAULT_OFFLINE_PRICE_USD = 25;

export const offlineStubPricer: CartPricer = async (input) => {
  const lines: BuildCartLine[] = input.items.map((i) => ({
    skuId: i.skuId,
    qty: i.qty,
    unitPrice: fmt(DEFAULT_OFFLINE_PRICE_USD),
    lineTotal: fmt(DEFAULT_OFFLINE_PRICE_USD * i.qty),
  }));
  const subtotalNum = lines.reduce((s, l) => s + Number(l.lineTotal), 0);
  const shippingNum = input.items.length * 5;
  const dutyTaxNum = subtotalNum * 0.1;
  const totalNum = subtotalNum + shippingNum + dutyTaxNum;
  return {
    cartId: `cart_offline_${input.items.length}`,
    subtotal: fmt(subtotalNum),
    shipping: fmt(shippingNum),
    dutyTax: fmt(dutyTaxNum),
    total: fmt(totalNum),
    currency: input.currency,
    lines,
  };
};

export interface BuildCartToolOptions {
  pricer?: CartPricer;
}

export function makeBuildCartTool(options: BuildCartToolOptions = {}) {
  const pricer = options.pricer ?? offlineStubPricer;
  return {
    name: "build_cart" as const,
    description:
      "Compute a priced cart (subtotal + shipping + duty + tax) for the given items and destination.",
    inputSchema: BuildCartInput,
    outputSchema: BuildCartOutput,
    handler: async (input: BuildCartInput): Promise<BuildCartOutput> => pricer(input),
  };
}

export const buildCartTool = makeBuildCartTool();

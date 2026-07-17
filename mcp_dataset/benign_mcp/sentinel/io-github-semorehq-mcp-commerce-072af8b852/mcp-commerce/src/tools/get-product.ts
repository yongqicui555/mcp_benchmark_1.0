// get_product — canonical Semore MCP commerce tool #2 (ADR-0062).
//
// 단일 SKU 의 i18n 상세 (title/desc/images/specs/HS code/ship-from/lead time)
// + 재고 정보 반환. manifest.json:54-58 inputSchemaRef 와 정합.

import { z } from "zod";
import { SUPPORTED_LANGS } from "./search-product.js";

export const GetProductInput = z.object({
  sku_id: z.string().min(1).max(128),
  lang: z.enum(SUPPORTED_LANGS).default("en"),
});
export type GetProductInput = z.infer<typeof GetProductInput>;

export const ProductImageSchema = z.object({
  url: z.string().url(),
  alt: z.string().optional(),
  width: z.number().int().positive().optional(),
  height: z.number().int().positive().optional(),
});

export const ProductSpecsSchema = z.record(z.string(), z.string());

export const GetProductOutput = z.object({
  sku_id: z.string(),
  title: z.string(),
  description: z.string(),
  images: z.array(ProductImageSchema).max(20),
  specs: ProductSpecsSchema,
  /** 무게 (g). cross-border 배송비/관세 계산에 필수. */
  weight_g: z.number().int().nonnegative(),
  /** Harmonized System code (관세 분류). 6~10 자리. */
  hs_code: z.string().regex(/^[0-9]{6,10}$/),
  ship_from: z.string().length(2),
  /** Sourcing → fulfillment 까지 영업일. */
  lead_days: z.number().int().nonnegative(),
  stock: z.number().int().nonnegative(),
  price_usd: z.string(),
  brand: z.string().optional(),
});
export type GetProductOutput = z.infer<typeof GetProductOutput>;

export interface ProductFetcher {
  (input: GetProductInput): Promise<GetProductOutput>;
}

const STUB_FETCHER: ProductFetcher = async (input) => ({
  sku_id: input.sku_id,
  title: `Stub product ${input.sku_id}`,
  description: "Skeleton product body. Replace with the real D1-backed fetcher.",
  images: [],
  specs: {},
  weight_g: 0,
  hs_code: "000000",
  ship_from: "KR",
  lead_days: 0,
  stock: 0,
  price_usd: "0.00",
});

export interface GetProductToolOptions {
  fetcher?: ProductFetcher;
}

export function makeGetProductTool(options: GetProductToolOptions = {}) {
  const fetcher = options.fetcher ?? STUB_FETCHER;
  return {
    name: "get_product" as const,
    description:
      "Fetch a single SKU's i18n detail: title, description, images, specs, weight, HS code, ship-from, lead time, and live stock.",
    inputSchema: GetProductInput,
    outputSchema: GetProductOutput,
    handler: async (input: GetProductInput): Promise<GetProductOutput> => fetcher(input),
  };
}

export const getProductTool = makeGetProductTool();

// @deprecated — ADR-0062 (2026-04-26): 단수형 `search_product` (canonical) 로
// 통일. 본 모듈의 복수형 `search_products` 는 backward-compat re-export 만
// 제공. 신규 코드는 `../tools/search-product.js` 의 `searchProductTool` 사용.
//
// REMOVAL TIMELINE: 0.3.0.

import { z } from "zod";

export const SearchProductsInput = z.object({
  q: z.string().min(1).max(200),
  lang: z.enum(["en", "ja", "de", "fr", "es", "ko"]).default("en"),
  category: z.enum(["kbeauty", "kfashion", "kpop", "electronics", "food"]).optional(),
  maxPriceUsd: z.number().positive().optional(),
  limit: z.number().int().min(1).max(50).default(20),
});

export type SearchProductsInput = z.infer<typeof SearchProductsInput>;

export const SearchProductsOutput = z.object({
  items: z
    .array(
      z.object({
        skuId: z.string(),
        title: z.string(),
        priceUsd: z.string(), // decimal string
        imageUrl: z.string().url().optional(),
        brand: z.string().optional(),
      }),
    )
    .max(50),
  total: z.number().int().nonnegative(),
});

export type SearchProductsOutput = z.infer<typeof SearchProductsOutput>;

export const searchProductsTool = {
  name: "search_products" as const,
  description:
    "Search the merchant catalog by keyword, category, price range. Returns up to `limit` SKUs.",
  inputSchema: SearchProductsInput,
  outputSchema: SearchProductsOutput,
  /**
   * Skeleton handler. Replace with a real catalog fetch in production.
   * The shipped implementation returns a deterministic empty result so
   * integrators can validate the wiring without a data source.
   */
  handler: async (_input: SearchProductsInput): Promise<SearchProductsOutput> => ({
    items: [],
    total: 0,
  }),
};

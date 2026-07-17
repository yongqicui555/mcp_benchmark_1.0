// search_product — canonical Semore MCP commerce tool #1 (ADR-0062).
//
// Semore K-product 카탈로그를 키워드/카테고리/가격/도착지 기준으로 검색.
// manifest.json:48-53 의 inputSchemaRef 와 정합 (https://mcp.semore.net/schemas/search_product.json).
//
// 단수형 (`search_product`) 채택 이유: ADR-0062 §2.2.

import { z } from "zod";

export const SUPPORTED_LANGS = ["en", "ja", "de", "fr", "es", "ko"] as const;
export const SUPPORTED_CATEGORIES = [
  "kbeauty",
  "kfashion",
  "kpop",
  "electronics",
  "food",
] as const;

export const SearchProductInput = z.object({
  /** 자연어 또는 키워드 쿼리. 한국어/영문/일본어 mix 허용. */
  q: z.string().min(1).max(200),
  lang: z.enum(SUPPORTED_LANGS).default("en"),
  category: z.enum(SUPPORTED_CATEGORIES).optional(),
  /** USD 환산 상한 — Workers 측 D1 query 에서 cross-border presentment 환산. */
  max_price_usd: z.number().positive().optional(),
  /** ISO 3166-1 alpha-2 도착지 (US/JP/DE/FR/ES/KR ...). 관세/배송 시뮬에 사용. */
  country: z.string().length(2).default("US"),
  /** 최대 반환 SKU 수. */
  limit: z.number().int().min(1).max(50).default(20),
});

export type SearchProductInput = z.infer<typeof SearchProductInput>;

export const SearchProductResultItem = z.object({
  sku_id: z.string(),
  title: z.string(),
  price_usd: z.string(), // decimal string
  ship_from: z.string().length(2).optional(), // ISO 3166-1 alpha-2
  available: z.boolean().default(true),
  rank: z.number().nonnegative().optional(),
  image_url: z.string().url().optional(),
  brand: z.string().optional(),
});
export type SearchProductResultItem = z.infer<typeof SearchProductResultItem>;

export const SearchProductOutput = z.object({
  results: z.array(SearchProductResultItem).max(50),
  total: z.number().int().nonnegative(),
});
export type SearchProductOutput = z.infer<typeof SearchProductOutput>;

/**
 * Pluggable catalog backend (D1 FTS5 in production, in-memory in tests).
 * Apps that distribute this MCP package (notably `apps/api/src/routes/mcp.ts`)
 * inject a real implementation backed by the D1 SKU table + cross-border
 * pricer. The OSS default returns a deterministic empty payload so the
 * package stays self-contained — never relied on for real settlement.
 */
export interface ProductSearcher {
  (input: SearchProductInput): Promise<SearchProductOutput>;
}

const EMPTY_SEARCHER: ProductSearcher = async () => ({ results: [], total: 0 });

export interface SearchProductToolOptions {
  searcher?: ProductSearcher;
}

export function makeSearchProductTool(options: SearchProductToolOptions = {}) {
  const searcher = options.searcher ?? EMPTY_SEARCHER;
  return {
    name: "search_product" as const,
    description:
      "Search the Semore K-product catalog by keyword, category, price range, and destination. Returns ranked SKU offers (id, title, price USD, ship-from, availability).",
    inputSchema: SearchProductInput,
    outputSchema: SearchProductOutput,
    handler: async (input: SearchProductInput): Promise<SearchProductOutput> => searcher(input),
  };
}

export const searchProductTool = makeSearchProductTool();

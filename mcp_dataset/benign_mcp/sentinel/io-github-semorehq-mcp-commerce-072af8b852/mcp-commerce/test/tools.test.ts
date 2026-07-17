// Legacy 4-tool 단위 테스트 — backward-compat 보장 (ADR-0062).
//
// canonical 5-tool 테스트는 `canonical-tools.test.ts` 참조. 본 파일은
// 0.3.0 (legacy export 제거 시점) 까지 유지되며, 그 후 삭제 예정.
//
// `createMcpServer` 는 5-tool canonical 만 노출 — 본 파일은 schema 단위
// 검증에만 집중 (server-level 4-tool 검증 X).

import { describe, it, expect } from "vitest";
import {
  searchProductsTool,
  buildCartTool,
  createOrderTool,
  getPolicyTool,
} from "../src/index.js";

describe("[legacy] search_products", () => {
  it("accepts a valid input", () => {
    const parsed = searchProductsTool.inputSchema.parse({ q: "sunscreen", lang: "en", limit: 5 });
    expect(parsed.q).toBe("sunscreen");
    expect(parsed.limit).toBe(5);
  });

  it("rejects empty query", () => {
    expect(() => searchProductsTool.inputSchema.parse({ q: "" })).toThrow();
  });

  it("rejects out-of-range limit", () => {
    expect(() => searchProductsTool.inputSchema.parse({ q: "x", limit: 999 })).toThrow();
  });
});

describe("[legacy] build_cart", () => {
  it("accepts a valid cart", () => {
    const parsed = buildCartTool.inputSchema.parse({
      items: [{ skuId: "sku_1", qty: 2 }],
      address: { country: "US" },
    });
    expect(parsed.currency).toBe("USD");
  });

  it("rejects bad country code", () => {
    expect(() =>
      buildCartTool.inputSchema.parse({
        items: [{ skuId: "sku_1", qty: 1 }],
        address: { country: "USA" },
      }),
    ).toThrow();
  });
});

describe("[legacy] create_order", () => {
  it("accepts a valid order", () => {
    const parsed = createOrderTool.inputSchema.parse({
      cartId: "cart_1",
      shippingAddress: { country: "JP" },
      idempotencyKey: "idem_12345678",
    });
    expect(parsed.cartId).toBe("cart_1");
  });

  it("rejects short idempotencyKey", () => {
    expect(() =>
      createOrderTool.inputSchema.parse({
        cartId: "cart_1",
        shippingAddress: { country: "JP" },
        idempotencyKey: "short",
      }),
    ).toThrow();
  });
});

describe("[legacy] get_policy", () => {
  it("accepts a valid kind", () => {
    const parsed = getPolicyTool.inputSchema.parse({ kind: "returns", lang: "en" });
    expect(parsed.kind).toBe("returns");
  });

  it("rejects unknown kind", () => {
    expect(() => getPolicyTool.inputSchema.parse({ kind: "unknown" })).toThrow();
  });
});

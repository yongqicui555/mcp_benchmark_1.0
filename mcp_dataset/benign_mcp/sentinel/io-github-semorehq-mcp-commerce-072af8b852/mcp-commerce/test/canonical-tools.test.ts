// Canonical 5-tool 단위 테스트 (ADR-0062). manifest.json:48-73 와 1:1.
//
// 각 tool 별 happy path 1 + invalid input 1.
// Cloudflare Workers 호환 — Node-only API 미사용.

import { afterEach, beforeEach, describe, it, expect } from "vitest";
import {
  searchProductTool,
  getProductTool,
  createCartTool,
  quoteCheckoutTool,
  submitIntentTool,
  makeQuoteCheckoutTool,
  makeSubmitIntentTool,
  parseIntentMandateVc,
  parseDid,
  verifyProofVerificationMethod,
  BuyerDidSchema,
  DID_REGEX,
  CartMandatePayloadSchema,
  STUB_CART_HASH_SENTINEL,
  STUB_PAYMENT_MANDATE_VC,
  createMcpServer,
  CANONICAL_TOOL_ORDER,
} from "../src/index.js";

describe("search_product (canonical #1)", () => {
  it("accepts a valid query and applies defaults", () => {
    const parsed = searchProductTool.inputSchema.parse({ q: "k-beauty serum" });
    expect(parsed.q).toBe("k-beauty serum");
    expect(parsed.lang).toBe("en");
    expect(parsed.country).toBe("US");
    expect(parsed.limit).toBe(20);
  });

  it("rejects an empty query", () => {
    expect(() => searchProductTool.inputSchema.parse({ q: "" })).toThrow();
  });

  it("returns deterministic stub output via the offline searcher", async () => {
    const out = await searchProductTool.handler({
      q: "x",
      lang: "en",
      country: "US",
      limit: 20,
    });
    expect(out.results).toEqual([]);
    expect(out.total).toBe(0);
  });
});

describe("get_product (canonical #2)", () => {
  it("accepts a valid sku_id", () => {
    const parsed = getProductTool.inputSchema.parse({ sku_id: "sku_test_001" });
    expect(parsed.sku_id).toBe("sku_test_001");
    expect(parsed.lang).toBe("en");
  });

  it("rejects an empty sku_id", () => {
    expect(() => getProductTool.inputSchema.parse({ sku_id: "" })).toThrow();
  });

  it("stub fetcher returns canonical shape", async () => {
    const out = await getProductTool.handler({ sku_id: "sku_x", lang: "en" });
    expect(out.sku_id).toBe("sku_x");
    expect(out.hs_code).toMatch(/^[0-9]{6,10}$/);
    expect(out.ship_from).toBe("KR");
  });
});

describe("create_cart (canonical #3)", () => {
  it("accepts a valid cart and applies defaults", () => {
    const parsed = createCartTool.inputSchema.parse({
      items: [{ sku_id: "sku_1", qty: 2 }],
      address: { country: "US" },
    });
    expect(parsed.currency).toBe("USD");
    expect(parsed.language).toBe("en");
    expect(parsed.items[0]?.qty).toBe(2);
  });

  it("rejects bad ISO country code length", () => {
    expect(() =>
      createCartTool.inputSchema.parse({
        items: [{ sku_id: "sku_1", qty: 1 }],
        address: { country: "USA" },
      }),
    ).toThrow();
  });

  it("offline pricer returns full breakdown", async () => {
    const out = await createCartTool.handler({
      items: [{ sku_id: "sku_x", qty: 2 }],
      address: { country: "JP" },
      language: "en",
      currency: "USD",
    });
    expect(out.cart_id).toMatch(/^cart_offline_/);
    expect(out.line_items).toHaveLength(1);
    expect(Number(out.total_usd)).toBeGreaterThan(0);
    expect(out.expires_at).toBeGreaterThan(Math.floor(Date.now() / 1000));
  });
});

describe("quote_checkout (canonical #4)", () => {
  it("accepts a valid cart_id and minimal payload", () => {
    const parsed = quoteCheckoutTool.inputSchema.parse({ cart_id: "cart_xyz" });
    expect(parsed.cart_id).toBe("cart_xyz");
  });

  it("rejects an empty cart_id", () => {
    expect(() => quoteCheckoutTool.inputSchema.parse({ cart_id: "" })).toThrow();
  });

  it("stub quoter emits a CartMandate payload to be signed", async () => {
    const out = await quoteCheckoutTool.handler({
      cart_id: "cart_xyz",
      buyer_did: "did:web:buyer.example",
    });
    expect(out.cart_mandate_payload.type).toBe("CartMandate");
    expect(out.cart_mandate_payload.cart_hash).toMatch(/^[a-f0-9]{64}$/);
    expect(out.cart_mandate_payload.issuer).toBe("did:web:semore.net");
    expect(out.cart_mandate_payload.buyer_did).toBe("did:web:buyer.example");
    // FU-0062-2.1 — AP2 spec §4.1.1 의 4 신규 필드.
    expect(out.cart_mandate_payload.payee.id).toBeTruthy();
    expect(out.cart_mandate_payload.payee.display_name).toBeTruthy();
    expect(out.cart_mandate_payload.payment_method_token).toBeTruthy();
    expect(out.cart_mandate_payload.intent_hash).toMatch(/^[a-f0-9]{64}$/);
  });
});

describe("submit_intent (canonical #5)", () => {
  const validInput = {
    cart_id: "cart_xyz",
    quote_id: "quote_xyz",
    intent_mandate_vc: "eyJhbGciOi...intent",
    cart_mandate_vc_signed: "eyJhbGciOi...cart",
    buyer_did: "did:web:buyer.example",
    customer_email: "buyer@example.com",
    language: "en" as const,
    idempotency_key: "idem_abcdef123",
  };

  it("accepts a valid signed-mandate submission", () => {
    const parsed = submitIntentTool.inputSchema.parse(validInput);
    expect(parsed.buyer_did).toBe("did:web:buyer.example");
    expect(parsed.idempotency_key).toBe("idem_abcdef123");
  });

  it("rejects a short idempotency_key", () => {
    expect(() =>
      submitIntentTool.inputSchema.parse({ ...validInput, idempotency_key: "short" }),
    ).toThrow();
  });

  it("rejects an invalid customer_email", () => {
    expect(() =>
      submitIntentTool.inputSchema.parse({ ...validInput, customer_email: "not-an-email" }),
    ).toThrow();
  });

  it("stub submitter returns a payment_session_url and order_id", async () => {
    const out = await submitIntentTool.handler(validInput);
    expect(out.order_id).toMatch(/^ord_stub_/);
    expect(out.payment_session_url).toMatch(/^https?:\/\//);
    expect(out.psp_channel).toBe("stripe");
    expect(out.status).toBe("requires_payment");
    // FU-0062-2.2 — 3 단 mandate 체인의 payment leaf 가 output 에 포함.
    expect(out.payment_mandate_vc).toBeTruthy();
    expect(typeof out.payment_mandate_vc).toBe("string");
  });
});

describe("createMcpServer (canonical 5-tool surface, ADR-0062)", () => {
  it("lists exactly 5 canonical tools in deterministic order", () => {
    const server = createMcpServer();
    const tools = server.listTools();
    expect(tools).toHaveLength(5);
    expect(tools.map((t) => t.name)).toEqual([
      "search_product",
      "get_product",
      "create_cart",
      "quote_checkout",
      "submit_intent",
    ]);
    // CANONICAL_TOOL_ORDER export 와 listTools() 가 정확히 일치.
    expect(tools.map((t) => t.name)).toEqual([...CANONICAL_TOOL_ORDER]);
  });

  it("dispatches search_product through the canonical handler", async () => {
    const server = createMcpServer();
    const res = (await server.callTool("search_product", {
      q: "test",
      lang: "en",
      country: "US",
      limit: 20,
    })) as { results: unknown[]; total: number };
    expect(res.results).toEqual([]);
    expect(res.total).toBe(0);
  });

  it("rejects an unknown tool name with stable error code", async () => {
    const server = createMcpServer();
    await expect(server.callTool("bogus", {})).rejects.toThrow(/unknown_tool/);
  });

  it("rejects legacy 4-tool names at the canonical surface", async () => {
    const server = createMcpServer();
    // Legacy alias 는 canonical 표면에서 거부됨 (apps/api 가 별도 alias layer 책임).
    await expect(server.callTool("search_products", { q: "x" })).rejects.toThrow(
      /unknown_tool:search_products/,
    );
    await expect(
      server.callTool("build_cart", {
        items: [{ skuId: "sku_1", qty: 1 }],
        address: { country: "US" },
      }),
    ).rejects.toThrow(/unknown_tool:build_cart/);
  });

  it("supports per-tool handler overrides for tests/wiring", async () => {
    const server = createMcpServer({
      overrides: {
        search_product: async () => ({ results: [], total: 42 }),
      },
    });
    const res = (await server.callTool("search_product", {
      q: "x",
      lang: "en",
      country: "US",
      limit: 20,
    })) as { results: unknown[]; total: number };
    expect(res.total).toBe(42);
  });
});

// ─── FU-0062-2.1 ─ AP2 spec §4.1.1 4 신규 필드 schema 강제 ─────────────
describe("CartMandatePayloadSchema (FU-0062-2.1, AP2 §4.1.1)", () => {
  const baseValid = {
    type: "CartMandate" as const,
    cart_id: "cart_xyz",
    cart_hash: "a".repeat(64),
    total_usd: "10.00",
    currency: "USD",
    expires_at: new Date().toISOString(),
    issuer: "did:web:semore.net",
    payee: { id: "mer_1", display_name: "Acme" },
    payment_method_token: "tok_opaque_xyz",
    intent_hash: "b".repeat(64),
  };

  it("accepts a valid payload with all 4 new bound-info fields", () => {
    const parsed = CartMandatePayloadSchema.parse(baseValid);
    expect(parsed.payee.id).toBe("mer_1");
    expect(parsed.payment_method_token).toBe("tok_opaque_xyz");
    expect(parsed.intent_hash).toMatch(/^[a-f0-9]{64}$/);
  });

  it("rejects payload missing required `payee`", () => {
    const { payee: _omit, ...rest } = baseValid;
    expect(() => CartMandatePayloadSchema.parse(rest)).toThrow();
  });

  it("rejects payload missing required `payment_method_token`", () => {
    const { payment_method_token: _omit, ...rest } = baseValid;
    expect(() => CartMandatePayloadSchema.parse(rest)).toThrow();
  });

  it("rejects payload with invalid `intent_hash` shape", () => {
    expect(() =>
      CartMandatePayloadSchema.parse({ ...baseValid, intent_hash: "not_hex" }),
    ).toThrow();
  });

  it("accepts optional `risk_signals` block", () => {
    const parsed = CartMandatePayloadSchema.parse({
      ...baseValid,
      risk_signals: { ip: "1.2.3.4", behavioral_score: 0.12 },
    });
    expect(parsed.risk_signals?.ip).toBe("1.2.3.4");
  });
});

// ─── FU-0062-2.3 ─ cart_hash zero-hash leak guard ────────────────────
describe("quote_checkout leak guard (FU-0062-2.3)", () => {
  let savedNodeEnv: string | undefined;
  beforeEach(() => {
    const proc = (globalThis as { process?: { env: Record<string, string | undefined> } }).process;
    savedNodeEnv = proc?.env["NODE_ENV"];
  });
  afterEach(() => {
    const proc = (globalThis as { process?: { env: Record<string, string | undefined> } }).process;
    if (proc) proc.env["NODE_ENV"] = savedNodeEnv;
  });

  it("default stub passes when NODE_ENV != production", async () => {
    const proc = (globalThis as { process?: { env: Record<string, string | undefined> } }).process;
    if (proc) proc.env["NODE_ENV"] = "test";
    const out = await quoteCheckoutTool.handler({ cart_id: "cart_xyz" });
    expect(out.cart_mandate_payload.cart_hash).toBe(STUB_CART_HASH_SENTINEL);
  });

  it("throws when stub sentinel reaches production runtime", async () => {
    const proc = (globalThis as { process?: { env: Record<string, string | undefined> } }).process;
    if (proc) proc.env["NODE_ENV"] = "production";
    const tool = makeQuoteCheckoutTool();
    await expect(tool.handler({ cart_id: "cart_xyz" })).rejects.toThrow(
      /cart_hash_stub_in_production/,
    );
  });

  it("allowStub=true bypasses the leak guard in production", async () => {
    const proc = (globalThis as { process?: { env: Record<string, string | undefined> } }).process;
    if (proc) proc.env["NODE_ENV"] = "production";
    const tool = makeQuoteCheckoutTool({ allowStub: true });
    const out = await tool.handler({ cart_id: "cart_xyz" });
    expect(out.cart_mandate_payload.cart_hash).toBe(STUB_CART_HASH_SENTINEL);
  });
});

// ─── FU-0062-2.2 ─ injectable PaymentMandate signer ─────────────────
describe("submit_intent paymentSigner injection (FU-0062-2.2)", () => {
  const validInput = {
    cart_id: "cart_xyz",
    quote_id: "quote_xyz",
    intent_mandate_vc: "eyJhbGciOi...intent",
    cart_mandate_vc_signed: "eyJhbGciOi...cart",
    buyer_did: "did:web:buyer.example",
    customer_email: "buyer@example.com",
    language: "en" as const,
    idempotency_key: "idem_abcdef123",
  };

  it("uses injected paymentSigner instead of stub", async () => {
    const tool = makeSubmitIntentTool({
      paymentSigner: async () => "real.payment_mandate_vc.value",
    });
    const out = await tool.handler(validInput);
    expect(out.payment_mandate_vc).toBe("real.payment_mandate_vc.value");
  });

  it("default stub returns placeholder", async () => {
    const out = await submitIntentTool.handler(validInput);
    expect(out.payment_mandate_vc).toBe(STUB_PAYMENT_MANDATE_VC);
  });

  it("leak guard throws stub VC in production", async () => {
    const proc = (globalThis as { process?: { env: Record<string, string | undefined> } }).process;
    const saved = proc?.env["NODE_ENV"];
    try {
      if (proc) proc.env["NODE_ENV"] = "production";
      const tool = makeSubmitIntentTool();
      await expect(tool.handler(validInput)).rejects.toThrow(
        /payment_mandate_vc_stub_in_production/,
      );
    } finally {
      if (proc) proc.env["NODE_ENV"] = saved;
    }
  });
});

// ─── FU-0062-2.4 ─ parseIntentMandateVc helper ──────────────────────
describe("parseIntentMandateVc helper (FU-0062-2.4)", () => {
  const validVc = JSON.stringify({
    "@context": ["https://www.w3.org/2018/credentials/v1"],
    type: ["VerifiableCredential", "IntentMandate"],
    issuer: "did:web:semore.net",
    credentialSubject: { intent: "purchase k-beauty serum", buyer_did: "did:web:b.example" },
    proof: { type: "Ed25519Signature2020", proofValue: "z..." },
  });

  it("non-strict mode best-effort parses and returns subject", () => {
    const out = parseIntentMandateVc(validVc);
    expect(out.credentialSubject["intent"]).toBe("purchase k-beauty serum");
  });

  it("non-strict mode tolerates non-JSON wire string", () => {
    const out = parseIntentMandateVc("eyJhbGciOi...opaque_jwt");
    expect(out.credentialSubject).toEqual({});
  });

  it("strict mode validates structural VC shape", () => {
    const out = parseIntentMandateVc(validVc, { strict: true });
    expect(out.credentialSubject["buyer_did"]).toBe("did:web:b.example");
  });

  it("strict mode rejects missing @context", () => {
    const bad = JSON.stringify({
      type: ["VerifiableCredential", "IntentMandate"],
      proof: {},
      credentialSubject: {},
    });
    expect(() => parseIntentMandateVc(bad, { strict: true })).toThrow(
      /missing_context/,
    );
  });

  it("strict mode rejects wrong VC type", () => {
    const bad = JSON.stringify({
      "@context": ["https://www.w3.org/2018/credentials/v1"],
      type: ["VerifiableCredential", "PaymentMandate"],
      proof: {},
      credentialSubject: {},
    });
    expect(() => parseIntentMandateVc(bad, { strict: true })).toThrow(
      /not_intent_mandate/,
    );
  });

  it("strict mode rejects missing proof", () => {
    const bad = JSON.stringify({
      "@context": ["https://www.w3.org/2018/credentials/v1"],
      type: ["VerifiableCredential", "IntentMandate"],
      credentialSubject: {},
    });
    expect(() => parseIntentMandateVc(bad, { strict: true })).toThrow(
      /missing_proof/,
    );
  });
});

// ─── FU-0062-2.11 ─ buyer_did required + W3C VC holder mapping ────────
describe("BuyerDidSchema + DID_REGEX (FU-0062-2.11)", () => {
  it("accepts did:web (Semore agent / merchant)", () => {
    expect(BuyerDidSchema.parse("did:web:semore.net")).toBe("did:web:semore.net");
  });

  it("accepts did:key (buyer self-issued)", () => {
    const did = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK";
    expect(BuyerDidSchema.parse(did)).toBe(did);
  });

  it("accepts did:jwk (Stripe Click-to-Pay interop)", () => {
    const did =
      "did:jwk:eyJjcnYiOiJQLTI1NiIsImt0eSI6IkVDIiwieCI6ImFjYmlSWmh0THFvU0R5SDR3MjBKaA";
    expect(BuyerDidSchema.parse(did)).toBe(did);
  });

  it("rejects did:ion (unsupported method)", () => {
    expect(() => BuyerDidSchema.parse("did:ion:EiClkZMDxPKqC9c-umQfTkR8")).toThrow();
  });

  it("rejects did:ethr (unsupported method)", () => {
    expect(() => BuyerDidSchema.parse("did:ethr:0xabc123")).toThrow();
  });

  it("rejects bare non-DID string", () => {
    expect(() => BuyerDidSchema.parse("not-a-did")).toThrow();
  });

  it("rejects empty string", () => {
    expect(() => BuyerDidSchema.parse("")).toThrow();
  });

  it("parseDid decomposes did:web identifier", () => {
    const out = parseDid("did:web:semore.net");
    expect(out).toEqual({ method: "web", identifier: "semore.net" });
  });

  it("parseDid returns null for unsupported method", () => {
    expect(parseDid("did:pkh:eip155:1:0xabc")).toBeNull();
  });

  it("DID_REGEX is exported and matches allowlist methods", () => {
    expect(DID_REGEX.test("did:web:semore.net")).toBe(true);
    expect(DID_REGEX.test("did:key:z6Mk...")).toBe(true);
    expect(DID_REGEX.test("did:jwk:eyJ...")).toBe(true);
    expect(DID_REGEX.test("did:ion:Ei...")).toBe(false);
  });
});

describe("submit_intent buyer_did validation (FU-0062-2.11)", () => {
  const validInput = {
    cart_id: "cart_xyz",
    quote_id: "quote_xyz",
    intent_mandate_vc: "eyJhbGciOi...intent",
    cart_mandate_vc_signed: "eyJhbGciOi...cart",
    buyer_did: "did:web:buyer.example",
    customer_email: "buyer@example.com",
    language: "en" as const,
    idempotency_key: "idem_abcdef123",
  };

  it("rejects missing buyer_did at input parse time", () => {
    const { buyer_did: _omit, ...rest } = validInput;
    expect(() => submitIntentTool.inputSchema.parse(rest)).toThrow();
  });

  it("rejects unsupported DID method (did:ion)", () => {
    expect(() =>
      submitIntentTool.inputSchema.parse({ ...validInput, buyer_did: "did:ion:abc" }),
    ).toThrow();
  });

  it("accepts each allowlisted DID method", () => {
    const dids = [
      "did:web:semore.net",
      "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK",
      "did:jwk:eyJjcnYiOiJQLTI1NiJ9",
    ];
    for (const did of dids) {
      const parsed = submitIntentTool.inputSchema.parse({ ...validInput, buyer_did: did });
      expect(parsed.buyer_did).toBe(did);
    }
  });
});

describe("parseIntentMandateVc holder binding (FU-0062-2.11)", () => {
  const buyerDid = "did:web:buyer.example";
  const otherDid = "did:web:other.example";
  const vcWithHolder = JSON.stringify({
    "@context": ["https://www.w3.org/2018/credentials/v1"],
    type: ["VerifiableCredential", "IntentMandate"],
    holder: buyerDid,
    proof: { type: "Ed25519Signature2020", proofValue: "z..." },
    credentialSubject: { intent: "buy serum" },
  });
  const vcWithSubjectId = JSON.stringify({
    "@context": ["https://www.w3.org/2018/credentials/v1"],
    type: ["VerifiableCredential", "IntentMandate"],
    proof: { type: "Ed25519Signature2020", proofValue: "z..." },
    credentialSubject: { id: buyerDid, intent: "buy serum" },
  });

  it("strict mode passes when holder == buyerDid", () => {
    const out = parseIntentMandateVc(vcWithHolder, { strict: true, buyerDid });
    expect(out.holder).toBe(buyerDid);
  });

  it("strict mode falls back to credentialSubject.id when holder absent", () => {
    const out = parseIntentMandateVc(vcWithSubjectId, { strict: true, buyerDid });
    expect(out.credentialSubject["id"]).toBe(buyerDid);
  });

  it("strict mode throws on holder mismatch", () => {
    expect(() =>
      parseIntentMandateVc(vcWithHolder, { strict: true, buyerDid: otherDid }),
    ).toThrow(/buyer_did_holder_mismatch/);
  });

  it("submit_intent handler throws on holder mismatch (default verifyHolderBinding)", async () => {
    await expect(
      submitIntentTool.handler({
        cart_id: "cart_xyz",
        quote_id: "quote_xyz",
        intent_mandate_vc: vcWithHolder,
        cart_mandate_vc_signed: "eyJhbGciOi...cart",
        buyer_did: otherDid, // mismatch — VC.holder = buyerDid
        customer_email: "buyer@example.com",
        language: "en",
        idempotency_key: "idem_abcdef123",
      }),
    ).rejects.toThrow(/buyer_did_holder_mismatch/);
  });

  it("submit_intent handler succeeds when holder == buyer_did", async () => {
    const out = await submitIntentTool.handler({
      cart_id: "cart_xyz",
      quote_id: "quote_xyz",
      intent_mandate_vc: vcWithHolder,
      cart_mandate_vc_signed: "eyJhbGciOi...cart",
      buyer_did: buyerDid, // matches VC.holder
      customer_email: "buyer@example.com",
      language: "en",
      idempotency_key: "idem_abcdef123",
    });
    expect(out.order_id).toMatch(/^ord_stub_/);
  });

  it("submit_intent handler skips check for opaque JWT VC (no top-level holder)", async () => {
    // Opaque wire string — caller-side verifier (apps/api) is authoritative.
    const out = await submitIntentTool.handler({
      cart_id: "cart_xyz",
      quote_id: "quote_xyz",
      intent_mandate_vc: "eyJhbGciOi...opaque_jwt",
      cart_mandate_vc_signed: "eyJhbGciOi...cart",
      buyer_did: buyerDid,
      customer_email: "buyer@example.com",
      language: "en",
      idempotency_key: "idem_abcdef123",
    });
    expect(out.order_id).toMatch(/^ord_stub_/);
  });
});

// ─── FU-0062-2.10 ─ CartMandate.refundable optional field ──────────────
describe("CartMandatePayloadSchema.refundable (FU-0062-2.10, AP2 §4.1.1)", () => {
  const baseValid = {
    type: "CartMandate" as const,
    cart_id: "cart_xyz",
    cart_hash: "a".repeat(64),
    total_usd: "10.00",
    currency: "USD",
    expires_at: new Date().toISOString(),
    issuer: "did:web:semore.net",
    payee: { id: "mer_1", display_name: "Acme" },
    payment_method_token: "tok_opaque_xyz",
    intent_hash: "b".repeat(64),
  };

  it("accepts refundable: true", () => {
    const parsed = CartMandatePayloadSchema.parse({ ...baseValid, refundable: true });
    expect(parsed.refundable).toBe(true);
  });

  it("accepts refundable: false", () => {
    const parsed = CartMandatePayloadSchema.parse({ ...baseValid, refundable: false });
    expect(parsed.refundable).toBe(false);
  });

  it("accepts payload without refundable (optional, undefined)", () => {
    const parsed = CartMandatePayloadSchema.parse(baseValid);
    expect(parsed.refundable).toBeUndefined();
  });
});

// ─── FU-0062-2.13 ─ DID_REGEX strict pct-encoded ABNF ─────────────────
describe("DID_REGEX pct-encoded strict ABNF (FU-0062-2.13, W3C DID Core §3.1)", () => {
  it("accepts a valid %HH pct-encoded sequence (did:web:semore.net%2Ftenant)", () => {
    expect(DID_REGEX.test("did:web:semore.net%2Ftenant")).toBe(true);
  });

  it("rejects a stand-alone % (did:web:bad%)", () => {
    expect(DID_REGEX.test("did:web:bad%")).toBe(false);
  });

  it("rejects %X (single hex digit, did:web:bad%X)", () => {
    expect(DID_REGEX.test("did:web:bad%X")).toBe(false);
  });

  it("rejects %XYZ (non-hex chars after %, did:web:bad%XYZ)", () => {
    expect(DID_REGEX.test("did:web:bad%XYZ")).toBe(false);
  });

  it("still accepts unchanged allowlist methods (regression guard)", () => {
    expect(BuyerDidSchema.parse("did:web:semore.net")).toBe("did:web:semore.net");
    const k = "did:key:z6MkhaXgBZDvotDkL5257faiztiGiC2QtKLGpbnnEGta2doK";
    expect(BuyerDidSchema.parse(k)).toBe(k);
  });
});

// ─── FU-0062-2.14 ─ holder ↔ credentialSubject.id strict mismatch ─────
describe("parseIntentMandateVc holder vs subject.id (FU-0062-2.14, W3C VC §A.4)", () => {
  const buyerDid = "did:web:buyer.example";
  const otherDid = "did:web:other.example";

  it("strict mode passes when both equal", () => {
    const vc = JSON.stringify({
      "@context": ["https://www.w3.org/2018/credentials/v1"],
      type: ["VerifiableCredential", "IntentMandate"],
      holder: buyerDid,
      proof: { type: "Ed25519Signature2020", proofValue: "z..." },
      credentialSubject: { id: buyerDid, intent: "buy" },
    });
    const out = parseIntentMandateVc(vc, { strict: true });
    expect(out.holder).toBe(buyerDid);
    expect(out.credentialSubject["id"]).toBe(buyerDid);
  });

  it("strict mode throws when both present but disagree", () => {
    const vc = JSON.stringify({
      "@context": ["https://www.w3.org/2018/credentials/v1"],
      type: ["VerifiableCredential", "IntentMandate"],
      holder: buyerDid,
      proof: { type: "Ed25519Signature2020", proofValue: "z..." },
      credentialSubject: { id: otherDid, intent: "buy" },
    });
    expect(() => parseIntentMandateVc(vc, { strict: true })).toThrow(
      /intent_mandate_vc\.holder_subject_mismatch/,
    );
  });

  it("strict mode tolerates holder-only (W3C VC §A.4 fallback)", () => {
    const vc = JSON.stringify({
      "@context": ["https://www.w3.org/2018/credentials/v1"],
      type: ["VerifiableCredential", "IntentMandate"],
      holder: buyerDid,
      proof: { type: "Ed25519Signature2020", proofValue: "z..." },
      credentialSubject: { intent: "buy" },
    });
    const out = parseIntentMandateVc(vc, { strict: true });
    expect(out.holder).toBe(buyerDid);
  });
});

// ─── FU-0062-2.15 ─ error code namespace 통일 (intent_mandate_vc.*) ───
describe("error code namespace unification (FU-0062-2.15)", () => {
  const buyerDid = "did:web:buyer.example";
  const otherDid = "did:web:other.example";
  const vcWithHolder = JSON.stringify({
    "@context": ["https://www.w3.org/2018/credentials/v1"],
    type: ["VerifiableCredential", "IntentMandate"],
    holder: buyerDid,
    proof: { type: "Ed25519Signature2020", proofValue: "z..." },
    credentialSubject: { intent: "buy" },
  });

  it("submit_intent throws exact `intent_mandate_vc.buyer_did_holder_mismatch`", async () => {
    await expect(
      submitIntentTool.handler({
        cart_id: "cart_xyz",
        quote_id: "quote_xyz",
        intent_mandate_vc: vcWithHolder,
        cart_mandate_vc_signed: "eyJhbGciOi...cart",
        buyer_did: otherDid,
        customer_email: "buyer@example.com",
        language: "en",
        idempotency_key: "idem_abcdef123",
      }),
    ).rejects.toThrowError(
      // Exact match — leading namespace prefix MUST be present, no bare alias.
      new Error("intent_mandate_vc.buyer_did_holder_mismatch"),
    );
  });

  it("parseIntentMandateVc strict mode throws exact same code (single source of truth)", () => {
    expect(() =>
      parseIntentMandateVc(vcWithHolder, { strict: true, buyerDid: otherDid }),
    ).toThrowError(new Error("intent_mandate_vc.buyer_did_holder_mismatch"));
  });
});

// ─── FU-0062-2.16 ─ verifyProofVerificationMethod (W3C VC §4.7) ───────
describe("verifyProofVerificationMethod (FU-0062-2.16)", () => {
  const holderDid = "did:web:buyer.example";

  it("accepts <did>#<keyId> (DID URL with fragment)", () => {
    expect(
      verifyProofVerificationMethod(
        { verificationMethod: `${holderDid}#key-1` },
        holderDid,
      ),
    ).toBe(true);
  });

  it("accepts bare <did> (implicit key id)", () => {
    expect(
      verifyProofVerificationMethod({ verificationMethod: holderDid }, holderDid),
    ).toBe(true);
  });

  it("rejects a different DID prefix", () => {
    expect(
      verifyProofVerificationMethod(
        { verificationMethod: "did:web:other.example#key-1" },
        holderDid,
      ),
    ).toBe(false);
  });

  it("rejects empty/missing proof", () => {
    expect(verifyProofVerificationMethod(undefined, holderDid)).toBe(false);
    expect(verifyProofVerificationMethod(null, holderDid)).toBe(false);
    // proof present but empty verificationMethod
    expect(
      verifyProofVerificationMethod({ verificationMethod: "" }, holderDid),
    ).toBe(false);
  });

  it("rejects <did># with empty fragment (FU-0062-2.16 syntactic strictness)", () => {
    expect(
      verifyProofVerificationMethod(
        { verificationMethod: `${holderDid}#` },
        holderDid,
      ),
    ).toBe(false);
  });
});

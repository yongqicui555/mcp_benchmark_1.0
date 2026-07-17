// quote_checkout — canonical Semore MCP commerce tool #4 (ADR-0062).
//
// 결제 직전 cart 재견적 (FX/shipping/duty/tax refresh) + AP2 CartMandate
// VC payload (서명 전 canonical) 산출. submit_intent 에서 서명된 VC 가
// 다시 들어와 결제 세션이 발급되는 2-step AP2 mandate 체인의 1단계.
//
// manifest.json:64-68 inputSchemaRef 와 정합.
// PAN/CVV 절대 통과 금지 (P4) — 본 tool 은 mandate payload 만 다룸.
//
// AP2 v0.1 spec §4.1.1 CartMandate 의 5 bound info (FU-0062-2.1):
//   - payee, payment_method_token, risk_signals, intent_hash 추가.
//   - cart_hash 는 ADR-0042 §19 invariant — SHA-256(JCS(payload-minus-cart_hash)).

import { z } from "zod";

/**
 * AP2 IntentMandate VC (사전 서명, search/대화 단계에서 발급).
 * 본 tool 은 검증만 — 실제 발급은 별도 ap2-agent 책임.
 *
 * 형식 = W3C Verifiable Credential JSON-LD 또는 JWT 인코딩 문자열.
 * 본 OSS 패키지는 wire-shape 만 정의 (parser/verifier 는 호출자 측 주입).
 */
export const IntentMandateVcSchema = z.string().min(1).max(16 * 1024);

/**
 * AP2 v0.1 spec §4.1.1 — Payer ("Verifiable identities for the user").
 * W3C VC Data Model 1.1 §4.4 — `holder` MUST be a URI; for DID-bound buyers
 * it is a DID (https://www.w3.org/TR/vc-data-model/#holder).
 *
 * Semore Phase 0 supports an explicit allowlist of 3 DID methods:
 *   - did:web   — Semore agent itself + merchants (`did:web:semore.net`)
 *   - did:key   — buyer self-issued key (Phase 1+ default)
 *   - did:jwk   — JWK direct (Stripe Click-to-Pay interop, draft-ietf-oauth-jwk)
 *
 * Other DID methods (did:ion / did:ethr / did:pkh / did:ebsi …) are
 * **explicitly rejected** at the OSS surface — adding support is tracked
 * as a follow-up FU per method (each requires resolver wiring + legal review).
 *
 * **FU-0062-2.13 — strict pct-encoded ABNF**:
 * W3C DID Core 1.0 §3.1 ABNF requires `idchar = ALPHA / DIGIT / "." / "-" /
 * "_" / pct-encoded` and `pct-encoded = "%" HEXDIG HEXDIG`. The previous
 * regex (`[a-zA-Z0-9._:%-]+`) admitted `%` as a stand-alone character —
 * `did:web:bad%` or `did:web:bad%XYZ` slipped through. This regex now
 * matches `%HH` strictly (exactly two hex digits per `%`). The `:` in the
 * character class accommodates DID method-specific identifiers that embed
 * additional path segments separated by `:` (e.g. `did:web:host:path:sub`).
 */
export const DID_REGEX =
  /^did:(web|key|jwk):(?:[a-zA-Z0-9._:-]|%[0-9a-fA-F]{2})+$/;

/**
 * Zod schema for AP2 `buyer_did`. Required + DID-method allowlist.
 * Reusable by callers that want to validate buyer_did independently
 * (e.g. apps/api before constructing a SubmitIntent payload).
 */
export const BuyerDidSchema = z
  .string()
  .min(1)
  .max(2048)
  .regex(DID_REGEX, "buyer_did must be did:web, did:key, or did:jwk");
export type BuyerDid = z.infer<typeof BuyerDidSchema>;

/**
 * FU-0062-2.16 — verifyProofVerificationMethod helper (W3C VC 1.1 §4.7).
 *
 * Syntactically validate that a Data-Integrity / Linked-Data proof's
 * `verificationMethod` URL points to a key controlled by `holderDid`:
 *   - `<holderDid>#<keyId>`  (DID URL with fragment — the common case)
 *   - `<holderDid>`          (bare DID — minority case where the key id is
 *                              implicit, e.g. did:key)
 *
 * This is **syntactic** only — full cryptographic verification (resolve the
 * controller's DID document, fetch the public key, verify the signature
 * over the JCS canonical) is the responsibility of `apps/api`'s
 * `did-issuer.ts` resolver (FU-0062-2.8 separate).
 *
 * References:
 *   - W3C VC Data Model 1.1 §4.7 (Proofs): https://www.w3.org/TR/vc-data-model/#proofs
 *     "verificationMethod ... a set of parameters that can be used together
 *     with a process to independently verify a proof."
 *   - W3C DID Core 1.0 §3.2 (DID URL Syntax): `did-url = did *( "/" path )
 *     [ "?" query ] [ "#" fragment ]`.
 */
export function verifyProofVerificationMethod(
  proof: { verificationMethod: string } | undefined | null,
  holderDid: string,
): boolean {
  if (!proof || typeof proof.verificationMethod !== "string") return false;
  if (typeof holderDid !== "string" || holderDid.length === 0) return false;
  const vm = proof.verificationMethod;
  if (vm === holderDid) return true;
  if (vm.startsWith(`${holderDid}#`) && vm.length > holderDid.length + 1) {
    return true;
  }
  return false;
}

/**
 * Decompose a DID string into its method + method-specific identifier.
 * Returns `null` when the input does not match the allowlist regex.
 *
 * Example:
 *   parseDid("did:web:semore.net") === { method: "web", identifier: "semore.net" }
 */
export function parseDid(
  input: string,
): { method: "web" | "key" | "jwk"; identifier: string } | null {
  const m = DID_REGEX.exec(input);
  if (!m) return null;
  const method = m[1] as "web" | "key" | "jwk";
  const identifier = input.slice(`did:${method}:`.length);
  return { method, identifier };
}

/**
 * Optional strict-mode parser for IntentMandate VC. Returns the decoded
 * `credentialSubject` if the wire string is a JSON-LD VC with the expected
 * `@context` / `type` / `proof` triple. Throws on structural mismatch.
 *
 * Caller side may opt-in for `quote_checkout` validation; the OSS handler
 * itself only enforces wire-shape (size). Integration is FU-0062-2.4 followup.
 *
 * Note: signature verification is **not** performed here — pair this with
 * the issuer's did:web key resolver (apps/api `did-issuer.ts`).
 *
 * **FU-0062-2.11 — buyer_did binding (W3C VC 1.1 §4.4 holder)**:
 * When `opts.buyerDid` is supplied AND `opts.strict` is true, the helper
 * additionally enforces that the VC's `holder` field (or, as a fallback,
 * `credentialSubject.id`) equals the supplied `buyerDid`. Mismatch throws
 * `intent_mandate_vc.buyer_did_holder_mismatch` so callers can surface a
 * stable error code (e.g. submit_intent handler).
 *
 *   - W3C VC Data Model 1.1 §4.4 (holder): https://www.w3.org/TR/vc-data-model/#holder
 *     "The holder of a verifiable credential is typically the subject … expressed
 *     using the holder property … the value of the holder property MUST be a URI."
 *   - W3C VC Data Model 1.1 §4.4 also notes that `credentialSubject.id` is the
 *     conventional binding for the subject DID; both are checked here.
 */
export function parseIntentMandateVc(
  raw: string,
  opts: { strict?: boolean; buyerDid?: string } = {},
): { credentialSubject: Record<string, unknown>; holder?: string } {
  if (!opts.strict) {
    // Non-strict: best-effort JSON parse, return empty subject if not JSON.
    try {
      const obj = JSON.parse(raw) as Record<string, unknown>;
      const subj = obj["credentialSubject"];
      const holder = obj["holder"];
      return {
        credentialSubject:
          subj && typeof subj === "object" ? (subj as Record<string, unknown>) : {},
        ...(typeof holder === "string" ? { holder } : {}),
      };
    } catch {
      return { credentialSubject: {} };
    }
  }
  let obj: unknown;
  try {
    obj = JSON.parse(raw);
  } catch {
    throw new Error("intent_mandate_vc.parse_failed:not_json");
  }
  if (!obj || typeof obj !== "object") {
    throw new Error("intent_mandate_vc.parse_failed:not_object");
  }
  const rec = obj as Record<string, unknown>;
  const ctx = rec["@context"];
  if (!Array.isArray(ctx) || ctx.length === 0) {
    throw new Error("intent_mandate_vc.parse_failed:missing_context");
  }
  const type = rec["type"];
  if (!Array.isArray(type) || !type.includes("VerifiableCredential")) {
    throw new Error("intent_mandate_vc.parse_failed:missing_vc_type");
  }
  if (!type.includes("IntentMandate")) {
    throw new Error("intent_mandate_vc.parse_failed:not_intent_mandate");
  }
  const proof = rec["proof"];
  if (!proof || typeof proof !== "object") {
    throw new Error("intent_mandate_vc.parse_failed:missing_proof");
  }
  const subj = rec["credentialSubject"];
  if (!subj || typeof subj !== "object") {
    throw new Error("intent_mandate_vc.parse_failed:missing_subject");
  }
  const subjRec = subj as Record<string, unknown>;
  const holderRaw = rec["holder"];
  const holder = typeof holderRaw === "string" ? holderRaw : undefined;
  const subjectId =
    typeof subjRec["id"] === "string" ? (subjRec["id"] as string) : undefined;
  // FU-0062-2.14 — strict holder ↔ credentialSubject.id consistency.
  //
  // W3C VC Data Model 1.1 §A.4 (Holders, Subjects, and Credentials —
  // Subject is the Holder) describes the conventional pattern that
  // `holder` and `credentialSubject.id` reference the same DID. When the
  // VC carries both, they MUST agree; otherwise the credential is
  // self-inconsistent and likely a confused-deputy / replay artifact.
  // Single-side presence (holder only OR credentialSubject.id only) is
  // tolerated — both are optional in the data model and either may be
  // omitted by the issuer (§A.4 fallback pattern).
  if (holder !== undefined && subjectId !== undefined && holder !== subjectId) {
    throw new Error("intent_mandate_vc.holder_subject_mismatch");
  }
  // FU-0062-2.11 — bind holder/subject.id to the caller-supplied buyer_did.
  if (opts.buyerDid !== undefined) {
    // W3C VC 1.1 §4.4: prefer top-level holder, else credentialSubject.id.
    const bound = holder ?? subjectId;
    if (bound === undefined) {
      throw new Error("intent_mandate_vc.buyer_did_holder_missing");
    }
    if (bound !== opts.buyerDid) {
      throw new Error("intent_mandate_vc.buyer_did_holder_mismatch");
    }
  }
  return {
    credentialSubject: subjRec,
    ...(holder !== undefined ? { holder } : {}),
  };
}

/**
 * AP2 v0.1 spec §4.1.1 — Payee identification (merchant-bound info).
 */
export const PayeeSchema = z.object({
  /** Merchant id (Semore-issued, e.g. `mer_abc123`). */
  id: z.string().min(1).max(128),
  /** Optional did:web for AP2 mandate proof chain. */
  did: z.string().min(1).max(256).optional(),
  /** Display name used in user-facing receipts. */
  display_name: z.string().min(1).max(256),
});
export type Payee = z.infer<typeof PayeeSchema>;

/**
 * AP2 v0.1 spec §4.1.1 — Risk signals (optional, PSP-bound info).
 *
 * AP2 v0.1 spec: §4.1.1 (Risk Payload) + §7.4 (Risk Signals) — both names refer to this schema.
 * Naming follows §7.4 (Risk Signals) for snake_case + plural noun convention.
 *
 * NOTE (PIPA): `ip` / `device_fp` are sensitive identifiers under PIPA.
 * Phase 0 sandbox 한정 — production 진입 시 별도 ADR (FU-0062-2 followup queue)
 * 로 retention/legal-basis 정의 필요. OSS schema 는 optional 표면만 노출.
 */
export const RiskSignalsSchema = z.object({
  ip: z.string().max(64).optional(),
  device_fp: z.string().max(256).optional(),
  /** PSP-issued behavioural risk score (0~1 or 0~100, PSP-defined). */
  behavioral_score: z.number().optional(),
  /** Free-form fraud flags (e.g. ["velocity_high", "geo_mismatch"]). */
  fraud_flags: z.array(z.string().min(1).max(64)).max(32).optional(),
});
export type RiskSignals = z.infer<typeof RiskSignalsSchema>;

export const QuoteCheckoutInput = z.object({
  cart_id: z.string().min(1),
  /** Optional. 사전 발급된 IntentMandate VC (없으면 anonymous quote). */
  intent_mandate_vc: IntentMandateVcSchema.optional(),
  /**
   * Buyer DID — AP2 holder (W3C VC 1.1 §4.4). Optional at the quote stage
   * to allow anonymous price preview; the `submit_intent` step requires it
   * (FU-0062-2.11). When supplied, the same allowlist (did:web/key/jwk)
   * applies as in `BuyerDidSchema`.
   */
  buyer_did: BuyerDidSchema.optional(),
  /** Optional payment method hint (Stripe/PayPal/Eximbay channel). */
  payment_method: z.enum(["stripe", "paypal", "eximbay"]).optional(),
  shipping_method: z.enum(["k_packet", "ems", "dhl_express"]).optional(),
});
export type QuoteCheckoutInput = z.infer<typeof QuoteCheckoutInput>;

/**
 * AP2 CartMandate VC payload (canonical, to-be-signed).
 *
 * 본 OSS wire-shape 는 minimal — 실제 issuer (`ap2-agent`) 는 W3C VC
 * `@context` + `type` + `credentialSubject` 를 채워서 Ed25519 서명을 부여.
 * 서명 후 결과를 `submit_intent.cart_mandate_vc_signed` 로 다시 전달.
 *
 * 4 신규 필드 (FU-0062-2.1, AP2 spec §4.1.1):
 *   - `payee`: merchant 식별 (id + did? + display_name)
 *   - `payment_method_token`: PSP 발급 opaque token (channel_key wrap, PCI safe)
 *   - `risk_signals`: optional PSP risk metadata (PIPA-sensitive — sandbox only)
 *   - `intent_hash`: SHA-256 hex chain link to IntentMandate (ADR-0042 §19)
 *
 * 추가 필드 (FU-0062-2.10, AP2 spec §4.1.1 5th bound info):
 *   - `refundable`: optional boolean — caller (merchant policy) 가 결정.
 *     true = refund 가능, false = no-refund. omitted = caller-default.
 *
 * cart_hash invariant (ADR-0042 §19):
 *   cart_hash = SHA-256(JCS(cart_payload_minus_cart_hash)) — RFC 8785
 *   즉 본 payload 에서 `cart_hash` 필드를 제거한 나머지를 JCS canonicalize 후
 *   SHA-256 hex 64. 검증은 issuer/verifier 측 책임. OSS 는 wire-shape regex 만.
 */
export const CartMandatePayloadSchema = z.object({
  type: z.literal("CartMandate"),
  cart_id: z.string(),
  /** Server-side canonical hash. cart_hash = SHA-256(JCS(cart_payload_minus_cart_hash)) — RFC 8785. */
  cart_hash: z.string().regex(/^[a-f0-9]{64}$/),
  total_usd: z.string(),
  currency: z.string(),
  fx_rate: z.string().optional(),
  /** ISO 8601 expiry — VC `exp` claim 매핑. */
  expires_at: z.string(),
  issuer: z.string(), // did:web:semore.net
  /**
   * Buyer DID — W3C VC 1.1 §4.4 holder mapping. Optional only when the
   * mandate is anonymous (rare); SubmitIntent requires it (FU-0062-2.11).
   */
  buyer_did: BuyerDidSchema.optional(),
  /** AP2 §4.1.1 — payee 식별. Merchant-bound info. */
  payee: PayeeSchema,
  /** AP2 §4.1.1 — PSP-issued opaque token (PortOne `channel_key` wrap, PAN/CVV X). */
  payment_method_token: z.string().min(1).max(2048),
  /** AP2 §4.1.1 — optional risk metadata (PIPA-sensitive in prod). */
  risk_signals: RiskSignalsSchema.optional(),
  /** ADR-0042 §19 — chain link to parent IntentMandate. SHA-256 hex of intent subject. */
  intent_hash: z.string().regex(/^[a-f0-9]{64}$/),
  /**
   * AP2 §4.1.1 5th bound info — caller (merchant policy) 가 결정.
   * true = refund 가능, false = no-refund. omitted = caller-default.
   */
  refundable: z.boolean().optional(),
});
export type CartMandatePayload = z.infer<typeof CartMandatePayloadSchema>;

export const QuoteCheckoutOutput = z.object({
  quote_id: z.string(),
  cart_id: z.string(),
  refreshed_total_usd: z.string(),
  tax_usd: z.string(),
  shipping_usd: z.string(),
  fx_rate: z.string().optional(),
  cart_mandate_payload: CartMandatePayloadSchema,
  /** Unix epoch (seconds). */
  expires_at: z.number().int(),
});
export type QuoteCheckoutOutput = z.infer<typeof QuoteCheckoutOutput>;

/**
 * Pluggable re-quote backend. Apps inject `lib/commerce.ts#requoteCart`
 * which (a) refreshes the cross-border quote against current FX/tariff/IOSS
 * tables and (b) hands the canonical CartMandate payload to the AP2 issuer
 * for signing in a downstream step.
 */
export interface CheckoutQuoter {
  (input: QuoteCheckoutInput): Promise<QuoteCheckoutOutput>;
}

const DEFAULT_QUOTE_TTL_SECONDS = 5 * 60; // 5 분 — re-quote 짧게
const DEFAULT_ISSUER = "did:web:semore.net";

/** Sentinel placeholder used by STUB_QUOTER. Production callers must replace. */
export const STUB_CART_HASH_SENTINEL = "0".repeat(64);
export const STUB_INTENT_HASH_SENTINEL = "0".repeat(64);

const STUB_QUOTER: CheckoutQuoter = async (input) => {
  const total = "0.00";
  const expiresAt = Math.floor(Date.now() / 1000) + DEFAULT_QUOTE_TTL_SECONDS;
  return {
    quote_id: `quote_stub_${input.cart_id}`,
    cart_id: input.cart_id,
    refreshed_total_usd: total,
    tax_usd: "0.00",
    shipping_usd: "0.00",
    cart_mandate_payload: {
      type: "CartMandate",
      cart_id: input.cart_id,
      // Deterministic 64-hex zero hash for the offline stub (placeholder).
      // Production callers MUST replace via injected quoter (leak guard below).
      cart_hash: STUB_CART_HASH_SENTINEL,
      total_usd: total,
      currency: "USD",
      expires_at: new Date(expiresAt * 1000).toISOString(),
      issuer: DEFAULT_ISSUER,
      ...(input.buyer_did !== undefined ? { buyer_did: input.buyer_did } : {}),
      payee: {
        id: "mer_stub",
        display_name: "Stub Merchant",
      },
      payment_method_token: "tok_stub_placeholder",
      intent_hash: STUB_INTENT_HASH_SENTINEL,
    },
    expires_at: expiresAt,
  };
};

export interface QuoteCheckoutToolOptions {
  quoter?: CheckoutQuoter;
  /**
   * Allow stub sentinel values (`cart_hash` / `intent_hash` = 64 zeros) to
   * pass through. Required when `process.env.NODE_ENV === "production"`
   * and a sentinel is detected — otherwise the handler throws to prevent
   * stub leakage. Defaults to `false`.
   */
  allowStub?: boolean;
}

/** Detect a stub-sentinel CartMandate that must not reach production. */
function isStubSentinel(payload: CartMandatePayload): boolean {
  return (
    payload.cart_hash === STUB_CART_HASH_SENTINEL ||
    payload.intent_hash === STUB_INTENT_HASH_SENTINEL
  );
}

function isProduction(): boolean {
  // Cloudflare Workers: `process` is shimmed; `globalThis.process` may be
  // undefined. Default to false to avoid false positives in Worker runtime.
  const proc = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process;
  return proc?.env?.["NODE_ENV"] === "production";
}

export function makeQuoteCheckoutTool(options: QuoteCheckoutToolOptions = {}) {
  const quoter = options.quoter ?? STUB_QUOTER;
  const allowStub = options.allowStub ?? false;
  return {
    name: "quote_checkout" as const,
    description:
      "Re-quote a cart immediately before checkout (refresh FX/shipping/duty/tax) and return the canonical AP2 CartMandate VC payload to be signed.",
    inputSchema: QuoteCheckoutInput,
    outputSchema: QuoteCheckoutOutput,
    handler: async (input: QuoteCheckoutInput): Promise<QuoteCheckoutOutput> => {
      const out = await quoter(input);
      // Leak guard — refuse to ship the deterministic stub sentinel into
      // production unless the caller has explicitly opted in via allowStub.
      if (isStubSentinel(out.cart_mandate_payload) && !allowStub && isProduction()) {
        throw new Error("cart_hash_stub_in_production");
      }
      return out;
    },
  };
}

export const quoteCheckoutTool = makeQuoteCheckoutTool();

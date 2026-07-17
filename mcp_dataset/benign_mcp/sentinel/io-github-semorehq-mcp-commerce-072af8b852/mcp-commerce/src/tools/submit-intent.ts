// submit_intent — canonical Semore MCP commerce tool #5 (ADR-0062).
//
// 서명된 IntentMandate + CartMandate VC 를 수신, PortOne 결제 세션 발급
// + order_id 반환. AP2 mandate 체인의 최종 단계 (intent → cart → submit).
//
// manifest.json:69-73 inputSchemaRef 와 정합.
//
// FU-0062-2.2 — output 에 `payment_mandate_vc` (서명된 PaymentMandate VC)
// 추가. ADR-0062 §2.3 의 3 단 mandate 체인 (Intent → Cart → Payment) 약속을
// OSS surface 에서도 충족. 실제 서명은 caller-injectable `paymentSigner` 가
// 담당 (apps/api `lib/ap2/payment-sign.ts` 가 production wiring).
//
// ⚠ P4 PCI: 본 tool 은 PAN/CVV 를 절대 받지 않는다. 카드 데이터는
// PortOne (Stripe/PayPal/Eximbay channel) 의 hosted UI 에서만 처리 →
// Semore 시스템에는 charge_id 만 전달. SAQ-A scope 유지.

import { z } from "zod";
import {
  IntentMandateVcSchema,
  CartMandatePayloadSchema,
  BuyerDidSchema,
  parseIntentMandateVc,
  type CartMandatePayload,
} from "./quote-checkout.js";

/** AP2 CartMandate VC (서명됨). quote_checkout 가 산출한 payload 의 서명 결과. */
export const SignedCartMandateVcSchema = z.string().min(1).max(16 * 1024);

/**
 * AP2 PaymentMandate VC (서명됨). submit_intent 의 caller-injectable
 * `paymentSigner` 가 발급. wire-shape 만 OSS 에서 정의 — 실제 서명/검증은
 * issuer (apps/api `lib/ap2/payment-sign.ts`) 책임.
 */
export const SignedPaymentMandateVcSchema = z.string().min(1).max(32 * 1024);

export const SubmitIntentInput = z.object({
  cart_id: z.string().min(1),
  quote_id: z.string().min(1),
  intent_mandate_vc: IntentMandateVcSchema,
  cart_mandate_vc_signed: SignedCartMandateVcSchema,
  /**
   * Buyer DID — required at submit-stage (FU-0062-2.11).
   * AP2 v0.1 spec §4.1.1 ("Verifiable identities for the user") + W3C VC
   * Data Model 1.1 §4.4 (`holder` MUST be a URI). Allowlist: did:web /
   * did:key / did:jwk. Other methods are explicitly rejected — adding
   * support is tracked as separate FUs (resolver wiring + legal review).
   */
  buyer_did: BuyerDidSchema,
  customer_email: z.string().email(),
  language: z.enum(["en", "ja", "de", "fr", "es", "ko"]).default("en"),
  /** Idempotency 키 — 동일 키 중복 호출 시 같은 order_id 반환. */
  idempotency_key: z.string().min(8).max(128),
});
export type SubmitIntentInput = z.infer<typeof SubmitIntentInput>;

export const SubmitIntentOutput = z.object({
  order_id: z.string(),
  /** PortOne 결제 세션 redirect URL (hosted UI). PAN/CVV 는 여기서만 입력. */
  payment_session_url: z.string().url(),
  payment_session_id: z.string(),
  /**
   * PSP 채널 — manifest.json 의 ACP/AP2 호환 PSP 라우팅 결과.
   * `stripe` | `paypal` | `eximbay`.
   */
  psp_channel: z.enum(["stripe", "paypal", "eximbay"]),
  status: z.enum(["pending", "requires_payment", "confirmed"]),
  /** Unix epoch (seconds) — 결제 세션 만료 시각. */
  expires_at: z.number().int(),
  /**
   * AP2 PaymentMandate VC (signed, wire-shape).
   * ADR-0062 §2.3 — 3 단 mandate 체인의 최종 leaf. caller-injected signer
   * (`paymentSigner`) 가 발급. apps/api `lib/ap2/payment-sign.ts` 가
   * production wiring (Ed25519, did:web:semore.net).
   */
  payment_mandate_vc: SignedPaymentMandateVcSchema,
});
export type SubmitIntentOutput = z.infer<typeof SubmitIntentOutput>;

/**
 * Pluggable PortOne session issuer. Apps inject the real implementation
 * backed by `lib/portone.ts#createSession` which:
 *   1. Verifies both VCs (Ed25519, did:web resolution).
 *   2. Picks PSP channel by buyer country + currency + risk score.
 *   3. POSTs to PortOne `/v2/payments/sessions` with cart hash + amount.
 *   4. Persists order row in D1 with mandate VC IDs for audit chain.
 */
export interface IntentSubmitter {
  (input: SubmitIntentInput): Promise<Omit<SubmitIntentOutput, "payment_mandate_vc">>;
}

/**
 * Pluggable PaymentMandate VC signer. Production wiring in apps/api
 * `lib/ap2/payment-sign.ts#signPaymentMandate` (Ed25519 over JCS canonical).
 *
 * 본 OSS 패키지는 issuer key 미보유 → 기본은 placeholder stub VC 반환.
 * stub 은 production (NODE_ENV) 에서 leak guard 가 throw 하므로 안전.
 */
export interface PaymentSigner {
  (
    intent_mandate_vc: string,
    cart_mandate_payload: CartMandatePayload,
  ): Promise<string>;
}

const DEFAULT_SESSION_TTL_SECONDS = 30 * 60; // 30 분

/** Sentinel placeholder used by STUB_PAYMENT_SIGNER. */
export const STUB_PAYMENT_MANDATE_VC = "stub.payment_mandate_vc.placeholder";

const STUB_SUBMITTER: IntentSubmitter = async (input) => {
  const sessionId = `psess_stub_${input.idempotency_key.slice(0, 8)}`;
  return {
    order_id: `ord_stub_${input.idempotency_key.slice(0, 8)}`,
    payment_session_url: `https://checkout.example/portone/${sessionId}`,
    payment_session_id: sessionId,
    psp_channel: "stripe",
    status: "requires_payment",
    expires_at: Math.floor(Date.now() / 1000) + DEFAULT_SESSION_TTL_SECONDS,
  };
};

const STUB_PAYMENT_SIGNER: PaymentSigner = async () => STUB_PAYMENT_MANDATE_VC;

export interface SubmitIntentToolOptions {
  submitter?: IntentSubmitter;
  /**
   * Caller-injectable PaymentMandate VC signer. Default returns a placeholder
   * string that is rejected by the leak guard in production.
   */
  paymentSigner?: PaymentSigner;
  /**
   * Allow stub `payment_mandate_vc` placeholder to flow in production.
   * Defaults to false. Required when running the OSS stub against
   * NODE_ENV=production deliberately (e.g. CI fixtures).
   */
  allowStub?: boolean;
  /**
   * FU-0062-2.11 — enforce W3C VC 1.1 §4.4 holder binding to `buyer_did`.
   *
   * When `true` (default) the handler best-effort parses
   * `intent_mandate_vc`; if the wire string is JSON-LD VC AND carries a
   * `holder` field or `credentialSubject.id`, that value MUST equal the
   * input `buyer_did`. Opaque JWT-encoded VCs (no holder/subject.id at
   * top level) skip the check — verification is caller responsibility.
   *
   * Set to `false` only for fixtures that intentionally exercise mismatch
   * paths or legacy callers that have not yet adopted DID-bound holders.
   */
  verifyHolderBinding?: boolean;
  /**
   * Optional CartMandate payload echo path. submit_intent does not parse
   * the signed VC by itself (that is verifier responsibility); apps/api
   * may inject a parsed payload via the submitter. The signer fallback
   * input is reconstructed minimally from the request for stub signers.
   */
}

function isProduction(): boolean {
  const proc = (globalThis as { process?: { env?: Record<string, string | undefined> } }).process;
  return proc?.env?.["NODE_ENV"] === "production";
}

export function makeSubmitIntentTool(options: SubmitIntentToolOptions = {}) {
  const submitter = options.submitter ?? STUB_SUBMITTER;
  const paymentSigner = options.paymentSigner ?? STUB_PAYMENT_SIGNER;
  const allowStub = options.allowStub ?? false;
  const verifyHolderBinding = options.verifyHolderBinding ?? true;
  return {
    name: "submit_intent" as const,
    description:
      "Submit signed AP2 IntentMandate + CartMandate VCs. Returns a PortOne payment session URL (Stripe/PayPal/Eximbay), an order_id, and a freshly signed PaymentMandate VC (3-tier AP2 mandate chain leaf). PAN/CVV never traverse Semore — handled exclusively by the chosen PSP (P4 PCI SAQ-A).",
    inputSchema: SubmitIntentInput,
    outputSchema: SubmitIntentOutput,
    handler: async (input: SubmitIntentInput): Promise<SubmitIntentOutput> => {
      // FU-0062-2.11 — bind W3C VC `holder` (or `credentialSubject.id`) to
      // input.buyer_did when the IntentMandate VC is a parseable JSON-LD VC.
      // Opaque JWT VCs (no top-level holder/subject) are passed through —
      // verifier (apps/api `did-issuer.ts`) is the authoritative check.
      if (verifyHolderBinding) {
        const parsed = parseIntentMandateVc(input.intent_mandate_vc); // non-strict
        const subjectId =
          typeof parsed.credentialSubject["id"] === "string"
            ? (parsed.credentialSubject["id"] as string)
            : undefined;
        const bound = parsed.holder ?? subjectId;
        if (bound !== undefined && bound !== input.buyer_did) {
          // FU-0062-2.15 — error code namespace 통일.
          // 모든 IntentMandate VC 검증 에러는 `intent_mandate_vc.<reason>` prefix.
          // (예: `intent_mandate_vc.parse_failed:*`, `intent_mandate_vc.holder_subject_mismatch`).
          throw new Error("intent_mandate_vc.buyer_did_holder_mismatch");
        }
      }
      const sessionResult = await submitter(input);
      // Best-effort cart payload reconstruction for the signer. Production
      // wiring should override `paymentSigner` to look up the canonical
      // payload by `cart_id` from D1; the stub does not need it.
      const minimalCartPayload: CartMandatePayload = {
        type: "CartMandate",
        cart_id: input.cart_id,
        cart_hash: "0".repeat(64),
        total_usd: "0.00",
        currency: "USD",
        expires_at: new Date().toISOString(),
        issuer: "did:web:semore.net",
        buyer_did: input.buyer_did,
        payee: { id: "mer_unknown", display_name: "(unknown)" },
        payment_method_token: "tok_unknown",
        intent_hash: "0".repeat(64),
      };
      const paymentMandateVc = await paymentSigner(
        input.intent_mandate_vc,
        minimalCartPayload,
      );
      // Leak guard — refuse to ship the placeholder VC into production
      // unless the caller has explicitly opted in via allowStub.
      if (paymentMandateVc === STUB_PAYMENT_MANDATE_VC && !allowStub && isProduction()) {
        throw new Error("payment_mandate_vc_stub_in_production");
      }
      return {
        ...sessionResult,
        payment_mandate_vc: paymentMandateVc,
      };
    },
  };
}

export const submitIntentTool = makeSubmitIntentTool();

// Re-export schema for convenience (apps/api may want CartMandatePayload).
export { CartMandatePayloadSchema };

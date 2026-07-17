# Changelog

All notable changes to `@semore/mcp-commerce` are documented here.
Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.4.1] — 2026-04-26 KST

> **Patch release** — backward-compatible. Tightens validation surface
> (rejects previously-invalid input only) + adds one optional schema
> field + one new helper export. No existing valid caller is affected.

### Added
- **FU-0062-2.10 — `CartMandatePayloadSchema.refundable: boolean.optional()`**.
  AP2 v0.1 spec §4.1.1 5th bound info — caller (merchant policy) decides;
  `true` = refund allowed, `false` = no-refund, omitted = caller-default.
- **FU-0062-2.16 — `verifyProofVerificationMethod(proof, holderDid)` helper**.
  Syntactic check (W3C VC 1.1 §4.7) that a Data-Integrity proof's
  `verificationMethod` URL points to the holder's DID
  (`<holderDid>#<keyId>` or bare `<holderDid>`). Cryptographic
  verification remains the responsibility of `apps/api`'s `did-issuer.ts`
  (FU-0062-2.8 separate). Exported from `@semore/mcp-commerce`.

### Changed
- **FU-0062-2.9 — `RiskSignalsSchema` alias docstring**. AP2 v0.1 spec
  refers to this concept as both "Risk Payload" (§4.1.1) and "Risk Signals"
  (§7.4); the schema docstring now records the alias and rationale for
  picking the §7.4 spelling (snake_case + plural noun).
- **FU-0062-2.13 — `DID_REGEX` strict pct-encoded ABNF**. Was
  `^did:(web|key|jwk):[a-zA-Z0-9._:%-]+$` which admitted a stand-alone
  `%`. Now `^did:(web|key|jwk):(?:[a-zA-Z0-9._:-]|%[0-9a-fA-F]{2})+$`,
  matching W3C DID Core 1.0 §3.1 (`pct-encoded = "%" HEXDIG HEXDIG`).
  Previously-valid DIDs (no `%`, or correct `%HH`) keep validating;
  invalid inputs that slipped through (`did:web:bad%`, `did:web:bad%XYZ`)
  are now rejected at parse time.
- **FU-0062-2.14 — `parseIntentMandateVc` strict mode now enforces
  holder ↔ credentialSubject.id consistency**. When *both* are present
  on the VC and disagree, throws
  `intent_mandate_vc.holder_subject_mismatch` (W3C VC 1.1 §A.4
  "Subject is the Holder"). Single-side presence (holder only OR
  credentialSubject.id only) is tolerated as before — §A.4 explicitly
  notes either may be omitted.
- **FU-0062-2.15 — error code namespace unified to `intent_mandate_vc.*`**.
  `submit_intent` previously threw a bare `buyer_did_holder_mismatch`;
  now throws the exact `intent_mandate_vc.buyer_did_holder_mismatch`
  string emitted by `parseIntentMandateVc` strict mode (single source
  of truth). Backward-compat: zero external publishes have shipped
  yet (npm registry has no 0.4.0 tag), so no caller can be relying
  on the bare alias. Existing `/buyer_did_holder_mismatch/` regex
  matchers (incl. our own tests) still match the prefixed version
  via substring.
- 16 new unit tests (66 → 82): `refundable` (3), pct-encoded ABNF (5),
  holder/subject mismatch (3), error code namespace exact-match (2),
  `verifyProofVerificationMethod` (5).

### Security / Compliance
- W3C DID Core 1.0 §3.1 ABNF compliance reduces the attack surface for
  malformed DIDs that previously squeaked past the schema and could
  confuse downstream resolvers.
- W3C VC 1.1 §A.4 enforcement closes a confused-deputy gap in which a
  signed VC could carry inconsistent holder vs subject identifiers
  while still being accepted by the `submit_intent` handler.

### References
- ADR-0062 Amendment §A.10 (this patch)
- AP2 v0.1 spec §4.1.1 / §7.4 — https://github.com/google-agentic-commerce/AP2
- W3C VC Data Model 1.1 §4.7 (Proofs) — https://www.w3.org/TR/vc-data-model/#proofs
- W3C VC Data Model 1.1 §A.4 — https://www.w3.org/TR/vc-data-model/#subject-is-holder
- W3C DID Core 1.0 §3.1 — https://www.w3.org/TR/did-core/#did-syntax

## [0.4.0] — 2026-04-26 KST

> **Breaking change**: `submit_intent.input.buyer_did` is now **required**
> and must match the DID method allowlist (`did:web` / `did:key` / `did:jwk`).
> Callers that previously omitted it (or sent unsupported methods such as
> `did:ion` / `did:ethr` / `did:pkh`) will now receive a Zod parse error.

### Added
- **FU-0062-2.11 — `buyer_did` required + W3C VC 1.1 §4.4 holder mapping**.
  AP2 v0.1 spec §4.1.1 ("Verifiable identities for the user") now expressed
  at the OSS surface:
  - `BuyerDidSchema` — Zod schema with DID method allowlist (3 methods:
    `did:web`, `did:key`, `did:jwk`). Other methods explicitly rejected;
    each future addition is gated on resolver wiring + legal review.
  - `DID_REGEX` — exported regex constant (`^did:(web|key|jwk):[a-zA-Z0-9._:%-]+$`).
  - `parseDid(input)` helper — decomposes a DID into `{ method, identifier }`
    or returns `null` for unsupported methods.
  - `parseIntentMandateVc(raw, { strict, buyerDid })` — new optional
    `buyerDid` opt enforces W3C VC `holder` (or fallback `credentialSubject.id`)
    matches the supplied DID. Throws `intent_mandate_vc.buyer_did_holder_mismatch`
    on mismatch (W3C VC Data Model 1.1 §4.4 `holder`).
  - `submit_intent` handler enforces holder binding by default
    (`verifyHolderBinding: true`); opt out via tool option only for
    fixtures or legacy callers (opaque JWT VCs without top-level holder
    fields skip the check — apps/api `did-issuer.ts` is authoritative).
- 19 new unit tests (47 → 66 PASS): DID schema/regex/parseDid (10),
  submit_intent buyer_did parse (3), holder binding (6).

### Changed
- **BREAKING**: `SubmitIntentInput.buyer_did` `z.string().min(1)` →
  `BuyerDidSchema` (required, regex-validated). See migration note above.
- `QuoteCheckoutInput.buyer_did` (still optional) and
  `CartMandatePayloadSchema.buyer_did` (still optional for anonymous
  mandates) tightened to the same `BuyerDidSchema` regex when present.

### Security / Compliance
- AP2 v0.1 spec §4.1.1 "Payer ... Verifiable identities for the user"
  now strictly enforced at the OSS surface — no more silent acceptance of
  unverifiable opaque buyer_did strings.
- W3C VC Data Model 1.1 §4.4 holder binding prevents a class of attacks
  where a signed IntentMandate VC could be replayed under a different
  buyer_did at the SubmitIntent step.

### References
- ADR-0062 Amendment §A.9 (this patch)
- AP2 v0.1 spec §4.1.1 — https://github.com/google-agentic-commerce/AP2
- W3C VC Data Model 1.1 §4.4 — https://www.w3.org/TR/vc-data-model/#holder
- ADR-0018 — `did:web:semore.net` trust boundary

## [0.3.0] — 2026-04-26 KST

### Added
- **ADR-0062 canonical 5-tool surface**: `search_product`, `get_product`,
  `create_cart`, `quote_checkout`, `submit_intent`. `manifest.json:48-73`
  와 1:1. `createMcpServer()` 가 정확히 5 tool 을 결정적 순서로 노출.
- **FU-0062-2.1 — `CartMandatePayloadSchema` AP2 §4.1.1 4 신규 필드**:
  `payee` (id + did? + display_name), `payment_method_token` (PSP-issued
  opaque, PAN-free), `risk_signals` (optional, PIPA-sensitive), `intent_hash`
  (SHA-256 hex chain link to IntentMandate, ADR-0042 §19).
- **FU-0062-2.2 — `submit_intent` output 에 `payment_mandate_vc`**.
  ADR-0062 §2.3 의 3 단 mandate 체인 (Intent → Cart → Payment) 약속
  OSS surface 에서 충족. `paymentSigner` caller-injectable
  (`apps/api/src/lib/ap2/payment-sign.ts` 가 production wiring).
- **FU-0062-2.3 — Stub leak guard**: `quote_checkout` 의 zero-hash
  cart_hash · `submit_intent` 의 placeholder VC 가 production
  (`NODE_ENV === "production"`) 에 leak 되면 throw. `allowStub: true`
  로만 우회 가능.
- **FU-0062-2.4 — `parseIntentMandateVc` helper export** (선택적
  strict mode). `@context` / `type` (`VerifiableCredential` +
  `IntentMandate`) / `proof` / `credentialSubject` 구조 검증.
  Integration 은 후속 FU.
- 추가 export: `PayeeSchema`, `RiskSignalsSchema`,
  `SignedPaymentMandateVcSchema`, `STUB_CART_HASH_SENTINEL`,
  `STUB_INTENT_HASH_SENTINEL`, `STUB_PAYMENT_MANDATE_VC`,
  `PaymentSigner` type.

### Changed
- `package.json#description` 을 ADR-0062 5-tool + AP2 chain 반영으로 갱신.
- `package.json#exports` 를 ESM-only (`.js`) 로 일원화 — 기존
  `.mjs/.cjs` 광고는 `dist/*.js` emit 과 mismatch 였음.
- canonical 5 subpath (`./tools/search-product` ~ `./tools/submit-intent`)
  추가. legacy 4 subpath (`./tools/search`, `./tools/cart`, `./tools/order`,
  `./tools/policy`) 유지 — backward-compat.

### Deprecated
- `searchProductsTool`, `buildCartTool`, `createOrderTool`,
  `getPolicyTool` 의 root export 는 0.4.0 에서 제거 예정. 그 사이 이용 시
  `@semore/mcp-commerce/tools/<name>` subpath 직접 import 권장.

### Security / Compliance
- PCI: PaymentMandate VC 는 PSP 발급 token 만 wrap — PAN/CVV unchanged.
- PIPA: `risk_signals.ip` / `device_fp` 는 sensitive identifier — Phase 0
  sandbox 한정. Production 진입 시 retention/legal-basis ADR 별도 필요
  (FU 큐화).

### References
- ADR-0062 — MCP Commerce Tool canonical 5-tool
- ADR-0042 §19 — cart_hash invariant
- AP2 v0.1 spec §4.1.1 — CartMandate 5 bound info

## 0.0.1 — 2026-04-20

- Initial skeleton: 4 tools (`search_products`, `build_cart`, `create_order`, `get_policy`)
  with Zod input/output schemas and deterministic stub handlers.
- `createMcpServer` transport-agnostic bootstrap.
- Apache-2.0 licensed.
- Source of Truth: Semore monorepo `packages/oss/mcp-commerce/` until repo split.
- Note: npm "@semore" scope reservation pending post-incorporation.

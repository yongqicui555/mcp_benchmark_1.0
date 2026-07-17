// @semore/mcp-commerce — public entrypoint.
//
// Canonical 5-tool surface (ADR-0062, 2026-04-26): manifest.json:48-73 와 1:1.
// Legacy 4-tool exports (search_products / build_cart / create_order / get_policy)
// 는 backward-compat 만 위해 유지 — 0.3.0 에서 제거 예정.

// --- Canonical tools (ADR-0062) -------------------------------------------
export {
  searchProductTool,
  makeSearchProductTool,
  SearchProductInput,
  SearchProductOutput,
  SearchProductResultItem,
  SUPPORTED_LANGS,
  SUPPORTED_CATEGORIES,
} from "./tools/search-product.js";
export type {
  ProductSearcher,
  SearchProductToolOptions,
} from "./tools/search-product.js";

export {
  getProductTool,
  makeGetProductTool,
  GetProductInput,
  GetProductOutput,
  ProductImageSchema,
  ProductSpecsSchema,
} from "./tools/get-product.js";
export type {
  ProductFetcher,
  GetProductToolOptions,
} from "./tools/get-product.js";

export {
  createCartTool,
  makeCreateCartTool,
  offlineStubPricer,
  CreateCartInput,
  CreateCartOutput,
  CartLineSchema,
  CartItemSchema,
  AddressSchema,
} from "./tools/create-cart.js";
export type {
  CartPricer,
  CartLine,
  CartItem,
  Address,
  CreateCartToolOptions,
} from "./tools/create-cart.js";

export {
  quoteCheckoutTool,
  makeQuoteCheckoutTool,
  parseIntentMandateVc,
  parseDid,
  verifyProofVerificationMethod,
  DID_REGEX,
  BuyerDidSchema,
  QuoteCheckoutInput,
  QuoteCheckoutOutput,
  CartMandatePayloadSchema,
  IntentMandateVcSchema,
  PayeeSchema,
  RiskSignalsSchema,
  STUB_CART_HASH_SENTINEL,
  STUB_INTENT_HASH_SENTINEL,
} from "./tools/quote-checkout.js";
export type {
  CheckoutQuoter,
  CartMandatePayload,
  Payee,
  RiskSignals,
  BuyerDid,
  QuoteCheckoutToolOptions,
} from "./tools/quote-checkout.js";

export {
  submitIntentTool,
  makeSubmitIntentTool,
  SubmitIntentInput,
  SubmitIntentOutput,
  SignedCartMandateVcSchema,
  SignedPaymentMandateVcSchema,
  STUB_PAYMENT_MANDATE_VC,
} from "./tools/submit-intent.js";
export type {
  IntentSubmitter,
  PaymentSigner,
  SubmitIntentToolOptions,
} from "./tools/submit-intent.js";

// --- Server bootstrap -----------------------------------------------------
export { createMcpServer, CANONICAL_TOOL_ORDER } from "./server.js";
export type {
  McpServer,
  McpServerOptions,
  McpToolDescriptor,
  CanonicalToolName,
} from "./server.js";

// --- Legacy / deprecated (kept for backward compatibility, ADR-0062) ------
// Removal target: 0.3.0.
//
// NOTE: 동명 충돌 회피 — `CartItemSchema`/`AddressSchema` 는 canonical
// (`./tools/create-cart`) 만 root index 에서 노출. Legacy 동명 심볼은
// `@semore/mcp-commerce/tools/cart` subpath 로 직접 import 필요.
export {
  searchProductsTool,
  SearchProductsInput,
  SearchProductsOutput,
} from "./tools/search.js";
export {
  buildCartTool,
  makeBuildCartTool,
  BuildCartInput,
  BuildCartOutput,
  BuildCartLineSchema,
} from "./tools/cart.js";
export type { BuildCartLine, BuildCartToolOptions } from "./tools/cart.js";
export {
  createOrderTool,
  CreateOrderInput,
  CreateOrderOutput,
} from "./tools/order.js";
export { getPolicyTool, GetPolicyInput, GetPolicyOutput } from "./tools/policy.js";

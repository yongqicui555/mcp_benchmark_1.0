# @semore/mcp-commerce

[![npm version](https://img.shields.io/npm/v/@semore/mcp-commerce.svg)](https://www.npmjs.com/package/@semore/mcp-commerce)
[![license](https://img.shields.io/badge/license-Apache--2.0-blue.svg)](./LICENSE)
[![MCP Registry](https://img.shields.io/badge/MCP%20Registry-io.github.semorehq%2Fmcp--commerce-34d399)](https://registry.modelcontextprotocol.io/v0/servers?search=semore)

Reference **Model Context Protocol (MCP)** server for K-product cross-border commerce —
five canonical tools that every agent-ready storefront should expose.

| # | Tool                | Purpose                                                                                       |
|---|---------------------|-----------------------------------------------------------------------------------------------|
| 1 | `search_product`    | Keyword / category / price / locale search across the K-product catalog                       |
| 2 | `get_product`       | Fetch a single SKU's full detail (i18n title/description, HS code, ship-from, lead time)      |
| 3 | `create_cart`       | Build cart with destination — returns itemized quote (subtotal + shipping + duty + import tax)|
| 4 | `quote_checkout`    | Re-quote cart immediately before checkout (refresh FX/duty), returns canonical CartMandate VC |
| 5 | `submit_intent`     | Submit AP2 IntentMandate VC + signed CartMandate, returns checkout URL + signed PaymentMandate|

> **Canonical 5-tool surface** per the [Semore MCP commerce spec](https://semore.net/docs/mcp).
> Production Semore MCP server runs at <https://mcp.semore.net>.
> This OSS package ships **schemas + reference handlers** so merchants can validate integrations locally.

## Install

```bash
npm install @semore/mcp-commerce zod
```

## Use the published MCP server (Claude Desktop / ChatGPT / Gemini)

```jsonc
// Claude Desktop config — `claude_desktop_config.json`
{
  "mcpServers": {
    "semore": {
      "command": "npx",
      "args": ["-y", "@semore/mcp-commerce"]
    }
  }
}
```

Or discover via the **official MCP Registry**:

```bash
curl "https://registry.modelcontextprotocol.io/v0/servers?search=semore"
# → io.github.semorehq/mcp-commerce@0.4.2
```

## Usage — schema-only (validate integrations)

```ts
import { searchProductTool } from "@semore/mcp-commerce/tools/search-product";

const parsed = searchProductTool.inputSchema.parse({
  q: "sunscreen",
  lang: "en",
  category: "kbeauty",
  limit: 10,
});

const result = await searchProductTool.handler(parsed);
```

## Usage — boot a minimal MCP server

```ts
import { createMcpServer } from "@semore/mcp-commerce";

const server = createMcpServer({
  // Wire your own catalog / cart / order resolvers here.
  // Default skeleton resolvers return deterministic fixtures useful for local tests.
});

// Then expose over your preferred transport (stdio, streamable-http, SSE).
```

## Companion adapters (5-protocol multi-adapter)

| Adapter                      | Spec                            | Status |
|------------------------------|---------------------------------|--------|
| [@semore/acp-adapter](https://www.npmjs.com/package/@semore/acp-adapter) | ACP (Stripe / PayPal)           | LIVE   |
| [@semore/ap2-adapter](https://www.npmjs.com/package/@semore/ap2-adapter) | AP2 (Google) — IntentMandate / CartMandate / PaymentMandate VC | LIVE   |
| [@semore/ucp-adapter](https://www.npmjs.com/package/@semore/ucp-adapter) | UCP (Google + Shopify)          | LIVE   |
| Visa TAP / MC Agent Pay      | Network agentic standards       | Phase 1 (signup) |

## Compliance & trust

- **PCI**: SAQ-A (no PAN/CVV transit through the MCP server)
- **PIPA §28-8**: cross-border consent flow active
- **AP2**: `did:web:semore.net` Ed25519 mandate signing (4-party card model preserved)
- **UCP**: `/ucp/capability` endpoint advertises `commerce.search`/`commerce.cart`/`commerce.checkout`

## Reference

- MCP spec: <https://modelcontextprotocol.io>
- Official MCP Registry: <https://registry.modelcontextprotocol.io>
- Semore production endpoint: <https://mcp.semore.net>
- Whitepaper (v0.1 in progress): <https://semore.net/docs/whitepaper/v0.1>
- Contact: `semore.hq@gmail.com` · GitHub [@semorehq](https://github.com/semorehq)

## License

Apache-2.0 — see [LICENSE](./LICENSE).

Copyright (c) Semore Founding Team.

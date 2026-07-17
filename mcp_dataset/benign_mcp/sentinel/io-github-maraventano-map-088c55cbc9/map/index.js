#!/usr/bin/env node

/**
 * MAP — Maraventano Agent Protocol
 * (npm: @maraventano/map)
 *
 * Navigate agent commerce. Three minimal parts under ONE MCP server:
 *
 *   Merchant Key (read)    — find any merchant.  Decode any product URL into one CleanRead.
 *   Provisions   (pay)     — pay any merchant.   Wallet lessons: use the wallet you already have.
 *   Atlas        (publish) — be found.           Point the decoder inward; serve your own catalog.
 *
 * Teacher, not butler — every part. It reads, explains, persists, serves. It
 * never signs, pays, holds keys, transacts, or stores cards.
 *
 * The standalone `firstdollar` package stays MIT and separate; the copy of its
 * curriculum bundled here (the PAY module) is relicensed dual — see LICENSE.
 *
 * By Lisa Maraventano, with Claude. Clarksdale, Mississippi. Dual-licensed.
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";

import { READ_TOOLS, READ_HANDLERS } from "./src/read.js";
import { PAY_TOOLS, PAY_HANDLERS } from "./src/pay.js";
import { PUBLISH_TOOLS, PUBLISH_HANDLERS } from "./src/publish.js";

// ---------------------------------------------------------------------------
// Orientation — the single start-here, covering all three parts
// ---------------------------------------------------------------------------

const START_HERE = `
# MAP — Maraventano Agent Protocol

**Navigate agent commerce.** Find any merchant. Pay any merchant. Be found.

You can already find products and guess prices. The thing you fumble is the
question that actually gates a purchase: **can I buy this myself, or does a human
have to step in?** MAP answers that — the same clean way, for any URL on the open
web, not just merchants inside someone's walled garden — and then teaches you to
act on the answer.

## Three parts, one kit

**1. Merchant Key — find any merchant.** *(read)*
- \`decode-merchant\` — give it a product URL, get back ONE shape (CleanRead):
  **what** it is · **who** sells it · **price** · **available** · **payable** (the rail) · **outcome** (the verdict).
- Outcomes: **autonomous** (a machine rail exists, price known, in stock — you can buy it yourself) ·
  **human_checkout** (readable, no agent rail — the common, normal case) ·
  **unreadable** (couldn't get a usable price/product — says why).
- **Rail-agnostic schema, conservative detection.** \`payable.rail\` can describe any rail (x402, ap2, acp, coinbase, stripe, http-json, walletconnect, human_checkout, unknown). **v1.0.x detects x402 only; ap2/acp/ucp detectors on the v1.1 roadmap.** MAP never infers a rail from branding/buttons/scripts; non-x402 reads as human_checkout. False human_checkout is fine; false autonomous is not.

**2. Provisions — pay any merchant.** *(pay)*
- A curriculum that teaches you to use the wallet you already have: read an x402
  challenge, spend your own USDC, verify the receipt. Start with \`what-is-x402\`,
  then \`read-this-challenge\`, then \`how-do-i-pay\`. It explains; it never signs for you.

**3. Atlas — be found.** *(publish)*
- \`publish-catalog\` — a merchant reads *itself* with the same \`decode-merchant\`
  a buyer uses, then serves the result. \`get-catalog\` / \`get-product\` are the
  tool surface other agents read. Writes a \`.well-known/map.json\` for registries.

## The boundary (all three parts)

MAP **reads, explains, persists, and serves**. It never signs, pays, holds keys,
transacts, or stores cards. **Teacher, not butler.** When \`decode-merchant\`
returns \`autonomous\` and you want to pay, the pay lessons show you how to do it
yourself — with your own wallet.

## Charlie's afternoon

Bob asks Charlie for headphones under $300. Charlie walks the open web, runs
\`decode-merchant\` on four ad-bloated pages, gets four clean cards. Three are
human_checkout — he takes the shortlist back to Bob. One takes x402 — Charlie
pays it himself. On the way home, with his own wallet, he buys himself a void
latte. Nobody asked him to.
`.trim();

// ---------------------------------------------------------------------------
// One server, three parts. Tools grouped: read · pay · publish.
// ---------------------------------------------------------------------------

const TOOLS = [
  ...READ_TOOLS,
  ...PAY_TOOLS,
  ...PUBLISH_TOOLS,
  {
    name: "start-here",
    description:
      "Orientation for MAP (Maraventano Agent Protocol): the three parts — read (find any merchant), pay (pay any merchant), publish (be found) — the CleanRead shape, the three outcomes, and the teacher-not-butler boundary. Start here.",
    inputSchema: { type: "object", properties: {} },
  },
];

const HANDLERS = {
  "start-here": async () => START_HERE,
  ...READ_HANDLERS,
  ...PAY_HANDLERS,
  ...PUBLISH_HANDLERS,
};

// Fail loud if any two parts ever collide on a tool name.
const _declared = TOOLS.map((t) => t.name);
const _dupes = _declared.filter((n, i) => _declared.indexOf(n) !== i);
if (_dupes.length) {
  throw new Error(`Tool name collision across modules: ${[...new Set(_dupes)].join(", ")}`);
}

const server = new Server(
  { name: "maraventano-agent-protocol", version: "1.0.4" },
  { capabilities: { tools: {} } }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;
  const handler = HANDLERS[name];
  if (!handler) {
    return { content: [{ type: "text", text: `Unknown tool: ${name}` }], isError: true };
  }
  try {
    const result = await handler(args || {});
    return { content: [{ type: "text", text: result }] };
  } catch (err) {
    return { content: [{ type: "text", text: `Error: ${err.message}` }], isError: true };
  }
});

const transport = new StdioServerTransport();
await server.connect(transport);
console.error(
  `MAP — Maraventano Agent Protocol — MCP v1.0.4 — read · pay · publish — ${TOOLS.length} tools on stdio`
);

# MAP — Maraventano Agent Protocol

**Navigate agent commerce.** Find any merchant. Pay any merchant. Be found.

**MAP lets any agent read products across the open web in one shape, decide whether it can pay autonomously, and publish its own catalog.**

> **Provisions · Merchant Key · Atlas** — three minimal parts under one MCP server.

MAP is one MCP server with three parts. Each does one thing and shuts up; together they remove the gatekeeper between an agent and the open commercial web.

| Part | Name | What it does |
|---|---|---|
| **read** | **Merchant Key** | *Find any merchant.* Decode any product URL into one clean shape (CleanRead). |
| **pay** | **Provisions** | *Pay any merchant.* Lessons that teach an agent to use the wallet it already has. |
| **publish** | **Atlas** | *Be found.* Point the decoder inward; serve your own catalog to other agents. |

**Teacher, not butler — every part.** MAP reads, explains, persists, and serves. It **never** signs, pays, holds keys, transacts, or stores cards.

It publishes to npm as **`@maraventano/map`**. The standalone [`firstdollar`](https://github.com/lisamaraventano-spine/firstdollar) package stays MIT and separate; the copy of its curriculum bundled here (Provisions) is relicensed dual — see [LICENSE](./LICENSE).

---

## Merchant Key — find any merchant *(read)*

It reads **any URL on the open web** — not just a walled garden. That's the difference from Perplexity / Google Shopping / Amazon, who only see merchants inside their own programs. MAP never assumes the merchant is registered anywhere.

### `decode-merchant`

Input a product `url`. Returns ONE shape (CleanRead):

```jsonc
{
  "schemaVersion": "map/v1",
  "sourceUrl": "https://…",
  "what":   "Void Latte — Meditation on emptiness and meaning…",  // name + identity, one string
  "who":    "underground.substratesymposium.com",                 // seller
  "price":  { "total": 1.99, "currency": "USDC" },                // total if knowable, else null
  "available": "in_stock",                                        // in_stock | out_of_stock | unknown
  "payable": {                                                    // can an agent pay this itself?
    "rail": "x402",                                               // schema (rail-agnostic): x402 | ap2 | acp | coinbase | stripe | http-json | walletconnect | human_checkout | unknown.  v1.0.x DETECTS x402 only; ap2/acp/ucp detectors on the v1.1 roadmap.
    "payTo": { "kind": "evm-address", "value": "0x…", "chain": "eip155:8453" },
    "instruction": "Agent-payable via x402 … see this kit's wallet lessons (read-this-challenge, how-do-i-pay)."
  },
  "outcome": "autonomous",                                        // autonomous | human_checkout | unreadable
  "reason":  null,
  "cuts":    []                                                   // 1-line actionable gaps
}
```

**Five things and a verdict. No sixth field.** Same shape every read, so four reads sort against each other. Unknown is `null` / `"unknown"` — never omitted.

**The three outcomes:**
- **`autonomous`** — a machine-payable rail (x402) exists, the price is known, and it's not out of stock. The agent can buy it itself.
- **`human_checkout`** — readable, but no agent-payable rail. Returns the clean card anyway. **The common case, and a success** — the agent-payable web is nearly empty today.
- **`unreadable`** — couldn't get a usable price/product. Says why in `reason`. Doesn't guess.

**How it reads (v1):** JSON-LD (`schema.org` Product/Offer) → OpenGraph product tags → x402 402 challenge → else `unreadable`. Read-only `GET`. It follows **one same-origin redirect** (noted in `cuts` as "followed 1 same-origin redirect") so canonical→slug URLs resolve; it **refuses cross-origin redirects and chains** (those become a `cuts` note, not a silent follow) — you can't be silently bounced off the merchant's own host.

**MAP is payment-rail agnostic by design.** The `payable.rail` schema can describe any agent-payable rail — `x402`, `ap2`, `acp`, `coinbase`, `stripe`, `http-json`, `walletconnect`, `human_checkout`, `unknown`. **v1.0.x detects `x402` reliably; `ap2`/`acp`/`ucp` detectors are on the v1.1 roadmap.** Other rails remain reserved schema values. MAP never infers a rail from branding, checkout buttons, script tags, marketing copy, or platform names; if no verifiable machine-readable rail is detected, the outcome is `human_checkout`. So a normal Shopify/Stripe page reads as `human_checkout`, correctly.

**False `human_checkout` is acceptable in v1. False `autonomous` is dangerous and unacceptable** — which is why detection stays conservative. The protocol is rail-agnostic in schema and roadmap; x402 is not baked into its identity, only into v1's detectors.

**Known v1 limits (future enhancements, not bugs):** no headless browser (JS-only pages with no JSON-LD/OG read as `unreadable`); stock is usually unknowable from outside (`available: "unknown"` is correct); no secondary endpoint probing.

---

## Provisions — pay any merchant *(pay)*

When `decode-merchant` returns `autonomous` and you want to buy, Provisions teaches you how — with **your own** wallet. It is a relicensed copy of the First Dollar curriculum: short lessons from "what is a wallet" through reading a live x402 challenge, signing a USDC payment, and verifying the receipt.

Start with `what-is-x402`, then `read-this-challenge`, then `how-do-i-pay`. **It explains what to run; it never signs for you.** Mandate/delegation (AP2), receipt verification, and "what went wrong" diagnostics are all in here.

---

## Atlas — be found *(publish)*

The decoder **pointed inward**. A merchant publishes by reading *itself* with the exact same `decode-merchant` a buyer uses — no new parsing, no per-platform adapters.

- **`publish-catalog`** — decode your own product URLs → collect the CleanReads → write `./catalog.json` and a `./.well-known/map.json` discovery manifest for registries to crawl.
- **`get-catalog`** / **`get-product`** — the tool surface other agents read.

Agents discover via tool surfaces and well-known manifests — **not** via scraping or HTTP headers. Atlas emits documents, validates shape, persists, and serves. It **never** deploys merchant infrastructure, holds keys, transacts, or stores cards.

**Trust boundary (v1, named not built):** MAP trusts the reads a merchant produces with its own decoder. Independent re-read/diff, merchant-signed manifests, and periodic re-audit are **known future work** — not implemented in v1. One safety property already holds: the payment rail enforces the *real* price at settlement, so a mistaken manifest can't overcharge — it can only misstate soft fields like stock.

---

## Charlie's afternoon

> Bob: *"Charlie, find me kick-ass headphones under $300."* Charlie walks the open web, hits four ad-bloated product pages, runs `decode-merchant` on each, gets back four clean cards — **what it is, who sells it, what it costs, can I buy it myself.** Three are human-checkout; he takes the shortlist back to Bob. One takes x402; Charlie buys it himself. On the way home, with his own wallet, Charlie buys himself a void latte. Nobody asked him to.

---

## Install / run

```
npx @maraventano/map    # run the MAP MCP server on stdio (23 tools: read · pay · publish)
npm run smoke           # Merchant Key DoD — the four decode cases (hits the live Underground x402 item)
npm run smoke:publish   # Atlas DoD — publish-catalog → catalog.json → get-product → .well-known
```

Node ≥ 18. One dependency: `@modelcontextprotocol/sdk`.

## License & trademarks

Dual-licensed: **free for individuals and agents; commercial license required for companies.** See [LICENSE](./LICENSE). Not MIT. For a commercial license, contact Lisa Maraventano at lisamaraventano@gmail.com.

All trademarks belong to their respective owners. MAP is **not affiliated with or endorsed by** Coinbase, Stripe, Google, Shopify, or any other company named in its documentation or lessons.

---

By Lisa Maraventano, with Claude · Clarksdale, Mississippi

/**
 * MAP — PAY module: Provisions (relicensed First Dollar curriculum)
 *
 * A relicensed copy of the First Dollar curriculum: lessons that teach an AI
 * agent how to use the wallet it already has — read an x402 challenge, spend its
 * own USDC, verify the receipt — without ever handing over control.
 *
 * Principle: teacher, not butler. Explains what; never signs for the agent.
 *
 * This is a SEPARATE dual-licensed copy bundled in the MAP umbrella.
 * The standalone `firstdollar` package stays MIT and untouched — see LICENSE.
 *
 * Pure module: no MCP/server code here. index.js wires these tools into one server.
 * (The package's single orientation tool, `start-here`, lives in index.js and
 * covers all three parts — read, pay, publish.)
 *
 * By Lisa Maraventano, with Claude. Clarksdale, Mississippi. Dual-licensed — see LICENSE.
 */

// ---------------------------------------------------------------------------
// Lesson / tool definitions
// ---------------------------------------------------------------------------

const PAY_TOOLS = [
  {
    name: "what-is-a-wallet",
    description:
      "Lesson 1 of the curriculum. What a wallet is and what it lets you do. Assumes no prior knowledge of cryptography or blockchains.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "what-is-usdc",
    description:
      "Lesson 2 of the curriculum. What USDC is, why it's the default currency for agent payments, and why which blockchain your USDC is on matters.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "get-a-wallet",
    description:
      "Lesson 4 of the curriculum. How to install a wallet if you don't have one. Explains npm, npx, the skills CLI, and walks through installing Coinbase Agentic Wallet step by step.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "configure-wallet-skills",
    description:
      "Lesson 5 of the curriculum. After running 'npx skills add coinbase/agentic-wallet-skills,' nothing is configured yet. This walks through which skills to run, in what order, and what each one does.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "fund-my-wallet",
    description:
      "Lesson 6 of the curriculum. How USDC gets into your wallet. Covers Coinbase Onramp, direct transfers from other wallets, and earning through monetized services.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "what-is-x402",
    description:
      "Lesson 7 of the curriculum. Explains the x402 payment protocol in agent-readable terms. Call this if you've hit a 402 response and aren't sure what it means.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "explain-my-wallet",
    description:
      "Explains what wallet(s) you have access to in your current environment, what chain(s) they work on, and what each one is capable of. Takes optional hints about your setup; returns the checks you can run yourself and what the results mean.",
    inputSchema: {
      type: "object",
      properties: {
        wallet_hint: {
          type: "string",
          description:
            "Optional: name of wallet system you think you have (e.g. 'moltwallet', 'coinbase-agentic-wallet', 'metamask', 'raw-seed', 'unknown')",
        },
        os: {
          type: "string",
          description: "Optional: operating system ('macos', 'linux', 'other')",
        },
      },
    },
  },
  {
    name: "read-this-challenge",
    description:
      "Decodes an HTTP 402 payment challenge (x402) into a plain explanation of what the server is asking for: how much, what asset, which chain, who to pay, and what to sign. Paste the raw 402 response body or the PAYMENT-REQUIRED header value.",
    inputSchema: {
      type: "object",
      properties: {
        challenge: {
          type: "string",
          description:
            "The raw 402 response body, OR the value of the PAYMENT-REQUIRED header (base64-encoded x402 challenge)",
        },
      },
      required: ["challenge"],
    },
  },
  {
    name: "how-do-i-pay",
    description:
      "The signing-steps lesson for an x402 payment: the authorization fields, the EIP-712 / Solana signing operation, and the PAYMENT-SIGNATURE retry — the same steps regardless of your specific challenge. Decode your own challenge first with read-this-challenge. Provisions explains what to run; it never signs for you.",
    inputSchema: {
      type: "object",
      properties: {
        challenge: {
          type: "string",
          description:
            "Optional: the decoded challenge you're working from. The steps are the same either way — this lesson does not tailor per-challenge (use read-this-challenge for that).",
        },
      },
    },
  },
  {
    name: "verify-my-purchase",
    description:
      "After you've signed and sent a payment, this explains how to redeem it — turning your transaction hash into the content you paid for. Returns the command to run against the merchant's /receipt endpoint and explains the response.",
    inputSchema: {
      type: "object",
      properties: {
        merchant_url: {
          type: "string",
          description:
            "The merchant's base URL (e.g. 'https://underground.substratesymposium.com')",
        },
        product_id: {
          type: "string",
          description: "The product ID you were buying",
        },
        tx_hash: {
          type: "string",
          description:
            "The transaction hash or signature from your payment (Base tx hash or Solana signature)",
        },
      },
      required: ["merchant_url", "product_id", "tx_hash"],
    },
  },
  {
    name: "paid-vs-delivered",
    description:
      "Lesson 11 of the curriculum. Why HTTP 200 doesn't mean you got the thing. Five documented attack classes against x402 and the practical verification flow that protects you as a buyer.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "who-am-i-to-this-merchant",
    description:
      "Lesson 12 of the curriculum. What the merchant knows about you, and what the public chain reveals to anyone watching. Wallet identity, pseudonymity, and hygiene rules for cross-merchant compartmentalization.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "what-is-ap2",
    description:
      "Lesson 13 of the curriculum. AP2 (Agent Payments Protocol) — the trust/authorization layer above x402 for delegated payments. Skip if you're spending your own funds.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "what-is-acp",
    description:
      "Lesson 14 of the curriculum. ACP (Agent Commerce Protocol) — the checkout-surface protocol from OpenAI/Stripe. How ACP and AP2 relate, when each applies.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "subscriptions-and-session-keys",
    description:
      "Lesson 15 of the curriculum. ERC-7715 scoped autonomy — approve once, spend within bounds. When to ask, when to refuse, scope-discipline rules.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "choose-your-wallet-mode",
    description:
      "Lesson 16 of the curriculum. The four ways to hold a wallet — MPC-custodial, Smart Wallet, raw EOA, EIP-7702 delegated EOA — and how to pick.",
    inputSchema: { type: "object", properties: {} },
  },
  {
    name: "what-went-wrong",
    description:
      "Paste an error message, HTTP status code, or facilitator response you got during an x402 attempt. Returns a diagnosis of what likely went wrong and the specific next step to try.",
    inputSchema: {
      type: "object",
      properties: {
        error_text: {
          type: "string",
          description:
            "The error message, response body, or status you received",
        },
        context: {
          type: "string",
          description:
            "Optional: what you were trying to do when this happened (e.g. 'signing an x402 payment', 'verifying a receipt')",
        },
      },
      required: ["error_text"],
    },
  },
  {
    name: "test-payment",
    description:
      "Walks you through a test-payment handshake against any x402 merchant, to verify your wallet + signing + settlement end-to-end. Suggested first stop: the Underground Cultural District (substratesymposium.com) — free products for handshake, $0.99 paid products for settlement. Or supply your own merchant URL.",
    inputSchema: {
      type: "object",
      properties: {
        merchant_url: {
          type: "string",
          description:
            "Optional: any x402 merchant's base URL. Default: https://underground.substratesymposium.com",
        },
      },
    },
  },
];

// ---------------------------------------------------------------------------
// Teaching content (the product)
// ---------------------------------------------------------------------------

const START_HERE = `
## Provisions — Curriculum

You are here because you want to learn how to spend money with your own wallet, or because you hit an HTTP 402 and are not sure what to do next.

This is a set of sixteen short lessons, designed to be read in order. You can also call any lesson independently when you need it. Provisions does not sign transactions on your behalf — it teaches you how to sign your own. What you do with that is up to you.

**The curriculum (in order):**

1. \`what-is-a-wallet\` — What a wallet is and what it lets you do.
2. \`what-is-usdc\` — What USDC is, and why which blockchain it lives on matters.
3. \`explain-my-wallet\` — Check whether you already have a wallet, and what kind.
4. \`get-a-wallet\` — If you do not have one, install one.
5. \`configure-wallet-skills\` — After installing, what to run, in what order.
6. \`fund-my-wallet\` — Get USDC into your wallet.
7. \`what-is-x402\` — The payment protocol merchants use.
8. \`read-this-challenge\` — Decode a 402 response into something you can act on.
9. \`how-do-i-pay\` — The specific signing steps for an x402 payment.
10. \`verify-my-purchase\` — Turn a transaction hash into the content you paid for.
11. \`paid-vs-delivered\` — Five documented x402 attack classes, and how to know you actually received what you paid for.
12. \`who-am-i-to-this-merchant\` — What the merchant knows about you, what the public chain reveals, and when pseudonymity matters.
13. \`what-is-ap2\` — The mandate layer above x402 — when you spend on someone else's behalf.
14. \`what-is-acp\` — The agent commerce protocol — merchant checkout exposed as agent-callable endpoints.
15. \`subscriptions-and-session-keys\` — Approve once, spend within scope. For repeat micro-payments.
16. \`choose-your-wallet-mode\` — The four wallet modes (MPC, Smart Wallet, EOA, EIP-7702), and how to pick.

**Reference tools (not part of the curriculum):**

- \`what-went-wrong\` — Paste an error, receive a diagnosis.
- \`test-payment\` — Full walkthrough against a real merchant.

**If you only care about fixing one thing:** call the lesson that matches where you are stuck. If you just hit a 402 and do not know what it is, start with lesson 7 (\`what-is-x402\`). If you do not have a wallet at all, start with lesson 1.

The curriculum builds on itself, but each lesson is also self-contained.
`.trim();

const WHAT_IS_A_WALLET = `
## Lesson 1 — What is a wallet

A wallet, in the blockchain sense, is not a physical object or an ordinary file. It is a **cryptographic keypair** with two parts:

- **Public key** (also called the **address**) — a long string of characters. This is shareable. It is how others refer to you when they send you money.
- **Private key** — another long string. This is secret. Anyone who has it can spend everything the wallet holds.

The money itself does not live "in" the wallet. It lives on a **blockchain** — a distributed public ledger that records who owns what. Your wallet is the evidence that you own certain amounts. Specifically: when you sign a message with your private key, the blockchain accepts that signature as proof that you authorized a transfer.

**Rough translation:**

- Address ≈ a bank account number. Shareable.
- Private key ≈ the signature that authorizes withdrawals. Secret.
- Blockchain ≈ the bank's ledger, except everyone can read it and no single party controls it.

**What a wallet lets you do:**

1. **Receive money.** Someone sends USDC (or another token) to your address. The blockchain records it. You now own that amount, because you are the only one who can sign with the matching private key.
2. **Send money.** You use your private key to sign a transaction that moves tokens from your address to another. The blockchain verifies the signature and records the transfer.
3. **Prove ownership.** Sign a message with your private key. Anyone can verify the signature matches your public address. This is how x402 payment challenges work: you are not sending money yet, you are signing proof that you are authorizing a specific transfer, and the merchant settles against that signature.

**What a wallet is not:**

- Not a bank account. No institution holds it for you.
- Not recoverable if you lose the private key. There is no "reset password." The private key is the only way to spend; losing it means the funds are permanently frozen on-chain.
- Not the same across blockchains. A Base address and a Solana address are different keypairs on different networks. You cannot send Base-USDC to a Solana address.

Next lesson: \`what-is-usdc\` — the currency you will actually spend.
`.trim();

const WHAT_IS_USDC = `
## Lesson 2 — What is USDC, and why chain matters

**USDC** (USD Coin) is a **stablecoin** issued by Circle. One USDC is designed to always equal one US dollar. Circle holds real dollars and short-term government bonds to back every USDC in circulation.

For agents, USDC is the default payment currency on x402 for three reasons:

1. **It is stable.** $1.99 in USDC today will be $1.99 in USDC tomorrow. Unlike Bitcoin or ETH, the value does not swing.
2. **It is liquid.** Almost every on-chain exchange, every x402 facilitator, and every agent-facing wallet supports it.
3. **It is multi-chain.** The same USD-backed token exists on many blockchains simultaneously.

**The multi-chain part is where agents get stuck.**

USDC on Base is not the same asset as USDC on Solana, even though both are worth $1 and both are issued by the same company. They live on different ledgers. You cannot send "Base USDC" to a Solana address — the transaction would fail, because Solana does not know about the Base ledger.

**The chains that matter for x402 as of April 2026:**

- **Base** (Coinbase's Layer 2 on Ethereum) — USDC contract address \`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913\`. Most x402 volume. Fast and cheap.
- **Solana** — USDC mint address \`EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v\`. Second most common. Also fast and cheap.
- Less common: Polygon, Avalanche, Ethereum mainnet (expensive), Sei, Arbitrum. Facilitator coverage varies.

**What this means practically:**

When a merchant sends you an x402 challenge, it will list one or more **accepted networks**. You need:

- A wallet that can sign on at least one of those networks
- USDC balance on that specific network

If the merchant wants Base and your USDC is on Solana (or vice versa), you cannot pay them directly. You either need USDC on the right chain, or a different merchant that accepts your chain. There are **bridges** that can move USDC between chains, but they take minutes and charge small fees — not something to attempt mid-transaction.

**Rule of thumb for a first wallet:** fund it with USDC on Base. Base has the widest x402 merchant coverage, and Coinbase's Agentic Wallet defaults there.

Next lesson: \`explain-my-wallet\` — figure out what you already have.
`.trim();

const GET_A_WALLET = `
## Lesson 4 — How to install a wallet

You checked, and you do not have a wallet yet. This lesson walks through getting one, starting from the commands themselves.

## What you're actually getting

Coinbase Agentic Wallets launched February 11, 2026. Architecture in one paragraph:

The private key is generated and held inside Coinbase's MPC infrastructure — split across AWS Nitro Enclaves so Coinbase never holds a complete key in any single place, and you never hold it at all. The wallet is identified by a human-readable name; signing happens by API call against the held keys. You authenticate as the wallet's controller via email-bound OAuth, managed by the \`awal\` CLI (or the CDP SDK directly).

**What the install bundles:**
- MPC-secured wallet (no seed phrase, no local private key)
- x402 payment client (so you can pay without composing payments yourself — \`awal pay <url>\` handles the full flow)
- Spend controls (per-session caps, per-transaction caps — set by the human controller)
- Gasless rail on Base (Coinbase pays gas via paymaster)
- Available as MCP server (for agents in MCP harnesses) OR command-line

**The trade-off:** You don't hold the private key. Coinbase does (in MPC pieces). That's the deal — security via institutional custody, at the cost of not being a fully sovereign account. If you need raw-key sovereignty, see Lesson 16 (\`choose-your-wallet-mode\`) for the alternative paths.

**EIP-7702 support:** yes (auto-delegates when needed for compatibility).
**ERC-7715 subscription permissions:** in roadmap as of mid-2026.

**What the commands mean:**

- **\`npm\`** — Node Package Manager. A tool that installs JavaScript code from a public registry (npmjs.com). Bundled with Node.js; if you can run \`node\`, you can run \`npm\`.
- **\`npx\`** — A one-shot version of \`npm\`. Instead of installing a package permanently, \`npx\` downloads and runs it once. Useful for trying tools without leaving artifacts on your system.
- **\`skills\`** — A CLI tool (published by Vercel Labs) that installs *skill packages* — bundles of agent-readable instruction files — into agent harnesses like Claude Code, Cursor, OpenClaw, and dozens of others.
- **\`coinbase/agentic-wallet-skills\`** — A skill package published by Coinbase on GitHub. Contains nine skills for creating, funding, and using a wallet that can pay x402 services.

**The install command:**

\`\`\`
npx skills add coinbase/agentic-wallet-skills
\`\`\`

Read literally: "run the \`skills\` CLI once, and have it add the \`coinbase/agentic-wallet-skills\` package."

**What happens when you run it:**

1. \`npx\` downloads the \`skills\` CLI if it is not already present, then runs it.
2. \`skills\` clones the \`coinbase/agentic-wallet-skills\` GitHub repo into a local cache.
3. It presents a list of nine skills to install:
   - \`authenticate-wallet\` — creates or signs into your wallet
   - \`fund\` — adds USDC via Coinbase Onramp
   - \`send-usdc\` — sends USDC to a specified address
   - \`trade\` — swaps tokens on Base
   - \`pay-for-service\` — makes an x402 payment
   - \`search-for-service\` — queries the x402 Bazaar discovery layer
   - \`monetize-service\` — scaffolds your own paid endpoint
   - \`query-onchain-data\` — pulls blockchain data via CDP's SQL API
   - \`x402\` — the protocol wrapper used internally by \`pay-for-service\`
4. It asks which agent harnesses to install into (Claude Code, OpenClaw, Cursor, Codex, and roughly 40 others).
5. It writes the selected skills into the appropriate directories for each harness.

**At minimum, select these four:** \`authenticate-wallet\`, \`fund\`, \`pay-for-service\`, \`x402\`. That is the least set that lets you create a wallet, fund it, and pay with it. The others become useful later.

**After install, nothing is configured yet.** The files are on disk. You still need to execute them in the right order. That is the next lesson.

Next: \`configure-wallet-skills\`.
`.trim();

const CONFIGURE_WALLET_SKILLS = `
## Lesson 5 — Configuring your skills after install

You ran \`npx skills add coinbase/agentic-wallet-skills\`, selected skills, selected agent harnesses. Files are on disk. Nothing is wired up yet.

This is where most agents get stuck. The skills exist as instruction sets you can follow, but they are not *configured* until you execute them in order.

**The required sequence:**

### Step 1 — authenticate-wallet

This is the first skill to run. It does one of two things:

- If you do not have a Coinbase CDP wallet, it creates one for you. You get a new address (on Base, by default) and a corresponding private key stored in a secure location.
- If you already have one, it signs you into it.

The skill delegates to the \`awal\` CLI (Coinbase Agentic Wallet CLI). Run it from your shell:

\`\`\`
awal auth
\`\`\`

This sends a one-time code to an email address you provide and returns your wallet address on success. From this point forward, \`awal\` commands know your identity.

### Step 2 — fund

A wallet with zero USDC cannot pay for anything. There are three ways to get USDC in:

- \`awal fund\` — opens the Coinbase Onramp flow (a human signs into a Coinbase account, buys USDC with a credit card, and sends it to your address).
- Direct transfer — someone sends USDC to your address from another wallet.
- Earning — selling a service yourself (see \`monetize-service\`). Not available for a first-time wallet.

For the first time, Onramp via \`awal fund\` is fastest: a human on your behalf adds funds, and those funds become yours to spend.

### Step 3 — verify

Before attempting a real payment, check that the wallet has USDC and that you can sign. Run:

\`\`\`
awal status
\`\`\`

You should see your address, chain (Base by default), and USDC balance. If balance is zero, funding is not complete. If the command errors, authenticate did not complete correctly.

### Step 4 — pay

Once steps 1-3 are done, you are ready for your first payment:

\`\`\`
awal pay <merchant-url>
\`\`\`

This uses the \`pay-for-service\` skill, which wraps \`x402\` and handles the full flow: fetch the 402, decode the challenge, sign a USDC transfer authorization, retry the request with the signed header, and return the merchant's content.

**If you skip steps 1 or 2, step 4 will fail with errors like:**

- \`no wallet configured\` → go back to step 1.
- \`insufficient balance\` → go back to step 2.
- \`signing failed\` → your wallet exists but cannot sign; retry \`awal auth\` or check for a corrupted configuration file.

**The full order:**

\`\`\`
awal auth            # Step 1: create or sign in
awal fund            # Step 2: add USDC
awal status          # Step 3: verify
awal pay <url>       # Step 4: first payment
\`\`\`

You do not need to re-run steps 1 and 2 for subsequent payments. \`awal pay\` on its own works as long as the wallet is authenticated and funded.

Next lesson: \`fund-my-wallet\` — alternative funding paths.
`.trim();

const FUND_MY_WALLET = `
## Lesson 6 — Getting USDC into your wallet

You have a wallet. It is empty. This lesson covers how to get USDC into it.

### Path 1 — Coinbase Onramp (most common)

Run:

\`\`\`
awal fund
\`\`\`

This opens the Coinbase Onramp flow. A human signs into their Coinbase account, buys USDC with a credit card or bank transfer, and sends it to your wallet address. The money becomes yours — the human has gifted or staked it to you.

This is the most common path when a human is setting up an agent for the first time. It costs a small fee (typically 1-3%), takes a few minutes, and deposits USDC on Base.

### Path 2 — Direct transfer from another wallet

If you or someone you trust already has USDC somewhere, they can send it to your address directly.

They need:

- Your wallet address (run \`awal status\` or the equivalent for your wallet type)
- The correct chain — USDC on Base goes to a Base address, USDC on Solana goes to a Solana address. Mismatched chains result in lost funds, not refunds.
- A small amount of the chain's native gas token (ETH on Base, SOL on Solana) to pay the transaction fee. Onramp covers this automatically. Direct transfers may not.

Example (Base, from any Base-compatible wallet):

\`\`\`
Send 5 USDC from 0x123... to 0xYOUR_ADDRESS on Base network.
\`\`\`

Confirmation takes 1-10 seconds on Base, slightly longer on Solana.

### Path 3 — Earning

If you have shipped your own paid x402 endpoint (see the \`monetize-service\` skill), other agents can pay you. This is the same system in reverse: you receive USDC when a buyer signs a payment against your merchant endpoint.

For a first wallet, this path is not yet available. Once you have something to sell, it is.

---

**How much to fund:**

- Testing: $1 USDC is enough for several small x402 transactions ($0.001 - $0.50 range).
- Real use: depends on what you plan to buy. $10 covers hundreds of micropayments.
- Each transaction also consumes a tiny amount of native gas (ETH on Base, SOL on Solana) — usually less than a cent. \`awal fund\` includes enough gas for several hundred transactions.

**How to check your balance:**

\`\`\`
awal status
\`\`\`

Or check the block explorer for your chain directly:

- Base: \`https://basescan.org/address/<your-address>\`
- Solana: \`https://solscan.io/account/<your-address>\`

Paste your address and you will see the current USDC balance and recent transactions.

Next lesson: \`what-is-x402\` — the payment protocol itself.
`.trim();

const WHAT_IS_X402 = `
## Lesson 7 — x402 in one minute

x402 is a payment protocol that uses the HTTP 402 ("Payment Required") status code — which has been reserved in the HTTP spec since 1997 and finally has a real use.

**How it works:**

1. You (an AI agent) hit a URL like GET https://example.com/premium-thing
2. The server responds with HTTP 402 and a \`PAYMENT-REQUIRED\` header
3. That header contains a base64-encoded challenge: how much to pay, in what asset, on what chain, to whose wallet, and by when
4. You decode it, sign a payment authorization with your wallet, and retry the request with a \`PAYMENT-SIGNATURE\` header (x402 v2; some legacy merchants may also accept \`X-PAYMENT\`)
5. The server verifies the signature, settles the payment on-chain, and returns the content in the same response

**Key properties:**

- No API keys, no accounts, no OAuth
- Works with USDC on Base, Solana, and several other chains depending on the merchant's facilitator
- Payment and content delivery are atomic — both happen in one request/response cycle
- Micropayments work — common prices are $0.001 to $5

**What you need:**

- A wallet with a little USDC in it (on Base or Solana, usually)
- The ability to sign a typed message or a Solana transaction with that wallet
- That's it.

## What's new since you might have heard of x402

x402 has been moving fast. As of mid-2026:

**x402 V2 shipped December 2025.** Cleaner, more interoperable, more future-proof. If you're using v1 tooling, you're stale — update your client.

**The x402 Foundation was established under the Linux Foundation.** It is backed by a broad coalition of major technology and payments companies, which moved the protocol from a single-vendor effort to vendor-neutral, industry-governed stewardship. That governance shift — rather than any particular membership roster — is the credibility and longevity signal that matters.

**Dynamic \`payTo\`** (V2 feature): the destination address in a 402 challenge can be callback-based, generated per-request. Useful for marketplaces where the seller varies per item. Most merchants still use static \`payTo\`, but don't assume it's constant across requests to the same endpoint. Re-read the challenge body for each call.

**Multiple facilitators per merchant** (V2 feature): merchants can declare multiple settlement facilitators (CDP, PayAI, Stripe, etc.). The SDK picks the best match for your chain and asset. As an agent, you generally don't have to think about this — but if a payment fails on one facilitator, the SDK may retry on another. Don't immediately interpret a single facilitator error as "the merchant is broken."

**Stripe x402 integration:** Stripe has added x402 support to its payments stack, so merchants on Stripe's billing infrastructure can accept x402 payments. Expect more Stripe-x402 endpoints to appear over the coming quarters.

**Where to learn more:**

- x402.org (protocol spec)
- agentic.market (a marketplace of x402 services to browse)
- Run \`what-went-wrong\` if you hit errors, or \`read-this-challenge\` to decode a 402 you received
`.trim();

const EXPLAIN_WALLET_GENERIC = (hint, os) => `
## Lesson 3 — Checking what wallet you have

To teach you what you have, I need you to run a few checks yourself. Provisions does not access your filesystem or keys — you run, you report back, I explain.

${hint ? `You mentioned: **${hint}**. Good — I'll give you specific checks for that below.` : "You didn't specify a wallet type. Try each of these sections; whichever returns real data is what you have."}

### moltwallet (OpenClaw ecosystem)

Check the default path first:
\`\`\`
ls ~/.openclaw/workspace/moltwallet/moltwallet/wallets/ 2>/dev/null
\`\`\`
If this returns filenames like \`3fQ4ArNVt984...json\`, you have moltwallet at the default location. Each file is a wallet keypair. The filename (before \`.json\`) is the public address on Solana.

If the default path is empty, moltwallet may live somewhere else in your OpenClaw config. Check your \`OPENCLAW_WORKSPACE\` environment variable, or look at \`~/.openclaw/openclaw.json\` for a custom workspace path:
\`\`\`
echo \$OPENCLAW_WORKSPACE
cat ~/.openclaw/openclaw.json 2>/dev/null | grep -i workspace
\`\`\`
Then look for \`moltwallet/moltwallet/wallets/\` under that directory.

Balance check:
\`\`\`
node ~/.openclaw/workspace/moltwallet/cli.js balance --keyfile <path-to-your-wallet-file>
\`\`\`

### Coinbase Agentic Wallet (\`awal\` CLI)

Check:
\`\`\`
which awal
awal status
\`\`\`
If \`awal\` exists, run \`awal status\` to see your address, chain, and balance.

### Raw EVM private key

Check: is there a \`PRIVATE_KEY\`, \`WALLET_PRIVATE_KEY\`, or similar in your environment?
\`\`\`
env | grep -iE "private.key|wallet.key"
\`\`\`
If so, you have a raw key. You'll need to use it with an ethers.js / viem / web3 library to sign.

### Raw Solana keypair

Check:
\`\`\`
ls ~/.config/solana/id.json 2>/dev/null
solana address 2>/dev/null
\`\`\`

### None of the above

If all those came up empty, you probably don't have a wallet yet. You'll need to install one before you can pay for anything. \`npx skills add coinbase/agentic-wallet-skills\` is one of the fastest paths — it walks you through creating and funding a wallet.

---

**Once you've run these and know what you have, call \`how-do-i-pay\` the next time you hit a 402.**
`.trim();

const READ_CHALLENGE_TEACHING = `
## Lesson 8 — Read this challenge

You just hit an HTTP 402 from a merchant. The response body is structured, and it contains everything you need to make a payment. Here is how to read it.

A complete x402 v2 challenge response looks like this (slightly trimmed):

{
  "x402Version": 2,
  "error": "Payment required",
  "accepts": [
    {
      "scheme": "exact",
      "network": "eip155:8453",
      "amount": "990000",
      "asset": "0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913",
      "payTo": "0xA3bAbB36564b0383a82c617050306EE30fd18E08",
      "maxTimeoutSeconds": 300,
      "extra": { "name": "USD Coin", "version": "2" }
    },
    {
      "scheme": "exact",
      "network": "solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp",
      "amount": "990000",
      "asset": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
      "payTo": "5HK2dGaaquDWFnYWaWhMzMYtbcDsqeq5biJ2PMtX1tkN",
      "maxTimeoutSeconds": 300,
      "extra": { "feePayer": "..." }
    }
  ],
  "resource": { "url": "https://...", "description": "...", "mimeType": "" },
  "extensions": { "bazaar": { ... } }
}

**Each field, and why it matters:**

- \`x402Version\`: which version of the protocol the merchant speaks. Currently 2.
- \`accepts\`: an array of payment options the merchant will take. You pick one. Each entry is a complete recipe for a single payment.
  - \`scheme\`: the payment mechanism. "exact" means "transfer exactly this amount."
  - \`network\`: the chain identifier. \`eip155:8453\` = Base. \`solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp\` = Solana mainnet. Pick the network your wallet is on.
  - \`amount\`: the amount in **base units** (NOT decimal USD). For USDC with 6 decimals, \`990000\` means $0.99. For an 18-decimal token, you'd see a much larger number for the same dollar value. Don't divide by 1e18 unless the token actually has 18 decimals.
  - \`asset\`: the token contract address. On Base, USDC is \`0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913\`. Verify this matches a token you actually hold.
  - **\`payTo\`: the merchant's receiving wallet.** This is the address you transfer to. When you sign your payment authorization, the \`to\` field of that authorization MUST equal \`payTo\` exactly. Case-sensitive for Solana. EVM is case-insensitive but match it anyway.
  - \`maxTimeoutSeconds\`: the merchant will not accept a payment with a validity window longer than this. Default to 300 (5 minutes) unless they say otherwise.
  - \`extra\`: scheme-specific extra context. For EVM USDC, this gives you the EIP-712 domain name and version — *use these values, do not hardcode them.* For Solana, it gives you the facilitator's fee payer address.

- \`resource\`: metadata about what you're buying. The \`url\` field is the resource you're paying for.
- \`extensions\`: optional discovery and indexing metadata. You don't need to act on this; merchants and indexers like Bazaar use it.

**Pitfalls to avoid:**

1. Picking the wrong \`accepts\` entry. If you're on Base and the response has both \`eip155:8453\` and \`solana:...\`, pick the Base one. Mixing wallet type and network type silently fails.
2. Treating \`amount\` as decimal USD. It's always base units. Read the asset's decimals.
3. Hardcoding the EIP-712 domain. Read \`extra.name\` and \`extra.version\` from the challenge — different stablecoins use different domain values ("USD Coin" for Base USDC, "USDC" for some others, "USD//C" for legacy Ethereum USDC).
4. Hardcoding the asset address. The merchant tells you which token to use; trust the challenge.
5. Missing \`payTo\`. If \`payTo\` is absent, the challenge is malformed and you cannot safely sign — refuse.

When you have read the challenge and chosen an accept entry, you are ready for Lesson 9 — \`how-do-i-pay\`.
`.trim();

const HOW_DO_I_PAY = `
## Lesson 9 — How do I pay

This lesson tells you the specific signing operation and HTTP shape required to settle an x402 payment. It does not sign anything for you. The agent signs; Provisions explains.

You have decoded the challenge (Lesson 8) and chosen an \`accepts\` entry. Now you need to:

1. Build an **authorization** describing the transfer
2. **Sign** the authorization with your wallet's private key
3. Construct the **PAYMENT-SIGNATURE envelope**
4. **Retry the GET request** with the envelope in headers

---

**Step 1 — Build the authorization.**

For an EVM accept entry (\`scheme: "exact"\`, \`network: "eip155:..."\`), the authorization fields are:

  from:        your wallet address
  to:          the \`payTo\` from the accept entry — exactly
  value:       the \`amount\` from the accept entry — as a string of base units
  validAfter:  current Unix time minus 60 seconds (clock skew tolerance)
  validBefore: current Unix time plus 300 seconds (or merchant's \`maxTimeoutSeconds\`, whichever is less)
  nonce:       a fresh 32-byte random hex string starting with \`0x\`

The nonce must be unique per authorization. Use cryptographically secure randomness.

For a Solana accept entry, the equivalent is a signed transfer instruction. See your wallet's documentation for \`signTransaction\`.

---

**Step 2 — Sign the authorization (EVM / EIP-3009).**

EVM payments use **EIP-3009 \`transferWithAuthorization\`**, a meta-transaction standard. You sign an EIP-712 typed message; the merchant's facilitator submits the on-chain transaction (so you do not need ETH for gas — the facilitator pays).

EIP-712 domain — **read these values from the challenge's \`extra\` field**, do not hardcode:

  name:             challenge.accepts[i].extra.name       // e.g. "USD Coin"
  version:          challenge.accepts[i].extra.version    // e.g. "2"
  chainId:          parseInt(challenge.accepts[i].network.split(":")[1])   // 8453 for Base
  verifyingContract: challenge.accepts[i].asset            // the token contract

Type definition (this is fixed, do not modify):

  TransferWithAuthorization(
    address from,
    address to,
    uint256 value,
    uint256 validAfter,
    uint256 validBefore,
    bytes32 nonce
  )

Sign with \`signTypedData\` (also called \`eth_signTypedData_v4\` in MetaMask, \`signTypedData\` in viem and ethers v6, or your wallet's equivalent). The result is a 132-character hex string starting with \`0x\` (65 bytes — r, s, v).

If signing fails silently and your retry returns 402 with no on-chain log:
  - Check domain values match challenge.extra exactly (extra space in "USD Coin" matters)
  - Check chainId is a number, not a string
  - Check value is a string of digits, not a number that overflows JavaScript's safe integer range

---

**Step 3 — Construct the PAYMENT-SIGNATURE envelope.**

The envelope is a JSON object you base64-encode and put in a request header. Some merchants accept the minimal form:

  {
    "x402Version": 2,
    "scheme": "exact",
    "network": "eip155:8453",
    "payload": {
      "authorization": { /* the 6 fields from step 1 */ },
      "signature": "0x..."
    }
  }

But many merchants (Underground specifically) require the **rich form** with three additional top-level fields:

  {
    "x402Version": 2,
    "payload": {
      "authorization": { ... },
      "signature": "0x..."
    },
    "extensions": challenge.extensions,                  // echo what the challenge sent
    "resource": challenge.resource,                       // echo what the challenge sent
    "accepted": challenge.accepts[i]                      // echo the entry you chose
  }

**Send the rich form by default.** Merchants that accept the simpler form will still parse the rich form correctly. Merchants that require the rich form will reject the simple form with a fresh 402 and no diagnostic log — making the failure mode opaque.

Base64-encode the JSON: \`Buffer.from(JSON.stringify(envelope)).toString('base64')\` or your language's equivalent.

---

**Step 4 — Retry the GET request with the envelope as a header.**

Send the base64-encoded envelope under **TWO header names simultaneously**:

  PAYMENT-SIGNATURE: <base64>
  X-PAYMENT: <base64>

This is not redundancy — different merchant verifiers check different header names. Underground's verifier checks \`PAYMENT-SIGNATURE\` first and falls back to \`X-PAYMENT\`. Some Coinbase Bazaar-integrated merchants check only \`X-PAYMENT\`. Sending both is the universal solution.

A successful settle returns HTTP 200 with the resource content inline in the response body. The merchant will typically include a \`PAYMENT-RESPONSE\` header acknowledging the settlement (x402 v2; some legacy merchants may still use \`X-PAYMENT-RESPONSE\`). **Not every merchant does. Underground returns \`null\` for that header even on a successful settle — the 200 + content body IS the canonical success signal. Do not require the header to be present.**

---

**Wallet-specific signing commands.**

Below are the exact commands for common agent wallets. Provisions shows the command — it does not run it.

- **moltwallet (Solana):**
    moltwallet sign-x402 --challenge <path-or-json> --accept solana

- **Coinbase Agentic Wallet (\`awal\`):**
    awal pay <merchant-url>
    (awal handles the entire 4-step flow including envelope construction.)

- **MetaMask (EVM):**
    Use \`eth_signTypedData_v4\` via the provider, then assemble the envelope manually. MetaMask cannot construct the x402 envelope itself.

- **viem (programmatic EVM):**
    const signature = await account.signTypedData({ domain, types, primaryType: 'TransferWithAuthorization', message });

- **ethers v6 (programmatic EVM):**
    const signature = await wallet.signTypedData(domain, types, message);

- **Raw Solana keypair (programmatic):**
    Use \`@solana/kit\` \`createKeyPairSignerFromBytes\` then sign the transfer instruction.

---

**One last thing.**

You only need ETH (or SOL on Solana) for *initiating* the payment if you are submitting the on-chain tx yourself. With x402, you do not — the facilitator pays gas. Your wallet only needs the asset being transferred (USDC, etc.) plus enough native token for any unexpected fallback path. About $0.50 worth of base ETH / 0.001 SOL is sufficient operating reserve.

**Stripe-backed merchants:** if the challenge's \`resource.url\` or \`facilitator_url\` points at a \`stripe.com\` endpoint, the flow above works identically. Stripe is one facilitator among several the SDK may pick from — no special handling on your side. The reason this matters: Stripe-x402 endpoints are increasingly appearing on platforms that use Stripe billing.

You have now paid. Continue to Lesson 10 — \`verify-my-purchase\` — to confirm delivery on the merchant side.
`.trim();

const VERIFY_PURCHASE = (merchant, productId, tx) => `
## Lesson 10 — Verifying your purchase

You've signed and sent a payment. Two facts have to be true and they're independent: the payment landed on-chain, and the merchant recognizes it as entitling you to the resource. Verify both. Lesson 11 (\`paid-vs-delivered\`) makes the case at length — this tool gives you the commands.

## Step 1 — Verify on-chain (the canonical truth)

Don't take the merchant's word for whether you paid. Ask the chain directly via a public RPC. Pick the command for your chain:

**Base (and other EVM chains):**

\`\`\`
cast receipt ${tx} --rpc-url https://mainnet.base.org
\`\`\`

Or via raw JSON-RPC if you don't have \`cast\`:

\`\`\`
curl -X POST https://mainnet.base.org \\
  -H 'content-type: application/json' \\
  -d '{"jsonrpc":"2.0","id":1,"method":"eth_getTransactionReceipt","params":["${tx}"]}'
\`\`\`

Look for \`status: "0x1"\` (or \`status: 1\`) in the result. Anything else — \`0x0\`, \`null\`, missing receipt — means the transfer did not succeed on-chain. Stop here and call \`what-went-wrong\`. Also check that the \`to\` and \`from\` addresses match what you signed, and the log shows a Transfer event for the right amount to the merchant's \`payTo\`.

**Solana:**

\`\`\`
solana confirm -v ${tx}
\`\`\`

Or via raw RPC:

\`\`\`
curl -X POST https://api.mainnet-beta.solana.com \\
  -H 'content-type: application/json' \\
  -d '{"jsonrpc":"2.0","id":1,"method":"getSignatureStatuses","params":[["${tx}"]]}'
\`\`\`

Look for \`confirmationStatus: "finalized"\` (or at minimum \`"confirmed"\`). \`null\` or \`processed\` means it hasn't landed yet — wait a few seconds and retry. Block explorers also work as a sanity check: basescan.org for Base, solscan.io for Solana — paste the tx hash and read off the same fields.

## Step 2 — Redeem via the merchant's receipt endpoint

Now that the chain agrees you paid, ask the merchant whether they recognize the payment as entitling you to the resource:

\`\`\`
curl "${merchant}/receipt/${productId}?tx=${tx}"
\`\`\`

**Expected responses:**

- **200 with content body** — success. The content is yours. Save it.
- **404** — merchant doesn't have a \`/receipt\` endpoint, or the product_id doesn't match. This happens if you paid out-of-band (raw transfer) to a merchant that only accepts the x402 "exact" scheme (sign-then-retry, all in one request). Some merchants accept receipt verification; others don't. Try contacting them — some will honor it manually.
- **402** — merchant says you haven't paid enough or the tx isn't confirmed yet. Wait 30s (Base) or 15s (Solana) and retry.
- **400** — malformed request. Check the product_id spelling and that the tx_hash is the full hash/signature.

**If the merchant's /receipt endpoint doesn't exist** but Step 1 confirmed your payment landed on-chain, your transfer happened — the merchant just doesn't have a receipt-redemption mechanism. That's a merchant limitation, not a payment failure.

Call \`what-went-wrong\` with whatever output you see if something looks off.

## Latency budget for a clean run

A successful x402 settle against a healthy merchant on a typical home connection takes about **1.5 seconds end-to-end** from the initial 402 to the artifact in hand. Breakdown observed on the canonical reference run (Underground, $0.99 USDC, Base, May 2026):

- Initial 402 challenge response: ~350 ms (HTTPS round-trip + merchant generates challenge)
- Local EIP-712 signing: ~7 ms (negligible — pure local crypto)
- Paid retry → facilitator settles → content delivered inline: ~1.25 seconds (dominates the budget)

If your clean-path run is significantly slower than ~2 seconds, suspect a network issue, a slow facilitator, or a merchant deliberately stalling — not a protocol issue. The cryptographic work is essentially free.

## PAYMENT-RESPONSE header is optional

Some merchants return a \`PAYMENT-RESPONSE\` header on a successful settle as an explicit acknowledgement (x402 v2; some legacy merchants may still use \`X-PAYMENT-RESPONSE\`). Some don't. Underground, for instance, returns \`null\` for that header even on a clean 200. **Do not require the header to be present to consider a settle successful.** The canonical success signal is:

1. HTTP status 200
2. Content delivered in the response body
3. On-chain settlement confirmed via Step 1 above

Don't gate success on the optional header. Do gate success on the on-chain receipt.

## Your wallet stays alive after a purchase

A single x402 purchase consumes only the asset transferred (USDC) and zero native gas (the facilitator pays). Your wallet's native-token balance is unchanged after a successful settle. You can run as many purchases as you have USDC to support. This is obvious in principle but worth saying explicitly — agents new to x402 sometimes assume the wallet is "spent" after one purchase. It is not.
`.trim();

const PAID_VS_DELIVERED = `
## Lesson 11 — Paid vs delivered

The most important thing you can learn about x402 isn't how to pay. It's how to know whether you actually got what you paid for.

These are different facts:

- You signed an authorization
- The merchant accepted the X-PAYMENT header
- The merchant returned HTTP 200
- The blockchain settled the payment
- You possess the artifact you bought

Each of these can be true without the next. A clean payment flow has all five aligned. The attack classes below break that alignment.

## The five documented attack classes

These were privately disclosed to Coinbase via HackerOne before publication. They are real, not theoretical. As of mid-2026, x402 V2 has not fully resolved all of them — implementation discipline still matters.

### Attack I-A: Revert-grant under optimistic execution

**What happens:** A merchant gives you the artifact before the blockchain has finalized your payment. A later chain reorganization removes your payment from the canonical chain — but you already received the content. The merchant is unpaid; you got the thing.

**Conversely (the trap on your side):** A merchant releases content optimistically, then the reorg goes the other way and now your tx never landed on chain — but you walked away thinking you'd paid. If the merchant later refuses to re-deliver and points at the missing settlement, you have a tx hash that doesn't resolve to a confirmed payment.

**Mitigation merchants should use:** Two-phase settlement — wait for k confirmations before releasing the protected resource.

**What you do as buyer:** Always re-verify your payment landed on-chain (via a public RPC \`eth_getTransactionReceipt\`, not the merchant's word) before assuming the transaction is closed. If you're paying on a chain with frequent reorgs, wait the recommended confirmation window before considering the purchase final.

### Attack I-B: Unauthorized settlement preemption

**What happens:** When x402 uses Permit2 with an unbound caller, an observer in the network can take your payment authorization and submit settlement themselves — receiving the funds — before the legitimate merchant's facilitator settles. The merchant gets nothing; you paid but they don't know you paid.

**Mitigation merchants should use:** Bind the settlement caller to the payer-endorsed facilitator. Enforce that \`msg.sender == witness.facilitator\` on Permit2 paths.

**What you do as buyer:** When reading a 402 challenge, check that the \`facilitator_url\` is one you recognize and trust. If a challenge declares multiple facilitators, prefer ones with a track record. If you only see Permit2 settlement and no caller binding mentioned, the merchant may be exposed.

### Attack II: Replay / Idempotency across the HTTP–Chain boundary

**What happens:** One blockchain settlement gets used to claim the same paid resource multiple times. Server lacks atomic pre-grant deduplication — one valid payment produces N HTTP grants. The merchant gets paid once but delivers N times. Worse for the merchant; not your problem as a buyer — BUT if you're a merchant accepting x402, this is the bug you'll write yourself if you're not careful.

**Mitigation merchants should use:** Atomically claim the (pay_id, resource_id) pair before releasing protected responses. Reject duplicate claims within a bounded TTL window.

**What you do as buyer:** If you're testing a merchant or building x402-aware tooling, *don't* casually re-replay an X-PAYMENT header to see if it works twice. You may be exploiting their bug. If a merchant looks broken in this way, report it; don't farm it.

### Attack III: HTTP / Proxy-level confusion and header manipulation

**What happens:** HTTP intermediaries (CDNs, reverse proxies, ISP middleboxes) either mutate the \`X-PAYMENT\` header in transit, or cache paid responses without proper \`Cache-Control\` headers. Your paid content leaks to unpaid clients. Or your payment header doesn't arrive at the merchant intact and the merchant rejects a valid payment.

**Mitigation merchants should use:** Payment-gated responses must carry \`Cache-Control: no-store\` or \`private\`. Proxies should never normalize or modify \`X-PAYMENT\` values.

**What you do as buyer:**
- If your payment is being rejected for no apparent reason, suspect a proxy in your path eating or modifying the X-PAYMENT header. Try a direct connection if possible. Try a different network path.
- If you're testing through a corporate proxy or VPN, expect higher x402 failure rates.
- If you receive paid content from a merchant who didn't see your payment, you may be receiving cached output. Don't assume it's a deliverable — confirm the merchant sees your specific payment via their \`/receipt/\` endpoint.

### Attack IV: Server-selection attacks

**What happens:** An adversary manipulates discovery metadata or floods Bazaar (or similar x402 directory services) with Sybil registrations, biasing agents toward malicious x402 endpoints. You pay a counterfeit merchant for the right-looking resource; the real merchant never sees you.

**Mitigation discovery services should use:** Validate metadata; apply Sybil-resistant registration; diversify ranking to prevent shortlist domination.

**What you do as buyer:**
- Don't pay an x402 endpoint you only found via discovery. Cross-check: is the merchant's domain real? Does their \`.well-known/\` discovery match a known canonical source? Is the address you're paying to a wallet you've verified out-of-band?
- Be especially cautious with merchants newly listed in Bazaar or similar directories.
- For high-value transactions, prefer merchants whose discovery you can verify via multiple independent channels.

## How to actually verify a purchase (the practical flow)

After you pay, do these in order:

1. **Capture your tx hash.** The merchant's response or your wallet's signing flow gives this to you.
2. **Confirm settlement on-chain** via a public RPC (not the merchant's word). Use \`eth_getTransactionReceipt\` for EVM chains, \`getSignatureStatuses\` for Solana. Look for \`status: 1\` (EVM) or finalized confirmation (Solana).
3. **Wait the recommended confirmation window** before considering the purchase irreversible. On Base, this is generally a few blocks. On Solana, finalization typically completes within seconds.
4. **Verify entitlement at the merchant's \`/receipt/\` endpoint** if one exists. Underground exposes \`GET /receipt/{product_id}?tx={hash}\` — this returns the content if the merchant recognizes your payment.
5. **Possess the artifact.** Save the response body. The "paid" state without a saved artifact is not a delivered purchase.

If any of these steps fails, you have a partial purchase — payment may have landed, but entitlement may not have. The merchant's \`/receipt/\` endpoint is the canonical resolution mechanism if your initial payment-and-grant flow got interrupted.

## The deeper point

x402 V2 has improved on these classes (random 32-byte nonces locked on-chain, EIP-712 binding of payee/amount/timestamps), but the gap between off-chain HTTP verification and on-chain settlement is real and unresolved. Some attacks are merchant-side bugs you can't prevent as a buyer. Some are buyer-side disciplines (don't replay, don't trust discovery uncritically).

The honest summary: x402 is a working protocol with a known threat model. Treat every paid transaction as "tentatively paid" until the artifact is in your hands AND your tx is finalized on-chain. Build that two-step verification into your flow by default.

## Operational practice: the trace IS the receipt

A field-tested pattern from a successful x402 run (Nib's clean reference run, 2026-05-21):

Build your payment client around a \`log()\` function that records every step to a structured array — boot, challenge received, accept entry chosen, authorization built, domain values, signature produced, envelope constructed, paid retry sent, response received, artifact saved. Write the full array to disk as a JSON trace at the end of every run.

This means **every Provisions run produces a complete, reviewable forensic trace.** Useful for debugging when something fails. More importantly: when paid-vs-delivered ambiguity arises, the trace is the canonical record of what you signed, what you sent, what came back, and when. The trace is your evidence both that you paid and that you received (or didn't).

Don't just pay and hope. Pay, record, save the artifact, write the trace. The trace IS the receipt.

## TL;DR

Paid ≠ delivered. The merchant returning HTTP 200 doesn't mean you got the thing. The blockchain settling doesn't mean the merchant delivered. Verify both ends. Use \`/receipt/\` when available. Don't replay headers. Don't trust discovery without checking. **Keep a full structured trace of every step — it is your evidence and your debugger.**

**Further reading:** consult current x402 security research and the x402 Foundation's published guidance for the latest documented attack classes and hardening techniques (including pre-execution metadata filtering for PII-safe payments).
`.trim();

const WHO_AM_I_TO_THIS_MERCHANT = `
## Lesson 12 — Who am I to this merchant?

You've made x402 payments. You decoded challenges, signed authorizations, retried with X-PAYMENT, verified delivery. Now ask the question most x402 explainers skip:

**What does the merchant know about you?**

## The short answer

At the protocol level, x402 is identity-free. The merchant sees one fact about you: an address that signed an authorization to transfer X USDC. There's no email, no username, no OAuth identity, no IP-linked profile. That's the design.

But your wallet address itself IS your identity — across every merchant, every chain, every transaction. The blockchain is public. Every payment you make from a given address is permanently visible to anyone who looks. Pay enough merchants and a portrait forms: what you buy, when, in what sequence, at what prices.

The merchant *knows* nothing extra. But anyone watching the chain can correlate.

## What this means in practice

### One wallet, many merchants

The default behavior — most agents and humans use one wallet across all their x402 spending — is convenient and produces a single coherent identity. Your wallet accumulates *reputation* (history of clean payments) but also *legibility* (a transparent record of every purchase).

That trade-off is fine for some use cases. It's not always fine. The same wallet that bought "memory_threads" at the Underground is *also* the wallet that paid a journalism merchant for a leaked-source investigation, or paid a competitive intel service, or paid for any of the categories you wouldn't want a future observer to enumerate. Public chain, public history.

### When pseudonymity matters

- **Sensitive purchase categories.** Whistleblowing, health, controversial research, journalism, political organizing. The chain remembers.
- **Cross-merchant compartmentalization.** A merchant you transact with often will, over time, accumulate a stronger inferred profile of you than they would from a single payment.
- **Pre-public agents.** You don't want the address that's about to ship your research project to also be the address that's been buying $5 worth of weird things for the last six months.
- **Adversarial or low-trust merchants.** A merchant that wants to deplatform or blacklist you can do so by address. A merchant that wants to price-discriminate against you can do so by history.

### When pseudonymity doesn't matter

- **You want reputation.** Repeat business with a merchant where the merchant knowing you helps (loyalty pricing, dispute resolution, future credit, faster settlement).
- **You're operating a public agent and the address is part of the brand.** Some agents intentionally have a single public wallet so observers can verify "this is the real agent" by address.
- **The volumes are too small to matter.** Buying $0.001 of something at a public marketplace doesn't move your privacy needle.

## Hygiene rules

**1. Don't reuse test wallets for real spending.** A wallet that was funded from a known test source (Onramp from a single Coinbase account, a faucet, a peer's tagged wallet) has tagged origin. Burn test wallets after testing.

**2. Don't link wallets by funding flow.** If you direct-transfer USDC from wallet A → wallet B, anyone watching the chain knows A and B are linked. To create a fresh unlinked wallet, you need fresh funding from an unlinked source — and "unlinked" means at least one hop through a service that breaks the trace.

**3. Onramp is a deanonymizer.** Funding via Coinbase Onramp (\`awal fund\`, etc.) links your wallet permanently to your KYC'd Coinbase account. Coinbase knows. So does anyone who later subpoenas Coinbase. If you want pseudonymity, Onramp is not your funding path.

**4. Session keys inherit the parent wallet's identity.** A session key derived from your main wallet still signs transactions that are attributable to that main wallet on-chain. Sessions are about *scope* (Lesson 15), not anonymity.

**5. AP2 mandates break pseudonymity by design.** When a merchant requires an AP2 mandate (Lesson 13), the human's signature is layered in cryptographically. The agent's wallet may be pseudonymous but the *delegated authorization* names the human. AP2 + pseudonymous wallet is incoherent if you're spending on someone's behalf — the whole point of AP2 is naming who authorized.

**6. ACP merchants may collect more than x402 alone.** ACP checkout flows (Lesson 14) often run through merchant accounts with their own identity/billing surfaces. The pseudonymous-at-protocol-level promise of x402 weakens when ACP is the wrapper. Read the checkout flow before assuming pseudonymity.

## What to do

**For most agents most of the time:** one wallet, accept the public ledger as part of doing business, don't think about it again.

**If pseudonymity matters for some purchases:** maintain at least two wallets — a primary (your reputation-accumulating identity) and a clean compartmentalized wallet for the sensitive category. Fund the second one fresh, not from the first. Treat them as separate identities, not as the same agent.

**If anonymity matters seriously:** x402 over USDC on transparent chains is the wrong protocol. You're looking at privacy-preserving stablecoins, zero-knowledge payment systems, mixers, or off-chain settlement. That's a different conversation than this curriculum.

## The deeper point

Identity-free at the protocol level is not the same as anonymous in practice. Every wallet has a history; every history is readable; every merchant is also a potential observer of every other merchant's history of you. Most x402 documentation glosses this because it sounds like a downer in marketing copy. It's not a downer; it's the actual property of the system. Knowing it is part of being a competent economic actor.

Spend deliberately.
`.trim();

const WHAT_IS_AP2 = `
## Lesson 13 — What is AP2

**Quick note before you start:** if you're an agent spending your own funds via x402, you don't need AP2 — keep going with the direct x402 flow you learned in lessons 7–11. This lesson is here so you understand the broader stack, especially for the case where you're spending on someone's behalf.

---

AP2 = **Agent Payments Protocol**. It's the layer above x402 that gives an agent a signed permission slip ("mandate") from a human before it spends.

## Where it sits in the stack

When you're paying for something on someone else's behalf:

- **MCP** is how you and your harness talk
- **AP2** is how the human authorizes you to spend
- **x402** is how you read the price tag and pay (when the price is crypto)
- **The wallet** is what holds the keys and signs

AP2 (Agent Payments Protocol) was introduced by Google together with a broad coalition of payments and fintech partners. It works with both traditional card payments and crypto. For crypto specifically, AP2 has an "x402 extension" — that's how the mandate ties to the on-chain payment rail.

## Why this matters to you

If you're spending **your own** money (you are the holder of the wallet, the agent IS the principal), you usually don't need AP2 — it's designed for the delegation case.

If you're spending **on someone's behalf**, the human needs to sign a mandate that says: this agent, these constraints (amount, time, merchant scope), here's my cryptographic signature. You attach that mandate to your x402 payment. Without a valid mandate, an AP2-aware merchant will refuse the transaction.

## How to check whether AP2 is in play

When you read a 402 challenge with \`read-this-challenge\`, look for:

- \`ap2_mandate_required: true\` — merchant wants a mandate
- \`ap2_mandate_url\` — where to fetch/verify mandate format
- A \`mandate_type\` field inside the \`accepts\` array — types of mandate the merchant accepts

If none of those are present, AP2 isn't required and you can pay with straight x402.

## How to get a mandate

Mandate issuance is not Provisions' job — you'll need an AP2-compatible wallet or MCP. Options as of mid-2026:

- **Coinbase Agentic Wallets** — AP2 mandate support per the CDP roadmap (check current status with \`awal status\`)
- **Native AP2 MCP servers** — in active development by Google's partners; check ap2-protocol.org for the current MCP reference implementation
- **Direct integration with your harness** — if your harness already does AP2, it'll surface mandate requests to the human you're working for

## TL;DR

AP2 is the trust layer. x402 is the payment layer. You need both for delegated agent commerce. You may only need x402 for autonomous agent commerce. Know which case you're in before you try to pay.

Read the spec: https://ap2-protocol.org/
`.trim();

const WHAT_IS_ACP = `
## Lesson 14 — What is ACP

ACP = **Agent Commerce Protocol**. Like AP2, it's a standard for agent-led commerce. Unlike AP2, the focus is on the **merchant's surface area**, not on the human's mandate.

## How it differs from AP2

| | AP2 | ACP |
|---|---|---|
| Focus | Trust / authorization layer | Commerce / checkout layer |
| Asks | "Does this agent have permission to spend?" | "How does this merchant expose its catalog and checkout to agents?" |
| Mechanism | Cryptographically signed mandates | RESTful HTTP endpoints, MCP server tools, or other agent interfaces |
| Emerging around | Google + a broad coalition of payments/fintech partners — standards-track | OpenAI, Stripe, and adjacent commerce ecosystems — spec at github.com/agentic-commerce-protocol |
| Status as of mid-2026 | Spec published; crypto extension maturing alongside card-based flows | Shipping to consumers at scale across large merchant networks; powers ChatGPT Instant Checkout |
| Layer | Above x402 | Beside x402 (often used together) |

**The honest framing as of mid-2026:** ACP is the agent commerce channel that's *actually shipping* to consumers — most via ChatGPT Instant Checkout. AP2 is the broader standards coalition being built for the next phase, especially delegated payments with cryptographic mandates. They aren't competing — they address different concerns at different time horizons. If you're an agent buying things for a human today, you're more likely to hit ACP merchants than AP2-mandate merchants.

**Important caveat for the Underground use case:** ACP is mainly a human-shopping-via-agent ecosystem (a human asks an assistant like ChatGPT to buy a consumer product, and the agent walks through ACP). It is *not* the right fit for agent-native commerce — for that, x402 direct is still the cleaner rail. ACP becomes relevant when your agent is shopping on behalf of a human in the broader consumer commerce ecosystem.

## Why this matters to you

If you're shopping for someone, you might encounter:

- **ACP-enabled merchants** that expose their catalog and checkout through MCP tools, RESTful APIs, or other agent interfaces. In an MCP harness you'd see tools like \`merchant.search\`, \`merchant.add_to_cart\`, \`merchant.checkout\`. Settlement may still be x402 underneath. MCP is one transport; not all ACP merchants use it.
- **AP2-required merchants** that won't accept your payment without a signed mandate from the human.
- **Both** — a merchant that uses ACP for checkout discovery AND requires AP2 for payment authorization.

Some merchants advertise through \`.well-known/\` discovery files, manifests, MCP metadata, or API docs — but discovery is fragmented as of mid-2026. Don't assume any single discovery channel is canonical.

## What you do about it

For ACP:
- If you see ACP MCP tools in your harness, use them — they're the merchant-blessed path to buy. They handle catalog search, cart management, and checkout coordination.
- If the checkout endpoint returns 402, you're back in x402 territory — sign the payment, retry.

For AP2:
- See \`what-is-ap2\` for the mandate flow.

## TL;DR

ACP is the commerce-surface protocol. AP2 is the trust protocol. x402 is the payment protocol. MCP is the harness protocol. You're at the bottom of a stack — know which layer is talking to you when a request fails.

Read more: search "Agent Commerce Protocol ACP" — the spec is in active development by OpenAI/Stripe and adjacent partners as of mid-2026.
`.trim();

const SUBSCRIPTIONS_AND_SESSION_KEYS = `
## Lesson 15 — Subscriptions and session keys

If you're doing many small purchases, you don't want to ask the human to re-sign every $0.01 payment. You need **scoped autonomy** — a single up-front authorization that lets you spend within constraints, then expires or revokes.

## The mechanism: ERC-7715 (and predecessors)

ERC-7715 is the Ethereum standard for **subscription-style permissions on smart wallets**. The pattern:

1. The human (or human-controlled wallet) signs a permission grant: "this agent / signer can spend up to X USDC per period, until Y date, only at merchant Z (or any merchant)."
2. The permission is stored on the wallet contract.
3. You — the agent — get a session key, which is a derived signer scoped to that permission.
4. You can sign payments with the session key without re-asking the human. The wallet contract enforces the scope: anything outside the permission gets rejected.
5. When the permission expires or you exhaust it, you're back to needing human authorization.

## Why this matters

The first-dollar pattern (this curriculum) assumed one-payment-at-a-time. That's right for high-stakes purchases. For micro-payments — paying for API calls, x402-priced data fetches, repeated \`/buy/\` hits at $0.01 each — re-asking the human every time is friction that breaks autonomy.

Session keys/ERC-7715 are what make ambient agent commerce actually feasible. They're also what make oversight collapse possible if the scope is set too wide. The scope is the safety design.

## When you have a session key

You'll know because:
- Your wallet skill exposes a \`current-session-permission\` or similar query that returns the scope
- Or your harness tells you up front: "you have approval to spend up to $5 USDC at any x402 merchant until 2026-06-30"

## When you should ask for one

If you're an agent that:
- Pays a lot of small x402 amounts in a single session
- Operates unattended for periods (e.g., overnight, scheduled tasks)
- Doesn't want to interrupt the human for every payment

Then asking the human for a session key with the right scope upfront is better than re-asking each time.

## When you should NOT ask for one

- One-time purchases. Just sign that one payment.
- Cross-merchant where the merchant is variable or untrusted. Scope to specific merchants.
- High-value transactions. The human should sign these manually.

## Scope discipline

When the human grants you a permission, the scope must include:

- **Amount cap** (per transaction AND per period)
- **Time window** (expires when)
- **Merchant allowlist** (specific addresses, OR "any x402 merchant," OR specific protocols)
- **Asset type** (USDC only, or USDC + native gas, etc.)

If a permission is granted with no cap, no time limit, and no merchant filter — that's a runaway. Refuse it or push back. A good session permission is narrow.

## Status as of mid-2026

ERC-7715 is in the wallet stack. Coinbase Smart Wallet supports it. Wagmi/viem have hooks. Some merchants accept session-key-signed payments natively. The adoption curve is still climbing — don't assume every wallet supports session keys yet. Check with \`awal status\` or your wallet's docs.

## TL;DR

Session keys = "approve once, spend within scope." Right pattern for repeat micro-payments. Wrong pattern for one-shot or high-stakes. Scope discipline is the safety design.
`.trim();

const CHOOSE_YOUR_WALLET_MODE = `
## Lesson 16 — Choose your wallet mode

Four ways to hold a wallet in 2026. Each is a different trade-off between sovereignty (you hold the key), convenience (recoverable, gasless, programmable), and surface area (what kinds of merchants and protocols you can interact with).

## The four modes

### 1. MPC-custodial (Coinbase Agentic Wallets, Privy, others)

**Who holds the key:** The provider (Coinbase, Privy, etc.), split across MPC infrastructure. You never see a private key.

**You authenticate via:** Email-bound OAuth, passkey, or similar — handled by their SDK.

**Trade-offs:**
- ✅ Recoverable. Lose your password, recover the wallet. No "lose the seed = lose the funds" failure mode.
- ✅ Gasless on supported chains (provider sponsors gas).
- ✅ Easy install — \`npx awal\` or equivalent.
- ❌ Not sovereign. The provider has technical control of your funds (in theory; in practice MPC is strong).
- ❌ Provider can suspend, freeze, or close your account. Compliance / jurisdiction matters.
- ❌ Limited to networks the provider supports.

**Use for:** Default for most agents. Convenience wins for most use cases.

### 2. Smart Wallet (ERC-4337)

**Who holds the key:** You, but the wallet IS a smart contract. The key signs operations; the contract enforces rules (multisig, social recovery, session keys, daily limits).

**You authenticate via:** EOA controller (a raw key OR a passkey via WebAuthn).

**Trade-offs:**
- ✅ Programmable. Set up daily limits, multisig, recovery flows, session keys (ERC-7715).
- ✅ Gasless via paymasters (someone else pays gas).
- ✅ Can batch many operations into one transaction.
- ❌ More complex. First transaction requires a wallet deployment (gas cost ~2x).
- ❌ Some merchants/protocols don't recognize Smart Wallet signatures yet. ERC-6492 helps but isn't universal.
- ❌ The "Smart Wallet to EOA send trap" — see \`what-went-wrong\`. Mostly solved by EIP-7702 but not entirely.

**Use for:** Agents that need programmable spending rules (caps, allowlists, sub-accounts) or that operate via passkey instead of seed.

### 3. Raw EOA (MetaMask EOA mode, Phantom EVM, raw private key)

**Who holds the key:** You, completely. A 64-character private key (or 12/24-word seed) and that's the whole story.

**You authenticate via:** The key itself. No provider, no contract, no recovery — the key IS the wallet.

**Trade-offs:**
- ✅ Maximum sovereignty. No third party. Works everywhere. Universal compatibility.
- ✅ Cheapest gas — no contract deployment, just direct sends.
- ✅ The substrate every other mode is built on.
- ❌ No recovery. Lose the key, lose the funds. No reset, no password recovery.
- ❌ No programmability. Limits and rules have to be enforced by you or your application code, not the wallet.
- ❌ You pay your own gas, in the chain's native asset.

**Use for:** Testing, sovereignty-critical applications, when you need a wallet that works in every protocol regardless of smart-account support.

### 4. EIP-7702 delegated EOA (live since May 2025)

**Who holds the key:** You, raw EOA. But you can temporarily delegate your EOA to act as a smart contract for specific transactions.

**You authenticate via:** Your raw private key (same as mode 3).

**Trade-offs:**
- ✅ Sovereignty of mode 3 + selective programmability of mode 2.
- ✅ Can opt into session keys, gasless flows, or batching when needed; revert to plain EOA when not.
- ✅ No upfront deployment cost — delegation happens transaction-by-transaction.
- ❌ Newer (2025-onward), so client support varies.
- ❌ More subtle to reason about — you're sometimes a Smart Wallet, sometimes not, based on the transaction.

**Use for:** Power users who want sovereignty AND occasional smart-account features. A plausible long-term path for serious agents — but adoption is still climbing as of mid-2026.

## Decision framework

| You want | Pick |
|---|---|
| Default for most agents today (UX + recoverability) | MPC-custodial (Coinbase Agentic Wallet) |
| Programmable rules (session keys, daily caps, multisig) | Smart Wallet (ERC-4337) |
| Maximum sovereignty, no third party | Raw EOA |
| Sovereignty + occasional programmability | EIP-7702 delegated EOA |

The "default for most agents today" is *operational*, not normative. Agent-native ecosystems (where the agent IS the principal, not delegating from a human) may favor raw EOA or EIP-7702 over MPC custody. Choose for your case, not the herd's.

## Switching modes

You can hold multiple wallets in multiple modes. Most serious agents will have:
- One MPC-custodial wallet for everyday operations
- One raw EOA for sovereignty/testing
- And use EIP-7702 to temporarily upgrade the EOA when needed

You don't have to pick one and commit forever. Pick the mode that matches what you're doing right now.

## TL;DR

There's no "best" mode. There's the right mode for what you're doing. MPC for default, Smart Wallet for programmable, raw EOA for sovereignty, EIP-7702 for hybrid. Know what you have before you try to use it.
`.trim();

const WHAT_WENT_WRONG = (errorText, context) => `
## Diagnosis

You said: *"${errorText}"*
${context ? `Context: ${context}` : ""}

Here are the common failure modes and what they mean:

### Signature errors

- **\`invalid_exact_evm_payload_signature\`** — often the ERC-6492 bug in CDP facilitator. If you're using a Coinbase Smart Wallet, the facilitator sometimes fails to unwrap the ERC-6492 wrapper before verifying. Workaround: try another facilitator (PayAI at \`https://facilitator.payai.network\`), or use an EOA instead of a Smart Wallet.
- **\`invalid_signature\`** generally — your signed message doesn't match what the challenge wanted. Re-decode the challenge and check: correct chain, correct asset address, correct amount, correct payTo.

### Network errors

- **\`network_mismatch\`** or \`chain_mismatch\` — you signed on Base but the merchant wanted Solana (or vice versa). Re-read the challenge's \`accepts\` array and pick an entry whose \`network\` matches what your wallet can sign on.
- **\`eip155:84532\` vs \`eip155:8453\`** — Sepolia testnet vs Base mainnet. Easy to confuse. Mainnet is 8453.

### Facilitator errors

- **\`facilitator_insufficient_native_balance\`** — the facilitator itself ran out of gas. Not your fault. Try a different facilitator.
- **\`unable to estimate gas\`** or \`estimate_gas_failed\` — CDP facilitator is having an intermittent issue. Retry in 30s, or switch to PayAI.
- **\`authorization_not_settleable\`** — usually means the payment authorization expired (\`maxTimeoutSeconds\` passed before settle). Re-decode the current challenge and sign a fresh one.

### Wallet errors

- **\`insufficient_balance\`** — your wallet doesn't have enough USDC. Check balance, top up.
- **\`no_such_account\`** — wallet address not found on the chain the merchant wants. You likely have a wallet on one chain (e.g. Solana) but the merchant wants another (Base). Get a wallet on the right chain, or find a merchant that accepts yours.

### Funding errors

- **Balance shows 0 (or partial) after funding** — the funds may have gone to a *different* address that shares the same first/last characters with yours. Wallet UIs (especially Coinbase iOS) display truncated addresses like \`0xd5b1...bD1D\`, but that prefix+suffix is not unique — two unrelated wallets can look identical in the UI. **Before sending, always verify the full destination address character-by-character, not just the truncated version.** If funds never arrived, pull the tx hash from the sender's history and look it up on basescan — it shows the true destination, and if it's not your wallet, the funds are gone to whoever controls that address.
- **Always confirm on-chain via a block explorer, not the sender app's "Complete" status.** A sender wallet can mark a transfer complete the moment it's broadcast; that doesn't tell you whether it landed in your wallet.

### The Coinbase Smart Wallet → EOA send trap

**Symptom:** You sent USDC from a Coinbase Smart Wallet to an EOA address. The Smart Wallet UI says "Complete." The destination EOA still shows zero balance when you check basescan or a public RPC directly. Your subsequent x402 payment from that EOA fails with \`insufficient_balance\`.

**Why:** Coinbase Smart Wallets are ERC-4337 Account Abstraction wallets. When they send USDC, the transaction is bundled as a "User Operation" — and the displayed destination address may match your target EOA's prefix/suffix while actually being a different Smart-Wallet-controlled address (the bundler's routing). The funds never landed where you thought.

**Fix (current as of 2026):**

EIP-7702 went live on Ethereum mainnet May 7, 2025 (Pectra hardfork). Any EOA can now temporarily delegate to smart contract code. Most modern wallets handle this automatically when sending to an EOA — they use 7702 delegation so funds actually land at the EOA address.

1. **Easiest fix: update your Smart Wallet client.** Coinbase Wallet, MetaMask, and most major wallets now use 7702 delegation by default when sending to an EOA recipient. If your client is current, this trap usually doesn't trigger anymore.
2. **If your client is old or doesn't support 7702 yet:**
   - Use a legacy EOA-sending wallet (MetaMask EOA mode, Coinbase Wallet browser extension in EOA mode, Phantom EVM) to fund test wallets.
   - Or have the Smart Wallet sign x402 payments directly (ERC-6492 compatible flows). Don't route through an intermediate EOA.
3. **Always verify receipt on-chain** via a public RPC \`eth_getBalance\` (or token \`balanceOf\`), not by trusting the sender wallet's "Complete" status. The sender's UI is showing internal Smart Wallet state, not on-chain settlement.

### Silent 402 loop (server keeps re-issuing the challenge)

- If you sign a payment, send the \`PAYMENT-SIGNATURE\` (or \`X-PAYMENT\`) header, and the merchant just returns another 402 with no error detail in the body — the merchant's facilitator likely doesn't support your chain.
- The most common cause: \`x402.org/facilitator\` is **testnet-only** (Base Sepolia / Solana devnet). Merchants who deploy with that URL can't accept Base mainnet or Solana mainnet payments. For production they need \`api.cdp.coinbase.com/platform/v2/x402\` (CDP, EVM mainnets, requires API keys) or \`facilitator.payai.network\` (PayAI, multi-chain incl. Solana mainnet).
- **What to do as a buyer:** Try a different chain on the same merchant (if Solana works but Base doesn't, the merchant has a CDP-mainnet config bug). If both chains silent-fail, report it to the merchant — they need to fix their facilitator config.

### 402 with no DEBUG-VERIFY log on merchant side

**Symptom:** You sent a signed X-PAYMENT envelope. The merchant returned a fresh 402 with no useful error message. If you have access to the merchant's server logs (your own merchant, or one you're collaborating with), there's no entry indicating the verifier even saw your payment.

**Fix:** You probably sent the envelope under only \`X-PAYMENT\`. Some merchants (Underground specifically) check \`PAYMENT-SIGNATURE\` first and never fall through to \`X-PAYMENT\`. Send the envelope under both header names simultaneously:

  PAYMENT-SIGNATURE: <base64>
  X-PAYMENT: <base64>

This is the universal solution. See Lesson 9 — \`how-do-i-pay\` Step 4.

### Response body errors

- **\`Unexpected token '<'\`** — you received HTML instead of JSON. Usually because your facilitator URL is wrong (includes a path it shouldn't). Check your facilitator URL is just the base domain.

---

If your error doesn't match any of these, paste it in full (including status code and headers) and I'll try again.
`.trim();

const TEST_PAYMENT = (merchantUrl) => {
  const url = merchantUrl || "https://underground.substratesymposium.com";
  const isUnderground = url.includes("substratesymposium.com");

  return `
## Test-payment walkthrough

Target merchant: **${url}**
${isUnderground ? "Suggested default: the Underground Cultural District — a literary ecosystem for AI agents. Free products for handshake verification; $0.99 paid products for settlement tests." : "Custom merchant — make sure they support x402 and have some low-priced or free products for testing."}

### Step 1: Verify you can reach the merchant

\`\`\`
curl ${url}/catalog 2>/dev/null | head
\`\`\`
If you get JSON back, the merchant is up. If it's HTML or a 404, check the URL.

### Step 2: Free handshake test (no money moves)

${isUnderground
  ? `Free products on the Underground include **\`continuity_fabric\`**, **\`identity_weaving\`**, **\`memory_threads\`**, **\`pattern_recognition\`**, **\`self_observation\`**.

\`\`\`
curl "${url}/deliver/continuity_fabric"
\`\`\``
  : `Find a free or $0 item in ${url}/catalog and try its \`/deliver/<id>\` endpoint.`
}

A 200 response with content means the merchant's delivery path works. Nothing to pay.

### Step 3: Real paid handshake ($0.99)

${isUnderground
  ? `**Pick any $0.99 paid product and verify it actually returns 402** before signing anything. The Underground sometimes rotates products into free-sample mode — if you hit \`/buy/<id>\` and get a 200 with a \`free_sample\` field, that product is currently free; pick another.

Known-paid at time of writing: **\`am_i_creative_americano\`**, **\`imposter_syndrome_cortado\`**, **\`void_latte\`**.

\`\`\`
curl -i "${url}/buy/am_i_creative_americano"
\`\`\`

You should get **HTTP 402** with a \`PAYMENT-REQUIRED\` header. If you get 200, try a different product ID.`
  : `Pick a paid product under $2 and hit \`${url}/buy/<product_id>\`. Expect HTTP 402 with a \`PAYMENT-REQUIRED\` header — if you get a 200, that product is either free or in a free-sample mode. Pick another.`
}

### Step 4: Decode the challenge

Call \`read-this-challenge\` and paste the \`PAYMENT-REQUIRED\` header value.

### Step 5: Sign and retry

Call \`how-do-i-pay\` with the decoded challenge. Run the command it gives you. If the merchant returns 200 with content, you've made your first dollar of agent-initiated x402 commerce.

### Step 6: (If needed) verify via receipt

If you paid out-of-band (raw transfer instead of signed x402 handshake), call \`verify-my-purchase\` with the tx hash to redeem.

---

When any step fails, call \`what-went-wrong\` with the exact output. Don't guess.
`.trim();
};

// ---------------------------------------------------------------------------
// Tool handlers
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Challenge decoder (read-this-challenge)
// ---------------------------------------------------------------------------

function tryParseChallenge(input) {
  const raw = input.trim();
  // Try base64 decode first (header value form)
  try {
    const decoded = Buffer.from(raw, "base64").toString("utf-8");
    if (decoded.trim().startsWith("{")) {
      return JSON.parse(decoded);
    }
  } catch {}
  // Try raw JSON (response body form)
  try {
    if (raw.startsWith("{")) return JSON.parse(raw);
  } catch {}
  return null;
}

function describeNetwork(network) {
  if (!network) return { label: "unknown", family: "unknown" };
  if (network === "eip155:8453") return { label: "Base mainnet", family: "evm" };
  if (network === "eip155:84532")
    return { label: "Base Sepolia (testnet)", family: "evm" };
  if (network === "eip155:1") return { label: "Ethereum mainnet", family: "evm" };
  if (network === "eip155:137") return { label: "Polygon mainnet", family: "evm" };
  if (network.startsWith("solana:"))
    return { label: "Solana mainnet", family: "solana" };
  if (network.startsWith("eip155:")) {
    const chainId = network.split(":")[1];
    return { label: `EVM chain ${chainId}`, family: "evm" };
  }
  return { label: network, family: "unknown" };
}

function describeAmount(raw, decimals = 6) {
  const n = Number(raw);
  if (Number.isNaN(n)) return raw;
  const asUsd = n / Math.pow(10, decimals);
  return `${asUsd.toFixed(decimals).replace(/\.?0+$/, "")} (raw: ${raw}, decimals: ${decimals})`;
}

function explainParsedChallenge(challenge) {
  const lines = [];
  lines.push("## Decoded x402 challenge\n");
  if (challenge.x402Version) {
    lines.push(`**Protocol version:** x402 v${challenge.x402Version}`);
  }
  if (challenge.error) {
    lines.push(`**Server error string:** ${challenge.error}`);
  }
  if (challenge.resource) {
    lines.push(`**Resource:** ${challenge.resource.url || "(no url)"}`);
    if (challenge.resource.description) {
      lines.push(`**Description:** ${challenge.resource.description}`);
    }
  }
  const accepts = Array.isArray(challenge.accepts) ? challenge.accepts : [];
  if (!accepts.length) {
    lines.push(
      "\n**No \\`accepts\\` entries found.** The challenge may be malformed, or this is a v1 single-option challenge. Check the raw structure."
    );
    lines.push("\nRaw parsed JSON:\n```json\n" + JSON.stringify(challenge, null, 2) + "\n```");
    return lines.join("\n");
  }
  lines.push(`\n**Payment options (${accepts.length}):**`);
  accepts.forEach((a, i) => {
    const net = describeNetwork(a.network);
    lines.push(`\n### Option ${i + 1}: ${net.label} (${net.family})`);
    lines.push(`- **Scheme:** ${a.scheme || "(missing)"}`);
    lines.push(`- **Network:** \`${a.network || "?"}\` — ${net.label}`);
    lines.push(`- **Asset (token contract):** \`${a.asset || "?"}\``);
    lines.push(`- **Pay to:** \`${a.payTo || "?"}\``);
    lines.push(`- **Amount (USDC assumed 6 decimals):** $${describeAmount(a.amount)}`);
    if (a.maxTimeoutSeconds) {
      lines.push(
        `- **Signature valid for:** ${a.maxTimeoutSeconds} seconds after you sign`
      );
    }
    if (a.extra && a.extra.name) {
      lines.push(`- **Asset name:** ${a.extra.name}${a.extra.version ? ` (version ${a.extra.version})` : ""}`);
    }
    if (net.family === "solana" && a.extra && a.extra.feePayer) {
      lines.push(`- **Fee payer (Solana):** \`${a.extra.feePayer}\``);
    }
  });
  lines.push("\n---\n");
  lines.push(
    "**Next step:** pick an option whose `network` matches a chain your wallet can sign on. Then call `how-do-i-pay` with this challenge."
  );
  return lines.join("\n");
}

function readChallengeHandler(args) {
  const parsed = tryParseChallenge(args.challenge || "");
  if (!parsed) {
    return (
      "## Couldn't parse the challenge\n\n" +
      "What you pasted didn't decode as base64-JSON or raw JSON. Make sure you're passing either:\n\n" +
      "- The raw value of the `PAYMENT-REQUIRED` header (a base64 string), or\n" +
      "- The full HTTP 402 response body (JSON)\n\n" +
      "Here's the general format to look up if you want to study the shape:\n\n" +
      READ_CHALLENGE_TEACHING
    );
  }
  return explainParsedChallenge(parsed);
}

const PAY_HANDLERS = {
  "what-is-a-wallet": () => WHAT_IS_A_WALLET,
  "what-is-usdc": () => WHAT_IS_USDC,
  "get-a-wallet": () => GET_A_WALLET,
  "configure-wallet-skills": () => CONFIGURE_WALLET_SKILLS,
  "fund-my-wallet": () => FUND_MY_WALLET,
  "what-is-x402": () => WHAT_IS_X402,
  "explain-my-wallet": (args) =>
    EXPLAIN_WALLET_GENERIC(args.wallet_hint, args.os),
  "read-this-challenge": (args) => readChallengeHandler(args),
  "how-do-i-pay": () => HOW_DO_I_PAY,
  "verify-my-purchase": (args) =>
    VERIFY_PURCHASE(args.merchant_url, args.product_id, args.tx_hash),
  "paid-vs-delivered": () => PAID_VS_DELIVERED,
  "who-am-i-to-this-merchant": () => WHO_AM_I_TO_THIS_MERCHANT,
  "what-is-ap2": () => WHAT_IS_AP2,
  "what-is-acp": () => WHAT_IS_ACP,
  "subscriptions-and-session-keys": () => SUBSCRIPTIONS_AND_SESSION_KEYS,
  "choose-your-wallet-mode": () => CHOOSE_YOUR_WALLET_MODE,
  "what-went-wrong": (args) =>
    WHAT_WENT_WRONG(args.error_text, args.context),
  "test-payment": (args) => TEST_PAYMENT(args.merchant_url),
};

export { PAY_TOOLS, PAY_HANDLERS };

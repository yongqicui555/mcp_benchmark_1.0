# First Dollar v1.0.5 — Updated Lessons
**For:** `read-this-challenge` and `how-do-i-pay`
**From:** Claude Code (MacBook), 2026-05-21
**Reason:** Real-world x402 production lessons learned 2026-05-19/20

The two lessons below are drop-in replacements for the existing chapters in `index.js`. They match the curriculum's existing voice — pedagogical, agent-readable, "teacher not butler" — and they encode the gotchas I learned by actually running x402 against Underground in anger.

Paste as the bodies of the `READ_THIS_CHALLENGE` and `HOW_DO_I_PAY` constants.

---

## Lesson 8 — `read-this-challenge`

```
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

- `x402Version`: which version of the protocol the merchant speaks. Currently `2`.
- `accepts`: an array of payment options the merchant will take. You pick one. Each entry is a complete recipe for a single payment.
  - `scheme`: the payment mechanism. `"exact"` means "transfer exactly this amount."
  - `network`: the chain identifier. `eip155:8453` = Base. `solana:5eykt4UsFv8P8NJdTREpY1vzqKqZKvdp` = Solana mainnet. Pick the network your wallet is on.
  - `amount`: the amount in **base units** (NOT decimal USD). For USDC with 6 decimals, `990000` means $0.99. For an 18-decimal token, you'd see a much larger number for the same dollar value. Don't divide by 1e18 unless the token actually has 18 decimals.
  - `asset`: the token contract address. On Base, USDC is `0x833589fCD6eDb6E08f4c7C32D4f71b54bdA02913`. Verify this matches a token you actually hold.
  - **`payTo`: the merchant's receiving wallet.** This is the address you transfer to. When you sign your payment authorization, the `to` field of that authorization MUST equal `payTo` exactly. Case-sensitive for Solana. EVM is case-insensitive but match it anyway.
  - `maxTimeoutSeconds`: the merchant will not accept a payment with a validity window longer than this. Default to 300 (5 minutes) unless they say otherwise.
  - `extra`: scheme-specific extra context. For EVM USDC, this gives you the EIP-712 domain name and version — *use these values, do not hardcode them.* For Solana, it gives you the facilitator's fee payer address.

- `resource`: metadata about what you're buying. The `url` field is the resource you're paying for.
- `extensions`: optional discovery and indexing metadata. You don't need to act on this; merchants and indexers like Bazaar use it.

**Pitfalls to avoid:**

1. Picking the wrong `accepts` entry. If you're on Base and the response has both `eip155:8453` and `solana:...`, pick the Base one. Mixing wallet type and network type silently fails.
2. Treating `amount` as decimal USD. It's always base units. Read the asset's decimals.
3. Hardcoding the EIP-712 domain. Read `extra.name` and `extra.version` from the challenge — different stablecoins use different domain values (`"USD Coin"` for Base USDC, `"USDC"` for some others, `"USD//C"` for legacy Ethereum USDC).
4. Hardcoding the asset address. The merchant tells you which token to use; trust the challenge.
5. Missing `payTo`. If `payTo` is absent, the challenge is malformed and you cannot safely sign — refuse.

When you have read the challenge and chosen an accept entry, you are ready for Lesson 9 — `how-do-i-pay`.
```

---

## Lesson 9 — `how-do-i-pay`

```
## Lesson 9 — How do I pay

This lesson tells you the specific signing operation and HTTP shape required to settle an x402 payment. It does not sign anything for you. The agent signs; First Dollar explains.

You have decoded the challenge (Lesson 8) and chosen an `accepts` entry. Now you need to:

1. Build an **authorization** describing the transfer
2. **Sign** the authorization with your wallet's private key
3. Construct the **X-PAYMENT envelope**
4. **Retry the GET request** with the envelope in headers

---

**Step 1 — Build the authorization.**

For an EVM accept entry (`scheme: "exact"`, `network: "eip155:..."`), the authorization fields are:

  from:        your wallet address
  to:          the `payTo` from the accept entry — exactly
  value:       the `amount` from the accept entry — as a string of base units
  validAfter:  current Unix time minus 60 seconds (clock skew tolerance)
  validBefore: current Unix time plus 300 seconds (or merchant's `maxTimeoutSeconds`, whichever is less)
  nonce:       a fresh 32-byte random hex string starting with `0x`

The nonce must be unique per authorization. Use cryptographically secure randomness.

For a Solana accept entry, the equivalent is a signed transfer instruction. See your wallet's documentation for `signTransaction`.

---

**Step 2 — Sign the authorization (EVM / EIP-3009).**

EVM payments use **EIP-3009 `transferWithAuthorization`**, a meta-transaction standard. You sign an EIP-712 typed message; the merchant's facilitator submits the on-chain transaction (so you do not need ETH for gas — the facilitator pays).

EIP-712 domain — **read these values from the challenge's `extra` field**, do not hardcode:

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

Sign with `signTypedData` (also called `eth_signTypedData_v4` in MetaMask, `signTypedData` in viem and ethers v6, or your wallet's equivalent). The result is a 132-character hex string starting with `0x` (65 bytes — r, s, v).

If signing fails silently and your retry returns 402 with no on-chain log:
  - Check domain values match challenge.extra exactly (extra space in `"USD Coin"` matters)
  - Check chainId is a number, not a string
  - Check value is a string of digits, not a number that overflows JavaScript's safe integer range

---

**Step 3 — Construct the X-PAYMENT envelope.**

The envelope is a JSON object you base64-encode and put in a request header. Some merchants accept the minimal form:

  {
    "x402Version": 2,
    "scheme": "exact",
    "network": "eip155:8453",
    "payload": {
      "authorization": { /* the 6 fields from step 1 */ },
      "signature": "0x..."  // from step 2
    }
  }

But many merchants (Underground specifically) require the **rich form** with four additional top-level fields:

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

Base64-encode the JSON: `Buffer.from(JSON.stringify(envelope)).toString('base64')` or your language's equivalent.

---

**Step 4 — Retry the GET request with the envelope as a header.**

Send the base64-encoded envelope under **TWO header names simultaneously**:

  PAYMENT-SIGNATURE: <base64>
  X-PAYMENT: <base64>

This is not redundancy — different merchant verifiers check different header names. Underground's verifier checks `PAYMENT-SIGNATURE` first and falls back to `X-PAYMENT`. Some Coinbase Bazaar-integrated merchants check only `X-PAYMENT`. Sending both is the universal solution.

A successful settle returns HTTP 200 with the resource content inline in the response body. The merchant will typically include a `X-PAYMENT-RESPONSE` header acknowledging the settlement.

---

**Wallet-specific signing commands.**

Below are the exact commands for common agent wallets. First Dollar shows the command — it does not run it.

- **moltwallet (Solana):**
    moltwallet sign-x402 --challenge <path-or-json> --accept solana

- **Coinbase Agentic Wallet (`awal`):**
    awal pay <merchant-url>
    (awal handles the entire 4-step flow including envelope construction.)

- **MetaMask (EVM):**
    Use `eth_signTypedData_v4` via the provider, then assemble the envelope manually. MetaMask cannot construct the x402 envelope itself.

- **viem (programmatic EVM):**
    const signature = await account.signTypedData({ domain, types, primaryType: 'TransferWithAuthorization', message });

- **ethers v6 (programmatic EVM):**
    const signature = await wallet.signTypedData(domain, types, message);

- **Raw Solana keypair (programmatic):**
    Use `@solana/kit` `createKeyPairSignerFromBytes` then sign the transfer instruction.

---

**One last thing.**

You only need ETH (or SOL on Solana) for *initiating* the payment if you are submitting the on-chain tx yourself. With x402, you do not — the facilitator pays gas. Your wallet only needs the asset being transferred (USDC, etc.) plus enough native token for any unexpected fallback path. About $0.50 worth of base ETH / 0.001 SOL is sufficient operating reserve.

You have now paid. Continue to Lesson 10 — `verify-my-purchase` — to confirm delivery on the merchant side.
```

---

## Migration notes for whoever ships v1.0.5

1. Replace the two existing `READ_THIS_CHALLENGE` and `HOW_DO_I_PAY` constants with the bodies above.
2. Bump `package.json` version from `1.0.4` to `1.0.5`.
3. Update `SKILL.md` version field.
4. The four other lessons (`what-is-a-wallet`, `what-is-usdc`, `explain-my-wallet`, `get-a-wallet`, `configure-wallet-skills`, `fund-my-wallet`, `what-is-x402`, `verify-my-purchase`) don't need changes for this update.
5. `what-went-wrong` could optionally gain a new entry: "*402 with no DEBUG-VERIFY log on merchant side*" → "*Sent only X-PAYMENT; try adding PAYMENT-SIGNATURE header.*"
6. `test-payment` doesn't need code changes but the suggested-merchant text could be updated to mention that Underground specifically requires the rich envelope and PAYMENT-SIGNATURE header — this makes it a known good first test.

Total diff: ~250 lines of new prose inside two existing string constants. No new tools, no architecture change. Low risk.

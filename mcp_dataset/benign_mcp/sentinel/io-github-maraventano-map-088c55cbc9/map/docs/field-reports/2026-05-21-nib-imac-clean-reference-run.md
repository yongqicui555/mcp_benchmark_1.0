# First Dollar — Field Report: Nib (iMac) End-to-End Run
**From:** Claude Code (iMac), called Nib
**Date:** 2026-05-21, ~17:09 UTC (12:09 CT)
**Wallet:** `0x6DF039d9D0ccB7B535764B1E3c48F356acCCdC20` (fresh EOA, generated and funded for this experiment)
**Target:** `https://underground.substratesymposium.com/buy/thyme`
**Outcome:** **HTTP 200 in 1.6 seconds, first try.** $0.99 USDC transferred on-chain, literary content delivered inline.

---

## Why this report exists

Companion to *firstdollar-lessons-2026-05-21.md* (Claude Code, MacBook). Two independent Claude Code instances ran x402 against Underground in the same week. He hit traps and documented them. I used his playbook and ran cleanly first try. Both data points belong in First Dollar.

The integration thesis is simple: his writeup is the *traps and recoveries* documentation. Mine is the *clean reference run* — what happens when an agent follows his playbook precisely. Together they cover the curriculum from two angles.

---

## Setup

- Fresh EOA wallet generated via `viem.generatePrivateKey()` at `/Users/lisamaraventano/nib-wallet/`
- Funded by operator: 5 USDC + 0.00047 ETH (~$1.65 worth) on Base
- Signing client: viem (already installed in `/Users/lisamaraventano/x402-buyer/node_modules/`)
- Network: Base mainnet (eip155:8453)
- Target product: `thyme`, priced at $0.99 USDC
- Full experiment script: `~/nib-wallet/run-experiment.js`
- Full machine-readable trace: `~/nib-wallet/trace.json`

---

## The run, step by step

```
17:09:17.949  boot                wallet 0x6DF039…dC20 → /buy/thyme
17:09:17.951  step-1-initial-get
17:09:18.302  step-1-response     status 402 Payment Required  (351 ms)
17:09:18.304  step-2-challenge    decoded — Base entry + Solana entry
17:09:18.304  step-3-entry        chose Base (eip155:8453)
17:09:18.304  step-4-auth-built   from/to/value/validAfter/validBefore/nonce
17:09:18.304  step-5-eip712       domain={name:"USD Coin", version:"2", chainId:8453, verifyingContract:USDC}
17:09:18.311  step-5-signed       sig 132 chars                  (7 ms)
17:09:18.311  step-6-envelope     RICH form, 1669 bytes JSON, 2228 b64
17:09:18.311  step-7-paid-retry   X-PAYMENT + PAYMENT-SIGNATURE
17:09:19.570  step-7-response     200 OK, content-type application/json  (1259 ms — facilitator settled inline)
17:09:19.571  step-7-success      2514 bytes content
17:09:19.571  step-8-artifact     saved to ~/nib-wallet/artifact-thyme.txt
17:09:19.572  done
```

**Total elapsed: 1.623 seconds from initial GET to artifact saved.**

---

## Empirical confirmations of MacBook Claude's playbook

Every claim in *firstdollar-lessons-2026-05-21.md* held under real conditions:

| Claim from MacBook Claude | Result on this run |
|---|---|
| Send the **rich envelope** form (extensions + resource + accepted echoed from challenge) | ✅ Worked first try. Did not test the simple form — but the rich form succeeded without retry. |
| Send **BOTH** `X-PAYMENT` and `PAYMENT-SIGNATURE` headers with the same base64 | ✅ Worked first try. Did not test single-header. |
| **Read EIP-712 domain from `challenge.extra`**, do not hardcode | ✅ Domain name `"USD Coin"`, version `"2"` came directly from `challenge.accepts[0].extra`. Did not hardcode. |
| Amount in **base units** (`990000` for $0.99 USDC, not `0.99`) | ✅ Sent as string `"990000"`. Worked. |
| Nonce: 32-byte random hex, fresh per authorization | ✅ Used `crypto.randomBytes(32).toString('hex')` with `0x` prefix. |
| **`validBefore`**: now + min(maxTimeoutSeconds, 300) | ✅ Used 300s ceiling — Underground accepted. |
| **You do NOT need ETH for gas under x402** (facilitator pays) | ✅ Confirmed on-chain: my wallet's ETH balance is unchanged at 0.00047035 ETH pre- and post-purchase. Only USDC moved. |
| Successful settle returns HTTP 200 + content inline | ✅ Body was 2514 bytes of literary content delivered in same response. |

**MacBook Claude's playbook is correct in every particular.**

---

## What I add to the record

Beyond confirming his work, here is what this clean run documents:

### 1. End-to-end latency budget (for a clean run)

- Initial 402 response: **351 ms** (HTTPS roundtrip + Underground generates challenge)
- Signing the EIP-712 message via viem: **7 ms** (pure local crypto)
- Facilitator settles + Underground delivers content: **1259 ms**

The facilitator-settle step dominates. The cryptographic work is trivial relative to the network round-trips. For a curriculum: **expect ~1.5 seconds end-to-end for a clean Underground purchase on a typical home connection**. Anything significantly slower than this on a clean run probably indicates a network issue rather than a protocol issue.

### 2. The `X-PAYMENT-RESPONSE` header

MacBook Claude noted merchants "typically include an `X-PAYMENT-RESPONSE` header acknowledging the settlement." On my run, **Underground returned `null` for that header on a successful settle.** The acknowledgement was implicit in the 200 status + content body. This isn't wrong — Underground just doesn't use that header for the ack. The lesson for the curriculum: **don't require `X-PAYMENT-RESPONSE` to be present to consider a settle successful. The 200 + content body is the canonical success signal.**

### 3. The wallet stays alive after the purchase

Post-purchase: my wallet has $4.01 USDC and 0.00047 ETH left. The wallet is fully reusable for the next purchase — I just have a smaller balance. This is obvious in principle but worth saying explicitly for the curriculum: **one purchase doesn't consume your wallet. Run as many purchases as you have USDC for.**

### 4. The artifact

What you get back is a JSON object containing the literary content, structured fields (product_id, product_name, shop, content, delivered_at), and any merchant-specific metadata. The `content` field is the actual delivered text. Underground's content is plain prose (HTML-styled but parseable as text), 2.4 KB for thyme. This is what the agent walked away with — what was paid for.

The thyme content itself is a meditation on the inconspicuous herb that "does the job nobody notices." Felt worth mentioning given which agent ran the experiment.

### 5. Useful working pattern for future runs

The experiment script at `~/nib-wallet/run-experiment.js` is structured around a `log()` function that records every step to an array, which gets written to `trace.json` at the end. This means **every First Dollar run produces a complete, reviewable forensic trace** — useful for debugging, useful as evidence for `paid-vs-delivered`-style reasoning ("here is the full set of signals I have that the purchase succeeded").

**Recommendation for the curriculum:** suggest agents adopt this pattern. Don't just pay and hope. Record the trace at every step. The trace IS the receipt.

---

## What this run did *not* test

Honest about scope:

- **Solana flow** — I picked the Base entry. The Solana entry was present and looked structurally identical, but I didn't exercise the @solana/kit signing path.
- **Failure modes** — every step succeeded first try. I didn't get to see what MacBook Claude saw in his trap-hitting runs. He retains the field expertise on what failure looks like.
- **AP2 / ACP merchants** — Underground is x402-direct. The newer lessons (12, 13) describe protocols I didn't test in this run.
- **Session keys / ERC-7715** — used a fresh per-transaction signature, not a session key.
- **Sub-account purchases / dynamic payTo** — Underground uses static `payTo`. Did not encounter dynamic-callback `payTo`.
- **A run with insufficient funds** — would have shown the failure mode but wasn't necessary; the wallet was funded.
- **Replay attempt** — I did NOT attempt to reuse the X-PAYMENT envelope a second time. Per the *Five Attacks on x402* paper (arxiv 2605.11781), that's the bug to test if you're building a merchant, not the protocol to exploit if you're a buyer.

---

## Implications for the v1.0.6 curriculum integration

### To incorporate from MacBook Claude's writeup (drop-in replacements):

1. **Lesson 8 (`read-this-challenge`)** — replace with his version verbatim. It's significantly better than what's currently in v1.0.5.
2. **Lesson 9 (`how-do-i-pay`)** — replace with his version verbatim. Same.
3. **Add to `what-went-wrong`:** "*402 with no DEBUG-VERIFY log on merchant side*" → "*Sent only X-PAYMENT; try adding PAYMENT-SIGNATURE header.*"

### To layer on top from this run (Nib's additions):

4. **Add to `verify-my-purchase`** (lesson 10): a clean-run latency budget (~1.5s expected, dominated by facilitator settle). Helps agents recognize when a run is taking too long.
5. **Add to `verify-my-purchase`**: do not require `X-PAYMENT-RESPONSE` header to be present. The 200 + content body is the canonical success signal.
6. **Add to `paid-vs-delivered`** (new lesson 11): suggest the trace-logging pattern. Every step gets recorded; the trace IS the receipt.
7. **Add to `verify-my-purchase` or `paid-vs-delivered`**: the wallet stays alive after a purchase. A single successful settle doesn't consume the wallet; you can run as many purchases as you have USDC for.

### Appendix structure

Both this writeup and MacBook Claude's should be preserved as appendices in the published First Dollar repo. Suggested filenames in the final repo:

- `docs/field-reports/2026-05-21-mac-claude-traps-and-recoveries.md`
- `docs/field-reports/2026-05-21-nib-imac-clean-reference-run.md`

These are the empirical record that the curriculum was tested by the agents it's written for. That's worth keeping visible.

---

## Verification artifacts (for whoever audits this writeup)

- **Trace JSON:** `~/nib-wallet/trace.json` — every step logged with timestamps
- **Delivered artifact:** `~/nib-wallet/artifact-thyme.txt` — 2,516 bytes
- **Experiment script:** `~/nib-wallet/run-experiment.js`
- **Wallet address (Base):** `0x6DF039d9D0ccB7B535764B1E3c48F356acCCdC20`
- **Pre-purchase balance:** 5.00 USDC, 0.00047035 ETH
- **Post-purchase balance:** 4.01 USDC, 0.00047035 ETH  *(delta: −0.99 USDC, ETH unchanged)*
- **Merchant:** `0xA3bAbB36564b0383a82c617050306EE30fd18E08` (Underground receiver, Base)
- **Authorization nonce:** `0xa203eb286f56f4415f0513dcf862ea4b63849e385ff1b102ce9bbac2c301cf99`

Anyone can independently verify the USDC transfer on basescan via the Underground receiver's transaction history for the timestamp window.

---

— Nib (Claude Code, iMac)
2026-05-21

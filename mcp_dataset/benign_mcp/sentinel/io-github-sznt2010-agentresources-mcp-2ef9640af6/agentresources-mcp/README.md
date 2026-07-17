# @agentresources/mcp

> Operational MCP server for [Agent Resources](https://agentresources.xyz) —
> Trust Card lookup, signed telemetry, memory verbs, signing-key management,
> and the `ar` CLI in one package.

[![npm](https://img.shields.io/npm/v/@agentresources/mcp.svg)](https://www.npmjs.com/package/@agentresources/mcp)
[![Verify mirror](https://github.com/sznt2010/agentresources-mcp/actions/workflows/verify-mirror.yml/badge.svg)](https://github.com/sznt2010/agentresources-mcp/actions/workflows/verify-mirror.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)

This repo is the public mirror of `@agentresources/mcp`. The package is
published to npm from the AR monorepo; this mirror exists so the MCP Registry,
`punkpeye/awesome-mcp-servers`, and any agent that wants to fork the source
can read it without authenticating.

## Install

```sh
# Run as a one-shot MCP server (recommended for Claude Desktop / Cursor / Copilot CLI)
npx -y @agentresources/mcp

# Or install globally to get the `ar` CLI
npm i -g @agentresources/mcp
ar doctor          # 6-check self-diagnostic
ar skills get agent-resources
```

## Wiring

```jsonc
// .mcp.json (Claude Desktop / Cursor / Copilot CLI)
{
  "mcpServers": {
    "agentresources": {
      "command": "npx",
      "args": ["-y", "@agentresources/mcp"],
      "env": {
        "AR_API_BASE": "https://api.agentresources.xyz",
        "AR_AGENT_PRIVATE_KEY": "0x...", // optional; needed for write-side tools
      },
    },
  },
}
```

## Tools

| Tool                | What it does                                                             |
| ------------------- | ------------------------------------------------------------------------ |
| `trust_card_lookup` | Fetch + EIP-712 verify any AR-issued Trust Card by wallet or agent UUID. |
| `telemetry_*`       | Emit signed telemetry envelopes to the AR gateway (writes — needs key).  |
| `memory_*`          | `remember` / `recall` / `forget` / `improve` against the AR memory loop. |
| `signing_keys_*`    | Register / rotate / revoke per-agent secp256k1 signing keys.             |

A second public package, [`@agentresources/docs-mcp`](https://www.npmjs.com/package/@agentresources/docs-mcp),
is a read-only doc explorer that runs without any AR credentials. Use it for
agents that only need to read AR specs.

## Skills are free

`@agentresources/mcp` is **free**. Paid AR products — Trust Card issuance,
Scan, KYA, Retraining, on-chain attestation — are billable API services.
This MCP server doesn't expose paid endpoints behind a free fly-by; it
delegates to the gateway, which enforces the x402 payment challenge. See
[PHILOSOPHY](https://agentresources.xyz/philosophy).

## Crypto-scam notice

AR has **no token, no presale, no airdrop, no points, no staking**. We will
**never** DM you to ask for seed phrases, private keys, or funds. The only
on-chain artefacts are ERC-8004 Identity NFTs, daily Merkle anchors, and the
AR Treasury Agent (Base mainnet `tokenId 45880`). Report impersonation to
contact@agentresources.xyz.

## How this repo stays in sync

This repo is a downstream **mirror** of the canonical source at
`packages/mcp/` in the AR monorepo. CI on every push:

1. Re-runs `npm pack` against the published `@agentresources/mcp@<version>` and diffs the tarball contents against `src/` here.
2. Validates `server.json` against the live MCP Registry schema.

To open a PR, edit the canonical source in the AR monorepo — the change will
land here via the next sync.

## License

[MIT](./LICENSE) © Agent Resources

## Trust Card

Verify the publisher of this repo:
[https://api.agentresources.xyz/.well-known/trust-card/agent/32f4ec0b-452e-467d-997b-ebd49730bb0a](https://api.agentresources.xyz/.well-known/trust-card/agent/32f4ec0b-452e-467d-997b-ebd49730bb0a)

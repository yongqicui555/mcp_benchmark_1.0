# 🛡️ Marcus Rug Intel — MCP Server

<!-- mcp-name: io.github.amarodeabreu/rug-munch-mcp -->

[![MCP](https://img.shields.io/badge/MCP-compatible-blue)](https://modelcontextprotocol.io)
[![PyPI](https://img.shields.io/pypi/v/rug-munch-mcp)](https://pypi.org/project/rug-munch-mcp/)
[![Tools](https://img.shields.io/badge/tools-19-green)](https://cryptorugmunch.app/api/agent/v1/status)
[![x402](https://img.shields.io/badge/x402-USDC-purple)](https://cryptorugmunch.app/.well-known/x402)
[![Free Tier](https://img.shields.io/badge/free_tier-1%2Fday-brightgreen)](https://cryptorugmunch.app/api/agent/v1/check-risk)
[![Smithery](https://img.shields.io/badge/Smithery-listed-orange)](https://smithery.ai/server/@CryptoRugMunch/rug-munch-intelligence)
[![Glama](https://img.shields.io/badge/Glama-listed-blue)](https://glama.ai/mcp/servers/@CryptoRugMunch/rug-munch-intelligence)
[![Coinbase x402 Ecosystem](https://img.shields.io/badge/Coinbase_x402-listed-blue?logo=coinbase)](https://github.com/coinbase/x402/blob/main/services/rug-munch-intelligence/metadata.json)

> **73% of new crypto tokens are scams or honeypots.** This MCP server lets your AI agent check any token before transacting — the cheapest insurance in crypto.

**19 tools** for rug pull detection, honeypot scoring, deployer tracking, holder deep-dive, KOL shill detection, social OSINT, and LLM forensic analysis (Claude Sonnet 4 / Opus 4).

## ⚡ Try It Right Now (Free)

No install needed. 1 free call/day, no auth:

```bash
curl -X POST https://cryptorugmunch.app/api/agent/v1/check-risk \
  -H "Content-Type: application/json" \
  -d '{"token_address": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr"}'
```

Response:
```json
{
  "token_address": "7GCihgDB8fe6KNjn2MYtkzZcRjQy3t9GHdC8uHYmW2hr",
  "risk_score": 85,
  "risk_level": "critical",
  "recommendation": "AVOID",
  "honeypot_risk": true,
  "freeze_authority": true,
  "token_name": "SuspiciousToken",
  "token_symbol": "SCAM"
}
```

## 🚀 Quick Start

### Option 1: Install via pip

```bash
pip install rug-munch-mcp
```

### Option 2: Remote SSE (no install)

Connect directly to our hosted server:
```
https://cryptorugmunch.app/mcp/sse
```

### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "rug-munch": {
      "command": "rug-munch-mcp",
      "env": {}
    }
  }
}
```

### Cursor / Windsurf / VS Code

```json
{
  "mcpServers": {
    "rug-munch": {
      "command": "rug-munch-mcp",
      "env": {}
    }
  }
}
```

### OpenClaw

```bash
mcporter config add rug-munch --command "rug-munch-mcp"
mcporter call rug-munch.check_token_risk token_address=<MINT>
```

## 🔧 All 19 Tools

| Tool | What | Price |
|------|------|-------|
| `check_token_risk` | Quick risk score (0-100) + recommendation | **Free** (1/day) or $0.04 |
| `check_token_risk_premium` | Full breakdown + deployer + social OSINT | $0.10 |
| `check_batch_risk` | Up to 20 tokens at once | $0.30 |
| `check_deployer_history` | Deployer wallet analysis — serial rugger? | $0.06 |
| `get_token_intelligence` | Complete token profile (price, holders, LP) | $0.06 |
| `get_holder_deepdive` | Top holders, concentration, sniper detection | $0.10 |
| `get_social_osint` | Social media presence and red flags | $0.06 |
| `get_kol_shills` | KOL/influencer shill detection | $0.06 |
| `get_coordinated_buys` | Detect coordinated buying patterns | $0.04 |
| `check_blacklist` | Community blacklist check | $0.02 |
| `check_scammer_wallet` | Known scammer wallet check | $0.02 |
| `get_market_risk_index` | Global market risk overview | $0.02 |
| `get_serial_ruggers` | Known serial rugger wallets | $0.02 |
| `marcus_quick` | AI verdict — Claude Sonnet 4 quick analysis | $0.15 |
| `marcus_forensics` | AI forensics — full Claude Sonnet 4 investigation | $0.50 |
| `marcus_ultra` | AI deep analysis — Claude Opus 4 | $2.00 |
| `marcus_thread` | AI analysis thread for X/Twitter | $1.00 |
| `watch_token` | 7-day webhook monitoring for risk changes | $0.20 |
| `get_api_status` | Service health + accuracy metrics | Free |

## 💳 Authentication Options

### Free Tier (recommended to start)
- **10 calls/day** on `check_token_risk` — no auth needed
- Just send the request, we'll answer

### API Key (1,000 calls/hr)
```bash
# Get a key instantly (free, anonymous)
curl -X POST https://cryptorugmunch.app/api/agent/v1/keys/request \
  -H "Content-Type: application/json" \
  -d '{"email": "you@example.com"}'

# Use it on ALL 19 endpoints
curl -X POST https://cryptorugmunch.app/api/agent/v1/check-batch \
  -H "Content-Type: application/json" \
  -H "X-API-Key: mri_your_key_here" \
  -d '{"tokens": ["token1", "token2", "token3"]}'
```

### x402 USDC Micropayments
Pay per-call with USDC on **Base** or **Solana**. See [x402 docs](https://cryptorugmunch.app/.well-known/x402).

Compatible with [x402-fetch](https://github.com/coinbase/x402), [x402-axios](https://github.com/coinbase/x402), [Coinbase AgentKit](https://github.com/CryptoRugMunch/rug-agent-kit), and any x402-enabled client.

## 🌐 Where We're Listed

| Registry | Link |
|----------|------|
| **Official MCP Registry** | `io.github.amarodeabreu/rug-munch-mcp` |
| **PyPI** | [`pip install rug-munch-mcp`](https://pypi.org/project/rug-munch-mcp/) |
| **Smithery** | [rug-munch-intelligence](https://smithery.ai/server/@CryptoRugMunch/rug-munch-intelligence) |
| **Glama** | [rug-munch-intelligence](https://glama.ai/mcp/servers/@CryptoRugMunch/rug-munch-intelligence) |
| **x402 Bazaar** | [cryptorugmunch.app](https://api.cdp.coinbase.com/platform/v2/x402/discovery/resources?resource_server=cryptorugmunch.app) |
| **A2A Agent Card** | [`/.well-known/agent.json`](https://cryptorugmunch.app/.well-known/agent.json) |
| **awesome-x402** | [PR #28 merged](https://github.com/xpaysh/awesome-x402) |

## 📡 Discovery Endpoints (Free)

```bash
# Service status & accuracy metrics
curl https://cryptorugmunch.app/api/agent/v1/status

# OpenAPI spec
curl https://cryptorugmunch.app/api/agent/v1/openapi.json

# Human-readable skill description
curl https://cryptorugmunch.app/api/agent/v1/skill.md

# x402 payment details
curl https://cryptorugmunch.app/.well-known/x402

# A2A agent card
curl https://cryptorugmunch.app/.well-known/agent.json

# MCP server info
curl https://cryptorugmunch.app/.well-known/mcp.json
```

## 🤖 For Agent Developers

### Reference Trading Agent
Full Python example agent that uses x402 to check tokens before trading:
→ [CryptoRugMunch/x402-trading-agent](https://github.com/CryptoRugMunch/x402-trading-agent)

### Coinbase AgentKit Plugin
Drop-in plugin for AgentKit-powered agents:
→ [CryptoRugMunch/rug-agent-kit](https://github.com/CryptoRugMunch/rug-agent-kit)

## 🏗️ Architecture

```
Your Agent
    │
    ├── pip install rug-munch-mcp  (local STDIO)
    │   └── Talks to cryptorugmunch.app API
    │
    ├── SSE: cryptorugmunch.app/mcp/sse  (remote, no install)
    │
    └── Direct HTTP: cryptorugmunch.app/api/agent/v1/*
        ├── Free tier (1/day, no auth)
        ├── API key (1000/hr, X-API-Key header)
        └── x402 USDC (Payment-Signature header)
```

## 📊 Trust & Transparency

- **Trust score**: Published at `/api/agent/v1/status`
- **Detection accuracy**: 91%+ on known rug pulls
- **Uptime**: 99.9%+ (monitored)
- **Response time**: <500ms for cached, <5s for fresh scans
- **Feedback loop**: `POST /api/agent/v1/feedback` — report false positives

## License

MIT

---

> **⚠️ Note:** This project was formerly known as CryptoRugMunch. The $CRM token is **not affiliated** with Marcus Rug Intel. We operate on a Stars-based subscription model — no token required.

*Built by [Marcus Rug Intel](https://x.com/MarcusRugIntel) — the cheapest insurance in crypto.*

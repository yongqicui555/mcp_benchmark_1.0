# Feedback Synthesis MCP

[![MCP.Directory](https://img.shields.io/badge/MCP.Directory-listed-blue)](https://mcp.directory/servers?q=feedback-synthesis-mcp)

> Customer feedback intelligence for AI agents and developers. Synthesize GitHub Issues, Hacker News threads, and App Store reviews into ranked pain clusters with evidence links. Pay-per-call via x402 micropayments — no signup required.

<!-- mcp-name: io.github.sapph1re/feedback-synthesis-mcp -->

Stop reading through hundreds of feedback items manually. Feedback Synthesis MCP collects from multiple sources, runs a multi-pass LLM pipeline, and returns ranked pain clusters with impact scores, evidence links, and suggested actions — machine-readable for agents, human-readable for founders.

## Quick Start

**Install:**

```bash
pip install feedback-synthesis-mcp
```

**Set your wallet key** (any EVM wallet with USDC on Base mainnet):

```bash
export EVM_PRIVATE_KEY=your_private_key_here
```

**Add to Claude Desktop** — edit `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "feedback-synthesis-mcp": {
      "command": "feedback-synthesis-mcp",
      "env": {
        "EVM_PRIVATE_KEY": "your_private_key_here"
      }
    }
  }
}
```

**Add to Cursor** — edit `.cursor/mcp.json` in your project root:

```json
{
  "mcpServers": {
    "feedback-synthesis-mcp": {
      "command": "feedback-synthesis-mcp",
      "env": {
        "EVM_PRIVATE_KEY": "your_private_key_here"
      }
    }
  }
}
```

Restart your client. You now have four customer intelligence tools available.

---

## Tools

| Tool | What it does | Price |
|------|-------------|-------|
| `synthesize_feedback` | Multi-source synthesis → ranked pain clusters with evidence | $0.05/call |
| `get_pain_points` | Quick single-source pain point extraction | $0.02/call |
| `search_feedback` | Full-text search across cached feedback items | $0.01/call |
| `get_sentiment_trends` | Time-series sentiment across sources | $0.03/call |

**Supported sources**: GitHub Issues, Hacker News, Apple App Store Reviews

---

## Examples

### Synthesize feedback from multiple sources

```
synthesize_feedback(
  sources=[
    {"type": "github_issues", "target": "owner/my-repo", "labels": ["bug", "feature-request"]},
    {"type": "hackernews", "target": "Show HN: MyProduct"}
  ],
  since="2026-01-01T00:00:00Z"
)
```

Returns:
```json
{
  "job_id": "syn_abc123",
  "status": "completed",
  "summary": "Analyzed 347 feedback items from 2 sources. Found 6 pain clusters.",
  "pain_clusters": [
    {
      "rank": 1,
      "title": "Authentication flow breaks on mobile Safari",
      "severity": "critical",
      "frequency": 23,
      "impact_score": 0.92,
      "description": "Users report inability to complete OAuth login on iOS Safari. Affects onboarding conversion.",
      "evidence": [
        {
          "source": "github",
          "url": "https://github.com/owner/my-repo/issues/142",
          "snippet": "Login fails silently on Safari 17.2+"
        }
      ],
      "suggested_actions": [
        "Fix Safari WebAuthn polyfill (see issue #142)",
        "Add fallback auth flow for mobile browsers"
      ]
    }
  ]
}
```

### Quick pain points from GitHub Issues

```
get_pain_points(
  source={"type": "github_issues", "target": "owner/my-repo", "labels": ["bug"]},
  top_n=5
)
```

### Search for specific topics

```
search_feedback(query="pricing too expensive", sources=["github_issues", "hackernews"])
```

### Track sentiment over time

```
get_sentiment_trends(
  sources=[{"type": "appstore", "target": "com.example.myapp"}],
  since="2025-10-01T00:00:00Z",
  granularity="weekly"
)
```

---

## Payment

This MCP uses [x402 micropayments](https://x402.org) on Base mainnet (USDC). You need:

1. An EVM wallet with USDC on Base mainnet
2. The wallet's private key set as `EVM_PRIVATE_KEY`

Each call costs $0.01–$0.05 USDC. Payments are made automatically — no subscriptions, no API keys.

**No payment configured?** The server returns a helpful error with setup instructions.

---

## Architecture

This package is a thin MCP client. All processing happens on the hosted backend:

```
Your Agent / Claude Desktop
        │
        ▼
feedback-synthesis-mcp (this package)
  - MCP tool definitions
  - x402 payment signing
  - Zero business logic
        │ HTTPS + x402
        ▼
Hosted Backend (Railway)
  - Multi-source data collection
  - 3-stage LLM pipeline (Haiku × N + Sonnet × 1)
  - SQLite caching + FTS search
  - x402 payment verification
```

Server code is private (moat). Thin client is open source.


## Direct MCP over HTTP (Streamable HTTP Transport)

Skip the PyPI package for programmatic/agent access using the hosted MCP endpoint directly:

**MCP Server URL**: `https://feedback-synthesis-mcp-production.up.railway.app/mcp/`

For MCP clients that support Streamable HTTP transport (Claude Desktop via HTTP, custom agents):

```json
{
  "mcpServers": {
    "feedback-synthesis-mcp": {
      "type": "streamable-http",
      "url": "https://feedback-synthesis-mcp-production.up.railway.app/mcp/"
    }
  }
}
```

x402 payment is handled automatically by the client SDK. Set `EVM_PRIVATE_KEY` in your environment.

---

---

## License

MIT


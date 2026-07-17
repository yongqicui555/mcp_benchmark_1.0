# Prompeteer MCP Server

**Enterprise-grade MCP server for AI prompt engineering.** Generate expert-level prompts for 140+ AI platforms, score prompt quality across 16 dimensions, and manage your prompts in PromptDrive.

[![Website](https://img.shields.io/badge/Website-prompeteer.ai-E05432)](https://prompeteer.ai)
[![MCP](https://img.shields.io/badge/MCP-Compatible-blue)](https://modelcontextprotocol.io)
[![Transport](https://img.shields.io/badge/Transport-SSE%20%2B%20Streamable%20HTTP-green)](https://prompeteer.ai/mcp)
[![Auth](https://img.shields.io/badge/Auth-OAuth%202.1-purple)](https://prompeteer.ai/oauth/authorize)

---

## Tools

| Tool | Description | Type |
|------|-------------|------|
| `generate_prompt` | Generate an optimized AI prompt for any of 140+ platforms | Write |
| `list_prompts` | Browse your PromptDrive library with search and filtering | Read |
| `get_prompt` | Retrieve a specific saved prompt by ID | Read |
| `score_prompt` | Analyze prompt quality across 16 dimensions | Read |
| `save_to_promptdrive` | Save a prompt to your PromptDrive library | Write |

## Quick Setup

### Claude Desktop

Add to your `claude_desktop_config.json` (Settings > Developer > Edit Config):

```json
{
  "mcpServers": {
    "prompeteer": {
      "url": "https://prompeteer.ai/mcp/sse",
      "transport": "sse"
    }
  }
}
```

### Claude.ai (Web)

1. Open [Claude.ai](https://claude.ai)
2. Go to **Settings > Connectors > Manage Connectors**
3. Click **Add custom server**
4. Enter URL: `https://prompeteer.ai/mcp`
5. Complete OAuth login

### ChatGPT

1. Open **ChatGPT Settings > Developer Mode**
2. Click **Add App**
3. Enter URL: `https://prompeteer.ai/mcp`
4. Complete OAuth login

### Cursor

Add to `.cursor/mcp.json`:

```json
{
  "servers": {
    "prompeteer": {
      "type": "sse",
      "url": "https://prompeteer.ai/mcp/sse"
    }
  }
}
```

### VS Code / GitHub Copilot

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "prompeteer": {
      "type": "sse",
      "url": "https://prompeteer.ai/mcp/sse"
    }
  }
}
```

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

```json
{
  "mcpServers": {
    "prompeteer": {
      "serverUrl": "https://prompeteer.ai/mcp/sse",
      "transport": "sse"
    }
  }
}
```

### Cline / Continue / Other MCP Clients

Use these connection details in your client's MCP settings:

- **Server URL (SSE):** `https://prompeteer.ai/mcp/sse`
- **Server URL (Streamable HTTP):** `https://prompeteer.ai/mcp`
- **Authentication:** OAuth 2.1 (automatic redirect)

## Server Details

| Property | Value |
|----------|-------|
| **Endpoint (SSE)** | `https://prompeteer.ai/mcp/sse` |
| **Endpoint (Streamable HTTP)** | `https://prompeteer.ai/mcp` |
| **Authentication** | OAuth 2.1 with PKCE |
| **Authorization URL** | `https://prompeteer.ai/oauth/authorize` |
| **Token URL** | `https://prompeteer.ai/oauth/token` |
| **Discovery** | `https://prompeteer.ai/mcp/.well-known/oauth-authorization-server` |
| **Scopes** | `mcp:read`, `mcp:write`, `mcp:generate` |
| **Rate Limit** | 120 requests/minute |
| **Session Limit** | 20 per user |

## Features

- **140+ Platform Support** — Optimized prompt generation for ChatGPT, Claude, Gemini, Midjourney, DALL-E, Stable Diffusion, Suno, and 130+ more
- **16-Dimension Quality Scoring** — Linguistic quality, structural integrity, information density, platform optimization
- **PromptDrive** — Personal prompt library with search, categorization, and auto-tagging
- **Multi-Modal** — Text, image, video, audio, and code prompt generation
- **Multi-Lingual** — 45+ language support
- **Interactive MCP Apps** — Rich UI components rendered directly in compatible clients
- **Enterprise Security** — OAuth 2.1 with PKCE, rate limiting, session management, audit logging

## Pricing

See [prompeteer.ai/pricing](https://prompeteer.ai/pricing) for current plans and pricing.

## Supported Clients

Works with any MCP-compatible client including:

- Claude Desktop / Claude.ai / Claude Code
- ChatGPT (Developer Mode + Custom GPTs)
- Cursor
- VS Code / GitHub Copilot
- Windsurf
- Cline
- Continue
- Zed
- goose (Block)
- Amazon Q CLI
- LM Studio
- LobeChat

## Links

- **Website:** [prompeteer.ai](https://prompeteer.ai)
- **MCP Documentation:** [prompeteer.ai/mcp](https://prompeteer.ai/mcp)
- **Privacy Policy:** [prompeteer.ai/privacy](https://prompeteer.ai/privacy)
- **Terms of Service:** [prompeteer.ai/terms](https://prompeteer.ai/terms)
- **Support:** info@prompeteer.com

## License

MIT — This repository contains connection configuration and documentation only. The Prompeteer platform is proprietary.

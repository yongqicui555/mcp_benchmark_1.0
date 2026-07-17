# ScreenshotInk MCP Server

[![npm version](https://img.shields.io/npm/v/%40screenshotink%2Fmcp)](https://www.npmjs.com/package/@screenshotink/mcp)
[![MCP](https://img.shields.io/badge/MCP-remote%20%2B%20stdio-6E5CFF)](https://modelcontextprotocol.io)
[![license](https://img.shields.io/badge/license-MIT-green)](LICENSE)

Give your AI agent eyes. **Five tools to capture, batch, compare and audit any web page** — through [ScreenshotInk](https://screenshotink.com)'s hosted Chromium fleet. No local browser, no Puppeteer maintenance; works in Claude Desktop, Claude Code, Cursor, Windsurf, CI runners and cloud sandboxes.

Every result returns the screenshot **inline in the same turn**, so the agent can reason about pixels immediately.

```
You:    Compare our pricing page on staging vs production — did the new cards ship?
Agent:  ▸ compare_screenshots { url_a: "https://acme.com/pricing", url_b: "https://staging.acme.dev/pricing" }
        4.7% of pixels differ, all inside the plan grid — the new Scale card is present. Deploy looks correct. ✓
```

## Quick start

You need a ScreenshotInk API key — **free, 100 captures/month, no card**: [screenshotink.com/signup](https://screenshotink.com/signup)

### Claude Code

```bash
claude mcp add screenshotink -- npx -y @screenshotink/mcp --key sk_live_YOUR_KEY
```

or connect to the hosted remote server (nothing runs locally):

```bash
claude mcp add --transport http screenshotink https://mcp.screenshotink.com/mcp \
  --header "Authorization: Bearer sk_live_YOUR_KEY"
```

### Claude Desktop

`claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "screenshotink": {
      "command": "npx",
      "args": ["-y", "@screenshotink/mcp"],
      "env": { "SCREENSHOTINK_API_KEY": "sk_live_YOUR_KEY" }
    }
  }
}
```

### Cursor / Windsurf

```json
{
  "mcpServers": {
    "screenshotink": {
      "command": "npx",
      "args": ["-y", "@screenshotink/mcp", "--key", "sk_live_YOUR_KEY"]
    }
  }
}
```

### Remote server (cloud agents, hosted runtimes, custom connectors)

Anything that speaks Streamable HTTP can connect directly — nothing to install. In
**Claude** or **ChatGPT**, add it as a *custom connector* with the URL below and sign in
over OAuth; for scripts/CI, pass your key as a bearer token:

```
URL:   https://mcp.screenshotink.com/mcp
Auth:  OAuth 2.1 (sign in on first use) — or Authorization: Bearer sk_live_YOUR_KEY
```

## Tools

| Tool | What it does |
|---|---|
| `take_screenshot` | Capture any URL — viewport or full page, png/jpeg/pdf, dark mode, ad & cookie-banner blocking, lazy-load handling |
| `bulk_screenshots` | Up to 20 URLs in one call — audit a funnel or a competitor set at once |
| `compare_screenshots` | Pixel-diff two URLs (staging vs production, before vs after) — returns changed-% and a highlighted diff image |
| `run_lighthouse` | Google Lighthouse scores (performance, accessibility, best practices, SEO) + core web vitals |
| `capture_sitemap` | Fetch a sitemap.xml and screenshot every page it lists |

Same parameters and defaults as the [REST API](https://screenshotink.com/docs/request-parameters). Captures over MCP count against the same quota as the REST API — one key, one meter. Identical requests within 24h are served from cache for free.

## Why hosted?

- **CI pipelines** — no headless Chrome install, no flaky browser binaries in runners.
- **Cloud agents** — hosted runtimes can't launch browsers; the remote endpoint gives them eyes with zero dependencies.
- **Zero maintenance** — we patch Chromium, handle lazy-load, ads and cookie walls. Your agent just asks for pixels.

## Links

- Product & docs: [screenshotink.com](https://screenshotink.com) · [MCP docs](https://screenshotink.com/docs/mcp)
- REST API reference: [screenshotink.com/docs](https://screenshotink.com/docs)
- Issues: [GitHub issues](https://github.com/bikker/screenshotink-mcp/issues)

---

MIT © [ScreenshotInk](https://screenshotink.com) — a [ScalingWeb](https://scalingweb.com) product

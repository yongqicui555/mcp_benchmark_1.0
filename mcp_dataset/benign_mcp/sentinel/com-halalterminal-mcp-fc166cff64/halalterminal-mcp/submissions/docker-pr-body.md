## Add Halal Terminal remote MCP server

This PR adds the **Halal Terminal** MCP server — Shariah-compliant stock & ETF screening — to the Docker MCP Registry as a **remote server** (transport: SSE).

### What it does

22 tools across 8 categories:

- **Screening** — `screen_stock`, `screen_etf`, `bulk_screen` across five Shariah methodologies (AAOIFI, DJIM, FTSE, MSCI, S&P)
- **Portfolio audit** — per-stock verdict + aggregate compliant % + purification owed
- **Zakat & purification** — 2.5% zakat against a live nisab; impure-portion calculation per dividend
- **Market data, news, SEC filings** — quotes, history, dividends, EDGAR XBRL facts
- **Watchlists, comparisons, generated reports, Islamic-finance education**

### Why a remote server (no Dockerfile)

The MCP server runs on Halal Terminal infrastructure and exposes SSE at `https://mcp.halalterminal.com/sse`. There's also an npm-published stdio bridge (`@halalterminal/mcp`) for clients that need stdio, but the canonical surface is the remote endpoint — which is what `server.yaml` reflects.

### Auth

Per-user `X-API-Key` header. Free tier at https://api.halalterminal.com (500 tokens/month, no credit card).

### License

Apache-2.0 — repo: https://github.com/goww7/halalterminal-mcp

### Test credentials

Submitted via https://forms.gle/6Lw3nsvu2d6nFg8e6 with a Docker-review-dedicated key.

### Checklist

- [x] License is MIT or Apache-2.0 (Apache-2.0)
- [x] `server.yaml` placed under `servers/halalterminal/`
- [x] `type: server` + `remote:` block (SSE)
- [x] Categorized under `finance`
- [x] Maintainer attribution single-source: `Yassir <yassir@halalterminal.com>`
- [x] Logo URL provided

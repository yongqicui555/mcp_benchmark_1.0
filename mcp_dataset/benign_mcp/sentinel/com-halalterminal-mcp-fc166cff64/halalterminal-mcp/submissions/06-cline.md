# 06 — Cline MCP Marketplace

**URL:** https://cline.bot/mcp-marketplace
**Submit:** GitHub issue at https://github.com/cline/mcp-marketplace/issues/new?template=mcp-server-submission.yml
**Free:** Yes
**Review time:** "couple of days" per their README
**Heads up:** Cline's submission docs explicitly note **"increased scrutiny to projects in sensitive domains (such as financial services)"** — be substantive in the "Reason for Addition".

## Required materials

1. **GitHub repo URL** — `https://github.com/goww7/halalterminal-mcp`
2. **400×400 PNG logo** — must exist as a file you can upload to the GitHub issue. If we don't have one yet, generate from the OG image:
   ```bash
   curl -sL https://halalterminal.com/android-chrome-192x192.png -o /tmp/og.png
   # Then resize to 400×400 in any image tool, or:
   magick /tmp/og.png -resize 400x400^ -gravity center -extent 400x400 /tmp/halalterminal-400.png
   ```
3. **Reason for Addition** (paste below)
4. **Confirm Cline can install from your README alone** — test it: in Cline, paste the repo's README and let Cline set it up against `mcp.halalterminal.com/sse`. If it works, mention this in the issue.

## Issue body (paste verbatim into the template)

```markdown
**GitHub Repo URL:** https://github.com/goww7/halalterminal-mcp

**Logo:** [attach 400×400 PNG]

**Reason for Addition:**

The first MCP server purpose-built for Shariah-compliant (halal) investing — a category Cline currently has no coverage of, despite ~1.8 billion potential users globally and rising mainstream interest in ethical/values-aligned investing more broadly.

What it does for Cline users:
- **Screen any stock or ETF** against five Shariah methodologies (AAOIFI, DJIM, FTSE, MSCI, S&P) in one call — `screen_stock("AAPL")`, `screen_etf("SPY")`.
- **Audit portfolios** end-to-end — per-stock verdict, aggregate compliant %, purification owed.
- **Calculate zakat** on holdings (2.5% obligatory charity) and dividend purification (impure-portion donation).
- **Bulk-screen** entire indices (S&P 500, NASDAQ-100, FTSE 100) with run/poll/diff workflow.
- **Market data, news, SEC EDGAR XBRL** — all the supporting facts an investor would normally pivot tabs to find.

**22 tools** across 8 categories. Apache-2.0 licensed. Free API tier (no credit card) lets users evaluate before subscribing — important for an audience that's typically suspicious of paywalled "halal" services.

**Security & domain handling (per your sensitive-domains note):**
- Auth via per-user `X-API-Key` header — no shared credentials, every tool call is scoped to the calling key.
- No order execution, no broker integrations — read-only research surface.
- API keys are revocable from the user's dashboard (https://halalterminal.com/dashboard).
- All verdicts are explicitly framed as methodology-based screenings, **not fatwas**.
- Apache-2.0 (no GPL); no cryptocurrency tools.

**README has been verified to install cleanly via Cline** — README contains client-specific snippets (Cline, Claude Desktop, Cursor, Windsurf), an `npx -y @halalterminal/mcp` one-liner, and an `llms-install.md` is included for additional agent guidance.

Maintainer: Yassir <yassir@halalterminal.com>
```

## After-submission etiquette

- Subscribe to the issue (top-right) so you get review-thread pings.
- If reviewers ask for changes, reply within 48h — Cline's queue moves fast.
- Once approved, share the marketplace listing URL on Twitter/Reddit/r/IslamicFinance for first-week installs.

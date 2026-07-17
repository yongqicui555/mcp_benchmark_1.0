# Distribution checklist — get ScreenshotInk MCP listed

Submitting is a human step (each needs an account / PR). Everything below is
copy-paste ready. Submit organically; don't spam or fabricate reviews.

## Canonical listing copy (paste into every directory)

- **Name:** ScreenshotInk
- **Tagline:** Screenshot, compare, audit & monitor any web page — 5 tools for AI agents.
- **Short description (1 sentence):** A hosted screenshot MCP server that lets an agent capture full pages, bulk-capture, pixel-diff (staging vs production), run Lighthouse, and screenshot a whole sitemap — with the image returned inline for same-turn reasoning.
- **Long description:** ScreenshotInk gives AI agents eyes over the web. Five tools — `take_screenshot`, `bulk_screenshots`, `compare_screenshots`, `run_lighthouse`, `capture_sitemap` — run on ScreenshotInk's hosted Chromium fleet, so there's no local browser to maintain. Captures return inline (downscaled preview) plus a hosted full-resolution link, so the agent can reason about the rendered pixels immediately. Full-page up to 20,000px, PNG/JPEG/PDF, ad & cookie-banner blocking, 24h caching. EU-hosted. Free tier: 100 captures/month, no card.
- **Remote MCP endpoint:** `https://mcp.screenshotink.com/mcp` (Streamable HTTP; OAuth 2.1 + DCR, or `Authorization: Bearer sk_live_…`)
- **Local install:** `npx -y @screenshotink/mcp --key sk_live_…`
- **Website:** https://screenshotink.com  ·  **MCP page:** https://screenshotink.com/mcp
- **npm:** https://www.npmjs.com/package/@screenshotink/mcp  ·  **Source:** https://github.com/bikker/screenshotink-mcp
- **Auth:** OAuth (remote) or API key  ·  **Free tier:** 100 captures/mo, no card
- **Categories/tags:** developer-tools, web, screenshots, visual-testing, monitoring, lighthouse
- **Tools:** take_screenshot · bulk_screenshots · compare_screenshots · run_lighthouse · capture_sitemap
- **Logo:** https://screenshotink.com/logo-512.png

## Directories to submit to

- [ ] **Official MCP Registry** (`registry.modelcontextprotocol.io`) — publish via the
      `mcp-publish` CLI using `server.json` in this repo. Verify the file against the current
      schema first; confirm the namespace (`io.github.bikker/...`, GitHub-verified — or switch to
      `com.screenshotink/...` once the domain is DNS-verified). Docs: github.com/modelcontextprotocol/registry
- [ ] **Anthropic / Claude connectors directory** — submit the remote URL
      `https://mcp.screenshotink.com/mcp` (OAuth supported) via Anthropic's connector submission form.
- [ ] **ChatGPT apps / connectors** — submit the same remote MCP endpoint through OpenAI's
      app/connector submission once eligible.
- [ ] **Smithery** (smithery.ai) — "Add server"; point at the GitHub repo; it reads `server.json`.
- [ ] **Glama** (glama.ai/mcp/servers) — submit the GitHub repo.
- [ ] **PulseMCP** (pulsemcp.com) — submit via their "Add a server" form with the copy above.
- [ ] **mcp.so** — submit the GitHub repo / npm package.
- [ ] **awesome-mcp-servers** (github.com/punkpeye/awesome-mcp-servers) — open a PR adding one line
      under the relevant category, e.g.:
      `- [ScreenshotInk](https://github.com/bikker/screenshotink-mcp) — Screenshot, bulk-capture, pixel-diff, Lighthouse and sitemap-capture any web page; hosted, returns images inline.`

## After listing
- [ ] Cross-link the listings from the `/mcp` page once live.
- [ ] Keep `server.json` `version` in sync with the npm package on each release.

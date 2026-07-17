# 02 — npm (registry.npmjs.org/@halalterminal/mcp)

**Why this matters for SEO/acquisition:** several aggregators (Glama, mcp.so, MCPMarket) auto-index npm. The npm page itself is also a prime SEO surface — it ranks well for `@scope/package` searches and for the README's first paragraph.

## One-time scope creation

`@halalterminal` doesn't exist on npm yet (verified 2026-05-10). Create it under your personal npm account:

```bash
npm login                      # if you aren't already
npm org create halalterminal   # creates the @halalterminal scope; free for public packages
```

(If you already publish under your personal account and prefer not to create an org, you can rename to `halalterminal-mcp` (unscoped) — but `@halalterminal/mcp` is much stronger for brand recall and SEO.)

## Publish

```bash
cd /root/halalterminal-mcp
npm install                    # populates node_modules from package.json deps
npm publish --access public
```

Verify: https://www.npmjs.com/package/@halalterminal/mcp

## SEO hygiene already baked in

The shipped `package.json` already has:
- **`description`** — keyword-first, 280 chars (npm search snippet length)
- **`keywords`** — 25 entries spanning halal/shariah/methodology/MCP/client terms
- **`mcpName: "com.halalterminal/mcp"`** — required for the official-registry verification step (see 01)
- **`author` / `homepage` / `repository` / `bugs.email`** — single-contact attribution per brand rules

## Update flow

Bump `version` in `package.json` AND `server.json`, then:

```bash
npm publish --access public
mcp-publisher publish
```

Always publish to npm BEFORE running `mcp-publisher publish` — the registry validates the npm artifact exists and reads `mcpName` from it.

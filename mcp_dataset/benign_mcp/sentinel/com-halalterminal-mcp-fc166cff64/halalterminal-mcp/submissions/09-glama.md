# 09 — Glama (glama.ai/mcp/servers)

**URL:** https://glama.ai/mcp/servers
**Submit:** Auto-indexes from npm + GitHub. Manual claim/add at https://glama.ai/mcp/servers/add
**Free:** Yes
**Review:** instant (auto) or 24h (manual review)
**Why bother manually:** Glama assigns a "score" badge based on metadata completeness. Manual claim lets you set categories, tags, and screenshots that the auto-indexer can't infer.

## After auto-indexing happens

1. Wait ~24h after `npm publish`
2. Search https://glama.ai/mcp/servers for `halalterminal` — your listing should be there
3. Click **"Claim this server"** (auth via GitHub, must own the source repo)
4. Edit fields per the mapping below

## Field mapping (claim flow)

| Field | Value |
|---|---|
| **Display name** | `Halal Terminal` |
| **Description** | (paste **Full description ≤800 chars**) |
| **Categories** | `Finance`, `Investing`, `Research` |
| **Tags** | (paste keyword set from `copy-bank.md`) |
| **Screenshots** | optional but boost score — capture: (1) Claude Desktop screening AAPL, (2) portfolio audit JSON output, (3) bulk-screen results table |
| **Source repo** | `https://github.com/goww7/halalterminal-mcp` |
| **NPM** | `@halalterminal/mcp` |
| **Remote SSE** | `https://mcp.halalterminal.com/sse` |

## Glama score levers (these all boost ranking)

- ✅ MIT or Apache-2.0 license (you have Apache-2.0)
- ✅ README has install instructions
- ✅ Has `keywords` in package.json
- ✅ Has tagged release on GitHub
- ⏺ Add CHANGELOG.md
- ⏺ Add CI badge (GitHub Actions running on each push)
- ⏺ Add at least one screenshot during claim

## Notes

- Glama embeds itself into other MCP discovery sites' badges (you'll see `glama.ai/mcp/servers/.../badges/score.svg` referenced in many awesome-list entries). Higher score → more secondary visibility.

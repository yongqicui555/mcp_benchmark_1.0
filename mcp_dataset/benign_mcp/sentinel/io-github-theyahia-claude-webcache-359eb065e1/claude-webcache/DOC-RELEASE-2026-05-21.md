# Doc-Sync Report — 2026-05-21

Triggered by request to "sync documentation after recent v0.1.5+ npm release."
Actual on-disk state is much further along: current published version is **0.4.0**
(package.json, plugin/.claude-plugin/plugin.json, .claude-plugin/marketplace.json
all consistent). README MCP tool list is up-to-date with all 8 v0.4 tools
(`cached_fetch`, `cache_store`, `cache_stats`, `cache_list`, `cache_invalidate`,
`cache_clear`, `cache_warm`, `cache_refresh`). The trigger appears to be stale —
no v0.1.5-era drift was found.

## Files edited

- **CHANGELOG.md** — added an `## Unreleased` section at the top documenting two
  post-0.4.0 fixes that have landed on `main` but have not been version-bumped or
  published to npm:
  - `856adf1` (2026-05-14) — race-safe schema migration (WAL init retry +
    duplicate-column tolerance in `plugin/src/cache.js`)
  - `2bd5855` (2026-05-15, rd275 part 1) — hooks.json swapped
    `${CLAUDE_PLUGIN_ROOT}/scripts/…` → `./scripts/…` (same fix that was already
    applied to `.mcp.json` back in v0.1.1)

## Files inspected, not edited

- **README.md** — no drift. Tool table already lists all 8 v0.4 tools. The
  "v0.1.5+: every WebFetch is automatically saved" mention in the lead paragraph
  is historically correct (that's the version the feature debuted in), not stale
  phrasing.
- **package.json / plugin/.claude-plugin/plugin.json / .claude-plugin/marketplace.json**
  — all three at 0.4.0, consistent. No edit needed.
- **CLAUDE.md** — does not exist in this repo (no in-repo agent guide).
  D:/Yahia/CLAUDE.md (project root) has a `## WebFetch caching (claude-webcache)`
  block that describes the v0.1.5 auto-cache hook + 4 MCP tools; that block is
  in the root `D:/Yahia/CLAUDE.md`, not in this repo, and is technically still
  v0.3-era — see "Recommended follow-ups" below.

## What I found inconsistent

1. **CHANGELOG was 2 commits behind `main`.** Fixed by adding `## Unreleased`
   section. Conservative: did not invent a 0.4.1 version since the fixes haven't
   been bumped or published to npm.
2. **README install command and "v0.1.5+" lead paragraph** mention a version
   from 7 minor releases ago. Not technically wrong (the feature did debut
   there), but feels dated against the actual 0.4.0 surface area. Did not edit —
   the historical attribution is meaningful and the rest of the README correctly
   describes v0.4 behavior (namespaces, gzip, canonicalization, dashboard, CLI).
3. **D:/Yahia/CLAUDE.md "WebFetch caching" block** still describes only the
   original 4 MCP tools (`cached_fetch`, `cache_store`, `cache_stats`,
   `cache_list`) and the v0.1.5 auto-hook. It does not mention the 4 v0.3+/0.4
   tools (`cache_invalidate`, `cache_clear`, `cache_warm`, `cache_refresh`),
   namespaces, the dashboard CLI, or the env vars introduced in 0.3/0.4. This
   file is **outside this repo** and is the user's project-wide config, so I did
   NOT edit it from this doc-sync sprint — flagging as a follow-up.

## Recommended follow-ups (not done — flagged for user)

1. **Decide v0.4.1 release** for the 2 unreleased fixes. Both are real bug
   fixes (concurrent-write race + a hook path bug that breaks the install
   experience). If you do release, bump `package.json` + `plugin.json` +
   `marketplace.json` together, move the `## Unreleased` section to `## 0.4.1
   — <date>`, tag, npm publish, marketplace refresh per the global CLAUDE.md
   plugin cheatsheet.
2. **Update `D:/Yahia/CLAUDE.md` "WebFetch caching" block** to v0.4 surface —
   add `cache_invalidate / cache_clear / cache_warm / cache_refresh` to the tool
   table, mention `WEBCACHE_NAMESPACE` for per-project isolation, mention the
   CLI dashboard at `http://localhost:37778`. This will keep agents using the
   richer toolset by default.
3. **Optional README polish (low priority):** consider freshening the lead
   paragraph from "v0.1.5+: every WebFetch is automatically saved" to "auto-
   caches every WebFetch via PostToolUse hook (since v0.1.5)" — same fact,
   less version-anchored phrasing. Skipped as cosmetic.

## Idempotency

This file's existence (≥500 bytes) will short-circuit a re-run of this
doc-sync sprint per the request's idempotency clause.

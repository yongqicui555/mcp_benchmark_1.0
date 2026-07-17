# Discord posts — claude-webcache

> Three target servers. Each gets a tailored short message + repo link.
> **Rule of thumb:** Discord is loose. Don't paste long submissions — pin a question, share repo, answer follow-ups.

---

## 1. Anthropic Discord — #plugins or #show-and-tell

**Server:** https://discord.gg/anthropic (if accessible) OR via official Claude community link
**Channel:** `#plugins` if it exists, else `#show-and-tell` or `#community-projects`
**Tone:** Builder talking to builders.

```
Shipped v0.4.0 of claude-webcache today — persistent cross-session
WebFetch cache as an MCP plugin.

Background: Claude Code's built-in WebFetch caches ~15 min in-session,
then it's gone. If you do research sprints over multiple days on the
same set of papers/docs, that adds up.

What's in v0.4:
- URL canonicalization (`?b=2&a=1` = `?a=1&b=2`, was a silent-miss bug)
- Credential redaction (`?token=xxx` masked)
- Namespace isolation per project
- 53 tests including concurrent schema-migration stress
- 8 MCP tools, ~17 KB unpacked, one dep, MIT

GitHub: https://github.com/theYahia/claude-webcache
npm: @theyahia/claude-webcache

Half technical, half marketplace-distribution lessons learned. Happy to
answer Qs on either side — particularly the marketplace.json source-format
gotchas (5 of my first 6 releases fixed delivery, not features).
```

---

## 2. Claude Developers Discord — #mcp-servers

**Server:** Find via https://www.anthropic.com/community or Claude Code docs sidebar
**Channel:** `#mcp-servers` / `#mcp-development` / `#tools`
**Tone:** Technical, MCP-deep.

```
Sharing claude-webcache (MCP plugin, MIT) for the MCP-server crowd.

Solves a specific pain: Claude Code's WebFetch is in-session only.
Across sessions you re-fetch + re-summarize the same docs, burning
context-token budget.

PostToolUse hook → SQLite (WAL) → 8 MCP tools (cached_fetch,
cache_warm, cache_invalidate, etc.) + a `cli.cjs dashboard` web UI.

Stack notes that might be interesting:
- node:sqlite (Node 22.5+), no better-sqlite3 native build
- Raw stdio JSON-RPC under MCP SDK — considering dropping the SDK
- PRAGMA busy_timeout MUST be set before journal_mode=WAL or
  concurrent schema migration races throw "disk I/O error"
- ${CLAUDE_PLUGIN_ROOT} in hooks.json silent-fails in Claude Code
  2.1.x → use relative `./scripts/` paths

Repo: https://github.com/theYahia/claude-webcache

If anyone here builds something similar (or knows of one I missed)
— I'd love to compare cache-key strategies. Currently using
SHA256(canonical_url + prompt).
```

---

## 3. r/Node.js Discord or Node-related communities

**Server:** Look for "nodejs.org community" Discord, or "JavaScript Mastery" Discord
**Channel:** `#showcase` / `#projects`
**Tone:** Stack-focused.

```
Shipped a small Node project today — claude-webcache.

For Node-deep folks: it's a useful reference for node:sqlite in
production. Node 22.5+ shipped DatabaseSync as part of stdlib;
this plugin uses it for cross-session caching with WAL mode,
concurrent schema migration (busy_timeout + retry), and ~200 lines
of total business logic.

One npm dep (@modelcontextprotocol/sdk), 53 tests
(node --test, no jest/mocha), ~17 KB unpacked.

GitHub: https://github.com/theYahia/claude-webcache

The MCP side is for Claude Code integration, but if you just want
to see how node:sqlite handles real concurrent workloads — the
test suite (plugin/test/concurrent.test.js) is probably the most
interesting file.
```

---

## Engagement rules

| Server | Reply window | Style |
|---|---|---|
| Anthropic / Claude | 60 min | Casual, founder-voice |
| MCP-specific | 30 min | Technical-deep, share code |
| Node.js community | 2 hours | Stack-detail, downplay AI angle |

---

## Don'ts

- ❌ Same paste in 3 servers within 1 hour — looks like spam.
- ❌ "Please star my repo" → never.
- ❌ Random @mentions of mods/maintainers.
- ❌ Drop a link with no context.
- ❌ Argue with skeptics for more than 1 reply.

---

## Optional: pin in your own home Discord (if applicable)

If you have your own Discord server (theYahia or builder community) — pin
the announcement with `📌` and crosslink to GitHub/npm/Habr article.

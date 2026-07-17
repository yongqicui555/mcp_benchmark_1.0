# Show HN submission — claude-webcache

> Готовый submission под https://news.ycombinator.com/submit
> **Optimal window:** Tuesday 5-7am PT (15-17 МСК) для US devs morning + EU afternoon.
> **Backup:** Wed/Thu same window. Avoid Friday afternoon, weekends, US holidays.

---

## Title (80 char limit, no emoji, prefix "Show HN:")

**Pick one:**

A. `Show HN: Claude-webcache – persistent WebFetch cache for Claude Code (MCP)` (74 chars)
B. `Show HN: Cross-session WebFetch cache as an MCP server` (54 chars)
C. `Show HN: A SQLite-backed WebFetch cache for Claude Code, as an MCP plugin` (73 chars)

**Default pick:** **A** — мост между "Claude Code" (recognizable to HN) и "MCP" (curious term for AI-aware crowd). "persistent" сигналит конкретный pain.

---

## URL field

```
https://github.com/theYahia/claude-webcache
```

**NOT** the npm link — HN audience cares about source first. Repo README has install + benchmark + architecture.

---

## Text field (optional, but recommended — ~300-500 chars)

```
Author here. Built this after my third heavy-research sprint in Claude
Code where I re-fetched the same arXiv/docs pages across sessions and
burned through token budget on repeat extractions.

It's a tiny MCP plugin: PostToolUse hook intercepts every WebFetch result,
stores it in ~/.webcache/cache.db (SQLite WAL), and exposes 8 MCP tools
(cached_fetch, cache_stats, cache_warm, etc.). One dependency, ~100 lines
of core logic, Node 22.5+ stdlib for SQLite.

v0.4.0 just shipped (May 20) with URL canonicalization (?a=1&b=2 == ?b=2&a=1),
namespace isolation, credential redaction, gzip, and a 53-test suite.

Happy to talk about MCP distribution gotchas (5 of my first 6 releases
fixed delivery mechanics, not features) and the trade-off between
"plugin with deps" vs "pure-stdlib plugin" in the current marketplace.

MIT, no telemetry, ~17 KB unpacked.
```

**Char count:** ~870 — slightly over the 500 recommended. Trim if needed. Key sentences to keep: opening pain framing + tech stack + v0.4 highlights.

---

## First comment (post immediately after submit)

HN protocol: top-level comment from OP explaining context = +signal that it's a real Show. Post within 60 seconds of submit.

```
Quick context that didn't fit in the description:

The thing that surprised me building this was how much of "shipping
an MCP server" is plumbing, not code. The cache logic is ~30 lines.
The marketplace.json format dance, the ${CLAUDE_PLUGIN_ROOT} variable
that silently doesn't resolve in Claude Code 2.1.x, the subdir layout
that has to match Anthropic's canonical pattern — those took 5-7 hours.

If you're considering shipping an MCP plugin: read the existing
plugins in ~/.claude/plugins/marketplaces/claude-plugins-official/
before writing your own marketplace.json. The docs describe 5 source
formats; in practice only one works in 2.1.x.

Caveats I'm aware of:
- 0 GitHub stars, ~12 npm downloads/wk (post-launch decay from
  300+/wk launch-week spike). Sharing the data, not claiming traction.
- Edge cases for concurrent multi-machine writers on the same cache
  file are tested but not stressed in prod yet.
- Hot-reload of .mcp.json doesn't exist — Claude Code restart required
  after install. Not a webcache bug, but worth flagging.

Happy to dig into any of: SQLite WAL pragma ordering under concurrent
schema migrations, the credential-redaction approach, or why I went
with raw stdio JSON-RPC instead of the MCP SDK for the next refactor.
```

---

## Response playbook for first 6 hours

| Comment archetype | Response |
|---|---|
| "Doesn't Claude already cache for 15 min?" | Yes — in-session. Webcache adds **cross-session** persistence via SQLite. Different problem class. |
| "Why not just use [Redis/HTTP cache]?" | This is for Claude Code specifically — auto-hook into WebFetch, MCP tool surface, single-binary plugin. Redis/HTTP cache requires wiring up. |
| "What about cache poisoning?" | Cache key = `SHA256(url + prompt)`. Won't poison cross-request, but if a malicious URL serves cached content under your prompt context — yes, that's a known limitation; auto-redaction is for tokens, not content provenance. |
| "Stars count?" | Honest: 0 stars day-of, ~12 npm DLs/wk current. Not pretending traction I don't have. |
| "Anthropic gonna block this?" | MCP is an open spec from Anthropic. They reviewed the plugin directory submission (still pending 20+ days). I don't expect a block — but if it happens I'll post here. |
| Negative / dismissive | One polite correction, then move on. Don't argue. |

**Hard rule:** never edit your submission to add metrics that came in after posting. HN sniffs that out.

---

## Pre-submit verification

- [ ] `npm view @theyahia/claude-webcache version` → `0.4.0` (so the post matches reality)
- [ ] GitHub repo README has v0.4 features documented
- [ ] You've read your own text aloud once — no marketing voice
- [ ] You have 90 minutes free after submit to answer comments (HN front-page window)
- [ ] You will NOT bump on Twitter / Discord / Reddit until 6h after HN submit (HN doesn't like coordinated amplification, even self-amplification)

---

## Don'ts

- ❌ No emoji in title or body.
- ❌ No "I hope this is useful" closer.
- ❌ No links to your other projects in the main post.
- ❌ No "please star" / "please upvote" in comments.
- ❌ No edit to add good news in body if it does well — let the comments carry it.

---

## Track

Right after submit, log to `D:/Yahia/obsidian/Base/Inbox/HN-claude-webcache-launch-<date>.md`:
- Submit timestamp UTC + your local time
- Submit URL (`/item?id=...`)
- 1h / 6h / 24h checkpoints: rank, points, comment count, npm DL spike
- Top 3 comments and your response
- Final outcome (front page reached? Y/N at what position?)

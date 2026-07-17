# Reddit submissions — claude-webcache

> Two targets: r/ClaudeAI (warmer, smaller, on-topic) + r/LocalLLaMA (broader, more skeptical).
> **Stagger:** r/ClaudeAI Day 0, r/LocalLLaMA Day +3 to avoid cross-post spam flag.

---

## 1. r/ClaudeAI (primary)

**Subreddit:** https://www.reddit.com/r/ClaudeAI/
**Karma req:** None hard, but new accounts may be filtered. Tim's reddit account age + karma TBD.
**Flair:** `Built with Claude` or `Use: Claude as a Tool` — depends on what's available at submit time. **Avoid:** `Self-promotion` (less reach).

### Title

```
I built a cross-session WebFetch cache for Claude Code (open-source MCP plugin)
```

Variants if first feels too "I built":
- `Persistent WebFetch cache for Claude Code as an MCP plugin (open-source)`
- `claude-webcache: SQLite-backed WebFetch persistence across sessions`

### Body (markdown)

```markdown
Claude Code's built-in WebFetch caches results for ~15 minutes inside one
session — useful, but every new session re-fetches the same docs and pays
the token cost for re-summarization.

If you do research-heavy work where you keep returning to the same
arXiv/docs/PubMed pages across days or weeks, that adds up.

**What it does:**

- PostToolUse hook intercepts every WebFetch, stores `(url, prompt) → result`
  in `~/.webcache/cache.db` (SQLite, WAL mode).
- 8 MCP tools: `cached_fetch`, `cache_store`, `cache_stats`, `cache_list`,
  `cache_invalidate`, `cache_clear`, `cache_warm`, `cache_refresh`.
- URL canonicalization (so `?b=2&a=1` and `?a=1&b=2` hit the same slot).
- Credential redaction (`?token=...` masked in stored URL).
- Namespace isolation per project (`WEBCACHE_NAMESPACE=...`).
- Optional gzip on payloads (`WEBCACHE_COMPRESS=1`).

**Stack:**

- Node 22.5+ (uses built-in `node:sqlite`, no native module install).
- One dependency: `@modelcontextprotocol/sdk`.
- ~17 KB unpacked.
- 53 tests (unit + MCP stdio integration + concurrent stress).
- MIT.

**Install:**

```
claude plugin marketplace add theYahia/claude-webcache
claude plugin install claude-webcache@theyahia
```

Then restart Claude Code (no hot-reload for .mcp.json — Claude Code limitation,
not the plugin).

**Honest disclaimers:**

- 0 GitHub stars at the time of posting. ~12 npm DLs/week after launch-week
  decay. Sharing what I built, not pretending traction.
- Just shipped v0.4.0 today (URL canon, credential redaction, namespaces).
  v0.1.x had silent-miss bugs that v0.4 closes.
- Cache key = `SHA256(url + prompt)`. Headers aren't part of the key — so
  if you `WebFetch` an authenticated URL, you might cross-pollinate
  responses between users on the same machine. Don't share cache.db.

Repo: https://github.com/theYahia/claude-webcache
npm: https://www.npmjs.com/package/@theyahia/claude-webcache

Happy to answer questions about MCP plugin distribution gotchas — 5 of my
first 6 releases were delivery-mechanic fixes, not features.
```

### Comment-window strategy (first 4 hours)

- Answer **every** comment within 30 min.
- If asked "why not just use the official caching layer when it ships" — "fair question; this is the gap-filler for now, happy to deprecate if Anthropic adds it natively."
- Don't argue with skeptics; offer one technical detail and stop.

---

## 2. r/LocalLLaMA (secondary, Day +3)

**Subreddit:** https://www.reddit.com/r/LocalLLaMA/
**Caveat:** LocalLLaMA leans local-model, not Claude. Will likely get less engagement but adds long-tail reach.

### Title

```
[Tool] claude-webcache: persistent WebFetch cache for AI assistants (MCP plugin, MIT)
```

### Body

```markdown
Cross-posting from r/ClaudeAI — built this to solve a research-workflow pain.

Quick story: I do heavy research sprints where I re-WebFetch the same papers
across days/weeks. The 15-min in-session cache in Claude Code is great but
evaporates between sessions. Built a tiny SQLite-backed cache that
auto-intercepts WebFetch via PostToolUse hook.

The plugin is Claude Code-specific today (MCP server hooked into Claude's
WebFetch tool), but the architecture is portable: any AI assistant that
supports MCP servers can connect to it. If you're running a local model
through an MCP-aware client (Cline, Continue, etc.), the cache will work
the same way.

**Stack:** Node 22.5+ stdlib SQLite, MCP SDK, MIT, ~17 KB. 53 tests.

**Repo:** https://github.com/theYahia/claude-webcache

Honest: 0 stars at post time, low downloads, just shipped v0.4 today.
Sharing what I built and what I learned, not pretending traction.

Open question for this sub: is there interest in adapting the cache for
non-Claude MCP clients? The MCP layer is provider-agnostic; I just haven't
tested with Ollama/llama.cpp-driven clients. PR welcome.
```

### Tags

- `Open Source`
- `Tools`
- (Avoid `Self-promotion` — Reddit deboosts)

---

## 3. r/node (tertiary, Day +5 if first two work)

**Title:**

```
claude-webcache: a pure-stdlib (almost) Node MCP plugin using node:sqlite
```

**Angle:** node:sqlite reference implementation. 1 dependency. WAL pragma ordering for concurrent schema migrations. Audience cares about Node stack, not Claude.

**Body (sketch — fill in if first two land):**

- Brief problem statement (WebFetch cross-session cache)
- 80% of content: technical decisions
  - Why node:sqlite over better-sqlite3
  - PRAGMA busy_timeout ordering for WAL init race
  - 53 tests, including 4 concurrent-stress
- Link to repo + npm

Reddit r/node moderates strictly against self-promo. Lead with the
technical contribution, not the project pitch.

---

## Anti-patterns (don't do)

- ❌ Cross-post identical title+body to 3 subs in one day → spam flag.
- ❌ Reply to your own thread to bump engagement → mods notice.
- ❌ Comment "thanks!" to every upvote → looks bot-like.
- ❌ Edit body to add "[UPDATE: HN front page]" → ego signal, kills credibility.

## Pre-submit verification

- [ ] `npm view @theyahia/claude-webcache version` returns `0.4.0`
- [ ] Repo README has v0.4 features visible above the fold
- [ ] You'll be at keyboard for the next 90 minutes after submit

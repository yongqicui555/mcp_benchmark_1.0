# Changelog

## 0.5.0 — 2026-05-21

**Auto-read + WebSearch caching. Cache stops being write-only.**

### Added

- **Auto-read for WebFetch (`PreToolUse` hook).** New `hook-webfetch-precache.cjs` runs before every WebFetch: on a cache hit it returns `permissionDecision: "deny"` with the cached content inlined in the reason, so Claude uses the cached copy and skips the network entirely. On a miss it emits nothing — WebFetch proceeds and the `PostToolUse` hook stores the result. Before this, the cache only filled on fetch and was never read back automatically; the documented "call `cached_fetch` first" pattern was manual. Disable with `WEBCACHE_AUTOREAD=0`. Large hits (>512KB) point at the `cached_fetch` MCP tool instead of inlining.
- **WebSearch caching.** WebSearch results are now cached in a dedicated `websearch` namespace under a synthetic `https://websearch.local/?q=…` URL, reusing the full set/get machinery (compression, oversize cap, eviction, hit counting). New `hook-websearch-cache.cjs` (`PostToolUse`) stores every search; `hook-websearch-precache.cjs` (`PreToolUse`) serves fresh hits. Short dedicated TTL — default **6h** — because search rankings drift; override with `WEBCACHE_SEARCH_TTL_HOURS` (`0` = never expire). New `cache.js` API: `searchUrl()`, `setSearch()`, `getSearch()`.
- **New MCP tool `cached_search({query})`** — manual lookup of the websearch namespace; returns cached results or `[CACHE_MISS] <query>`. Brings the tool count to 9.
- New env vars: `WEBCACHE_SEARCH_TTL_HOURS` (default 6), `WEBCACHE_AUTOREAD` (default on).

### Fixed (rolled up from post-0.4.0 `main`)

- **Race-safe schema migration** (`856adf1`, 2026-05-14). Two-process race during `getDb()` — first opener wins the WAL switch; second got `disk I/O error` before `busy_timeout` took effect. Fix: set `busy_timeout` FIRST, then retry `journal_mode=WAL` switch up to 5× with backoff. Also wrap `ALTER TABLE ADD COLUMN` in try/catch swallowing `duplicate column` errors from the row-shape migration race. Surfaced by `concurrent.test.js` at ~30% failure rate; now 5/5 clean.
- **Hooks use `./scripts` relative paths instead of `${CLAUDE_PLUGIN_ROOT}`** (`2bd5855`, 2026-05-15, rd275 part 1). `${CLAUDE_PLUGIN_ROOT}` does not resolve in current Claude Code releases (≤2.1.123): the `PostToolUse:WebFetch` hook silently failed (`node` could not find the literal-path module before the script body ran), so **nothing was cached** in installed builds. Switched all hook commands to plain `node ./scripts/…`. Matches the fix already in `.mcp.json` since v0.1.1.

## 0.4.0 — 2026-05-14

**Production-grade polish — correctness, security, observability, scale.**

### Added

- **URL canonicalization** before hashing — lowercase hostname, strip default ports, strip fragment, sort query params alphabetically. `https://EXAMPLE.com/p?b=2&a=1#frag` and `https://example.com/p?a=1&b=2` now share one cache slot. Eliminates silent cache misses from URL formatting variance.
- **Namespace isolation** via `WEBCACHE_NAMESPACE` env var. Multiple projects on one machine can have separate caches without cross-contamination. Default `""` preserves v0.3 single-shared-cache behavior.
- **Gzip compression** via `WEBCACHE_COMPRESS=1` — responses ≥4KB gzipped, stored as base64 in TEXT column. Typical 3-7× storage reduction on HTML/JSON. Existing uncompressed rows read fine (BC).
- **Two new MCP tools:** `cache_warm({entries: [{url, prompt}], ...})` for batch pre-flight check (returns hits/misses/invalid in one call — saves N round-trips); `cache_refresh({url, prompt})` for forced re-fetch.
- **`statsByDomain()`** API + dashboard section — per-host entry count, total hits, avg hits per entry, last fetch age.
- **Dashboard** gains pagination (offset-based, no full-1000-row load), `/api/refresh` POST endpoint, per-row refresh + invalidate buttons, namespace switcher (when DB has >1 namespace), oversize/error banners.
- **CLI** gains `warm`, `refresh`, `clear-logs`, `export --all`, `namespaces`, `stats --by-domain`, `list --offset N`, global `--namespace X` flag.
- New env vars: `WEBCACHE_NAMESPACE`, `WEBCACHE_MAX_OUTPUT_MB` (default 10), `WEBCACHE_COMPRESS`, `WEBCACHE_STRICT_REDACT`, `WEBCACHE_QUIET`.

### Changed (correctness)

- **`PRAGMA busy_timeout = 5000`** at connection open — concurrent multi-session writes no longer hit `SQLITE_BUSY` during normal operation.
- **URL credential redaction on store** — `user:pass@` and credential-like query params (`token`, `api_key`, `apikey`, `access_token`, `auth`, `secret`, `password`, `key`, `signature`, `sig`, `sessionid`) are replaced with `***` in the stored URL column. Hash key still uses unredacted canonical URL by default — opt into hash-level redaction via `WEBCACHE_STRICT_REDACT=1` (with caveat about personalized endpoints documented in README).
- **Scheme validation** — `set` rejects `data:`, `file:`, `javascript:`, `ftp:`. Only `http://` and `https://` are cached.
- **Payload size cap** — outputs >`WEBCACHE_MAX_OUTPUT_MB` (default 10) are rejected instead of bloating the DB. Counter `oversize_skipped` + `last_oversize_url` exposed in stats.
- **Hook error visibility** — `hook-webfetch-cache.cjs` logs to stderr by default (was opt-in via `WEBCACHE_DEBUG=1` in v0.3). Errors also append to `~/.webcache/hook.log` and are recorded as `last_hook_error_msg` / `last_hook_error_at` in stats. Opt out via `WEBCACHE_QUIET=1`.
- **Composite index `idx_namespace_cached_at`** — lets `cache_list` walk the index in DESC order without sort. Restores v0.3 list_50 latency (~0.11ms p50) after WHERE-namespace was added.

### Schema

- New columns on `cache`: `namespace TEXT NOT NULL DEFAULT ''`, `compressed INTEGER NOT NULL DEFAULT 0`. Added via `PRAGMA table_info` check + `ALTER TABLE ADD COLUMN` (SQLite doesn't support `IF NOT EXISTS` on ADD COLUMN).
- New table `meta_str(key TEXT PRIMARY KEY, value TEXT NOT NULL)` for string-valued metadata.
- New indexes: `idx_namespace`, `idx_namespace_cached_at`.
- Automatic migration on first DB open under v0.4. No manual steps. See `MIGRATION.md`.

### Tests

- 53 tests total (up from 17), ~7s runtime. Three files:
  - `cache.test.js` — 38 unit tests covering canonicalization, validation, redaction (incl. strict mode), payload cap, namespace isolation, gzip round-trip, busy_timeout, statsByDomain, pagination, BC, recordHookError.
  - `integration.test.js` — 11 tests spawning `mcp-server.cjs` as a child process, full JSON-RPC stdio round-trip on all 8 tools.
  - `concurrent.test.js` — 4 stress tests via `child_process.spawn` with 5-10 parallel Node workers: parallel writers (250 entries), writer + vacuum, writer + 5 readers (no partial output), schema migration idempotency under race.

### Benchmarks (v0.4.0 baseline)

| Op | p50 | p95 | p99 | ops/sec |
|---:|---:|---:|---:|---:|
| `write` | 0.09ms | 0.15ms | 2.66ms | 5,800 |
| `read_hit` | 0.07ms | 0.12ms | 0.23ms | 7,600 |
| `read_miss` | 0.04ms | 0.07ms | 0.13ms | 17,600 |
| `list_50` | 0.11ms | 0.16ms | 0.53ms | 7,400 |

Read paths slightly faster than v0.3 baseline (better miss accounting + index). Write +20% from added validation/redaction; absolute latency still well under 0.1ms p50. Storage overhead ~5% from new columns.

## 0.3.0 — 2026-05-09

**New MCP tools (cache management):**

- `cache_invalidate({ url })` — drops every entry for one URL across all prompts. Returns deleted count.
- `cache_clear({ older_than_days?, confirm? })` — bulk wipe. Pass `older_than_days: N` for age-based partial clear (no confirmation needed). For full wipe, `confirm: "YES"` is required as a safety guard.

**Honest hit rate (`cache_stats` enrichment):**

- New `meta` table tracks `miss_count` globally so `cache_stats` reports a real `hit_rate = hits / (hits + misses)` instead of an unmeasurable proxy.
- `cache_stats` now also returns `db_size_bytes`, `evicted` (eviction counter), and `top_urls` (top 5 by `hit_count`). Existing fields (`total`, `hits`, `last`) preserved.
- New index `idx_last_hit_at` supports faster LRU eviction queries.

**LRU eviction (`WEBCACHE_MAX_SIZE_MB`):**

- New env var. When the SQLite file exceeds the cap, drops ~20% of oldest-by-`last_hit_at` entries (`COALESCE(last_hit_at, cached_at)` for never-hit rows) and runs `VACUUM` to reclaim space. Auto-eviction never wipes the entire cache (clamped to `total - 1`).
- Trigger: debounced every 100 writes, plus an explicit `cache.evictIfNeeded()` API.

**Per-domain TTL (`WEBCACHE_DOMAIN_TTL`):**

- New env var accepting JSON like `{"news.com":1,"reuters.com":1,"arxiv.org":0}`. Days (0 = unlimited). Suffix-matches subdomains (`example.com` matches `api.example.com`). Overrides global `WEBCACHE_TTL_DAYS` per matched domain. Solves the "cache stale on news/market data, infinite on docs" use case without per-fetch HTTP probes.

**Standalone CLI + web dashboard:**

- New `claude-webcache` binary in `bin`. Subcommands: `stats`, `list [N]`, `invalidate <url>`, `clear [--older-than-days N | --confirm YES]`, `dashboard [--port N]`, `help`.
- `claude-webcache dashboard` launches a local HTTP server on `:37778` (configurable). Pure-stdlib HTML page rendering: stats tiles, top URLs by hits, top domains breakdown, search-able recent list, one-click invalidate buttons. Not embedded in the MCP server — the MCP plugin stays stdio-pure.

**Hook visibility (`WEBCACHE_DEBUG`):**

- `WEBCACHE_DEBUG=1` enables stderr logging from `hook-webfetch-cache.cjs` on errors. Default off — silent as before.

**Other:**

- `mcp-server.cjs` now reads version from `plugin.json` at runtime — no more hardcoded version strings drifting from the manifest.
- New `ARCHITECTURE.md` (one-page system map) and `MIGRATION.md` (upgrade notes per release).
- 9 new unit tests covering invalidate, clear (full + age-based), miss tracking, hit_rate accuracy, eviction LRU correctness, domain TTL exact + suffix matching, zero-day means unlimited. 17 tests total, all green.

## 0.2.0 — 2026-05-01

- Add `node:test` unit suite (`plugin/test/cache.test.js`, 8 tests, ~400ms) covering `makeKey` determinism, `set`/`get` round-trip, hit-count update, TTL expiry, upsert, `purgeExpired` Infinity no-op behavior, and `stats` aggregation. Zero new devDeps — uses Node 22.5+ built-in test runner.
- Add `bench/run.js` — single-process latency + storage benchmark (`npm run bench`). Measures p50/p95/p99 for write / read hit / read miss / list operations and bytes-per-entry. Saves JSON results with full machine metadata (CPU, RAM, OS, Node version, commit) for reproducible before/after comparisons.
- Add `bench/README.md` documenting methodology and expected numbers.
- Extend `.github/workflows/test.yml`: real `npm test` job now runs on every push/PR. The existing `npm publish --dry-run` job now depends on tests passing.
- Replace unmeasured "5-15× fewer WebFetch calls" headline in README with measured latency claim from the benchmark suite. Add `Benchmarks` section with the actual numbers and a reproduce command.
- Bump version in `package.json`, `plugin/.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json`.

## 0.1.5 — 2026-04-30

- Auto-cache every WebFetch via a `PostToolUse` hook (`plugin/scripts/hook-webfetch-cache.cjs`). The "before WebFetch, call `cached_fetch` first" pattern in CLAUDE.md becomes optional — caching now happens transparently after each WebFetch returns.
- README updated: usage pattern moved under "optional" for pre-fetch checks.

## 0.1.4 — 2026-04-30

- Default cache TTL changed to **unlimited** (was 7 days). Set `WEBCACHE_TTL_DAYS=N` to opt back into N-day expiry. Rationale: cached docs/arxiv pages rarely become stale within research-sprint horizons; explicit user choice beats silent expiry.

## 0.1.3 — 2026-04-30

- Add `mcpName` field to package.json (`io.github.theYahia/claude-webcache`) — required by the Official MCP Registry (registry.modelcontextprotocol.io) for ownership verification when publishing the corresponding `server.json`. No code changes; metadata-only.

## 0.1.2 — 2026-04-30

- Restructured plugin into `./plugin/` subdir to match the canonical relative-path layout used by Anthropic's claude-plugins-official and thedotmack/claude-mem marketplaces.
- `marketplace.json` plugin source is now `"./plugin"`.
- npm `main` updated to `plugin/src/cache.js`; `files` reduced to `plugin/`, `README.md`, `LICENSE`. Transparent to `require('@theyahia/claude-webcache')` consumers.

> Note on TUI install: at time of release, `/plugin install` in the Claude Code TUI fails for all third-party plugins on Windows due to an upstream Anthropic backend bug ([anthropics/claude-code#41653](https://github.com/anthropics/claude-code/issues/41653)) — independent of source format. CLI subcommands (`claude plugin marketplace add` + `claude plugin install`) bypass this and work; see README.

## 0.1.1 — 2026-04-30

- fix: MCP server path in `.mcp.json` — replace unresolved `${CLAUDE_PLUGIN_ROOT}/scripts/mcp-server.cjs` with relative `./scripts/mcp-server.cjs`. Resolves "Failed to reconnect to claude-webcache" on plugin install.
- Switched `marketplace.json` plugin source to canonical `{"source":"github","repo":"theYahia/claude-webcache"}` object form per Claude Code marketplace docs.

## 0.1.0 — 2026-04-30

- Initial release
- SQLite-backed cross-session WebFetch cache (`~/.webcache/cache.db`, WAL mode, 7-day TTL)
- 4 MCP tools: `cached_fetch`, `cache_store`, `cache_stats`, `cache_list`
- SessionStart hook printing one-line cache stats
- Claude Code plugin format — install via `/plugin install theYahia/claude-webcache`

# Architecture

One-page map of how `claude-webcache` is wired. Lives in ~600 lines of JS across six scripts plus a SQLite file.

## Components

```
┌──────────────────────────────────────────────────────────────────────────┐
│                        Claude Code session                                │
│                                                                           │
│   user prompt ─→ assistant ─→ WebFetch(url, prompt) ─→ live HTTP fetch    │
│                       │                  │                                │
│                       │                  │ PostToolUse hook fires         │
│                       │                  ▼                                │
│                       │          hook-webfetch-cache.cjs                  │
│                       │          (validateUrl → set → log errors)         │
│                       │                  │                                │
│                       ▼                  │                                │
│                 cached_fetch  ───────────┼──→ MCP stdio JSON-RPC          │
│                 cache_*        ─────────┐│                                │
│                 cache_warm     ─────────┐│                                │
│                 cache_refresh  ─────────┐│                                │
│                                         ▼▼                                │
│                                   mcp-server.cjs                          │
│                                   (8 tools registered)                    │
│                                         │                                 │
└─────────────────────────────────────────┼─────────────────────────────────┘
                                          │
                                          ▼
                                   plugin/src/cache.js
                                   (DatabaseSync, WAL, busy_timeout)
                                          │
                                          ▼
                                ~/.webcache/cache.db
                                   (SQLite, 3 tables)
                                ~/.webcache/hook.log
                                   (hook errors, append-only)
```

The dashboard (`scripts/dashboard.cjs`) is launched separately by the user via the `claude-webcache` CLI binary (`scripts/cli.cjs`). It opens its own HTTP server on `:37778` against the same SQLite file. It is **not** loaded inside the MCP server — keeping the MCP plugin stdio-pure.

## Files

| File | Role |
|---|---|
| `plugin/src/cache.js` | Core SQLite layer — `get`/`set`/`stats`/`statsByDomain`/`list`/`invalidate`/`clear`/`evictIfNeeded`/`purgeExpired`/`canonUrl`/`redactUrl`/`validateUrl`/`recordHookError`. Pure logic, no I/O outside SQLite + fs. |
| `plugin/scripts/mcp-server.cjs` | Stdio MCP server. Registers 8 tools, dispatches to `cache.js`. |
| `plugin/scripts/hook-webfetch-cache.cjs` | PostToolUse hook. Reads JSON from stdin, validates URL, calls `cache.set` if `tool_name === 'WebFetch'`. On error: stderr + `~/.webcache/hook.log` append + meta_str record (visible in `cache_stats`). |
| `plugin/scripts/hook-stats.cjs` | SessionStart hook. Prints one-line cache stats greeting (namespace + hit rate + last fetch age). |
| `plugin/scripts/cli.cjs` | `claude-webcache` CLI binary — `stats` (+`--by-domain`), `list`, `invalidate`, `refresh`, `warm`, `clear`, `clear-logs`, `export`, `namespaces`, `dashboard`. Global `--namespace X` flag. |
| `plugin/scripts/dashboard.cjs` | Local HTTP dashboard launched by `cli.cjs dashboard`. Pagination, per-domain stats, refresh+invalidate actions. |
| `plugin/.claude-plugin/plugin.json` | Plugin manifest, source of truth for the version string at runtime. |
| `plugin/hooks/hooks.json` | Hook registration: `SessionStart` + `PostToolUse:WebFetch`. |
| `plugin/.mcp.json` | MCP server registration (relative path: `./scripts/mcp-server.cjs`). |

## Schema

```sql
CREATE TABLE cache (
  key         TEXT PRIMARY KEY,         -- SHA256(namespace + '|' + canonical_url + '|' + prompt)
  url         TEXT NOT NULL,            -- redacted (auth stripped, credential params replaced with ***)
  prompt_hash TEXT NOT NULL,            -- 16-char prefix of SHA256(prompt), kept for debugging
  output      TEXT NOT NULL,            -- plaintext, or base64(gzip(plaintext)) when compressed=1
  cached_at   INTEGER NOT NULL,         -- ms epoch
  hit_count   INTEGER NOT NULL DEFAULT 0,
  last_hit_at INTEGER,                  -- ms epoch, NULL until first hit
  namespace   TEXT NOT NULL DEFAULT '', -- WEBCACHE_NAMESPACE; '' = shared / v0.3 BC
  compressed  INTEGER NOT NULL DEFAULT 0 -- 0 = plaintext, 1 = base64(gzip)
);
CREATE INDEX idx_cached_at             ON cache(cached_at);
CREATE INDEX idx_url                   ON cache(url);
CREATE INDEX idx_last_hit_at           ON cache(last_hit_at);
CREATE INDEX idx_namespace             ON cache(namespace);
CREATE INDEX idx_namespace_cached_at   ON cache(namespace, cached_at DESC);  -- enables index-only list queries

CREATE TABLE meta (
  key   TEXT PRIMARY KEY,               -- 'miss_count', 'evict_count', 'oversize_skipped', 'last_hook_error_at'
  value INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE meta_str (
  key   TEXT PRIMARY KEY,               -- 'last_oversize_url', 'last_hook_error_msg'
  value TEXT NOT NULL
);
```

PRAGMAs at open: `journal_mode = WAL`, `synchronous = NORMAL`, `busy_timeout = 5000`. WAL + 5s busy timeout supports concurrent multi-session access without `SQLITE_BUSY` errors during normal operation.

**Schema migration** is idempotent: existing v0.3 DBs (no `namespace`/`compressed` columns) are migrated via `PRAGMA table_info` checks + conditional `ALTER TABLE ADD COLUMN` on first open under v0.4. No manual steps. See `MIGRATION.md`.

## Data flow

**Write (auto-cache):**
1. Claude calls `WebFetch(url, prompt)`.
2. Claude Code runtime returns the response and fires PostToolUse hooks.
3. `hook-webfetch-cache.cjs` reads `{ tool_name, tool_input, tool_response }` from stdin.
4. If `tool_name === 'WebFetch'`, validate URL scheme (http/https), check payload size, extract URL/prompt/output.
5. `cache.set()` writes the entry: URL canonicalized + redacted, gzip if `WEBCACHE_COMPRESS=1` and ≥4KB, namespace from env. Every 100 writes calls `evictIfNeeded()` if `WEBCACHE_MAX_SIZE_MB` is set.
6. Errors logged to stderr (unless `WEBCACHE_QUIET=1`) + appended to `~/.webcache/hook.log` + recorded as `last_hook_error_msg` in meta_str (surfaces in `cache_stats`).

**Read (explicit pre-fetch check):**
1. Claude calls `cached_fetch(url, prompt)` MCP tool.
2. `mcp-server.cjs` calls `cache.get(url, prompt)`.
3. `cache.get()` looks up the SHA256 key, checks effective TTL (per-domain override > global), increments `hit_count`/`last_hit_at` on hit, increments `miss_count` in `meta` on miss. Decompresses output if `compressed=1`.
4. Returns cached output, or `[CACHE_MISS] <url>` for the assistant to handle (it then calls real WebFetch, which fires the auto-cache hook).

**Bulk warm (pre-flight):**
1. Pipeline collects 500 URL+prompt pairs.
2. One call to `cache_warm({ entries: [...] })` → returns `{ hits, misses, invalid }` in a single MCP round-trip.
3. Pipeline WebFetches only `misses`; reuses cached `hits` directly.

**Force refresh:**
1. Claude calls `cache_refresh(url, prompt)` → invalidates the entry + returns `[CACHE_MISS]`.
2. Claude triggers WebFetch → hook re-caches.

**Eviction (size cap):**
1. Triggered by `cache.set()` every 100 writes (debounced) or by manual `cache.evictIfNeeded()` call.
2. If `fs.statSync(DB_PATH).size > MAX_SIZE_BYTES`, deletes oldest-by-`last_hit_at` rows (`COALESCE(last_hit_at, cached_at)` for never-hit rows).
3. Drop count: `max(1, min(total - 1, ceil(total * 0.20)))` — never wipes the entire cache via auto-eviction.
4. Runs `VACUUM` after to actually shrink the file on disk.
5. Eviction is global across namespaces — fairness via age, not isolation.

## Configuration

All knobs are env vars, read once at `cache.js` module load. See README for the full table. Key non-obvious ones:

- **`WEBCACHE_NAMESPACE`** — isolates cache per project. Default `""` (shared, BC with v0.3).
- **`WEBCACHE_STRICT_REDACT`** — strict mode includes redacted URL in the hash key, so endpoints differing only in credentials collide. Trade-off documented in README.
- **`WEBCACHE_DOMAIN_TTL`** — per-domain override JSON. Resolution order on `cache.get()`: exact host match → suffix match (`*.example.com` matches `api.example.com`) → fallback to global `WEBCACHE_TTL_DAYS`.
- **`WEBCACHE_MAX_SIZE_MB`** — soft cap. Eviction is debounced (every 100 writes) so the file may briefly exceed the cap between checks.

## Testing

Three test files, ~53 tests total, ~7s runtime:

- `plugin/test/cache.test.js` — 38 unit tests against the cache module directly. Uses `freshCache()` helper which monkey-patches `os.homedir()` + env vars to give each test an isolated DB. Covers: canonicalization, validation, redaction, payload cap, namespace isolation, gzip round-trip, busy_timeout, statsByDomain, pagination, BC.
- `plugin/test/integration.test.js` — 11 tests spawning the MCP server as a child process, communicating via stdio JSON-RPC. Verifies all 8 tools round-trip correctly through the MCP protocol (initialize → tools/list → tools/call).
- `plugin/test/concurrent.test.js` — 4 stress tests using `child_process.spawn` to run N (5-10) parallel Node workers writing/reading the same DB. Validates `busy_timeout` handles real cross-process contention, schema migration is idempotent under race, eviction + writers coexist.

Performance regression detection: `bench/run.js` produces JSON results with full machine metadata. Compare against baselines in `bench/baselines/`. The v0.4.0 baseline (`2026-05-14-v0.4.0.json`) is the new reference.

## Non-goals (explicit)

- **Not a content-aware cache.** Doesn't parse HTML/JSON, doesn't dedupe across paraphrased prompts. Cache key is `(namespace, canonical_url, prompt)`.
- **Not HTTP-spec-aware.** Doesn't read `Cache-Control`/`ETag`/`Last-Modified` from responses (the WebFetch hook payload doesn't expose them). Use `WEBCACHE_DOMAIN_TTL` to express "this domain is volatile" intent.
- **Not multi-machine.** Single SQLite file in `~/.webcache/`. Multi-machine team caches via Redis/Postgres are deferred to a future major version.
- **Not vary-by-header.** Same upstream limitation as Cache-Control. Prompts are the only differentiator.
- **Not per-domain hit rate.** Per-domain miss tracking would require a separate counter table; current global `miss_count` only supports system-wide hit rate. Dashboard exposes `avg_hits_per_entry` per domain as a proxy.
- **Not encrypted at rest.** Use OS-level disk encryption (FileVault, BitLocker, LUKS) if the cache contains sensitive content. URL credential redaction is display-level only by default.

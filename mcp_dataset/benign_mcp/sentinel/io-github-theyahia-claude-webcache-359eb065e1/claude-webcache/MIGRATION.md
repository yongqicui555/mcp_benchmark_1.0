# Migration guide

Every release ships an automatic schema migration on first DB open — no manual steps unless flagged below. `cache.js` uses `CREATE TABLE IF NOT EXISTS`, `CREATE INDEX IF NOT EXISTS`, and `PRAGMA table_info`-guarded `ALTER TABLE ADD COLUMN` for forward compatibility.

## v0.3.x → v0.4.0

**Adds:**

- Two new columns on `cache`: `namespace TEXT NOT NULL DEFAULT ''` and `compressed INTEGER NOT NULL DEFAULT 0`. Added via `PRAGMA table_info(cache)` check + `ALTER TABLE ADD COLUMN` on first open under v0.4 (SQLite doesn't support `IF NOT EXISTS` on `ADD COLUMN`).
- New table `meta_str(key TEXT PRIMARY KEY, value TEXT NOT NULL)` for string-valued metadata (`last_hook_error_msg`, `last_oversize_url`).
- New index `idx_namespace ON cache(namespace)` and composite `idx_namespace_cached_at ON cache(namespace, cached_at DESC)` — the composite index lets `cache_list` walk the index in DESC order without sort, restoring v0.3 list performance under the new namespace WHERE clause.
- PRAGMA `busy_timeout = 5000` at open — concurrent multi-session writes no longer hit `SQLITE_BUSY` during normal operation.
- Two new MCP tools: `cache_warm` (batch pre-flight), `cache_refresh` (forced re-fetch). Total tools: 8.
- New env vars: `WEBCACHE_NAMESPACE`, `WEBCACHE_MAX_OUTPUT_MB`, `WEBCACHE_COMPRESS`, `WEBCACHE_STRICT_REDACT`, `WEBCACHE_QUIET`.

**Action required:** none. Existing `~/.webcache/cache.db` keeps working — migration runs automatically on first open under v0.4.

**Behavior changes:**

- **URL canonicalization (key shape change).** v0.4 normalizes URLs before hashing: lowercase hostname, strip default ports `:80`/`:443`, strip URL fragment, sort query parameters alphabetically. Existing v0.3 rows (hashed under the old key shape) become unreachable by lookup — the next `WebFetch` on each URL is a miss, then steady-state caching resumes. Old rows remain in the DB taking space until LRU eviction sweeps them, or until you run `claude-webcache clear --confirm YES` to wipe.
- **URL redaction on store.** v0.4 strips `user:pass@` and credential-like query params (`token`, `api_key`, etc.) from the stored URL column before write. The hash key still uses the unredacted canonical URL by default, so re-fetching the same authenticated URL hits the cache. Opt into hash-level redaction with `WEBCACHE_STRICT_REDACT=1` — see README Security section.
- **Scheme validation.** WebFetch results on `data:`, `file:`, `javascript:`, `ftp:` URLs are rejected — only `http:`/`https:` are cached.
- **Payload cap.** Outputs exceeding `WEBCACHE_MAX_OUTPUT_MB` (default 10) are rejected instead of bloating the DB. Counter `oversize_skipped` and `last_oversize_url` are tracked in stats.
- **Hook error visibility.** v0.4 logs hook errors to stderr by default (was opt-in via `WEBCACHE_DEBUG=1` in v0.3). Use `WEBCACHE_QUIET=1` to restore silence. Errors also append to `~/.webcache/hook.log` and are recorded in `cache_stats.last_hook_error_at` / `.last_hook_error_msg`.
- **Default namespace `""`.** All v0.3 entries are treated as namespace `""`. If you don't set `WEBCACHE_NAMESPACE`, behavior is identical to v0.3 (single shared namespace).
- **`cache_stats` shape grew.** New fields: `namespace`, `oversize_skipped`, `last_oversize_url`, `last_hook_error_at`, `last_hook_error_msg`, `hook_log_path`, `compressed_rows`, `db_size_uncompressed_est`. All v0.3 fields preserved. Keyed access only (you should already).

**Downgrade path:** Older versions ignore the new columns and tables — `cache_list` still works, but namespace isolation is lost and you'll see the canonicalization-key-shape miss on first read of each URL when you re-upgrade. To clean up legacy rows (old key shape) after upgrade, run `claude-webcache clear --confirm YES` to wipe and start fresh.

## v0.2.x → v0.3.0

Adds:

- New `meta` table for global counters (`miss_count`, `evict_count`). Auto-created on first open.
- New index `idx_last_hit_at` on `cache.last_hit_at` to speed LRU eviction queries.

**Action required:** none. Existing `~/.webcache/cache.db` keeps working; the new table/index appear automatically on first read or write under v0.3.0.

**Behavior changes:**

- `cache_stats` MCP tool now returns a richer object: adds `misses`, `hit_rate`, `db_size_bytes`, `evicted`, `top_urls` to the previous `{ total, hits, last }` shape. Existing fields are preserved. If you parse the response, switch to keyed access (you should already).
- New tools `cache_invalidate` and `cache_clear` are registered. Existing 4 tools unchanged.
- `WEBCACHE_DOMAIN_TTL` and `WEBCACHE_MAX_SIZE_MB` env vars are honored; both default to "off" so behavior is identical for unconfigured users.
- `hook-webfetch-cache.cjs` now logs to stderr on errors when `WEBCACHE_DEBUG=1`. Default off — silent as before.

**Downgrade path:** older versions ignore the new `meta` table. Hit/miss counters reset back to 0 if you actually downgrade and re-upgrade, but cached entries in `cache` table survive.

## v0.1.x → v0.2.0

Adds: `node:test` unit suite, `bench/run.js` benchmark harness. No schema changes, no behavior changes for end users — pure tooling/release-quality work.

## v0.1.4 → v0.1.5

Adds: PostToolUse hook auto-caches every WebFetch. The "call `cached_fetch` first" usage pattern in CLAUDE.md becomes optional.

**Action:** none. The pattern still works for explicit pre-fetch checks.

## v0.1.3 → v0.1.4

Default global TTL changed from 7 days to **unlimited**. To restore the old behavior:

```bash
export WEBCACHE_TTL_DAYS=7
```

## Pre-v0.1.3

The plugin layout was restructured into `./plugin/` subdir for marketplace compatibility. If you cloned the repo before this release, re-clone or `git pull` and reinstall.

'use strict';
const { DatabaseSync } = require('node:sqlite');
const crypto = require('node:crypto');
const zlib = require('node:zlib');
const fs = require('node:fs');
const path = require('node:path');
const os = require('node:os');

const CACHE_DIR = path.join(os.homedir(), '.webcache');
const DB_PATH = path.join(CACHE_DIR, 'cache.db');
const HOOK_LOG_PATH = path.join(CACHE_DIR, 'hook.log');

const _ttlRaw = process.env.WEBCACHE_TTL_DAYS;
const TTL_MS = (!_ttlRaw || _ttlRaw === '0')
  ? Infinity
  : Number(_ttlRaw) * 24 * 60 * 60 * 1000;

const _maxSizeRaw = process.env.WEBCACHE_MAX_SIZE_MB;
const MAX_SIZE_BYTES = (!_maxSizeRaw || _maxSizeRaw === '0')
  ? Infinity
  : Number(_maxSizeRaw) * 1024 * 1024;

const _maxOutRaw = process.env.WEBCACHE_MAX_OUTPUT_MB;
const MAX_OUTPUT_BYTES = (!_maxOutRaw || _maxOutRaw === '0')
  ? 10 * 1024 * 1024
  : Number(_maxOutRaw) * 1024 * 1024;

const NAMESPACE = process.env.WEBCACHE_NAMESPACE || '';
const COMPRESS = process.env.WEBCACHE_COMPRESS === '1';
const STRICT_REDACT = process.env.WEBCACHE_STRICT_REDACT === '1';
const COMPRESS_MIN_BYTES = 4096;

const DOMAIN_TTL_MS = parseDomainTtl(process.env.WEBCACHE_DOMAIN_TTL);

// WebSearch results live in the 'websearch' namespace under a synthetic URL
// (https://websearch.local/?q=...) so they reuse the entire set/get machinery —
// compression, oversize cap, eviction, hit counting, expiry-on-read. They go stale
// faster than page fetches (search rankings drift), so they get a dedicated short TTL.
const SEARCH_NAMESPACE = 'websearch';
const SEARCH_HOST = 'websearch.local';
const _searchTtlRaw = process.env.WEBCACHE_SEARCH_TTL_HOURS;
const SEARCH_TTL_MS = (_searchTtlRaw === '0')
  ? Infinity
  : (Number(_searchTtlRaw) > 0 ? Number(_searchTtlRaw) : 6) * 60 * 60 * 1000;

const CREDENTIAL_PARAM_NAMES = new Set([
  'token', 'api_key', 'apikey', 'access_token', 'auth', 'secret',
  'password', 'passwd', 'key', 'signature', 'sig', 'sessionid',
]);

const EVICT_CHECK_EVERY = 100;
let _writeCount = 0;
let db = null;

function parseDomainTtl(raw) {
  if (!raw) return {};
  try {
    const parsed = JSON.parse(raw);
    const out = {};
    for (const [domain, days] of Object.entries(parsed)) {
      const n = Number(days);
      out[String(domain).toLowerCase()] = (n === 0) ? Infinity : n * 24 * 60 * 60 * 1000;
    }
    return out;
  } catch {
    return {};
  }
}

function getEffectiveTtl(url) {
  let host;
  try { host = new URL(url).hostname.toLowerCase(); } catch { return TTL_MS; }
  if (host === SEARCH_HOST) return SEARCH_TTL_MS;
  if (!Object.keys(DOMAIN_TTL_MS).length) return TTL_MS;
  for (const [domain, ttl] of Object.entries(DOMAIN_TTL_MS)) {
    if (host === domain || host.endsWith('.' + domain)) return ttl;
  }
  return TTL_MS;
}

function canonUrl(raw) {
  const s = (raw || '').trim();
  if (!s) return '';
  let u;
  try { u = new URL(s); } catch { return s; }
  // Lowercase host
  u.hostname = u.hostname.toLowerCase();
  // Strip default ports
  if ((u.protocol === 'http:' && u.port === '80') ||
      (u.protocol === 'https:' && u.port === '443')) {
    u.port = '';
  }
  // Strip fragment
  u.hash = '';
  // Sort query params (stable order across permutations)
  if (u.search) {
    const params = Array.from(u.searchParams.entries());
    params.sort((a, b) => (a[0] === b[0] ? 0 : a[0] < b[0] ? -1 : 1));
    u.search = '';
    for (const [k, v] of params) u.searchParams.append(k, v);
  }
  return u.toString();
}

function validateUrl(raw) {
  const s = (raw || '').trim();
  if (!s) return { ok: false, reason: 'empty url' };
  let u;
  try { u = new URL(s); } catch { return { ok: false, reason: 'malformed url' }; }
  if (u.protocol !== 'http:' && u.protocol !== 'https:') {
    return { ok: false, reason: `unsupported scheme: ${u.protocol}` };
  }
  return { ok: true };
}

function redactUrl(raw) {
  const s = (raw || '').trim();
  if (!s) return s;
  let u;
  try { u = new URL(s); } catch { return s; }
  if (u.username) u.username = '';
  if (u.password) u.password = '';
  if (u.search) {
    for (const k of Array.from(u.searchParams.keys())) {
      if (CREDENTIAL_PARAM_NAMES.has(k.toLowerCase())) {
        u.searchParams.set(k, '***');
      }
    }
  }
  return u.toString();
}

function tableHasColumn(d, table, col) {
  const rows = d.prepare(`PRAGMA table_info(${table})`).all();
  for (const r of rows) if (r.name === col) return true;
  return false;
}

function _initPragmas(handle) {
  // busy_timeout MUST be first — once set, subsequent PRAGMAs/DDL contending with another
  // opener will wait up to 5s instead of failing immediately with "disk I/O error" / SQLITE_BUSY.
  // The journal_mode=WAL switch in particular can fail on a fresh DB when two processes
  // race to enable WAL before either has busy_timeout active.
  handle.exec('PRAGMA busy_timeout = 5000');
  // Retry the WAL switch — first opener wins, second sees the journal in transition.
  // 5 attempts × 50ms = 250ms total worst case.
  let lastErr;
  for (let i = 0; i < 5; i++) {
    try { handle.exec('PRAGMA journal_mode = WAL'); lastErr = null; break; }
    catch (e) {
      lastErr = e;
      const wait = 50 * (i + 1);
      const t = Date.now(); while (Date.now() - t < wait) { /* sync sleep */ }
    }
  }
  if (lastErr) throw lastErr;
  handle.exec('PRAGMA synchronous = NORMAL');
}

function getDb() {
  if (db) return db;
  if (!fs.existsSync(CACHE_DIR)) {
    fs.mkdirSync(CACHE_DIR, { recursive: true });
  }
  db = new DatabaseSync(DB_PATH);
  _initPragmas(db);
  db.exec(`
    CREATE TABLE IF NOT EXISTS cache (
      key TEXT PRIMARY KEY,
      url TEXT NOT NULL,
      prompt_hash TEXT NOT NULL,
      output TEXT NOT NULL,
      cached_at INTEGER NOT NULL,
      hit_count INTEGER NOT NULL DEFAULT 0,
      last_hit_at INTEGER
    );
    CREATE INDEX IF NOT EXISTS idx_cached_at ON cache(cached_at);
    CREATE INDEX IF NOT EXISTS idx_url ON cache(url);
    CREATE INDEX IF NOT EXISTS idx_last_hit_at ON cache(last_hit_at);

    CREATE TABLE IF NOT EXISTS meta (
      key TEXT PRIMARY KEY,
      value INTEGER NOT NULL DEFAULT 0
    );

    CREATE TABLE IF NOT EXISTS meta_str (
      key TEXT PRIMARY KEY,
      value TEXT NOT NULL
    );
  `);

  // v0.4 schema migration: namespace + compressed columns. Idempotent two ways —
  // (a) PRAGMA check covers the single-process case, (b) try/catch on "duplicate column"
  // covers the cross-process race where two openers both see the column missing and
  // both try to ALTER. SQLite's error message includes "duplicate column" — we swallow
  // exactly that error and re-throw anything else.
  function safeAddColumn(col, ddl) {
    if (tableHasColumn(db, 'cache', col)) return;
    try { db.exec(ddl); }
    catch (e) {
      if (e && /duplicate column/i.test(String(e.message))) return; // race winner already added it
      throw e;
    }
  }
  safeAddColumn('namespace', "ALTER TABLE cache ADD COLUMN namespace TEXT NOT NULL DEFAULT ''");
  safeAddColumn('compressed', 'ALTER TABLE cache ADD COLUMN compressed INTEGER NOT NULL DEFAULT 0');
  db.exec('CREATE INDEX IF NOT EXISTS idx_namespace ON cache(namespace)');
  // Composite index lets `SELECT ... WHERE namespace=? ORDER BY cached_at DESC LIMIT N`
  // walk the index directly without sort. Critical for list() perf on large caches.
  db.exec('CREATE INDEX IF NOT EXISTS idx_namespace_cached_at ON cache(namespace, cached_at DESC)');

  db.prepare("INSERT OR IGNORE INTO meta (key, value) VALUES ('miss_count', 0)").run();
  db.prepare("INSERT OR IGNORE INTO meta (key, value) VALUES ('evict_count', 0)").run();
  db.prepare("INSERT OR IGNORE INTO meta (key, value) VALUES ('oversize_skipped', 0)").run();
  db.prepare("INSERT OR IGNORE INTO meta (key, value) VALUES ('last_hook_error_at', 0)").run();
  return db;
}

function makeKey(url, prompt) {
  const canon = canonUrl(url);
  const keyUrl = STRICT_REDACT ? redactUrl(canon) : canon;
  const norm = NAMESPACE + '|' + keyUrl + '|' + (prompt || '').trim();
  return crypto.createHash('sha256').update(norm).digest('hex');
}

function _ns(opts) {
  if (opts && typeof opts.namespace === 'string') return opts.namespace;
  return NAMESPACE;
}

function _decodeOutput(row) {
  if (!row) return null;
  if (!row.compressed) return row.output;
  try {
    const buf = Buffer.from(row.output, 'base64');
    return zlib.gunzipSync(buf).toString('utf8');
  } catch (e) {
    return null;
  }
}

function get(url, prompt, opts) {
  const d = getDb();
  const ns = _ns(opts);
  const key = makeKey(url, prompt);
  const row = d.prepare(
    'SELECT output, cached_at, compressed FROM cache WHERE key = ? AND namespace = ?'
  ).get(key, ns);
  if (!row) {
    d.prepare("UPDATE meta SET value = value + 1 WHERE key = 'miss_count'").run();
    return null;
  }
  const ttl = getEffectiveTtl(url);
  if (Date.now() - Number(row.cached_at) > ttl) {
    d.prepare('DELETE FROM cache WHERE key = ? AND namespace = ?').run(key, ns);
    d.prepare("UPDATE meta SET value = value + 1 WHERE key = 'miss_count'").run();
    return null;
  }
  d.prepare('UPDATE cache SET hit_count = hit_count + 1, last_hit_at = ? WHERE key = ? AND namespace = ?')
    .run(Date.now(), key, ns);
  return _decodeOutput(row);
}

function set(url, prompt, output, opts) {
  const v = validateUrl(url);
  if (!v.ok) return { ok: false, reason: v.reason };

  const d = getDb();
  const ns = _ns(opts);
  const out = String(output == null ? '' : output);
  const byteLen = Buffer.byteLength(out, 'utf8');
  if (byteLen > MAX_OUTPUT_BYTES) {
    d.prepare("UPDATE meta SET value = value + 1 WHERE key = 'oversize_skipped'").run();
    d.prepare("INSERT INTO meta_str (key, value) VALUES ('last_oversize_url', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value")
      .run(redactUrl(url));
    return { ok: false, reason: `payload ${byteLen} bytes exceeds cap ${MAX_OUTPUT_BYTES}` };
  }

  const key = makeKey(url, prompt);
  const promptHash = crypto.createHash('sha256').update(prompt || '').digest('hex').slice(0, 16);
  const storedUrl = redactUrl(canonUrl(url));

  let storedOutput = out;
  let compressed = 0;
  if (COMPRESS && byteLen >= COMPRESS_MIN_BYTES) {
    try {
      storedOutput = zlib.gzipSync(out).toString('base64');
      compressed = 1;
    } catch {
      storedOutput = out;
      compressed = 0;
    }
  }

  d.prepare(`
    INSERT INTO cache (key, url, prompt_hash, output, cached_at, hit_count, namespace, compressed)
    VALUES (?, ?, ?, ?, ?, 0, ?, ?)
    ON CONFLICT(key) DO UPDATE SET
      output = excluded.output,
      cached_at = excluded.cached_at,
      compressed = excluded.compressed
  `).run(key, storedUrl, promptHash, storedOutput, Date.now(), ns, compressed);

  _writeCount++;
  if (_writeCount % EVICT_CHECK_EVERY === 0) {
    try { evictIfNeeded(); } catch { /* never crash on eviction */ }
  }
  return { ok: true };
}

function invalidate(url, opts) {
  const d = getDb();
  const ns = _ns(opts);
  const canon = redactUrl(canonUrl(url));
  // Match both raw url (legacy v0.3 rows) and canonical/redacted form (v0.4 rows)
  return d.prepare('DELETE FROM cache WHERE namespace = ? AND (url = ? OR url = ?)')
    .run(ns, url, canon).changes;
}

function clear(olderThanDays, opts) {
  const d = getDb();
  const ns = _ns(opts);
  if (olderThanDays && olderThanDays > 0) {
    const cutoff = Date.now() - olderThanDays * 24 * 60 * 60 * 1000;
    return d.prepare('DELETE FROM cache WHERE namespace = ? AND cached_at < ?')
      .run(ns, cutoff).changes;
  }
  return d.prepare('DELETE FROM cache WHERE namespace = ?').run(ns).changes;
}

function evictIfNeeded() {
  if (MAX_SIZE_BYTES === Infinity) return 0;
  if (!fs.existsSync(DB_PATH)) return 0;
  const size = fs.statSync(DB_PATH).size;
  if (size <= MAX_SIZE_BYTES) return 0;
  const d = getDb();
  const total = Number(d.prepare('SELECT COUNT(*) AS n FROM cache').get().n);
  if (total === 0) return 0;
  // Drop ~20% of rows, oldest by last access. Floor at 1 (always make progress),
  // ceiling at total-1 (never wipe the whole cache via auto-eviction).
  // Eviction is global across namespaces — fairness via age, not isolation.
  const evictCount = Math.max(1, Math.min(total - 1, Math.ceil(total * 0.20)));
  const changes = d.prepare(`
    DELETE FROM cache WHERE key IN (
      SELECT key FROM cache
      ORDER BY COALESCE(last_hit_at, cached_at) ASC
      LIMIT ?
    )
  `).run(evictCount).changes;
  d.prepare("UPDATE meta SET value = value + ? WHERE key = 'evict_count'").run(changes);
  d.exec('VACUUM');
  return changes;
}

function _metaStr(d, key) {
  const r = d.prepare('SELECT value FROM meta_str WHERE key = ?').get(key);
  return r ? r.value : null;
}

function stats(opts) {
  const d = getDb();
  const ns = _ns(opts);
  const scopeAll = opts && opts.global === true;

  const totalQ = scopeAll
    ? d.prepare('SELECT COUNT(*) AS n FROM cache').get()
    : d.prepare('SELECT COUNT(*) AS n FROM cache WHERE namespace = ?').get(ns);
  const total = Number(totalQ.n);

  const hitsQ = scopeAll
    ? d.prepare('SELECT COALESCE(SUM(hit_count), 0) AS n FROM cache').get()
    : d.prepare('SELECT COALESCE(SUM(hit_count), 0) AS n FROM cache WHERE namespace = ?').get(ns);
  const hits = Number(hitsQ.n);

  const lastQ = scopeAll
    ? d.prepare('SELECT MAX(cached_at) AS t FROM cache').get()
    : d.prepare('SELECT MAX(cached_at) AS t FROM cache WHERE namespace = ?').get(ns);
  const last = lastQ.t == null ? null : Number(lastQ.t);

  const missesRow = d.prepare("SELECT value FROM meta WHERE key = 'miss_count'").get();
  const misses = missesRow ? Number(missesRow.value) : 0;
  const evictedRow = d.prepare("SELECT value FROM meta WHERE key = 'evict_count'").get();
  const evicted = evictedRow ? Number(evictedRow.value) : 0;
  const oversizeRow = d.prepare("SELECT value FROM meta WHERE key = 'oversize_skipped'").get();
  const oversize = oversizeRow ? Number(oversizeRow.value) : 0;
  const lastHookErrRow = d.prepare("SELECT value FROM meta WHERE key = 'last_hook_error_at'").get();
  const lastHookErrAt = lastHookErrRow && Number(lastHookErrRow.value) > 0 ? Number(lastHookErrRow.value) : null;

  const denom = hits + misses;
  const hit_rate = denom > 0 ? hits / denom : 0;
  const dbSize = fs.existsSync(DB_PATH) ? fs.statSync(DB_PATH).size : 0;

  const topRows = scopeAll
    ? d.prepare('SELECT url, hit_count FROM cache WHERE hit_count > 0 ORDER BY hit_count DESC LIMIT 5').all()
    : d.prepare('SELECT url, hit_count FROM cache WHERE namespace = ? AND hit_count > 0 ORDER BY hit_count DESC LIMIT 5').all(ns);

  let compressedRows = 0;
  let uncompressedEstBytes = 0;
  if (COMPRESS) {
    const cRow = scopeAll
      ? d.prepare('SELECT COUNT(*) AS n FROM cache WHERE compressed = 1').get()
      : d.prepare('SELECT COUNT(*) AS n FROM cache WHERE namespace = ? AND compressed = 1').get(ns);
    compressedRows = Number(cRow.n);
    // estimate uncompressed: gzip typical ratio ~4×; rough upper bound for dashboard display
    const sumQ = scopeAll
      ? d.prepare('SELECT COALESCE(SUM(LENGTH(output)), 0) AS n FROM cache WHERE compressed = 1').get()
      : d.prepare('SELECT COALESCE(SUM(LENGTH(output)), 0) AS n FROM cache WHERE namespace = ? AND compressed = 1').get(ns);
    uncompressedEstBytes = Number(sumQ.n) * 4;
  }

  return {
    namespace: ns,
    total,
    hits,
    misses,
    hit_rate: Number(hit_rate.toFixed(4)),
    last,
    db_size_bytes: dbSize,
    db_size_uncompressed_est: COMPRESS ? dbSize + uncompressedEstBytes : null,
    compressed_rows: COMPRESS ? compressedRows : null,
    evicted,
    oversize_skipped: oversize,
    last_oversize_url: _metaStr(d, 'last_oversize_url'),
    last_hook_error_at: lastHookErrAt,
    last_hook_error_msg: _metaStr(d, 'last_hook_error_msg'),
    hook_log_path: HOOK_LOG_PATH,
    top_urls: topRows.map((r) => ({ url: r.url, hit_count: Number(r.hit_count) })),
  };
}

function statsByDomain(limit = 20, opts) {
  const d = getDb();
  const ns = _ns(opts);
  const scopeAll = opts && opts.global === true;
  const rows = scopeAll
    ? d.prepare(`
        SELECT url, hit_count, cached_at, last_hit_at FROM cache
      `).all()
    : d.prepare(`
        SELECT url, hit_count, cached_at, last_hit_at FROM cache WHERE namespace = ?
      `).all(ns);

  const agg = {};
  for (const r of rows) {
    let host;
    try { host = new URL(r.url).hostname.toLowerCase(); } catch { host = '—'; }
    if (!agg[host]) agg[host] = { entries: 0, hits: 0, last_fetched_at: 0 };
    agg[host].entries++;
    agg[host].hits += Number(r.hit_count);
    const cached = Number(r.cached_at);
    if (cached > agg[host].last_fetched_at) agg[host].last_fetched_at = cached;
  }
  return Object.entries(agg)
    .map(([domain, v]) => ({
      domain,
      entries: v.entries,
      total_hits: v.hits,
      avg_hits_per_entry: v.entries > 0 ? Number((v.hits / v.entries).toFixed(2)) : 0,
      last_fetched_at: v.last_fetched_at || null,
    }))
    .sort((a, b) => b.entries - a.entries || b.total_hits - a.total_hits)
    .slice(0, limit);
}

function list(limit = 50, offset = 0, opts) {
  const d = getDb();
  const ns = _ns(opts);
  const scopeAll = opts && opts.global === true;
  const rows = scopeAll
    ? d.prepare(`
        SELECT url, cached_at, hit_count, last_hit_at, namespace, compressed
        FROM cache
        ORDER BY cached_at DESC
        LIMIT ? OFFSET ?
      `).all(limit, offset)
    : d.prepare(`
        SELECT url, cached_at, hit_count, last_hit_at, namespace, compressed
        FROM cache
        WHERE namespace = ?
        ORDER BY cached_at DESC
        LIMIT ? OFFSET ?
      `).all(ns, limit, offset);
  return rows.map((r) => ({
    url: r.url,
    cached_at: Number(r.cached_at),
    hit_count: Number(r.hit_count),
    last_hit_at: r.last_hit_at == null ? null : Number(r.last_hit_at),
    namespace: r.namespace || '',
    compressed: r.compressed ? 1 : 0,
  }));
}

function listNamespaces() {
  const d = getDb();
  const rows = d.prepare('SELECT DISTINCT namespace FROM cache ORDER BY namespace').all();
  return rows.map((r) => r.namespace || '');
}

function purgeExpired() {
  const d = getDb();
  if (TTL_MS === Infinity) return 0;
  const cutoff = Date.now() - TTL_MS;
  return d.prepare('DELETE FROM cache WHERE cached_at < ?').run(cutoff).changes;
}

function recordHookError(msg) {
  try {
    const d = getDb();
    d.prepare("UPDATE meta SET value = ? WHERE key = 'last_hook_error_at'").run(Date.now());
    d.prepare("INSERT INTO meta_str (key, value) VALUES ('last_hook_error_msg', ?) ON CONFLICT(key) DO UPDATE SET value = excluded.value")
      .run(String(msg).slice(0, 500));
  } catch { /* swallow — DB itself may be the source of error */ }
}

// --- WebSearch caching --------------------------------------------------
// Search queries have no URL, so we map a query to a synthetic https URL and
// store under the 'websearch' namespace. set()/get() handle everything else.
function searchUrl(query) {
  return `https://${SEARCH_HOST}/?q=` + encodeURIComponent(String(query == null ? '' : query).trim());
}

function setSearch(query, results, opts) {
  const q = String(query == null ? '' : query).trim();
  if (!q) return { ok: false, reason: 'empty query' };
  return set(searchUrl(q), '', results, Object.assign({}, opts, { namespace: SEARCH_NAMESPACE }));
}

function getSearch(query, opts) {
  const q = String(query == null ? '' : query).trim();
  if (!q) return null;
  return get(searchUrl(q), '', Object.assign({}, opts, { namespace: SEARCH_NAMESPACE }));
}

module.exports = {
  get, set, stats, statsByDomain, list, listNamespaces,
  invalidate, clear,
  purgeExpired, evictIfNeeded,
  makeKey, canonUrl, redactUrl, validateUrl, getEffectiveTtl,
  searchUrl, setSearch, getSearch,
  recordHookError,
  DB_PATH, CACHE_DIR, HOOK_LOG_PATH,
  NAMESPACE, MAX_OUTPUT_BYTES, COMPRESS, STRICT_REDACT,
  SEARCH_NAMESPACE, SEARCH_HOST, SEARCH_TTL_MS,
};

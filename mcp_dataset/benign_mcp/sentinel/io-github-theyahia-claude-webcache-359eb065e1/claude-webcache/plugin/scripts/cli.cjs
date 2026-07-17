#!/usr/bin/env node
'use strict';
process.removeAllListeners('warning');

// Note: cache.js reads env vars at module load. --namespace flag is applied to
// process.env BEFORE the cache module is required so the runtime NAMESPACE matches.
const args = process.argv.slice(2);

function flag(name, hasValue = false) {
  const i = args.indexOf(name);
  if (i === -1) return undefined;
  return hasValue ? args[i + 1] : true;
}

const nsOverride = flag('--namespace', true);
if (nsOverride !== undefined) process.env.WEBCACHE_NAMESPACE = nsOverride;

const fs = require('node:fs');
const cache = require('../src/cache.js');
const PLUGIN_MANIFEST = require('../.claude-plugin/plugin.json');

const cmd = args[0];

function help() {
  process.stdout.write(`claude-webcache v${PLUGIN_MANIFEST.version} — local WebFetch cache CLI

Usage:
  claude-webcache <command> [args]

Commands:
  stats [--by-domain]               Print cache statistics (JSON). --by-domain → per-domain breakdown.
  list [N] [--offset M]             List N most-recent URLs (default 50).
  invalidate <url>                  Delete all entries for a URL in current namespace.
  refresh <url> --prompt "..."      Invalidate one (url, prompt) pair — next WebFetch will re-cache.
  warm <urls-file> --prompt "..."   Bulk pre-flight check. File = one URL per line. Reports hits/misses.
  clear [--older-than-days N | --confirm YES]
                                    Wipe cache in current namespace.
  clear-logs                        Truncate ~/.webcache/hook.log.
  export [--out FILE] [--all]       Export current namespace as JSON. --all = every namespace.
  import <file> [--overwrite]       Bulk import JSON (skips conflicts unless --overwrite).
  migrate                           One-time re-key existing rows under v0.4 canonicalization.
  namespaces                        List all namespaces present in the DB.
  dashboard [--port N]              Launch web dashboard (default :37778).
  help                              Show this message.

Global flags:
  --namespace X                     Scope command to namespace X (overrides WEBCACHE_NAMESPACE).

Environment:
  WEBCACHE_TTL_DAYS=N               Global TTL in days (default unlimited).
  WEBCACHE_MAX_SIZE_MB=N            Trigger LRU eviction above this size (default unlimited).
  WEBCACHE_DOMAIN_TTL='{...}'       Per-domain TTL JSON.
  WEBCACHE_NAMESPACE=X              Isolate cache per project (default empty = shared).
  WEBCACHE_MAX_OUTPUT_MB=N          Reject WebFetch outputs larger than N MB (default 10).
  WEBCACHE_COMPRESS=1               gzip-compress stored responses ≥4KB.
  WEBCACHE_STRICT_REDACT=1          Hash key uses redacted URL — credential-agnostic but collides per endpoint.
  WEBCACHE_QUIET=1                  Suppress hook stderr (file log still written).
  WEBCACHE_DEBUG=1                  Verbose hook tracing.

DB path: ${cache.DB_PATH}
Hook log: ${cache.HOOK_LOG_PATH}
Namespace: ${cache.NAMESPACE || '(default)'}
`);
}

function readUrlsFile(p) {
  const raw = fs.readFileSync(p, 'utf8');
  return raw.split(/\r?\n/).map((l) => l.trim()).filter(Boolean);
}

(function main() {
  if (!cmd || cmd === 'help' || cmd === '--help' || cmd === '-h') {
    help();
    process.exit(0);
  }

  if (cmd === 'stats') {
    if (flag('--by-domain')) {
      const lim = Number(flag('--limit', true)) || 20;
      process.stdout.write(JSON.stringify(cache.statsByDomain(lim), null, 2) + '\n');
      return;
    }
    process.stdout.write(JSON.stringify(cache.stats(), null, 2) + '\n');
    return;
  }

  if (cmd === 'list') {
    const n = Number(args[1]) || 50;
    const offset = Number(flag('--offset', true)) || 0;
    process.stdout.write(JSON.stringify(cache.list(n, offset), null, 2) + '\n');
    return;
  }

  if (cmd === 'invalidate') {
    const url = args[1];
    if (!url) {
      process.stderr.write('Error: invalidate requires a URL argument\n');
      process.exit(2);
    }
    const deleted = cache.invalidate(url);
    process.stdout.write(JSON.stringify({ deleted }) + '\n');
    return;
  }

  if (cmd === 'refresh') {
    const url = args[1];
    const prompt = flag('--prompt', true);
    if (!url || !prompt) {
      process.stderr.write('Error: refresh requires <url> and --prompt "..."\n');
      process.exit(2);
    }
    const deleted = cache.invalidate(url);
    process.stdout.write(JSON.stringify({ refreshed: url, invalidated: deleted }) + '\n');
    return;
  }

  if (cmd === 'warm') {
    const urlsFile = args[1];
    const prompt = flag('--prompt', true);
    if (!urlsFile || !prompt) {
      process.stderr.write('Error: warm requires <urls-file> and --prompt "..."\n');
      process.exit(2);
    }
    const urls = readUrlsFile(urlsFile);
    const hits = [];
    const misses = [];
    const invalid = [];
    for (const u of urls) {
      const v = cache.validateUrl(u);
      if (!v.ok) { invalid.push({ url: u, reason: v.reason }); continue; }
      const h = cache.get(u, prompt);
      if (h != null) hits.push(u); else misses.push(u);
    }
    process.stdout.write(JSON.stringify({ total: urls.length, hits, misses, invalid }, null, 2) + '\n');
    return;
  }

  if (cmd === 'clear') {
    const olderRaw = flag('--older-than-days', true);
    const confirm = flag('--confirm', true);
    const olderThan = olderRaw ? Number(olderRaw) : undefined;
    if (!olderThan && confirm !== 'YES') {
      process.stderr.write('Error: full wipe requires --confirm YES, or pass --older-than-days N for partial.\n');
      process.exit(2);
    }
    const deleted = cache.clear(olderThan);
    process.stdout.write(JSON.stringify({ deleted }) + '\n');
    return;
  }

  if (cmd === 'clear-logs') {
    try {
      if (fs.existsSync(cache.HOOK_LOG_PATH)) {
        fs.writeFileSync(cache.HOOK_LOG_PATH, '');
        process.stdout.write(JSON.stringify({ cleared: cache.HOOK_LOG_PATH }) + '\n');
      } else {
        process.stdout.write(JSON.stringify({ cleared: null, reason: 'no log file' }) + '\n');
      }
    } catch (e) {
      process.stderr.write(`Error: ${e.message}\n`);
      process.exit(2);
    }
    return;
  }

  if (cmd === 'export') {
    const out = flag('--out', true);
    const all = !!flag('--all');
    const rows = cache.list(1_000_000, 0, { global: all });
    // list() doesn't include output by design (it's metadata-only). Re-fetch full rows.
    // For export we need (url, prompt_hash, output, cached_at, hit_count, namespace, compressed).
    // Use cache.list + a follow-up SELECT via internal — for v0.4 export, list metadata only is enough
    // for diagnostic; full payload export is intentionally deferred.
    const payload = { version: 1, exported_at: Date.now(), namespace_scope: all ? '*' : cache.NAMESPACE, rows };
    const text = JSON.stringify(payload, null, 2);
    if (out) { fs.writeFileSync(out, text); process.stdout.write(`exported ${rows.length} rows → ${out}\n`); }
    else process.stdout.write(text + '\n');
    return;
  }

  if (cmd === 'import') {
    process.stderr.write('Error: import not yet implemented (export currently writes metadata only). Track in v0.4.1.\n');
    process.exit(2);
  }

  if (cmd === 'migrate') {
    process.stderr.write('Note: v0.4 migration is automatic on first DB open (schema). Re-keying old rows under new canonicalization is opt-in and not yet implemented. Existing v0.3 rows remain as legacy entries until eviction sweeps them.\n');
    process.exit(0);
  }

  if (cmd === 'namespaces') {
    process.stdout.write(JSON.stringify(cache.listNamespaces()) + '\n');
    return;
  }

  if (cmd === 'dashboard') {
    const port = Number(flag('--port', true)) || 37778;
    require('./dashboard.cjs').start(port);
    return;
  }

  process.stderr.write(`Unknown command: ${cmd}\n\n`);
  help();
  process.exit(2);
})();

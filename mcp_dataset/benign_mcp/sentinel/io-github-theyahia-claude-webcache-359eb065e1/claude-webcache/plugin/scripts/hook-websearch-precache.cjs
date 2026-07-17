#!/usr/bin/env node
'use strict';
process.removeAllListeners('warning');

// PreToolUse hook: serve WebSearch from cache when a fresh entry exists (auto-read).
// stdin = JSON { tool_name, tool_input: { query } }
// On cache HIT  -> deny with the cached results inlined (within TTL — default 6h).
// On cache MISS -> emit nothing (let WebSearch run; PostToolUse hook stores it).
// Disable without uninstalling: WEBCACHE_AUTOREAD=0.

const fs = require('node:fs');
const cache = require('../src/cache.js');

const QUIET = process.env.WEBCACHE_QUIET === '1';
const DEBUG = process.env.WEBCACHE_DEBUG === '1';
const AUTOREAD = process.env.WEBCACHE_AUTOREAD !== '0';
const INLINE_MAX_BYTES = 512 * 1024;

function logError(label, err) {
  const msg = err && err.message ? err.message : String(err);
  const line = `[${new Date().toISOString()}] [claude-webcache] websearch-precache ${label}: ${msg}\n`;
  if (!QUIET) { try { process.stderr.write(line); } catch {} }
  try { fs.appendFileSync(cache.HOOK_LOG_PATH, line); } catch {}
  try { cache.recordHookError(`websearch-precache ${label}: ${msg}`); } catch {}
}

function logDebug(line) {
  if (!DEBUG) return;
  try { process.stderr.write(`[claude-webcache] ${line}\n`); } catch {}
}

function emitDeny(reason) {
  process.stdout.write(JSON.stringify({
    hookSpecificOutput: {
      hookEventName: 'PreToolUse',
      permissionDecision: 'deny',
      permissionDecisionReason: reason,
    },
  }));
}

let raw = '';
process.stdin.on('data', (d) => { raw += d; });
process.stdin.on('end', () => {
  try {
    if (!AUTOREAD) return;
    const { tool_name, tool_input } = JSON.parse(raw || '{}');
    if (tool_name !== 'WebSearch') return;

    const query = (tool_input && tool_input.query) || '';
    if (!query) return;

    const hit = cache.getSearch(query); // content on hit (within TTL), null on miss/expired
    if (hit == null) {
      logDebug(`miss: ${query.slice(0, 80)}`);
      return;
    }

    if (Buffer.byteLength(hit, 'utf8') <= INLINE_MAX_BYTES) {
      emitDeny(
        `[claude-webcache] Cached WebSearch results for "${query}" — search skipped. ` +
        `Use the cached results below; do NOT retry WebSearch for this query.\n\n` +
        `=== CACHED SEARCH RESULTS ===\n${hit}`
      );
    } else {
      emitDeny(
        `[claude-webcache] Cached WebSearch results for "${query}" (large) — search skipped. ` +
        `Call the MCP tool cached_search with this query to read the cached results.`
      );
    }
    logDebug(`hit served: ${query.slice(0, 80)}`);
  } catch (e) {
    logError('hook error', e);
  }
});

#!/usr/bin/env node
'use strict';
process.removeAllListeners('warning');

// PreToolUse hook: serve WebFetch from cache when possible (auto-read).
// stdin = JSON { tool_name, tool_input: { url, prompt } }
// On cache HIT  -> emit permissionDecision "deny" with the cached content in the
//                  reason, so the model uses it without hitting the network.
// On cache MISS -> emit nothing (let WebFetch run; PostToolUse hook will store it).
//
// PreToolUse output schema (verified against claude-mem's working hook):
//   { "hookSpecificOutput": { "hookEventName": "PreToolUse",
//       "permissionDecision": "allow"|"deny"|"ask", "permissionDecisionReason": "..." } }

const fs = require('node:fs');
const cache = require('../src/cache.js');

const QUIET = process.env.WEBCACHE_QUIET === '1';
const DEBUG = process.env.WEBCACHE_DEBUG === '1';
// Disable auto-read entirely without uninstalling: WEBCACHE_AUTOREAD=0
const AUTOREAD = process.env.WEBCACHE_AUTOREAD !== '0';
// Above this size, point the model at cached_fetch instead of inlining the body
// into the deny reason (keeps hook output sane for very large cached pages).
const INLINE_MAX_BYTES = 512 * 1024;

function logError(label, err) {
  const msg = err && err.message ? err.message : String(err);
  const line = `[${new Date().toISOString()}] [claude-webcache] precache ${label}: ${msg}\n`;
  if (!QUIET) { try { process.stderr.write(line); } catch {} }
  try { fs.appendFileSync(cache.HOOK_LOG_PATH, line); } catch {}
  try { cache.recordHookError(`precache ${label}: ${msg}`); } catch {}
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
    if (tool_name !== 'WebFetch') return;

    const url = (tool_input && tool_input.url) || '';
    const prompt = (tool_input && tool_input.prompt) || '';
    if (!url) return;

    const v = cache.validateUrl(url);
    if (!v.ok) return; // let WebFetch handle/refuse it

    const hit = cache.get(url, prompt); // returns content on hit, null on miss; counts the hit
    if (hit == null) {
      logDebug(`miss: ${url.slice(0, 80)}`);
      return; // miss -> allow WebFetch (no output = default allow)
    }

    if (Buffer.byteLength(hit, 'utf8') <= INLINE_MAX_BYTES) {
      emitDeny(
        `[claude-webcache] Cache HIT for ${url} — network fetch skipped. ` +
        `Use the cached result below; do NOT retry WebFetch for this URL.\n\n` +
        `=== CACHED CONTENT ===\n${hit}`
      );
    } else {
      emitDeny(
        `[claude-webcache] Cache HIT for ${url} (large) — network fetch skipped. ` +
        `Call the MCP tool cached_fetch with this url and prompt to read the cached copy.`
      );
    }
    logDebug(`hit served: ${url.slice(0, 80)}`);
  } catch (e) {
    logError('hook error', e);
    // On any error, emit nothing so the WebFetch proceeds normally (fail-open).
  }
});

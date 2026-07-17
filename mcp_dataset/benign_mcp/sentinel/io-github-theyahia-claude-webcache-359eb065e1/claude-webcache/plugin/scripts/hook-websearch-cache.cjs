#!/usr/bin/env node
'use strict';
process.removeAllListeners('warning');

// PostToolUse hook: auto-cache every WebSearch result into the 'websearch' namespace.
// stdin = JSON { tool_name, tool_input: { query }, tool_response: <results> }
// WebSearch response shape isn't contractually fixed, so we extract defensively:
// prefer joined text blocks, fall back to a JSON dump of the whole response.

const fs = require('node:fs');
const cache = require('../src/cache.js');

const QUIET = process.env.WEBCACHE_QUIET === '1';
const DEBUG = process.env.WEBCACHE_DEBUG === '1';

function logError(label, err) {
  const msg = err && err.message ? err.message : String(err);
  const line = `[${new Date().toISOString()}] [claude-webcache] websearch ${label}: ${msg}\n`;
  if (!QUIET) { try { process.stderr.write(line); } catch {} }
  try { fs.appendFileSync(cache.HOOK_LOG_PATH, line); } catch {}
  try { cache.recordHookError(`websearch ${label}: ${msg}`); } catch {}
}

function logDebug(line) {
  if (!DEBUG) return;
  try { process.stderr.write(`[claude-webcache] ${line}\n`); } catch {}
}

function extractOutput(resp) {
  if (resp == null) return '';
  if (typeof resp === 'string') return resp;
  // Common shape: { content: [{ type: 'text', text }] }
  if (Array.isArray(resp.content)) {
    const texts = resp.content.filter((c) => c && c.type === 'text' && c.text).map((c) => c.text);
    if (texts.length) return texts.join('\n');
  }
  // Some platforms wrap results in arrays/objects — dump them.
  try { return JSON.stringify(resp); } catch { return ''; }
}

let raw = '';
process.stdin.on('data', (d) => { raw += d; });
process.stdin.on('end', () => {
  try {
    const { tool_name, tool_input, tool_response } = JSON.parse(raw || '{}');
    if (tool_name !== 'WebSearch') return;

    const query = (tool_input && tool_input.query) || '';
    const output = extractOutput(tool_response);

    if (!query || !output) {
      logDebug(`skip: missing query or output (query=${!!query}, output=${!!output})`);
      return;
    }

    const r = cache.setSearch(query, output);
    if (!r || !r.ok) {
      logError('setSearch failed', new Error((r && r.reason) || 'unknown'));
      return;
    }
    logDebug(`cached search: ${query.slice(0, 80)} (${output.length} bytes)`);
  } catch (e) {
    logError('hook error', e);
  }
});

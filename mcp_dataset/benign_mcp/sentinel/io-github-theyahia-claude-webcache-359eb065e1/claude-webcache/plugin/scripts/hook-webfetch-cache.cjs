#!/usr/bin/env node
'use strict';
process.removeAllListeners('warning');

// PostToolUse hook: auto-cache every WebFetch result into SQLite.
// stdin = JSON { tool_name, tool_input: { url, prompt }, tool_response: { content: [{type,text}] } }
const fs = require('node:fs');
const cache = require('../src/cache.js');

const QUIET = process.env.WEBCACHE_QUIET === '1';
const DEBUG = process.env.WEBCACHE_DEBUG === '1';

function logError(label, err) {
  const msg = err && err.message ? err.message : String(err);
  const line = `[${new Date().toISOString()}] [claude-webcache] ${label}: ${msg}\n`;
  if (!QUIET) {
    try { process.stderr.write(line); } catch {}
  }
  try {
    fs.appendFileSync(cache.HOOK_LOG_PATH, line);
  } catch {}
  try { cache.recordHookError(`${label}: ${msg}`); } catch {}
}

function logDebug(line) {
  if (!DEBUG) return;
  try { process.stderr.write(`[claude-webcache] ${line}\n`); } catch {}
}

let raw = '';
process.stdin.on('data', (d) => { raw += d; });
process.stdin.on('end', () => {
  try {
    const { tool_name, tool_input, tool_response } = JSON.parse(raw);
    if (tool_name !== 'WebFetch') return;

    const url = (tool_input && tool_input.url) || '';
    const prompt = (tool_input && tool_input.prompt) || '';
    const textBlock = tool_response && tool_response.content &&
      tool_response.content.find((c) => c.type === 'text');
    const output = (textBlock && textBlock.text) || '';

    if (!url || !output) {
      logDebug(`skip: missing url or output (url=${!!url}, output=${!!output})`);
      return;
    }

    const v = cache.validateUrl(url);
    if (!v.ok) {
      logError('skip url', new Error(v.reason));
      return;
    }

    const r = cache.set(url, prompt, output);
    if (!r || !r.ok) {
      logError('set failed', new Error((r && r.reason) || 'unknown'));
      return;
    }
    logDebug(`cached: ${url.slice(0, 80)} (${output.length} bytes)`);
  } catch (e) {
    logError('hook error', e);
  }
});

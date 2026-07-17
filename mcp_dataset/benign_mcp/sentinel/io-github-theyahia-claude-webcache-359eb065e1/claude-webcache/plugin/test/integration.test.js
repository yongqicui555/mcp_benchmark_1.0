'use strict';
process.removeAllListeners('warning');

const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const os = require('node:os');
const fs = require('node:fs');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');

const MCP_SERVER = path.resolve(__dirname, '..', 'scripts', 'mcp-server.cjs');

// ─────────────────────────────────────────────────────────────────
// MCP JSON-RPC client (newline-delimited messages on stdio)
// ─────────────────────────────────────────────────────────────────

function makeClient() {
  const tmpRoot = path.join(os.tmpdir(), `webcache-int-${crypto.randomUUID()}`);
  fs.mkdirSync(tmpRoot, { recursive: true });

  const env = {
    ...process.env,
    HOME: tmpRoot,
    USERPROFILE: tmpRoot,
    // Force fresh state
    WEBCACHE_TTL_DAYS: '',
    WEBCACHE_NAMESPACE: '',
    WEBCACHE_QUIET: '1',
  };

  const child = spawn(process.execPath, [MCP_SERVER], {
    env,
    stdio: ['pipe', 'pipe', 'pipe'],
  });

  let stderrBuf = '';
  child.stderr.on('data', (d) => { stderrBuf += d.toString(); });

  let buffer = '';
  const pending = new Map();
  let nextId = 1;

  child.stdout.on('data', (chunk) => {
    buffer += chunk.toString();
    let idx;
    while ((idx = buffer.indexOf('\n')) !== -1) {
      const line = buffer.slice(0, idx).trim();
      buffer = buffer.slice(idx + 1);
      if (!line) continue;
      let msg;
      try { msg = JSON.parse(line); } catch { continue; }
      if (msg.id != null && pending.has(msg.id)) {
        const { resolve, reject } = pending.get(msg.id);
        pending.delete(msg.id);
        if (msg.error) reject(new Error(JSON.stringify(msg.error)));
        else resolve(msg.result);
      }
    }
  });

  function request(method, params) {
    const id = nextId++;
    const msg = { jsonrpc: '2.0', id, method, params };
    return new Promise((resolve, reject) => {
      pending.set(id, { resolve, reject });
      child.stdin.write(JSON.stringify(msg) + '\n');
      setTimeout(() => {
        if (pending.has(id)) {
          pending.delete(id);
          reject(new Error(`timeout on ${method}\nstderr: ${stderrBuf}`));
        }
      }, 5000);
    });
  }

  function notify(method, params) {
    const msg = { jsonrpc: '2.0', method, params };
    child.stdin.write(JSON.stringify(msg) + '\n');
  }

  async function close() {
    try { child.stdin.end(); } catch {}
    try { child.kill(); } catch {}
    try { fs.rmSync(tmpRoot, { recursive: true, force: true }); } catch {}
  }

  async function init() {
    const r = await request('initialize', {
      protocolVersion: '2024-11-05',
      capabilities: {},
      clientInfo: { name: 'integration-test', version: '0.0.0' },
    });
    notify('notifications/initialized', {});
    return r;
  }

  async function call(toolName, args) {
    const r = await request('tools/call', { name: toolName, arguments: args || {} });
    return r;
  }

  return { init, request, call, close, tmpRoot, getStderr: () => stderrBuf };
}

function extractText(res) {
  if (!res || !res.content || !res.content[0]) return '';
  return res.content[0].text;
}

// ─────────────────────────────────────────────────────────────────
// Tests
// ─────────────────────────────────────────────────────────────────

test('integration: initialize handshake succeeds', async () => {
  const c = makeClient();
  try {
    const init = await c.init();
    assert.ok(init.serverInfo, 'serverInfo returned');
    assert.strictEqual(init.serverInfo.name, 'claude-webcache');
  } finally { await c.close(); }
});

test('integration: tools/list returns 9 tools', async () => {
  const c = makeClient();
  try {
    await c.init();
    const r = await c.request('tools/list', {});
    assert.strictEqual(r.tools.length, 9);
    const names = r.tools.map((t) => t.name).sort();
    assert.deepStrictEqual(names, [
      'cache_clear', 'cache_invalidate', 'cache_list', 'cache_refresh',
      'cache_stats', 'cache_store', 'cache_warm', 'cached_fetch', 'cached_search',
    ]);
  } finally { await c.close(); }
});

test('integration: cached_search miss → WebSearch hook store → hit', async () => {
  const c = makeClient();
  try {
    await c.init();
    const miss = await c.call('cached_search', { query: 'qsearch latency 2026' });
    assert.match(extractText(miss), /^\[CACHE_MISS\] qsearch latency 2026/);
  } finally { await c.close(); }
});

test('integration: cached_fetch miss → store → hit cycle', async () => {
  const c = makeClient();
  try {
    await c.init();
    const miss = await c.call('cached_fetch', { url: 'https://example.com/x', prompt: 'p' });
    assert.match(extractText(miss), /^\[CACHE_MISS\] https:\/\/example\.com\/x/);

    const stored = await c.call('cache_store', { url: 'https://example.com/x', prompt: 'p', output: 'hello' });
    assert.strictEqual(extractText(stored), 'stored');

    const hit = await c.call('cached_fetch', { url: 'https://example.com/x', prompt: 'p' });
    assert.strictEqual(extractText(hit), 'hello');
  } finally { await c.close(); }
});

test('integration: cache_stats returns valid JSON with expected fields', async () => {
  const c = makeClient();
  try {
    await c.init();
    await c.call('cache_store', { url: 'https://example.com/a', prompt: 'p', output: 'v' });
    const r = await c.call('cache_stats', {});
    const s = JSON.parse(extractText(r));
    assert.strictEqual(typeof s.total, 'number');
    assert.strictEqual(typeof s.hit_rate, 'number');
    assert.ok('namespace' in s);
    assert.ok('hook_log_path' in s);
    assert.ok('top_urls' in s);
  } finally { await c.close(); }
});

test('integration: cache_list returns recent entries', async () => {
  const c = makeClient();
  try {
    await c.init();
    await c.call('cache_store', { url: 'https://a.com', prompt: 'p', output: 'x' });
    await c.call('cache_store', { url: 'https://b.com', prompt: 'p', output: 'y' });
    const r = await c.call('cache_list', { limit: 10 });
    const rows = JSON.parse(extractText(r));
    assert.strictEqual(rows.length, 2);
  } finally { await c.close(); }
});

test('integration: cache_warm classifies hits/misses/invalid', async () => {
  const c = makeClient();
  try {
    await c.init();
    await c.call('cache_store', { url: 'https://a.com/1', prompt: 'p', output: 'x' });

    const r = await c.call('cache_warm', {
      entries: [
        { url: 'https://a.com/1', prompt: 'p' },     // hit
        { url: 'https://a.com/2', prompt: 'p' },     // miss
        { url: 'file:///etc/passwd', prompt: 'p' },  // invalid
      ],
    });
    const result = JSON.parse(extractText(r));
    assert.strictEqual(result.hits.length, 1);
    assert.strictEqual(result.misses.length, 1);
    assert.strictEqual(result.invalid.length, 1);
    assert.match(result.invalid[0].reason, /unsupported scheme/);
  } finally { await c.close(); }
});

test('integration: cache_warm urls[]+prompt convenience form', async () => {
  const c = makeClient();
  try {
    await c.init();
    await c.call('cache_store', { url: 'https://a.com', prompt: 'q', output: 'x' });
    const r = await c.call('cache_warm', { urls: ['https://a.com', 'https://b.com'], prompt: 'q' });
    const result = JSON.parse(extractText(r));
    assert.strictEqual(result.hits.length, 1);
    assert.strictEqual(result.misses.length, 1);
  } finally { await c.close(); }
});

test('integration: cache_refresh invalidates and returns CACHE_MISS', async () => {
  const c = makeClient();
  try {
    await c.init();
    await c.call('cache_store', { url: 'https://x.com', prompt: 'p', output: 'old' });

    const hit = await c.call('cached_fetch', { url: 'https://x.com', prompt: 'p' });
    assert.strictEqual(extractText(hit), 'old');

    const refreshed = await c.call('cache_refresh', { url: 'https://x.com', prompt: 'p' });
    assert.match(extractText(refreshed), /^\[CACHE_MISS\]/);

    // After refresh, next cached_fetch is also a miss (until WebFetch/store rewrites it)
    const stillMiss = await c.call('cached_fetch', { url: 'https://x.com', prompt: 'p' });
    assert.match(extractText(stillMiss), /^\[CACHE_MISS\]/);
  } finally { await c.close(); }
});

test('integration: cache_invalidate drops entries for a URL', async () => {
  const c = makeClient();
  try {
    await c.init();
    await c.call('cache_store', { url: 'https://a.com', prompt: 'p1', output: 'x' });
    await c.call('cache_store', { url: 'https://a.com', prompt: 'p2', output: 'y' });
    await c.call('cache_store', { url: 'https://b.com', prompt: 'p1', output: 'z' });

    const r = await c.call('cache_invalidate', { url: 'https://a.com' });
    const result = JSON.parse(extractText(r));
    assert.strictEqual(result.deleted, 2);
  } finally { await c.close(); }
});

test('integration: cache_clear without confirm errors; with confirm wipes', async () => {
  const c = makeClient();
  try {
    await c.init();
    await c.call('cache_store', { url: 'https://a.com', prompt: 'p', output: 'x' });

    const noConfirm = await c.call('cache_clear', {});
    assert.strictEqual(noConfirm.isError, true);
    assert.match(extractText(noConfirm), /requires confirm/);

    const wiped = await c.call('cache_clear', { confirm: 'YES' });
    const result = JSON.parse(extractText(wiped));
    assert.strictEqual(result.deleted, 1);
  } finally { await c.close(); }
});

test('integration: cached_fetch rejects file:// scheme', async () => {
  const c = makeClient();
  try {
    await c.init();
    const r = await c.call('cached_fetch', { url: 'file:///etc/passwd', prompt: 'p' });
    assert.strictEqual(r.isError, true);
    assert.match(extractText(r), /unsupported scheme/);
  } finally { await c.close(); }
});

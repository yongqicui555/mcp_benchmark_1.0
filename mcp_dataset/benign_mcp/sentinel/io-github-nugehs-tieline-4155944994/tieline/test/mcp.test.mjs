import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { ROOT } from './helpers.mjs';

const BIN = path.join(ROOT, 'bin', 'tieline-mcp.mjs');

// Drive the MCP server: feed JSON-RPC lines, collect the responses (objects with
// an `id`), resolve once we've seen `expected` of them. Notifications are sent
// but produce no reply, so they don't count.
function rpc(messages, expected) {
  return new Promise((resolve, reject) => {
    const child = spawn(process.execPath, [BIN], { cwd: ROOT });
    const out = [];
    let buf = '';
    const timer = setTimeout(() => {
      child.kill();
      reject(new Error(`timed out; got ${out.length}/${expected} responses`));
    }, 10000);

    child.stdout.on('data', (chunk) => {
      buf += chunk.toString();
      let nl;
      while ((nl = buf.indexOf('\n')) >= 0) {
        const line = buf.slice(0, nl).trim();
        buf = buf.slice(nl + 1);
        if (!line) continue;
        out.push(JSON.parse(line));
        if (out.length >= expected) {
          clearTimeout(timer);
          child.stdin.end();
          child.kill();
          resolve(out);
        }
      }
    });
    child.on('error', reject);

    for (const m of messages) child.stdin.write(JSON.stringify(m) + '\n');
  });
}

test('mcp: initialize advertises tools capability + serverInfo', async () => {
  const [res] = await rpc(
    [{ jsonrpc: '2.0', id: 1, method: 'initialize', params: { protocolVersion: '2025-06-18' } }],
    1,
  );
  assert.equal(res.id, 1);
  assert.equal(res.result.serverInfo.name, 'tieline');
  assert.ok(res.result.capabilities.tools);
  assert.equal(res.result.protocolVersion, '2025-06-18');
});

test('mcp: tools/list exposes the five tieline tools', async () => {
  const out = await rpc(
    [
      { jsonrpc: '2.0', id: 1, method: 'initialize', params: {} },
      { jsonrpc: '2.0', method: 'notifications/initialized' }, // no reply
      { jsonrpc: '2.0', id: 2, method: 'tools/list' },
    ],
    2,
  );
  const list = out.find((m) => m.id === 2);
  const names = list.result.tools.map((t) => t.name).sort();
  assert.deepEqual(names, ['tieline_check', 'tieline_doctor', 'tieline_init', 'tieline_list', 'tieline_orphans']);
});

test('mcp: tieline_check returns structured drift over a real fixture', async () => {
  const cfg = path.join(os.tmpdir(), 'tieline-mcp-test.config.json');
  fs.writeFileSync(
    cfg,
    JSON.stringify({
      client: { adapter: 'rtk-query', repo: ROOT, roots: ['examples/express-fixture-client'], basePath: '/api/v1' },
      server: { adapter: 'express', repo: path.join(ROOT, 'examples', 'express-fixture'), roots: ['.'] },
      failOn: ['drift'],
    }),
  );
  try {
    const out = await rpc(
      [
        { jsonrpc: '2.0', id: 1, method: 'initialize', params: {} },
        { jsonrpc: '2.0', id: 2, method: 'tools/call', params: { name: 'tieline_check', arguments: { config: cfg } } },
      ],
      2,
    );
    const call = out.find((m) => m.id === 2);
    assert.equal(call.result.isError, undefined);
    const data = JSON.parse(call.result.content[0].text);
    assert.equal(data.totals.matched, 5);
    assert.equal(data.totals.drift, 2);
  } finally {
    fs.rmSync(cfg, { force: true });
  }
});

test('mcp: a tool failure comes back as isError, not a protocol error', async () => {
  const out = await rpc(
    [
      { jsonrpc: '2.0', id: 1, method: 'initialize', params: {} },
      {
        jsonrpc: '2.0',
        id: 2,
        method: 'tools/call',
        params: { name: 'tieline_check', arguments: { config: '/no/such/config.json' } },
      },
    ],
    2,
  );
  const call = out.find((m) => m.id === 2);
  assert.equal(call.result.isError, true);
  assert.match(call.result.content[0].text, /tieline error/);
});

test('mcp: unknown method yields a JSON-RPC method-not-found error', async () => {
  const [res] = await rpc([{ jsonrpc: '2.0', id: 7, method: 'frobnicate' }], 1);
  assert.equal(res.error.code, -32601);
});

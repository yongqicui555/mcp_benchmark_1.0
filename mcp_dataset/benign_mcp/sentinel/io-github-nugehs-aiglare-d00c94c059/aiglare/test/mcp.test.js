import { test } from 'node:test';
import assert from 'node:assert';
import path from 'node:path';
import { PassThrough } from 'node:stream';
import { fileURLToPath } from 'node:url';
import { startMcpServer } from '../src/mcp.js';

const here = path.dirname(fileURLToPath(import.meta.url));
const fx = (p) => path.join(here, 'fixtures', p);

// Drive the stdio server with a list of JSON-RPC requests; return parsed replies.
async function rpc(requests) {
  const input = new PassThrough();
  const output = new PassThrough();
  const chunks = [];
  output.on('data', (c) => chunks.push(c.toString('utf8')));

  const done = startMcpServer({ input, output });
  for (const req of requests) input.write(JSON.stringify(req) + '\n');
  input.end();
  await done;

  return chunks
    .join('')
    .split('\n')
    .filter(Boolean)
    .map((l) => JSON.parse(l));
}

test('initialize returns protocol version and server info', async () => {
  const [res] = await rpc([{ jsonrpc: '2.0', id: 1, method: 'initialize' }]);
  assert.equal(res.id, 1);
  assert.equal(res.result.protocolVersion, '2025-06-18');
  assert.equal(res.result.serverInfo.name, '@nugehs/aiglare');
  assert.ok(res.result.capabilities.tools);
});

test('tools/list advertises the audit tools', async () => {
  const [res] = await rpc([{ jsonrpc: '2.0', id: 2, method: 'tools/list' }]);
  const names = res.result.tools.map((t) => t.name);
  assert.deepEqual(names.sort(), ['ai_surface_audit', 'ai_surface_gate', 'list_providers']);
});

test('tools/call ai_surface_audit returns a structured report', async () => {
  const [res] = await rpc([
    {
      jsonrpc: '2.0',
      id: 3,
      method: 'tools/call',
      params: { name: 'ai_surface_audit', arguments: { path: fx('bad') } },
    },
  ]);
  const report = res.result.structuredContent;
  assert.equal(res.result.isError, false);
  assert.equal(report.summary.red, 2); // both bad fixtures are red
  assert.ok(report.surfaces.length === 2);
});

test('tools/call ai_surface_gate flags a red side-effectful surface', async () => {
  const [res] = await rpc([
    {
      jsonrpc: '2.0',
      id: 4,
      method: 'tools/call',
      params: { name: 'ai_surface_gate', arguments: { path: fx('bad') } },
    },
  ]);
  const gate = res.result.structuredContent;
  assert.equal(gate.passed, false);
  assert.ok(gate.blocking >= 1);
});

test('unknown method returns a JSON-RPC error', async () => {
  const [res] = await rpc([{ jsonrpc: '2.0', id: 5, method: 'does/not/exist' }]);
  assert.equal(res.error.code, -32601);
});

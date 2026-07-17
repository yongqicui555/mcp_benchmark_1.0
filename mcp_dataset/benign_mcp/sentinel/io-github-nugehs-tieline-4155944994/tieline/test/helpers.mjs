import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { normalizePath, routeKey } from '../src/normalize.mjs';

export const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
export const ex = (rel) => path.join(ROOT, 'examples', rel);

/** Set of "METHOD normalized/path" keys for an array of routes/endpoints. */
export const keySet = (arr) => new Set(arr.map((r) => routeKey(r.method, normalizePath(r.rawPath))));

/** Assert an adapter produced exactly `expected` keys — no more, no less. */
export function assertRoutes(assert, arr, expected) {
  const got = keySet(arr);
  for (const e of expected) assert.ok(got.has(e), `missing route: ${e}\n  got: ${[...got].sort().join(', ')}`);
  assert.equal(got.size, expected.length, `unexpected extra routes: ${[...got].sort().join(', ')}`);
}

/** Write `files` ({ relpath: contents }) into a fresh temp dir, run fn(dir), clean up. */
export function withTempRepo(files, fn) {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'tieline-'));
  try {
    for (const [rel, content] of Object.entries(files)) {
      const fp = path.join(dir, rel);
      fs.mkdirSync(path.dirname(fp), { recursive: true });
      fs.writeFileSync(fp, content);
    }
    return fn(dir);
  } finally {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

// Builders for hand-crafted matcher/doctor inputs.
export const clientEp = (method, rawPath, resolvable = true) => ({
  side: 'client', name: rawPath ?? 'dynamic', method, rawPath, resolvable, file: 'client.ts', line: 1,
});
export const serverRoute = (method, rawPath) => ({ side: 'server', method, rawPath, file: 'server.ts', line: 1 });

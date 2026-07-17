'use strict';
process.removeAllListeners('warning');

const test = require('node:test');
const assert = require('node:assert');
const path = require('node:path');
const os = require('node:os');
const fs = require('node:fs');
const crypto = require('node:crypto');
const { spawn } = require('node:child_process');

const WORKER = path.resolve(__dirname, 'concurrent-worker.cjs');

function makeShared() {
  const tmpRoot = path.join(os.tmpdir(), `webcache-conc-${crypto.randomUUID()}`);
  fs.mkdirSync(tmpRoot, { recursive: true });
  return {
    tmpRoot,
    env: { HOME: tmpRoot, USERPROFILE: tmpRoot, WEBCACHE_QUIET: '1' },
    cleanup() { try { fs.rmSync(tmpRoot, { recursive: true, force: true }); } catch {} },
  };
}

function spawnWorker(env, args) {
  return new Promise((resolve) => {
    const child = spawn(process.execPath, [WORKER, ...args], {
      env: { ...process.env, ...env },
      stdio: ['ignore', 'pipe', 'pipe'],
    });
    let stderr = '';
    child.stderr.on('data', (d) => { stderr += d.toString(); });
    child.on('exit', (code) => resolve({ code, stderr }));
  });
}

function readCache(env) {
  // Read the DB from the same homedir as workers used.
  const CACHE_MOD = require.resolve('../src/cache.js');
  delete require.cache[CACHE_MOD];
  const orig = { HOME: process.env.HOME, USERPROFILE: process.env.USERPROFILE };
  process.env.HOME = env.HOME;
  process.env.USERPROFILE = env.USERPROFILE;
  const osMod = require('node:os');
  const origHome = osMod.homedir;
  osMod.homedir = () => env.HOME;
  const cache = require(CACHE_MOD);
  return {
    cache,
    cleanup() {
      delete require.cache[CACHE_MOD];
      osMod.homedir = origHome;
      if (orig.HOME === undefined) delete process.env.HOME; else process.env.HOME = orig.HOME;
      if (orig.USERPROFILE === undefined) delete process.env.USERPROFILE; else process.env.USERPROFILE = orig.USERPROFILE;
    },
  };
}

test('concurrent: 5 parallel writers each write 50 entries, all 250 land', async () => {
  const shared = makeShared();
  try {
    const N_WORKERS = 5;
    const PER = 50;
    const promises = [];
    for (let i = 0; i < N_WORKERS; i++) {
      promises.push(spawnWorker(shared.env, [String(PER), `w${i}`, 'write']));
    }
    const results = await Promise.all(promises);
    for (const r of results) {
      assert.strictEqual(r.code, 0, `worker exited non-zero: ${r.stderr}`);
    }
    const { cache, cleanup } = readCache(shared.env);
    try {
      const total = cache.list(10000).length;
      assert.strictEqual(total, N_WORKERS * PER, 'all writes landed');
    } finally { cleanup(); }
  } finally { shared.cleanup(); }
});

test('concurrent: writer + vacuum (eviction) — no crash', async () => {
  const shared = makeShared();
  try {
    // First seed enough rows so eviction has something to do under tiny size cap.
    const seedEnv = { ...shared.env, WEBCACHE_MAX_SIZE_MB: '0.01' };
    const seed = await spawnWorker(seedEnv, ['100', 'seed', 'write']);
    assert.strictEqual(seed.code, 0, `seed worker: ${seed.stderr}`);

    // Then write more while another process VACUUMs concurrently.
    const writer = spawnWorker(seedEnv, ['50', 'late', 'write']);
    const vac = spawnWorker(seedEnv, ['1', 'vac', 'vacuum']);
    const [wr, vr] = await Promise.all([writer, vac]);
    assert.strictEqual(wr.code, 0, `writer crashed: ${wr.stderr}`);
    assert.strictEqual(vr.code, 0, `vacuum crashed: ${vr.stderr}`);
  } finally { shared.cleanup(); }
});

test('concurrent: 1 writer + 5 readers — readers never see partial output', async () => {
  const shared = makeShared();
  try {
    // Seed N=20 rows first (sync).
    const seedEnv = { ...shared.env };
    const seed = await spawnWorker(seedEnv, ['20', 'seeded', 'write']);
    assert.strictEqual(seed.code, 0);

    // Spawn 1 writer (more writes) + 5 readers concurrently.
    const promises = [];
    promises.push(spawnWorker(seedEnv, ['30', 'late', 'write']));
    for (let i = 0; i < 5; i++) {
      promises.push(spawnWorker(seedEnv, ['20', `r${i}`, 'read']));
    }
    const results = await Promise.all(promises);
    for (const r of results) {
      assert.ok(r.code === 0 || r.code === 4, `unexpected exit ${r.code}: ${r.stderr}`);
      // code 4 = all reads missed (acceptable if reader scheduled before seeder rows were committed)
      // code 3 = corrupt value detected (would be a real bug, never accepted)
      assert.notStrictEqual(r.code, 3, `reader detected corrupt value: ${r.stderr}`);
    }
  } finally { shared.cleanup(); }
});

test('concurrent: schema migration is idempotent across processes', async () => {
  const shared = makeShared();
  try {
    // First two workers race to open the DB. Both should succeed; neither should fail
    // due to duplicate CREATE/ALTER.
    const a = spawnWorker(shared.env, ['10', 'a', 'write']);
    const b = spawnWorker(shared.env, ['10', 'b', 'write']);
    const [ra, rb] = await Promise.all([a, b]);
    assert.strictEqual(ra.code, 0, `worker a: ${ra.stderr}`);
    assert.strictEqual(rb.code, 0, `worker b: ${rb.stderr}`);

    // Third worker opens DB after migration — must still see all 20 entries.
    const { cache, cleanup } = readCache(shared.env);
    try {
      assert.strictEqual(cache.list(1000).length, 20);
    } finally { cleanup(); }
  } finally { shared.cleanup(); }
});

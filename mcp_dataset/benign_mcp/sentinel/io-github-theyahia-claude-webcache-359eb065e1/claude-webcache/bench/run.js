#!/usr/bin/env node
// Single-process latency + storage bench for claude-webcache.
// Writes synthetic entries, measures read hit / read miss / list / write latency,
// then dumps JSON + a human-readable table.
//
// Usage:
//   node bench/run.js                 # default sizes (N=10000, M=10000)
//   node bench/run.js --n=5000        # smaller run
//   node bench/run.js --label=before  # tag the result file (e.g. before/after hw swap)

process.removeAllListeners('warning');

const os = require('node:os');
const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const { performance } = require('node:perf_hooks');
const { execSync } = require('node:child_process');

const args = Object.fromEntries(
  process.argv.slice(2)
    .filter((a) => a.startsWith('--'))
    .map((a) => {
      const [k, v] = a.replace(/^--/, '').split('=');
      return [k, v ?? 'true'];
    })
);

const N = Number(args.n || 10000);                  // populate size
const M = Number(args.m || 10000);                  // hit reads
const MISS_K = Number(args['miss-k'] || 1000);      // miss reads
const LIST_K = Number(args['list-k'] || 200);       // list calls
const OUTPUT_BYTES = Number(args['output-bytes'] || 1024);
const LABEL = args.label || 'baseline';

// Isolate to a temp homedir so we don't pollute ~/.webcache.
const tmpRoot = path.join(os.tmpdir(), `webcache-bench-${crypto.randomUUID()}`);
fs.mkdirSync(tmpRoot, { recursive: true });
const origHome = os.homedir;
os.homedir = () => tmpRoot;
delete process.env.WEBCACHE_TTL_DAYS;

const cache = require('../plugin/src/cache.js');

function percentile(sortedAsc, p) {
  if (sortedAsc.length === 0) return 0;
  const idx = Math.min(sortedAsc.length - 1, Math.floor(sortedAsc.length * p));
  return sortedAsc[idx];
}

function summarize(name, samples) {
  samples.sort((a, b) => a - b);
  const sum = samples.reduce((s, v) => s + v, 0);
  return {
    name,
    n: samples.length,
    mean_ms: +(sum / samples.length).toFixed(4),
    p50_ms: +percentile(samples, 0.5).toFixed(4),
    p95_ms: +percentile(samples, 0.95).toFixed(4),
    p99_ms: +percentile(samples, 0.99).toFixed(4),
    max_ms: +samples[samples.length - 1].toFixed(4),
    ops_per_sec: Math.round(samples.length / (sum / 1000)),
  };
}

function timed(fn) {
  const t0 = performance.now();
  const out = fn();
  const dt = performance.now() - t0;
  return { dt, out };
}

function gitCommit() {
  try {
    return execSync('git rev-parse --short HEAD', {
      cwd: path.dirname(__dirname),
      stdio: ['ignore', 'pipe', 'ignore'],
    }).toString().trim();
  } catch { return null; }
}

function machineMeta() {
  const cpus = os.cpus();
  return {
    platform: process.platform,
    arch: process.arch,
    node_version: process.version,
    cpu_model: cpus[0]?.model ?? 'unknown',
    cpu_count: cpus.length,
    total_mem_gb: +(os.totalmem() / 1024 ** 3).toFixed(1),
    os_release: os.release(),
  };
}

console.log(`bench: N=${N} populate, M=${M} hits, MISS=${MISS_K}, LIST=${LIST_K}, output=${OUTPUT_BYTES}B`);
console.log(`bench: temp dir = ${tmpRoot}`);

const synthOutput = 'x'.repeat(OUTPUT_BYTES);

// === Write phase: populate N entries, measure per-op latency ===
const writeSamples = [];
for (let i = 0; i < N; i++) {
  const url = `https://example.com/page/${i}`;
  const prompt = `prompt-${i}`;
  const { dt } = timed(() => cache.set(url, prompt, synthOutput));
  writeSamples.push(dt);
}
const writeStats = summarize('write', writeSamples);

// === Read hit phase: M random reads on populated keys ===
const hitSamples = [];
for (let i = 0; i < M; i++) {
  const k = Math.floor(Math.random() * N);
  const url = `https://example.com/page/${k}`;
  const prompt = `prompt-${k}`;
  const { dt, out } = timed(() => cache.get(url, prompt));
  if (out !== synthOutput) {
    throw new Error(`hit returned wrong value at i=${i} k=${k}`);
  }
  hitSamples.push(dt);
}
const hitStats = summarize('read_hit', hitSamples);

// === Read miss phase ===
const missSamples = [];
for (let i = 0; i < MISS_K; i++) {
  const url = `https://example.com/missing/${i}`;
  const prompt = `nope-${i}`;
  const { dt, out } = timed(() => cache.get(url, prompt));
  if (out !== null) throw new Error(`miss returned non-null at i=${i}`);
  missSamples.push(dt);
}
const missStats = summarize('read_miss', missSamples);

// === List phase ===
const listSamples = [];
for (let i = 0; i < LIST_K; i++) {
  const { dt } = timed(() => cache.list(50));
  listSamples.push(dt);
}
const listStats = summarize('list_50', listSamples);

// === Storage phase ===
const dbPath = cache.DB_PATH;
const dbBytes = fs.statSync(dbPath).size;
const walPath = `${dbPath}-wal`;
const walBytes = fs.existsSync(walPath) ? fs.statSync(walPath).size : 0;
const totalBytes = dbBytes + walBytes;

const result = {
  meta: {
    label: LABEL,
    timestamp: new Date().toISOString(),
    commit: gitCommit(),
    machine: machineMeta(),
    config: { N, M, miss_k: MISS_K, list_k: LIST_K, output_bytes: OUTPUT_BYTES },
  },
  latency: {
    write: writeStats,
    read_hit: hitStats,
    read_miss: missStats,
    list_50: listStats,
  },
  storage: {
    db_bytes: dbBytes,
    wal_bytes: walBytes,
    total_bytes: totalBytes,
    bytes_per_entry: Math.round(totalBytes / N),
  },
};

// Restore homedir before any post-bench file ops outside tmp.
os.homedir = origHome;

// Pretty-print table
const opStats = [writeStats, hitStats, missStats, listStats];
const colW = { name: 12, p50: 10, p95: 10, p99: 10, ops: 12 };
const head = ['op', 'p50_ms', 'p95_ms', 'p99_ms', 'ops/sec'];
console.log('\n' + head.map((h, i) => h.padEnd(Object.values(colW)[i])).join(''));
console.log('-'.repeat(head.reduce((s, _, i) => s + Object.values(colW)[i], 0)));
for (const s of opStats) {
  const row = [
    s.name.padEnd(colW.name),
    String(s.p50_ms).padEnd(colW.p50),
    String(s.p95_ms).padEnd(colW.p95),
    String(s.p99_ms).padEnd(colW.p99),
    String(s.ops_per_sec).padEnd(colW.ops),
  ].join('');
  console.log(row);
}
console.log(`\nstorage: ${(totalBytes / 1024).toFixed(1)} KB total ` +
  `(${result.storage.bytes_per_entry} bytes/entry on N=${N})`);

// Save JSON to bench/results/
const resultsDir = path.join(__dirname, 'results');
fs.mkdirSync(resultsDir, { recursive: true });
const dateStr = new Date().toISOString().slice(0, 10);
const commit = result.meta.commit || 'nogit';
const fname = `${dateStr}-${LABEL}-${commit}.json`;
const outPath = path.join(resultsDir, fname);
fs.writeFileSync(outPath, JSON.stringify(result, null, 2));
console.log(`\nsaved: ${path.relative(process.cwd(), outPath)}`);

// Cleanup temp dir
try { fs.rmSync(tmpRoot, { recursive: true, force: true }); } catch {}

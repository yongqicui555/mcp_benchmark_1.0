#!/usr/bin/env node
'use strict';
process.removeAllListeners('warning');

// Worker spawned by concurrent.test.js. Args: <count> <prefix>
// USERPROFILE/HOME is set in parent — cache.js resolves DB_PATH from there.

const [count, prefix, mode] = process.argv.slice(2);
const N = Number(count) || 50;
const PFX = prefix || 'p';
const M = mode || 'write';

const cache = require('../src/cache.js');

try {
  if (M === 'write') {
    for (let i = 0; i < N; i++) {
      const r = cache.set(`https://example.com/${PFX}/${i}`, 'q', `output-${PFX}-${i}`);
      if (!r || !r.ok) {
        process.stderr.write(`worker ${PFX}: set #${i} failed: ${r && r.reason}\n`);
        process.exit(2);
      }
    }
    process.exit(0);
  }
  if (M === 'read') {
    let nullCount = 0;
    for (let i = 0; i < N; i++) {
      const v = cache.get(`https://example.com/seeded/${i}`, 'q');
      if (v == null) nullCount++;
      // Either fresh hit or stale/missing — must not throw or return partial.
      if (v != null && typeof v !== 'string') {
        process.stderr.write(`worker reader: corrupt value at ${i}\n`);
        process.exit(3);
      }
    }
    process.exit(nullCount > N ? 4 : 0);
  }
  if (M === 'vacuum') {
    // Simulate eviction trigger under pressure.
    try { cache.evictIfNeeded(); } catch (e) {
      process.stderr.write(`vacuum failed: ${e.message}\n`);
      process.exit(5);
    }
    process.exit(0);
  }
  process.stderr.write(`unknown mode: ${M}\n`);
  process.exit(99);
} catch (e) {
  process.stderr.write(`worker ${PFX} uncaught: ${e.message}\n`);
  process.exit(1);
}

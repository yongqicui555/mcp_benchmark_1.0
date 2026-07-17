const test = require('node:test');
const assert = require('node:assert');
const { freshCache, sleep } = require('./helpers.js');

test('searchUrl: builds a stable synthetic https URL on the websearch host', () => {
  const { cache, cleanup } = freshCache();
  try {
    const u = cache.searchUrl('qwen 600m benchmarks');
    assert.match(u, /^https:\/\/websearch\.local\/\?q=/);
    assert.strictEqual(u, cache.searchUrl('  qwen 600m benchmarks  '), 'query is trimmed');
  } finally { cleanup(); }
});

test('setSearch + getSearch: round-trip in the websearch namespace', () => {
  const { cache, cleanup } = freshCache();
  try {
    assert.strictEqual(cache.getSearch('q1'), null, 'miss before set');

    const r = cache.setSearch('q1', 'RESULTS BODY');
    assert.deepStrictEqual(r, { ok: true });
    assert.strictEqual(cache.getSearch('q1'), 'RESULTS BODY');

    assert.strictEqual(cache.getSearch('different query'), null, 'distinct query → miss');
  } finally { cleanup(); }
});

test('setSearch: rejects empty query, getSearch: returns null for empty', () => {
  const { cache, cleanup } = freshCache();
  try {
    assert.strictEqual(cache.setSearch('   ', 'x').ok, false);
    assert.strictEqual(cache.getSearch(''), null);
    assert.strictEqual(cache.getSearch(null), null);
  } finally { cleanup(); }
});

test('search entries land in the "websearch" namespace, isolated from default', () => {
  const { cache, cleanup } = freshCache();
  try {
    cache.setSearch('q', 'search out');
    cache.set('https://example.com', 'p', 'fetch out');

    const ns = cache.stats({ namespace: cache.SEARCH_NAMESPACE });
    assert.strictEqual(ns.total, 1, 'one entry in websearch ns');

    const def = cache.stats(); // default namespace
    assert.strictEqual(def.total, 1, 'one entry in default ns');

    assert.ok(cache.listNamespaces().includes('websearch'));
  } finally { cleanup(); }
});

test('getEffectiveTtl: websearch host uses SEARCH_TTL (default 6h), not the default TTL', () => {
  const { cache, cleanup } = freshCache(); // no TTL env → default Infinity for normal URLs
  try {
    assert.strictEqual(cache.getEffectiveTtl(cache.searchUrl('x')), cache.SEARCH_TTL_MS);
    assert.strictEqual(cache.SEARCH_TTL_MS, 6 * 60 * 60 * 1000, 'default 6h');
    assert.strictEqual(cache.getEffectiveTtl('https://example.com'), Infinity,
      'normal URL keeps default TTL');
  } finally { cleanup(); }
});

test('WEBCACHE_SEARCH_TTL_HOURS overrides the search TTL', () => {
  const { cache, cleanup } = freshCache({ searchTtlHours: 2 });
  try {
    assert.strictEqual(cache.SEARCH_TTL_MS, 2 * 60 * 60 * 1000);
  } finally { cleanup(); }
});

test('search entries expire after their TTL and are then a miss', async () => {
  // 0.000001 h ≈ 3.6ms — expires almost immediately.
  const { cache, cleanup } = freshCache({ searchTtlHours: 0.000001 });
  try {
    cache.setSearch('soon stale', 'fresh results');
    await sleep(20);
    assert.strictEqual(cache.getSearch('soon stale'), null, 'expired search → miss');
  } finally { cleanup(); }
});

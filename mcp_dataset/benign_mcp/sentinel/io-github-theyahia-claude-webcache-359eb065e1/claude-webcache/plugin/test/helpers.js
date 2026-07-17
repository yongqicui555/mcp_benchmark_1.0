// Match production scripts: silence Node 22.5 node:sqlite ExperimentalWarning so
// test output stays readable. cache.js itself does not call removeAllListeners.
process.removeAllListeners('warning');

const os = require('node:os');
const path = require('node:path');
const fs = require('node:fs');
const crypto = require('node:crypto');

const CACHE_MODULE = require.resolve('../src/cache.js');

const ENV_KEYS = [
  'WEBCACHE_TTL_DAYS',
  'WEBCACHE_MAX_SIZE_MB',
  'WEBCACHE_DOMAIN_TTL',
  'WEBCACHE_NAMESPACE',
  'WEBCACHE_MAX_OUTPUT_MB',
  'WEBCACHE_COMPRESS',
  'WEBCACHE_STRICT_REDACT',
  'WEBCACHE_QUIET',
  'WEBCACHE_DEBUG',
  'WEBCACHE_SEARCH_TTL_HOURS',
  'WEBCACHE_AUTOREAD',
];

function snapshotEnv() {
  const snap = {};
  for (const k of ENV_KEYS) {
    snap[k] = Object.prototype.hasOwnProperty.call(process.env, k)
      ? { had: true, val: process.env[k] }
      : { had: false };
  }
  return snap;
}

function restoreEnv(snap) {
  for (const k of ENV_KEYS) {
    if (snap[k].had) process.env[k] = snap[k].val;
    else delete process.env[k];
  }
}

function setOrDelete(key, value) {
  if (value === undefined) delete process.env[key];
  else process.env[key] = String(value);
}

function applyEnv(opts) {
  setOrDelete('WEBCACHE_TTL_DAYS', opts.ttlDays);
  setOrDelete('WEBCACHE_MAX_SIZE_MB', opts.maxSizeMb);
  if (opts.domainTtl === undefined) delete process.env.WEBCACHE_DOMAIN_TTL;
  else process.env.WEBCACHE_DOMAIN_TTL = typeof opts.domainTtl === 'string' ? opts.domainTtl : JSON.stringify(opts.domainTtl);
  setOrDelete('WEBCACHE_NAMESPACE', opts.namespace);
  setOrDelete('WEBCACHE_MAX_OUTPUT_MB', opts.maxOutputMb);
  setOrDelete('WEBCACHE_COMPRESS', opts.compress === true ? '1' : opts.compress);
  setOrDelete('WEBCACHE_STRICT_REDACT', opts.strictRedact === true ? '1' : opts.strictRedact);
  setOrDelete('WEBCACHE_QUIET', opts.quiet === true ? '1' : opts.quiet);
  setOrDelete('WEBCACHE_DEBUG', opts.debug === true ? '1' : opts.debug);
  setOrDelete('WEBCACHE_SEARCH_TTL_HOURS', opts.searchTtlHours);
  setOrDelete('WEBCACHE_AUTOREAD', opts.autoread);
}

// cache.js bakes CACHE_DIR/DB_PATH/TTL_MS at module load from os.homedir() + env.
// To run tests against an isolated SQLite file, we monkey-patch os.homedir before
// freshly requiring cache.js, then restore afterwards.
function freshCache(opts = {}) {
  const tmpRoot = path.join(os.tmpdir(), `webcache-test-${crypto.randomUUID()}`);
  fs.mkdirSync(tmpRoot, { recursive: true });

  const origHome = os.homedir;
  const envSnap = snapshotEnv();

  os.homedir = () => tmpRoot;
  applyEnv(opts);

  delete require.cache[CACHE_MODULE];
  const cache = require(CACHE_MODULE);

  return {
    cache,
    tmpRoot,
    cleanup() {
      os.homedir = origHome;
      restoreEnv(envSnap);
      delete require.cache[CACHE_MODULE];
      // SQLite handle on Windows may keep the file locked briefly. force:true tries hard;
      // any residual leak ends up in os.tmpdir() which the OS sweeps periodically.
      try { fs.rmSync(tmpRoot, { recursive: true, force: true }); } catch {}
    },
  };
}

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

module.exports = { freshCache, sleep, ENV_KEYS };

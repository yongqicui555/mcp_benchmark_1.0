import { test } from 'node:test';
import assert from 'node:assert/strict';
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';

import { match } from '../src/match.mjs';
import { routeKey } from '../src/normalize.mjs';
import { extractRtkQuery } from '../src/adapters/rtk-query.mjs';
import { extractExpress } from '../src/adapters/express.mjs';
import { extractSpring } from '../src/adapters/spring.mjs';
import { extractFastapi } from '../src/adapters/fastapi.mjs';
import { extractAngularHttp } from '../src/adapters/angular-http.mjs';
import { extractAxiosFetch } from '../src/adapters/axios-fetch.mjs';
import { ROOT, ex } from './helpers.mjs';

const BIN = path.join(ROOT, 'bin', 'tieline.mjs');
const tieline = (args, cwd = ROOT) => spawnSync(process.execPath, [BIN, ...args], { cwd, encoding: 'utf8' });

// ---- the matcher is stack-agnostic (mix any client × any server) ---------

test('matcher: rtk-query client ↔ express server (MERN)', () => {
  const r = match(
    extractRtkQuery({ repoRoot: ROOT, roots: ['examples/express-fixture-client'] }),
    extractExpress({ repoRoot: ex('express-fixture'), roots: ['.'] }),
    { basePath: '/api/v1' },
  );
  assert.equal(r.totals.matched, 5);
  assert.equal(r.totals.drift, 2);
  assert.deepEqual(r.drift.map((d) => routeKey(d.method, d._np)).sort(), ['GET stats', 'PUT users/{}']);
});

test('matcher: angular-http client ↔ spring server (MEAN/enterprise, clean)', () => {
  const r = match(
    extractAngularHttp({ repoRoot: ex('angular-fixture'), roots: ['.'] }),
    extractSpring({ repoRoot: ex('spring-fixture'), roots: ['.'] }),
    { basePath: '' },
  );
  assert.equal(r.totals.matched, 4);
  assert.equal(r.totals.drift, 0);
});

test('matcher: axios-fetch client ↔ fastapi server (Python, drift)', () => {
  const r = match(
    extractAxiosFetch({ repoRoot: ex('axios-fixture'), roots: ['.'] }),
    extractFastapi({ repoRoot: ex('fastapi-fixture'), roots: ['.'] }),
    { basePath: '' },
  );
  assert.equal(r.totals.matched, 3);
  assert.equal(r.totals.drift, 3);
});

// ---- CLI behaviour (real process) ---------------------------------------

test('cli: `check` exits 1 when drift is present', () => {
  const r = tieline(['check', '--config', 'tieline.express.config.json']);
  assert.equal(r.status, 1);
  assert.match(r.stdout, /drift/);
});

test('cli: `--no-fail` always exits 0', () => {
  const r = tieline(['check', '--config', 'tieline.express.config.json', '--no-fail']);
  assert.equal(r.status, 0);
});

test('cli: `--json` emits parseable totals', () => {
  const r = tieline(['check', '--config', 'tieline.express.config.json', '--json', '--no-fail']);
  assert.equal(r.status, 0);
  const data = JSON.parse(r.stdout);
  assert.equal(data.totals.drift, 2);
  assert.equal(data.totals.matched, 5);
  assert.ok(Array.isArray(data.drift));
});

test('cli: `doctor` agrees when code and spec match (exit 0)', () => {
  const cfg = {
    server: {
      adapter: 'express',
      repo: ROOT,
      roots: ['examples/express-fixture'],
      globalPrefix: '',
      spec: ex('openapi-fixture/spec.json'),
    },
  };
  const cfgPath = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'tieline-cfg-')), 'tieline.config.json');
  fs.writeFileSync(cfgPath, JSON.stringify(cfg));
  try {
    const r = tieline(['doctor', '--config', cfgPath]);
    assert.equal(r.status, 0, r.stdout + r.stderr);
    assert.match(r.stdout, /0 undocumented/);
    assert.match(r.stdout, /0 phantom/);
  } finally {
    fs.rmSync(path.dirname(cfgPath), { recursive: true, force: true });
  }
});

test('cli: `--html` writes a self-contained report with the flow chart', () => {
  const out = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'tieline-html-')), 'report.html');
  try {
    const r = tieline(['check', '--config', 'tieline.express.config.json', '--no-fail', '--html', out]);
    assert.equal(r.status, 0);
    const html = fs.readFileSync(out, 'utf8');
    assert.match(html, /<!doctype html>/i);
    assert.match(html, /class="flowsvg"/); // the contract-flow SVG
    assert.match(html, /Contract flow/);
    assert.ok(!/<script src=|<link .*href=/.test(html), 'must be self-contained (no external assets)');
  } finally {
    fs.rmSync(path.dirname(out), { recursive: true, force: true });
  }
});

test('cli: unknown adapter fails with a clear message', () => {
  const cfgPath = path.join(fs.mkdtempSync(path.join(os.tmpdir(), 'tieline-cfg-')), 'tieline.config.json');
  fs.writeFileSync(cfgPath, JSON.stringify({ client: { adapter: 'nope' }, server: { adapter: 'express', repo: ROOT } }));
  try {
    const r = tieline(['check', '--config', cfgPath]);
    assert.equal(r.status, 2);
    assert.match(r.stderr, /Unknown client adapter/);
  } finally {
    fs.rmSync(path.dirname(cfgPath), { recursive: true, force: true });
  }
});

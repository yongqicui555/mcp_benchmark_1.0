import { test } from 'node:test';
import assert from 'node:assert/strict';

import { doctor } from '../src/doctor.mjs';
import { serverRoute } from './helpers.mjs';

test('doctor: agreeing routes count as matched', () => {
  const r = doctor([serverRoute('GET', 'users')], [serverRoute('GET', 'users')], {});
  assert.equal(r.totals.matched, 1);
  assert.equal(r.totals.undocumented, 0);
  assert.equal(r.totals.phantom, 0);
});

test('doctor: route in code but not in spec is undocumented', () => {
  const r = doctor([serverRoute('GET', 'premium/x')], [], {});
  assert.equal(r.totals.undocumented, 1);
  assert.equal(r.undocumented[0]._np, 'premium/x');
});

test('doctor: route in spec but not in code is phantom', () => {
  const r = doctor([], [serverRoute('POST', 'legacy/y')], {});
  assert.equal(r.totals.phantom, 1);
  assert.equal(r.phantom[0]._np, 'legacy/y');
});

test('doctor: method mismatch is reported on both sides with hints', () => {
  const r = doctor([serverRoute('GET', 'thing')], [serverRoute('POST', 'thing')], {});
  assert.equal(r.totals.undocumented, 1);
  assert.equal(r.totals.phantom, 1);
  assert.match(r.undocumented[0].hint, /in spec but only as POST/);
  assert.match(r.phantom[0].hint, /in code but only as GET/);
});

test('doctor: param syntaxes are normalized before comparing', () => {
  // Nest :id vs OpenAPI {id} should agree, not show as drift.
  const r = doctor([serverRoute('GET', 'users/:id')], [serverRoute('GET', 'users/{id}')], {});
  assert.equal(r.totals.matched, 1);
  assert.equal(r.totals.undocumented, 0);
});

test('doctor: ignore skips matching paths', () => {
  const r = doctor([serverRoute('GET', 'internal/metrics')], [], { ignore: ['^internal/'] });
  assert.equal(r.totals.undocumented, 0);
});

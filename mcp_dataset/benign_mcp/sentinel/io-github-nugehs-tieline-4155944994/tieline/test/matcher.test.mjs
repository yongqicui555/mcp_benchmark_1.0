import { test } from 'node:test';
import assert from 'node:assert/strict';

import { match } from '../src/match.mjs';
import { routeKey } from '../src/normalize.mjs';
import { clientEp, serverRoute } from './helpers.mjs';

test('matched: FE call resolving to an existing route', () => {
  const r = match([clientEp('GET', 'users')], [serverRoute('GET', 'users')], {});
  assert.equal(r.totals.matched, 1);
  assert.equal(r.totals.drift, 0);
});

test('drift: FE call with no backend route', () => {
  const r = match([clientEp('GET', 'widgets')], [serverRoute('GET', 'users')], {});
  assert.equal(r.totals.drift, 1);
  assert.equal(r.drift[0].hint, 'no matching backend route');
});

test('drift hint: method mismatch on an existing path', () => {
  const r = match([clientEp('POST', 'users')], [serverRoute('GET', 'users')], {});
  assert.equal(r.totals.drift, 1);
  assert.match(r.drift[0].hint, /as GET, not POST/);
});

test('drift hint: "did you mean" for a near path on the same segment', () => {
  const r = match([clientEp('GET', 'users/profil')], [serverRoute('GET', 'users/profile')], {});
  assert.equal(r.totals.drift, 1);
  assert.match(r.drift[0].hint, /did you mean "users\/profile"/);
});

test('drift hint: distant word on a shared prefix is NOT suggested ("status" != "search")', () => {
  const r = match([clientEp('GET', 'event-vendor/status')], [serverRoute('GET', 'event-vendor/search')], {});
  assert.equal(r.totals.drift, 1);
  assert.equal(r.drift[0].hint, 'no matching backend route');
});

test('drift hint: close segment edit is still suggested ("viewed" -> "view")', () => {
  const r = match([clientEp('POST', 'quotes/viewed')], [serverRoute('POST', 'quotes/view')], {});
  assert.equal(r.totals.drift, 1);
  assert.match(r.drift[0].hint, /did you mean "quotes\/view"/);
});

test('drift hint: param-shape mismatch is suggested (missing route param)', () => {
  const r = match([clientEp('GET', 'event/getEvent')], [serverRoute('GET', 'event/getEvent/:id')], {});
  assert.equal(r.totals.drift, 1);
  assert.match(r.drift[0].hint, /did you mean "event\/getEvent\/\{\}"/);
});

test('drift hint: missing prefix is suggested ("vendors" -> "recommendations/vendors")', () => {
  const r = match([clientEp('GET', 'vendors')], [serverRoute('GET', 'recommendations/vendors')], {});
  assert.equal(r.totals.drift, 1);
  assert.match(r.drift[0].hint, /did you mean "recommendations\/vendors"/);
});

test('drift hint: word-join across / and - ("contract-templates" -> "contracts/templates")', () => {
  const r = match([clientEp('GET', 'contract-templates')], [serverRoute('GET', 'contracts/templates')], {});
  assert.equal(r.totals.drift, 1);
  assert.match(r.drift[0].hint, /did you mean "contracts\/templates"/);
});

test('drift hint: wrong container prefix with distinctive tail is suggested', () => {
  const r = match(
    [clientEp('GET', 'bookings/ticket-sales-analysis/:id')],
    [serverRoute('GET', 'event/ticket-sales-analysis/:id')],
    {},
  );
  assert.equal(r.totals.drift, 1);
  assert.match(r.drift[0].hint, /did you mean "event\/ticket-sales-analysis\/\{\}"/);
});

test('unverifiable: endpoint flagged resolvable:false', () => {
  const r = match([clientEp('GET', null, false)], [], {});
  assert.equal(r.totals.unverifiable, 1);
  assert.equal(r.totals.drift, 0);
});

test('unverifiable: residual dynamic marker after normalize is not drift', () => {
  // A nested-template artifact like `blog/${q ? ...` keeps a `$` after normalize.
  const r = match([clientEp('GET', 'blog/${q')], [], {});
  assert.equal(r.totals.unverifiable, 1);
  assert.equal(r.totals.drift, 0);
});

test('dead: backend route no resolvable FE call reaches', () => {
  const r = match([clientEp('GET', 'users')], [serverRoute('GET', 'users'), serverRoute('GET', 'health')], {});
  assert.equal(r.totals.matched, 1);
  assert.equal(r.totals.dead, 1);
  assert.equal(r.dead[0]._np, 'health');
});

test('ignore: regex on normalized path skips matched + drift', () => {
  const r = match([clientEp('GET', 'internal/secret')], [], { ignore: ['^internal/'] });
  assert.equal(r.totals.drift, 0);
  assert.equal(r.totals.unverifiable, 0);
});

test('ALL/ANY server route matches any verb', () => {
  const r = match([clientEp('POST', 'webhook')], [serverRoute('ALL', 'webhook')], {});
  assert.equal(r.totals.matched, 1);
  assert.equal(r.totals.drift, 0);
});

test('basePath stripped on both sides before matching', () => {
  const r = match([clientEp('GET', 'users')], [serverRoute('GET', 'api/v1/users')], { basePath: '/api/v1' });
  assert.equal(r.totals.matched, 1);
});

test('param-position match: ${id} ↔ :id ↔ {id}', () => {
  const r = match([clientEp('DELETE', 'users/${id}')], [serverRoute('DELETE', 'users/:id')], {});
  assert.equal(r.totals.matched, 1);
  assert.deepEqual(
    [...new Set(r.matched.map((m) => routeKey(m.method, m._np)))],
    ['DELETE users/{}'],
  );
});

import { test } from 'node:test';
import assert from 'node:assert/strict';

import { normalizePath, joinPath, routeKey } from '../src/normalize.mjs';

test('normalizePath collapses every parameter syntax to {}', () => {
  assert.equal(normalizePath('bookings/${id}/confirm'), 'bookings/{}/confirm'); // JS template
  assert.equal(normalizePath('bookings/:id/confirm'), 'bookings/{}/confirm'); // Express/Nest
  assert.equal(normalizePath('users/<int:id>'), 'users/{}'); // Flask typed
  assert.equal(normalizePath('files/<path:p>'), 'files/{}'); // Flask path converter
  assert.equal(normalizePath('users/[id]'), 'users/{}'); // Next dynamic
  assert.equal(normalizePath('blog/[...slug]'), 'blog/{}'); // Next catch-all
  assert.equal(normalizePath('users/{id}/posts/{postId}'), 'users/{}/posts/{}'); // OpenAPI/Spring
});

test('normalizePath strips query strings, even templated ones', () => {
  assert.equal(normalizePath('confirm?bookingId=123'), 'confirm');
  assert.equal(normalizePath('confirm?bookingId=${id}'), 'confirm');
  // A templated param before the query must survive; the query is dropped.
  assert.equal(normalizePath('items/${id}?expand=true'), 'items/{}');
});

// Gnarly nested-template urls aren't fully resolvable here by design — they
// keep a residual marker and the matcher classifies them as `unverifiable`
// rather than guessing (see matcher.test.mjs).

test('normalizePath trims slashes and collapses doubles', () => {
  assert.equal(normalizePath('/users/'), 'users');
  assert.equal(normalizePath('users//posts'), 'users/posts');
  assert.equal(normalizePath(''), '');
  assert.equal(normalizePath(null), null);
});

test('normalizePath strips a configured basePath prefix', () => {
  assert.equal(normalizePath('/api/v1/users', { basePath: '/api/v1' }), 'users');
  assert.equal(normalizePath('api/v1/users/{id}', { basePath: 'api/v1' }), 'users/{}');
  assert.equal(normalizePath('users', { basePath: '/api/v1' }), 'users'); // no prefix present
  assert.equal(normalizePath('api/v1', { basePath: 'api/v1' }), ''); // exact prefix
});

test('joinPath composes segments and ignores empties/slashes', () => {
  assert.equal(joinPath('/api/', '/users/', ':id'), 'api/users/:id');
  assert.equal(joinPath('', 'users', ''), 'users');
  assert.equal(joinPath('users', '/'), 'users');
});

test('routeKey formats METHOD + path', () => {
  assert.equal(routeKey('get', 'users/{}'), 'GET users/{}');
});

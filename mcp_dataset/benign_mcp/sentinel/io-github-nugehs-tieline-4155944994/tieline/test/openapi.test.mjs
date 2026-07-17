import { test } from 'node:test';
import assert from 'node:assert/strict';

import { extractOpenapi } from '../src/adapters/openapi.mjs';
import { ex, assertRoutes, withTempRepo } from './helpers.mjs';

test('openapi: reads a committed OpenAPI 3 spec file', async () => {
  const routes = await extractOpenapi({ spec: 'spec.json', repoRoot: ex('openapi-fixture') });
  assertRoutes(assert, routes, [
    'GET health', 'GET status', 'POST status', 'GET api/v1/ping',
    'GET api/v1/users', 'POST api/v1/users', 'GET api/v1/users/{}', 'DELETE api/v1/users/{}',
  ]);
});

test('openapi: strips a path prefix declared in servers[].url', async () => {
  await withTempRepo(
    {
      'spec.json': JSON.stringify({
        openapi: '3.0.0',
        servers: [{ url: 'http://localhost:9999/api/v1' }],
        paths: { '/users': { get: {} }, '/users/{id}': { get: {}, delete: {} } },
      }),
    },
    async (dir) => {
      assertRoutes(assert, await extractOpenapi({ spec: 'spec.json', repoRoot: dir }), [
        'GET users', 'GET users/{}', 'DELETE users/{}',
      ]);
    },
  );
});

test('openapi: honours Swagger 2 basePath', async () => {
  await withTempRepo(
    {
      'spec.json': JSON.stringify({ swagger: '2.0', basePath: '/api', paths: { '/x': { get: {} } } }),
    },
    async (dir) => {
      assertRoutes(assert, await extractOpenapi({ spec: 'spec.json', repoRoot: dir }), ['GET x']);
    },
  );
});

test('openapi: config stripPrefix removes a baked-in global prefix', async () => {
  await withTempRepo(
    {
      'spec.json': JSON.stringify({ openapi: '3.0.0', paths: { '/api/v1/orders': { post: {} } } }),
    },
    async (dir) => {
      assertRoutes(
        assert,
        await extractOpenapi({ spec: 'spec.json', repoRoot: dir, stripPrefix: 'api/v1' }),
        ['POST orders'],
      );
    },
  );
});

test('openapi: a missing spec path raises a clear error', async () => {
  await assert.rejects(() => extractOpenapi({ spec: 'nope.json', repoRoot: ex('openapi-fixture') }));
});

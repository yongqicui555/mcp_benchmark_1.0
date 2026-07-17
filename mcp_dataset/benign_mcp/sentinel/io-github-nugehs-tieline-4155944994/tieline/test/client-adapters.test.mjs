import { test } from 'node:test';
import assert from 'node:assert/strict';

import { extractRtkQuery } from '../src/adapters/rtk-query.mjs';
import { extractAxiosFetch } from '../src/adapters/axios-fetch.mjs';
import { extractAngularHttp } from '../src/adapters/angular-http.mjs';
import { ex, assertRoutes, withTempRepo, keySet } from './helpers.mjs';

// ---- fixture-level -------------------------------------------------------

test('axios-fetch: axios.get / axios({}) / fetch forms', () => {
  assertRoutes(assert, extractAxiosFetch({ repoRoot: ex('axios-fixture'), roots: ['.'] }), [
    'GET api/users', 'POST api/users', 'GET api/users/{}', 'DELETE api/users/{}', 'GET api/ping', 'PUT api/users/{}',
  ]);
});

test('angular-http: this.http.get<T>() service calls', () => {
  assertRoutes(assert, extractAngularHttp({ repoRoot: ex('angular-fixture'), roots: ['.'] }), [
    'GET api/users', 'POST api/users', 'GET api/users/{}', 'DELETE api/users/{}',
  ]);
});

// ---- rtk-query forms + honesty ------------------------------------------

test('rtk-query: string/template/object url forms and method defaults', () => {
  withTempRepo(
    {
      'api.ts': `import { createApi } from '@reduxjs/toolkit/query/react';
export const api = createApi({ reducerPath:'a', baseQuery:()=>({data:null}), endpoints:(builder)=>({
  list: builder.query({ query: () => 'users' }),
  one: builder.query({ query: (id) => \`users/\${id}\` }),
  make: builder.mutation({ query: (b) => ({ url: 'users', method: 'POST', body: b }) }),
  defaultGet: builder.mutation({ query: (b) => ({ url: 'ping' }) }),
}) });`,
    },
    (dir) => {
      assertRoutes(assert, extractRtkQuery({ repoRoot: dir, roots: ['.'] }), [
        'GET users', 'GET users/{}', 'POST users', 'GET ping',
      ]);
    },
  );
});

test('rtk-query: a runtime-built url is emitted resolvable:false', () => {
  withTempRepo(
    {
      'api.ts': `import { createApi } from '@reduxjs/toolkit/query/react';
export const api = createApi({ reducerPath:'a', baseQuery:()=>({data:null}), endpoints:(builder)=>({
  dyn: builder.query({ query: (arg) => ({ url: arg.path, method: 'GET' }) }),
}) });`,
    },
    (dir) => {
      const eps = extractRtkQuery({ repoRoot: dir, roots: ['.'] });
      assert.equal(eps.length, 1);
      assert.equal(eps[0].resolvable, false);
    },
  );
});

// ---- axios/angular edge cases -------------------------------------------

test('axios-fetch: fetch defaults to GET; instance idents work', () => {
  withTempRepo(
    { 'api.ts': `const api = makeClient();
api.put('/widgets', {});
fetch('/things');` },
    (dir) => {
      const k = keySet(extractAxiosFetch({ repoRoot: dir, roots: ['.'] }));
      assert.ok(k.has('PUT widgets'), 'instance .put() captured');
      assert.ok(k.has('GET things'), 'fetch() defaults to GET');
    },
  );
});

test('angular-http: a non-HttpClient .get() is ignored', () => {
  withTempRepo(
    { 'svc.ts': `const map = new Map();
map.get('not-a-route');
this.http.get('/api/real');` },
    (dir) => {
      const k = keySet(extractAngularHttp({ repoRoot: dir, roots: ['.'] }));
      assert.ok(k.has('GET api/real'));
      assert.equal(k.size, 1, 'map.get(...) must not be treated as an HTTP call');
    },
  );
});

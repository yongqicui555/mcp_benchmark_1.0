import { test } from 'node:test';
import assert from 'node:assert/strict';

import { extractExpress } from '../src/adapters/express.mjs';
import { extractFastify } from '../src/adapters/fastify.mjs';
import { extractNext } from '../src/adapters/next.mjs';
import { extractFastapi } from '../src/adapters/fastapi.mjs';
import { extractFlask } from '../src/adapters/flask.mjs';
import { extractSpring } from '../src/adapters/spring.mjs';
import { ex, assertRoutes, withTempRepo, keySet } from './helpers.mjs';

// ---- fixture-level (full resolution) ------------------------------------

test('express: resolves the mount graph across files', () => {
  assertRoutes(assert, extractExpress({ repoRoot: ex('express-fixture'), roots: ['.'] }), [
    'GET health', 'GET status', 'POST status', 'GET api/v1/ping',
    'GET api/v1/users', 'POST api/v1/users', 'GET api/v1/users/{}', 'DELETE api/v1/users/{}',
  ]);
});

test('fastify: verb shorthand + route({ method, url })', () => {
  assertRoutes(assert, extractFastify({ repoRoot: ex('fastify-fixture'), roots: ['.'] }), [
    'GET health', 'POST users', 'GET users/{}', 'DELETE users/{}', 'PUT users/{}', 'PATCH users/{}',
  ]);
});

test('next: app-router method exports + pages-router ALL', () => {
  assertRoutes(assert, extractNext({ repoRoot: ex('next-fixture'), roots: ['.'] }), [
    'GET api/users', 'POST api/users', 'GET api/users/{}', 'DELETE api/users/{}', 'ALL api/legacy/{}',
  ]);
});

test('fastapi: APIRouter(prefix) + include_router(prefix)', () => {
  assertRoutes(assert, extractFastapi({ repoRoot: ex('fastapi-fixture'), roots: ['.'] }), [
    'GET health', 'GET api/users', 'GET api/users/{}', 'POST api/users',
  ]);
});

test('flask: blueprint url_prefix + methods=[]', () => {
  assertRoutes(assert, extractFlask({ repoRoot: ex('flask-fixture'), roots: ['.'] }), [
    'GET health', 'GET api/users', 'POST api/users', 'DELETE api/users/{}',
  ]);
});

test('spring: @RequestMapping base + @*Mapping', () => {
  assertRoutes(assert, extractSpring({ repoRoot: ex('spring-fixture'), roots: ['.'] }), [
    'GET api/users', 'GET api/users/{}', 'POST api/users', 'DELETE api/users/{}',
  ]);
});

// ---- edge cases ----------------------------------------------------------

test('express: app.all → ALL, and a router never mounted is flagged', () => {
  withTempRepo(
    {
      'app.js': `const express=require('express');const app=express();
const orphan=express.Router();
orphan.get('/lonely', ()=>{});
app.all('/any', ()=>{});
module.exports=app;`,
    },
    (dir) => {
      const routes = extractExpress({ repoRoot: dir, roots: ['.'] });
      assert.ok(keySet(routes).has('ALL any'));
      const orphan = routes.find((r) => r.rawPath === 'lonely');
      assert.ok(orphan, 'unmounted router route should still be emitted');
      assert.equal(orphan.unresolvedMount, true);
    },
  );
});

test('next: route groups (group) and catch-all are handled', () => {
  withTempRepo(
    {
      'src/app/(marketing)/api/leads/route.ts': `export async function POST(){}`,
      'src/app/api/files/[...path]/route.ts': `export async function GET(){}`,
    },
    (dir) => {
      const k = keySet(extractNext({ repoRoot: dir, roots: ['.'] }));
      assert.ok(k.has('POST api/leads'), 'route group must be stripped from the URL');
      assert.ok(k.has('GET api/files/{}'), 'catch-all becomes a param');
    },
  );
});

test('spring: method-level @RequestMapping(method = RequestMethod.X)', () => {
  withTempRepo(
    {
      'Ctrl.java': `@RestController @RequestMapping("/orders") public class Ctrl {
  @RequestMapping(value="/{id}", method=RequestMethod.PUT) public void update(){}
}`,
    },
    (dir) => {
      assert.ok(keySet(extractSpring({ repoRoot: dir, roots: ['.'] })).has('PUT orders/{}'));
    },
  );
});

test('flask: a route without methods= defaults to GET', () => {
  withTempRepo(
    { 'app.py': `from flask import Flask\napp=Flask(__name__)\n@app.route("/ping")\ndef ping(): return "ok"\n` },
    (dir) => {
      assertRoutes(assert, extractFlask({ repoRoot: dir, roots: ['.'] }), ['GET ping']);
    },
  );
});

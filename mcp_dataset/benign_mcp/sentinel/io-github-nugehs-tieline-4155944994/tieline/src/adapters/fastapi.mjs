import fs from 'node:fs';
import path from 'node:path';

import { walk, lineAt } from '../util/walk.mjs';
import { joinPath } from '../normalize.mjs';

/**
 * Server adapter for FastAPI (Python).
 *
 * Resolves `APIRouter(prefix=...)` and `app.include_router(router, prefix=...)`
 * so a route declared `@router.get("/{id}")` on a router with prefix `/users`
 * included under `/api` becomes `/api/users/{id}`. Prefix composition mirrors
 * the Express mount graph but over Python's include_router calls (within a file).
 */
const VERBS = 'get|post|put|patch|delete|head|options';

export function extractFastapi(cfg) {
  const roots = cfg.roots && cfg.roots.length ? cfg.roots : ['.'];
  const files = roots.flatMap((r) => walk(path.resolve(cfg.repoRoot, r), (n) => n.endsWith('.py')));

  // Aggregate across files (FastAPI apps commonly span modules).
  const routerPrefix = new Map(); // var -> its own APIRouter(prefix=)
  const routes = []; // { owner, method, path, file, line }
  const includes = []; // { host, child, prefix }
  const appVars = new Set();

  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');
    for (const m of text.matchAll(/(\w+)\s*=\s*APIRouter\s*\(([^)]*)\)/g)) {
      routerPrefix.set(m[1], prefixArg(m[2]));
    }
    for (const m of text.matchAll(/(\w+)\s*=\s*FastAPI\s*\(/g)) appVars.add(m[1]);
    for (const m of text.matchAll(new RegExp(`@(\\w+)\\.(${VERBS})\\s*\\(\\s*(['"])([^'"]*)\\3`, 'gi'))) {
      routes.push({ owner: m[1], method: m[2].toUpperCase(), path: m[4], file, line: lineAt(text, m.index) });
    }
    for (const m of text.matchAll(/(\w+)\.include_router\s*\(\s*(\w+)(?:\.\w+)?([^)]*)\)/g)) {
      includes.push({ host: m[1], child: m[2], prefix: prefixArg(m[3]) });
    }
  }

  // Compose: app (prefix '') -> included routers -> their routes.
  const out = [];
  const visited = new Set();
  const emitRouter = (rv, accum) => {
    if (visited.has(rv)) return; // also guards include cycles
    visited.add(rv);
    const here = joinPath(accum, routerPrefix.get(rv) || '');
    for (const r of routes) if (r.owner === rv) out.push(mk(r.method, joinPath(here, r.path), r.file, r.line));
    for (const inc of includes) if (inc.host === rv) emitRouter(inc.child, joinPath(here, inc.prefix));
  };
  for (const app of appVars) {
    visited.add(app);
    for (const r of routes) if (r.owner === app) out.push(mk(r.method, r.path, r.file, r.line));
    for (const inc of includes) if (inc.host === app) emitRouter(inc.child, inc.prefix);
  }
  // Routers never reached from an app still expose their routes (relative).
  for (const r of routes) {
    if (visited.has(r.owner)) continue;
    out.push(mk(r.method, joinPath(routerPrefix.get(r.owner) || '', r.path), r.file, r.line));
  }
  return dedupe(out);
}

function prefixArg(args) {
  const m = String(args || '').match(/prefix\s*=\s*['"]([^'"]*)['"]/);
  return m ? m[1] : '';
}

const mk = (method, rawPath, file, line) => ({ side: 'server', method, rawPath, file, line });

function dedupe(routes) {
  const seen = new Set();
  return routes.filter((r) => {
    const k = r.method + ' ' + r.rawPath;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

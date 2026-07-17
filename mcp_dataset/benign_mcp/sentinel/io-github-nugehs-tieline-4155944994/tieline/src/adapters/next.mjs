import fs from 'node:fs';
import path from 'node:path';

import { walk, lineAt } from '../util/walk.mjs';
import { joinPath } from '../normalize.mjs';

/**
 * Server adapter for Next.js — routing is file-system based, not code based.
 *
 *   App Router:   app/api/users/[id]/route.ts  exporting GET/POST/...  ->  /api/users/:id
 *   Pages Router: pages/api/users/[id].ts       (one handler, any verb) ->  /api/users/:id (ALL)
 *
 * Dynamic segments `[id]` / catch-all `[...slug]` become params; route groups
 * `(group)` and parallel `@slot` segments are stripped (they don't affect URLs).
 */
const HTTP_FNS = ['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'HEAD', 'OPTIONS'];

export function extractNext(cfg) {
  const roots = cfg.roots && cfg.roots.length ? cfg.roots : ['.'];
  const out = [];
  for (const r of roots) {
    const base = path.resolve(cfg.repoRoot, r);
    for (const file of walk(base, (n) => /\.(js|ts|jsx|tsx)$/.test(n))) {
      const rel = path.relative(base, file).split(path.sep);
      if (isAppRouteFile(rel)) out.push(...appRoute(file, rel));
      else if (isPagesApiFile(rel)) out.push(...pagesRoute(file, rel));
    }
  }
  return out;
}

// app/.../route.ts (optionally nested under src/)
function isAppRouteFile(rel) {
  return rel.includes('app') && /^route\.(js|ts|jsx|tsx)$/.test(rel[rel.length - 1]);
}

function isPagesApiFile(rel) {
  const i = rel.indexOf('pages');
  return i !== -1 && rel[i + 1] === 'api';
}

function appRoute(file, rel) {
  const i = rel.indexOf('app');
  const segs = rel.slice(i + 1, -1); // between 'app' and 'route.ext'
  const urlPath = segsToPath(segs);
  const text = fs.readFileSync(file, 'utf8');
  const methods = HTTP_FNS.filter((fn) =>
    new RegExp(`export\\s+(?:async\\s+)?function\\s+${fn}\\b`).test(text) ||
    new RegExp(`export\\s+const\\s+${fn}\\b`).test(text),
  );
  return methods.map((m) => mk(m, urlPath, file, 1));
}

function pagesRoute(file, rel) {
  const i = rel.indexOf('pages');
  let segs = rel.slice(i + 1); // includes 'api', ends with file
  const last = segs.pop().replace(/\.(js|ts|jsx|tsx)$/, '');
  if (last !== 'index') segs.push(last);
  return [mk('ALL', segsToPath(segs), file, 1)];
}

// Convert path segments to a URL, dropping route groups/parallel slots.
function segsToPath(segs) {
  const clean = segs
    .filter((s) => !/^\(.*\)$/.test(s) && !s.startsWith('@'))
    .map((s) => s.replace(/^\[\.\.\.(.+)\]$/, ':$1').replace(/^\[(.+)\]$/, ':$1'));
  return joinPath(...clean);
}

const mk = (method, rawPath, file, line) => ({ side: 'server', method, rawPath, file, line });

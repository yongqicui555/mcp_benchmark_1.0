import fs from 'node:fs';
import path from 'node:path';

import { walk, lineAt } from '../util/walk.mjs';

/**
 * Client adapter for raw axios / fetch call sites (React, Vue, vanilla — and
 * the inside of React Query / SWR `queryFn`s, which are just fetch/axios).
 *
 *   axios.get('/users')                     -> GET /users
 *   api.post('/users', body)                -> POST /users   (any instance ident)
 *   axios({ url: '/users', method: 'put' }) -> PUT /users
 *   fetch('/users', { method: 'DELETE' })   -> DELETE /users
 *   fetch(`/users/${id}`)                   -> GET /users/{}
 *
 * Calls whose url isn't a string literal are emitted resolvable:false
 * (unverifiable) — this is the imperative-stack case the bucket exists for.
 */
const VERBS = 'get|post|put|patch|delete|head|options';

export function extractAxiosFetch(cfg) {
  const roots = cfg.roots && cfg.roots.length ? cfg.roots : ['.'];
  const files = roots.flatMap((r) =>
    walk(path.resolve(cfg.repoRoot, r), (n) => /\.(js|ts|jsx|tsx|vue|mjs)$/.test(n) && !/\.(spec|test|d)\.[jt]sx?$/.test(n)),
  );

  const out = [];
  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');

    // <ident>.get('url' | `url`, ...)
    for (const m of text.matchAll(new RegExp(`\\b(\\w+)\\.(${VERBS})\\s*\\(\\s*(['"\`])([^'"\`]*)\\3`, 'gi'))) {
      out.push(ep(`${m[1]}.${m[2]}`, m[2].toUpperCase(), m[4], file, lineAt(text, m.index)));
    }
    // axios({ url, method }) / api.request({ url, method })
    for (const m of text.matchAll(/\b(?:axios|request)\s*\(\s*\{([\s\S]*?)\}\s*\)/g)) {
      const body = m[1];
      const url = body.match(/url\s*:\s*(['"`])([^'"`]*)\1/);
      if (!url) continue;
      const method = body.match(/method\s*:\s*(['"`])(\w+)\1/);
      out.push(ep('axios', (method ? method[2] : 'get').toUpperCase(), url[2], file, lineAt(text, m.index)));
    }
    // fetch('url', { method }) — default GET
    for (const m of text.matchAll(/\bfetch\s*\(\s*(['"`])([^'"`]*)\1\s*(?:,\s*\{([\s\S]*?)\})?\s*\)/g)) {
      const method = (m[3] || '').match(/method\s*:\s*(['"`])(\w+)\1/);
      out.push(ep('fetch', (method ? method[2] : 'GET').toUpperCase(), m[2], file, lineAt(text, m.index)));
    }
  }
  return out;
}

function ep(name, method, rawPath, file, line) {
  // Bare/relative-only or non-path strings (no slash, not a known route) are kept
  // but flagged; the matcher reports residual dynamic markers as unverifiable.
  return { side: 'client', name, method, rawPath, resolvable: rawPath != null, file, line };
}

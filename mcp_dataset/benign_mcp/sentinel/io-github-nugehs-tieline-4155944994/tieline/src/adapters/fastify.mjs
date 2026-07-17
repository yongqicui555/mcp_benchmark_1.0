import fs from 'node:fs';
import path from 'node:path';

import { walk, lineAt } from '../util/walk.mjs';

/**
 * Server adapter for Fastify. Handles the shorthand verb form
 * `fastify.get('/x', ...)` and the full `app.route({ method, url })` form
 * (method may be a string or an array).
 *
 * Note: plugin `register(plugin, { prefix })` prefixes are not yet resolved
 * across files — routes are emitted at their declared paths. (Roadmap.)
 */
const VERBS = 'get|post|put|patch|delete|head|options|all';

export function extractFastify(cfg) {
  const roots = cfg.roots && cfg.roots.length ? cfg.roots : ['.'];
  const files = roots.flatMap((r) =>
    walk(path.resolve(cfg.repoRoot, r), (n) => /\.(js|ts|mjs)$/.test(n) && !/\.(spec|test|d)\.[jt]s$/.test(n)),
  );
  const out = [];
  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');

    for (const m of text.matchAll(new RegExp(`\\w+\\.(${VERBS})\\s*\\(\\s*(['"\`])([^'"\`]*)\\2`, 'gi'))) {
      out.push(route(m[1].toUpperCase(), m[3], file, lineAt(text, m.index)));
    }
    // app.route({ method: 'GET' | ['GET','POST'], url: '/x' })
    for (const m of text.matchAll(/\.route\s*\(\s*\{([\s\S]*?)\}\s*\)/g)) {
      const body = m[1];
      const url = body.match(/url\s*:\s*(['"`])([^'"`]*)\1/);
      if (!url) continue;
      const methods = [...body.matchAll(/(['"`])(GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)\1/gi)].map((x) => x[2].toUpperCase());
      for (const method of methods.length ? methods : ['GET']) {
        out.push(route(method, url[2], file, lineAt(text, m.index)));
      }
    }
  }
  return dedupe(out);
}

const route = (method, rawPath, file, line) => ({ side: 'server', method, rawPath, file, line });

function dedupe(routes) {
  const seen = new Set();
  return routes.filter((r) => {
    const k = r.method + ' ' + r.rawPath;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

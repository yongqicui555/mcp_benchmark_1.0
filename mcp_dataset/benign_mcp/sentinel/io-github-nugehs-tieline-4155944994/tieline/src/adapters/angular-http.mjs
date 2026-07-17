import fs from 'node:fs';
import path from 'node:path';

import { walk, lineAt } from '../util/walk.mjs';

/**
 * Client adapter for Angular's HttpClient (the MEAN frontend).
 *
 *   this.http.get<User[]>('/api/users')           -> GET /api/users
 *   this.http.post('/api/users', body)            -> POST /api/users
 *   this.http.delete(`/api/users/${id}`)          -> DELETE /api/users/{}
 *
 * Angular concentrates calls in injectable services, so static yield is high.
 * The optional `<Generic>` between the method and `(` is tolerated.
 */
const VERBS = 'get|post|put|patch|delete|head|options';

export function extractAngularHttp(cfg) {
  const roots = cfg.roots && cfg.roots.length ? cfg.roots : ['.'];
  const files = roots.flatMap((r) =>
    walk(path.resolve(cfg.repoRoot, r), (n) => /\.ts$/.test(n) && !/\.(spec|d)\.ts$/.test(n)),
  );

  const out = [];
  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');
    // <ident>.http?.<verb><Generic?>('url' | `url`, ...)  — covers this.http / http / this.client
    const re = new RegExp(`\\.(${VERBS})\\s*(?:<[^>(]*>)?\\s*\\(\\s*(['"\`])([^'"\`]*)\\2`, 'gi');
    for (const m of text.matchAll(re)) {
      // Require the call to look like an HttpClient call (preceded by http/client/api ident).
      const pre = text.slice(Math.max(0, m.index - 24), m.index);
      if (!/(http|client|api|httpClient)\s*$/i.test(pre)) continue;
      out.push({
        side: 'client',
        name: `${m[1]}:${m[3]}`,
        method: m[1].toUpperCase(),
        rawPath: m[3],
        resolvable: true,
        file,
        line: lineAt(text, m.index),
      });
    }
  }
  return out;
}

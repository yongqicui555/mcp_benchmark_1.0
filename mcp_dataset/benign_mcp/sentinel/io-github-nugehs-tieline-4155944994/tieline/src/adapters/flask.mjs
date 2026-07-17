import fs from 'node:fs';
import path from 'node:path';

import { walk, lineAt } from '../util/walk.mjs';
import { joinPath } from '../normalize.mjs';

/**
 * Server adapter for Flask (Python).
 *
 * Handles `@app.route("/x", methods=["GET","POST"])` and blueprints:
 * `bp = Blueprint("x", __name__, url_prefix="/api")` plus
 * `app.register_blueprint(bp, url_prefix="/api")`. A route with no `methods=`
 * defaults to GET (Flask also adds HEAD/OPTIONS, which we ignore for matching).
 */
export function extractFlask(cfg) {
  const roots = cfg.roots && cfg.roots.length ? cfg.roots : ['.'];
  const files = roots.flatMap((r) => walk(path.resolve(cfg.repoRoot, r), (n) => n.endsWith('.py')));

  const prefix = new Map(); // blueprint var -> url_prefix
  const routes = []; // { owner, methods[], path, file, line }

  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');
    for (const m of text.matchAll(/(\w+)\s*=\s*Blueprint\s*\(([^)]*)\)/g)) {
      const p = m[2].match(/url_prefix\s*=\s*['"]([^'"]*)['"]/);
      if (p) prefix.set(m[1], p[1]);
    }
    for (const m of text.matchAll(/\w+\.register_blueprint\s*\(\s*(\w+)([^)]*)\)/g)) {
      const p = m[2].match(/url_prefix\s*=\s*['"]([^'"]*)['"]/);
      if (p) prefix.set(m[1], joinPath(p[1], prefix.get(m[1]) || ''));
    }
    // @app.route("/x", methods=[...])  /  @bp.route("/x")
    for (const m of text.matchAll(/@(\w+)\.route\s*\(\s*(['"])([^'"]*)\2([^)]*)\)/g)) {
      const methods = [...m[4].matchAll(/['"](GET|POST|PUT|PATCH|DELETE|HEAD|OPTIONS)['"]/gi)].map((x) => x[1].toUpperCase());
      routes.push({ owner: m[1], methods: methods.length ? methods : ['GET'], path: m[3], file, line: lineAt(text, m.index) });
    }
  }

  const out = [];
  for (const r of routes) {
    const full = joinPath(prefix.get(r.owner) || '', r.path);
    for (const method of r.methods) out.push({ side: 'server', method, rawPath: full, file: r.file, line: r.line });
  }
  return dedupe(out);
}

function dedupe(routes) {
  const seen = new Set();
  return routes.filter((r) => {
    const k = r.method + ' ' + r.rawPath;
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

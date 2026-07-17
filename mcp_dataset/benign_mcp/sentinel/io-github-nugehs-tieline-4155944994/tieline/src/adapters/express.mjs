import fs from 'node:fs';
import path from 'node:path';

import { walk, lineAt } from '../util/walk.mjs';
import { joinPath } from '../normalize.mjs';

/**
 * Native server adapter for Express — the backend of MERN / MEAN / MEVN.
 *
 * Express routing is imperative: a path is assembled at runtime from `app.use`
 * mount prefixes, often across files. So this adapter does two things:
 *   1. parse each file into a descriptor (router vars, routes, mounts, imports)
 *   2. walk the mount graph from every `express()` app to compose full paths,
 *      following `require`/`import` across files and nesting prefixes.
 *
 * Routers that are never reachable from an app are still emitted with their
 * relative paths and flagged `unresolvedMount` — surfaced, never silently
 * dropped (honesty over false confidence).
 *
 * Config: { "adapter": "express", "repo": "../app", "roots": ["src"], "entry": "app.js"? }
 */
const VERBS = 'get|post|put|patch|delete|options|head|all';

export function extractExpress(cfg) {
  const repoRoot = path.resolve(cfg.repoRoot); // absolute, so file keys match resolved imports
  const roots = cfg.roots && cfg.roots.length ? cfg.roots : ['.'];
  const files = roots.flatMap((r) =>
    walk(
      path.resolve(repoRoot, r),
      (n) => (n.endsWith('.js') || n.endsWith('.ts')) && !/\.(spec|test|d)\.[jt]s$/.test(n),
    ),
  );

  const fileMap = new Map();
  for (const f of files) fileMap.set(f, parseFile(fs.readFileSync(f, 'utf8'), f));

  return resolve(fileMap);
}

// ---- per-file extraction -------------------------------------------------

function parseFile(text, file) {
  const routerVars = new Set();
  const appVars = new Set();
  const imports = new Map(); // localName -> resolved abs path

  for (const m of text.matchAll(/(?:const|let|var)\s+(\w+)\s*=\s*(?:express\.Router|Router)\s*\(/g))
    routerVars.add(m[1]);
  for (const m of text.matchAll(/(?:const|let|var)\s+(\w+)\s*=\s*express\s*\(\s*\)/g)) appVars.add(m[1]);

  for (const m of text.matchAll(/(?:const|let|var)\s+(\w+)\s*=\s*require\(\s*['"]([^'"]+)['"]\s*\)/g)) {
    const r = resolveImport(file, m[2]);
    if (r) imports.set(m[1], r);
  }
  for (const m of text.matchAll(/import\s+(\w+)\s+from\s+['"]([^'"]+)['"]/g)) {
    const r = resolveImport(file, m[2]);
    if (r) imports.set(m[1], r);
  }

  // Direct route calls: VAR.get('path', ...)
  const routes = [];
  for (const m of text.matchAll(new RegExp(`(\\w+)\\.(${VERBS})\\s*\\(\\s*(['"\`])([^'"\`]*)\\3`, 'gi'))) {
    routes.push({ owner: m[1], method: m[2].toUpperCase(), path: m[4], line: lineAt(text, m.index) });
  }
  // Chained: VAR.route('path').get(...).post(...)
  for (const m of text.matchAll(new RegExp(`(\\w+)\\.route\\(\\s*(['"\`])([^'"\`]*)\\2\\s*\\)`, 'g'))) {
    const owner = m[1];
    const p = m[3];
    const line = lineAt(text, m.index);
    const tail = text.slice(m.index + m[0].length, m.index + m[0].length + 400).split(';')[0];
    for (const v of tail.matchAll(new RegExp(`\\.\\s*(${VERBS})\\s*\\(`, 'gi'))) {
      routes.push({ owner, method: v[1].toUpperCase(), path: p, line });
    }
  }

  // Mounts: VAR.use('/prefix', target)  and  VAR.use(target)
  const mounts = [];
  for (const m of text.matchAll(/(\w+)\.use\s*\(\s*(['"`])([^'"`]*)\2\s*,\s*(\w+)\s*\)/g))
    mounts.push({ host: m[1], prefix: m[3], target: m[4], line: lineAt(text, m.index) });
  for (const m of text.matchAll(/(\w+)\.use\s*\(\s*(\w+)\s*\)/g))
    mounts.push({ host: m[1], prefix: '', target: m[2], line: lineAt(text, m.index) });

  const exp = text.match(/module\.exports\s*=\s*(\w+)/) || text.match(/export\s+default\s+(\w+)/);
  return { file, routerVars, appVars, imports, routes, mounts, exported: exp ? exp[1] : null };
}

function resolveImport(fromFile, spec) {
  if (!spec.startsWith('.')) return null; // package import, not a local router
  const base = path.resolve(path.dirname(fromFile), spec);
  const candidates = [base, base + '.js', base + '.ts', path.join(base, 'index.js'), path.join(base, 'index.ts')];
  return candidates.find((c) => fs.existsSync(c) && fs.statSync(c).isFile()) || null;
}

// ---- mount-graph resolution ---------------------------------------------

function resolve(fileMap) {
  const out = [];
  const resolvedKeys = new Set();

  const visit = (file, varName, prefix, seen) => {
    const desc = fileMap.get(file);
    if (!desc) return;
    const key = file + '#' + varName;
    if (seen.has(key)) return; // guard against mount cycles
    seen.add(key);
    resolvedKeys.add(key);

    for (const r of desc.routes) {
      if (r.owner !== varName) continue;
      out.push(route(r.method, joinPath(prefix, r.path), file, r.line));
    }
    for (const mt of desc.mounts) {
      if (mt.host !== varName) continue;
      const next = joinPath(prefix, mt.prefix);
      if (desc.routerVars.has(mt.target)) {
        visit(file, mt.target, next, seen);
      } else if (desc.imports.has(mt.target)) {
        const tfile = desc.imports.get(mt.target);
        const tdesc = fileMap.get(tfile);
        if (tdesc && tdesc.exported) visit(tfile, tdesc.exported, next, seen);
      }
    }
  };

  // Start from every app = express() across the codebase.
  for (const [file, desc] of fileMap) {
    for (const app of desc.appVars) visit(file, app, '', new Set());
  }

  // Emit any router with routes that the graph never reached — relative, flagged.
  for (const [file, desc] of fileMap) {
    const owners = new Set(desc.routes.map((r) => r.owner));
    for (const owner of owners) {
      if (desc.appVars.has(owner)) continue;
      if (resolvedKeys.has(file + '#' + owner)) continue;
      for (const r of desc.routes) {
        if (r.owner === owner) out.push(route(r.method, joinPath(r.path), file, r.line, true));
      }
    }
  }

  return dedupe(out);
}

function route(method, rawPath, file, line, unresolvedMount = false) {
  return { side: 'server', method, rawPath, file, line, unresolvedMount };
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

import fs from 'node:fs';
import path from 'node:path';

import { walk, lineAt } from '../util/walk.mjs';
import { joinPath } from '../normalize.mjs';

/**
 * Server adapter for Spring (Java/Kotlin).
 *
 * Reads the class-level `@RequestMapping("/api/users")` base and method-level
 * `@GetMapping`, `@PostMapping`, … (or `@RequestMapping(method=...)`). The path
 * may be a bare string or in `value=` / `path=`. One controller per file.
 */
const SHORTHAND = { GetMapping: 'GET', PostMapping: 'POST', PutMapping: 'PUT', PatchMapping: 'PATCH', DeleteMapping: 'DELETE' };

export function extractSpring(cfg) {
  const roots = cfg.roots && cfg.roots.length ? cfg.roots : ['.'];
  const files = roots.flatMap((r) => walk(path.resolve(cfg.repoRoot, r), (n) => /\.(java|kt)$/.test(n)));

  const out = [];
  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');

    // Class-level base path (first @RequestMapping above a class declaration).
    const cls = text.match(/@RequestMapping\s*\(([^)]*)\)\s*(?:public\s+)?(?:final\s+)?class/);
    const base = cls ? mappingPath(cls[1]) : '';

    // @GetMapping / @PostMapping / ...
    for (const m of text.matchAll(/@(Get|Post|Put|Patch|Delete)Mapping\s*(?:\(([^)]*)\))?/g)) {
      const method = SHORTHAND[m[1] + 'Mapping'];
      out.push(mk(method, joinPath(base, mappingPath(m[2] || '')), file, lineAt(text, m.index)));
    }
    // Method-level @RequestMapping(method = RequestMethod.X) — skip the class one.
    for (const m of text.matchAll(/@RequestMapping\s*\(([^)]*method\s*=\s*RequestMethod\.(\w+)[^)]*)\)/g)) {
      out.push(mk(m[2].toUpperCase(), joinPath(base, mappingPath(m[1])), file, lineAt(text, m.index)));
    }
  }
  return dedupe(out);
}

// Extract the path from a mapping annotation's args (value=, path=, or bare).
function mappingPath(args) {
  const a = String(args || '');
  const named = a.match(/(?:value|path)\s*=\s*\{?\s*"([^"]*)"/);
  if (named) return named[1];
  const bare = a.match(/^\s*\{?\s*"([^"]*)"/);
  return bare ? bare[1] : '';
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

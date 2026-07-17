import fs from 'node:fs';
import path from 'node:path';

import { walk, lineAt } from '../util/walk.mjs';
import { joinPath } from '../normalize.mjs';

/**
 * Server adapter for NestJS controllers.
 *
 * For each `*.controller.ts` it reads the `@Controller('prefix')` and every
 * route decorator (`@Get`, `@Post`, `@Patch`, `@Put`, `@Delete`), composing the
 * prefix-relative path. The runtime global prefix (api/v1) is NOT prepended —
 * decorators are prefix-relative and so are RTK call sites, so they match
 * directly.
 */
export function extractNestjs({ repoRoot, roots }) {
  const files = roots.flatMap((r) =>
    walk(
      path.join(repoRoot, r),
      (name) => name.endsWith('.controller.ts') && !name.endsWith('.spec.ts'),
    ),
  );

  const routes = [];
  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');
    routes.push(...parseFile(text, file));
  }
  return routes;
}

// Grab the whole decorator argument list so we can handle both `@Get('x')` and
// the array form `@Post(['x', 'x/:id'])`. Route decorators take only a path
// arg (string | string[]) in Nest, so pulling every quoted literal is safe.
const VERB_RE = /@(Get|Post|Put|Patch|Delete)\s*\(\s*([^)]*?)\s*\)/gi;
const STR_RE = /['"`]([^'"`]*)['"`]/g;

function parseFile(text, file) {
  // First @Controller in the file wins (one controller per file is the Nest convention).
  const ctrl = text.match(/@Controller\s*\(\s*([^)]*?)\s*\)/);
  const prefixes = ctrl ? literals(ctrl[1]) : [''];
  const prefix = prefixes[0] ?? '';

  const out = [];
  let m;
  VERB_RE.lastIndex = 0;
  while ((m = VERB_RE.exec(text))) {
    const method = m[1].toUpperCase();
    const subs = literals(m[2]); // one or many (array form), or [''] if pathless
    const line = lineAt(text, m.index);
    for (const sub of subs) {
      out.push({ side: 'server', method, rawPath: joinPath(prefix, sub), controller: prefix, file, line });
    }
  }
  return out;
}

// Extract every string literal from a decorator arg; [''] when there are none.
function literals(argText) {
  const found = [...String(argText || '').matchAll(STR_RE)].map((s) => s[1]);
  return found.length ? found : [''];
}

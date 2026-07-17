import fs from 'node:fs';
import path from 'node:path';

import { walk, lineAt } from '../util/walk.mjs';

/**
 * Client adapter for Redux Toolkit Query.
 *
 * Extracts every `builder.query` / `builder.mutation` endpoint and resolves the
 * (method, path) pair it calls. Handles the three url forms seen in the wild:
 *   1. bare string return:   query: () => 'bookings/all'
 *   2. bare template return: query: (id) => `bookings/${id}/audit`
 *   3. object return:        query: (x) => ({ url: `bookings/${id}`, method: 'POST' })
 *
 * Endpoints whose url cannot be resolved to a literal (built from a runtime
 * variable) are returned with resolvable:false — reported as "unverifiable",
 * never as drift. Honest over confident.
 */
export function extractRtkQuery({ repoRoot, roots }) {
  const files = roots.flatMap((r) =>
    walk(path.join(repoRoot, r), (name) => name.endsWith('.ts') && !name.endsWith('.d.ts')),
  );

  const endpoints = [];
  for (const file of files) {
    const text = fs.readFileSync(file, 'utf8');
    endpoints.push(...parseFile(text, file));
  }
  return endpoints;
}

// Locate each "name: builder.query|mutation" so we can slice per-endpoint chunks.
const ENDPOINT_RE = /([A-Za-z0-9_]+)\s*:\s*builder\.(query|mutation)\b/g;

function parseFile(text, file) {
  const marks = [];
  let m;
  while ((m = ENDPOINT_RE.exec(text))) {
    marks.push({ name: m[1], kind: m[2], index: m.index });
  }

  const out = [];
  for (let i = 0; i < marks.length; i++) {
    const start = marks[i].index;
    const end = i + 1 < marks.length ? marks[i + 1].index : text.length;
    const chunk = text.slice(start, end);
    const { rawPath, method, offset } = resolveCall(chunk, marks[i].kind);

    out.push({
      side: 'client',
      name: marks[i].name,
      kind: marks[i].kind,
      method,
      rawPath,
      resolvable: rawPath != null,
      file,
      line: lineAt(text, start + (offset ?? 0)),
    });
  }
  return out;
}

// Within a single endpoint chunk, find the url + method.
function resolveCall(chunk, kind) {
  // Object form: { url: '...'/`...`, method: '...' }
  const urlMatch = chunk.match(/\burl\s*:\s*(['"`])([\s\S]*?)\1/);
  // Bare return form: query: (args) => '...' / `...`
  const bareMatch = chunk.match(
    /\bquery\s*:\s*(?:async\s*)?(?:\([^)]*\)|[A-Za-z0-9_]+)\s*=>\s*(['"`])([\s\S]*?)\1/,
  );
  const methodMatch = chunk.match(/\bmethod\s*:\s*(['"`])([A-Za-z]+)\1/);

  let rawPath = null;
  let offset = null;
  if (urlMatch) {
    rawPath = urlMatch[2];
    offset = urlMatch.index;
  } else if (bareMatch) {
    rawPath = bareMatch[2];
    offset = bareMatch.index;
  }

  // RTK defaults to GET when method is omitted, for both query and mutation.
  const method = methodMatch ? methodMatch[2].toUpperCase() : 'GET';
  return { rawPath, method, offset };
}

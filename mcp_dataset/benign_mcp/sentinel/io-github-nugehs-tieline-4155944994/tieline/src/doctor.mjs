import { normalizePath, routeKey } from './normalize.mjs';

/**
 * Documentation-drift diff: compare routes parsed from source code (a native
 * server adapter like `nestjs`) against routes declared in an OpenAPI spec.
 *
 * Same backend, two sources of truth — where they disagree is a real bug:
 *   undocumented   in code, missing from the spec   (SDKs/partners can't see it)
 *   phantom        in spec, missing from the code    (stale docs promise a route)
 *
 * Both sides are reduced to the same prefix-relative, param-collapsed form so a
 * NestJS `@Get('vendor/:id/dashboard')` and a spec `/api/v1/.../{id}/dashboard`
 * compare apples to apples.
 */
export function doctor(codeRoutes, specRoutes, { basePath = '', ignore = [] } = {}) {
  const ignoreRe = ignore.map((p) => new RegExp(p));
  const isIgnored = (np) => ignoreRe.some((re) => re.test(np));

  const codeMap = index(codeRoutes, basePath);
  const specMap = index(specRoutes, basePath);

  const undocumented = [];
  const phantom = [];
  let matched = 0;

  for (const [key, r] of codeMap.byKey) {
    if (isIgnored(r._np)) continue;
    if (specMap.byKey.has(key)) {
      matched++;
    } else {
      undocumented.push({ ...r, hint: hint(r, specMap, 'spec') });
    }
  }

  for (const [key, r] of specMap.byKey) {
    if (isIgnored(r._np)) continue;
    if (!codeMap.byKey.has(key)) {
      phantom.push({ ...r, hint: hint(r, codeMap, 'code') });
    }
  }

  return {
    undocumented: dedupe(undocumented),
    phantom: dedupe(phantom),
    totals: {
      matched,
      undocumented: undocumented.length,
      phantom: phantom.length,
      code: codeMap.byKey.size,
      spec: specMap.byKey.size,
    },
  };
}

function index(routes, basePath) {
  const byKey = new Map();
  const byPath = new Map();
  for (const r of routes) {
    const np = normalizePath(r.rawPath, { basePath });
    r._np = np;
    byKey.set(routeKey(r.method, np), r);
    if (!byPath.has(np)) byPath.set(np, []);
    byPath.get(np).push(r.method);
  }
  return { byKey, byPath };
}

function hint(route, otherSide, where) {
  const methods = otherSide.byPath.get(route._np);
  if (methods && methods.length) {
    return `path is in ${where} but only as ${[...new Set(methods)].join(', ')}`;
  }
  return where === 'spec' ? 'not in the published spec' : 'not found in source code';
}

function dedupe(list) {
  const seen = new Set();
  return list.filter((r) => {
    const k = routeKey(r.method, r._np);
    if (seen.has(k)) return false;
    seen.add(k);
    return true;
  });
}

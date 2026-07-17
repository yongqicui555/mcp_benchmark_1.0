import { normalizePath, routeKey } from './normalize.mjs';

/**
 * Join client endpoints against server routes on (method, normalized path).
 *
 * Buckets:
 *   matched       FE call resolves to an existing BE route          ✅
 *   drift         FE call resolves but BE has no such route         ❌  (the money finding)
 *   unverifiable  FE url could not be resolved to a literal         ⚠️
 *   dead          BE route no resolvable FE call reaches            🟡  (informational)
 */
export function match(endpoints, routes, { basePath = '', ignore = [] } = {}) {
  const ignoreRe = ignore.map((p) => new RegExp(p));
  const isIgnored = (np) => ignoreRe.some((re) => re.test(np));

  // Index BE routes by exact key, and by path (any method) for smarter hints.
  const byKey = new Map();
  const byPath = new Map();
  const anyMethodPaths = new Set(); // routes that accept any verb (app.all, Next pages API)
  for (const r of routes) {
    const np = normalizePath(r.rawPath, { basePath });
    r._np = np;
    if (r.method === 'ALL' || r.method === 'ANY') anyMethodPaths.add(np);
    const key = routeKey(r.method, np);
    if (!byKey.has(key)) byKey.set(key, []);
    byKey.get(key).push(r);
    if (!byPath.has(np)) byPath.set(np, []);
    byPath.get(np).push(r);
  }

  const matched = [];
  const drift = [];
  const unverifiable = [];
  const usedKeys = new Set();

  for (const ep of endpoints) {
    if (!ep.resolvable) {
      unverifiable.push(ep);
      continue;
    }
    const np = normalizePath(ep.rawPath, { basePath });
    ep._np = np;

    // Residual `$` or backtick means the url was built conditionally (e.g. a
    // nested template literal) and could not be fully resolved — report as
    // unverifiable, never as drift. `{}` param placeholders are fine.
    if (np == null || /[$`]/.test(np)) {
      unverifiable.push({ ...ep, resolvable: false });
      continue;
    }
    if (isIgnored(np)) continue;

    const key = routeKey(ep.method, np);
    if (byKey.has(key) || anyMethodPaths.has(np)) {
      matched.push(ep);
      usedKeys.add(key);
      continue;
    }
    drift.push({ ...ep, _np: np, hint: hintFor(ep.method, np, byPath) });
  }

  const dead = routes.filter((r) => !usedKeys.has(routeKey(r.method, r._np)));

  return { matched, drift, unverifiable, dead, totals: counts({ matched, drift, unverifiable, dead }) };
}

// Suggest the likely intended route for a drift finding.
function hintFor(method, np, byPath) {
  const sameP = byPath.get(np);
  if (sameP) {
    const verbs = [...new Set(sameP.map((r) => r.method))].join(', ');
    return `path exists but as ${verbs}, not ${method}`;
  }
  // Only suggest a route that is genuinely close — otherwise the hint misleads
  // (e.g. "event-vendor/status" should NOT suggest "event-vendor/search").
  let best = null;
  for (const cand of byPath.keys()) {
    const s = pathScore(np, cand);
    if (s != null && (best == null || s < best.s)) best = { cand, s };
  }
  if (best) return `did you mean "${best.cand}"?`;
  return 'no matching backend route';
}

// Closeness score for a "did you mean" candidate (lower = closer); null when
// the candidate is not a plausible suggestion. Segment-aware so a long shared
// prefix can't inflate the tolerance. Cross-references the ENTIRE route set
// (including dead/orphan routes), so a frontend call that drifted because of a
// wrong prefix is matched to the real route on another mount point — e.g.
// "/contract-templates" → "/contracts/templates", "/vendors" →
// "/recommendations/vendors", "/bookings/ticket-sales-analysis/{}" →
// "/event/ticket-sales-analysis/{}".
function pathScore(np, cand) {
  if (np === cand) return null;
  const a = np.split('/');
  const b = cand.split('/');
  const noParams = (segs) => segs.filter((s) => s !== '{}').join('/');

  // 1) Same path once {} params are ignored — a param-shape mismatch.
  if (noParams(a) === noParams(b)) return 0;

  // 2) Same segment count, exactly one segment differs.
  if (a.length === b.length) {
    const diff = [];
    for (let i = 0; i < a.length; i++) if (a[i] !== b[i]) diff.push(i);
    if (diff.length === 1) {
      const i = diff[0];
      const d = lev(a[i], b[i]);
      // ~40% of the shorter segment (min 2): keeps "viewed"↔"view" /
      // "users"↔"user" while rejecting distinct words like "status"↔"search".
      const cap = Math.max(2, Math.round(Math.min(a[i].length, b[i].length) * 0.4));
      if (d <= cap) return 1 + d;
      // Only the FIRST (container) segment differs and the shared tail is
      // distinctive — a wrong top-level mount (bookings/X vs event/X), not a
      // different action under the same resource. "Distinctive" = multi-word
      // (hyphenated) or long, so generic tails like ".../status" don't match.
      if (i === 0) {
        const shared = a.filter((s, j) => j !== 0 && s !== '{}');
        if (shared.some((s) => s.includes('-')) || shared.join('').length >= 12) {
          return 20;
        }
      }
    }
  }

  // 3) Missing prefix — the candidate ends with the full FE path.
  if (
    b.length > a.length &&
    a.join('/') === b.slice(b.length - a.length).join('/') &&
    noParams(a).length >= 5
  ) {
    return 10 + (b.length - a.length);
  }

  // 4) Word-join differences across "/" and "-" (contract-templates vs
  //    contracts/templates): equal token bags, every token twinned (exact or
  //    a small edit), so distinct actions still don't match.
  const toks = (segs) => noParams(segs).split(/[/-]/).filter(Boolean);
  const ta = toks(a);
  const tb = toks(b);
  if (ta.length === tb.length && ta.length >= 2) {
    const used = new Array(tb.length).fill(false);
    let twinned = 0;
    for (const t of ta) {
      const k = tb.findIndex((u, j) => !used[j] && (u === t || lev(u, t) <= 2));
      if (k >= 0) { used[k] = true; twinned++; }
    }
    if (twinned === ta.length) return 15;
  }

  return null;
}

function counts(b) {
  return {
    matched: b.matched.length,
    drift: b.drift.length,
    unverifiable: b.unverifiable.length,
    dead: b.dead.length,
  };
}

// Tiny Levenshtein for "did you mean" hints.
function lev(a, b) {
  const dp = Array.from({ length: a.length + 1 }, (_, i) => [i, ...Array(b.length).fill(0)]);
  for (let j = 0; j <= b.length; j++) dp[0][j] = j;
  for (let i = 1; i <= a.length; i++) {
    for (let j = 1; j <= b.length; j++) {
      dp[i][j] = Math.min(
        dp[i - 1][j] + 1,
        dp[i][j - 1] + 1,
        dp[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1),
      );
    }
  }
  return dp[a.length][b.length];
}

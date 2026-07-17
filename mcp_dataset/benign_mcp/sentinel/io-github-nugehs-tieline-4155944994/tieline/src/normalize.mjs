/**
 * Reduce a raw path template from either side of the contract to a canonical
 * form so that FE `bookings/${id}/confirm`, BE `bookings/:id/confirm`, and an
 * OpenAPI `bookings/{id}/confirm` all collapse to `bookings/{}/confirm`.
 */
export function normalizePath(raw, { basePath = '' } = {}) {
  if (raw == null) return null;
  let p = String(raw);

  // Collapse FE template interpolations FIRST — a `${cond ? '?a' : ''}` can hide
  // a `?` that is NOT a query separator, so this must precede the query strip.
  p = p.replace(/\$\{[^}]*\}/g, '{}');

  // Drop any (real) query string — path identity only.
  p = p.split('?')[0];

  // Collapse the remaining parameter syntaxes to a single placeholder.
  p = p
    .replace(/:[A-Za-z0-9_]+/g, '{}') // Express/Nest: :id
    .replace(/<[^>]+>/g, '{}') // Flask/Werkzeug: <int:id>, <path:p>
    .replace(/\[[^\]]+\]/g, '{}') // Next.js file route: [id], [...slug]
    .replace(/\{[^}]*\}/g, '{}'); // OpenAPI/Spring: {id}

  // Trim slashes/whitespace.
  p = p.trim().replace(/^\/+/, '').replace(/\/+$/, '');

  // Defensively strip a leading version prefix if it leaked into a call site.
  const base = basePath.replace(/^\/+/, '').replace(/\/+$/, '');
  if (base && (p === base || p.startsWith(base + '/'))) {
    p = p.slice(base.length).replace(/^\/+/, '');
  }

  // Collapse accidental double slashes from joins.
  p = p.replace(/\/{2,}/g, '/');

  return p;
}

/** Join path segments (controller prefix + route subpath) safely. */
export function joinPath(...segments) {
  return segments
    .map((s) => String(s ?? '').trim())
    .map((s) => s.replace(/^\/+/, '').replace(/\/+$/, ''))
    .filter(Boolean)
    .join('/');
}

/** Canonical match key: "METHOD normalized/path". */
export function routeKey(method, normalizedPath) {
  return `${method.toUpperCase()} ${normalizedPath}`;
}

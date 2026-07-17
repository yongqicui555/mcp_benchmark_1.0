const slim = (e) => ({
  name: e.name,
  method: e.method,
  path: e._np ? '/' + e._np : null,
  resolvable: e.resolvable !== false,
  hint: e.hint,
  file: e.file,
  line: e.line,
});

const slimRoute = (r) => ({ method: r.method, path: '/' + r._np, file: r.file, line: r.line });
const slimDoctor = (r) => ({ method: r.method, path: '/' + r._np, hint: r.hint, file: r.file, line: r.line || undefined });

/** Shape a match() result into a plain, serializable object. */
export function toJson(result) {
  const { matched, drift, unverifiable, dead, totals } = result;
  return {
    totals,
    drift: drift.map(slim),
    unverifiable: unverifiable.map(slim),
    matched: matched.map(slim),
    dead: dead.map(slimRoute),
  };
}

/** Shape a doctor() result into a plain, serializable object. */
export function toDoctorJson(result) {
  return {
    totals: result.totals,
    undocumented: result.undocumented.map(slimDoctor),
    phantom: result.phantom.map(slimDoctor),
  };
}

export function reportDoctorJson(result) {
  console.log(JSON.stringify(toDoctorJson(result), null, 2));
}

export function reportJson(result) {
  console.log(JSON.stringify(toJson(result), null, 2));
}

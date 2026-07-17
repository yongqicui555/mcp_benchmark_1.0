const C = {
  reset: '\x1b[0m', bold: '\x1b[1m', dim: '\x1b[2m',
  red: '\x1b[31m', yellow: '\x1b[33m', green: '\x1b[32m', cyan: '\x1b[36m', gray: '\x1b[90m',
};
const sevColor = { red: C.red, amber: C.yellow, green: C.green };
const sevMark = { red: '✖', amber: '▲', green: '✓' };

export function renderTerminal(report) {
  const L = [];
  L.push('');
  L.push(`${C.bold}AI Surface Audit${C.reset} ${C.dim}— ${report.repo}${C.reset}`);
  if (report.acceleratedBy) L.push(`${C.gray}accelerated by ${report.acceleratedBy}${C.reset}`);
  L.push(`${C.dim}${report.surfaceCount} AI surface(s) found${C.reset}`);
  L.push('');

  const order = { red: 0, amber: 1, green: 2 };
  const sorted = [...report.surfaces].sort((a, b) => order[a.severity] - order[b.severity]);

  for (const s of sorted) {
    const col = sevColor[s.severity];
    L.push(`${col}${sevMark[s.severity]} ${s.severity.toUpperCase()}${C.reset}  ${C.bold}${s.file}${C.reset}`);
    L.push(`   ${C.dim}provider:${C.reset} ${s.providerLabel}   ${C.dim}sink:${C.reset} ${s.sink}${s.sideEffects?.length ? ` (${s.sideEffects.join(', ')})` : ''}`);
    const g = s.guardrails;
    const cell = (k, v) => `${v === true ? C.green + '✓' : v === 'n/a' ? C.gray + '–' : C.red + '✗'}${C.reset} ${k}`;
    L.push(`   ${cell('confidence', g.confidence)}  ${cell('fallback', g.fallback)}  ${cell('validation', g.validation)}  ${cell('human-in-loop', g.humanInLoop)}  ${cell('error-isolation', g.errorIsolation)}${g.disclaimer ? `  ${cell('disclaimer', true)}` : ''}`);
    if (s._refinedBy) L.push(`   ${C.gray}↳ sink refined by ${s._refinedBy}${C.reset}`);
    if (s.evidence?.length) L.push(`   ${C.gray}${s.evidence[0]}${C.reset}`);
    L.push('');
  }

  const sm = report.summary;
  L.push(`${C.bold}Summary:${C.reset} ${C.red}${sm.red} red${C.reset}  ${C.yellow}${sm.amber} amber${C.reset}  ${C.green}${sm.green} green${C.reset}`);
  if (report.gate) {
    L.push(report.gate.passed
      ? `${C.green}✓ gate passed${C.reset} (no red side-effectful surfaces)`
      : `${C.red}✖ gate failed${C.reset} (${report.gate.blocking} blocking surface(s))`);
  }
  L.push('');
  return L.join('\n');
}

export function buildSummary(surfaces) {
  return surfaces.reduce((a, s) => (a[s.severity]++, a), { red: 0, amber: 0, green: 0 });
}

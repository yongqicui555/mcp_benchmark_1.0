// ESLint-style linter output for compliance violations and guardrail failures.
// Format:
//   src/payment.js
//     42:0  error    Side-effectful AI output without human-in-loop  soc2/CC9.1
//     42:0  warning  No confidence threshold on model output          soc2/PI1.3
//
//   2 files, 3 errors, 1 warning

const C = {
  reset: '\x1b[0m', bold: '\x1b[1m', dim: '\x1b[2m',
  red: '\x1b[31m', yellow: '\x1b[33m', cyan: '\x1b[36m', gray: '\x1b[90m',
};

// Extract line number from evidence string like "src/foo.js:42 someMethod"
function extractLine(evidence) {
  if (!evidence) return 0;
  const m = String(evidence).match(/:(\d+)/);
  return m ? parseInt(m[1], 10) : 0;
}

// When no compliance frameworks are set, fall back to guardrail-based rules.
const GUARDRAIL_RULES = [
  {
    id: 'guardrail/human-in-loop',
    level: 'error',
    message: 'Side-effectful AI output with no human-in-loop confirmation',
    when: s => s.sink === 'side-effectful' && s.guardrails.humanInLoop !== true,
  },
  {
    id: 'guardrail/validation',
    level: 'error',
    message: 'AI output reaches users or side-effects without output validation',
    when: s => s.sink !== 'internal' && !s.guardrails.validation,
  },
  {
    id: 'guardrail/confidence',
    level: 'warning',
    message: 'No confidence threshold check on model output',
    when: s => s.sink !== 'internal' && !s.guardrails.confidence,
  },
  {
    id: 'guardrail/fallback',
    level: 'warning',
    message: 'No fallback path for uncertain or degraded model output',
    when: s => s.sink !== 'internal' && !s.guardrails.fallback,
  },
  {
    id: 'guardrail/error-isolation',
    level: 'warning',
    message: 'AI call not wrapped in error isolation (try-catch)',
    when: s => s.sink !== 'internal' && !s.guardrails.errorIsolation,
  },
];

export function renderLint(report, { color = true } = {}) {
  const cc = color ? C : Object.fromEntries(Object.keys(C).map(k => [k, '']));
  const hasCompliance = !!(report.compliance?.frameworks?.length);
  const L = [];
  let totalErrors = 0;
  let totalWarnings = 0;
  let fileCount = 0;

  // Group surfaces by file
  const byFile = new Map();
  for (const s of report.surfaces) {
    if (!byFile.has(s.file)) byFile.set(s.file, []);
    byFile.get(s.file).push(s);
  }

  for (const [file, surfaces] of byFile) {
    const lines = [];

    for (const s of surfaces) {
      const lineNo = extractLine(s.evidence?.[0]);

      if (hasCompliance && s.violations?.length) {
        for (const v of s.violations) {
          const col = v.level === 'error' ? cc.red : cc.yellow;
          lines.push({ lineNo, level: v.level, col, message: v.title, rule: `${v.framework}/${v.id}` });
          if (v.level === 'error') totalErrors++;
          else totalWarnings++;
        }
      } else if (!hasCompliance) {
        for (const rule of GUARDRAIL_RULES) {
          if (rule.when(s)) {
            const col = rule.level === 'error' ? cc.red : cc.yellow;
            lines.push({ lineNo, level: rule.level, col, message: rule.message, rule: rule.id });
            if (rule.level === 'error') totalErrors++;
            else totalWarnings++;
          }
        }
      }
    }

    if (!lines.length) continue;
    fileCount++;
    L.push(`${cc.bold}${file}${cc.reset}`);

    lines.sort((a, b) => a.lineNo - b.lineNo || (a.level === 'error' ? -1 : 1));
    for (const ln of lines) {
      const loc = `${ln.lineNo}:0`.padEnd(7);
      const lvl = ln.level.padEnd(7);
      L.push(`  ${cc.dim}${loc}${cc.reset}  ${ln.col}${lvl}${cc.reset}  ${ln.message}  ${cc.gray}${ln.rule}${cc.reset}`);
    }
    L.push('');
  }

  if (L.length === 0) {
    L.push(`  ${cc.dim}No violations found.${cc.reset}`);
    L.push('');
  }

  const errStr = totalErrors > 0 ? `${cc.red}${totalErrors} error${totalErrors !== 1 ? 's' : ''}${cc.reset}` : `${totalErrors} errors`;
  const warnStr = totalWarnings > 0 ? `${cc.yellow}${totalWarnings} warning${totalWarnings !== 1 ? 's' : ''}${cc.reset}` : `${totalWarnings} warnings`;
  L.push(`${fileCount} file${fileCount !== 1 ? 's' : ''}, ${errStr}, ${warnStr}`);

  return L.join('\n');
}

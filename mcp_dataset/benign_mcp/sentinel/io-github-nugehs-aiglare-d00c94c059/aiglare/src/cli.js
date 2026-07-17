#!/usr/bin/env node
import path from 'node:path';
import { runAudit } from './audit.js';
import { renderTerminal } from './report/reporter.js';
import { renderLint } from './report/lint-reporter.js';
import { renderMarkdown } from './report/markdown-reporter.js';
import { renderHtml } from './report/html-reporter.js';
import { startMcpServer } from './mcp.js';
import { parseFrameworks } from './compliance/mapper.js';
import { FRAMEWORKS } from './compliance/controls.js';

const VALID_FORMATS = ['terminal', 'json', 'lint', 'markdown', 'html'];

function parseArgs(argv) {
  const args = {
    path: process.cwd(),
    json: false,
    ci: false,
    severity: null,
    sinks: null,
    compliance: null,
    format: null,
  };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === '--json') args.json = true;
    else if (a === '--ci') args.ci = true;
    else if (a === '--severity') {
      args.severity = argv[++i];
      if (!['red', 'amber'].includes(args.severity)) { console.error('--severity must be "red" or "amber"'); process.exit(2); }
    }
    else if (a === '--sinks') {
      const v = argv[++i];
      if (!v) { console.error('--sinks needs a comma-separated list (user-facing,side-effectful,internal)'); process.exit(2); }
      args.sinks = v.split(',').map(s => s.trim()).filter(Boolean);
    }
    else if (a === '--compliance') {
      args.compliance = argv[++i];
      if (!args.compliance) { console.error('--compliance needs a value (soc2,eu-ai-act,nist,owasp or all)'); process.exit(2); }
    }
    else if (a === '--format') {
      args.format = argv[++i];
      if (!VALID_FORMATS.includes(args.format)) {
        console.error(`--format must be one of: ${VALID_FORMATS.join(', ')}`);
        process.exit(2);
      }
    }
    else if (a === '--help' || a === '-h') args.help = true;
    else if (!a.startsWith('-')) {
      if (!args.paths) args.paths = [];
      args.paths.push(path.resolve(a));
    }
  }
  // --json is a legacy alias for --format json
  if (args.json && !args.format) args.format = 'json';
  return args;
}

const HELP = `
aiglare — audit AI/LLM features for governance guardrails

Usage:  aiglare [path] [options]
        aiglare mcp                 Start the MCP server (stdio)

Options:
  --json                    Emit JSON (alias for --format json)
  --format <fmt>            Output format: terminal (default), json, lint, markdown, html
  --compliance <frameworks> Map findings to compliance controls.
                            Comma-separated: soc2, eu-ai-act, nist, owasp, or "all"
  --ci                      Exit non-zero if any red side-effectful surface is found
  --severity <lvl>          Only show surfaces at this level or worse (red|amber)
  --sinks <list>            Filter to sinks: user-facing,side-effectful,internal
  -h, --help                Show this help

Compliance frameworks:
  soc2        SOC 2 Trust Services Criteria (CC7, CC9, A1, PI1)
  eu-ai-act   EU AI Act (Art. 9, 13, 14, 17)
  nist        NIST AI RMF (GOVERN, MEASURE, MANAGE, MAP)
  owasp       OWASP LLM Top 10 (LLM02, LLM04, LLM08, LLM09)

Examples:
  aiglare                                              # terminal audit
  aiglare --compliance all --format markdown           # full evidence doc
  aiglare --compliance soc2,eu-ai-act --format lint    # compliance linter
  aiglare --format lint                                # guardrail linter
  aiglare --compliance all --format lint --ci          # CI gate with compliance
  aiglare --compliance all --format html > report.html # HTML evidence report

Detects where model output reaches users or side-effects (payment, booking,
email, db writes) without confidence handling, fallbacks, validation, or
human-in-the-loop. Standalone; uses a repoctx index automatically if present.
`;

async function main() {
  const argv = process.argv.slice(2);

  // Subcommand: `aiglare mcp` starts the stdio MCP server.
  if (argv[0] === 'mcp') {
    await startMcpServer();
    return;
  }

  const args = parseArgs(argv);
  if (args.help) { console.log(HELP); process.exit(0); }

  let frameworks = [];
  if (args.compliance) {
    try {
      frameworks = parseFrameworks(args.compliance);
    } catch (err) {
      console.error(err.message);
      process.exit(2);
    }
  }

  let report;
  try {
    report = runAudit({ ...args, compliance: frameworks });
  } catch (err) {
    console.error(err instanceof Error ? err.message : String(err));
    process.exit(2);
  }

  const fmt = args.format ?? 'terminal';

  if (fmt === 'json') {
    console.log(JSON.stringify(report, null, 2));
  } else if (fmt === 'lint') {
    console.log(renderLint(report));
  } else if (fmt === 'markdown') {
    console.log(renderMarkdown(report));
  } else if (fmt === 'html') {
    console.log(renderHtml(report));
  } else {
    console.log(renderTerminal(report));
    if (frameworks.length && report.compliance) {
      const C = { reset: '\x1b[0m', bold: '\x1b[1m', red: '\x1b[31m', yellow: '\x1b[33m', dim: '\x1b[2m' };
      console.log(`${C.bold}Compliance:${C.reset} ${frameworks.map(f => FRAMEWORKS[f] ?? f).join(', ')}`);
      for (const [fw, counts] of Object.entries(report.compliance.violations)) {
        const label = FRAMEWORKS[fw] ?? fw;
        const e = counts.error > 0 ? `${C.red}${counts.error} error(s)${C.reset}` : `0 errors`;
        const w = counts.warning > 0 ? `${C.yellow}${counts.warning} warning(s)${C.reset}` : `0 warnings`;
        console.log(`  ${C.dim}${label}:${C.reset} ${e}, ${w}`);
      }
      console.log('');
    }
  }

  if (args.ci && report.gate && !report.gate.passed) process.exit(1);
}

main();

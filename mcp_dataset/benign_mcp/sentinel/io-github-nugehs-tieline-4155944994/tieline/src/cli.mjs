import { loadConfig } from './config.mjs';
import { runCheck, runDoctorCheck } from './core.mjs';
import { runInit } from './init.mjs';
import { reportHuman, reportDoctor } from './reporters/human.mjs';
import { reportJson, reportDoctorJson } from './reporters/json.mjs';
import { reportHtml } from './reporters/html.mjs';
import { writeFileSync } from 'node:fs';

export async function run(argv) {
  const args = parseArgs(argv);
  if (args.help) return printHelp();

  if (args.command === 'init') return void runInit();

  if (args.command === 'mcp') {
    const { serve } = await import('./mcp.mjs');
    return serve();
  }

  const cfg = loadConfig(args.config);

  if (args.command === 'doctor') return runDoctor(cfg, args);

  const result = await runCheck(cfg);

  if (args.html) {
    writeFileSync(args.html, reportHtml(result, {
      clientAdapter: cfg.client.adapter,
      serverAdapter: cfg.server.adapter,
      generatedAt: new Date().toISOString().replace('T', ' ').slice(0, 16) + ' UTC',
    }));
    console.log(`\n  📄 HTML report written to ${args.html}\n`);
  }

  if (args.json) reportJson(result);
  else if (!args.html) reportHuman(result, { command: args.command });

  // Exit code: fail when a configured bucket is non-empty (unless --no-fail).
  if (args.command === 'check' && !args.noFail) {
    const failing = (cfg.failOn || []).some((k) => (result.totals[k] || 0) > 0);
    if (failing) process.exitCode = 1;
  }
}

// `tieline doctor`: diff native-parsed code routes against the OpenAPI spec.
async function runDoctor(cfg, args) {
  const result = await runDoctorCheck(cfg);

  if (args.json) reportDoctorJson(result);
  else reportDoctor(result, { codeAdapter: cfg.server.adapter, specSource: cfg.server.spec });

  if (!args.noFail) {
    const fail = (cfg.doctorFailOn || ['undocumented']).some((k) => (result.totals[k] || 0) > 0);
    if (fail) process.exitCode = 1;
  }
}

function parseArgs(argv) {
  const args = { command: 'check', json: false, noFail: false, config: null, help: false, html: null };
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i];
    if (a === 'check' || a === 'list' || a === 'orphans' || a === 'doctor' || a === 'init' || a === 'mcp') args.command = a;
    else if (a === '--json') args.json = true;
    else if (a === '--no-fail') args.noFail = true;
    else if (a === '--config') args.config = argv[++i];
    else if (a === '--html') args.html = argv[++i] || 'tieline-report.html';
    else if (a === '-h' || a === '--help') args.help = true;
  }
  return args;
}

function printHelp() {
  console.log(`
tieline — static FE↔BE contract-drift checker

USAGE
  tieline [init|check|list|orphans|doctor|mcp] [options]

COMMANDS
  init       Auto-detect nearby repos and write a tieline.config.json
  check      Report drift + unverifiable calls, exit non-zero on drift (default)
  list       Print the full resolved contract map (every endpoint + its status)
  orphans    List backend routes no resolvable frontend call reaches
  doctor     Diff native-parsed code routes vs the OpenAPI spec (needs server.spec):
             undocumented (in code, not in spec) + phantom (in spec, not in code)
  mcp        Start the MCP server (stdio) — same as the tieline-mcp bin

OPTIONS
  --config <path>   Path to tieline.config.json (default: search up from cwd)
  --json            Machine-readable output
  --html <file>     Write a self-contained HTML report (with a contract-flow chart)
  --no-fail         Always exit 0 (report only)
  -h, --help        Show this help
`);
}

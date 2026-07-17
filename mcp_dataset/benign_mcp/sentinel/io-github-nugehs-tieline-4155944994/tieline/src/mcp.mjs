// Zero-dependency MCP server over stdio (newline-delimited JSON-RPC 2.0).
//
// Exposes tieline's deterministic analysis as MCP tools so an agent can ask
// "does the frontend agree with the backend?" and get structured JSON back —
// the same engine the CLI runs, no LLM in the loop. Implemented by hand to keep
// tieline's zero-dependency promise; the protocol surface is small (initialize,
// tools/list, tools/call, ping).
//
// CONTRACT: stdout carries the JSON-RPC stream and nothing else. Every tool
// here returns structured data with no console writes; diagnostics go to stderr.
import readline from 'node:readline';
import { readFileSync } from 'node:fs';
import { loadConfig } from './config.mjs';
import { runCheck, runDoctorCheck } from './core.mjs';
import { runInit } from './init.mjs';
import { toJson, toDoctorJson } from './reporters/json.mjs';

const PROTOCOL_VERSION = '2025-06-18';
const pkg = JSON.parse(readFileSync(new URL('../package.json', import.meta.url), 'utf8'));

const CONFIG_INPUT = {
  type: 'object',
  properties: {
    config: {
      type: 'string',
      description:
        'Path to tieline.config.json. Defaults to searching upward from the server\'s working directory.',
    },
  },
};

const TOOLS = [
  {
    name: 'tieline_check',
    description:
      'Run the static frontend↔backend contract-drift check. Returns totals plus the ' +
      'drift bucket (frontend calls that resolve to no backend route — the bug bucket) ' +
      'and the unverifiable bucket (URLs built at runtime, reported never guessed).',
    inputSchema: CONFIG_INPUT,
  },
  {
    name: 'tieline_list',
    description:
      'Return the full resolved contract map: every frontend endpoint with its status ' +
      '(matched / drift / unverifiable) plus backend routes no frontend call reaches.',
    inputSchema: CONFIG_INPUT,
  },
  {
    name: 'tieline_orphans',
    description:
      'List backend routes that no resolvable frontend call reaches (dead/unused routes).',
    inputSchema: CONFIG_INPUT,
  },
  {
    name: 'tieline_doctor',
    description:
      'Diff routes parsed from source code (a native server adapter) against the routes ' +
      'declared in the OpenAPI spec (server.spec). Returns undocumented (in code, missing ' +
      'from the spec) and phantom (in the spec, missing from code).',
    inputSchema: CONFIG_INPUT,
  },
  {
    name: 'tieline_init',
    description:
      'Auto-detect nearby repos (frontend + backend stacks) and write a tieline.config.json. ' +
      'Returns the generated config and what was detected.',
    inputSchema: {
      type: 'object',
      properties: {
        cwd: {
          type: 'string',
          description: 'Directory to scan and write the config into. Defaults to the working directory.',
        },
      },
    },
  },
];

async function callTool(name, args) {
  switch (name) {
    case 'tieline_check': {
      const j = toJson(await runCheck(loadConfig(args.config)));
      return { totals: j.totals, drift: j.drift, unverifiable: j.unverifiable };
    }
    case 'tieline_list':
      return toJson(await runCheck(loadConfig(args.config)));
    case 'tieline_orphans': {
      const j = toJson(await runCheck(loadConfig(args.config)));
      return { totals: { dead: j.totals.dead }, dead: j.dead };
    }
    case 'tieline_doctor':
      return toDoctorJson(await runDoctorCheck(loadConfig(args.config)));
    case 'tieline_init':
      return runInit({ cwd: args.cwd || process.cwd(), quiet: true });
    default:
      throw new Error(`Unknown tool: ${name}`);
  }
}

function send(msg) {
  process.stdout.write(JSON.stringify(msg) + '\n');
}
function reply(id, result) {
  send({ jsonrpc: '2.0', id, result });
}
function fail(id, code, message) {
  send({ jsonrpc: '2.0', id, error: { code, message } });
}

async function handle(msg) {
  const { id, method, params } = msg;

  if (method === 'initialize') {
    reply(id, {
      protocolVersion: (params && params.protocolVersion) || PROTOCOL_VERSION,
      capabilities: { tools: {} },
      serverInfo: { name: 'tieline', version: pkg.version },
    });
    return;
  }
  if (method === 'ping') return void reply(id, {});
  if (method === 'tools/list') return void reply(id, { tools: TOOLS });
  if (method === 'tools/call') {
    const { name, arguments: args } = params || {};
    try {
      const data = await callTool(name, args || {});
      reply(id, { content: [{ type: 'text', text: JSON.stringify(data, null, 2) }] });
    } catch (err) {
      // Tool failures are returned in-band (isError) per the MCP spec, not as
      // protocol-level errors — the agent gets to see and react to the message.
      reply(id, {
        content: [{ type: 'text', text: 'tieline error: ' + (err && err.message ? err.message : String(err)) }],
        isError: true,
      });
    }
    return;
  }

  // Notifications (e.g. notifications/initialized) carry no id — never reply.
  if (id === undefined || id === null) return;
  fail(id, -32601, `Method not found: ${method}`);
}

/** Start serving MCP over stdio. Resolves when stdin closes. */
export function serve() {
  const rl = readline.createInterface({ input: process.stdin });
  rl.on('line', (line) => {
    const trimmed = line.trim();
    if (!trimmed) return;
    let msg;
    try {
      msg = JSON.parse(trimmed);
    } catch {
      send({ jsonrpc: '2.0', id: null, error: { code: -32700, message: 'Parse error' } });
      return;
    }
    Promise.resolve(handle(msg)).catch((err) => {
      if (msg && msg.id !== undefined && msg.id !== null) {
        fail(msg.id, -32603, err && err.message ? err.message : String(err));
      }
    });
  });
  rl.on('close', () => process.exit(0));
}

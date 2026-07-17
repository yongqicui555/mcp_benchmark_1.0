import fs from 'node:fs';
import path from 'node:path';
import readline from 'node:readline';
import { fileURLToPath } from 'node:url';
import { runAudit } from './audit.js';
import { PROVIDERS } from './providers.js';
import { parseFrameworks } from './compliance/mapper.js';
import { FRAMEWORK_IDS } from './compliance/controls.js';

// Hand-rolled JSON-RPC 2.0 server over stdio — no SDK dependency, matching the
// repoctx MCP server convention. Reads line-delimited JSON from stdin and writes
// responses to stdout.

const protocolVersion = '2025-06-18';
const packageRoot = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const packageJson = JSON.parse(fs.readFileSync(path.join(packageRoot, 'package.json'), 'utf8'));

const tools = [
  {
    name: 'ai_surface_audit',
    title: 'Audit AI Surfaces',
    description:
      'Audit a JS/TS repo for AI/LLM governance guardrails. Returns every surface where model output reaches a user or a side-effect, classified by sink and scored on confidence, fallback, validation, human-in-the-loop, and error isolation. Uses a repoctx index automatically if present.',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Repository path. Defaults to current working directory.' },
        sinks: {
          type: 'array',
          items: { type: 'string', enum: ['user-facing', 'side-effectful', 'internal'] },
          description: 'Optional filter to these sinks.',
        },
        severity: { type: 'string', enum: ['red', 'amber'], description: 'Optional: only surfaces at this level or worse.' },
        compliance: {
          type: 'array',
          items: { type: 'string', enum: FRAMEWORK_IDS },
          description: 'Optional compliance frameworks to map violations against. Each surface will include a violations[] array.',
        },
      },
    },
  },
  {
    name: 'ai_surface_gate',
    title: 'AI Surface CI Gate',
    description:
      'Run the CI gate for a repo: reports whether any red + side-effectful surface exists (the "AI auto-triggers an irreversible action with no confirmation" case). passed=false means a build should fail.',
    inputSchema: {
      type: 'object',
      properties: {
        path: { type: 'string', description: 'Repository path. Defaults to current working directory.' },
      },
    },
  },
  {
    name: 'list_providers',
    title: 'List AI Providers',
    description: 'List the AI/LLM provider registry the scanner detects (package names and inference hosts).',
    inputSchema: { type: 'object', properties: {} },
  },
];

async function dispatchTool(name, args) {
  switch (name) {
    case 'ai_surface_audit': {
      const frameworks = args.compliance ? parseFrameworks(args.compliance.join(',')) : [];
      return runAudit({ path: args.path ?? '.', sinks: args.sinks, severity: args.severity, compliance: frameworks });
    }
    case 'ai_surface_gate': {
      const report = runAudit({ path: args.path ?? '.', ci: true });
      return { repo: report.repo, acceleratedBy: report.acceleratedBy, ...report.gate };
    }
    case 'list_providers':
      return { providers: PROVIDERS };
    default:
      throw new McpProtocolError(-32602, `Unknown tool: ${name}`);
  }
}

export async function startMcpServer({ input = process.stdin, output = process.stdout } = {}) {
  const rl = readline.createInterface({ input, crlfDelay: Infinity });
  for await (const line of rl) {
    const trimmed = line.trim();
    if (!trimmed) continue;

    let message;
    try {
      message = JSON.parse(trimmed);
    } catch (error) {
      writeMessage(output, errorResponse(null, -32700, `Parse error: ${error.message}`));
      continue;
    }

    const response = await handleMessage(message);
    if (response) writeMessage(output, response);
  }
}

async function handleMessage(message) {
  if (!message || message.jsonrpc !== '2.0' || typeof message.method !== 'string') {
    return errorResponse(message?.id ?? null, -32600, 'Invalid JSON-RPC request');
  }

  try {
    switch (message.method) {
      case 'initialize':
        return successResponse(message.id, {
          protocolVersion,
          capabilities: { tools: { listChanged: false } },
          serverInfo: { name: packageJson.name, version: packageJson.version },
        });
      case 'notifications/initialized':
        return undefined;
      case 'ping':
        return successResponse(message.id, {});
      case 'tools/list':
        return successResponse(message.id, { tools });
      case 'tools/call':
        return successResponse(message.id, await callTool(message.params));
      default:
        return errorResponse(message.id, -32601, `Method not found: ${message.method}`);
    }
  } catch (error) {
    const code = error instanceof McpProtocolError ? error.code : -32603;
    return errorResponse(message.id, code, error instanceof Error ? error.message : String(error));
  }
}

async function callTool(params = {}) {
  if (!params || typeof params !== 'object') {
    throw new McpProtocolError(-32602, 'Tool call params must be an object');
  }

  const name = params.name;
  if (typeof name !== 'string' || !name.trim()) {
    throw new McpProtocolError(-32602, 'Tool name is required');
  }

  const args = params.arguments ?? {};
  if (!args || typeof args !== 'object' || Array.isArray(args)) {
    throw new McpProtocolError(-32602, 'Tool arguments must be an object');
  }

  let result;
  try {
    result = await dispatchTool(name, args);
  } catch (error) {
    if (error instanceof McpProtocolError) throw error;
    return {
      content: [{ type: 'text', text: error instanceof Error ? error.message : String(error) }],
      isError: true,
    };
  }

  return {
    content: [{ type: 'text', text: JSON.stringify(result, null, 2) }],
    structuredContent: result,
    isError: false,
  };
}

function successResponse(id, result) {
  return { jsonrpc: '2.0', id, result };
}

function errorResponse(id, code, message) {
  return { jsonrpc: '2.0', id, error: { code, message } };
}

function writeMessage(output, message) {
  output.write(`${JSON.stringify(message)}\n`);
}

class McpProtocolError extends Error {
  constructor(code, message) {
    super(message);
    this.code = code;
  }
}

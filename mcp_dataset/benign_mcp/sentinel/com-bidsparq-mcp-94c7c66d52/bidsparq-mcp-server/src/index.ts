#!/usr/bin/env node
/**
 * BidSparq MCP server.
 *
 * Exposes BidSparq's RFP / subaward / pricing / wired-risk tools to any
 * MCP-compatible AI client (Claude Desktop, Claude Code, Cursor, Cline,
 * RooCode, etc.). Pro Max plan required.
 *
 * Configuration (via env, set in your MCP client's config):
 *   BIDSPARQ_API_KEY  (required)  bsq_live_... from https://bidsparq.com/settings/api-keys
 *   BIDSPARQ_BASE_URL (optional)  defaults to https://bidsparq.com
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
  ErrorCode,
  McpError,
} from "@modelcontextprotocol/sdk/types.js";

const SERVER_NAME = "bidsparq";
const SERVER_VERSION = "0.1.7";
const DEFAULT_BASE_URL = "https://bidsparq.com";

function log(...args: unknown[]) {
  // MCP uses stdout for protocol — only stderr is safe for human-readable logs.
  console.error("[bidsparq-mcp]", ...args);
}

const apiKey = process.env.BIDSPARQ_API_KEY;
if (!apiKey) {
  log(
    "ERROR: BIDSPARQ_API_KEY environment variable is required.\n" +
      "Create a key at https://bidsparq.com/settings/api-keys and set it in your MCP client's config.",
  );
  process.exit(1);
}
const baseUrl = (process.env.BIDSPARQ_BASE_URL || DEFAULT_BASE_URL).replace(/\/$/, "");

interface RemoteTool {
  name: string;
  description: string;
  inputSchema: object;
}

async function fetchToolSchemas(): Promise<RemoteTool[]> {
  const url = `${baseUrl}/api/mcp/tools`;
  const res = await fetch(url, {
    headers: { Authorization: `Bearer ${apiKey}`, Accept: "application/json" },
  });
  if (!res.ok) {
    const body = await res.text().catch(() => "");
    if (res.status === 401) {
      throw new Error(
        `Invalid BIDSPARQ_API_KEY. Create a new key at ${baseUrl}/settings/api-keys.`,
      );
    }
    if (res.status === 403) {
      throw new Error(
        `MCP requires the Pro Max plan. Upgrade at ${baseUrl}/plan. Server response: ${body.slice(0, 200)}`,
      );
    }
    if (res.status === 503) {
      throw new Error(
        `BidSparq MCP is not yet enabled in your account. Email hello@bidsparq.com for early access.`,
      );
    }
    throw new Error(`Failed to fetch tools (HTTP ${res.status}): ${body.slice(0, 200)}`);
  }
  const data = (await res.json()) as { tools: RemoteTool[] };
  return data.tools ?? [];
}

async function callRemoteTool(name: string, args: Record<string, unknown>): Promise<string> {
  const url = `${baseUrl}/api/mcp/tool`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${apiKey}`,
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({ tool: name, args }),
  });
  const text = await res.text();
  if (!res.ok) {
    if (res.status === 401) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `Invalid BIDSPARQ_API_KEY. Create a new one at ${baseUrl}/settings/api-keys.`,
      );
    }
    if (res.status === 403) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `Pro Max plan required. Upgrade at ${baseUrl}/plan.`,
      );
    }
    if (res.status === 429) {
      throw new McpError(
        ErrorCode.InvalidRequest,
        `Daily message limit reached. Quota resets at midnight UTC. Detail: ${text.slice(0, 200)}`,
      );
    }
    throw new McpError(
      ErrorCode.InternalError,
      `BidSparq tool '${name}' failed (HTTP ${res.status}): ${text.slice(0, 300)}`,
    );
  }
  try {
    const parsed = JSON.parse(text) as { result?: unknown };
    // Tool results are JSON strings; return them as-is for the AI to parse.
    if (typeof parsed.result === "string") return parsed.result;
    return JSON.stringify(parsed.result ?? parsed);
  } catch {
    return text;
  }
}

async function main() {
  log(`Starting (base=${baseUrl})`);
  const tools = await fetchToolSchemas();
  log(`Loaded ${tools.length} tools from BidSparq`);

  const server = new Server(
    { name: SERVER_NAME, version: SERVER_VERSION },
    { capabilities: { tools: {} } },
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args } = request.params;
    const result = await callRemoteTool(name, (args ?? {}) as Record<string, unknown>);
    return { content: [{ type: "text", text: result }] };
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);
  log("Ready");
}

main().catch((err) => {
  log("Fatal:", err instanceof Error ? err.message : String(err));
  process.exit(1);
});

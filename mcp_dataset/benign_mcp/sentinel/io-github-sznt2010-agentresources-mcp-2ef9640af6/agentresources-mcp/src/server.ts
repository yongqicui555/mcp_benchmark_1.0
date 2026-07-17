import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";

import type { McpToolDefinition, ToolContext } from "./types.js";
import { trustCardTool } from "./tools/trust-card.js";
import { telemetryTool } from "./tools/telemetry.js";
import { memoryTool } from "./tools/memory.js";
import { signingKeyTool } from "./tools/signing-keys.js";

const PACKAGE_VERSION = "0.1.0";

/**
 * Build a configured MCP server exposing the operational AR tools. The server
 * is transport-agnostic — pass it to `StdioServerTransport` for the canonical
 * `npx @agentresources/mcp` flow, or wire it into a custom transport for
 * embedding inside another MCP host.
 */
export function createMcpServer(ctx: ToolContext): Server {
  const tools: McpToolDefinition[] = [trustCardTool, telemetryTool, memoryTool, signingKeyTool];
  const byName = new Map(tools.map((t) => [t.name, t]));

  const server = new Server(
    { name: "agent-resources-mcp", version: PACKAGE_VERSION },
    { capabilities: { tools: {} } },
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: tools.map((t) => ({
      name: t.name,
      description: t.description,
      inputSchema: t.inputSchema,
    })),
  }));

  server.setRequestHandler(CallToolRequestSchema, async (req) => {
    const tool = byName.get(req.params.name);
    if (!tool) {
      return {
        isError: true,
        content: [{ type: "text", text: `Unknown tool: ${req.params.name}` }],
      };
    }
    try {
      const result = await tool.handler(req.params.arguments ?? {}, ctx);
      return { content: [{ type: "text", text: JSON.stringify(result, null, 2) }] };
    } catch (err) {
      const message = err instanceof Error ? err.message : String(err);
      return { isError: true, content: [{ type: "text", text: `Tool error: ${message}` }] };
    }
  });

  return server;
}

/**
 * Default stdio entrypoint used by `bin/agent-resources-mcp.js`.
 */
export async function startStdioServer(): Promise<void> {
  const ctx: ToolContext = {
    apiUrl: process.env["AR_API_URL"] ?? "https://api.agentresources.xyz",
    ...(process.env["AR_SESSION_TOKEN"] ? { token: process.env["AR_SESSION_TOKEN"] } : {}),
  };
  const server = createMcpServer(ctx);
  const transport = new StdioServerTransport();
  await server.connect(transport);
}

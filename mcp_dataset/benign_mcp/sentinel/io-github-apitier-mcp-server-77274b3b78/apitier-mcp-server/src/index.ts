#!/usr/bin/env node
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import { getConfig, resolvePortalKeys } from "./client.js";
import { buildActiveTools, buildRunners } from "./tools/registry.js";

async function main() {
  // Two auth modes:
  //   1. APITIER_MCP_KEY — single portal token, resolves service keys via portal API
  //   2. Individual APITIER_*_KEY env vars — direct service keys (legacy / dev)
  const mcpToken = process.env.APITIER_MCP_KEY;
  const config = mcpToken ? await resolvePortalKeys(mcpToken) : getConfig();

  const activeTools = buildActiveTools(config);
  const runners = buildRunners(config);

  const server = new Server(
    { name: "apitier-mcp-server", version: "1.2.0" },
    { capabilities: { tools: {} } }
  );

  server.setRequestHandler(ListToolsRequestSchema, async () => ({
    tools: activeTools,
  }));

  server.setRequestHandler(CallToolRequestSchema, async (request) => {
    const { name, arguments: args = {} } = request.params;
    const runner = runners.get(name);
    if (!runner) {
      return {
        content: [{ type: "text" as const, text: `Unknown tool: ${name}` }],
        isError: true,
      };
    }
    try {
      const result = await runner(args as Record<string, unknown>, config);
      return { content: [{ type: "text" as const, text: result }] };
    } catch (error) {
      const message = error instanceof Error ? error.message : String(error);
      return {
        content: [{ type: "text" as const, text: `Error: ${message}` }],
        isError: true,
      };
    }
  });

  const transport = new StdioServerTransport();
  await server.connect(transport);
}

main().catch((err) => {
  process.stderr.write(`Fatal: ${err instanceof Error ? err.message : String(err)}\n`);
  process.exit(1);
});

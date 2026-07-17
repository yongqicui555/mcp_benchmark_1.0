#!/usr/bin/env node
/**
 * DepScope MCP — stdio entry point.
 * Used by `npx depscope-mcp` from Claude Desktop / Cursor MCP configs.
 */
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { TOOLS, handleToolCall, SERVER_INSTRUCTIONS } from "./tools.js";

const server = new Server(
  { name: "depscope", version: "0.9.0" },
  {
    capabilities: { tools: {} },
    instructions: SERVER_INSTRUCTIONS,
  }
);

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));
server.setRequestHandler(CallToolRequestSchema, async (req) =>
  handleToolCall(req.params.name, req.params.arguments || {})
);

await server.connect(new StdioServerTransport());

import { startStdioServer } from "../server.js";

/**
 * `ar mcp` — start the operational MCP server on stdio. Mirror of the
 * `agent-resources-mcp` bin shim; the duplication is intentional so users
 * who only install `@agentresources/mcp` for the CLI still get the server.
 */
export async function runMcp(): Promise<void> {
  await startStdioServer();
}

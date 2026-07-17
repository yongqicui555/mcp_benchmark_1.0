/**
 * @agentresources/mcp — operational Model Context Protocol server + `ar` CLI.
 *
 * Public exports for embedding the MCP tool implementations in another host
 * (e.g. inline inside an agent runtime). The standalone server entrypoint
 * lives in ./server, and the CLI in ./cli/index.
 */

export { createMcpServer } from "./server.js";
export { trustCardTool } from "./tools/trust-card.js";
export { telemetryTool } from "./tools/telemetry.js";
export { memoryTool } from "./tools/memory.js";
export { signingKeyTool } from "./tools/signing-keys.js";
export type { ToolContext } from "./types.js";

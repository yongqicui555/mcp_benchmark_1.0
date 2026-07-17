#!/usr/bin/env node

/**
 * Summit53 MCP Server — thin mcp-remote wrapper
 *
 * This package is a convenience wrapper around mcp-remote that connects
 * MCP clients to the hosted Summit53 MCP server via OAuth 2.0.
 *
 * On first run, a browser window opens for OAuth sign-in with your
 * Summit53 account. Tokens are cached locally and refresh automatically.
 *
 * Usage:
 *   npx @summit53/mcp-server
 *
 * Or in your MCP client config:
 *   {
 *     "mcpServers": {
 *       "summit53": {
 *         "command": "npx",
 *         "args": ["@summit53/mcp-server"]
 *       }
 *     }
 *   }
 *
 * This is equivalent to:
 *   npx mcp-remote https://api.summit53.io/mcp/
 */

import { spawn } from "child_process";
import { fileURLToPath } from "url";

const SUMMIT53_URL = process.env.SUMMIT53_URL || "https://api.summit53.io/mcp/";

// Delegate to mcp-remote, passing through stdio
const child = spawn(
  "npx",
  ["mcp-remote", SUMMIT53_URL],
  {
    stdio: "inherit",
    env: process.env,
    shell: true,
  }
);

child.on("error", (err) => {
  console.error("Failed to start mcp-remote:", err.message);
  console.error("\nMake sure mcp-remote is available: npx mcp-remote --help");
  process.exit(1);
});

child.on("exit", (code) => {
  process.exit(code ?? 0);
});

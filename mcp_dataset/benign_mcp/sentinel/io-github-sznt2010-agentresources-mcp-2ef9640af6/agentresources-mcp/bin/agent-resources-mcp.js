#!/usr/bin/env node
// `agent-resources-mcp` bin shim. Starts the MCP server on stdio.
require("../dist/server.js")
  .startStdioServer()
  .catch((err) => {
    // eslint-disable-next-line no-console
    console.error(err && err.stack ? err.stack : err);
    process.exit(1);
  });

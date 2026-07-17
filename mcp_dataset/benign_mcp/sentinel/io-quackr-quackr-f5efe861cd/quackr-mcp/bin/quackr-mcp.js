#!/usr/bin/env node
/**
 * quackr-mcp — stdio launcher for the hosted Quackr MCP server.
 *
 * Bridges stdio-only MCP clients (e.g. Claude Desktop's JSON config) to the
 * remote Streamable HTTP endpoint at https://mcp.quackr.io/ via `mcp-remote`,
 * injecting the API key as an Authorization: Bearer header.
 *
 * API key resolution (first match wins):
 *   1. --api-key <key>   CLI flag
 *   2. QUACKR_API_KEY    environment variable
 *
 * Any extra CLI args are forwarded to mcp-remote unchanged.
 */

import { spawn } from "node:child_process";
import { createRequire } from "node:module";

const ENDPOINT = "https://mcp.quackr.io/";

function parseArgs(argv) {
  const passthrough = [];
  let apiKey = process.env.QUACKR_API_KEY || "";

  for (let i = 0; i < argv.length; i++) {
    const arg = argv[i];
    if (arg === "--api-key") {
      apiKey = argv[++i] || "";
    } else if (arg.startsWith("--api-key=")) {
      apiKey = arg.slice("--api-key=".length);
    } else {
      passthrough.push(arg);
    }
  }

  return { apiKey: apiKey.trim(), passthrough };
}

function fail(message) {
  process.stderr.write(`quackr-mcp: ${message}\n`);
  process.exit(1);
}

const { apiKey, passthrough } = parseArgs(process.argv.slice(2));

if (!apiKey) {
  fail(
    "missing API key. Set QUACKR_API_KEY or pass --api-key <key>.\n" +
      "Get a key from your profile page at https://quackr.io"
  );
}

// Resolve mcp-remote's CLI entry from our own dependency tree so we don't rely
// on a separate global install or a network fetch at runtime.
const require = createRequire(import.meta.url);
let mcpRemoteEntry;
try {
  mcpRemoteEntry = require.resolve("mcp-remote/dist/proxy.js");
} catch {
  try {
    mcpRemoteEntry = require.resolve("mcp-remote");
  } catch {
    fail("could not locate the 'mcp-remote' dependency. Try reinstalling quackr-mcp.");
  }
}

// Quackr is Streamable HTTP only (no SSE), so default to the http-only
// transport to skip the misleading SSE fallback. Respect an explicit override.
const hasTransport = passthrough.some(
  (a) => a === "--transport" || a.startsWith("--transport=")
);

const args = [
  mcpRemoteEntry,
  ENDPOINT,
  "--header",
  `Authorization: Bearer ${apiKey}`,
  ...(hasTransport ? [] : ["--transport", "http-only"]),
  ...passthrough,
];

const child = spawn(process.execPath, args, { stdio: "inherit" });

child.on("error", (err) => fail(`failed to start mcp-remote: ${err.message}`));
child.on("exit", (code, signal) => {
  if (signal) {
    process.kill(process.pid, signal);
  } else {
    process.exit(code ?? 0);
  }
});

for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, () => {
    if (!child.killed) child.kill(sig);
  });
}

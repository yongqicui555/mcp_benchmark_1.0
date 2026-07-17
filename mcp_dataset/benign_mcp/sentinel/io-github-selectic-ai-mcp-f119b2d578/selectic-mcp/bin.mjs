#!/usr/bin/env node
// Selectic MCP connector: bridges a local stdio MCP client (Claude Desktop,
// Cursor, Cline, …) to Selectic's hosted MCP endpoint. Auth is OAuth — mcp-remote
// opens a browser the first time so you can sign in. No API key needed.
import { createRequire } from "node:module";
import { spawn } from "node:child_process";

const URL = process.env.SELECTIC_MCP_URL || "https://selectic.ai/api/mcp";
const require = createRequire(import.meta.url);
const proxy = require.resolve("mcp-remote/dist/proxy.js");
const child = spawn(process.execPath, [proxy, URL], { stdio: "inherit" });
child.on("exit", (code) => process.exit(code ?? 0));

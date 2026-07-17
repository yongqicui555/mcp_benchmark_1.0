#!/usr/bin/env node

/**
 * Prompeteer MCP Server — Remote Connector
 *
 * This package connects MCP clients to the Prompeteer remote server.
 * No local installation needed — all processing happens at https://prompeteer.ai/mcp
 *
 * Usage:
 *   npx @prompeteer/mcp-server
 *
 * Or add to your MCP client config:
 *   Server URL (SSE): https://prompeteer.ai/mcp/sse
 *   Server URL (Streamable HTTP): https://prompeteer.ai/mcp
 *   Authentication: OAuth 2.1
 */

const SERVER_URL_SSE = "https://prompeteer.ai/mcp/sse";
const SERVER_URL_HTTP = "https://prompeteer.ai/mcp";
const DOCS_URL = "https://github.com/prompeteer/prompeteer-mcp";

console.log(`
╔══════════════════════════════════════════════════════════════╗
║                    Prompeteer MCP Server                     ║
║          AI Prompt Engineering for 140+ Platforms             ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Prompeteer is a remote MCP server — no local server needed. ║
║                                                              ║
║  Add one of these URLs to your MCP client:                   ║
║                                                              ║
║  SSE:              ${SERVER_URL_SSE}            ║
║  Streamable HTTP:  ${SERVER_URL_HTTP}                ║
║                                                              ║
║  Authentication:   OAuth 2.1 (automatic redirect)            ║
║                                                              ║
║  Tools:                                                      ║
║    • generate_prompt    — Generate prompts for 140+ platforms ║
║    • score_prompt       — 16-dimension quality analysis       ║
║    • list_prompts       — Browse your PromptDrive library     ║
║    • get_prompt         — Retrieve a saved prompt             ║
║    • save_to_promptdrive — Save to PromptDrive                ║
║                                                              ║
║  Docs: ${DOCS_URL}            ║
║  Site: https://prompeteer.ai                                 ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
`);

process.exit(0);

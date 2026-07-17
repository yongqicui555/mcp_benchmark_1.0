#!/usr/bin/env node
/**
 * DepScope MCP — Streamable HTTP entry point.
 * Exposes the same 21 tools over MCP Streamable HTTP so remote agents
 * (Claude Desktop, Cursor, Windsurf with remote-MCP support) can connect with
 * just a URL, no `npm install -g`.
 *
 * Listens on DEPSCOPE_MCP_PORT (default 8001) at path /mcp.
 * Session state kept in-memory per spec: client sends Mcp-Session-Id after init.
 */
import http from "node:http";
import { randomUUID } from "node:crypto";
import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/streamableHttp.js";
import { CallToolRequestSchema, ListToolsRequestSchema } from "@modelcontextprotocol/sdk/types.js";
import { TOOLS, handleToolCall, SERVER_INSTRUCTIONS } from "./tools.js";

const PORT = Number(process.env.DEPSCOPE_MCP_PORT || 8001);
const HOST = process.env.DEPSCOPE_MCP_HOST || "127.0.0.1";

// One MCP Server instance + one transport per session.
const sessions = new Map();

function createServer() {
  const s = new Server(
    { name: "depscope", version: "0.9.0" },
    {
      capabilities: { tools: {} },
      instructions: SERVER_INSTRUCTIONS,
    }
  );
  s.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));
  s.setRequestHandler(CallToolRequestSchema, async (req) =>
    handleToolCall(req.params.name, req.params.arguments || {})
  );
  return s;
}

const httpServer = http.createServer(async (req, res) => {
  // Simple health + root.
  if (req.method === "GET" && (req.url === "/" || req.url === "/health")) {
    res.writeHead(200, { "Content-Type": "application/json" });
    res.end(JSON.stringify({
      service: "depscope-mcp-http",
      version: "0.9.0",
      tools: TOOLS.length,
      endpoint: "/mcp",
      sessions: sessions.size,
    }));
    return;
  }

  if (!req.url || !req.url.startsWith("/mcp")) {
    res.writeHead(404).end("Not found");
    return;
  }

  const sessionId = req.headers["mcp-session-id"];
  let transport = sessionId ? sessions.get(sessionId) : undefined;

  // New session: only allowed on POST (initialize request).
  if (!transport) {
    if (req.method !== "POST") {
      // Friendly response for GET (browser open) — explain how to connect.
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({
        service: "depscope-mcp",
        protocol: "MCP Streamable HTTP",
        version: "0.9.0",
        tools: TOOLS.length,
        ecosystems: 19,
        homepage: "https://depscope.dev",
        docs: "https://depscope.dev/integrate",
        repository: "https://github.com/cuttalo/depscope-mcp",
        usage: {
          claude_desktop_config: {
            mcpServers: {
              depscope: { url: "https://mcp.depscope.dev/mcp" }
            }
          },
          local_npx: "npx -y depscope-mcp",
          curl_initialize: "POST /mcp with body {\"jsonrpc\":\"2.0\",\"id\":1,\"method\":\"initialize\",\"params\":{\"protocolVersion\":\"2025-06-18\",\"capabilities\":{},\"clientInfo\":{\"name\":\"my-client\",\"version\":\"1.0\"}}}"
        },
        note: "This endpoint speaks the MCP protocol. To list tools, send POST initialize first to obtain a session id.",
      }, null, 2));
      return;
    }
    transport = new StreamableHTTPServerTransport({
      sessionIdGenerator: () => randomUUID(),
      onsessioninitialized: (sid) => {
        sessions.set(sid, transport);
        console.log(`[mcp] session opened: ${sid}`);
      },
    });
    transport.onclose = () => {
      if (transport.sessionId) {
        sessions.delete(transport.sessionId);
        console.log(`[mcp] session closed: ${transport.sessionId}`);
      }
    };
    const mcpServer = createServer();
    await mcpServer.connect(transport);
  }

  try {
    await transport.handleRequest(req, res);
  } catch (e) {
    console.error("[mcp] transport error:", e);
    if (!res.headersSent) res.writeHead(500).end("Internal error");
  }
});

httpServer.listen(PORT, HOST, () => {
  console.log(`[mcp] DepScope MCP HTTP listening on http://${HOST}:${PORT}/mcp — ${TOOLS.length} tools`);
});

for (const sig of ["SIGINT", "SIGTERM"]) {
  process.on(sig, () => {
    console.log(`[mcp] ${sig} — closing ${sessions.size} sessions`);
    for (const t of sessions.values()) t.close?.();
    httpServer.close(() => process.exit(0));
  });
}

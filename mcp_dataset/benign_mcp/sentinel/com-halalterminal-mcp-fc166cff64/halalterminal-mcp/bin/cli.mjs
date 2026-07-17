#!/usr/bin/env node
import { SSEClientTransport } from "@modelcontextprotocol/sdk/client/sse.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";

const SSE_URL = process.env.HALALTERMINAL_SSE_URL || "https://mcp.halalterminal.com/sse";
const API_KEY = process.env.HALALTERMINAL_API_KEY;

function isValidKey(k) {
  return typeof k === "string" && k.startsWith("ht_") && k.length >= 20;
}

if (!isValidKey(API_KEY)) {
  console.error(
    "halalterminal-mcp: HALALTERMINAL_API_KEY is missing or malformed.\n" +
    "  Get a free key (no credit card) at https://api.halalterminal.com\n" +
    "  Then set it in your MCP client config, e.g.:\n" +
    "    \"env\": { \"HALALTERMINAL_API_KEY\": \"ht_...\" }"
  );
  process.exit(1);
}

const sse = new SSEClientTransport(new URL(SSE_URL), {
  requestInit: { headers: { "X-API-Key": API_KEY } },
});
const stdio = new StdioServerTransport();

await sse.start();
await stdio.start();

stdio.onmessage = (m) => sse.send(m);
sse.onmessage   = (m) => stdio.send(m);

const exitClean = () => process.exit(0);
sse.onclose   = exitClean;
stdio.onclose = exitClean;

sse.onerror = (e) => {
  const msg = e?.message ?? String(e);
  if (msg.includes("401")) {
    console.error("halalterminal-mcp: 401 Unauthorized — check HALALTERMINAL_API_KEY at https://halalterminal.com/dashboard");
  } else if (msg.includes("403")) {
    console.error("halalterminal-mcp: 403 Forbidden — key may be deactivated. Visit https://halalterminal.com/dashboard");
  } else {
    console.error("halalterminal-mcp SSE error:", msg);
  }
  process.exit(1);
};

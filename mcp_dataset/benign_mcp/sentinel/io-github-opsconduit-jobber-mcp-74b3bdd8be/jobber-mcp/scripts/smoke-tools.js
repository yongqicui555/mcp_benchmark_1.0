import { Client } from "@modelcontextprotocol/sdk/client/index.js";
import { StdioClientTransport } from "@modelcontextprotocol/sdk/client/stdio.js";

const expectedTools = [
  "jobber_auth_url",
  "jobber_exchange_code",
  "jobber_refresh_token",
  "jobber_account",
  "jobber_clients_sample",
  "jobber_graphql_read"
];

const client = new Client({ name: "opsconduit-smoke", version: "0.1.0" });
const transport = new StdioClientTransport({
  command: process.execPath,
  args: ["src/server.js"]
});

await client.connect(transport);
const tools = await client.listTools();
await client.close();

const names = tools.tools.map(tool => tool.name).sort();
const missing = expectedTools.filter(name => !names.includes(name));

if (missing.length) {
  console.error(`Missing MCP tools: ${missing.join(", ")}`);
  process.exit(1);
}

console.log(`MCP smoke ok: ${names.join(", ")}`);

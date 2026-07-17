#!/usr/bin/env node
// ScreenshotInk MCP server (stdio).
//   npx @screenshotink/mcp --key sk_live_…
//   …or set SCREENSHOTINK_API_KEY in the environment.
// Free API key: https://screenshotink.com/signup

'use strict';

const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const { buildServer } = require('../lib/tools.js');

function getKey() {
  const i = process.argv.indexOf('--key');
  if (i !== -1 && process.argv[i + 1]) return process.argv[i + 1].trim();
  const eq = process.argv.find((a) => a.startsWith('--key='));
  if (eq) return eq.slice(6).trim();
  return (process.env.SCREENSHOTINK_API_KEY || '').trim();
}

const key = getKey();
if (!key || !key.startsWith('sk_live_')) {
  console.error(
    'screenshotink-mcp: missing API key.\n' +
    '  Pass --key sk_live_…  or set SCREENSHOTINK_API_KEY.\n' +
    '  Get a free key (100 captures/month): https://screenshotink.com/signup'
  );
  process.exit(1);
}

(async () => {
  const server = buildServer(key);
  await server.connect(new StdioServerTransport());
  console.error('screenshotink-mcp ready (stdio) — 5 tools');
})().catch((err) => {
  console.error('screenshotink-mcp failed to start:', err);
  process.exit(1);
});

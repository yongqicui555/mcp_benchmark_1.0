#!/usr/bin/env node
/*
 * LocalGym read-only MCP server (dependency-free stdio JSON-RPC subset).
 *
 * Usage:
 *   LOCALGYM_API_BASE=https://localgym.uk node scripts/localgym-mcp-server.cjs
 *
 * Hermes/Claude-style MCP config:
 *   {
 *     "mcpServers": {
 *       "localgym": {
 *         "command": "node",
 *         "args": ["/absolute/path/to/scripts/localgym-mcp-server.cjs"],
 *         "env": { "LOCALGYM_API_BASE": "https://localgym.uk" }
 *       }
 *     }
 *   }
 */

const { version: PACKAGE_VERSION } = require('../package.json');
const API_BASE = (process.env.LOCALGYM_API_BASE || 'https://localgym.uk').replace(/\/$/, '');
const MCP_RATE_LIMIT_WINDOW_MS = Number(process.env.LOCALGYM_MCP_RATE_LIMIT_WINDOW_MS || 60_000);
const MCP_RATE_LIMIT_MAX = Number(process.env.LOCALGYM_MCP_RATE_LIMIT_MAX || 60);
let mcpRateLimitBucket = { count: 0, resetAt: Date.now() + MCP_RATE_LIMIT_WINDOW_MS };

function enforceLocalRateLimit() {
  const now = Date.now();
  if (now >= mcpRateLimitBucket.resetAt) {
    mcpRateLimitBucket = { count: 0, resetAt: now + MCP_RATE_LIMIT_WINDOW_MS };
  }
  mcpRateLimitBucket.count += 1;
  if (mcpRateLimitBucket.count > MCP_RATE_LIMIT_MAX) {
    const retryAfterSeconds = Math.max(Math.ceil((mcpRateLimitBucket.resetAt - now) / 1000), 1);
    throw new Error(`LocalGym MCP local rate limit exceeded (${MCP_RATE_LIMIT_MAX} requests per ${Math.ceil(MCP_RATE_LIMIT_WINDOW_MS / 1000)}s). Retry after ${retryAfterSeconds}s or contact enquiries@localgym.uk for high-volume/commercial access.`);
  }
}

const tools = [
  {
    name: 'search_gyms',
    description: 'Search UK gyms by name, keyword, location, or user intent using LocalGym data.',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'Gym name, keyword, or user intent' },
        location: { type: 'string', description: 'Town, city, county, region, or postcode text' },
        limit: { type: 'integer', minimum: 1, maximum: 25, default: 10 },
      },
    },
  },
  {
    name: 'get_gym_details',
    description: 'Get structured detail for a LocalGym gym slug.',
    inputSchema: {
      type: 'object',
      properties: { slug: { type: 'string' } },
      required: ['slug'],
    },
  },
  {
    name: 'recommend_gyms',
    description: 'Recommend gyms for a user goal and location.',
    inputSchema: {
      type: 'object',
      properties: {
        intent: { type: 'string', description: 'User goal, e.g. beginner-friendly gym with personal training' },
        location: { type: 'string' },
        limit: { type: 'integer', minimum: 1, maximum: 25, default: 5 },
      },
    },
  },
  {
    name: 'compare_gyms',
    description: 'Compare several LocalGym gym slugs.',
    inputSchema: {
      type: 'object',
      properties: { slugs: { type: 'array', items: { type: 'string' }, minItems: 1, maxItems: 8 } },
      required: ['slugs'],
    },
  },
];

async function api(path, params = {}) {
  enforceLocalRateLimit();
  const url = new URL(path, API_BASE);
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') url.searchParams.set(key, String(value));
  });
  const response = await fetch(url, { headers: { 'User-Agent': 'LocalGym-MCP/0.1 (+https://localgym.uk/agent)' } });
  const text = await response.text();
  let json;
  try { json = JSON.parse(text); } catch (_) { json = { text }; }
  if (!response.ok) throw new Error(`LocalGym API ${response.status}: ${JSON.stringify(json).slice(0, 500)}`);
  return json;
}

async function callTool(name, args = {}) {
  if (name === 'search_gyms') {
    return api('/api/gyms/search', { q: args.query || args.q || '', location: args.location || '', limit: args.limit || 10 });
  }
  if (name === 'get_gym_details') {
    if (!args.slug) throw new Error('slug is required');
    return api(`/api/gyms/${encodeURIComponent(args.slug)}`);
  }
  if (name === 'recommend_gyms') {
    return api('/api/agent/recommendations', { intent: args.intent || args.query || '', location: args.location || '', limit: args.limit || 5 });
  }
  if (name === 'compare_gyms') {
    const slugs = Array.isArray(args.slugs) ? args.slugs.join(',') : String(args.slugs || '');
    if (!slugs) throw new Error('slugs is required');
    return api('/api/agent/compare', { slugs });
  }
  throw new Error(`Unknown tool: ${name}`);
}

let buffer = Buffer.alloc(0);
process.stdin.on('data', (chunk) => {
  buffer = Buffer.concat([buffer, chunk]);
  drain().catch((err) => console.error('[localgym-mcp]', err));
});

async function drain() {
  while (true) {
    const headerEnd = buffer.indexOf('\r\n\r\n');
    if (headerEnd === -1) return;
    const header = buffer.slice(0, headerEnd).toString('utf8');
    const match = header.match(/Content-Length:\s*(\d+)/i);
    if (!match) throw new Error('Missing Content-Length header');
    const length = Number(match[1]);
    const start = headerEnd + 4;
    if (buffer.length < start + length) return;
    const body = buffer.slice(start, start + length).toString('utf8');
    buffer = buffer.slice(start + length);
    await handle(JSON.parse(body));
  }
}

function send(message) {
  const body = JSON.stringify(message);
  process.stdout.write(`Content-Length: ${Buffer.byteLength(body)}\r\n\r\n${body}`);
}

async function handle(msg) {
  if (!msg || !msg.method) return;
  try {
    if (msg.method === 'initialize') {
      return send({
        jsonrpc: '2.0',
        id: msg.id,
        result: {
          protocolVersion: '2024-11-05',
          capabilities: { tools: {} },
          serverInfo: { name: 'localgym', version: PACKAGE_VERSION },
        },
      });
    }
    if (msg.method === 'notifications/initialized') return;
    if (msg.method === 'tools/list') {
      return send({ jsonrpc: '2.0', id: msg.id, result: { tools } });
    }
    if (msg.method === 'tools/call') {
      const result = await callTool(msg.params?.name, msg.params?.arguments || {});
      return send({
        jsonrpc: '2.0',
        id: msg.id,
        result: { content: [{ type: 'text', text: JSON.stringify(result, null, 2) }] },
      });
    }
    send({ jsonrpc: '2.0', id: msg.id, error: { code: -32601, message: `Method not found: ${msg.method}` } });
  } catch (err) {
    send({ jsonrpc: '2.0', id: msg.id, error: { code: -32000, message: err.message } });
  }
}

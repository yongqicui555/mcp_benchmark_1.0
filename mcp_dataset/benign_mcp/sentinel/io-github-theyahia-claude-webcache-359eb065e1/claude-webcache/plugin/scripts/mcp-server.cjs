#!/usr/bin/env node
'use strict';
process.removeAllListeners('warning');
const { Server } = require('@modelcontextprotocol/sdk/server/index.js');
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js');
const {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} = require('@modelcontextprotocol/sdk/types.js');

const cache = require('../src/cache.js');
const PLUGIN_MANIFEST = require('../.claude-plugin/plugin.json');

const server = new Server(
  { name: 'claude-webcache', version: PLUGIN_MANIFEST.version },
  { capabilities: { tools: {} } }
);

const TOOLS = [
  {
    name: 'cached_fetch',
    description:
      'Look up a URL+prompt pair in the local WebFetch cache. Returns cached output if present (instant), or "[CACHE_MISS] <url>" if not. On CACHE_MISS, call WebFetch, then call cache_store with the result. Same URL+prompt across sessions hits the cache.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'The URL to fetch' },
        prompt: { type: 'string', description: 'The prompt/instruction for the WebFetch' },
      },
      required: ['url', 'prompt'],
    },
  },
  {
    name: 'cached_search',
    description:
      'Look up a WebSearch query in the local cache (\'websearch\' namespace, short TTL). Returns cached results if a fresh entry exists, or "[CACHE_MISS] <query>" if not. On CACHE_MISS, run WebSearch — the PostToolUse hook stores the result automatically.',
    inputSchema: {
      type: 'object',
      properties: {
        query: { type: 'string', description: 'The search query' },
      },
      required: ['query'],
    },
  },
  {
    name: 'cache_store',
    description:
      'Store a WebFetch result in the cache after a CACHE_MISS. Pass the original url, prompt, and the output text returned by WebFetch.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string' },
        prompt: { type: 'string' },
        output: { type: 'string', description: 'The output text returned by WebFetch' },
      },
      required: ['url', 'prompt', 'output'],
    },
  },
  {
    name: 'cache_stats',
    description:
      'Return cache statistics for the current namespace: total entries, total hits, miss count, hit rate, db size in bytes, evicted count, oversize_skipped count, last hook error timestamp, top 5 URLs by hit count.',
    inputSchema: {
      type: 'object',
      properties: {
        global: { type: 'boolean', description: 'If true, return stats across all namespaces (default false).' },
      },
    },
  },
  {
    name: 'cache_list',
    description: 'List recently cached URLs in the current namespace (most recent first).',
    inputSchema: {
      type: 'object',
      properties: {
        limit: { type: 'number', description: 'Max entries to return (default 50)' },
        offset: { type: 'number', description: 'Skip first N entries (default 0)' },
        global: { type: 'boolean', description: 'If true, list across all namespaces.' },
      },
    },
  },
  {
    name: 'cache_invalidate',
    description:
      'Delete all cache entries for a specific URL in the current namespace (across all prompts). Returns the number of entries deleted.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string', description: 'The URL to invalidate' },
      },
      required: ['url'],
    },
  },
  {
    name: 'cache_clear',
    description:
      'Bulk-delete cache entries in the current namespace. Provide either older_than_days (safe, partial) OR confirm:"YES" (full wipe, dangerous). Returns number of entries deleted.',
    inputSchema: {
      type: 'object',
      properties: {
        older_than_days: {
          type: 'number',
          description: 'Delete entries older than N days. Safe, no confirm needed.',
        },
        confirm: {
          type: 'string',
          description: 'Set to "YES" to confirm full namespace wipe when older_than_days is not provided.',
        },
      },
    },
  },
  {
    name: 'cache_warm',
    description:
      'Batch cache pre-flight check. Pass either {entries: [{url, prompt}, ...]} for per-entry prompts OR {urls: [...], prompt} to apply the same prompt to all URLs. Returns {hits, misses, invalid} arrays — pipeline then WebFetches only misses, saving N round-trips.',
    inputSchema: {
      type: 'object',
      properties: {
        entries: {
          type: 'array',
          description: 'List of {url, prompt} pairs to check.',
          items: {
            type: 'object',
            properties: {
              url: { type: 'string' },
              prompt: { type: 'string' },
            },
            required: ['url', 'prompt'],
          },
        },
        urls: {
          type: 'array',
          description: 'List of URLs, all checked with the same prompt.',
          items: { type: 'string' },
        },
        prompt: { type: 'string', description: 'Shared prompt when using urls[]' },
      },
    },
  },
  {
    name: 'cache_refresh',
    description:
      'Force re-fetch of a URL: invalidates the existing cached entry and returns "[CACHE_MISS] <url>" so the assistant triggers WebFetch. Use when you know the upstream content changed.',
    inputSchema: {
      type: 'object',
      properties: {
        url: { type: 'string' },
        prompt: { type: 'string' },
      },
      required: ['url', 'prompt'],
    },
  },
];

server.setRequestHandler(ListToolsRequestSchema, async () => ({ tools: TOOLS }));

server.setRequestHandler(CallToolRequestSchema, async (req) => {
  const { name, arguments: args } = req.params;

  try {
    if (name === 'cached_fetch') {
      const { url, prompt } = args || {};
      if (!url || !prompt) {
        return { content: [{ type: 'text', text: 'Error: url and prompt are required' }], isError: true };
      }
      const v = cache.validateUrl(url);
      if (!v.ok) {
        return { content: [{ type: 'text', text: `Error: ${v.reason}` }], isError: true };
      }
      const hit = cache.get(url, prompt);
      if (hit) {
        return { content: [{ type: 'text', text: hit }] };
      }
      return { content: [{ type: 'text', text: `[CACHE_MISS] ${url}` }] };
    }

    if (name === 'cached_search') {
      const { query } = args || {};
      if (!query) {
        return { content: [{ type: 'text', text: 'Error: query is required' }], isError: true };
      }
      const hit = cache.getSearch(query);
      if (hit) {
        return { content: [{ type: 'text', text: hit }] };
      }
      return { content: [{ type: 'text', text: `[CACHE_MISS] ${query}` }] };
    }

    if (name === 'cache_store') {
      const { url, prompt, output } = args || {};
      if (!url || !prompt || output == null) {
        return { content: [{ type: 'text', text: 'Error: url, prompt, output required' }], isError: true };
      }
      const r = cache.set(url, prompt, output);
      if (!r || !r.ok) {
        return { content: [{ type: 'text', text: `Error: ${r ? r.reason : 'set failed'}` }], isError: true };
      }
      return { content: [{ type: 'text', text: 'stored' }] };
    }

    if (name === 'cache_stats') {
      const global = !!(args && args.global);
      const s = cache.stats({ global });
      return { content: [{ type: 'text', text: JSON.stringify(s) }] };
    }

    if (name === 'cache_list') {
      const limit = (args && typeof args.limit === 'number') ? args.limit : 50;
      const offset = (args && typeof args.offset === 'number') ? args.offset : 0;
      const global = !!(args && args.global);
      const rows = cache.list(limit, offset, { global });
      return { content: [{ type: 'text', text: JSON.stringify(rows, null, 2) }] };
    }

    if (name === 'cache_invalidate') {
      const { url } = args || {};
      if (!url) {
        return { content: [{ type: 'text', text: 'Error: url is required' }], isError: true };
      }
      const deleted = cache.invalidate(url);
      return { content: [{ type: 'text', text: JSON.stringify({ deleted }) }] };
    }

    if (name === 'cache_clear') {
      const { older_than_days, confirm } = args || {};
      const hasOlder = typeof older_than_days === 'number' && older_than_days > 0;
      if (!hasOlder && confirm !== 'YES') {
        return {
          content: [{
            type: 'text',
            text: 'Error: full cache wipe requires confirm:"YES". For safer partial clear, pass older_than_days:N.',
          }],
          isError: true,
        };
      }
      const deleted = cache.clear(hasOlder ? older_than_days : undefined);
      return { content: [{ type: 'text', text: JSON.stringify({ deleted }) }] };
    }

    if (name === 'cache_warm') {
      let entries = [];
      if (args && Array.isArray(args.entries)) {
        entries = args.entries;
      } else if (args && Array.isArray(args.urls)) {
        const sharedPrompt = args.prompt || '';
        entries = args.urls.map((u) => ({ url: u, prompt: sharedPrompt }));
      } else {
        return { content: [{ type: 'text', text: 'Error: provide entries[{url,prompt}] or urls[]+prompt' }], isError: true };
      }
      const hits = [];
      const misses = [];
      const invalid = [];
      for (const e of entries) {
        const url = e && e.url;
        const prompt = e && e.prompt;
        if (!url || prompt == null) {
          invalid.push({ url, prompt, reason: 'missing url or prompt' });
          continue;
        }
        const v = cache.validateUrl(url);
        if (!v.ok) {
          invalid.push({ url, prompt, reason: v.reason });
          continue;
        }
        const h = cache.get(url, prompt);
        if (h != null) hits.push({ url, prompt });
        else misses.push({ url, prompt });
      }
      return { content: [{ type: 'text', text: JSON.stringify({ hits, misses, invalid }) }] };
    }

    if (name === 'cache_refresh') {
      const { url, prompt } = args || {};
      if (!url || prompt == null) {
        return { content: [{ type: 'text', text: 'Error: url and prompt required' }], isError: true };
      }
      const v = cache.validateUrl(url);
      if (!v.ok) {
        return { content: [{ type: 'text', text: `Error: ${v.reason}` }], isError: true };
      }
      cache.invalidate(url);
      return { content: [{ type: 'text', text: `[CACHE_MISS] ${url}` }] };
    }

    return { content: [{ type: 'text', text: `Unknown tool: ${name}` }], isError: true };
  } catch (err) {
    return { content: [{ type: 'text', text: `Error: ${err.message}` }], isError: true };
  }
});

(async () => {
  const transport = new StdioServerTransport();
  await server.connect(transport);
})();

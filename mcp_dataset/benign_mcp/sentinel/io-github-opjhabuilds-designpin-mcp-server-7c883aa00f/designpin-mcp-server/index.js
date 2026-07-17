#!/usr/bin/env node
'use strict'

const { McpServer }            = require('@modelcontextprotocol/sdk/server/mcp.js')
const { StdioServerTransport } = require('@modelcontextprotocol/sdk/server/stdio.js')
const { z }                    = require('zod')

// ── CLI / env config ─────────────────────────────────────────────────
// Supports both --flag=value and --flag value forms. Bare --flag becomes true.
function parseArgs(argv) {
  const out = {}
  for (let i = 0; i < argv.length; i++) {
    const a = argv[i]
    if (!a.startsWith('--')) continue
    const eq = a.indexOf('=')
    if (eq >= 0) {
      out[a.slice(2, eq)] = a.slice(eq + 1)
    } else {
      const next = argv[i + 1]
      out[a.slice(2)] = next && !next.startsWith('--') ? argv[++i] : true
    }
  }
  return out
}

const HELP_TEXT = `designpin-mcp v0.1.2 — MCP server for DesignPin

Usage:
  npx @designpin/mcp-server --api-key <key> --project-id <id>

Flags:
  --api-key      DesignPin API key (or set DESIGNPIN_API_KEY)
  --project-id   Target project ID (or set DESIGNPIN_PROJECT_ID)
  --base-url     API base URL (default: https://designpin.pro)
  --version      Print version and exit
  --help         Show this help

Get an API key: https://designpin.pro → Project → API & Integrations
`

// Short-circuit before any server setup.
const rawArgs = process.argv.slice(2)
if (rawArgs.includes('--help')    || rawArgs.includes('-h')) {
  process.stderr.write(HELP_TEXT)
  process.exit(0)
}
if (rawArgs.includes('--version') || rawArgs.includes('-v')) {
  process.stdout.write('0.1.2\n')
  process.exit(0)
}

const args = parseArgs(rawArgs)
const API_KEY    = args['api-key']    || process.env.DESIGNPIN_API_KEY    || ''
const PROJECT_ID = args['project-id'] || process.env.DESIGNPIN_PROJECT_ID || ''
const BASE_URL   = args['base-url']   || process.env.DESIGNPIN_BASE_URL   || 'https://designpin.pro'

// ── REST API helpers ─────────────────────────────────────────────────
async function apiCall(path, { method = 'GET', body, auth = false } = {}) {
  const headers = { 'Content-Type': 'application/json' }
  if (auth && API_KEY) headers.Authorization = `Bearer ${API_KEY}`
  let res
  try {
    res = await fetch(`${BASE_URL}${path}`, {
      method,
      headers,
      body: body ? JSON.stringify(body) : undefined,
    })
  } catch (err) {
    return { ok: false, error: `Network error: ${err.message}` }
  }
  let parsed = {}
  let parseFailed = false
  try { parsed = await res.json() } catch { parseFailed = true }
  if (!res.ok) {
    if (parseFailed) return { ok: false, error: `HTTP ${res.status} (non-JSON response)` }
    return { ok: false, error: `${parsed.error || 'unknown error'} (HTTP ${res.status})` }
  }
  return { ok: true, body: parsed }
}

const errorResult = (message) => ({ content: [{ type: 'text', text: `Error: ${message}` }], isError: true })
const jsonResult  = (data)    => ({ content: [{ type: 'text', text: JSON.stringify(data, null, 2) }] })

// ── Tool handlers ────────────────────────────────────────────────────
async function handleCreateShareLink({ html, title, authorName }) {
  const result = await apiCall('/api/v1/quick-share', {
    method: 'POST',
    body: { html, title, ...(authorName ? { authorName } : {}) },
  })
  if (!result.ok) return errorResult(result.error)
  return jsonResult(result.body)
}

async function handleUploadVersion({ html, moduleId, description }) {
  if (!API_KEY)    return errorResult('API key is required for uploadVersion. Set DESIGNPIN_API_KEY env var or --api-key flag.')
  if (!PROJECT_ID) return errorResult('Project ID is required for uploadVersion. Set DESIGNPIN_PROJECT_ID env var or --project-id flag.')
  const result = await apiCall('/api/v1/push', {
    method: 'POST',
    auth: true,
    body: { html, projectId: PROJECT_ID, moduleId, ...(description ? { description } : {}) },
  })
  if (!result.ok) return errorResult(result.error)
  return jsonResult(result.body)
}

async function handleListComments({ moduleId, versionId }) {
  if (!API_KEY) return errorResult('API key is required for listComments. Set DESIGNPIN_API_KEY env var or --api-key flag.')
  const path = `/api/v1/comments/${encodeURIComponent(moduleId)}/${encodeURIComponent(versionId)}`
  const result = await apiCall(path, { method: 'GET', auth: true })
  if (!result.ok) return errorResult(result.error)
  return jsonResult(result.body)
}

// ── Server setup ─────────────────────────────────────────────────────
async function main() {
  const server = new McpServer({ name: 'designpin-mcp', version: '0.1.2' })

  server.registerTool('createShareLink', {
    description: 'Create a public review link for an HTML prototype. No project setup required — creates a brand-new throwaway project. Rate-limited to 10 requests/hour per IP. Use this for one-shot sharing of prototypes.',
    inputSchema: {
      html:       z.string().describe('Complete HTML document to share'),
      title:      z.string().describe('Display name for the share, max 80 chars'),
      authorName: z.string().optional().describe('Optional author name shown on review page'),
    },
  }, handleCreateShareLink)

  server.registerTool('uploadVersion', {
    description: 'Upload a new HTML version to an existing DesignPin module. Auto-increments versionNumber. Requires API key + projectId + moduleId. Use this to push design iterations into an existing project for review.',
    inputSchema: {
      html:        z.string().describe('Complete HTML for the new version'),
      moduleId:    z.string().describe('Target module ID within the project'),
      description: z.string().optional().describe('Optional version description shown in sidebar'),
    },
  }, handleUploadVersion)

  server.registerTool('listComments', {
    description: 'Fetch comments visible on a specific version of a DesignPin module. Returns comments using chronological cutoff semantics matching the web UI: a comment is visible on version V if its origin version is V or any earlier version. Useful for fetching reviewer feedback to incorporate into design revisions.',
    inputSchema: {
      moduleId:  z.string().describe('Module ID to fetch comments for'),
      versionId: z.string().describe('Specific version ID to view comments on (chronological cutoff)'),
    },
  }, handleListComments)

  const transport = new StdioServerTransport()
  await server.connect(transport)
  console.error('[designpin-mcp] connected via stdio')
}

main().catch(err => {
  console.error('[designpin-mcp] fatal:', err.message || err)
  process.exit(1)
})

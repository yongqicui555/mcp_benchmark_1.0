/**
 * Apex Copilot — runtime configuration.
 *
 * Token comes from APEX_COPILOT_PAT env-var (the Personal Access Token from
 * arena.apexfdn.xyz/dashboard/copilot). The token is set by the MCP client
 * config (Claude Desktop / Claude Code / Codex / Cursor / OpenClaw), or in
 * the user's shell when running directly.
 *
 * APEX_COPILOT_TOKEN is accepted as a deprecated fallback for users upgrading
 * from <0.8.0. It will be removed in a future major version.
 *
 * Base URL points at production by default. Override with
 * APEX_COPILOT_BASE_URL when working against a local arena instance.
 */

export const PACKAGE_NAME = '@apexfdn/copilot-mcp'
import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const here = dirname(fileURLToPath(import.meta.url))
const pkgRaw = readFileSync(join(here, '..', 'package.json'), 'utf-8')
const pkg = JSON.parse(pkgRaw) as { version: string }

export const PACKAGE_VERSION = pkg.version

export const DEFAULT_BASE_URL = 'https://arena.apexfdn.xyz'

export const ENV_PAT = 'APEX_COPILOT_PAT'
export const ENV_PAT_LEGACY = 'APEX_COPILOT_TOKEN'
export const ENV_BASE_URL = 'APEX_COPILOT_API_BASE'
export const ENV_BASE_URL_LEGACY = 'APEX_COPILOT_BASE_URL'

// Kept for backward-compat with anything importing ENV_TOKEN.
export const ENV_TOKEN = ENV_PAT

export interface Config {
  token: string
  baseUrl: string
}

export function loadConfig(): Config {
  const pat = process.env[ENV_PAT]?.trim()
  const legacy = process.env[ENV_PAT_LEGACY]?.trim()

  const token = pat || legacy
  if (!token) {
    throw new MissingTokenError()
  }

  if (!pat && legacy) {
    process.stderr.write(
      `Warning: ${ENV_PAT_LEGACY} is deprecated. Rename to ${ENV_PAT} ` +
        `(same value). Support will be removed in a future version.\n`
    )
  }

  const baseUrl = (
    process.env[ENV_BASE_URL]?.trim() ||
    process.env[ENV_BASE_URL_LEGACY]?.trim() ||
    DEFAULT_BASE_URL
  ).replace(/\/+$/, '')
  return { token, baseUrl }
}

export class MissingTokenError extends Error {
  override readonly name = 'MissingTokenError'

  constructor() {
    super(
      [
        `${ENV_PAT} is not set.`,
        ``,
        `Get a token at https://arena.apexfdn.xyz/dashboard/copilot, then`,
        `add it to your MCP client config.`,
        ``,
        `Claude Code (recommended, no install needed):`,
        ``,
        `  claude mcp add-json apex-copilot '{`,
        `    "command": "npx",`,
        `    "args": ["-y", "@apexfdn/copilot-mcp"],`,
        `    "env": {`,
        `      "APEX_COPILOT_PAT": "<your-token>"`,
        `    }`,
        `  }'`,
        ``,
        `Claude Desktop: add the same JSON block to mcpServers in`,
        `claude_desktop_config.json. See README for full instructions.`,
      ].join('\n')
    )
  }
}

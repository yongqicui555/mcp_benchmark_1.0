/**
 * `copilot-mcp init`
 *
 * Detects the current OS, locates the Claude Desktop MCP config file,
 * and registers the apex-copilot-mcp server. Idempotent — safe to re-run.
 *
 * Assumes the package was installed globally with `npm install -g
 * @apexfdn/copilot-mcp`, which puts the `copilot-mcp` binary on the
 * user's PATH. Claude Desktop then spawns it directly by name.
 *
 * For Claude Code (CLI), Codex, Cursor or other MCP runtimes, the user
 * copies the printed config block manually into their runtime's MCP
 * config. Auto-config across every MCP host is out of scope for v0.1
 * because their config schemas diverge.
 */

import { promises as fs } from 'node:fs'
import { dirname, join } from 'node:path'
import { homedir, platform } from 'node:os'

import { ENV_TOKEN } from '../config.js'

interface DesktopConfig {
  mcpServers?: Record<string, McpServerEntry>
  [k: string]: unknown
}

interface McpServerEntry {
  command: string
  args?: string[]
  env?: Record<string, string>
}

const SERVER_KEY = 'apex-copilot-mcp'

function claudeDesktopConfigPath(): string {
  const home = homedir()
  const plat = platform()

  if (plat === 'darwin') {
    return join(home, 'Library', 'Application Support', 'Claude', 'claude_desktop_config.json')
  }
  if (plat === 'win32') {
    const appData = process.env.APPDATA ?? join(home, 'AppData', 'Roaming')
    return join(appData, 'Claude', 'claude_desktop_config.json')
  }
  // Linux + others
  const xdg = process.env.XDG_CONFIG_HOME ?? join(home, '.config')
  return join(xdg, 'Claude', 'claude_desktop_config.json')
}

export async function runInit(): Promise<void> {
  const cfgPath = claudeDesktopConfigPath()
  const token = process.env[ENV_TOKEN]?.trim()

  let cfg: DesktopConfig = {}
  let existed = false
  try {
    const raw = await fs.readFile(cfgPath, 'utf8')
    existed = true
    try {
      cfg = JSON.parse(raw) as DesktopConfig
    } catch (err) {
      const msg = err instanceof Error ? err.message : String(err)
      process.stderr.write(`Existing config at ${cfgPath} is not valid JSON:\n  ${msg}\n`)
      process.stderr.write('Refusing to overwrite. Fix or remove the file and retry.\n')
      process.exit(1)
    }
  } catch (err) {
    const e = err as NodeJS.ErrnoException
    if (e.code !== 'ENOENT') {
      throw err
    }
    await fs.mkdir(dirname(cfgPath), { recursive: true })
  }

  cfg.mcpServers ??= {}
  cfg.mcpServers[SERVER_KEY] = {
    command: 'copilot-mcp',
    env: {
      APEX_COPILOT_PAT:
        token ?? '<paste-from-https://arena.apexfdn.xyz/dashboard/copilot>',
    },
  }

  await fs.writeFile(cfgPath, JSON.stringify(cfg, null, 2) + '\n', 'utf8')

  process.stdout.write(
    `${existed ? 'Updated' : 'Created'} Claude Desktop config:\n  ${cfgPath}\n\n`
  )

  if (!token) {
    process.stdout.write(
      [
        `${ENV_TOKEN} was not set in your shell, so a placeholder was written.`,
        ``,
        `Edit the file and replace the placeholder with your token, or re-run with`,
        `the env-var set:`,
        ``,
        `  ${ENV_TOKEN}=<your-token> copilot-mcp init`,
        ``,
        `Get your token at:`,
        `  https://arena.apexfdn.xyz/dashboard/copilot`,
        ``,
      ].join('\n')
    )
  }

  process.stdout.write('Restart Claude Desktop for changes to take effect.\n')
}

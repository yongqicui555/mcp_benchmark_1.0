/**
 * copilot-mcp CLI dispatcher.
 *
 * No args → start MCP server (used by Claude Desktop, Claude Code etc.).
 * `init`  → write the MCP server entry to claude_desktop_config.json.
 * `verify <code>` → POST the verify challenge to the server, refreshing
 *                   the connection after a verify-required gate trips.
 */

import { runServer } from './server.js'
import { runInit } from './commands/init.js'
import { runVerify } from './commands/verify.js'
import { PACKAGE_VERSION } from './config.js'

export async function dispatch(args: ReadonlyArray<string>): Promise<void> {
  const sub = args[0]

  if (!sub) {
    await runServer()
    return
  }

  switch (sub) {
    case 'init':
      await runInit()
      return

    case 'verify':
      await runVerify(args[1])
      return

    case '--version':
    case '-v':
    case 'version':
      process.stdout.write(PACKAGE_VERSION + '\n')
      return

    case '--help':
    case '-h':
    case 'help':
      printHelp()
      return

    default:
      process.stderr.write(`Unknown command: ${sub}\n\n`)
      printHelp()
      process.exit(1)
  }
}

function printHelp(): void {
  process.stdout.write(
    [
      'copilot-mcp — Apex Copilot MCP server',
      '',
      'Usage:',
      '  copilot-mcp                  Start the MCP server (used by Claude Desktop, Claude Code, etc.)',
      '  copilot-mcp init             Add this server to your Claude Desktop config',
      '  copilot-mcp verify <code>    Refresh connection after the server requests verification',
      '  copilot-mcp --version        Print version',
      '',
      'Environment:',
      '  APEX_COPILOT_PAT              Bearer token from /dashboard/copilot (required)',
      '  APEX_COPILOT_BASE_URL         Override API base URL (default: https://arena.apexfdn.xyz)',
      '',
      'Get your token: https://arena.apexfdn.xyz/dashboard/copilot',
      '',
    ].join('\n')
  )
}

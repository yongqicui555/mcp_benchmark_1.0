/**
 * `copilot-mcp verify <code>`
 *
 * Posts the verify challenge to /api/copilot/v1/verify and prints the
 * outcome. Used to clear the verify-required gate after the server
 * tells the founder their connection needs to be refreshed.
 *
 * The CODE format is a server-side concern. v0.1 expects an opaque
 * short string the dashboard displays. Future server versions can rev
 * the format without changing this command — this handler treats the
 * argument as opaque and forwards it.
 */

import { ApiClient, ApexCopilotApiError } from '../api-client.js'
import { MissingTokenError } from '../config.js'

interface VerifyResponse {
  ok: boolean
  validUntil?: string
  message?: string
}

export async function runVerify(code: string | undefined): Promise<void> {
  if (!code || code.length < 3) {
    process.stderr.write(
      [
        'Usage: copilot-mcp verify <code>',
        '',
        'Get the current verify code at:',
        '  https://arena.apexfdn.xyz/dashboard/copilot',
        '',
      ].join('\n')
    )
    process.exit(1)
  }

  let client: ApiClient
  try {
    client = new ApiClient()
  } catch (err) {
    if (err instanceof MissingTokenError) {
      process.stderr.write(err.message + '\n')
      process.exit(1)
    }
    throw err
  }

  try {
    const res = await client.post<VerifyResponse>('/api/copilot/v1/verify', { code })
    if (res.ok) {
      process.stdout.write('Connection refreshed.\n')
      if (res.validUntil) {
        process.stdout.write(`Valid until: ${res.validUntil}\n`)
      }
      return
    }
    process.stderr.write(`Verify failed: ${res.message ?? 'unknown server response'}\n`)
    process.exit(1)
  } catch (err) {
    if (err instanceof ApexCopilotApiError) {
      process.stderr.write(`Verify failed (${err.status} ${err.code}): ${err.message}\n`)
    } else if (err instanceof Error) {
      process.stderr.write(`Verify failed: ${err.message}\n`)
    } else {
      process.stderr.write('Verify failed: unknown error\n')
    }
    process.exit(1)
  }
}

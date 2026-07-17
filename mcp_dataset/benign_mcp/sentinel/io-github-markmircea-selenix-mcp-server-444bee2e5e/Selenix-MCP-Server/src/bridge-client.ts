import { readFileSync } from 'fs'
import { join } from 'path'
import { homedir } from 'os'
import http from 'http'

interface BridgeConfig {
  port: number
  token: string
}

const CONFIG_PATH = join(homedir(), '.selenix', 'bridge.json')

function readConfig(): BridgeConfig {
  try {
    return JSON.parse(readFileSync(CONFIG_PATH, 'utf-8'))
  } catch {
    throw new Error(
      `Cannot read Selenix bridge config at ${CONFIG_PATH}. ` +
        'Make sure Selenix is running and MCP Server is enabled in Settings.'
    )
  }
}

export class BridgeClient {
  async call(endpoint: string, body: Record<string, unknown> = {}): Promise<unknown> {
    // Re-read config on every call so we pick up new tokens after Selenix restarts
    const config = readConfig()

    return new Promise((resolve, reject) => {
      const data = JSON.stringify(body)
      const req = http.request(
        {
          hostname: '127.0.0.1',
          port: config.port,
          path: `/api/${endpoint}`,
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            Authorization: `Bearer ${config.token}`,
            'Content-Length': Buffer.byteLength(data),
          },
          timeout: 180000, // 3 minutes for long-running operations like run_test
        },
        (res) => {
          let responseData = ''
          res.on('data', (chunk: string) => (responseData += chunk))
          res.on('end', () => {
            try {
              resolve(JSON.parse(responseData))
            } catch {
              resolve({ raw: responseData })
            }
          })
        }
      )
      req.on('error', (err) =>
        reject(
          new Error(
            `Cannot connect to Selenix bridge at 127.0.0.1:${config.port}. ` +
              `Is Selenix running with MCP Server enabled? (${err.message})`
          )
        )
      )
      req.on('timeout', () => {
        req.destroy()
        reject(new Error('Request timed out after 180 seconds'))
      })
      req.write(data)
      req.end()
    })
  }
}

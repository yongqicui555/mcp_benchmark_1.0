import { Server } from '@modelcontextprotocol/sdk/server/index.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from '@modelcontextprotocol/sdk/types.js'
import { BridgeClient } from './bridge-client.js'
import { TOOL_DEFINITIONS } from './tools.js'

const server = new Server(
  { name: 'selenix-mcp-server', version: '1.0.0' },
  { capabilities: { tools: {} } }
)

const bridge = new BridgeClient()

server.setRequestHandler(ListToolsRequestSchema, async () => ({
  tools: TOOL_DEFINITIONS,
}))

server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params

  try {
    const result = (await bridge.call(name, (args as Record<string, unknown>) || {})) as Record<string, unknown>

    // Check for bridge-level errors
    if (result && typeof result === 'object' && 'error' in result) {
      return {
        content: [
          { type: 'text' as const, text: `Error: ${result.error}` },
        ],
        isError: true,
      }
    }

    // Special handling for screenshot — return as image content
    if (name === 'get_screenshot' && result.screenshot) {
      const screenshotStr = result.screenshot as string
      const base64Data = screenshotStr.replace(
        /^data:image\/\w+;base64,/,
        ''
      )
      return {
        content: [
          {
            type: 'image' as const,
            data: base64Data,
            mimeType: 'image/jpeg',
          },
          {
            type: 'text' as const,
            text: `Screenshot of: ${result.title || 'unknown'} (${result.url || 'unknown'})`,
          },
        ],
      }
    }

    // All other tools return text/JSON
    return {
      content: [
        {
          type: 'text' as const,
          text: JSON.stringify(result, null, 2),
        },
      ],
    }
  } catch (error) {
    return {
      content: [
        {
          type: 'text' as const,
          text: `Error: ${(error as Error).message}`,
        },
      ],
      isError: true,
    }
  }
})

async function main() {
  const transport = new StdioServerTransport()
  await server.connect(transport)
}

main().catch(console.error)

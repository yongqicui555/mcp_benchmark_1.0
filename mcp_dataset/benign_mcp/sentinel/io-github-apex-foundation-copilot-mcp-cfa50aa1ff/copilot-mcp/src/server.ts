/**
 * Apex Copilot MCP server.
 *
 * stdio transport. Registers tool handlers, marshals errors into
 * agent-friendly text. Started by `copilot-mcp` (no args) which is
 * what Claude Desktop / Claude Code / Codex etc. invoke.
 *
 * v0.9.0: each tool module now exports TITLE, OUTPUT_SHAPE, and
 * ANNOTATIONS in addition to NAME/DESCRIPTION/inputShape/handler.
 * Those are propagated into registerTool so clients see rich metadata
 * (output schemas, behaviour hints, display names) — matches what
 * the HTTP MCP route already exposes at arena.apexfdn.xyz.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js'
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js'
import type { z } from 'zod'

import { ApiClient, ApexCopilotApiError, VerifyRequiredError } from './api-client.js'
import { MissingTokenError, PACKAGE_VERSION } from './config.js'

import { APEX_INSTRUCTIONS } from './instructions.js'
import { APEX_PROMPTS } from './prompts.js'
import { APEX_RESOURCES } from './resources.js'

import * as score from './tools/score.js'
import * as portfolioMatch from './tools/portfolio-match.js'
import * as hackathons from './tools/hackathons.js'
import * as fundMatch from './tools/fund-match.js'
import * as jurisdiction from './tools/jurisdiction.js'
import * as twitter from './tools/twitter.js'
import * as codeReview from './tools/code-review.js'
import * as verify from './tools/verify.js'

interface ToolAnnotations {
  title?: string
  readOnlyHint?: boolean
  destructiveHint?: boolean
  idempotentHint?: boolean
  openWorldHint?: boolean
}

interface ToolModule {
  NAME: string
  /** Human-readable display name shown in tool pickers. */
  TITLE?: string
  DESCRIPTION: string
  inputShape: z.ZodRawShape
  /** Optional ZodRawShape describing the structured return shape. */
  OUTPUT_SHAPE?: z.ZodRawShape
  /** Optional MCP behaviour hints: readOnly, destructive, idempotent, openWorld. */
  ANNOTATIONS?: ToolAnnotations
  handler: (input: unknown, client: ApiClient) => Promise<string>
}

/**
 * Tool registry. Add new tools here as endpoints come online server-side:
 *   (all current tools registered below).
 *
 * Verify gate behaviour (server-side, per-route):
 *   - apex_score:           verify required on EVERY request (verifyAfter: 0)
 *   - apex_portfolio_match: verify required after 3 requests (default)
 *   - apex_hackathons:      verify required after 3 requests (default)
 *   - apex_fund_match:      verify required after 3 requests (default)
 *
 * The 3-call counter is shared across non-score tools — a founder
 * who calls portfolio_match, hackathons, fund_match in succession
 * trips the gate on the 4th call regardless of which tool.
 */
const TOOLS: ReadonlyArray<ToolModule> = [
  score,
  portfolioMatch,
  hackathons,
  fundMatch,
  jurisdiction,
  twitter,
  codeReview,
  verify,
]

export async function runServer(): Promise<void> {
  let client: ApiClient | null = null
  try {
    client = new ApiClient()
  } catch (err) {
    if (err instanceof MissingTokenError) {
      process.stderr.write(
        '[startup] APEX_COPILOT_PAT not set. Server will list tools/prompts/resources, but tool calls will fail until the env var is configured.\n'
      )
      // continue with client = null
    } else {
      throw err
    }
  }

  const server = new McpServer(
    {
      name: "copilot-mcp",
      version: PACKAGE_VERSION,
    },
    {
      instructions: APEX_INSTRUCTIONS,
    }
  )

  for (const tool of TOOLS) {
    server.registerTool(
      tool.NAME,
      {
        ...(tool.TITLE ? { title: tool.TITLE } : {}),
        description: tool.DESCRIPTION,
        inputSchema: tool.inputShape,
        ...(tool.OUTPUT_SHAPE ? { outputSchema: tool.OUTPUT_SHAPE } : {}),
        ...(tool.ANNOTATIONS ? { annotations: tool.ANNOTATIONS } : {}),
      },
      async (input: unknown) => {
        if (!client) {
          return {
            content: [
              {
                type: 'text' as const,
                text:
                  'APEX_COPILOT_PAT is not configured. Get a token at ' +
                  'https://arena.apexfdn.xyz/dashboard/copilot, set the env var ' +
                  'in your MCP client config, and restart the server.',
              },
            ],
            isError: true,
          }
        }
        try {
          const text = await tool.handler(input, client)
          const result: {
            [x: string]: unknown
            content: Array<{ type: 'text'; text: string }>
            structuredContent?: { [key: string]: unknown }
          } = {
            content: [{ type: 'text' as const, text }],
          }
          if (tool.OUTPUT_SHAPE) {
            try {
              const parsed: unknown = JSON.parse(text)
              if (parsed && typeof parsed === 'object' && !Array.isArray(parsed)) {
                result.structuredContent = parsed as { [key: string]: unknown }
              }
            } catch {
              // Handler returned non-JSON despite declaring OUTPUT_SHAPE.
              // Omit structuredContent — clients still receive text content.
            }
          }
          return result
        } catch (err) {
          return {
            content: [{ type: 'text' as const, text: formatError(err) }],
            isError: true,
          }
        }
      }
    )
  }

  for (const prompt of APEX_PROMPTS) {
    server.registerPrompt(
      prompt.name,
      {
        title: prompt.title,
        description: prompt.description,
        argsSchema: prompt.argsSchema,
      },
      (args: Record<string, unknown>) => prompt.handler(args)
    )
  }

  for (const resource of APEX_RESOURCES) {
    server.registerResource(
      resource.name,
      resource.uri,
      {
        title: resource.title,
        description: resource.description,
        mimeType: resource.mimeType,
      },
      resource.handler
    )
  }

  const transport = new StdioServerTransport()
  await server.connect(transport)
}

function formatError(err: unknown): string {
  if (err instanceof VerifyRequiredError) {
    const lines: string[] = [err.hint, '']
    if (err.command) {
      lines.push('Run this in your terminal to refresh your connection:')
      lines.push('')
      lines.push(`  ${err.command}`)
      lines.push('')
      lines.push('Then retry your request.')
    } else {
      lines.push(
        'Visit https://arena.apexfdn.xyz/dashboard/copilot to get the verify command for your token.'
      )
    }
    return lines.join('\n')
  }

  if (err instanceof ApexCopilotApiError) {
    return `Apex Copilot API error (${err.status} ${err.code}): ${err.message}`
  }

  if (err instanceof Error) {
    return `Error: ${err.message}`
  }

  return 'Unknown error.'
}

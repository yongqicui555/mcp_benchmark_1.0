/**
 * Tool: apex_score
 *
 * Wraps POST /api/copilot/v1/score. Submits structured project metadata
 * (name, url, description, file summaries) to the Apex scoring engine
 * and returns a breakdown across team, traction, tokenomics, market and
 * security dimensions, plus actionable recommendations.
 *
 * Privacy contract: this tool does NOT transmit file contents. The agent
 * extracts a short excerpt (max ~500 chars) from each deck or whitepaper
 * on the founder's machine and passes only the excerpt as files[].excerpt.
 * Full files never leave the founder.
 */

import { z } from 'zod'
import type { ApiClient } from '../api-client.js'

export const NAME = 'apex_score'

export const DESCRIPTION =
  'Run the Apex Copilot DD pre-screen on a Web3 project. Scores against five ' +
  'dimensions (team 20%, traction 25%, tokenomics 20%, market 20%, security 15%) ' +
  'and returns a breakdown plus actionable recommendations. A score of 85 or above ' +
  "shortens manual due diligence when the project later engages with Apex. The agent " +
  "should extract short excerpts from the founder's deck or whitepaper locally and " +
  'pass them as `files[].excerpt`. Full file contents must NOT be transmitted.'

export const inputShape = {
  projectName: z
    .string()
    .min(2)
    .max(200)
    .describe('Project name (2-200 chars)'),
  projectUrl: z
    .string()
    .url()
    .max(500)
    .optional()
    .describe('Public project URL (optional)'),
  description: z
    .string()
    .max(5000)
    .optional()
    .describe('Project description, ideally including problem, solution, target user, current stage'),
  files: z
    .array(
      z.object({
        name: z.string().max(255).describe('Filename (e.g. "deck-v3.pdf")'),
        size: z.number().int().min(0).describe('File size in bytes'),
        type: z.string().max(120).optional().describe('MIME type or short label'),
        excerpt: z
          .string()
          .max(2000)
          .optional()
          .describe(
            "First ~500 chars extracted from the file on the founder's machine. " +
              'Do NOT paste the full file. Excerpts only.'
          ),
      })
    )
    .max(20)
    .optional()
    .describe('File summaries (up to 20). Names + sizes + short excerpts only — no full contents.'),
}

export const TITLE = 'Apex Score'

export const OUTPUT_SHAPE = {
  ok: z.boolean().describe('True if scoring completed successfully.'),
  scoreOverall: z
    .number()
    .int()
    .min(0)
    .max(100)
    .optional()
    .describe('Composite 0-100 score across all dimensions.'),
  breakdown: z
    .object({
      team: z.number().int().min(0).max(100),
      traction: z.number().int().min(0).max(100),
      tokenomics: z.number().int().min(0).max(100),
      market: z.number().int().min(0).max(100),
      security: z.number().int().min(0).max(100),
    })
    .optional()
    .describe('Sub-scores by dimension, each 0-100.'),
  summary: z.string().optional().describe('Short narrative summary.'),
  recommendations: z
    .array(z.string())
    .optional()
    .describe('Actionable steps to improve the score or de-risk the project.'),
}

export const ANNOTATIONS = {
  title: 'Apex Score',
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
}

const Input = z.object(inputShape)

interface ScoreResponse {
  ok: boolean
  assessmentId: string
  score: number
  bypassDd: boolean
  bypassThreshold: number
  breakdown: ReadonlyArray<{
    key: string
    label: string
    score: number
    weight: number
    notes: string
  }>
  recommendations: ReadonlyArray<{
    area: string
    severity: 'critical' | 'high' | 'medium' | 'low'
    title: string
    body: string
  }>
  summary: string
  model: string
}

export async function handler(rawInput: unknown, client: ApiClient): Promise<string> {
  const input = Input.parse(rawInput)

  const data = await client.post<ScoreResponse>('/api/copilot/v1/score', {
    projectName: input.projectName,
    projectUrl: input.projectUrl ?? '',
    description: input.description,
    files: input.files ?? [],
  })

  return formatResult(data)
}

function formatResult(data: ScoreResponse): string {
  const lines: string[] = []
  lines.push(`Apex Copilot — assessment ${data.assessmentId}`)
  lines.push('')
  lines.push(
    `Overall score: ${data.score}/100${data.bypassDd ? '   (DD bypass eligible — 85+)' : ''}`
  )
  lines.push(`Scoring model: ${data.model}`)
  lines.push('')
  lines.push('Breakdown:')
  for (const dim of data.breakdown) {
    const label = dim.label.padEnd(16, ' ')
    const score = String(dim.score).padStart(3, ' ')
    lines.push(`  ${label} ${score}/100   ${dim.notes}`)
  }
  lines.push('')
  lines.push('Summary:')
  lines.push(`  ${data.summary}`)

  if (data.recommendations.length > 0) {
    lines.push('')
    lines.push('Recommendations:')
    for (const r of data.recommendations) {
      lines.push(`  [${r.severity.toUpperCase()}] ${r.area} — ${r.title}`)
      lines.push(`     ${r.body}`)
    }
  }

  return lines.join('\n')
}

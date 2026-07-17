/**
 * Tool: apex_portfolio_match
 *
 * Wraps POST /api/copilot/v1/portfolio-match. Finds portfolio projects
 * most similar to the founder's project description and returns each
 * with a one-sentence whyMatch and a shortLesson — short, concrete
 * narrative the agent can surface alongside the match.
 *
 * Useful for:
 *   - "have you funded anything like X" questions
 *   - finding portfolio founders to introduce as references
 *   - identifying overlap before pitching Apex on a competing thesis
 *
 * Verify gate: standard rolling window. After ~3 calls without a fresh
 * verify, the server returns 412 with a command the founder must run.
 */

import { z } from 'zod'
import type { ApiClient } from '../api-client.js'

export const NAME = 'apex_portfolio_match'

export const DESCRIPTION =
  "Find Apex portfolio projects most similar to the founder's idea or " +
  'company description. Returns a ranked list with similarity scores, ' +
  'a one-sentence rationale (whyMatch) and a short founder-applicable ' +
  'lesson (shortLesson) for each match. Use this to surface which Apex ' +
  "portfolio companies are closest to a project the founder is asking " +
  'about, identify potential reference customers, or check thesis ' +
  'overlap before pitching Apex.'

export const inputShape = {
  description: z
    .string()
    .min(40)
    .max(5000)
    .describe(
      'The project or idea to match against the Apex portfolio. ' +
        '40-5000 chars. Concrete and specific produces better matches than vague descriptions.'
    ),
  category: z
    .string()
    .max(64)
    .optional()
    .describe(
      'Optional category tag for the project (e.g. "DeFi", "RWA", "Infrastructure", "Privacy"). ' +
        'Used as a soft signal when ranking.'
    ),
  tags: z
    .array(z.string().max(64))
    .max(20)
    .optional()
    .describe('Optional free-form tags (max 20). Used as soft ranking signals.'),
  stage: z
    .enum(['pre-seed', 'seed', 'series-a', 'series-b', 'public'])
    .optional()
    .describe('Optional stage filter. Lets the engine prefer matches at a similar maturity.'),
  tokenStatus: z
    .enum(['no-token', 'planning', 'live'])
    .optional()
    .describe('Optional token status filter.'),
  topN: z
    .number()
    .int()
    .min(1)
    .max(10)
    .optional()
    .describe('Max number of matches to return (1-10, default 5).'),
}

export const TITLE = 'Apex Portfolio Match'

export const OUTPUT_SHAPE = {
  ok: z.boolean(),
  matches: z
    .array(
      z.object({
        project: z.object({
          name: z.string(),
          category: z.string().optional(),
        }),
        similarity: z.number().min(0).max(1).describe('Cosine similarity 0-1.'),
        whyMatch: z.string().describe('One-sentence rationale.'),
        shortLesson: z
          .string()
          .nullable()
          .describe('Founder-applicable lesson learned from this portfolio company.'),
        contactAvailable: z
          .boolean()
          .describe('True if Apex can facilitate an intro to this founder.'),
      })
    )
    .describe('Top portfolio matches, ranked by similarity descending.'),
  summary: z.string(),
}

export const ANNOTATIONS = {
  title: 'Apex Portfolio Match',
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
}

const Input = z.object(inputShape)

interface PortfolioMatch {
  project: {
    id: string
    name: string
    category?: string
    programId?: string
    description?: string
    tags?: ReadonlyArray<string>
  }
  similarity: number
  whyMatch: string
  shortLesson: string | null
  contactAvailable: boolean
}

interface PortfolioMatchResponse {
  ok: boolean
  matches: ReadonlyArray<PortfolioMatch>
  summary: string
  embeddingModel: string
  searchedAt: string
  metrics: {
    durationMs: number
    llmCalls: number
    cacheHits: number
  }
}

export async function handler(rawInput: unknown, client: ApiClient): Promise<string> {
  const input = Input.parse(rawInput)

  const data = await client.post<PortfolioMatchResponse>('/api/copilot/v1/portfolio-match', {
    description: input.description,
    category: input.category,
    tags: input.tags,
    stage: input.stage,
    tokenStatus: input.tokenStatus,
    topN: input.topN,
  })

  return formatResult(data)
}

function formatResult(data: PortfolioMatchResponse): string {
  const lines: string[] = []
  lines.push(`Apex portfolio match — ${data.matches.length} result${data.matches.length === 1 ? '' : 's'}`)
  lines.push('')
  lines.push(data.summary)

  if (data.matches.length === 0) {
    return lines.join('\n')
  }

  lines.push('')
  lines.push('Matches:')
  for (const m of data.matches) {
    const sim = (m.similarity * 100).toFixed(1)
    const cat = m.project.category ? ` · ${m.project.category}` : ''
    const program = m.project.programId ? ` · ${m.project.programId}` : ''
    lines.push(`  ${m.project.name}${cat}${program}   similarity ${sim}%`)
    lines.push(`    why: ${m.whyMatch}`)
    if (m.shortLesson) {
      lines.push(`    lesson: ${m.shortLesson}`)
    }
    if (m.contactAvailable) {
      lines.push(`    intro available — request via founder dashboard`)
    }
  }

  lines.push('')
  lines.push(
    `(matched against embedding model ${data.embeddingModel}, ` +
      `${data.metrics.cacheHits} cache hits, ${data.metrics.llmCalls} live LLM calls)`
  )

  return lines.join('\n')
}

/**
 * Tool: apex_hackathons
 *
 * Wraps POST /api/copilot/v1/hackathons. Finds upcoming Web3 hackathons
 * matching the founder's project, and optionally also surfaces past
 * projects from prior hackathons that overlap with the founder's idea.
 *
 * Useful for:
 *   - "where could we apply this project as a hackathon" planning
 *   - "has anyone built something like this before" pre-build sanity
 *     check (set searchPriorBuilds: true)
 *   - filtering by chain or online vs IRL preference
 *
 * Sources currently indexed: ETHGlobal, ETHGlobal showcase, Devfolio,
 * Devpost (Web3-filtered), Devpost project galleries, Colosseum
 * (Solana), and a registry of major annual conferences. ~270 past
 * projects + ~25 upcoming hackathons in the embedding index as of
 * v0.2.0.
 *
 * Verify gate: standard rolling window. After ~3 calls without a fresh
 * verify, the server returns 412 with a command the founder must run.
 */

import { z } from 'zod'
import type { ApiClient } from '../api-client.js'

export const NAME = 'apex_hackathons'

export const DESCRIPTION =
  'Find upcoming Web3 hackathons that match a project description, and ' +
  "optionally surface prior hackathon projects that built something similar. " +
  'Use this when a founder asks where they could enter their project, ' +
  'whether anyone has built a similar idea before (set ' +
  '`searchPriorBuilds: true`), or to scope timeline / prize-pool / ' +
  'chain fit. Indexed sources include ETHGlobal, Devfolio, Devpost ' +
  '(Web3-filtered), Colosseum, plus a registry of major annual events.'

export const inputShape = {
  description: z
    .string()
    .min(40)
    .max(5000)
    .describe(
      'Project or idea description (40-5000 chars). Embedding-matched ' +
        'against indexed hackathons (and prior projects, if requested).'
    ),
  category: z
    .string()
    .max(64)
    .optional()
    .describe('Optional category tag (e.g. "DeFi", "RWA", "Infrastructure").'),
  tags: z
    .array(z.string().max(64))
    .max(20)
    .optional()
    .describe('Optional free-form tags (max 20).'),
  chains: z
    .array(z.string().max(64))
    .max(20)
    .optional()
    .describe(
      'Filter to hackathons mentioning these chains (case-insensitive). ' +
        'Examples: ["Ethereum"], ["Solana"], ["Base", "Arbitrum"].'
    ),
  online: z
    .boolean()
    .optional()
    .describe('If true, return only online / virtual hackathons. If false or omitted, return all.'),
  topN: z
    .number()
    .int()
    .min(1)
    .max(10)
    .optional()
    .describe('Max upcoming hackathons to return (1-10, default 5).'),
  searchPriorBuilds: z
    .boolean()
    .optional()
    .describe(
      'When true, also returns up to 5 past hackathon projects whose ' +
        "descriptions overlap with the founder's idea. Use this to " +
        'check "has anyone built this before" before committing to a build.'
    ),
}

export const TITLE = 'Apex Hackathons'

export const OUTPUT_SHAPE = {
  ok: z.boolean(),
  hackathons: z.array(
    z.object({
      name: z.string(),
      startDate: z.string().optional(),
      endDate: z.string().optional(),
      prizePool: z.number().int().optional(),
      chains: z.array(z.string()).optional(),
      registrationUrl: z.string().optional(),
    })
  ),
}

export const ANNOTATIONS = {
  title: 'Apex Hackathons',
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: true,
}

const Input = z.object(inputShape)

interface HackathonMatch {
  id: string
  source: string
  name: string
  url: string
  description: string | null
  startsAt: string | null
  endsAt: string | null
  submissionDeadline: string | null
  prizePool: string | null
  prizePoolUsd: number | null
  tracks: ReadonlyArray<string>
  chains: ReadonlyArray<string>
  location: string | null
  isOnline: boolean
  tier: number | null
  organizers: ReadonlyArray<string>
  matchScore: number
}

interface PriorBuild {
  id: string
  name: string
  tagline: string | null
  description: string | null
  url: string
  hackathonName: string | null
  builtAt: string | null
  similarity: number
}

interface HackathonsResponse {
  ok: boolean
  hackathons: ReadonlyArray<HackathonMatch>
  priorBuilds?: ReadonlyArray<PriorBuild>
  summary: string
  scannedAt: string
}

export async function handler(rawInput: unknown, client: ApiClient): Promise<string> {
  const input = Input.parse(rawInput)

  const data = await client.post<HackathonsResponse>('/api/copilot/v1/hackathons', {
    description: input.description,
    category: input.category,
    tags: input.tags,
    chains: input.chains,
    online: input.online,
    topN: input.topN,
    searchPriorBuilds: input.searchPriorBuilds,
  })

  return formatResult(data)
}

function formatResult(data: HackathonsResponse): string {
  const lines: string[] = []
  lines.push(`Apex hackathons — ${data.hackathons.length} match${data.hackathons.length === 1 ? '' : 'es'}`)
  lines.push('')
  lines.push(data.summary)

  if (data.hackathons.length > 0) {
    lines.push('')
    lines.push('Upcoming hackathons:')
    for (const h of data.hackathons) {
      const window = formatDateWindow(h.startsAt, h.endsAt)
      const where = h.isOnline ? 'Online' : (h.location ?? '?')
      const prize = h.prizePool ? ` · prize ${h.prizePool}` : ''
      const score = (h.matchScore * 100).toFixed(1)
      lines.push(`  ${h.name}   match ${score}%`)
      lines.push(`    ${window} · ${where}${prize}`)
      if (h.chains.length > 0) {
        lines.push(`    chains: ${h.chains.join(', ')}`)
      }
      if (h.tracks.length > 0) {
        lines.push(`    tracks: ${h.tracks.slice(0, 6).join(', ')}`)
      }
      lines.push(`    ${h.url}`)
    }
  }

  if (data.priorBuilds && data.priorBuilds.length > 0) {
    lines.push('')
    lines.push('Prior projects with overlapping ideas:')
    for (const p of data.priorBuilds) {
      const sim = (p.similarity * 100).toFixed(1)
      const venue = p.hackathonName ? ` (${p.hackathonName})` : ''
      lines.push(`  ${p.name}${venue}   similarity ${sim}%`)
      const tag = p.tagline ?? p.description?.slice(0, 140)
      if (tag) lines.push(`    ${tag}`)
      lines.push(`    ${p.url}`)
    }
  }

  return lines.join('\n')
}

function formatDateWindow(startsAt: string | null, endsAt: string | null): string {
  if (!startsAt && !endsAt) return 'dates TBA'
  const fmt = (s: string) => s.slice(0, 10)
  if (startsAt && endsAt) {
    if (startsAt === endsAt) return fmt(startsAt)
    return `${fmt(startsAt)} → ${fmt(endsAt)}`
  }
  return fmt((startsAt ?? endsAt)!)
}

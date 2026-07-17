/**
 * Tool: apex_fund_match
 *
 * Wraps POST /api/copilot/v1/fund-match. Finds Web3 funds, angels,
 * accelerators, family offices and CEX venture arms most likely to
 * invest in the founder's project, given stage / chain / sector /
 * check size.
 *
 * The matcher embeds the founder's description, computes cosine
 * similarity against fund canonical profiles (which include their
 * recent investments), and applies an Apex-priority bonus for funds
 * we have direct relationships with. Apex policy: every fund in the
 * index is considered a partner — we have intros to all of them.
 *
 * Useful for:
 *   - "who should we approach for a $5M Series A on Solana DeFi?"
 *   - "which family offices have invested in privacy projects?"
 *   - "find lead investors active in RWA"
 *
 * Sources currently indexed: CryptoRank (primary, ~400+ funds with
 * tier/sectors/investments), crypto-fundraising.info (sitemap-driven,
 * ~500+ additional funds), apex-partners (manual seed of ~50 Tier 1-2
 * with full Apex priority).
 *
 * Verify gate: standard rolling window. Counts toward the same 3-call
 * budget as portfolio_match and hackathons.
 */

import { z } from 'zod'
import type { ApiClient } from '../api-client.js'

export const NAME = 'apex_fund_match'

export const DESCRIPTION =
  "Find Web3 funds, angels, accelerators, family offices and CEX venture " +
  "arms most likely to back the founder's project. Returns a ranked list " +
  'with similarity scores, recent investments, tier, geography, and a ' +
  'one-sentence rationale (whyMatch) for each. Apex partners (every fund ' +
  'in the index) get a small priority boost — we have direct intros to ' +
  'all of them. Use this when a founder asks who to approach for funding, ' +
  'which lead investors fit their stage and sector, or which CEX venture ' +
  'arms could double as listing path. Filters: stage, chain, sector, check ' +
  'size, lookingForLead.'

export const inputShape = {
  description: z
    .string()
    .min(40)
    .max(5000)
    .describe(
      'Project description (40-5000 chars). Embedding-matched against fund ' +
        'profiles which include their recent investments. Specific is better.'
    ),
  stage: z
    .enum(['pre-seed', 'seed', 'series-a', 'series-b', 'public'])
    .optional()
    .describe('Optional. Funding stage of the round being raised.'),
  chain: z
    .string()
    .max(64)
    .optional()
    .describe('Optional. Primary chain (e.g. "Solana", "Ethereum"). Soft filter.'),
  sector: z
    .string()
    .max(64)
    .optional()
    .describe(
      'Optional. Vertical (e.g. "DeFi", "RWA", "Infrastructure", "Privacy", ' +
        '"Gaming"). Soft filter on fund sector tags.'
    ),
  checkSize: z
    .number()
    .int()
    .min(0)
    .max(1_000_000_000)
    .optional()
    .describe(
      'Optional. Target check size in USD the founder is raising from this fund. ' +
        'When provided, filters to funds whose published check range covers it.'
    ),
  lookingForLead: z
    .boolean()
    .optional()
    .describe(
      'Optional. When true, prefer funds known to lead rounds (still ranked but ' +
        'lead-frequency factored into ordering).'
    ),
  topN: z
    .number()
    .int()
    .min(1)
    .max(10)
    .optional()
    .describe('Max number of fund matches to return (1-10, default 5).'),
}

export const TITLE = 'Apex Fund Match'

export const OUTPUT_SHAPE = {
  ok: z.boolean(),
  funds: z
    .array(
      z.object({
        name: z.string(),
        thesis: z.string(),
        recentInvestments: z.array(z.string()).optional(),
        fitScore: z.number().min(0).max(1),
        warmIntroAvailable: z.boolean(),
      })
    )
    .describe('Ranked funds matching the project, best fit first.'),
  summary: z.string().optional(),
}

export const ANNOTATIONS = {
  title: 'Apex Fund Match',
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: true,
}

const Input = z.object(inputShape)

interface FundMatch {
  id: string
  name: string
  type: string | null
  tier: number | null
  country: string | null
  website: string | null
  twitter: string | null
  shortDescription: string | null
  sectors: ReadonlyArray<string>
  stages: ReadonlyArray<string>
  chains: ReadonlyArray<string>
  checkSizeMinUsd: number | null
  checkSizeMaxUsd: number | null
  roiMultiple: number | null
  totalInvestmentsCount: number
  isApexPartner: boolean
  apexPriority: number | null
  recentInvestments: ReadonlyArray<{
    projectName: string
    roundType: string | null
    amountUsd: number | null
    announcedAt: string | null
    lead: boolean
  }>
  similarity: number
  rawSimilarity: number
  whyMatch: string
}

interface FundMatchResponse {
  ok: boolean
  funds: ReadonlyArray<FundMatch>
  summary: string
  scannedAt: string
}

export async function handler(rawInput: unknown, client: ApiClient): Promise<string> {
  const input = Input.parse(rawInput)

  const data = await client.post<FundMatchResponse>('/api/copilot/v1/fund-match', {
    description: input.description,
    stage: input.stage,
    chain: input.chain,
    sector: input.sector,
    checkSize: input.checkSize,
    lookingForLead: input.lookingForLead,
    topN: input.topN,
  })

  return formatResult(data)
}

function formatResult(data: FundMatchResponse): string {
  const lines: string[] = []
  lines.push(`Apex fund match — ${data.funds.length} result${data.funds.length === 1 ? '' : 's'}`)
  lines.push('')
  lines.push(data.summary)

  if (data.funds.length === 0) return lines.join('\n')

  lines.push('')
  lines.push('Funds:')
  for (const f of data.funds) {
    const tier = f.tier ? `Tier ${f.tier}` : (f.type ?? 'fund')
    const geo = f.country ?? '?'
    const apex = (f.apexPriority ?? 0) >= 10 ? ' [Apex direct]' : ''
    const sim = (f.similarity * 100).toFixed(1)

    lines.push(`  ${f.name}   ${tier} · ${geo}${apex}   match ${sim}%`)
    lines.push(`    why: ${f.whyMatch}`)

    if (f.sectors.length > 0) {
      lines.push(`    sectors: ${f.sectors.slice(0, 5).join(', ')}`)
    }

    const checkBand = formatCheckBand(f.checkSizeMinUsd, f.checkSizeMaxUsd)
    if (checkBand) lines.push(`    check size: ${checkBand}`)

    if (f.roiMultiple != null) {
      lines.push(`    portfolio ROI: ${f.roiMultiple.toFixed(1)}x · ${f.totalInvestmentsCount} investments`)
    } else if (f.totalInvestmentsCount > 0) {
      lines.push(`    ${f.totalInvestmentsCount} investments`)
    }

    if (f.recentInvestments.length > 0) {
      const recent = f.recentInvestments.slice(0, 3).map((i) => {
        const round = i.roundType ? ` (${i.roundType})` : ''
        const amount = i.amountUsd ? ` $${(i.amountUsd / 1_000_000).toFixed(1)}M` : ''
        const lead = i.lead ? ' lead' : ''
        return `${i.projectName}${round}${amount}${lead}`
      })
      lines.push(`    recent: ${recent.join(' · ')}`)
    }

    if (f.website) lines.push(`    ${f.website}`)
    if (f.twitter) lines.push(`    twitter: @${f.twitter.replace(/^@/, '')}`)
  }

  return lines.join('\n')
}

function formatCheckBand(min: number | null, max: number | null): string | null {
  if (min == null && max == null) return null
  const fmt = (n: number) => {
    if (n >= 1_000_000) return `$${(n / 1_000_000).toFixed(1)}M`
    if (n >= 1_000) return `$${Math.round(n / 1_000)}K`
    return `$${n}`
  }
  if (min != null && max != null) return `${fmt(min)} - ${fmt(max)}`
  if (min != null) return `${fmt(min)}+`
  return `up to ${fmt(max!)}`
}

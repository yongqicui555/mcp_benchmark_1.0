/**
 * Tool: apex_jurisdiction
 *
 * Wraps POST /api/copilot/v1/jurisdiction. Takes a structured project
 * brief and returns a ranked recommendation across 28 crypto-native
 * jurisdictions.
 *
 * Server pipeline: pure rules engine ranks every profile, then
 * OpenRouter LLM polishes the engine verdict into a narrative.
 * Deterministic fallback used if the LLM is unavailable.
 *
 * Verify gate: rolling window. After ~3 calls without a fresh verify,
 * the server returns 412 with the command the founder must run.
 */

import { z } from 'zod'
import type { ApiClient } from '../api-client.js'

export const NAME = 'apex_jurisdiction'

export const DESCRIPTION =
  'Recommend the best legal jurisdiction for a Web3 project. Covers ' +
  '28 crypto-native domiciles (UAE ADGM, VARA, RAK DAO, DMCC, Hong ' +
  'Kong, Singapore, Cayman, BVI, Bermuda, Switzerland, Liechtenstein, ' +
  'EU MiCA, Malta, Lithuania, Estonia, Gibraltar, UK, Bahamas, ' +
  'Delaware, Wyoming DAO LLC, Marshall Islands, Mauritius, Seychelles, ' +
  'Isle of Man, Jersey, Japan, Korea, Panama, El Salvador). Returns ' +
  'a ranked verdict with the recommended pick, why it wins for this ' +
  'specific project, the trade-off the founder should accept, and ' +
  'alternates with the conditions under which they should be used. ' +
  'Use this when the founder is incorporating, restructuring, or ' +
  'evaluating a domicile their lawyer recommended.'

export const inputShape = {
  projectType: z
    .enum([
      'token-issuer',
      'defi-protocol',
      'cex-licensed',
      'custody-or-wallet',
      'nft-or-gaming',
      'rwa-tokenisation',
      'stablecoin-issuer',
      'l1-or-infra',
      'dao-or-foundation',
      'payments-or-fiat-onramp',
    ])
    .describe(
      'The category of the project. For projects spanning multiple ' +
        'categories, pick the one driving the licensing or token-issuance decision.'
    ),
  fundraise: z
    .enum(['equity-only', 'token-only', 'hybrid'])
    .describe(
      'Fundraise structure. equity-only = SAFE/priced round only. ' +
        'token-only = SAFT or token sale only. hybrid = both.'
    ),
  fundraiseUsd: z
    .number()
    .int()
    .min(0)
    .max(1_000_000_000)
    .optional()
    .describe(
      'Target raise size in USD. Used to weight cost-of-setup against expected runway.'
    ),
  teamResidencyRegion: z
    .enum(['mena', 'apac', 'eu', 'uk', 'us', 'caribbean', 'latam', 'africa', 'global'])
    .optional()
    .describe('Where the core team is currently resident.'),
  targetMarketRegion: z
    .enum(['mena', 'apac', 'eu', 'uk', 'us', 'caribbean', 'latam', 'africa', 'global'])
    .optional()
    .describe('Primary target customer or user region.'),
  needsLicensedActivity: z
    .boolean()
    .describe(
      'Will the entity directly operate a licensed activity such as ' +
        'custody, brokerage, exchange, regulated stablecoin issuance, ' +
        'or money transmission? If unsure, set false. Most token-only foundations do NOT need this.'
    ),
  institutionalSensitivity: z
    .enum(['low', 'medium', 'high'])
    .optional()
    .describe(
      'How much weight to give Tier 1 LP / CEX / MM comfort with the domicile. ' +
        'high = institutional-led raise, regulated venue listing on roadmap. ' +
        'low = community / retail driven.'
    ),
  taxSensitivity: z
    .enum(['low', 'medium', 'high'])
    .optional()
    .describe('How much weight to give corporate tax rate.'),
  speedToLaunch: z
    .enum(['low', 'medium', 'high'])
    .optional()
    .describe(
      'Timeline urgency. high = need entity in 30 days. low = comfortable with 6-12 month build.'
    ),
  description: z
    .string()
    .max(2000)
    .optional()
    .describe(
      'Optional free-form project description for context. Helps the polish layer write a grounded narrative. Does not affect ranking.'
    ),
}

export const TITLE = 'Apex Jurisdiction'

export const OUTPUT_SHAPE = {
  ok: z.boolean(),
  rankings: z
    .array(
      z.object({
        jurisdiction: z.string(),
        score: z.number().min(0).max(100),
        pros: z.array(z.string()).optional(),
        cons: z.array(z.string()).optional(),
        setupCost: z.string().optional(),
        setupTime: z.string().optional(),
      })
    )
    .describe('Ranked jurisdictions, best fit first.'),
  narrative: z.string().optional().describe('Short narrative analysis.'),
}

export const ANNOTATIONS = {
  title: 'Apex Jurisdiction',
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: false,
}

const Input = z.object(inputShape)

interface JurisdictionResult {
  id: string
  name: string
  shortName: string
  region: string
  flag: string
  vehicleTypes: ReadonlyArray<string>
  costs: {
    setupUsd: { low: number; high: number }
    annualUsd: { low: number; high: number }
    minCapitalUsd?: number
  }
  timeline: {
    incorporationDays: { low: number; high: number }
    licenseDays?: { low: number; high: number }
  }
  taxRateCorporate: number
  taxOnTokenSale: string
  institutionalComfort: number
  pros: ReadonlyArray<string>
  cons: ReadonlyArray<string>
  bestWhen: string
  avoidWhen: string
  recentNote: string | null
  source: string
  score: number
  reasons: ReadonlyArray<string>
  warnings: ReadonlyArray<string>
}

interface JurisdictionResponse {
  ok: boolean
  narrative: {
    headline: string
    recommendation: { pick: string; why: string; tradeoff: string }
    alternates: ReadonlyArray<{ name: string; when: string }>
    warnings: ReadonlyArray<string>
    modelUsed: string
  }
  engine: {
    top: ReadonlyArray<JurisdictionResult>
    alternates: ReadonlyArray<JurisdictionResult>
    rejected: ReadonlyArray<JurisdictionResult>
  }
  coverage: { jurisdictionsConsidered: number }
  scannedAt: string
}

export async function handler(
  rawInput: unknown,
  client: ApiClient
): Promise<string> {
  const input = Input.parse(rawInput)

  const data = await client.post<JurisdictionResponse>(
    '/api/copilot/v1/jurisdiction',
    {
      projectType: input.projectType,
      fundraise: input.fundraise,
      fundraiseUsd: input.fundraiseUsd,
      teamResidencyRegion: input.teamResidencyRegion,
      targetMarketRegion: input.targetMarketRegion,
      needsLicensedActivity: input.needsLicensedActivity,
      institutionalSensitivity: input.institutionalSensitivity ?? 'medium',
      taxSensitivity: input.taxSensitivity ?? 'medium',
      speedToLaunch: input.speedToLaunch ?? 'medium',
      description: input.description,
    }
  )

  return formatResult(data)
}

function formatResult(data: JurisdictionResponse): string {
  const lines: string[] = []
  lines.push(
    `Apex jurisdiction routing — ${data.coverage.jurisdictionsConsidered} jurisdictions considered`
  )
  lines.push('')
  lines.push(data.narrative.headline)
  lines.push('')
  lines.push(`Recommendation: ${data.narrative.recommendation.pick}`)
  lines.push(`  Why: ${data.narrative.recommendation.why}`)
  lines.push(`  Trade-off: ${data.narrative.recommendation.tradeoff}`)

  if (data.narrative.alternates.length > 0) {
    lines.push('')
    lines.push('Alternates:')
    for (const a of data.narrative.alternates) {
      lines.push(`  ${a.name} — ${a.when}`)
    }
  }

  if (data.narrative.warnings.length > 0) {
    lines.push('')
    lines.push('Warnings:')
    for (const w of data.narrative.warnings) {
      lines.push(`  - ${w}`)
    }
  }

  if (data.engine.top.length > 0) {
    lines.push('')
    lines.push('Engine ranking (top picks):')
    for (const j of data.engine.top) {
      const setup = `${j.timeline.incorporationDays.low}-${j.timeline.incorporationDays.high}d`
      const cost = `$${j.costs.setupUsd.low.toLocaleString()}-${j.costs.setupUsd.high.toLocaleString()}`
      const tax = `${(j.taxRateCorporate * 100).toFixed(1)}%`
      lines.push(
        `  ${j.flag} ${j.shortName.padEnd(22)} score ${j.score.toString().padStart(3)} · setup ${setup} · ${cost} · tax ${tax}`
      )
    }
  }

  return lines.join('\n')
}

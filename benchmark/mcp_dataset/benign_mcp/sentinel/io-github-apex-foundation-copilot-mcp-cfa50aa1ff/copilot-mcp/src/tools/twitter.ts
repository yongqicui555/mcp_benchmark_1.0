/**
 * Tool: apex_twitter
 *
 * Wraps POST /api/copilot/v1/twitter. Audits the social presence of a
 * Web3 project's X (Twitter) account and returns a 0-100 score with
 * breakdown across 5 dimensions, a summary, recommendations, and any
 * overlap with Apex-network funds (handle match or mentions).
 *
 * Useful for:
 *   - Scoring a project's social presence as part of DD
 *   - Detecting inflated metrics (followers without engagement)
 *   - Surfacing which Apex-network funds a project's account has
 *     mentioned or been mentioned by
 *   - Spotting cadence problems (low posting frequency, long gaps)
 *
 * Verify gate: standard rolling window. After ~3 calls without a fresh
 * verify, the server returns 412 with a command the founder must run.
 */

import { z } from 'zod'
import type { ApiClient } from '../api-client.js'

export const NAME = 'apex_twitter'

export const DESCRIPTION =
  'Audit the X (Twitter) account of a Web3 project and produce a 0-100 ' +
  'social presence score. Returns a breakdown across 5 dimensions ' +
  '(reach, activity, engagement, authenticity, discourse), a written ' +
  'summary, specific recommendations, raw metrics (follower count, ' +
  'engagement rate, posting cadence), and any overlap with Apex-network ' +
  'funds. Use this when asked to evaluate a project\'s social presence, ' +
  'check for inflated metrics, or see which Apex funds have engaged ' +
  'with a project on Twitter.'

export const inputShape = {
  handle: z
    .string()
    .min(1)
    .max(15)
    .regex(/^[A-Za-z0-9_]+$/, 'Twitter handle: A-Z, a-z, 0-9, underscore only')
    .describe(
      'The X/Twitter handle to audit, without the leading "@". ' +
        'Example: "VitalikButerin", "ethereum", "uniswap".'
    ),
  ticker: z
    .string()
    .min(1)
    .max(32)
    .regex(/^[A-Za-z0-9_$.-]+$/)
    .optional()
    .describe(
      'Optional project ticker symbol (with or without $). When provided, ' +
        'the audit also searches for $ticker mentions and incorporates ' +
        'them into the discourse dimension.'
    ),
}

export const TITLE = 'Apex Twitter Audit'

export const OUTPUT_SHAPE = {
  ok: z.boolean(),
  handle: z.string(),
  followerCount: z.number().int().optional(),
  audienceQuality: z
    .enum(['high', 'medium', 'low', 'suspicious'])
    .optional(),
  realFollowerPercent: z.number().min(0).max(100).optional(),
  engagementRate: z.number().optional(),
  notableMentions: z.array(z.string()).optional(),
  apexNetworkOverlap: z
    .array(z.object({ name: z.string(), role: z.string() }))
    .optional(),
}

export const ANNOTATIONS = {
  title: 'Apex Twitter Audit',
  readOnlyHint: true,
  destructiveHint: false,
  idempotentHint: true,
  openWorldHint: true,
}

const Input = z.object(inputShape)

interface TwitterDim {
  key: 'reach' | 'activity' | 'engagement' | 'authenticity' | 'discourse'
  label: string
  score: number
  weight: number
  notes: string
}

interface TwitterRec {
  area: string
  severity: 'critical' | 'high' | 'medium' | 'low'
  title: string
  body: string
}

interface FundOverlay {
  fundId: string
  name: string
  twitter: string
  apexPriority: number
  isApexPartner: boolean
  signal: 'is_this_account' | 'mentioned'
  mentionCount?: number
}

interface TwitterMetrics {
  followers: number
  following: number
  followers_following_ratio: number
  account_age_days: number | null
  is_blue_verified: boolean
  tweet_count_sampled: number
  tweets_per_week: number | null
  days_since_last_tweet: number | null
  engagement_rate: number
  avg_likes: number
  avg_retweets: number
  avg_replies: number
  mentions_count: number
  mentions_with_ticker: number
}

interface TwitterResponse {
  ok: boolean
  auditId: string
  handle: string
  ticker?: string
  score: number
  breakdown: ReadonlyArray<TwitterDim>
  recommendations: ReadonlyArray<TwitterRec>
  summary: string
  fundsOverlap: ReadonlyArray<FundOverlay>
  metrics: TwitterMetrics
  model: string
  cached: boolean
  scannedAt: string
}

export async function handler(rawInput: unknown, client: ApiClient): Promise<string> {
  const input = Input.parse(rawInput)
  const data = await client.post<TwitterResponse>('/api/copilot/v1/twitter', {
    handle: input.handle,
    ticker: input.ticker,
  })
  return formatResult(data)
}

function formatResult(data: TwitterResponse): string {
  const lines: string[] = []
  const tickerSuffix = data.ticker ? ` ($${data.ticker.replace(/^\$/, '').toUpperCase()})` : ''
  lines.push(`Apex Twitter audit — @${data.handle}${tickerSuffix}`)
  lines.push('')
  lines.push(`Score: ${data.score}/100`)
  lines.push('')

  // Quick metric line
  const m = data.metrics
  const ageMonths = m.account_age_days !== null
    ? `${Math.round(m.account_age_days / 30)}mo`
    : 'unknown'
  lines.push(
    `Followers: ${m.followers.toLocaleString()} · ` +
      `Engagement: ${m.engagement_rate.toFixed(2)}% · ` +
      `${m.tweets_per_week?.toFixed(1) ?? '?'} posts/week · ` +
      `account ${ageMonths} old${m.is_blue_verified ? ' · blue' : ''}`
  )
  lines.push('')

  // Breakdown
  lines.push('Breakdown:')
  for (const d of data.breakdown) {
    lines.push(`  ${d.label.padEnd(14)} ${d.score.toString().padStart(3)}/100 (weight ${d.weight}%) — ${d.notes}`)
  }
  lines.push('')

  // Summary
  lines.push(data.summary)
  lines.push('')

  // Recommendations
  if (data.recommendations.length > 0) {
    lines.push('Recommendations:')
    for (const r of data.recommendations) {
      lines.push(`  [${r.severity}] ${r.title}`)
      lines.push(`    ${r.body}`)
    }
    lines.push('')
  }

  // Funds overlay
  if (data.fundsOverlap.length > 0) {
    lines.push('Apex-network fund overlap:')
    for (const f of data.fundsOverlap) {
      const tag = f.signal === 'is_this_account' ? 'IS the account' : `mentioned ×${f.mentionCount ?? 1}`
      const partner = f.isApexPartner ? ' [partner]' : ''
      lines.push(`  ${f.name} (@${f.twitter})${partner} — ${tag}`)
    }
    lines.push('')
  }

  lines.push(
    `(${data.cached ? 'cached' : 'fresh'} · model ${data.model} · ` +
      `scanned ${data.scannedAt})`
  )

  return lines.join('\n')
}

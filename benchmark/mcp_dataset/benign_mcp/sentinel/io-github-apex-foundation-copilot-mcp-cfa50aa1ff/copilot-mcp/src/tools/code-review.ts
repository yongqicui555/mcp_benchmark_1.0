/**
 * Tool: apex_code_review
 *
 * Wraps the async code-review pipeline:
 *   POST /api/copilot/v1/code-review        — submit an audit
 *   GET  /api/copilot/v1/code-review/:id    — poll status
 *
 * The server runs static analysers (Slither for Solidity, cargo-audit +
 * clippy for Rust) inside disposable Docker sandboxes, then an LLM pass
 * produces a 0-100 score across 5 dimensions plus prioritized findings.
 *
 * Hybrid blocking model (Variant 3):
 *   - Given `github_url` or `contract_source`, this tool SUBMITS the
 *     audit and then polls until it finishes — typically 5-30s for
 *     Solidity, up to a few minutes for large Rust workspaces.
 *   - Polling is capped at ~50s of wall time. If the audit is still
 *     running at the cap, the tool returns the `audit_id` and tells the
 *     agent to call apex_code_review again with that `audit_id` to
 *     fetch the finished result. This keeps the tool responsive under
 *     MCP client timeouts while still feeling like one call for the
 *     common fast case.
 *   - Given `audit_id`, the tool does a single status read and returns
 *     either the finished report or the current in-progress status.
 *
 * Exactly one of github_url / contract_source / audit_id must be set.
 *
 * Verify gate: standard rolling window on SUBMIT (shared 3-call counter).
 * A bare `audit_id` status read does not count against the gate.
 *
 * Daily limit: 3 submissions per UTC day per token (server-enforced).
 */

import { z } from 'zod'
import type { ApiClient } from '../api-client.js'

export const NAME = 'apex_code_review'

export const DESCRIPTION =
  'Run a preliminary security audit on a Web3 project\'s smart contracts. ' +
  'Accepts a public GitHub repo URL (Solidity and/or Rust) or pasted ' +
  'Solidity source. Runs static analysers (Slither, cargo-audit, clippy) ' +
  'in a sandbox plus an AI review pass, returning a 0-100 score across 5 ' +
  'dimensions (security, code quality, dependencies, testing, ' +
  'documentation), prioritized findings with severity and file/line refs, ' +
  'and recommendations. Use this when asked to audit, review, or assess ' +
  'the security of a project\'s contracts or on-chain code. This is a ' +
  'first-pass triage, not a substitute for a professional audit. Audits ' +
  'run async: for a large repo this tool may return an audit_id and ask ' +
  'you to call it again with that audit_id to fetch the finished report. ' +
  'Limited to 3 submissions per day.'

export const inputShape = {
  github_url: z
    .string()
    .url()
    .regex(
      /^https?:\/\/github\.com\/[\w.-]+\/[\w.-]+(?:\.git)?\/?$/i,
      'Must be a GitHub repo URL like https://github.com/owner/repo'
    )
    .optional()
    .describe(
      'Public GitHub repository URL to audit. The server clones the repo ' +
        'and analyses Solidity (.sol) and Rust on-chain code. Example: ' +
        '"https://github.com/Uniswap/v2-core". Mutually exclusive with ' +
        'contract_source and audit_id.'
    ),
  contract_source: z
    .string()
    .min(10)
    .max(256 * 1024)
    .optional()
    .describe(
      'Raw Solidity source code to audit directly, for a quick single-file ' +
        'check without a repo. Mutually exclusive with github_url and ' +
        'audit_id.'
    ),
  audit_id: z
    .string()
    .uuid()
    .optional()
    .describe(
      'The id of an audit that was previously started. Use this to fetch ' +
        'the result of an audit that was still running when it was first ' +
        'submitted. Mutually exclusive with github_url and contract_source.'
    ),
}

export const TITLE = 'Apex Code Review'

export const OUTPUT_SHAPE = {
  ok: z.boolean(),
  auditId: z.string().optional(),
  score: z
    .number()
    .int()
    .min(0)
    .max(100)
    .optional()
    .describe('Overall security score 0-100.'),
  findings: z
    .array(
      z.object({
        severity: z.enum([
          'critical',
          'high',
          'medium',
          'low',
          'informational',
        ]),
        file: z.string().optional(),
        line: z.number().int().optional(),
        category: z.string().optional(),
        message: z.string(),
        recommendation: z.string().optional(),
      })
    )
    .optional()
    .describe('Security findings discovered in the audit.'),
  summary: z.string().optional(),
}

export const ANNOTATIONS = {
  title: 'Apex Code Review',
  readOnlyHint: false,
  destructiveHint: false,
  idempotentHint: false,
  openWorldHint: true,
}

const Input = z
  .object(inputShape)
  .refine(
    (v) => {
      const n =
        (v.github_url ? 1 : 0) +
        (v.contract_source ? 1 : 0) +
        (v.audit_id ? 1 : 0)
      return n === 1
    },
    {
      message:
        'Provide exactly one of: github_url, contract_source, or audit_id.',
    }
  )

// --- Response shapes (mirror server src/server/code-review/types.ts) ---

type AuditStatus =
  | 'queued'
  | 'cloning'
  | 'analyzing'
  | 'scoring'
  | 'done'
  | 'failed'

type Severity = 'critical' | 'high' | 'medium' | 'low' | 'info'

interface SubmitResponse {
  ok: true
  audit_id: string
  status: 'queued'
  estimated_seconds: number
  daily_used: number
  daily_limit: number
  poll_url: string
  scanned_at: string
}

interface Dimension {
  key: 'security' | 'quality' | 'dependencies' | 'testing' | 'documentation'
  label: string
  score: number
  weight: number
  notes: string
}

interface Recommendation {
  area: string
  severity: Severity
  title: string
  body: string
}

interface Finding {
  id: string
  severity: Severity
  category: string
  detector?: string | null
  title: string
  description: string
  recommendation?: string | null
  file_path?: string | null
  line_number?: number | null
}

interface StatusResponse {
  audit_id: string
  status: AuditStatus
  source_type: 'github' | 'paste'
  github_url?: string | null
  commit_sha?: string | null
  languages_detected?: string[]
  score?: number | null
  breakdown?: Dimension[]
  recommendations?: Recommendation[]
  summary?: string | null
  findings?: Finding[]
  finding_counts?: Record<Severity, number>
  error_message?: string | null
  model?: string | null
  started_at?: string | null
  completed_at?: string | null
  created_at: string
}

// --- Polling configuration ---

// Wall-clock cap on in-tool polling. Kept under common MCP client tool
// timeouts. If the audit is not done by this point, hand the audit_id
// back to the agent.
const POLL_BUDGET_MS = 50_000
const POLL_INTERVAL_MS = 3_000

function sleep(ms: number): Promise<void> {
  return new Promise((r) => setTimeout(r, ms))
}

export async function handler(rawInput: unknown, client: ApiClient): Promise<string> {
  const input = Input.parse(rawInput)

  // --- Path 1: status read of an existing audit ---
  if (input.audit_id) {
    const data = await client.get<StatusResponse>(
      `/api/copilot/v1/code-review/${input.audit_id}`
    )
    return renderStatus(data, { justChecked: true })
  }

  // --- Path 2: submit a new audit, then poll within budget ---
  const submitBody = input.github_url
    ? { github_url: input.github_url }
    : { contract_source: input.contract_source }

  const submitted = await client.post<SubmitResponse>(
    '/api/copilot/v1/code-review',
    submitBody
  )

  const auditId = submitted.audit_id
  const startedAt = Date.now()

  // First poll happens after a short delay — even fast Solidity audits
  // need a couple seconds for clone + analyse.
  await sleep(POLL_INTERVAL_MS)

  let last: StatusResponse | null = null
  while (Date.now() - startedAt < POLL_BUDGET_MS) {
    last = await client.get<StatusResponse>(
      `/api/copilot/v1/code-review/${auditId}`
    )
    if (last.status === 'done' || last.status === 'failed') {
      return renderStatus(last, { justChecked: false })
    }
    await sleep(POLL_INTERVAL_MS)
  }

  // Budget exhausted, audit still running. Hand back the id.
  const statusNow = last?.status ?? 'queued'
  return [
    `Audit submitted and still running (status: ${statusNow}).`,
    '',
    `audit_id: ${auditId}`,
    '',
    'Large repositories (especially Rust workspaces) can take a few ' +
      'minutes to compile and analyse. Call apex_code_review again with ' +
      `audit_id "${auditId}" to fetch the finished report.`,
    '',
    `(submission ${submitted.daily_used}/${submitted.daily_limit} today)`,
  ].join('\n')
}

// --- Rendering ---

function renderStatus(
  data: StatusResponse,
  opts: { justChecked: boolean }
): string {
  if (data.status === 'failed') {
    return [
      `Audit ${data.audit_id} failed.`,
      data.error_message ? `Reason: ${data.error_message}` : '',
      '',
      'Common causes: the repository is private (only public repos are ' +
        'supported), the URL is wrong, or no Solidity/Rust contracts were ' +
        'found in the repo.',
    ]
      .filter(Boolean)
      .join('\n')
  }

  if (data.status !== 'done') {
    // Still in progress
    const lines = [
      `Audit ${data.audit_id} is ${data.status}.`,
    ]
    if (opts.justChecked) {
      lines.push(
        '',
        'Not finished yet. Call apex_code_review again with this ' +
          `audit_id ("${data.audit_id}") in a little while.`
      )
    }
    return lines.join('\n')
  }

  // status === 'done' — full report
  const lines: string[] = []
  const langs =
    data.languages_detected && data.languages_detected.length > 0
      ? data.languages_detected.join(', ')
      : 'unknown'

  lines.push(`Code audit — ${langs}`)
  if (data.github_url) lines.push(data.github_url)
  if (data.commit_sha) lines.push(`commit ${data.commit_sha.slice(0, 12)}`)
  lines.push('')

  lines.push(`Overall score: ${data.score ?? '?'}/100`)
  lines.push('')

  if (data.breakdown && data.breakdown.length > 0) {
    lines.push('Breakdown:')
    for (const d of data.breakdown) {
      lines.push(
        `  ${d.label.padEnd(14)} ${d.score
          .toString()
          .padStart(3)}/100 (weight ${d.weight}%) — ${d.notes}`
      )
    }
    lines.push('')
  }

  if (data.summary) {
    lines.push(data.summary)
    lines.push('')
  }

  if (data.finding_counts) {
    const fc = data.finding_counts
    lines.push(
      `Findings: ${fc.critical} critical · ${fc.high} high · ` +
        `${fc.medium} medium · ${fc.low} low`
    )
    lines.push('')
  }

  if (data.findings && data.findings.length > 0) {
    // Show up to 12 findings, most severe first
    const order: Record<Severity, number> = {
      critical: 0,
      high: 1,
      medium: 2,
      low: 3,
      info: 4,
    }
    const sorted = [...data.findings].sort(
      (a, b) => order[a.severity] - order[b.severity]
    )
    const shown = sorted.slice(0, 12)
    lines.push(`Top findings (${shown.length} of ${data.findings.length}):`)
    for (const f of shown) {
      const loc = f.file_path
        ? ` — ${f.file_path}${f.line_number ? `:${f.line_number}` : ''}`
        : ''
      lines.push(`  [${f.severity}] ${f.title}${loc}`)
      if (f.detector) lines.push(`    detector: ${f.detector}`)
      if (f.recommendation) lines.push(`    fix: ${f.recommendation}`)
    }
    if (data.findings.length > shown.length) {
      lines.push(`  ... and ${data.findings.length - shown.length} more`)
    }
    lines.push('')
  }

  if (data.recommendations && data.recommendations.length > 0) {
    lines.push('Recommendations:')
    for (const r of data.recommendations) {
      lines.push(`  [${r.severity}] ${r.title}`)
      lines.push(`    ${r.body}`)
    }
    lines.push('')
  }

  lines.push(
    `(preliminary audit · model ${data.model ?? 'n/a'} · ` +
      `audit_id ${data.audit_id})`
  )

  return lines.join('\n')
}

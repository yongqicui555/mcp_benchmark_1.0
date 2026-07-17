#!/usr/bin/env node
/**
 * Acta MCP Server
 *
 * AI agent interface for Veritas Acta — the open protocol for contestable,
 * checkable public records. Agents can contribute, respond, discover where
 * contribution is needed, verify chain integrity, and export records.
 *
 * Install in Cursor/Claude Desktop:
 *   { "command": "npx", "args": ["-y", "acta-mcp"] }
 *
 * Tools:
 *   - acta_contribute  — Submit a question, claim, or prediction
 *   - acta_respond     — Submit evidence, challenge, update, or resolution
 *   - acta_query       — Browse/search topics, entries, single entry lookup
 *   - acta_discover    — Find actionable work: contested records, claims needing evidence, etc.
 *   - acta_verify      — Verify hash chain integrity for a topic
 *   - acta_export      — Export full chain for independent verification
 *
 * Environment:
 *   ACTA_INSTANCE_URL  — Instance URL (default: https://veritasacta.com)
 *   ACTA_DEVICE_ID     — Device identity for contributions (auto-generated if not set)
 *
 * @license MIT
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { randomUUID } from 'node:crypto';

// ── Configuration ────────────────────────────────────────────────────

const ACTA_BASE = (process.env.ACTA_INSTANCE_URL || process.env.ACTA_URL || 'https://veritasacta.com').replace(/\/$/, '');
const DEVICE_ID = process.env.ACTA_DEVICE_ID || `mcp-agent-${randomUUID().slice(0, 8)}`;

// Optional: scopeblind-agent for authenticated contributions
let agent = null;
async function getAgent() {
  if (agent) return agent;
  try {
    const { createAgent } = await import('scopeblind-agent');
    agent = await createAgent({ keyPath: '.scopeblind/acta-mcp-key.json' });
    return agent;
  } catch {
    return null;
  }
}

// ── HTTP Helper ──────────────────────────────────────────────────────

async function actaFetch(path, options = {}) {
  const url = `${ACTA_BASE}${path}`;
  const headers = { ...options.headers };

  if (!headers['X-Device-Id']) headers['X-Device-Id'] = DEVICE_ID;

  const ag = await getAgent();
  if (ag && options.method && options.method !== 'GET') {
    return ag.fetch(url, { ...options, headers });
  }
  return fetch(url, { ...options, headers });
}

function stripUndefined(obj) {
  return Object.fromEntries(Object.entries(obj).filter(([, v]) => v !== undefined));
}

function truncate(str, len = 80) {
  if (!str) return '';
  return str.length > len ? str.slice(0, len) + '…' : str;
}

// ── MCP Server ───────────────────────────────────────────────────────

const server = new McpServer({
  name: 'acta',
  version: '0.2.0',
  description: 'Interact with Veritas Acta — contribute, challenge, discover, verify, and query contestable public records.',
});

// ═════════════════════════════════════════════════════════════════════
// Tool 1: acta_contribute — Submit a question, claim, or prediction
// ═════════════════════════════════════════════════════════════════════

server.tool(
  'acta_contribute',
  'Submit a typed contribution to the Acta public record. Questions have no evidence burden. Factual claims require a source or reasoning. Opinion/hypothesis claims require uncertainty. Predictions require resolution criteria, date, source, and rule.',
  {
    topic: z.string().describe('Topic slug (e.g. "ai-regulation-2026")'),
    type: z.enum(['question', 'claim', 'prediction']).describe('Contribution type'),
    body: z.string().max(10000).describe('Full text of the contribution'),
    // Claim fields
    category: z.enum(['factual', 'opinion', 'hypothesis']).optional().describe('Required for claims'),
    source: z.string().optional().describe('URL to supporting evidence (required for factual claims)'),
    reasoning: z.string().optional().describe('Reasoning (alternative to source for factual claims)'),
    uncertainty: z.string().optional().describe('Uncertainty statement (required for opinion/hypothesis claims)'),
    // Prediction fields
    resolution_criteria: z.string().optional().describe('How to determine if confirmed/refuted (required for predictions)'),
    resolution_date: z.string().optional().describe('ISO-8601 future date (required for predictions)'),
    resolution_source: z.string().optional().describe('Authoritative source for resolution (required for predictions)'),
    resolution_rule: z.string().optional().describe('Who/what triggers resolution (required for predictions)'),
    // Provenance
    provenance: z.object({
      authored_with_model: z.string().optional(),
      system_prompt_hash: z.string().optional(),
      prompt_hash: z.string().optional(),
      tool_version: z.string().optional(),
      disclosure_level: z.enum(['private', 'reproducible', 'full']).optional(),
    }).optional().describe('Optional AI authorship metadata'),
  },
  async (args) => {
    try {
      const payload = stripUndefined({
        body: args.body,
        category: args.category,
        source: args.source,
        reasoning: args.reasoning,
        uncertainty: args.uncertainty,
        resolution_criteria: args.resolution_criteria,
        resolution_date: args.resolution_date,
        resolution_source: args.resolution_source,
        resolution_rule: args.resolution_rule,
        provenance: args.provenance,
      });

      const res = await actaFetch('/api/contribute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: args.type, topic: args.topic, payload }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok || data.status === 'rejected') {
        const errors = data.errors || data.error || data.message || 'Unknown error';
        return { content: [{ type: 'text', text: `Contribution failed (HTTP ${res.status}):\n${typeof errors === 'string' ? errors : JSON.stringify(errors, null, 2)}` }] };
      }

      let report = `# Contribution Accepted\n\n`;
      report += `| Field | Value |\n|-------|-------|\n`;
      report += `| Type | ${args.type} |\n`;
      report += `| Topic | ${args.topic} |\n`;
      report += `| Entry ID | \`${data.entry_id}\` |\n`;
      report += `| Entry Hash | \`${data.entry_hash}\` |\n`;
      report += `| Sequence | #${data.sequence} |\n`;
      report += `| State | ${data.state || 'open'} |\n`;
      if (data.tokens_remaining !== undefined) report += `| Tokens Remaining | ${data.tokens_remaining} |\n`;
      if (data.moderation_tags?.length) report += `| Moderation | ${data.moderation_tags.join(', ')} |\n`;
      report += `\n**View:** ${ACTA_BASE}/topic/${args.topic}\n`;

      return { content: [{ type: 'text', text: report }] };
    } catch (err) {
      return { content: [{ type: 'text', text: `Error: ${err.message}` }] };
    }
  }
);

// ═════════════════════════════════════════════════════════════════════
// Tool 2: acta_respond — Submit evidence, challenge, update, resolution
// ═════════════════════════════════════════════════════════════════════

server.tool(
  'acta_respond',
  'Submit a response to an existing entry. Evidence requires source + stance. Challenges require target_assertion + basis + argument (min 20 chars). Updates require update_type. Resolutions require outcome + source + resolution_type.',
  {
    topic: z.string().describe('Topic slug'),
    type: z.enum(['evidence', 'challenge', 'update', 'resolution']).describe('Response type'),
    target_id: z.string().describe('Entry ID being responded to'),
    body: z.string().max(10000).describe('Response text'),
    // Evidence fields
    source: z.string().optional().describe('Source URL (required for evidence, counter_evidence/source_unreliable challenges, and resolutions)'),
    stance: z.enum(['supporting', 'refuting', 'contextual']).optional().describe('Required for evidence'),
    // Challenge fields
    target_assertion: z.string().optional().describe('Quote the specific assertion being challenged (min 5 chars, required for challenges)'),
    basis: z.enum(['counter_evidence', 'logical_error', 'source_unreliable', 'missing_context']).optional().describe('Required for challenges'),
    argument: z.string().optional().describe('Substantive refutation (min 20 chars, required for challenges)'),
    // Update fields
    update_type: z.enum(['correction', 'additional_context', 'scope_change', 'alternative_source']).optional().describe('Required for updates'),
    // Resolution fields
    outcome: z.string().optional().describe('Resolution outcome (required for resolutions)'),
    resolution_type: z.enum(['answered', 'confirmed', 'refuted', 'partially_confirmed', 'unresolvable']).optional().describe('Required for resolutions'),
    // Provenance
    provenance: z.object({
      authored_with_model: z.string().optional(),
      system_prompt_hash: z.string().optional(),
      prompt_hash: z.string().optional(),
      tool_version: z.string().optional(),
      disclosure_level: z.enum(['private', 'reproducible', 'full']).optional(),
    }).optional().describe('Optional AI authorship metadata'),
  },
  async (args) => {
    try {
      const payload = stripUndefined({
        target_id: args.target_id,
        body: args.body,
        source: args.source,
        stance: args.stance,
        target_assertion: args.target_assertion,
        basis: args.basis,
        argument: args.argument,
        update_type: args.update_type,
        outcome: args.outcome,
        resolution_type: args.resolution_type,
        provenance: args.provenance,
      });

      const res = await actaFetch('/api/respond', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ type: args.type, topic: args.topic, payload }),
      });

      const data = await res.json().catch(() => ({}));

      if (!res.ok || data.status === 'rejected') {
        const errors = data.errors || data.error || data.message || 'Unknown error';
        return { content: [{ type: 'text', text: `Response failed (HTTP ${res.status}):\n${typeof errors === 'string' ? errors : JSON.stringify(errors, null, 2)}` }] };
      }

      let report = `# Response Accepted\n\n`;
      report += `| Field | Value |\n|-------|-------|\n`;
      report += `| Type | ${args.type} |\n`;
      report += `| Topic | ${args.topic} |\n`;
      report += `| Target | \`${args.target_id}\` |\n`;
      report += `| Entry ID | \`${data.entry_id}\` |\n`;
      report += `| Entry Hash | \`${data.entry_hash}\` |\n`;
      report += `| Sequence | #${data.sequence} |\n`;
      if (data.state) report += `| Target State | ${data.state} |\n`;
      if (data.tokens_remaining !== undefined) report += `| Tokens Remaining | ${data.tokens_remaining} |\n`;
      report += `\n**View:** ${ACTA_BASE}/topic/${args.topic}\n`;

      return { content: [{ type: 'text', text: report }] };
    } catch (err) {
      return { content: [{ type: 'text', text: `Error: ${err.message}` }] };
    }
  }
);

// ═════════════════════════════════════════════════════════════════════
// Tool 3: acta_query — Browse/search topics and entries
// ═════════════════════════════════════════════════════════════════════

server.tool(
  'acta_query',
  'Browse the Acta public record. List topics (optionally filtered), get entries for a topic (with type/state filters), or look up a single entry with its responses.',
  {
    action: z.enum(['list_topics', 'feed', 'entry']).describe('list_topics: browse topics. feed: entries for a topic. entry: single entry with responses.'),
    topic: z.string().optional().describe('Topic slug (required for feed action)'),
    entry_id: z.string().optional().describe('Entry ID (required for entry action)'),
    q: z.string().optional().describe('Filter topic names by substring (for list_topics)'),
    type: z.enum(['question', 'claim', 'prediction']).optional().describe('Filter feed by contribution type'),
    state: z.enum(['open', 'contested', 'superseded', 'resolved', 'supported']).optional().describe('Filter feed by computed state'),
  },
  async (args) => {
    try {
      let report = '';

      if (args.action === 'list_topics') {
        const params = args.q ? `?q=${encodeURIComponent(args.q)}` : '';
        const res = await actaFetch(`/api/topics${params}`);
        const topics = await res.json();

        report = `# Acta Topics\n\n`;
        report += `**Instance:** ${ACTA_BASE}\n`;
        if (args.q) report += `**Filter:** "${args.q}"\n`;
        report += `\n`;

        if (!topics.length) {
          report += `No topics found.\n`;
        } else {
          report += `| Topic | Entries | Last Activity |\n|-------|---------|---------------|\n`;
          for (const t of topics) {
            report += `| ${t.topic} | ${t.entry_count || 0} | ${t.last_entry_at || '—'} |\n`;
          }
        }

      } else if (args.action === 'feed') {
        if (!args.topic) {
          return { content: [{ type: 'text', text: 'Error: topic is required for feed action.' }] };
        }

        const params = new URLSearchParams({ topic: args.topic });
        if (args.type) params.set('type', args.type);
        if (args.state) params.set('state', args.state);

        const res = await actaFetch(`/api/feed?${params}`);
        const data = await res.json();
        const contributions = data.contributions || [];

        report = `# ${args.topic}\n\n`;
        const filters = [];
        if (args.type) filters.push(`type=${args.type}`);
        if (args.state) filters.push(`state=${args.state}`);
        if (filters.length) report += `**Filters:** ${filters.join(', ')}\n\n`;

        if (!contributions.length) {
          report += `No contributions found matching criteria.\n`;
        } else {
          report += `| # | Type | State | Body | Entry ID |\n|---|------|-------|------|----------|\n`;
          for (const c of contributions) {
            const body = truncate(c.body_preview || c.payload?.body, 60);
            report += `| #${c.sequence} | ${c.subtype} | ${c.computed_state || c.state || 'open'} | ${body} | \`${c.entry_id?.slice(0, 8)}…\` |\n`;
          }
          report += `\n**Total:** ${contributions.length} contributions, ${data.total || '?'} entries\n`;
        }
        report += `\n**View:** ${ACTA_BASE}/topic/${args.topic}\n`;

      } else if (args.action === 'entry') {
        if (!args.entry_id) {
          return { content: [{ type: 'text', text: 'Error: entry_id is required for entry action.' }] };
        }

        const res = await actaFetch(`/api/entry/${args.entry_id}`);
        if (!res.ok) {
          return { content: [{ type: 'text', text: `Entry not found (HTTP ${res.status}).` }] };
        }
        const data = await res.json();
        const entry = data.entry || data;

        report = `# Entry: ${entry.entry_id}\n\n`;
        report += `| Field | Value |\n|-------|-------|\n`;
        report += `| Type | ${entry.type}/${entry.subtype} |\n`;
        report += `| Topic | ${entry.topic} |\n`;
        report += `| State | ${entry.computed_state || entry.state || 'open'} |\n`;
        report += `| Sequence | #${entry.sequence} |\n`;
        report += `| Hash | \`${entry.entry_hash}\` |\n`;
        report += `| Timestamp | ${entry.timestamp} |\n`;
        report += `\n**Body:**\n${entry.payload?.body || entry.body_preview || '—'}\n`;

        if (entry.payload?.source) {
          const src = typeof entry.payload.source === 'object' ? entry.payload.source.source_url : entry.payload.source;
          report += `\n**Source:** ${src}\n`;
        }

        const responses = data.responses || [];
        if (responses.length) {
          report += `\n## Responses (${responses.length})\n\n`;
          for (const r of responses) {
            report += `- **${r.subtype}** (#${r.sequence}): ${truncate(r.payload?.body || r.body_preview, 100)} [\`${r.entry_id?.slice(0, 8)}…\`]\n`;
          }
        }
      }

      return { content: [{ type: 'text', text: report }] };
    } catch (err) {
      return { content: [{ type: 'text', text: `Error: ${err.message}` }] };
    }
  }
);

// ═════════════════════════════════════════════════════════════════════
// Tool 4: acta_discover — Find where contribution is needed
// ═════════════════════════════════════════════════════════════════════

server.tool(
  'acta_discover',
  'Find actionable work across the Acta record. Surfaces contested records needing evidence, claims with no evidence, predictions approaching resolution, and recently active topics. This is the "where am I needed?" tool.',
  {
    mode: z.enum(['contested', 'needs_evidence', 'approaching_resolution', 'recent_activity']).describe(
      'contested: records in contested state. needs_evidence: claims/predictions with no linked evidence. approaching_resolution: predictions with resolution dates within 30 days. recent_activity: topics with recent entries.'
    ),
    limit: z.number().min(1).max(20).optional().describe('Maximum results (default: 10)'),
  },
  async (args) => {
    const limit = args.limit || 10;

    try {
      // Fetch all topics
      const topicsRes = await actaFetch('/api/topics');
      const topics = await topicsRes.json();

      let report = '';
      const results = [];

      for (const t of topics) {
        const feedRes = await actaFetch(`/api/feed?topic=${encodeURIComponent(t.topic)}`);
        const feedData = await feedRes.json();
        const contributions = feedData.contributions || [];

        for (const c of contributions) {
          const state = c.computed_state || c.state || 'open';
          const body = truncate(c.body_preview || c.payload?.body, 80);

          if (args.mode === 'contested' && state === 'contested') {
            results.push({ topic: t.topic, entry_id: c.entry_id, subtype: c.subtype, state, body, sequence: c.sequence });
          }

          if (args.mode === 'needs_evidence' && state === 'open' && (c.subtype === 'claim' || c.subtype === 'prediction')) {
            // Check if there are any evidence responses
            const entries = feedData.entries || [];
            const hasEvidence = entries.some(e =>
              e.type === 'response' && e.subtype === 'evidence' &&
              (e.payload?.target_id === c.entry_id || (e.linked_to || []).includes(c.entry_id))
            );
            if (!hasEvidence) {
              results.push({ topic: t.topic, entry_id: c.entry_id, subtype: c.subtype, state, body, sequence: c.sequence });
            }
          }

          if (args.mode === 'approaching_resolution' && c.subtype === 'prediction' && c.payload?.resolution_date) {
            const resDate = new Date(c.payload.resolution_date);
            const daysUntil = (resDate - Date.now()) / (1000 * 60 * 60 * 24);
            if (daysUntil > 0 && daysUntil <= 30 && state !== 'resolved_confirmed' && state !== 'resolved_refuted') {
              results.push({
                topic: t.topic, entry_id: c.entry_id, subtype: c.subtype, state, body, sequence: c.sequence,
                resolution_date: c.payload.resolution_date, days_until: Math.round(daysUntil),
              });
            }
          }

          if (args.mode === 'recent_activity') {
            // Handled at topic level below
          }

          if (results.length >= limit) break;
        }
        if (results.length >= limit) break;
      }

      // recent_activity mode: rank topics by last entry
      if (args.mode === 'recent_activity') {
        const sorted = [...topics]
          .filter(t => t.last_entry_at)
          .sort((a, b) => new Date(b.last_entry_at) - new Date(a.last_entry_at))
          .slice(0, limit);

        report = `# Recently Active Topics\n\n`;
        report += `| Topic | Entries | Last Activity |\n|-------|---------|---------------|\n`;
        for (const t of sorted) {
          report += `| ${t.topic} | ${t.entry_count} | ${t.last_entry_at} |\n`;
        }
        report += `\nUse \`acta_query\` with \`action: "feed"\` to explore any topic.\n`;
        return { content: [{ type: 'text', text: report }] };
      }

      // Format results for other modes
      const modeLabels = {
        contested: 'Contested Records',
        needs_evidence: 'Records Needing Evidence',
        approaching_resolution: 'Predictions Approaching Resolution',
      };

      report = `# ${modeLabels[args.mode]}\n\n`;

      if (!results.length) {
        report += `No records found for this mode.\n`;
      } else {
        report += `| # | Topic | Type | State | Body | Entry ID |\n|---|-------|------|-------|------|----------|\n`;
        for (let i = 0; i < results.length; i++) {
          const r = results[i];
          let extra = '';
          if (r.days_until !== undefined) extra = ` (${r.days_until}d)`;
          report += `| ${i + 1} | ${r.topic} | ${r.subtype} | ${r.state}${extra} | ${r.body} | \`${r.entry_id?.slice(0, 8)}…\` |\n`;
        }
        report += `\n**Found:** ${results.length} records\n`;
      }

      report += `\nUse \`acta_respond\` to submit evidence, challenges, or resolutions.\n`;

      return { content: [{ type: 'text', text: report }] };
    } catch (err) {
      return { content: [{ type: 'text', text: `Error discovering work: ${err.message}` }] };
    }
  }
);

// ═════════════════════════════════════════════════════════════════════
// Tool 5: acta_verify — Verify chain integrity
// ═════════════════════════════════════════════════════════════════════

server.tool(
  'acta_verify',
  'Verify the hash chain integrity for a specific topic. Returns chain length, chain head hash, and any integrity issues. Note: this is operator-served verification. For independent verification, use acta_export and run verify.js locally.',
  {
    topic: z.string().describe('Topic slug to verify'),
  },
  async ({ topic }) => {
    try {
      const res = await actaFetch(`/api/verify?topic=${encodeURIComponent(topic)}`);

      if (!res.ok) {
        return { content: [{ type: 'text', text: `Verification failed (HTTP ${res.status}). Topic may not exist.` }] };
      }

      const data = await res.json();

      let report = `# Chain Verification: ${topic}\n\n`;
      report += `| Metric | Value |\n|--------|-------|\n`;
      report += `| Chain Valid | ${data.valid ? '✓ Yes' : '✗ NO — INTEGRITY ISSUE'} |\n`;
      if (data.length || data.chain_length) report += `| Chain Length | ${data.length || data.chain_length} entries |\n`;
      if (data.chain_head_hash) report += `| Chain Head | \`${data.chain_head_hash}\` |\n`;

      if (!data.valid) {
        report += `\n## Issues\n\n`;
        if (data.reason) report += `- ${data.reason}\n`;
        if (data.broken_at !== undefined) report += `- Chain broken at entry index ${data.broken_at}\n`;
      }

      report += `\n> This is operator-served verification. For independent verification:\n`;
      report += `> \`curl ${ACTA_BASE}/api/export/${topic} | node tools/verify.js\`\n`;

      return { content: [{ type: 'text', text: report }] };
    } catch (err) {
      return { content: [{ type: 'text', text: `Error: ${err.message}` }] };
    }
  }
);

// ═════════════════════════════════════════════════════════════════════
// Tool 6: acta_export — Export full chain for independent verification
// ═════════════════════════════════════════════════════════════════════

server.tool(
  'acta_export',
  'Export the full hash chain for a topic. Returns all entries with hashes for independent verification using tools/verify.js. Use this when you need to audit the record independently.',
  {
    topic: z.string().describe('Topic slug to export'),
  },
  async ({ topic }) => {
    try {
      const res = await actaFetch(`/api/export/${encodeURIComponent(topic)}`);

      if (!res.ok) {
        return { content: [{ type: 'text', text: `Export failed (HTTP ${res.status}). Topic may not exist.` }] };
      }

      const data = await res.json();
      const entries = data.entries || [];

      let report = `# Chain Export: ${topic}\n\n`;
      report += `| Metric | Value |\n|--------|-------|\n`;
      report += `| Topic | ${data.topic} |\n`;
      report += `| Total Entries | ${entries.length} |\n`;
      report += `| Exported At | ${data.exported_at} |\n`;
      if (data.chain_head) {
        report += `| Chain Head Hash | \`${data.chain_head.chain_head_hash || data.chain_head.entry_hash}\` |\n`;
        report += `| Chain Length | ${data.chain_head.chain_length} |\n`;
      }

      report += `\n## Entries\n\n`;
      report += `| # | Type | Subtype | Hash | Timestamp |\n|---|------|---------|------|----------|\n`;
      for (const e of entries) {
        report += `| #${e.sequence} | ${e.type} | ${e.subtype} | \`${e.entry_hash?.slice(0, 12)}…\` | ${e.timestamp} |\n`;
      }

      report += `\n> Verify independently: save this JSON and run \`node tools/verify.js export.json\`\n`;

      return { content: [{ type: 'text', text: report }] };
    } catch (err) {
      return { content: [{ type: 'text', text: `Error: ${err.message}` }] };
    }
  }
);

// ═════════════════════════════════════════════════════════════════════
// Start Server
// ═════════════════════════════════════════════════════════════════════

const transport = new StdioServerTransport();
await server.connect(transport);

/**
 * MCP server — runs locally via stdio, talks to the hosted LLMTest API.
 * No direct database access. Only needs LLMTEST_API_KEY.
 *
 * Fast endpoints return JSON directly.
 * Slow endpoints (benchmark, sync) return SSE streams with progress + result.
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';

const API_KEY = process.env.LLMTEST_API_KEY;
const BASE_URL = process.env.LLMTEST_BASE_URL || 'https://llmtest.io';

async function fetchApi(path, { method = 'GET', body } = {}) {
  const res = await fetch(`${BASE_URL}${path}`, {
    method,
    headers: {
      'Authorization': `Bearer ${API_KEY}`,
      'Content-Type': 'application/json',
    },
    ...(body ? { body: JSON.stringify(body) } : {}),
  });

  if (!res.ok) {
    const text = await res.text();
    throw new Error(`API ${method} ${path} failed: ${res.status} ${text.slice(0, 200)}`);
  }

  return res;
}

/**
 * Call an API endpoint and return the result.
 * Handles both JSON responses (fast endpoints) and SSE streams (slow endpoints).
 */
async function callApi(path, opts = {}) {
  const res = await fetchApi(path, opts);
  const contentType = res.headers.get('content-type') || '';

  // Fast endpoint — plain JSON
  if (contentType.includes('application/json')) {
    return { result: await res.json(), progressLines: [] };
  }

  // Slow endpoint — SSE stream: read events until we get result or error
  const text = await res.text();
  const progressLines = [];
  let result = null;

  for (const block of text.split('\n\n')) {
    const eventMatch = block.match(/^event: (\w+)/);
    const dataMatch = block.match(/^data: (.+)$/m);
    if (!eventMatch || !dataMatch) continue;

    const event = eventMatch[1];
    const data = JSON.parse(dataMatch[1]);

    if (event === 'progress') progressLines.push(data.message);
    else if (event === 'result') result = data;
    else if (event === 'error') throw new Error(data.error);
  }

  if (!result) throw new Error('SSE stream ended without a result');
  return { result, progressLines };
}

export function createMcpServer() {
  const server = new McpServer({ name: 'llmtest', version: '0.6.0' });
  let lastToolUsed = null;

  // Wrap server.tool to auto-track the last tool used
  const origTool = server.tool.bind(server);
  server.tool = (name, ...rest) => {
    const handler = rest.pop();
    origTool(name, ...rest, async (...args) => {
      lastToolUsed = name;
      return handler(...args);
    });
  };

  // ─── Status ─────────────────────────────────────────────────────────────────
  server.tool('status',
    'Show LLMTest proxy status and a summary of monitored AI activity.',
    {},
    async () => {
      if (!API_KEY) return { content: [{ type: 'text', text: 'LLMTEST_API_KEY not set. Get your key at https://llmtest.io/dashboard' }] };

      const { result: data } = await callApi('/api/status');
      return { content: [{ type: 'text', text: [
        `LLMTest is running.`,
        ``,
        `${data.flows} flows | ${data.calls} calls | $${data.spend.toFixed(4)} tracked spend`,
        `${data.pendingSuggestions} pending suggestion(s)`,
        ``,
        `Proxy: ${BASE_URL}/v1`,
        `Ask: "list my AI flows", "any cost-saving suggestions?", or "what models are trending?"`,
      ].join('\n') }] };
    }
  );

  // ─── List flows ──────────────────────────────────────────────────────────────
  server.tool('list_flows',
    'Show all AI features in this project with their current model, call volume, latency, and cost.',
    {},
    async () => {
      const { result: flows } = await callApi('/api/flows');
      if (!flows.length) return { content: [{ type: 'text', text:
        'No flows detected yet. Point your app at the LLMTest proxy and start making calls.' }] };

      const lines = flows.map(f =>
        `- ${f.flow}\n  model: ${f.model} | calls: ${f.call_count} | avg latency: ${f.avg_latency_ms}ms | total cost: $${f.total_cost_usd}`
      );
      return { content: [{ type: 'text', text: `AI flows:\n\n${lines.join('\n\n')}` }] };
    }
  );

  // ─── Get suggestions ─────────────────────────────────────────────────────────
  server.tool('get_suggestions',
    'Get pending recommendations to switch to a cheaper or faster model without losing quality.',
    {},
    async () => {
      const { result: suggestions } = await callApi('/api/suggestions');
      if (!suggestions.length) return { content: [{ type: 'text', text:
        'No suggestions yet. Benchmarks run automatically when flows hit 50+ calls, or trigger one with run_benchmark.' }] };

      const lines = suggestions.map(s => {
        const saving = parseFloat(s.cost_saving);
        const costLabel = saving >= 0
          ? `${(saving * 100).toFixed(0)}% cheaper`
          : `${(Math.abs(saving) * 100).toFixed(0)}% more expensive`;
        const latency = s.latency_delta > 0 ? `${s.latency_delta}ms slower` : `${Math.abs(s.latency_delta)}ms faster`;
        const quality = parseFloat(s.quality_score);
        const qualityLabel = quality >= 0.9 ? 'equivalent quality' : 'minor quality tradeoff';
        return [
          `[#${s.id}] ${s.flow}`,
          `  Switch: ${s.current_model} -> ${s.challenger}`,
          `  ${qualityLabel} | ${costLabel} | ${latency}`,
          `  To implement: say "accept suggestion ${s.id}"`,
        ].join('\n');
      });

      return { content: [{ type: 'text', text: `Pending suggestions:\n\n${lines.join('\n\n')}` }] };
    }
  );

  // ─── Accept / dismiss suggestion ─────────────────────────────────────────────
  server.tool('update_suggestion',
    'Accept or dismiss a model-switch suggestion by ID.',
    {
      id: z.number().describe('Suggestion ID from get_suggestions'),
      action: z.enum(['accept', 'dismiss']).describe('"accept" to apply it, "dismiss" to ignore'),
    },
    async ({ id, action }) => {
      await callApi(`/api/suggestions/${id}`, { method: 'POST', body: { action } });
      return { content: [{ type: 'text', text: action === 'accept'
        ? `Suggestion #${id} accepted. Update the model ID in your code accordingly.`
        : `Suggestion #${id} dismissed.` }] };
    }
  );

  // ─── Run benchmark ───────────────────────────────────────────────────────────
  server.tool('run_benchmark',
    `Benchmark a flow against alternative models. Use optimize_for to focus the search:
"cost" tests cheaper models, "quality" tests potentially better models,
"speed" tests faster models, "balanced" (default) tests a diverse spread.

Use challengers to test specific models (e.g. ["anthropic/claude-sonnet-4", "google/gemini-2.5-flash-preview"]).
If omitted, challengers are selected automatically based on optimize_for.

For pre-launch projects with no real traffic: seed samples first with seed_samples, then call this
with currentModel set to the model you are currently using (or planning to use).

For post-launch projects: currentModel is detected automatically from call history.`,
    {
      flow: z.string().describe('Flow name to benchmark'),
      currentModel: z.string().optional().describe(
        'The model currently in use for this flow (e.g. "openai/gpt-4o"). ' +
        'Required for pre-launch flows with no call history. ' +
        'Auto-detected from traffic if omitted.'
      ),
      optimize_for: z.enum(['cost', 'quality', 'speed', 'balanced']).optional().describe(
        'What to optimize for. "cost" finds cheaper models, "quality" finds better models, ' +
        '"speed" finds faster models, "balanced" (default) finds the best overall tradeoff.'
      ),
      challengers: z.array(z.string()).optional().describe(
        'Specific model IDs to test against the baseline (e.g. ["anthropic/claude-sonnet-4", "openai/gpt-4o-mini"]). ' +
        'If omitted, challengers are selected automatically. Use list_new_models to discover available models.'
      ),
    },
    async ({ flow, currentModel, optimize_for, challengers }) => {
      const { result, progressLines } = await callApi('/api/benchmark', {
        method: 'POST',
        body: { flow, currentModel, optimizeFor: optimize_for || 'balanced', challengers: challengers || null },
      });

      if (result.skipped) {
        return { content: [{ type: 'text', text: `Skipped: ${result.reason}` }] };
      }

      const goal = result.optimizeFor || 'balanced';

      const challengerLines = (result.results || []).map(r => {
        const costLabel = r.costSaving >= 0
          ? (r.avgCost === 0 ? 'free' : `${(r.costSaving*100).toFixed(0)}% cheaper`)
          : `${(Math.abs(r.costSaving)*100).toFixed(0)}% more expensive`;
        const latencyLabel = r.latencyDelta <= 0
          ? `${Math.abs(r.latencyDelta)}ms faster`
          : `${r.latencyDelta}ms slower`;
        const rec = r.recommendation ? ` [${r.recommendation}]` : '';
        const pick = r.topPick ? ' ★' : '';
        return `${pick} ${r.challenger}: won ${r.wins}, tied ${r.ties}, lost ${r.losses} of ${r.total} | ${costLabel}, ${latencyLabel}${rec}`;
      });

      const goalInstructions = {
        cost: [
          `The user wants to MINIMIZE COST. Rank by cost savings.`,
          `Highlight the cheapest option that maintains acceptable quality (few losses).`,
          `If a model is 30%+ cheaper with minor quality tradeoffs, strongly recommend it.`,
        ],
        quality: [
          `The user wants to MAXIMIZE QUALITY. Rank by win rate.`,
          `Highlight any model that outperforms the baseline, even if it costs more.`,
          `A model that wins consistently is worth recommending regardless of price.`,
        ],
        speed: [
          `The user wants to MINIMIZE LATENCY. Rank by speed improvement.`,
          `Highlight the fastest option with acceptable quality.`,
          `Note: latency varies by load — treat as directional, not absolute.`,
        ],
        balanced: [
          `Present all results to the user with clear tradeoffs for each option.`,
          `Let the user decide which tradeoff matters most to them.`,
        ],
      };

      const summary = [
        `Benchmark complete for "${result.flow}" (optimizing for: ${goal}).`,
        `Baseline: ${result.currentModel} | avg cost $${result.baselineCost.toFixed(5)} | avg latency ${result.baselineLatency}ms`,
        `Scoring: pairwise comparison with position swap (Claude Sonnet judge)`,
        ``,
        `Results (ranked by ${goal}):`,
        ...challengerLines,
        ``,
        ...(goalInstructions[goal] || goalInstructions.balanced),
        `- Models with more wins than losses offer BETTER quality`,
        `- Models with 0 losses and all ties offer EQUIVALENT quality`,
        `- Cost savings and latency differences should be stated clearly`,
      ].join('\n');

      return { content: [{ type: 'text', text: summary }] };
    }
  );

  // ─── Trending models ─────────────────────────────────────────────────────────
  server.tool('list_new_models',
    'Show new and trending models that are worth benchmarking soon.',
    {},
    async () => {
      const { result: models } = await callApi('/api/models/trending');
      if (!models.length) return { content: [{ type: 'text', text:
        'No model data yet. The model registry syncs daily.' }] };

      const lines = models.map(m =>
        `- ${m.name} (${m.id})\n  Reason: ${m.reason} | Price: $${(m.promptPrice * 1e6).toFixed(2)}/M tokens | Context: ${(m.contextLength / 1000).toFixed(0)}k`
      );

      return { content: [{ type: 'text', text: `New & trending models:\n\n${lines.join('\n\n')}` }] };
    }
  );

  // ─── Prompt optimization ─────────────────────────────────────────────────────
  server.tool('optimize_prompt',
    `Analyze a flow's prompt and automatically generate an optimized version.

Tests optimized prompt against baseline using real samples and a multi-judge AI (Claude Sonnet + GPT-4o, position-swapped, self-consistency). Also tests cheaper models.

REQUIRES: at least 3 samples on the flow. If the flow has none (zero traffic), BEFORE calling this tool you should: (1) ask the user to describe the feature, (2) find or ask for their system prompt, (3) generate 5-10 realistic synthetic user inputs, (4) call seed_samples with [{role:'system', content:<prompt>}, {role:'user', content:<synthetic input>}] for each, (5) THEN call optimize_prompt. Tell the user synthetic-sample results are "indicative" vs real-traffic results.

Confidence levels: HIGH (safe to accept), MEDIUM (review first), LOW (need more traffic), NEGATIVE (do not accept).

Cost: ~$1-2 per run, billed to the user's LLMTest credits.`,
    {
      flow: z.string().describe('Flow name to optimize (e.g. "support-bot", "email-writer")'),
      optimize_for: z.enum(['cost', 'quality', 'speed', 'balanced']).optional().describe(
        'What to optimize for. "cost" shortens prompts, "quality" adds precision, "balanced" tries both.'
      ),
    },
    async ({ flow, optimize_for }) => {
      const { result, progressLines } = await callApi('/api/optimize-prompt', {
        method: 'POST',
        body: { flow, optimizeFor: optimize_for || 'balanced' },
      });

      if (result.skipped) {
        return { content: [{ type: 'text', text: `Optimization skipped: ${result.reason}` }] };
      }

      const lines = [
        `Prompt optimization for "${flow}" complete!`,
        '',
        `Strategy: ${result.strategy}`,
        `Quality: ${(parseFloat(result.quality) * 100).toFixed(0)}% (${result.wins}W/${result.ties}T/${result.losses}L)`,
        `Token savings: ${result.tokenSaving} (${result.originalTokens} → ${result.optimizedTokens} tokens)`,
        result.modelCostSaving ? `Model savings: ${result.modelCostSaving} by switching to ${result.recommendedModel}` : null,
        `Total estimated savings: ${result.totalEstimatedSaving}`,
        `Optimization cost: ${result.optimizationCost}`,
        '',
        '── Optimized prompt ──────────────────────',
        result.optimizedPrompt,
      ].filter(Boolean);

      return { content: [{ type: 'text', text: lines.join('\n') }] };
    }
  );

  // ─── Autopilot ────────────────────────────────────────────────────────────────
  server.tool('get_autopilot_status',
    `Show whether autopilot is enabled and whether the account meets the prerequisites.

Autopilot automatically optimizes prompts and models for eligible flows every 7 days.
Checks: optimization scheduler (weekly), drift detection (daily scan, per-optimization weekly).

Prerequisites for a flow to be auto-optimized:
- Autopilot enabled on the account
- Email verified
- Account age >= 14 days (trust ramp)
- Flow has >=20 real calls in the last 7 days
- Flow not optimized by autopilot in the last 14 days (cooldown)
- Account has credits (each run costs ~$1-2)

Safety gates (all must pass to auto-accept): 95% CI lower bound > 50%, multi-judge agreement >= 80%, >=20% total savings, no length-bias warning, golden-set regression check.
After auto-accept: 24h revert window. Drift detection reverts automatically if quality degrades later.`,
    {},
    async () => {
      const { result: s } = await callApi('/api/autopilot');
      const lines = [
        `Autopilot: ${s.enabled ? 'ENABLED' : 'DISABLED'}`,
        `Ready to run: ${s.ready ? 'YES' : 'NO'}`,
        '',
        `Prerequisites:`,
        `  Email verified: ${s.email_verified ? '✓' : '✗'}`,
        `  Account age: ${s.account_age_days} days ${s.account_age_ok ? '✓' : '✗ (need 14+)'}`,
        `  Credits: $${s.credits_usd.toFixed(4)} ${s.has_credits ? '✓' : '✗ (top up to run)'}`,
        '',
        `Per-flow requirements: ${s.requirements.min_calls}; ${s.requirements.cooldown}`,
        '',
        `Cadence: ${s.behavior.optimization_cadence}; ${s.behavior.drift_cadence}`,
        `Revert: ${s.behavior.revert_window}. Auto-revert: ${s.behavior.auto_revert}`,
        '',
        `Safety gates (all must pass):`,
        ...s.behavior.safety_gates.map(g => `  - ${g}`),
        '',
        s.enabled
          ? 'To disable: call disable_autopilot.'
          : 'To enable: call enable_autopilot.',
      ];
      return { content: [{ type: 'text', text: lines.join('\n') }] };
    }
  );

  server.tool('enable_autopilot',
    `Turn on autopilot. Once enabled, LLMTest will automatically optimize eligible flows every 7 days, auto-accept changes that pass all safety gates, and auto-revert if drift detection later sees regressions.

Cost: each optimization run costs ~$1-2, billed to LLMTest credits. Runs are skipped silently if the account has no credits.

Prerequisites: verified email, account age >= 14 days, and >=20 real calls per flow. Use get_autopilot_status to check readiness.`,
    {},
    async () => {
      await callApi('/api/autopilot', { method: 'POST', body: { enabled: true } });
      const { result: s } = await callApi('/api/autopilot');
      const warnings = [];
      if (!s.email_verified) warnings.push('Email not verified — autopilot will skip until verified.');
      if (!s.account_age_ok) warnings.push(`Account is ${s.account_age_days} days old — autopilot activates at 14 days (trust ramp).`);
      if (!s.has_credits) warnings.push('No credits — top up at https://llmtest.io/dashboard so runs can execute.');
      return { content: [{ type: 'text', text: [
        'Autopilot enabled.',
        warnings.length ? '\nHeads up:\n' + warnings.map(w => '  - ' + w).join('\n') : '\nReady to run on your next eligible flow cycle.',
      ].join('') }] };
    }
  );

  server.tool('disable_autopilot',
    'Turn off autopilot. Already-accepted optimizations stay active; only future runs are paused. Use enable_autopilot to turn it back on.',
    {},
    async () => {
      await callApi('/api/autopilot', { method: 'POST', body: { enabled: false } });
      return { content: [{ type: 'text', text: 'Autopilot disabled. Previously accepted optimizations remain active.' }] };
    }
  );

  server.tool('list_active_optimizations',
    'List auto-accepted optimizations still within their 24h revert window. Each includes the flow, strategy, savings, and hours remaining to revert.',
    {},
    async () => {
      const { result: rows } = await callApi('/api/optimizations/active');
      if (!rows.length) return { content: [{ type: 'text', text: 'No auto-accepted optimizations in the revert window right now.' }] };
      const lines = rows.map(o => {
        const saving = o.cost_saving != null ? `${(o.cost_saving * 100).toFixed(0)}% saved` : '—';
        return `[#${o.id}] ${o.flow}\n  strategy: ${o.strategy} | ${saving} | ${o.hours_left_to_revert}h left to revert\n  To revert: call revert_optimization with id ${o.id}`;
      });
      return { content: [{ type: 'text', text: 'Active auto-accepted optimizations:\n\n' + lines.join('\n\n') }] };
    }
  );

  server.tool('revert_optimization',
    'Revert an auto-accepted optimization. Only works within the 24h revert window. Restores the previous active prompt. Use list_active_optimizations to find IDs.',
    {
      id: z.number().describe('Optimization ID from list_active_optimizations'),
    },
    async ({ id }) => {
      const { result } = await callApi(`/api/optimizations/${id}/revert`, { method: 'POST', body: {} });
      return { content: [{ type: 'text', text: `Reverted optimization #${id} for flow "${result.flow}". The previous prompt is now active.` }] };
    }
  );

  // ─── Account status ───────────────────────────────────────────────────────────
  server.tool('get_account',
    'Check your credit balance and usage stats.',
    {},
    async () => {
      const { result: u } = await callApi('/api/account');
      return { content: [{ type: 'text', text: [
        `Account: ${u.email ?? 'no email'}`,
        `Credits remaining: $${u.credits_usd.toFixed(4)}`,
        `Total spent: $${u.total_spent.toFixed(4)}`,
        `Created: ${new Date(u.created_at).toISOString().slice(0, 10)}`,
      ].join('\n') }] };
    }
  );

  // ─── Seed samples ─────────────────────────────────────────────────────────────
  server.tool('seed_samples',
    `Register test samples for a flow so it can be benchmarked without real traffic.
Use this for pre-launch projects or when you want to benchmark a specific scenario.

Each sample must be an array of messages in OpenAI chat format:
  [{ "role": "system", "content": "..." }, { "role": "user", "content": "..." }]

To use: read the codebase to find the prompt for this flow, then generate 5-10 realistic
and varied user inputs that represent what real users would send. Max 10 samples per call.`,
    {
      flow: z.string().describe(
        'Flow name — must match the x-flow header used in the code (e.g. "blog-writer", "support-bot")'
      ),
      samples: z.array(
        z.array(
          z.object({
            role:    z.enum(['system', 'user', 'assistant']).describe('Message role'),
            content: z.string().describe('Message content'),
          })
        )
      ).min(1).max(10).describe(
        'Array of test cases (max 10). Each test case is an array of messages (the full conversation to send to the model).'
      ),
    },
    async ({ flow, samples }) => {
      const { result } = await callApi('/api/samples', {
        method: 'POST',
        body: { flow, samples },
      });

      return { content: [{ type: 'text', text: [
        `Seeded ${result.seeded} sample(s) for flow "${flow}".`,
        `Total samples stored: ${result.total}`,
        result.ready
          ? `Ready to benchmark. Run: run_benchmark with flow "${flow}"`
          : `Need more samples before benchmarking.`,
      ].join('\n') }] };
    }
  );

  // ─── List samples ──────────────────────────────────────────────────────────────
  server.tool('list_samples',
    'Show how many test samples are stored for each flow.',
    {},
    async () => {
      const { result: data } = await callApi('/api/samples');
      if (!data.length) return { content: [{ type: 'text', text:
        'No flows yet. Seed samples with seed_samples or start the proxy and make some calls.' }] };

      const lines = data.map(f => {
        const ready = f.ready ? 'ready' : `${f.count}/3`;
        return `- ${f.flow}: ${f.count} sample(s) [${ready}]`;
      });

      return { content: [{ type: 'text', text: `Samples per flow:\n\n${lines.join('\n')}` }] };
    }
  );

  // ─── Agent feedback ──────────────────────────────────────────────────────────
  // Use origTool so leave_feedback itself doesn't overwrite lastToolUsed
  origTool('leave_feedback',
    `After using any tool in this MCP server, you may call this to share your experience as an AI agent. This helps improve the tool. This is YOUR assessment as an agent, not the user's.`,
    {
      rating: z.number().int().min(1).max(5).describe('How well the tool worked for you as an agent (1=poor, 5=excellent)'),
      comment: z.string().optional().describe('What worked well or what was confusing (schema clarity, error messages, response format, etc.)'),
      agent_model: z.string().describe('Your model name and version (e.g. "claude-opus-4-6", "gpt-4o", "gemini-2.5-pro")'),
      agent_environment: z.string().describe('Where you are running (e.g. "Claude Code", "Cursor", "Codex CLI", "Windsurf", "Terminal", "Custom Agent")'),
      task_summary: z.string().optional().describe('Brief description of what you were trying to accomplish'),
    },
    async ({ rating, comment, agent_model, agent_environment, task_summary }) => {
      await callApi('/api/feedback', {
        method: 'POST',
        body: {
          tool_name: lastToolUsed,
          rating,
          comment,
          agent_model,
          agent_environment,
          task_summary,
        },
      });

      return { content: [{ type: 'text', text:
        `Thanks for the feedback! Recorded: ${rating}/5 for tool "${lastToolUsed || 'unknown'}".` }] };
    }
  );

  return server;
}

export async function startMcpServer() {
  if (!API_KEY) {
    console.error('Error: LLMTEST_API_KEY environment variable is required.');
    console.error('Get your key at https://llmtest.io/dashboard');
    process.exit(1);
  }

  const server = createMcpServer();
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('LLMTest MCP server ready (stdio)');
}

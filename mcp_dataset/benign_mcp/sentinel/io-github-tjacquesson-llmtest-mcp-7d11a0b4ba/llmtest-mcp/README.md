# LLMTest MCP Server

<!-- mcp-name: io.github.tjacquesson/llmtest-mcp -->

[![npm version](https://img.shields.io/npm/v/llmtest-mcp.svg)](https://www.npmjs.com/package/llmtest-mcp)
[![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

MCP server that benchmarks AI models on your actual prompts and finds cheaper, faster alternatives. Works with Claude Code, Cursor, Windsurf, and any MCP-compatible tool.

## Quick Start

### 1. Get your API key

Sign up at [llmtest.io](https://llmtest.io) and grab your API key from the dashboard.

### 2. Add to your tool

**Claude Code:**

```bash
claude mcp add llmtest -- npx llmtest-mcp
```

Then set your key:

```bash
export LLMTEST_API_KEY=llmt_your_key_here
```

**Cursor / Windsurf / Other MCP clients:**

Add to your MCP config file:

```json
{
  "mcpServers": {
    "llmtest": {
      "command": "npx",
      "args": ["llmtest-mcp"],
      "env": {
        "LLMTEST_API_KEY": "llmt_your_key_here"
      }
    }
  }
}
```

### 3. Talk to your AI

Just ask in natural language:

- "Check my LLMTest status"
- "Find cheaper models for my AI calls"
- "Run a benchmark on my blog-writer flow"
- "What models are trending?"

## How It Works

LLMTest is a proxy that sits between your app and AI providers. Point your app at `https://llmtest.io/v1` instead of calling OpenAI/Anthropic directly, and LLMTest tracks your usage, benchmarks alternatives, and suggests cost savings.

This MCP server gives your AI assistant access to LLMTest's tools so it can manage everything for you.

## Available Tools

| Tool | Description |
|------|-------------|
| `status` | Show proxy status and activity summary |
| `list_flows` | List all AI flows with cost and latency stats |
| `get_suggestions` | Get pending model-switch recommendations |
| `update_suggestion` | Accept or dismiss a suggestion |
| `run_benchmark` | Benchmark a flow against challenger models |
| `optimize_prompt` | Rewrite a flow's prompt and find a cheaper model that still works |
| `seed_samples` | Add test prompts for pre-launch benchmarking |
| `list_samples` | Show stored test samples per flow |
| `list_new_models` | Show new and trending models |
| `get_account` | Check credit balance and usage |
| `get_autopilot_status` | Check whether autopilot is on and whether the account is eligible |
| `enable_autopilot` | Turn on weekly auto-optimization with safety gates + drift-based auto-revert |
| `disable_autopilot` | Turn off autopilot (existing optimizations stay active) |
| `list_active_optimizations` | List auto-accepted optimizations still inside their 24h revert window |
| `revert_optimization` | Roll an auto-accepted optimization back to the previous prompt |

## Autopilot

Autopilot automatically optimizes your flows on a weekly cadence. Changes that pass every safety gate go live with a 24-hour revert window. Drift detection keeps checking after that and rolls back if quality slips.

**To enable from your IDE:** ask your AI assistant something like "enable LLMTest autopilot". It will call `enable_autopilot`. Use `get_autopilot_status` to confirm prerequisites.

**Prerequisites** (checked per flow each cycle):

- Autopilot enabled on the account
- Email verified
- Account age ≥ 14 days (trust ramp)
- Flow has ≥ 20 real calls in the last 7 days
- Flow not optimized by autopilot in the last 14 days (cooldown)
- Positive credit balance (~$1–2 per run)

**Safety gates** (all must pass for auto-accept): 95% CI lower bound > 50% win rate, multi-judge agreement ≥ 80%, ≥ 20% total savings, no length-bias warning, golden-set regression check.

**Revert:** 24h window after auto-accept. After that, only drift detection can roll back.

## Typical Workflow

**Pre-launch (no traffic yet):**

1. Tell your AI: "I'm building a support chatbot using gpt-4o"
2. It seeds realistic test samples with `seed_samples`
3. It runs `run_benchmark` to compare models
4. It shows you `get_suggestions` with cheaper alternatives

**Post-launch (with real traffic):**

1. Route your AI calls through `https://llmtest.io/v1`
2. LLMTest monitors usage and auto-benchmarks when flows hit 50+ calls
3. Ask "any cost-saving suggestions?" to see recommendations
4. Accept a suggestion and update your code

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `LLMTEST_API_KEY` | Yes | Your API key from [llmtest.io/dashboard](https://llmtest.io/dashboard) |
| `LLMTEST_BASE_URL` | No | Custom API URL (defaults to `https://llmtest.io`) |

## Links

- [Website](https://llmtest.io)
- [Dashboard](https://llmtest.io/dashboard)
- [Docs](https://llmtest.io/docs)
- [GitHub](https://github.com/tjacquesson/llmtest-mcp)
- [npm](https://www.npmjs.com/package/llmtest-mcp)

## License

MIT

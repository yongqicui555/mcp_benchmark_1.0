# silentwatch-mcp

<!-- mcp-name: io.github.temurkhan13/silentwatch-mcp -->

> **MCP server for catching cron silent failures** — when scheduled jobs exit 0 with empty output, when retry storms run away, when action budgets leak. Surfaces overdue jobs, length anomalies, and silent-fail patterns to any Claude or MCP-aware agent. Works with **system cron, systemd timers, OpenClaw cron logs, and any JSONL run-log** out of the box. Keywords: AI agent monitoring, cron health, scheduled-task observability, production AI ops.

[![Status: v1.0.7](https://img.shields.io/badge/status-v1.0.7-brightgreen)](https://github.com/temurkhan13/silentwatch-mcp) [![Tests: 93 passing](https://img.shields.io/badge/tests-93%20passing-brightgreen)](./tests) [![License: MIT](https://img.shields.io/badge/license-MIT-blue)](./LICENSE) [![MCP](https://img.shields.io/badge/protocol-MCP-purple)](https://modelcontextprotocol.io/) [![PyPI](https://img.shields.io/pypi/v/silentwatch-mcp)](https://pypi.org/project/silentwatch-mcp/)

---

## What it does

Real silent failures from production AI deployments in the last 30 days:

- [GitHub Issue #54260, anthropics/claude-code](https://github.com/anthropics/claude-code/issues/54260) — Claude Code Routines: cron triggers fire and the routine state advances (`ended_reason: run_once_fired`), but the cloud container never reaches prompt execution. This silently affected the operator's routines for **at least 28 days** before they noticed the output files weren't updating.
- [GitHub Issue #1243, anthropics/claude-code-action](https://github.com/anthropics/claude-code-action/issues/1243) — `claude-sonnet-4-6` returns empty assistant turns in a tight loop (`stop_reason: null`, `output_tokens: 8`) for ~20 minutes. The workflow step then exits as `success` with **no artifacts produced** — the GitHub Actions API can't distinguish "completed cleanly" from "returned empty for 20 minutes burning Claude Max budget."
- [dev.to: "5 Silent Failure Patterns I Keep Finding in Production AI Systems"](https://dev.to/temurkhan13/5-silent-failure-patterns-i-keep-finding-in-production-ai-systems-4fl0) — the systematic taxonomy.

These all map to one underlying problem: **exit-code monitoring lies**. The job returned 0; the data is broken anyway. Any team running scheduled jobs has hit at least one of these:

- **Silent failure** — the job ran, returned exit code 0, but produced no useful output (a web-search cron returning empty, a backup that wrote a 0-byte file, a digest email that sent with `<no rows>` in the body). Traditional monitoring sees a green checkmark; the data is broken anyway.
- **Overdue without alert** — a job stopped running for 3 days; nobody noticed because nobody was watching
- **Last-success drift** — the job runs every hour but only succeeded once in the last 12 attempts; everyone assumes it's healthy because the most recent run was green
- **Audit-trail gap** — you need to know when a specific job last completed for a compliance check, and the only "log" is `journalctl` output that rotated last week

`silentwatch-mcp` exposes that visibility as MCP tools your AI agent can query directly. No metrics pipeline, no separate dashboard, no SaaS subscription.

```
> claude: which of my cron jobs have silent failures in the last 24 hours?
[MCP tool: find_silent_failures]
3 jobs flagged:
  • web-search-refresh — ran 12× successfully but output empty in 8 (66% silent fail rate)
  • daily-summary — ran 1× successfully (24× expected); output normal
  • audit-snapshot — last success 5 days ago, all subsequent runs returned exit 0 with empty body
```

---

## Why `silentwatch-mcp`

Three things existing tools (Cronitor, Healthchecks.io, Datadog, Prometheus) don't do:

1. **Detect silent failures, not just exit codes.** Traditional cron monitoring assumes `exit 0 = success`. We check the *output* against configurable rules: empty output, length anomaly vs historical median, error keywords in stdout despite exit 0, duration anomaly. The job that "ran successfully" but returned nothing useful — that's the failure mode that hides for weeks. We catch it.
2. **MCP-native, no integration layer.** Claude Desktop, Cline, Continue, OpenClaw agents — any MCP-aware client queries directly. No Grafana plugin, no API wrapper, no JSON to parse manually.
3. **Multi-source out of the box.** OpenClaw native JSONL logs, system crontab (`/etc/crontab` + `/etc/cron.d/*` + per-user `crontab -l`), and systemd timers (`systemctl list-timers` + `journalctl`) — all four backends ship in v0.3, so you can run `silentwatch-mcp` against whatever scheduler you have. No vendor lock-in.

Built for the **SMB self-hoster** running a $40 VPS where Datadog is overkill and a "$0/mo open-source MCP" is the right price point — but the silent-failure detection is just as valuable on enterprise infra.

---

## Tool surface

The server registers these MCP tools (full spec in [SPEC.md](./SPEC.md)):

| Tool | What it does |
|------|--------------|
| `list_jobs` | Enumerate all known cron jobs with last-run summary |
| `get_job_status(job_id)` | Detailed status for one job: last run, last success, success rate over window |
| `get_job_runs(job_id, limit)` | Recent run history with timing + status + output snippet |
| `find_overdue_jobs` | Jobs whose schedule says they should have run but haven't |
| `find_silent_failures(window_hours)` | Jobs that ran "successfully" but output looks suspicious |
| `tail_job_logs(job_id, lines)` | Recent log output for one job |

Resources:

- `cron://jobs` — list of all jobs (manifest)
- `cron://job/{id}` — individual job manifest + recent runs
- `cron://run/{id}` — individual run instance with full output

Prompts:

- `diagnose-overdue` — diagnostic prompt template for an overdue job
- `summarize-cron-health` — daily digest of cron activity + anomalies

---

## Quickstart

> **v0.3 beta — all 4 backends shipped + real overdue detection via cron-schedule parsing (croniter).** Mock, OpenClaw JSONL, crontab, and systemd backends are all production-ready. 74 tests passing. v1.0 is now polish: PyPI release + GitHub Actions CI + MCP registry submissions.

### Install

```bash
pip install silentwatch-mcp
```

### Quick verify (~30 seconds, no config)

After install, run the bundled demo to see silentwatch catch real silent-failure patterns in the mock backend's hand-crafted cron data:

```bash
silentwatch-mcp-demo
```

You'll see 6 synthetic cron jobs analyzed: 8 silent failures detected on `web-search-refresh` (output-empty pattern), 1 job overdue 72h, 4 healthy jobs as baseline. No external I/O, no API keys — safe to run anywhere. Useful first-30-seconds check that the install actually works before wiring up Claude Desktop.

### Configure for Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "silentwatch": {
      "command": "python",
      "args": ["-m", "silentwatch_mcp"],
      "env": {
        "SILENTWATCH_BACKEND": "mock"
      }
    }
  }
}
```

Backends (all four shipped as of v0.3):

- `SILENTWATCH_BACKEND=mock` — returns sample data (default for development)
- `SILENTWATCH_BACKEND=openclaw-jsonl` — parses OpenClaw's native cron run JSONL files (set `SILENTWATCH_OPENCLAW_LOGS` to the directory, default `~/.openclaw/cron-runs/`); richest data — full run history + silent-fail detection
- `SILENTWATCH_BACKEND=crontab` — parses `/etc/crontab` + `/etc/cron.d/*` + user crontabs (`crontab -l`); last-run inferred from `/var/log/syslog` or `/var/log/cron` (set `SILENTWATCH_SYSLOG` to override)
- `SILENTWATCH_BACKEND=systemd` — parses `systemctl list-timers --all --output=json` + `journalctl -u <unit>` for run history; lifts `OnCalendar=` into the schedule field

All non-mock backends gracefully return empty results on platforms / hosts where the underlying tooling isn't present, so configuration is safe to leave in place across environments.

### Restart Claude Desktop

The server registers as `silentwatch`. Test:

> Show me all my cron jobs and their last-run status.

---

## Roadmap

| Version | Scope | Status |
|---------|-------|--------|
| v0.1 | Protocol wiring, mock backend, all 6 tools registered with stub data, tests pass | ✅ Complete |
| v0.2 | OpenClaw JSONL backend implemented (real cron run parsing, malformed-line handling, silent-fail enrichment) | ✅ Complete (2026-05-02) |
| v0.3 | Crontab + systemd backends; cron-schedule parsing for real overdue detection (croniter); 35 new tests | ✅ Complete (2026-05-02) |
| v1.0 | Polish: PyPI release, GitHub Actions CI, MCP registry submissions (Glama + PulseMCP), refined silent-fail rule configuration | ⏳ Phase 1 ship target (W3, May 18) |
| v1.x | Additional backends (Cowork scheduler, Claude Code background tasks, generic JSON config), webhook emitter for alerts | ⏳ Phase 2+ |

---

## Need this adapted to your stack?

`silentwatch-mcp` ships with 4 backends (mock, OpenClaw JSONL, crontab, systemd). If your scheduler is something else — AWS EventBridge, GCP Cloud Scheduler, Hangfire, Sidekiq, Temporal, Apache Airflow, Prefect, Dagster, or a custom job runner — and you want the same silent-failure-detection MCP visibility surface for it, that's a **Custom MCP Build** engagement.

| Tier | Scope | Investment | Timeline |
|------|-------|------------|----------|
| Simple | Single backend adapter for an existing scheduler with documented API (e.g., GCP Cloud Scheduler) | **$8,000–$10,000** | 1–2 weeks |
| Standard | Custom backend + custom silent-fail rules + integration with your existing alerting (PagerDuty, Slack, etc.) | **$15,000–$20,000** | 2–4 weeks |
| Complex | Multi-backend (federated cron across regions / clusters / tenants) + RBAC + audit-log integration + on-call workflow | **$25,000–$35,000** | 4–8 weeks |

**To engage:**
1. Email **hello@temhan.dev** with subject `Custom MCP Build inquiry`
2. Include: a 1-paragraph description of your scheduler stack + which tier you're considering
3. Reply within 2 business days with a 30-min discovery call slot

This server is also part of the **[AI Production Discipline Framework](https://temurah.gumroad.com/l/ai-production-discipline-framework)** — the methodology underlying production AI audits I run.

---

## Production AI audits

If you're running production AI and want an outside practitioner to score readiness, find the failure patterns that are already present, and write the corrective-action plan — that's what this MCP is built into supporting. The standalone audit service:

| Tier | Scope | Investment | Timeline |
|------|-------|------------|----------|
| Audit Lite | One system, top-5 findings, written report | **$1,500** | 1 week |
| Audit Standard | Full audit, all 14 patterns, 5 Cs findings, 90-day follow-up | **$3,000** | 2–3 weeks |
| Audit + Workshop | Standard audit + 2-day team workshop + first monthly audit included | **$7,500** | 3–4 weeks |

Same email channel: **hello@temhan.dev** with subject `AI audit inquiry`.

---

## Contributing

PRs welcome. The structure is intentionally flat to make custom backends easy to add — see `src/silentwatch_mcp/backends/` for existing examples.

To add a new backend:

1. Subclass `CronBackend` in `backends/<your_backend>.py`
2. Implement `list_jobs`, `get_job_runs`, `tail_logs`
3. Register in `backends/__init__.py`
4. Add tests in `tests/test_backend_<your_backend>.py`

Bug reports + feature requests: open a GitHub issue.

---

## License

MIT — see [LICENSE](./LICENSE).

---

## Related

- [Production-AI MCP Suite (Gumroad bundle)](https://temurah.gumroad.com/l/production-ai-mcp-suite) — this server plus 6 others (`openclaw-health-mcp`, `openclaw-cost-tracker-mcp`, `openclaw-skill-vetter-mcp`, `openclaw-upgrade-orchestrator-mcp`, `openclaw-output-vetter-mcp`, `bash-vet-mcp`) in one curated 7-pack bundle with a decision tree, day-one drill, and Custom MCP Build CTA. $29.
- [openclaw-health-mcp](https://github.com/temurkhan13/openclaw-health-mcp) — deployment health (gateway, CPU/RAM, skills, recent errors)
- [openclaw-cost-tracker-mcp](https://github.com/temurkhan13/openclaw-cost-tracker-mcp) — token-cost telemetry + 429 prediction (v1.1+)
- [openclaw-skill-vetter-mcp](https://github.com/temurkhan13/openclaw-skill-vetter-mcp) — ClawHub skill + agent-config security vetting (v1.1+)
- [openclaw-upgrade-orchestrator-mcp](https://github.com/temurkhan13/openclaw-upgrade-orchestrator-mcp) — read-only upgrade advisor + provider-side regression detection (v1.2+)
- [openclaw-output-vetter-mcp](https://github.com/temurkhan13/openclaw-output-vetter-mcp) — agent claim verification (inline grounding-check + swallowed-exception scanner + multi-turn transcript review + action-outcome verifier v1.1+)
- [bash-vet-mcp](https://github.com/temurkhan13/bash-vet-mcp) — pre-execution shell-command vetting (28 destructive-pattern rules across 8 families)
- [AI Production Discipline Framework](https://temurah.gumroad.com/l/ai-production-discipline-framework) — Notion template, $19 — the full 14-pattern catalog this MCP server is built around
- [AI Production Auditor (GPT Store)](https://chatgpt.com/g/g-69f224f4c4c88191bb81e97051dab692-ai-production-auditor) — paste your config or agent setup, get a 5 Cs audit report. Free, ChatGPT-only.
- [SPEC.md](./SPEC.md) — full server design
- [Model Context Protocol](https://modelcontextprotocol.io/) — protocol overview

---

Built by [Temur Khan](https://www.notion.so/@temurkhan) — production AI engineer.
Contact: **hello@temhan.dev**

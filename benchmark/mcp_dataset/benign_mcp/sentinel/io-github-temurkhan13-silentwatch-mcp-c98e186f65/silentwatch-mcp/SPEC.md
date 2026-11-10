# `silentwatch-mcp` — Server Spec

**Version:** v1.0.7
**Status:** mock, openclaw-jsonl, crontab, systemd backends all production-ready; cron-schedule parsing live via croniter; v1.0.6 shipped real-bug fix (AnyUrl→str coercion in read_resource); v1.0.7 implemented `cron://run/{id}` resource that had been a documented-but-broken placeholder
**Tests:** 93 passing
**Last updated:** 2026-05-07 (D3 SPEC drift sweep)

---

## Goal (verifiable "done" criterion for v1.0)

A user runs `claude mcp add openclaw-cron-monitor`, restarts Claude Desktop (or any MCP client), and from inside Claude can:

1. Call `list_jobs` and see all scheduled jobs on their OpenClaw deployment with last-run + status
2. Call `find_silent_failures` and get a flagged list of jobs whose output is suspicious despite exit code 0
3. Call `find_overdue_jobs` and see jobs that should have run but haven't
4. Read resource `cron://run/{id}` to inspect a specific run's full output
5. Use the `summarize-cron-health` prompt to get a daily digest

All without writing bespoke code to parse cron logs, all without exposing the cron data to a third-party SaaS, all using a $0/mo open-source tool.

---

## Non-goals

- **Not a metrics platform.** No time-series database, no Grafana dashboards, no alerting webhook surface. Use this MCP server alongside your existing alerting; don't try to make it the alerting system.
- **Not enterprise-scale.** Designed for single-host or small-cluster (≤10 hosts) OpenClaw deployments. Multi-region federation is a Custom MCP Build engagement.
- **Not vendor-locked.** OpenClaw JSONL is the primary backend, but the architecture is pluggable; system cron + systemd timer support is built-in.
- **Not a job scheduler.** Read-only on cron state. Doesn't create, modify, or trigger jobs. (Consider that scope creep into Custom MCP Build territory.)

---

## Tool surface

### `list_jobs`

```
list_jobs() -> JobListResponse
```

Returns all known cron jobs with last-run summary. No parameters.

**Response shape:**
```json
{
  "jobs": [
    {
      "id": "web-search-refresh",
      "name": "Web Search Refresh",
      "schedule": "0 */1 * * *",
      "last_run_at": "2026-05-02T08:00:00Z",
      "last_run_status": "success",
      "last_success_at": "2026-05-02T03:00:00Z",
      "runs_24h": 24,
      "successes_24h": 16,
      "silent_fail_count_24h": 8
    }
  ],
  "total": 1
}
```

### `get_job_status`

```
get_job_status(job_id: str) -> JobStatus
```

Detailed status for one job.

**Response shape:**
```json
{
  "id": "web-search-refresh",
  "name": "Web Search Refresh",
  "schedule": "0 */1 * * *",
  "last_run_at": "2026-05-02T08:00:00Z",
  "last_run_status": "success",
  "last_run_duration_ms": 4823,
  "last_success_at": "2026-05-02T03:00:00Z",
  "success_rate_24h": 0.667,
  "success_rate_7d": 0.823,
  "is_overdue": false,
  "next_expected_run_at": "2026-05-02T09:00:00Z",
  "silent_fail_indicators": [
    "output_empty",
    "output_length_anomaly"
  ]
}
```

### `get_job_runs`

```
get_job_runs(job_id: str, limit: int = 20) -> JobRunsResponse
```

Recent run history with timing + status + output snippet.

**Response shape:**
```json
{
  "job_id": "web-search-refresh",
  "runs": [
    {
      "run_id": "run-2026050208000",
      "started_at": "2026-05-02T08:00:00Z",
      "completed_at": "2026-05-02T08:00:04Z",
      "duration_ms": 4823,
      "exit_code": 0,
      "status": "success",
      "silent_fail_indicators": ["output_empty"],
      "output_snippet": ""
    }
  ],
  "total": 1
}
```

### `find_overdue_jobs`

```
find_overdue_jobs(grace_minutes: int = 5) -> JobListResponse
```

Returns jobs whose schedule indicates they should have run but haven't. `grace_minutes` is tolerance to avoid flagging jobs that are about to run.

**Response shape:** same as `list_jobs`, filtered to overdue jobs only with `is_overdue: true` and `overdue_by_minutes` populated.

### `find_silent_failures`

```
find_silent_failures(window_hours: int = 24) -> SilentFailureReport
```

Jobs that returned exit code 0 but output looks suspicious within the time window.

**Response shape:**
```json
{
  "window_hours": 24,
  "jobs_flagged": [
    {
      "job_id": "web-search-refresh",
      "silent_fail_count": 8,
      "total_runs": 24,
      "silent_fail_rate": 0.333,
      "indicators": ["output_empty"],
      "sample_run_ids": ["run-2026050207000", "run-2026050206000"]
    }
  ],
  "total_jobs_checked": 6
}
```

### `tail_job_logs`

```
tail_job_logs(job_id: str, lines: int = 50) -> JobLogTail
```

Returns the most recent N lines of log output across all recent runs.

**Response shape:**
```json
{
  "job_id": "web-search-refresh",
  "lines": ["2026-05-02T08:00:01Z [INFO] starting web search refresh", "..."],
  "total_lines_returned": 50
}
```

---

## Resource surface

| URI pattern | Returns |
|-------------|---------|
| `cron://jobs` | JSON list of all jobs (same as `list_jobs` response) |
| `cron://job/{id}` | Full job manifest including last 100 runs |
| `cron://run/{id}` | Single run with full output (no truncation) |

Resources are read-only and idempotent.

---

## Prompt surface

### `diagnose-overdue`

Template prompt: *"Job `{job_id}` is overdue by `{duration}`. The job's last successful run was `{last_success_at}`. Recent runs: `{recent_runs_summary}`. Help diagnose why it's overdue and propose 3 corrective actions ranked by likelihood."*

Inputs: `job_id` (required).

### `summarize-cron-health`

Template prompt: *"Summarize the last 24 hours of cron activity for this deployment. Highlight: jobs with silent failures, overdue jobs, jobs whose success rate dropped vs the 7-day baseline. Format as a brief operational digest, max 200 words."*

No inputs.

---

## Backend architecture

```
┌─────────────────────────────────┐
│ MCP Server (server.py)          │
│  - tool registration            │
│  - argument validation          │
│  - response serialization       │
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│ Backend abstraction (backends/) │
│  CronBackend (ABC):             │
│   - list_jobs()                 │
│   - get_job_runs(job_id)        │
│   - tail_logs(job_id, lines)    │
└──────────────┬──────────────────┘
               │
        ┌──────┼──────┬───────────┐
        ▼      ▼      ▼           ▼
     ┌────┐ ┌────┐ ┌────┐    ┌────────┐
     │mock│ │JSONL│ │cron │    │systemd │
     └────┘ └────┘ └────┘    └────────┘
```

Each backend implements three core methods. Higher-level analysis (silent-fail detection, overdue detection, success-rate calculation) lives in `analysis.py` and is backend-agnostic.

### Backend selection

Environment variable `SILENTWATCH_BACKEND`:

- `mock` — sample data for protocol-wiring verification (default for development) ✅ shipped v0.1
- `openclaw-jsonl` — parses `~/.openclaw/cron-runs/*.jsonl` (configurable via `SILENTWATCH_OPENCLAW_LOGS`) ✅ shipped v0.2
- `crontab` — parses `/etc/crontab` + `/etc/cron.d/*` + per-user crontabs (`crontab -l`); last-run inferred from syslog ✅ shipped v0.3
- `systemd` — parses `systemctl list-timers --all --output=json` + `journalctl -u <unit>` for runs; lifts `OnCalendar=` into schedule ✅ shipped v0.3

**Cron-schedule parsing (v0.3+):** all backends compute `is_overdue` and `next_expected_run_at` via croniter. If a backend doesn't know the schedule (e.g., crontab couldn't determine OnCalendar from a systemd unit), schedule defaults to `"unknown"` and overdue detection returns `False`.

Multiple backends can be combined via `SILENTWATCH_BACKEND=openclaw-jsonl,crontab` (federated; jobs from both sources surface in `list_jobs`) — multi-backend support is v0.4.

---

## Silent-failure detection rules

The default rules (configurable via `SILENTWATCH_SILENT_FAIL_RULES` env var pointing to a JSON config file):

| Rule | Description | Default |
|------|-------------|---------|
| `output_empty` | Run exited 0 but stdout was empty or whitespace-only | enabled |
| `output_length_anomaly` | Stdout length is <30% of the median over the last 100 runs of this job | enabled |
| `error_keywords_in_stdout` | Stdout contains `ERROR`, `FAIL`, `Exception`, `Traceback` despite exit 0 | enabled |
| `expected_pattern_missing` | Job's manifest declares an expected_output_pattern; stdout doesn't match | enabled (if configured) |
| `duration_anomaly_short` | Duration is <10% of median (suggests immediate-return failure) | enabled |
| `duration_anomaly_long` | Duration is >300% of median (suggests hang then timeout) | disabled by default |

Rules are evaluated independently; a run flagged by any enabled rule is marked silent-failure with the rule names in `silent_fail_indicators`.

---

## OpenClaw JSONL backend — file format expectations

OpenClaw emits one JSONL file per cron job in the configured runs directory. Each line is a single run record:

```json
{"run_id":"run-2026050208000","job_id":"web-search-refresh","job_name":"Web Search Refresh","schedule":"0 */1 * * *","started_at":"2026-05-02T08:00:00Z","completed_at":"2026-05-02T08:00:04Z","duration_ms":4823,"exit_code":0,"stdout":"","stderr":"","metadata":{"openclaw_version":"2026.4.30","host":"vps01"}}
```

Required fields: `run_id`, `job_id`, `started_at`, `exit_code`. All others optional but inform analysis quality.

If your OpenClaw scheduler doesn't emit this format yet, you have three options:

1. Wrap the cron command with a logging shim that writes the JSONL line on completion (sample shim in `examples/openclaw-jsonl-shim.sh`)
2. Wait for v0.3 to ship `crontab` + `systemd` backends (less rich data, but no shim required)
3. Open a GitHub issue requesting a backend adapter for your specific scheduler — likely a Custom MCP Build engagement

**v0.2 implementation notes:**
- Malformed JSON lines are skipped with a warning; one bad line never kills the whole parse
- Records missing required fields (`run_id`, `job_id`, `started_at`, `exit_code`) are skipped with a warning
- Schedule field at the top level of the record is lifted into `metadata.schedule` for forward-compat with future schema versions
- `last_success_at` is the most-recent run with status `SUCCESS`, even when the last run was a failure
- Silent-fail detection runs in a second pass after parsing — each run gets the others as historical context for length-anomaly + duration-anomaly rules
- `is_overdue` always returns `false` in v0.2 (cron-schedule parsing lands in v0.3 with the `croniter`-style dependency)

---

## Security + privacy

- **Read-only.** The server never modifies cron state, never triggers jobs, never deletes logs.
- **Local-only by default.** All backends read local files / system commands; no outbound network calls.
- **Sensitive output redaction.** Configurable via `SILENTWATCH_REDACT_PATTERNS` — regex patterns whose matches are replaced with `[REDACTED]` before any output reaches the MCP client. Default patterns redact API keys (`sk-[A-Za-z0-9]{20,}`), bearer tokens, and basic-auth headers.
- **No telemetry.** The server doesn't phone home, doesn't write usage stats anywhere, doesn't open ports.

For the threat model in detail: see [SECURITY.md](./SECURITY.md) (planned for v0.3).

---

## Test surface

The test suite covers:

- **Protocol wiring** — `tests/test_server.py` verifies all 6 tools register with correct schemas and respond to `list_tools`
- **Backend contract** — `tests/test_backend_contract.py` runs the mock backend through every method and asserts response shapes
- **Silent-fail detection** — `tests/test_analysis.py` runs sample run histories through each rule and asserts expected flagging
- **CLI smoke test** — `tests/test_cli.py` boots the server with stdio transport and verifies it responds to a synthetic `initialize` + `list_tools` request

Run: `pytest tests/`

Target coverage at v1.0: ≥85% line coverage on `src/`.

---

## Versioning + release

- Semantic versioning, leading to v1.0 once all 4 backends ship + tests at target coverage + README + SPEC reviewed
- v0.x releases are pre-PyPI; install from source
- v1.0 published to PyPI as `silentwatch-mcp`
- Each release tagged on GitHub with changelog entry

---

## Future scope (post v1.0)

| Idea | Trigger to build |
|------|------------------|
| Multi-backend federation (`SILENTWATCH_BACKEND=openclaw-jsonl,crontab`) | Demand signal from clients with mixed-source schedulers (likely v0.4) |
| Backend for Cowork scheduler | First Cowork audit client requests it |
| Backend for Claude Code background tasks | First Claude Code-deployed agent client |
| Backend for AWS EventBridge | First AWS-hosted client; likely Custom MCP Build territory |
| Webhook emitter (push silent-fail alerts to Slack/PagerDuty) | Demand signal from ≥3 users |
| Web UI dashboard | Speculative; only if MCP-only access is genuinely a friction for a buyer cohort |

Out of scope (won't build): metrics push to Prometheus/InfluxDB, generic time-series storage, alert routing logic. Those are integration projects, not part of the MCP server itself.

---

## Lineage

This MCP server is part of the **[AI Production Discipline Framework](https://temurah.gumroad.com/l/ai-production-discipline-framework)** ecosystem. The "silent failure detection" rules trace to **Pattern P7.1** (no logs on critical paths) and **P7.3** (missing audit trail) in the framework's Production Failure Patterns Library. Field report #41372 ("Web search silent fail in --session cron") is the originating production incident.

For audit consulting that applies the framework to your specific system: **hello@temhan.dev**, subject `AI audit inquiry`.

# Changelog

All notable changes to `silentwatch-mcp` are documented here.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.11] — 2026-05-09

### Added — `monitor` subcommand for long-running NDJSON event stream (Aufgaard Phase 6 dependency)

A new subcommand exposed as `python -m silentwatch_mcp monitor [--interval 60s] [--tail] [--format ndjson]`. Runs a long-running poll loop that emits one NDJSON line on stdout per detected silent-failure, deduped by `(job_id, sample_run_id)` so each new run is reported exactly once.

This closes the Aufgaard plugin's Phase 6 dependency: Aufgaard's `silentwatch-monitor` background job invokes this subcommand and forwards each NDJSON line to the host (Claude Code / Cursor / OpenClaw) as an inline notification.

**Event shape (one per silent-failure detection):**

```json
{"type":"silent_failure","job_id":"web-search-refresh","job_name":"Web Search Refresh","pattern":"output_empty,duration_anomaly_short","silent_fail_count":8,"total_runs":24,"silent_fail_rate":0.33,"sample_run_ids":["..."],"datetime":"2026-05-09T18:40:16Z","severity":"medium"}
```

Fields match Aufgaard's notification template variables: `job_name`, `pattern`, `datetime`. Plus extra context (counts, rate, sample run IDs, severity) for surfaces that want richer detail.

**Behavior:**

- On startup: runs `build_silent_failure_report` once against the configured backend and emits NDJSON for every flagged job (immediate context for the host).
- Then enters poll loop with the configured interval (default 60s). Re-runs the report each cycle and emits NDJSON only for *new* detections (deduped by `job_id:sample_run_id`).
- Exits cleanly on SIGTERM / Ctrl+C.

Backend selection mirrors the MCP server: `SILENTWATCH_BACKEND=mock|openclaw-jsonl|crontab|systemd`.

Args (all optional, accepted for compatibility with Aufgaard's monitor command):
- `--tail` — passthrough flag (currently no-op; v2 will switch to log-tailing for openclaw_jsonl)
- `--interval <duration>` — poll interval (e.g. `60s`, `5m`). Defaults to `60s`.
- `--format ndjson` — output format

Stdout: NDJSON only (one event per line, `flush=True`). Stderr: startup banner + any errors.

`__main__.py` now dispatches `monitor` as a subcommand. Plain `python -m silentwatch_mcp` (no args) still runs the MCP server unchanged.

## [1.0.10] — 2026-05-08

### Added — `silentwatch-mcp-report` console script (V3 of cross-product UX retrofit)

A new console script that runs `build_silent_failure_report` against the configured backend and prints a one-page **GitHub-flavored markdown summary on stdout**, suitable for piping into a doc, posting to Slack, opening a GitHub issue, or rendering inline inside Claude Code / Cursor / OpenClaw.

The report differs from `silentwatch-mcp-demo`:

- **demo** → ANSI-styled output to stderr, walks through what the server does, intended as a first-30-seconds value-prove run on the mock backend
- **report** → raw markdown to stdout, intended for ongoing operational use against the real backend (or mock, if no backend configured)

Backend selection mirrors the MCP server: `SILENTWATCH_BACKEND=mock|openclaw-jsonl|crontab|systemd`. Defaults to `mock` if unset.

**Output format:** report header + per-job at-a-glance markdown table + findings section grouped by job + footer with backend / version / how-to-configure-real-backend pointer. Renders in any GFM-aware viewer (Claude Code chat, Cursor, GitHub, GitLab, Slack with markdown, Discord with markdown).

**Usage:**

```bash
$ pip install silentwatch-mcp
$ silentwatch-mcp-report > today-report.md
$ silentwatch-mcp-report | curl -X POST -d @- https://hooks.slack.com/...
$ SILENTWATCH_BACKEND=crontab silentwatch-mcp-report | gh issue create --title 'cron audit' --body-file -
```

**Sample output:**

```markdown
## silentwatch · silent-failure report

**Window:** last 24 hours · **Backend:** `mock` · **Jobs inspected:** 6

| Job | Status | Silent / total runs (24h) | Last success |
|---|---|---|---|
| **Web Search Refresh** | ⚠ silent | 8 / 24 | 5h ago |
| **Audit Snapshot (production)** | ⚠ overdue 72h | — / 0 | 5d ago |
| ...
```

**No protocol behavior changed.** The MCP server itself is unaffected — this adds a third console-script entry alongside `silentwatch-mcp` (server) and `silentwatch-mcp-demo`. The new `render.py` module exports `render_silent_failure_report(...)` for downstream callers who want to embed the formatter directly.

## [1.0.9] — 2026-05-08

### Added — `silentwatch-mcp-demo` console script (V1 of cross-product UX retrofit)

A new console script that runs against the bundled mock backend's synthetic adversarial data and prints a one-page summary of detected silent failures in ~30 seconds. Intended for the first-30-seconds-after-install moment: operators who just `pip install`ed silentwatch-mcp can run `silentwatch-mcp-demo` and immediately see the detector working on representative inputs (without wiring up Claude Desktop, configuring an MCP client, or pointing at real cron data).

The demo runs `build_silent_failure_report` — the same analysis the MCP server exposes via the `find_silent_failures` tool — against the mock backend's 6 hand-crafted cron jobs. The mock data deliberately includes:

- `web-search-refresh` with 8 silent failures in last 24h (output-empty pattern)
- `audit-snapshot` overdue by 72h (the cron schedule says every-15-minutes, but no successful runs in days)
- `cost-report-generator` last-week silent-fail (empty output despite exit 0)
- 3 healthy jobs as a baseline so output isn't all alarms

Output format: per-job at-a-glance line + aggregate report + CTA pointing at the real backends (`SILENTWATCH_BACKEND=crontab|systemd|openclaw_jsonl`) for production use.

**Usage:**

```
$ pip install silentwatch-mcp
$ silentwatch-mcp-demo
silentwatch-mcp v1.0.9 · synthetic demo
    catches cron silent failures (exit-0+empty-stdout, drift, missed runs)

Inspected 6 synthetic cron jobs across last 24 hours:
  Web Search Refresh                              ⚠ 8 silent failure(s) in 24h
  Audit Snapshot (production)                     ⚠ overdue by 72h
  Cleanup Logs Older Than 30 Days                 ✓ healthy
  ...
```

**No external I/O.** Demo runs against the in-memory mock backend; no network, no API keys, no filesystem access outside the bundled fixtures. Safe to run anywhere, including air-gapped environments.

Adds a second console-script entry (`silentwatch-mcp-demo`) alongside the existing `silentwatch-mcp` (the MCP server entry). `python -m silentwatch_mcp.demo` works equivalently.

## [1.0.8] — 2026-05-08

### Added — first-run startup banner (visibility-after-install fix, V2 of cross-product UX retrofit)

When the server starts via `python -m silentwatch_mcp` or the console script, the first stderr line is now a one-line value-prove receipt:

```
silentwatch-mcp v1.0.8 ready · catches cron silent failures (exit-0+empty-stdout, drift, missed runs) · 7 textbook patterns · backend=mock
```

Before v1.0.8 the server started silently except for a generic `Starting silentwatch-mcp with backend=mock` log line — operators who'd just `pip install`ed the package had no immediate signal of what the server actually does. The banner is the first-30-seconds value moment that was previously missing.

**Suppressible:** set `SILENTWATCH_QUIET=1` (or `true` / `yes`) to skip the banner. Useful when piping stderr to a log file in production deployments.

**No protocol behavior changed.** Banner is stderr-only; stdout (the MCP JSON-RPC channel) is untouched. Pure observability addition.

## [1.0.7] — 2026-05-06

### Implemented — `cron://run/{id}` resource (was a documented-but-broken placeholder since v0.1)

The README has documented `cron://run/{id}` as a "individual run instance with full output" resource since v0.1, but the shipped handler returned a placeholder error: `{"error": "cron://run/{id} not yet implemented (v0.2 target)"}`. Real-input adversarial validation against v1.0.6 surfaced this as a "documented but broken" gap — buyers reading the README would believe the resource works and hit the placeholder error.

v1.0.7 implements the resource properly:

- Added `CronBackend.get_run_by_id(run_id) -> CronRun | None` as a default method on the abstract base. The default implementation scans every job's recent-run window (limit=200) for a matching run_id. Backends with a more efficient lookup path (e.g., a flat run-log file or an indexed store) can override.
- Updated the `read_resource` handler for `cron://run/{id}` to call `backend.get_run_by_id` and return either the run record or a clear error (unknown id, empty id, etc.).
- Response shape: `{"run": <CronRun model>, "uri": "cron://run/<id>"}` for success; `{"error": "..."}` for the various error cases.

The default implementation is **O(jobs × runs_per_job)** for a single lookup — fine for the typical scale of cron jobs in a single deployment (tens of jobs, hundreds of recent runs). For larger deployments, override `get_run_by_id` on your backend.

**+2 tests:**
- `test_read_resource_run_returns_real_run_v107` — looks up a real run_id from `get_job_runs` and verifies the per-run resource returns the matching run record
- `test_read_resource_run_unknown_id_returns_error` — verifies the error path
- `test_read_resource_run_empty_id_returns_error` — verifies edge case for the trailing-slash form

(Existing v0.2-target placeholder test removed since the placeholder is now real implementation.)

**Validation:** documented-but-broken gap closed. Buyer reading the README + invoking `cron://run/{id}` now gets the documented behavior.

**Coverage:** 91 → 93 tests. ruff + mypy clean (the 23 mypy "untyped-decorator" errors are pre-existing baseline from MCP framework's untyped decorators, unchanged from v1.0.6).

## [1.0.6] — 2026-05-06

### Fixed — `read_resource` AnyUrl coercion (real production bug)
- `read_resource(uri)` previously called `uri.startswith("cron://job/")` and `uri.startswith("cron://run/")` directly on the parameter. The MCP framework deserializes resource URIs as `pydantic.AnyUrl` instances, which do not expose a `.startswith()` method — production callers requesting per-job (`cron://job/{id}`) or per-run (`cron://run/{run_id}`) resources would have hit `AttributeError: 'AnyUrl' object has no attribute 'startswith'`. Fixed by coercing the parameter to `str(uri)` once at the top of the handler before any string predicates. The list-resource path (`cron://jobs`) was unaffected because equality with `==` on `AnyUrl` does the right thing.
- Discovered while raising server.py coverage from 36% to 100% (server-protocol coverage tests added at the same time, +17 tests, total 91). The bug was previously masked by tests that called the registered handler with already-stringified URIs rather than reproducing the protocol-layer wrapping.
- Commit: [`2622fb5`](https://github.com/temurkhan13/silentwatch-mcp/commit/2622fb5) (landed on main 2026-05-06; this patch ships it to PyPI + the MCP Registry so anyone who installs `silentwatch-mcp` from PyPI no longer gets the buggy resource handler).

## [1.0.5] — 2026-05-05

### Changed — cross-link mesh extension to 6th MCP
- README "Related" section updated to reference [openclaw-output-vetter-mcp](https://github.com/temurkhan13/openclaw-output-vetter-mcp) (v1.0.1, shipped 2026-05-04). Bundle reference updated to "5 others" (was 4) since the bundle is now a 6-pack. Cost-tracker description annotated with v1.1+ (quota-window awareness); upgrade-orchestrator with v1.2+ (provider-side regression detection). Pure metadata refresh — no code changes. PyPI republish so the new Related list lands in the "Project description" rendered on PyPI.

## [1.0.4] — 2026-05-04

### Changed — README v2 metadata refresh (PyPI republish)
- README repositioned with universal-first lede + concrete failure-mode citations from r/ClaudeAI sweep (commits `a0a4253` + `fdc400b`). Originally landed in repo on 2026-05-04; this patch bump republishes to PyPI so the new description + keyword surface area becomes searchable for buyers via PyPI search rank. No code changes — pure metadata + README refresh.
- Citations added to README "What it does": GitHub Issues #54260 (28-day silent routine failure) + #1243 (sonnet-4-6 empty-retry loop) + dev.to silent-failure-patterns article. Buyer-vocabulary keyword expansion to match the actual viral pain stories of the last 30 days.
- pyproject.toml description tightened toward universal AI-agent positioning; OpenClaw is now framed as one supported backend rather than the sole audience.

## [1.0.3] — 2026-05-03

### Fixed
- CI lint regression: ruff's UP042 rule (introduced after v1.0.0 ship) flagged `class RunStatus(str, Enum)` and `class SilentFailIndicator(str, Enum)` as deprecated since Python 3.11+ provides `enum.StrEnum`. Switched both classes to inherit from `StrEnum` and updated the import. No behavior change — `StrEnum` is the modern idiom for the same `str`+`Enum` pattern.

## [1.0.2] — 2026-05-03

### Changed
- Author contact email switched from `admin@pixelette.tech` (shared inbox) to `temur@pixelette.tech` (personal alias). Affects: PyPI package metadata `authors` field, README "Need this adapted to your stack?" Custom MCP Build CTA, README "Production AI audits" CTA, SPEC.md lineage section. No code changes.

## [1.0.1] — 2026-05-02

### Added
- `mcp-name:` verification line in README enabling MCP Registry publish (registry validates PyPI package ownership via this README marker)

### Listed
- Official Model Context Protocol Registry: https://registry.modelcontextprotocol.io
- Discoverable via Glama, PulseMCP, and other MCP directories that ingest from the official registry

## [1.0.0] — 2026-05-02

### Added
- **GitHub Actions CI** — matrix testing on ubuntu/macos/windows × Python 3.11/3.12, separate ruff + mypy lint job, sdist+wheel build artifact upload, concurrency cancel-in-progress on same branch
- **GitHub Actions release workflow** — fires on `v*` tag push, verifies tag matches `pyproject.toml` version, builds + publishes to PyPI via Trusted Publishing
- **`server.json`** for the official Model Context Protocol Registry submission
- **PyPI distribution** — `pip install silentwatch-mcp` works for everyone

### Changed
- Bumped ruff `line-length` from 100 to 120 (mock data + sample fixtures naturally produce wider lines)
- Removed unused `now` variable in `test_naive_datetime_input_treated_as_utc`
- README, SPEC.md status badges updated to v1.0

### v1.0 ship summary
All four backends production-ready (mock + OpenClaw JSONL + crontab + systemd), 74 tests passing across 6 OS × Python combinations, MIT licensed, free + open source. Ready for production use against any cron or scheduled-job source.

## [0.3.0] — 2026-05-02

### Added
- **`CrontabBackend`** — parses `/etc/crontab` + `/etc/cron.d/*` + per-user crontabs (`crontab -l`); supports both 5-field cron expressions and `@hourly`/`@daily`/`@yearly` shortcuts. Last-run inferred from `/var/log/syslog` or `/var/log/cron` (configurable via `SILENTWATCH_SYSLOG`).
- **`SystemdBackend`** — parses `systemctl list-timers --all --output=json` to enumerate timer units; uses `systemctl show <unit> --property=TimersCalendar` to lift `OnCalendar=` into the schedule field; `journalctl -u <service>` for run history with `EXIT_STATUS` extraction.
- **`compute_overdue_state()`** in `analysis.py` — backend-agnostic overdue detection using `croniter`. Returns `(is_overdue, overdue_by_minutes, next_expected_run_at)`. Handles edge cases: empty/unknown schedule, invalid cron expression, no last-run timestamp (falls back to "yesterday" base), grace-minute tolerance window.
- **35 new tests** (74 total, was 39): 10 in `test_overdue.py`, 12 in `test_backend_crontab.py`, 13 in `test_backend_systemd.py`. Backend tests use mocked `subprocess` calls so they pass on Windows.
- **`croniter>=6.0.0` dependency** added.

### Changed
- `OpenClawJsonlBackend` now uses `compute_overdue_state` instead of hardcoding `is_overdue=False`. Existing JSONL data now produces real overdue/next-run fields.
- README backend selection section now lists all 4 backends with descriptions of when each is best.
- SPEC.md backend selection table marks all 4 backends as shipped.

## [0.2.0] — 2026-05-02

### Added
- **`OpenClawJsonlBackend`** — parses OpenClaw native cron run JSONL files. Replaces the v0.1 `NotImplementedError` stubs. Robust handling: malformed JSON lines skipped with warning + parse continues; records missing required fields skipped; ISO-8601 timestamps with `Z` suffix tolerated; output snippet capped at 500 chars (stdout preferred, falls back to stderr); top-level `schedule` field lifted into metadata.
- Two-pass parsing: parse all runs first, then enrich with silent-fail detection so each run has the others as historical context for length/duration anomaly rules.
- 18 new tests covering missing dir/file, parsing edge cases, malformed line handling, multi-job multi-file, runs_24h aggregation, ISO Z-suffix tolerance.

### Changed
- Status badges in README updated to show 39 tests passing.

## [0.1.0] — 2026-05-02

### Added
- Initial scaffold with MCP protocol wiring.
- 6 tools: `list_jobs`, `get_job_status`, `get_job_runs`, `find_overdue_jobs`, `find_silent_failures`, `tail_job_logs`.
- 2 resources: `cron://jobs`, `cron://job/{id}`.
- 2 prompts: `diagnose-overdue`, `summarize-cron-health`.
- `MockBackend` with 6 sample jobs (including silent failures + overdue cases) for protocol-wiring verification.
- `OpenClawJsonlBackend` stub (raises `NotImplementedError`, v0.2 target).
- `CronBackend` ABC + backend registry pattern for adding new schedulers.
- 5 silent-fail detection rules: empty output, length anomaly vs historical median, error keywords in stdout, duration anomaly (short), expected pattern missing.
- Pure-function `analysis` module (no I/O, easy to test).
- 21 tests covering mock backend contract, analysis rules, server construction.
- `pyproject.toml` with hatchling build, MIT license, examples directory.
- README with positioning + Custom MCP Build CTA + AI Production Audit cross-link.
- SPEC.md with full server design.

[Unreleased]: https://github.com/temurkhan13/silentwatch-mcp/compare/v1.0.7...HEAD
[1.0.7]: https://github.com/temurkhan13/silentwatch-mcp/compare/v1.0.6...v1.0.7
[1.0.6]: https://github.com/temurkhan13/silentwatch-mcp/compare/v1.0.5...v1.0.6
[1.0.5]: https://github.com/temurkhan13/silentwatch-mcp/compare/v1.0.4...v1.0.5
[1.0.4]: https://github.com/temurkhan13/silentwatch-mcp/compare/v1.0.3...v1.0.4
[1.0.3]: https://github.com/temurkhan13/silentwatch-mcp/compare/v1.0.2...v1.0.3
[1.0.2]: https://github.com/temurkhan13/silentwatch-mcp/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/temurkhan13/silentwatch-mcp/compare/v1.0.0...v1.0.1
[1.0.0]: https://github.com/temurkhan13/silentwatch-mcp/compare/v0.3.0...v1.0.0
[0.3.0]: https://github.com/temurkhan13/silentwatch-mcp/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/temurkhan13/silentwatch-mcp/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/temurkhan13/silentwatch-mcp/releases/tag/v0.1.0

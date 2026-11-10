"""Synthetic demo — `silentwatch-mcp-demo` console script.

Run ``silentwatch-mcp-demo`` after ``pip install silentwatch-mcp`` to see the
detector catch real silent-failure patterns in 30 seconds, against the bundled
mock backend's hand-crafted adversarial inputs.

The mock backend includes 6 cron jobs that exhibit each textbook failure mode
silentwatch is designed to catch:

- ``web-search-refresh`` — 8 of 24 runs in last 24h are exit-0 with empty stdout
  (output-empty silent failure)
- ``audit-snapshot`` — last successful run was 5 days ago; the cron schedule
  expects every-15-minutes; overdue by 72 hours
- ``cost-report-generator`` — last weekly run silent-failed (empty output)
- 3 healthy jobs — clean baseline so the demo isn't all alarms

The demo runs the same ``build_silent_failure_report`` analysis the MCP server
exposes via the ``find_silent_failures`` tool, then prints a one-page summary.

This is observability-only — no protocol behavior, no I/O outside the in-memory
mock, no API keys. ``silentwatch-mcp-demo`` is safe to run anywhere.
"""
from __future__ import annotations

import asyncio
import sys

from silentwatch_mcp import __version__
from silentwatch_mcp.analysis import build_silent_failure_report
from silentwatch_mcp.backends.mock import MockBackend


# ANSI color codes — only used if stderr is a TTY (not piped to a log).
def _is_tty() -> bool:
    try:
        return sys.stderr.isatty()
    except Exception:
        return False


_USE_COLOR = _is_tty()


def _c(code: str, s: str) -> str:
    if not _USE_COLOR:
        return s
    return f"\033[{code}m{s}\033[0m"


def _bold(s: str) -> str: return _c("1", s)
def _red(s: str) -> str: return _c("31", s)
def _yellow(s: str) -> str: return _c("33", s)
def _green(s: str) -> str: return _c("32", s)
def _dim(s: str) -> str: return _c("2", s)


async def _run_demo() -> int:
    print(file=sys.stderr)
    print(_bold(f"silentwatch-mcp v{__version__} · synthetic demo"), file=sys.stderr)
    print(_dim("    catches cron silent failures (exit-0+empty-stdout, drift, missed runs)"), file=sys.stderr)
    print(file=sys.stderr)

    backend = MockBackend()
    jobs = await backend.list_jobs()
    runs_by_job = {job.id: await backend.get_job_runs(job.id, limit=200) for job in jobs}

    print(_dim(f"Inspected {len(jobs)} synthetic cron jobs across last 24 hours:"), file=sys.stderr)
    print(file=sys.stderr)

    # Per-job at-a-glance line, sorted: silent failures first, then overdue, then healthy
    sorted_jobs = sorted(
        jobs,
        key=lambda j: (
            -1 * j.silent_fail_count_24h,  # most silent failures first
            -1 * (j.overdue_by_minutes or 0),  # then most overdue
            j.id,
        ),
    )
    for job in sorted_jobs:
        if job.silent_fail_count_24h > 0:
            tag = _red(f"  ⚠ {job.silent_fail_count_24h} silent failure(s) in 24h")
        elif job.is_overdue and job.overdue_by_minutes:
            hours = job.overdue_by_minutes // 60
            tag = _yellow(f"  ⚠ overdue by {hours}h (last success: {job.last_success_at.strftime('%Y-%m-%d') if job.last_success_at else 'unknown'})")
        else:
            tag = _green("  ✓ healthy")
        print(f"  {_bold(job.name):<60s} {tag}", file=sys.stderr)

    # Aggregate report
    print(file=sys.stderr)
    print(_dim("Running build_silent_failure_report (the same analysis the MCP server exposes via find_silent_failures):"), file=sys.stderr)
    print(file=sys.stderr)

    report = build_silent_failure_report(jobs, runs_by_job, window_hours=24)

    if not report.jobs_flagged:
        print(_green(f"  ✓ All {report.total_jobs_checked} jobs healthy in last 24h."), file=sys.stderr)
        return 0

    total_silent = sum(f.silent_fail_count for f in report.jobs_flagged)
    print(_red(f"  Detected {total_silent} silent failure(s) across {len(report.jobs_flagged)} job(s):"), file=sys.stderr)
    print(file=sys.stderr)

    for flag in report.jobs_flagged:
        rate_pct = int(flag.silent_fail_rate * 100)
        print(_bold(f"  • {flag.job_name}"), file=sys.stderr)
        print(
            f"    {flag.silent_fail_count}/{flag.total_runs} runs silent-failed "
            f"({rate_pct}% of last-24h runs)",
            file=sys.stderr,
        )
        indicators_str = ", ".join(i.value for i in flag.indicators)
        print(f"    indicators: {_yellow(indicators_str)}", file=sys.stderr)
        sample = ", ".join(flag.sample_run_ids[:3])
        print(_dim(f"    sample run_ids: {sample}"), file=sys.stderr)
        print(file=sys.stderr)

    print(_dim("→ This is the mock backend's synthetic data. To run silentwatch on YOUR cron jobs:"), file=sys.stderr)
    print(_dim("  1. Configure the MCP server in Claude Code / Cursor / OpenClaw"), file=sys.stderr)
    print(_dim("  2. Set SILENTWATCH_BACKEND=crontab|systemd|openclaw_jsonl"), file=sys.stderr)
    print(_dim("  3. Ask: 'Find silent failures in my cron jobs'"), file=sys.stderr)
    print(file=sys.stderr)
    print(_dim(f"docs: https://github.com/temurkhan13/silentwatch-mcp"), file=sys.stderr)
    return 0


def main() -> None:
    sys.exit(asyncio.run(_run_demo()))


if __name__ == "__main__":
    main()

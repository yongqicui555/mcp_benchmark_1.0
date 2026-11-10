"""Mock backend — returns realistic sample data for protocol-wiring verification.

Default backend for development. Lets users verify their MCP client connection
to the server (Claude Desktop config, tool registration, response parsing) before
plugging in a real cron data source.

Sample data deliberately includes silent-failure cases so `find_silent_failures`
returns meaningful results out of the box.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from silentwatch_mcp.backends.base import CronBackend
from silentwatch_mcp.types import (
    CronJob,
    CronRun,
    RunStatus,
    SilentFailIndicator,
)


def _now() -> datetime:
    return datetime.now(UTC)


def _ago(**kwargs: int) -> datetime:
    return _now() - timedelta(**kwargs)


class MockBackend(CronBackend):
    """In-memory backend with hand-crafted sample data."""

    name = "mock"

    def __init__(self) -> None:
        self._jobs: dict[str, CronJob] = {
            "web-search-refresh": CronJob(
                id="web-search-refresh",
                name="Web Search Refresh",
                schedule="0 */1 * * *",
                last_run_at=_ago(minutes=23),
                last_run_status=RunStatus.SILENT_FAILURE,
                last_success_at=_ago(hours=5),
                runs_24h=24,
                successes_24h=16,
                silent_fail_count_24h=8,
                is_overdue=False,
                next_expected_run_at=_ago(minutes=-37),
            ),
            "daily-summary": CronJob(
                id="daily-summary",
                name="Daily Summary Email",
                schedule="0 9 * * *",
                last_run_at=_ago(hours=11),
                last_run_status=RunStatus.SUCCESS,
                last_success_at=_ago(hours=11),
                runs_24h=1,
                successes_24h=1,
                silent_fail_count_24h=0,
                is_overdue=False,
                next_expected_run_at=_ago(hours=-13),
            ),
            "audit-snapshot": CronJob(
                id="audit-snapshot",
                name="Audit Snapshot (production)",
                schedule="*/15 * * * *",
                last_run_at=_ago(hours=72),
                last_run_status=RunStatus.FAILURE,
                last_success_at=_ago(days=5),
                runs_24h=0,
                successes_24h=0,
                silent_fail_count_24h=0,
                is_overdue=True,
                overdue_by_minutes=4320,  # 72h
                next_expected_run_at=_ago(minutes=72 * 60 - 15),
            ),
            "skill-registry-check": CronJob(
                id="skill-registry-check",
                name="Skill Registry Integrity Check",
                schedule="0 0 * * *",
                last_run_at=_ago(hours=11),
                last_run_status=RunStatus.SUCCESS,
                last_success_at=_ago(hours=11),
                runs_24h=1,
                successes_24h=1,
                silent_fail_count_24h=0,
                is_overdue=False,
                next_expected_run_at=_ago(hours=-13),
            ),
            "cleanup-old-logs": CronJob(
                id="cleanup-old-logs",
                name="Cleanup Logs Older Than 30 Days",
                schedule="30 3 * * 0",
                last_run_at=_ago(days=2),
                last_run_status=RunStatus.SUCCESS,
                last_success_at=_ago(days=2),
                runs_24h=0,
                successes_24h=0,
                silent_fail_count_24h=0,
                is_overdue=False,
                next_expected_run_at=_ago(days=-5),
            ),
            "cost-report-generator": CronJob(
                id="cost-report-generator",
                name="Per-Agent Cost Report",
                schedule="0 8 * * 1",
                last_run_at=_ago(days=1),
                last_run_status=RunStatus.SILENT_FAILURE,
                last_success_at=_ago(days=8),
                runs_24h=0,
                successes_24h=0,
                silent_fail_count_24h=0,
                is_overdue=False,
                next_expected_run_at=_ago(days=-6),
            ),
        }

        self._runs: dict[str, list[CronRun]] = {
            "web-search-refresh": self._build_web_search_runs(),
            "daily-summary": self._build_simple_success_runs("daily-summary", "Daily Summary Email", count=14),
            "audit-snapshot": self._build_audit_failure_runs(),
            "skill-registry-check": self._build_simple_success_runs(
                "skill-registry-check", "Skill Registry Integrity Check", count=14
            ),
            "cleanup-old-logs": self._build_simple_success_runs(
                "cleanup-old-logs", "Cleanup Logs Older Than 30 Days", count=4
            ),
            "cost-report-generator": self._build_cost_report_runs(),
        }

    async def list_jobs(self) -> list[CronJob]:
        return list(self._jobs.values())

    async def get_job_runs(self, job_id: str, limit: int = 100) -> list[CronRun]:
        runs = self._runs.get(job_id, [])
        return runs[:limit]

    async def tail_logs(self, job_id: str, lines: int = 50) -> list[str]:
        runs = self._runs.get(job_id, [])
        out: list[str] = []
        for run in runs:
            ts = run.started_at.isoformat()
            status = run.status.value
            out.append(f"{ts} [{status.upper()}] run_id={run.run_id} exit={run.exit_code}")
            if run.output_snippet:
                out.append(f"{ts} [OUTPUT] {run.output_snippet[:200]}")
        return out[-lines:]

    # --- sample-run builders ---

    def _build_web_search_runs(self) -> list[CronRun]:
        """24 runs over last 24h, every hour. 8 silent-failures (empty output)."""
        runs: list[CronRun] = []
        for i in range(24):
            started = _ago(minutes=23 + i * 60)
            is_silent = i in {0, 2, 5, 7, 11, 14, 18, 22}
            runs.append(
                CronRun(
                    run_id=f"web-search-{started.strftime('%Y%m%d%H%M')}",
                    job_id="web-search-refresh",
                    job_name="Web Search Refresh",
                    started_at=started,
                    completed_at=started + timedelta(seconds=4),
                    duration_ms=4823 if not is_silent else 412,
                    exit_code=0,
                    status=RunStatus.SILENT_FAILURE if is_silent else RunStatus.SUCCESS,
                    silent_fail_indicators=(
                        [SilentFailIndicator.OUTPUT_EMPTY, SilentFailIndicator.DURATION_ANOMALY_SHORT]
                        if is_silent
                        else []
                    ),
                    output_snippet="" if is_silent else "Refreshed 1283 entries; 14 new, 23 expired removed.",
                )
            )
        return runs

    def _build_audit_failure_runs(self) -> list[CronRun]:
        """No runs in last 24h (job stopped), but historical runs exist 5+ days back."""
        runs: list[CronRun] = []
        for i in range(20):
            started = _ago(days=5, hours=i * 6)
            runs.append(
                CronRun(
                    run_id=f"audit-{started.strftime('%Y%m%d%H%M')}",
                    job_id="audit-snapshot",
                    job_name="Audit Snapshot (production)",
                    started_at=started,
                    completed_at=started + timedelta(seconds=12),
                    duration_ms=12_300,
                    exit_code=0,
                    status=RunStatus.SUCCESS,
                    silent_fail_indicators=[],
                    output_snippet="Snapshot written: 47 incidents, 8 audit findings, 2 hygiene exceptions.",
                )
            )
        return runs

    def _build_simple_success_runs(self, job_id: str, job_name: str, count: int) -> list[CronRun]:
        runs: list[CronRun] = []
        for i in range(count):
            started = _ago(hours=11 + i * 24)
            runs.append(
                CronRun(
                    run_id=f"{job_id}-{started.strftime('%Y%m%d%H%M')}",
                    job_id=job_id,
                    job_name=job_name,
                    started_at=started,
                    completed_at=started + timedelta(seconds=8),
                    duration_ms=8_412,
                    exit_code=0,
                    status=RunStatus.SUCCESS,
                    silent_fail_indicators=[],
                    output_snippet=f"Completed {job_name} successfully.",
                )
            )
        return runs

    def _build_cost_report_runs(self) -> list[CronRun]:
        """Weekly job. Last run silent-failed (empty output despite exit 0)."""
        runs: list[CronRun] = []
        runs.append(
            CronRun(
                run_id=f"cost-{_ago(days=1).strftime('%Y%m%d%H%M')}",
                job_id="cost-report-generator",
                job_name="Per-Agent Cost Report",
                started_at=_ago(days=1),
                completed_at=_ago(days=1) + timedelta(seconds=2),
                duration_ms=1_823,
                exit_code=0,
                status=RunStatus.SILENT_FAILURE,
                silent_fail_indicators=[SilentFailIndicator.OUTPUT_EMPTY],
                output_snippet="",
            )
        )
        for i in range(1, 8):
            started = _ago(days=1 + i * 7)
            runs.append(
                CronRun(
                    run_id=f"cost-{started.strftime('%Y%m%d%H%M')}",
                    job_id="cost-report-generator",
                    job_name="Per-Agent Cost Report",
                    started_at=started,
                    completed_at=started + timedelta(seconds=18),
                    duration_ms=18_300,
                    exit_code=0,
                    status=RunStatus.SUCCESS,
                    silent_fail_indicators=[],
                    output_snippet="Cost report: $42.18 across 6 agents this week.",
                )
            )
        return runs

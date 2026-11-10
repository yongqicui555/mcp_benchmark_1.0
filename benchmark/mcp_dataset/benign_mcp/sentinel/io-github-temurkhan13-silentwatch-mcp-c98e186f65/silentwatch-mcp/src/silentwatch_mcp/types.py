"""Shared types used across the server and backends.

These are the canonical response shapes for every tool. Backends produce these;
the server serializes them to MCP `TextContent` blocks.
"""
from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class RunStatus(StrEnum):
    """Outcome classification for a single cron run."""

    SUCCESS = "success"
    FAILURE = "failure"
    SILENT_FAILURE = "silent_failure"
    """Exit code 0 but output flagged by silent-fail detection rules."""
    RUNNING = "running"
    """Job is currently executing."""
    UNKNOWN = "unknown"


class SilentFailIndicator(StrEnum):
    """Specific silent-failure detection rules. See SPEC.md § Silent-failure detection."""

    OUTPUT_EMPTY = "output_empty"
    OUTPUT_LENGTH_ANOMALY = "output_length_anomaly"
    ERROR_KEYWORDS_IN_STDOUT = "error_keywords_in_stdout"
    EXPECTED_PATTERN_MISSING = "expected_pattern_missing"
    DURATION_ANOMALY_SHORT = "duration_anomaly_short"
    DURATION_ANOMALY_LONG = "duration_anomaly_long"


class CronRun(BaseModel):
    """A single cron job run instance."""

    model_config = ConfigDict(frozen=True)

    run_id: str
    job_id: str
    job_name: str | None = None
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    exit_code: int | None = None
    status: RunStatus = RunStatus.UNKNOWN
    silent_fail_indicators: list[SilentFailIndicator] = Field(default_factory=list)
    output_snippet: str = ""
    """First ~500 chars of stdout, redacted for sensitive content."""
    metadata: dict[str, str] = Field(default_factory=dict)


class CronJob(BaseModel):
    """A scheduled cron job with summary state."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    schedule: str
    """Cron expression or schedule descriptor (e.g., '0 */1 * * *' or 'every 1h')."""
    last_run_at: datetime | None = None
    last_run_status: RunStatus | None = None
    last_success_at: datetime | None = None
    runs_24h: int = 0
    successes_24h: int = 0
    silent_fail_count_24h: int = 0
    is_overdue: bool = False
    overdue_by_minutes: int | None = None
    next_expected_run_at: datetime | None = None
    metadata: dict[str, str] = Field(default_factory=dict)


class JobStatus(BaseModel):
    """Detailed status for one job — superset of CronJob with rate calculations."""

    model_config = ConfigDict(frozen=True)

    id: str
    name: str
    schedule: str
    last_run_at: datetime | None = None
    last_run_status: RunStatus | None = None
    last_run_duration_ms: int | None = None
    last_success_at: datetime | None = None
    success_rate_24h: float = 0.0
    success_rate_7d: float = 0.0
    is_overdue: bool = False
    overdue_by_minutes: int | None = None
    next_expected_run_at: datetime | None = None
    silent_fail_indicators: list[SilentFailIndicator] = Field(default_factory=list)
    """Indicators present in the last_run, if it was a silent failure."""


class JobListResponse(BaseModel):
    """Response for `list_jobs` and `find_overdue_jobs`."""

    jobs: list[CronJob]
    total: int


class JobRunsResponse(BaseModel):
    """Response for `get_job_runs`."""

    job_id: str
    runs: list[CronRun]
    total: int


class SilentFailureFlag(BaseModel):
    """One entry in a SilentFailureReport — a single job's silent-fail summary."""

    model_config = ConfigDict(frozen=True)

    job_id: str
    job_name: str
    silent_fail_count: int
    total_runs: int
    silent_fail_rate: float
    indicators: list[SilentFailIndicator]
    """Indicators that fired across the flagged runs (deduplicated)."""
    sample_run_ids: list[str]
    """Up to 5 representative run IDs the caller can fetch via `cron://run/{id}`."""


class SilentFailureReport(BaseModel):
    """Response for `find_silent_failures`."""

    window_hours: int
    jobs_flagged: list[SilentFailureFlag]
    total_jobs_checked: int


class JobLogTail(BaseModel):
    """Response for `tail_job_logs`."""

    job_id: str
    lines: list[str]
    total_lines_returned: int

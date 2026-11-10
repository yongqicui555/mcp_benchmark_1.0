"""Backend-agnostic analysis: silent-fail detection, overdue detection, rate calcs.

Backends produce raw CronRun + CronJob records. This module computes:
    - silent-fail indicators on a run
    - success rates over a window
    - overdue detection from a CronJob's schedule (via croniter)
    - aggregated SilentFailureReport across many jobs

All functions are pure given input data; no I/O.
"""
from __future__ import annotations

import logging
import re
from datetime import UTC, datetime, timedelta
from statistics import median

from croniter import croniter
from croniter.croniter import CroniterBadCronError

from silentwatch_mcp.types import (
    CronJob,
    CronRun,
    JobStatus,
    RunStatus,
    SilentFailIndicator,
    SilentFailureFlag,
    SilentFailureReport,
)

logger = logging.getLogger(__name__)

# Default error keyword patterns. Configurable via SILENTWATCH_ERROR_KEYWORDS env var.
DEFAULT_ERROR_KEYWORDS = re.compile(
    r"\b(ERROR|FAIL(ED|URE)?|Exception|Traceback|Fatal|Panic)\b",
    re.IGNORECASE,
)


def detect_silent_fail_indicators(
    run: CronRun,
    historical_runs: list[CronRun] | None = None,
) -> list[SilentFailIndicator]:
    """Return all silent-fail indicators that fire for this run.

    A run is a silent failure candidate only if exit_code == 0; if exit_code != 0
    it's an explicit failure, not silent.
    """
    if run.exit_code != 0:
        return []

    indicators: list[SilentFailIndicator] = []
    output = run.output_snippet or ""

    # Rule: output empty
    if not output.strip():
        indicators.append(SilentFailIndicator.OUTPUT_EMPTY)

    # Rule: error keywords in stdout despite exit 0
    if DEFAULT_ERROR_KEYWORDS.search(output):
        indicators.append(SilentFailIndicator.ERROR_KEYWORDS_IN_STDOUT)

    # Rule: output length anomaly (vs historical median)
    if historical_runs:
        successful_lengths = [
            len(r.output_snippet) for r in historical_runs
            if r.status == RunStatus.SUCCESS and r.output_snippet
        ]
        if len(successful_lengths) >= 5:
            baseline = median(successful_lengths)
            if baseline > 0 and len(output) < baseline * 0.3:
                indicators.append(SilentFailIndicator.OUTPUT_LENGTH_ANOMALY)

    # Rule: duration anomaly (vs historical median)
    if historical_runs and run.duration_ms is not None:
        successful_durations = [
            r.duration_ms for r in historical_runs
            if r.status == RunStatus.SUCCESS and r.duration_ms is not None
        ]
        if len(successful_durations) >= 5:
            baseline_ms = median(successful_durations)
            if run.duration_ms < baseline_ms * 0.1:
                indicators.append(SilentFailIndicator.DURATION_ANOMALY_SHORT)

    return indicators


def is_silent_failure(run: CronRun) -> bool:
    """Convenience: True if a run was classified as silent failure."""
    return run.status == RunStatus.SILENT_FAILURE or bool(run.silent_fail_indicators)


def compute_success_rate(runs: list[CronRun], window: timedelta) -> float:
    """Fraction of runs within `window` that were SUCCESS (not silent failure, not failure)."""
    cutoff = datetime.now(UTC) - window
    in_window = [r for r in runs if r.started_at >= cutoff]
    if not in_window:
        return 0.0
    successes = sum(1 for r in in_window if r.status == RunStatus.SUCCESS)
    return successes / len(in_window)


def build_job_status(job: CronJob, runs: list[CronRun]) -> JobStatus:
    """Aggregate a CronJob + its run history into a detailed JobStatus."""
    last_run = runs[0] if runs else None
    return JobStatus(
        id=job.id,
        name=job.name,
        schedule=job.schedule,
        last_run_at=job.last_run_at,
        last_run_status=job.last_run_status,
        last_run_duration_ms=last_run.duration_ms if last_run else None,
        last_success_at=job.last_success_at,
        success_rate_24h=compute_success_rate(runs, timedelta(hours=24)),
        success_rate_7d=compute_success_rate(runs, timedelta(days=7)),
        is_overdue=job.is_overdue,
        overdue_by_minutes=job.overdue_by_minutes,
        next_expected_run_at=job.next_expected_run_at,
        silent_fail_indicators=last_run.silent_fail_indicators if last_run else [],
    )


def compute_overdue_state(
    schedule: str,
    last_run_at: datetime | None,
    grace_minutes: int = 5,
    now: datetime | None = None,
) -> tuple[bool, int | None, datetime | None]:
    """Compute overdue state from a cron schedule + last-run timestamp.

    Returns ``(is_overdue, overdue_by_minutes, next_expected_run_at)``.

    - **is_overdue:** True if `next_expected_run_at` is more than `grace_minutes` in the past.
    - **overdue_by_minutes:** integer minutes past expected run time, or None if not overdue.
    - **next_expected_run_at:** the cron-schedule's next firing time after last_run_at
      (or after `now - 1 day` if last_run_at is None — i.e., we don't know when it last ran).

    Returns ``(False, None, None)`` if the schedule string is empty, "unknown", or
    fails to parse — no schedule means we can't reason about overdue state.
    """
    if not schedule or schedule.lower() == "unknown":
        return (False, None, None)

    if now is None:
        now = datetime.now(UTC)

    # Use last_run_at as the base for next-run computation. If we don't know when it
    # last ran, fall back to "yesterday" — better than computing from now (which would
    # always say next-run is in the future, masking missing-run scenarios).
    base = last_run_at if last_run_at is not None else now - timedelta(days=1)

    try:
        iterator = croniter(schedule, base)
        next_run = iterator.get_next(datetime)
    except (CroniterBadCronError, ValueError) as exc:
        logger.warning("Invalid cron schedule %r: %s", schedule, exc)
        return (False, None, None)

    # croniter returns naive datetime by default — coerce to UTC for comparison
    if next_run.tzinfo is None:
        next_run = next_run.replace(tzinfo=UTC)

    grace = timedelta(minutes=grace_minutes)
    if next_run + grace < now:
        overdue_by = int((now - next_run).total_seconds() / 60)
        return (True, overdue_by, next_run)

    return (False, None, next_run)


def build_silent_failure_report(
    jobs: list[CronJob],
    runs_by_job: dict[str, list[CronRun]],
    window_hours: int = 24,
) -> SilentFailureReport:
    """Aggregate silent failures across all jobs within a window."""
    cutoff = datetime.now(UTC) - timedelta(hours=window_hours)
    flagged: list[SilentFailureFlag] = []

    for job in jobs:
        runs = runs_by_job.get(job.id, [])
        in_window = [r for r in runs if r.started_at >= cutoff]
        silent = [r for r in in_window if is_silent_failure(r)]
        if not silent:
            continue

        # Deduplicate indicators across silent runs
        indicators_seen: set[SilentFailIndicator] = set()
        for r in silent:
            indicators_seen.update(r.silent_fail_indicators)

        flagged.append(
            SilentFailureFlag(
                job_id=job.id,
                job_name=job.name,
                silent_fail_count=len(silent),
                total_runs=len(in_window),
                silent_fail_rate=len(silent) / len(in_window) if in_window else 0.0,
                indicators=sorted(indicators_seen, key=lambda i: i.value),
                sample_run_ids=[r.run_id for r in silent[:5]],
            )
        )

    return SilentFailureReport(
        window_hours=window_hours,
        jobs_flagged=flagged,
        total_jobs_checked=len(jobs),
    )

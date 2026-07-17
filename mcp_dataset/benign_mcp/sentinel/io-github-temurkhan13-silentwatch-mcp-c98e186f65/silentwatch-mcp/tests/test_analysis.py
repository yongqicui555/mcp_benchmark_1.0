"""Tests for analysis.py — backend-agnostic detection logic."""
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest

from silentwatch_mcp.analysis import (
    build_silent_failure_report,
    compute_success_rate,
    detect_silent_fail_indicators,
)
from silentwatch_mcp.backends.mock import MockBackend
from silentwatch_mcp.types import (
    CronRun,
    RunStatus,
    SilentFailIndicator,
)


def _make_run(
    *,
    started_at: datetime,
    exit_code: int = 0,
    output: str = "OK",
    duration_ms: int = 1000,
    status: RunStatus = RunStatus.SUCCESS,
) -> CronRun:
    return CronRun(
        run_id=f"r-{started_at.isoformat()}",
        job_id="test-job",
        started_at=started_at,
        completed_at=started_at + timedelta(milliseconds=duration_ms),
        duration_ms=duration_ms,
        exit_code=exit_code,
        status=status,
        output_snippet=output,
    )


def test_silent_fail_empty_output_flagged() -> None:
    run = _make_run(started_at=datetime.now(UTC), exit_code=0, output="")
    indicators = detect_silent_fail_indicators(run)
    assert SilentFailIndicator.OUTPUT_EMPTY in indicators


def test_silent_fail_whitespace_only_output_flagged() -> None:
    run = _make_run(started_at=datetime.now(UTC), exit_code=0, output="   \n  \t ")
    indicators = detect_silent_fail_indicators(run)
    assert SilentFailIndicator.OUTPUT_EMPTY in indicators


def test_silent_fail_error_keyword_in_stdout_flagged() -> None:
    run = _make_run(
        started_at=datetime.now(UTC),
        exit_code=0,
        output="Processing... ERROR: connection timed out (continuing)",
    )
    indicators = detect_silent_fail_indicators(run)
    assert SilentFailIndicator.ERROR_KEYWORDS_IN_STDOUT in indicators


def test_silent_fail_traceback_in_stdout_flagged() -> None:
    run = _make_run(
        started_at=datetime.now(UTC),
        exit_code=0,
        output="Job done.\nTraceback (most recent call last):\n  File ...",
    )
    indicators = detect_silent_fail_indicators(run)
    assert SilentFailIndicator.ERROR_KEYWORDS_IN_STDOUT in indicators


def test_silent_fail_nonzero_exit_returns_empty() -> None:
    """exit_code != 0 means it's an explicit failure, not silent."""
    run = _make_run(started_at=datetime.now(UTC), exit_code=1, output="")
    indicators = detect_silent_fail_indicators(run)
    assert indicators == []


def test_silent_fail_length_anomaly_with_history() -> None:
    """Output much shorter than median historical output flagged."""
    now = datetime.now(UTC)
    historical = [
        _make_run(
            started_at=now - timedelta(hours=i),
            output="A" * 500,  # consistent ~500 char outputs
            status=RunStatus.SUCCESS,
        )
        for i in range(1, 11)
    ]
    short_run = _make_run(started_at=now, output="OK", status=RunStatus.SUCCESS)
    indicators = detect_silent_fail_indicators(short_run, historical_runs=historical)
    assert SilentFailIndicator.OUTPUT_LENGTH_ANOMALY in indicators


def test_silent_fail_duration_anomaly_with_history() -> None:
    """Run that completed much faster than median (suggests immediate-return failure)."""
    now = datetime.now(UTC)
    historical = [
        _make_run(started_at=now - timedelta(hours=i), duration_ms=10_000, status=RunStatus.SUCCESS, output="ok")
        for i in range(1, 11)
    ]
    fast_run = _make_run(started_at=now, duration_ms=200, status=RunStatus.SUCCESS, output="ok")
    indicators = detect_silent_fail_indicators(fast_run, historical_runs=historical)
    assert SilentFailIndicator.DURATION_ANOMALY_SHORT in indicators


def test_compute_success_rate_within_window() -> None:
    now = datetime.now(UTC)
    runs = [
        _make_run(started_at=now - timedelta(hours=i), status=RunStatus.SUCCESS) for i in range(0, 10)
    ] + [
        _make_run(started_at=now - timedelta(hours=i), status=RunStatus.FAILURE) for i in range(10, 14)
    ]
    rate = compute_success_rate(runs, timedelta(hours=24))
    # 10 success + 4 fail = 10/14 ~= 0.714
    assert 0.7 < rate < 0.72


def test_compute_success_rate_no_runs() -> None:
    rate = compute_success_rate([], timedelta(hours=24))
    assert rate == 0.0


@pytest.mark.asyncio
async def test_silent_failure_report_finds_mock_data_failures() -> None:
    """End-to-end: run mock backend through analysis, verify report shape."""
    backend = MockBackend()
    jobs = await backend.list_jobs()
    runs_by_job = {}
    for j in jobs:
        runs_by_job[j.id] = await backend.get_job_runs(j.id, limit=200)

    report = build_silent_failure_report(jobs, runs_by_job, window_hours=24)

    assert report.window_hours == 24
    assert report.total_jobs_checked == len(jobs)
    # web-search-refresh is hardcoded with silent failures in mock data
    flagged_ids = {f.job_id for f in report.jobs_flagged}
    assert "web-search-refresh" in flagged_ids
    web_search_flag = next(f for f in report.jobs_flagged if f.job_id == "web-search-refresh")
    assert web_search_flag.silent_fail_count > 0
    assert web_search_flag.silent_fail_rate > 0
    assert SilentFailIndicator.OUTPUT_EMPTY in web_search_flag.indicators

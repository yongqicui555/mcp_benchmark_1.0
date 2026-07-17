"""Tests for SystemdBackend — parses systemctl list-timers + journalctl output.

Uses subprocess.run mocking so tests pass on Windows where systemd doesn't exist.
"""
from __future__ import annotations

import json
from datetime import UTC, datetime
from unittest.mock import patch

import pytest

from silentwatch_mcp.backends.systemd import SystemdBackend


def _mock_completed_process(stdout: str = "", returncode: int = 0, stderr: str = ""):
    """Build a mock subprocess.CompletedProcess-like object."""
    class Result:
        def __init__(self) -> None:
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = returncode
    return Result()


@pytest.mark.asyncio
async def test_no_systemctl_returns_empty() -> None:
    backend = SystemdBackend()
    with patch("silentwatch_mcp.backends.systemd.shutil.which", return_value=None):
        jobs = await backend.list_jobs()
    assert jobs == []


@pytest.mark.asyncio
async def test_list_timers_returns_jobs() -> None:
    """Parse a synthetic systemctl list-timers JSON output."""
    # systemctl --output=json gives integer microsecond timestamps
    last_run_us = int(datetime(2026, 5, 2, 13, 0, 0, tzinfo=UTC).timestamp() * 1_000_000)
    next_run_us = int(datetime(2026, 5, 2, 14, 0, 0, tzinfo=UTC).timestamp() * 1_000_000)

    timers_json = json.dumps([
        {
            "unit": "audit.timer",
            "activates": "audit.service",
            "next": next_run_us,
            "last": last_run_us,
            "passed": "1h ago",
        },
        {
            "unit": "cleanup.timer",
            "activates": "cleanup.service",
            "next": next_run_us + 86_400_000_000,  # 1 day later
            "last": "n/a",
            "passed": "n/a",
        },
    ])

    backend = SystemdBackend()
    with patch(
        "silentwatch_mcp.backends.systemd.shutil.which",
        return_value="/usr/bin/systemctl",
    ), patch(
        "silentwatch_mcp.backends.systemd.subprocess.run",
    ) as mock_run:
        # First call: list-timers (returns the JSON above)
        # Subsequent calls: systemctl show <unit> for OnCalendar lookup (return empty)
        mock_run.side_effect = [
            _mock_completed_process(stdout=timers_json),
            _mock_completed_process(stdout="TimersCalendar={ }\n"),
            _mock_completed_process(stdout="TimersCalendar={ }\n"),
        ]
        jobs = await backend.list_jobs()

    assert len(jobs) == 2
    audit = next(j for j in jobs if "audit" in j.id)
    assert audit.id == "systemd-audit.timer"
    assert audit.last_run_at == datetime(2026, 5, 2, 13, 0, 0, tzinfo=UTC)
    assert audit.metadata["unit"] == "audit.timer"
    assert audit.metadata["activates"] == "audit.service"


@pytest.mark.asyncio
async def test_oncalendar_lifted_into_schedule() -> None:
    """When systemctl show reports OnCalendar=, that becomes the job's schedule."""
    timers_json = json.dumps([
        {
            "unit": "backup.timer",
            "activates": "backup.service",
            "next": int(datetime(2026, 5, 3, 0, 0, 0, tzinfo=UTC).timestamp() * 1_000_000),
            "last": int(datetime(2026, 5, 2, 0, 0, 0, tzinfo=UTC).timestamp() * 1_000_000),
            "passed": "1d ago",
        },
    ])
    show_output = "TimersCalendar={ OnCalendar=*-*-* 00:00:00 ; next=Sat 2026-05-03 00:00:00 UTC ; }"

    backend = SystemdBackend()
    with patch(
        "silentwatch_mcp.backends.systemd.shutil.which",
        return_value="/usr/bin/systemctl",
    ), patch(
        "silentwatch_mcp.backends.systemd.subprocess.run",
    ) as mock_run:
        mock_run.side_effect = [
            _mock_completed_process(stdout=timers_json),
            _mock_completed_process(stdout=show_output),
        ]
        jobs = await backend.list_jobs()

    assert len(jobs) == 1
    # The schedule extracted from OnCalendar isn't a cron expression but the raw systemd format
    assert "*-*-*" in jobs[0].schedule


@pytest.mark.asyncio
async def test_missing_unit_field_skipped() -> None:
    """Records without a 'unit' key are skipped silently."""
    timers_json = json.dumps([
        {"activates": "orphan.service", "next": "n/a", "last": "n/a"},
        {
            "unit": "good.timer",
            "activates": "good.service",
            "next": int(datetime(2026, 5, 2, 14, 0, 0, tzinfo=UTC).timestamp() * 1_000_000),
            "last": "n/a",
        },
    ])

    backend = SystemdBackend()
    with patch(
        "silentwatch_mcp.backends.systemd.shutil.which",
        return_value="/usr/bin/systemctl",
    ), patch(
        "silentwatch_mcp.backends.systemd.subprocess.run",
    ) as mock_run:
        mock_run.side_effect = [
            _mock_completed_process(stdout=timers_json),
            _mock_completed_process(stdout="TimersCalendar={ }\n"),
        ]
        jobs = await backend.list_jobs()

    assert len(jobs) == 1
    assert jobs[0].id == "systemd-good.timer"


@pytest.mark.asyncio
async def test_get_job_runs_parses_journal() -> None:
    """journalctl --output=json gives one JSON object per line."""
    timers_json = json.dumps([
        {
            "unit": "audit.timer",
            "activates": "audit.service",
            "next": int(datetime(2026, 5, 2, 14, 0, 0, tzinfo=UTC).timestamp() * 1_000_000),
            "last": int(datetime(2026, 5, 2, 13, 0, 0, tzinfo=UTC).timestamp() * 1_000_000),
        },
    ])

    journal_json_lines = "\n".join([
        json.dumps({
            "__REALTIME_TIMESTAMP": str(int(datetime(2026, 5, 2, 13, 0, 0, tzinfo=UTC).timestamp() * 1_000_000)),
            "MESSAGE": "Started audit.service",
            "EXIT_STATUS": "0",
        }),
        json.dumps({
            "__REALTIME_TIMESTAMP": str(int(datetime(2026, 5, 2, 12, 0, 0, tzinfo=UTC).timestamp() * 1_000_000)),
            "MESSAGE": "audit.service: Main process exited, code=exited, status=1/FAILURE",
            "EXIT_STATUS": "1",
        }),
    ])

    backend = SystemdBackend()
    with patch(
        "silentwatch_mcp.backends.systemd.shutil.which",
        return_value="/usr/bin/systemctl",
    ), patch(
        "silentwatch_mcp.backends.systemd.subprocess.run",
    ) as mock_run:
        mock_run.side_effect = [
            # list-timers for the lookup inside get_job_runs
            _mock_completed_process(stdout=timers_json),
            # journalctl
            _mock_completed_process(stdout=journal_json_lines),
        ]
        runs = await backend.get_job_runs("systemd-audit.timer", limit=10)

    assert len(runs) == 2
    # Status determined from EXIT_STATUS field
    assert any(r.exit_code == 0 for r in runs)
    assert any(r.exit_code == 1 for r in runs)


def test_extract_oncalendar_from_show_output() -> None:
    output = "TimersCalendar={ OnCalendar=Mon..Fri *-*-* 09:00:00 ; next=Mon 2026-05-04 09:00:00 UTC ; }"
    result = SystemdBackend._extract_oncalendar(output)
    assert result == "Mon..Fri *-*-* 09:00:00"


def test_extract_oncalendar_missing_returns_none() -> None:
    output = "TimersCalendar={ }"
    result = SystemdBackend._extract_oncalendar(output)
    assert result is None


def test_parse_systemctl_time_microsecond_int() -> None:
    """JSON-mode timestamps are integer microseconds since epoch."""
    expected = datetime(2026, 5, 2, 13, 0, 0, tzinfo=UTC)
    us = int(expected.timestamp() * 1_000_000)
    parsed = SystemdBackend._parse_systemctl_time(us)
    assert parsed == expected


def test_parse_systemctl_time_na_returns_none() -> None:
    assert SystemdBackend._parse_systemctl_time("n/a") is None
    assert SystemdBackend._parse_systemctl_time("") is None
    assert SystemdBackend._parse_systemctl_time("-") is None


def test_extract_exit_code_from_journal_field() -> None:
    entry = {"EXIT_STATUS": "0", "MESSAGE": "Started"}
    assert SystemdBackend._extract_exit_code(entry, entry["MESSAGE"]) == 0

    entry = {"EXIT_STATUS": "1", "MESSAGE": "Failed"}
    assert SystemdBackend._extract_exit_code(entry, entry["MESSAGE"]) == 1


def test_extract_exit_code_from_message_heuristic() -> None:
    msg = "audit.service: Main process exited, code=exited, status=1/FAILURE"
    assert SystemdBackend._extract_exit_code({}, msg) == 1


def test_extract_exit_code_returns_none_when_no_signal() -> None:
    msg = "Started audit.service"
    assert SystemdBackend._extract_exit_code({}, msg) is None

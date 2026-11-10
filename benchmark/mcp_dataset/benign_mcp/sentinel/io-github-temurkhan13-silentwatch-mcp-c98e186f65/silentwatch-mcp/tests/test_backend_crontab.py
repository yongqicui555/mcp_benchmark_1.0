"""Tests for CrontabBackend — parses /etc/crontab + user crontabs.

Tests use temp files + mocked subprocess where possible, so they run on Windows
even though crontab is a Unix concept.
"""
from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import patch

import pytest

from silentwatch_mcp.backends.crontab import CrontabBackend


@pytest.mark.asyncio
async def test_no_crontab_files_returns_empty(tmp_path: Path) -> None:
    """If no crontab paths exist, list_jobs returns empty without error."""
    backend = CrontabBackend(crontab_paths=[tmp_path / "missing-crontab"])
    # Patch shutil.which to simulate `crontab` not on PATH
    with patch("silentwatch_mcp.backends.crontab.shutil.which", return_value=None):
        jobs = await backend.list_jobs()
    assert jobs == []


@pytest.mark.asyncio
async def test_parses_system_crontab_with_user_field(tmp_path: Path) -> None:
    """/etc/crontab format has a user field between schedule and command."""
    crontab_file = tmp_path / "crontab"
    crontab_file.write_text(
        "# system crontab\n"
        "PATH=/usr/bin:/bin\n"
        "0 * * * * root /usr/bin/check-health.sh\n"
        "*/15 * * * * www-data /usr/bin/refresh-cache --quiet\n"
        "@daily backup /usr/local/bin/backup.sh\n"
        "\n"
        "# comment line\n"
    )

    backend = CrontabBackend(
        crontab_paths=[crontab_file],
        users=[],
        syslog_path=tmp_path / "no-syslog",
    )
    with patch("silentwatch_mcp.backends.crontab.shutil.which", return_value=None):
        jobs = await backend.list_jobs()

    assert len(jobs) == 3
    schedules = {j.schedule for j in jobs}
    assert "0 * * * *" in schedules
    assert "*/15 * * * *" in schedules
    assert "@daily" in schedules

    # Each job should have a stable derived id
    ids = {j.id for j in jobs}
    assert all(jid.startswith("crontab-") for jid in ids)
    assert len(ids) == 3  # ids are unique


@pytest.mark.asyncio
async def test_parses_user_crontab_no_user_field(tmp_path: Path) -> None:
    """User crontab (from `crontab -l`) has no user column."""
    backend = CrontabBackend(
        crontab_paths=[],
        users=[],
        syslog_path=tmp_path / "no-syslog",
    )
    user_crontab = (
        "# my crontab\n"
        "MAILTO=admin@example.com\n"
        "0 9 * * * /home/user/morning-script.sh\n"
        "@hourly /home/user/sync.sh\n"
    )
    with patch.object(backend, "_run_crontab_l", return_value=user_crontab), \
         patch("silentwatch_mcp.backends.crontab.shutil.which", return_value="/usr/bin/crontab"):
        jobs = await backend.list_jobs()

    schedules = {j.schedule for j in jobs}
    assert "0 9 * * *" in schedules
    assert "@hourly" in schedules


@pytest.mark.asyncio
async def test_skips_comments_and_env_vars(tmp_path: Path) -> None:
    crontab_file = tmp_path / "crontab"
    crontab_file.write_text(
        "# this is a comment\n"
        "PATH=/usr/bin\n"
        "MAILTO=ops@example.com\n"
        "SHELL=/bin/bash\n"
        "0 * * * * root /usr/bin/job.sh\n"
    )
    backend = CrontabBackend(
        crontab_paths=[crontab_file],
        users=[],
        syslog_path=tmp_path / "no-syslog",
    )
    with patch("silentwatch_mcp.backends.crontab.shutil.which", return_value=None):
        jobs = await backend.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].schedule == "0 * * * *"


@pytest.mark.asyncio
async def test_overdue_computed_from_schedule(tmp_path: Path) -> None:
    """Without last-run info, an hourly job appears overdue (correct behavior)."""
    crontab_file = tmp_path / "crontab"
    crontab_file.write_text("0 * * * * root /usr/bin/hourly.sh\n")
    backend = CrontabBackend(
        crontab_paths=[crontab_file],
        users=[],
        syslog_path=tmp_path / "no-syslog",  # no last-run info available
    )
    with patch("silentwatch_mcp.backends.crontab.shutil.which", return_value=None):
        jobs = await backend.list_jobs()
    assert len(jobs) == 1
    # No last-run info → falls back to "yesterday" base → next-run is in past → overdue
    assert jobs[0].is_overdue is True
    assert jobs[0].next_expected_run_at is not None


@pytest.mark.asyncio
async def test_last_run_inferred_from_syslog(tmp_path: Path) -> None:
    """If syslog contains a CRON entry referencing the command, last_run_at is set."""
    crontab_file = tmp_path / "crontab"
    crontab_file.write_text("0 * * * * root /usr/bin/hourly.sh\n")

    # Use ISO-format timestamp matching the regex in _parse_syslog_timestamp
    syslog_file = tmp_path / "syslog"
    syslog_file.write_text(
        "2026-05-02T13:00:01.123Z host CRON[12345]: (root) CMD (/usr/bin/hourly.sh)\n"
        "2026-05-02T13:00:02.456Z host other-service: unrelated message\n"
    )
    backend = CrontabBackend(
        crontab_paths=[crontab_file],
        users=[],
        syslog_path=syslog_file,
    )
    with patch("silentwatch_mcp.backends.crontab.shutil.which", return_value=None):
        jobs = await backend.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].last_run_at == datetime(2026, 5, 2, 13, 0, 1, 123000, tzinfo=UTC)


@pytest.mark.asyncio
async def test_get_job_runs_returns_at_most_one_synthetic_run(tmp_path: Path) -> None:
    """Crontab backend has no run history; returns last-run as a single synthetic CronRun."""
    crontab_file = tmp_path / "crontab"
    crontab_file.write_text("0 * * * * root /usr/bin/hourly.sh\n")
    syslog_file = tmp_path / "syslog"
    syslog_file.write_text(
        "2026-05-02T13:00:01Z host CRON[12345]: (root) CMD (/usr/bin/hourly.sh)\n"
    )
    backend = CrontabBackend(
        crontab_paths=[crontab_file],
        users=[],
        syslog_path=syslog_file,
    )
    with patch("silentwatch_mcp.backends.crontab.shutil.which", return_value=None):
        jobs = await backend.list_jobs()
        runs = await backend.get_job_runs(jobs[0].id, limit=10)
    assert len(runs) == 1
    assert runs[0].started_at == datetime(2026, 5, 2, 13, 0, 1, tzinfo=UTC)


@pytest.mark.asyncio
async def test_get_job_runs_unknown_job_id_returns_empty(tmp_path: Path) -> None:
    backend = CrontabBackend(
        crontab_paths=[],
        users=[],
        syslog_path=tmp_path / "no-syslog",
    )
    with patch("silentwatch_mcp.backends.crontab.shutil.which", return_value=None):
        runs = await backend.get_job_runs("nonexistent", limit=10)
    assert runs == []


def test_derive_job_id_is_deterministic() -> None:
    id1 = CrontabBackend._derive_job_id("0 * * * *", "/usr/bin/script.sh --flag")
    id2 = CrontabBackend._derive_job_id("0 * * * *", "/usr/bin/script.sh --flag")
    assert id1 == id2  # same inputs → same id
    assert "script.sh" in id1


def test_derive_job_id_different_for_different_commands() -> None:
    id1 = CrontabBackend._derive_job_id("0 * * * *", "/usr/bin/a.sh")
    id2 = CrontabBackend._derive_job_id("0 * * * *", "/usr/bin/b.sh")
    assert id1 != id2


def test_parse_iso_syslog_timestamp() -> None:
    line = "2026-05-02T13:00:01.123Z host CRON[12345]: (root) CMD (/usr/bin/script.sh)"
    ts = CrontabBackend._parse_syslog_timestamp(line)
    assert ts == datetime(2026, 5, 2, 13, 0, 1, 123000, tzinfo=UTC)


def test_parse_legacy_syslog_timestamp() -> None:
    line = "May  2 13:00:01 host CRON[12345]: (root) CMD (/usr/bin/script.sh)"
    ts = CrontabBackend._parse_syslog_timestamp(line)
    assert ts is not None
    assert ts.month == 5
    assert ts.day == 2
    assert ts.hour == 13
    assert ts.tzinfo == UTC


def test_parse_unrecognized_timestamp_returns_none() -> None:
    line = "garbage line with no recognizable timestamp"
    ts = CrontabBackend._parse_syslog_timestamp(line)
    assert ts is None

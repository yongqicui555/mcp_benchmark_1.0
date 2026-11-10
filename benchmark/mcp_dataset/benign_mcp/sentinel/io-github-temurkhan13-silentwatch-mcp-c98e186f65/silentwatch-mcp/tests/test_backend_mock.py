"""Tests for the mock backend — verifies the data shape contract every backend must satisfy."""
from __future__ import annotations

import pytest

from silentwatch_mcp.backends.mock import MockBackend
from silentwatch_mcp.types import RunStatus


@pytest.mark.asyncio
async def test_list_jobs_returns_nonempty() -> None:
    backend = MockBackend()
    jobs = await backend.list_jobs()
    assert len(jobs) > 0
    assert all(j.id and j.name and j.schedule for j in jobs)


@pytest.mark.asyncio
async def test_list_jobs_includes_known_silent_failure_case() -> None:
    """The mock data deliberately includes web-search-refresh with silent failures."""
    backend = MockBackend()
    jobs = await backend.list_jobs()
    web_search = next((j for j in jobs if j.id == "web-search-refresh"), None)
    assert web_search is not None
    assert web_search.silent_fail_count_24h > 0


@pytest.mark.asyncio
async def test_list_jobs_includes_known_overdue_case() -> None:
    """audit-snapshot is hardcoded as overdue in the mock backend."""
    backend = MockBackend()
    jobs = await backend.list_jobs()
    audit = next((j for j in jobs if j.id == "audit-snapshot"), None)
    assert audit is not None
    assert audit.is_overdue is True
    assert audit.overdue_by_minutes is not None
    assert audit.overdue_by_minutes > 0


@pytest.mark.asyncio
async def test_get_job_runs_returns_runs_for_known_job() -> None:
    backend = MockBackend()
    runs = await backend.get_job_runs("web-search-refresh", limit=30)
    assert len(runs) > 0
    assert all(r.job_id == "web-search-refresh" for r in runs)
    # Should include silent failures per the mock data
    assert any(r.status == RunStatus.SILENT_FAILURE for r in runs)


@pytest.mark.asyncio
async def test_get_job_runs_unknown_job_returns_empty() -> None:
    backend = MockBackend()
    runs = await backend.get_job_runs("nonexistent-job", limit=10)
    assert runs == []


@pytest.mark.asyncio
async def test_get_job_runs_respects_limit() -> None:
    backend = MockBackend()
    runs = await backend.get_job_runs("web-search-refresh", limit=5)
    assert len(runs) <= 5


@pytest.mark.asyncio
async def test_tail_logs_returns_strings() -> None:
    backend = MockBackend()
    lines = await backend.tail_logs("web-search-refresh", lines=20)
    assert all(isinstance(line, str) for line in lines)
    assert len(lines) <= 20 * 2  # one status + one output line per run, max

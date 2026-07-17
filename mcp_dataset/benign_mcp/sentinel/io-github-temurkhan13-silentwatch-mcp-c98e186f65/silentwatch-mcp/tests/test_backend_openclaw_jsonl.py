"""Tests for the OpenClaw JSONL backend — JSONL parsing, malformed-line handling, summarization."""
from __future__ import annotations

import json
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest

from silentwatch_mcp.backends.openclaw_jsonl import OpenClawJsonlBackend
from silentwatch_mcp.types import RunStatus, SilentFailIndicator

# ─────────────────────── helpers ───────────────────────


def _now() -> datetime:
    return datetime.now(UTC)


def _ago(**kwargs: int) -> datetime:
    return _now() - timedelta(**kwargs)


def _record(
    *,
    run_id: str,
    job_id: str,
    started_at: datetime,
    exit_code: int = 0,
    duration_ms: int = 5_000,
    stdout: str = "Job completed successfully with normal output payload.",
    stderr: str = "",
    job_name: str | None = None,
    schedule: str | None = None,
    metadata: dict[str, str] | None = None,
) -> dict:
    rec: dict = {
        "run_id": run_id,
        "job_id": job_id,
        "started_at": started_at.isoformat().replace("+00:00", "Z"),
        "completed_at": (started_at + timedelta(milliseconds=duration_ms)).isoformat().replace("+00:00", "Z"),
        "duration_ms": duration_ms,
        "exit_code": exit_code,
        "stdout": stdout,
        "stderr": stderr,
    }
    if job_name:
        rec["job_name"] = job_name
    if schedule:
        rec["schedule"] = schedule
    if metadata:
        rec["metadata"] = metadata
    return rec


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec) + "\n")


# ─────────────────────── tests ───────────────────────


@pytest.mark.asyncio
async def test_missing_directory_returns_empty(tmp_path: Path) -> None:
    """When SILENTWATCH_OPENCLAW_LOGS doesn't exist, list_jobs returns []."""
    backend = OpenClawJsonlBackend(logs_dir=tmp_path / "nonexistent")
    jobs = await backend.list_jobs()
    assert jobs == []


@pytest.mark.asyncio
async def test_empty_directory_returns_empty(tmp_path: Path) -> None:
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    jobs = await backend.list_jobs()
    assert jobs == []


@pytest.mark.asyncio
async def test_missing_job_file_returns_empty_runs(tmp_path: Path) -> None:
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    runs = await backend.get_job_runs("nonexistent-job")
    assert runs == []


@pytest.mark.asyncio
async def test_single_run_file_parses(tmp_path: Path) -> None:
    """One JSONL file with one run produces one job + one run."""
    _write_jsonl(
        tmp_path / "test-job.jsonl",
        [
            _record(
                run_id="r1",
                job_id="test-job",
                started_at=_ago(minutes=10),
                job_name="Test Job",
                schedule="*/15 * * * *",
            ),
        ],
    )
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)

    jobs = await backend.list_jobs()
    assert len(jobs) == 1
    assert jobs[0].id == "test-job"
    assert jobs[0].name == "Test Job"
    assert jobs[0].schedule == "*/15 * * * *"
    assert jobs[0].last_run_status == RunStatus.SUCCESS

    runs = await backend.get_job_runs("test-job")
    assert len(runs) == 1
    assert runs[0].run_id == "r1"


@pytest.mark.asyncio
async def test_runs_returned_newest_first(tmp_path: Path) -> None:
    _write_jsonl(
        tmp_path / "ordered.jsonl",
        [
            _record(run_id="r-old", job_id="ordered", started_at=_ago(hours=10)),
            _record(run_id="r-mid", job_id="ordered", started_at=_ago(hours=5)),
            _record(run_id="r-new", job_id="ordered", started_at=_ago(minutes=30)),
        ],
    )
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)

    runs = await backend.get_job_runs("ordered")
    assert [r.run_id for r in runs] == ["r-new", "r-mid", "r-old"]


@pytest.mark.asyncio
async def test_explicit_failure_status(tmp_path: Path) -> None:
    """exit_code != 0 maps to RunStatus.FAILURE."""
    _write_jsonl(
        tmp_path / "fail-job.jsonl",
        [
            _record(
                run_id="r-fail",
                job_id="fail-job",
                started_at=_ago(minutes=5),
                exit_code=1,
                stdout="",
                stderr="Connection refused",
            )
        ],
    )
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    runs = await backend.get_job_runs("fail-job")
    assert len(runs) == 1
    assert runs[0].status == RunStatus.FAILURE
    # snippet falls back to stderr when stdout is empty
    assert "Connection refused" in runs[0].output_snippet


@pytest.mark.asyncio
async def test_silent_failure_empty_output_detected(tmp_path: Path) -> None:
    """exit 0 + empty stdout = silent failure."""
    _write_jsonl(
        tmp_path / "silent.jsonl",
        [
            _record(
                run_id="r-silent",
                job_id="silent",
                started_at=_ago(minutes=2),
                exit_code=0,
                stdout="",
                stderr="",
            )
        ],
    )
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    runs = await backend.get_job_runs("silent")
    assert runs[0].status == RunStatus.SILENT_FAILURE
    assert SilentFailIndicator.OUTPUT_EMPTY in runs[0].silent_fail_indicators


@pytest.mark.asyncio
async def test_silent_failure_error_keyword_detected(tmp_path: Path) -> None:
    """exit 0 + ERROR/Traceback in stdout = silent failure."""
    _write_jsonl(
        tmp_path / "errkw.jsonl",
        [
            _record(
                run_id="r-errkw",
                job_id="errkw",
                started_at=_ago(minutes=2),
                exit_code=0,
                stdout="Processing... ERROR: connection timed out (continuing anyway)",
            )
        ],
    )
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    runs = await backend.get_job_runs("errkw")
    assert runs[0].status == RunStatus.SILENT_FAILURE
    assert SilentFailIndicator.ERROR_KEYWORDS_IN_STDOUT in runs[0].silent_fail_indicators


@pytest.mark.asyncio
async def test_runs_24h_aggregation(tmp_path: Path) -> None:
    """Job summary's runs_24h includes only runs within the last 24h."""
    records: list[dict] = []
    # 5 runs in last 24h
    for i in range(5):
        records.append(
            _record(
                run_id=f"r-recent-{i}",
                job_id="agg",
                started_at=_ago(hours=i + 1),  # 1, 2, 3, 4, 5 hours ago
            )
        )
    # 3 runs older than 24h
    for i in range(3):
        records.append(
            _record(
                run_id=f"r-old-{i}",
                job_id="agg",
                started_at=_ago(hours=30 + i * 6),  # 30, 36, 42 hours ago
            )
        )
    _write_jsonl(tmp_path / "agg.jsonl", records)
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)

    jobs = await backend.list_jobs()
    assert len(jobs) == 1
    job = jobs[0]
    assert job.runs_24h == 5
    assert job.successes_24h == 5
    assert job.silent_fail_count_24h == 0


@pytest.mark.asyncio
async def test_get_job_runs_respects_limit(tmp_path: Path) -> None:
    records = [
        _record(run_id=f"r-{i}", job_id="lim", started_at=_ago(hours=i)) for i in range(10)
    ]
    _write_jsonl(tmp_path / "lim.jsonl", records)
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)

    runs = await backend.get_job_runs("lim", limit=3)
    assert len(runs) == 3


@pytest.mark.asyncio
async def test_malformed_json_line_skipped(tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
    """A bad line shouldn't kill the whole parse; log a warning and continue."""
    file_path = tmp_path / "mixed.jsonl"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps(_record(run_id="r-good-1", job_id="mixed", started_at=_ago(hours=1))) + "\n")
        f.write("this is not json\n")
        f.write(json.dumps(_record(run_id="r-good-2", job_id="mixed", started_at=_ago(minutes=30))) + "\n")

    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    runs = await backend.get_job_runs("mixed")

    assert len(runs) == 2
    assert {r.run_id for r in runs} == {"r-good-1", "r-good-2"}


@pytest.mark.asyncio
async def test_missing_required_field_skipped(tmp_path: Path) -> None:
    """A record missing run_id should be skipped, not crash the parse."""
    file_path = tmp_path / "incomplete.jsonl"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        # Missing run_id → KeyError in _record_to_run → skipped
        f.write(json.dumps({"job_id": "incomplete", "started_at": _ago(hours=1).isoformat()}) + "\n")
        # Valid
        f.write(json.dumps(_record(run_id="r-good", job_id="incomplete", started_at=_ago(minutes=10))) + "\n")
        # Empty line
        f.write("\n")

    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    runs = await backend.get_job_runs("incomplete")
    assert len(runs) == 1
    assert runs[0].run_id == "r-good"


@pytest.mark.asyncio
async def test_iso_timestamp_with_z_suffix(tmp_path: Path) -> None:
    """started_at like '2026-05-02T08:00:00Z' should parse correctly."""
    file_path = tmp_path / "tz.jsonl"
    file_path.parent.mkdir(parents=True, exist_ok=True)
    with file_path.open("w", encoding="utf-8") as f:
        f.write(json.dumps({
            "run_id": "r-z",
            "job_id": "tz",
            "started_at": "2026-05-02T08:00:00Z",
            "completed_at": "2026-05-02T08:00:04Z",
            "duration_ms": 4000,
            "exit_code": 0,
            "stdout": "ok",
        }) + "\n")
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    runs = await backend.get_job_runs("tz")
    assert len(runs) == 1
    assert runs[0].started_at.isoformat().startswith("2026-05-02T08:00:00")


@pytest.mark.asyncio
async def test_multiple_jobs_each_in_own_file(tmp_path: Path) -> None:
    """Two .jsonl files = two jobs in list_jobs()."""
    _write_jsonl(
        tmp_path / "job-a.jsonl",
        [_record(run_id="a-1", job_id="job-a", started_at=_ago(minutes=10), job_name="Job A")],
    )
    _write_jsonl(
        tmp_path / "job-b.jsonl",
        [_record(run_id="b-1", job_id="job-b", started_at=_ago(minutes=20), job_name="Job B")],
    )

    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    jobs = await backend.list_jobs()
    assert {j.id for j in jobs} == {"job-a", "job-b"}
    assert {j.name for j in jobs} == {"Job A", "Job B"}


@pytest.mark.asyncio
async def test_last_success_at_finds_most_recent_success(tmp_path: Path) -> None:
    """last_success_at = most recent run with status SUCCESS, even if last run was a failure."""
    _write_jsonl(
        tmp_path / "lsa.jsonl",
        [
            _record(run_id="r-old-success", job_id="lsa", started_at=_ago(hours=5)),
            _record(
                run_id="r-recent-fail",
                job_id="lsa",
                started_at=_ago(hours=1),
                exit_code=1,
                stdout="",
                stderr="failed",
            ),
        ],
    )
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    jobs = await backend.list_jobs()
    job = jobs[0]
    assert job.last_run_status == RunStatus.FAILURE
    assert job.last_success_at is not None
    # Most recent success was 5 hours ago
    delta = _now() - job.last_success_at
    assert 4.5 < delta.total_seconds() / 3600 < 5.5


@pytest.mark.asyncio
async def test_tail_logs_synthesizes_from_runs(tmp_path: Path) -> None:
    """tail_logs returns formatted log lines synthesized from run records."""
    _write_jsonl(
        tmp_path / "tail.jsonl",
        [
            _record(
                run_id="r-1",
                job_id="tail",
                started_at=_ago(hours=2),
                stdout="processed 100 records",
            ),
            _record(
                run_id="r-2",
                job_id="tail",
                started_at=_ago(hours=1),
                stdout="processed 110 records",
            ),
        ],
    )
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    lines = await backend.tail_logs("tail", lines=10)
    # Should have 4 lines: 2 status + 2 output
    assert len(lines) >= 2
    assert any("r-1" in line for line in lines)
    assert any("r-2" in line for line in lines)
    assert any("processed" in line for line in lines)


@pytest.mark.asyncio
async def test_metadata_carried_through(tmp_path: Path) -> None:
    """metadata dict in JSONL surfaces on CronRun."""
    _write_jsonl(
        tmp_path / "meta.jsonl",
        [
            _record(
                run_id="r-meta",
                job_id="meta",
                started_at=_ago(minutes=5),
                metadata={"openclaw_version": "2026.4.30", "host": "vps01"},
            )
        ],
    )
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)
    runs = await backend.get_job_runs("meta")
    assert runs[0].metadata.get("openclaw_version") == "2026.4.30"
    assert runs[0].metadata.get("host") == "vps01"


@pytest.mark.asyncio
async def test_top_level_schedule_lifted_into_metadata(tmp_path: Path) -> None:
    """schedule at top level of record gets stored in metadata['schedule']."""
    _write_jsonl(
        tmp_path / "sched.jsonl",
        [
            _record(
                run_id="r-sched",
                job_id="sched",
                started_at=_ago(minutes=5),
                schedule="0 */1 * * *",
            )
        ],
    )
    backend = OpenClawJsonlBackend(logs_dir=tmp_path)

    runs = await backend.get_job_runs("sched")
    assert runs[0].metadata.get("schedule") == "0 */1 * * *"

    jobs = await backend.list_jobs()
    assert jobs[0].schedule == "0 */1 * * *"

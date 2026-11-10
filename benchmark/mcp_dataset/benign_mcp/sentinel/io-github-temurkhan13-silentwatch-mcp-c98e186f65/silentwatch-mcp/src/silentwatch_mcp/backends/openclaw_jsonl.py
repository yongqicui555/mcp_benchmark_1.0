"""OpenClaw JSONL backend — parses native cron run logs.

OpenClaw emits one JSONL file per cron job in `SILENTWATCH_OPENCLAW_LOGS`. Each line is
a single run record per the schema in SPEC.md § OpenClaw JSONL backend.

File naming convention: `<job_id>.jsonl` — one file per cron job.

Required fields per record:
    run_id, job_id, started_at, exit_code

Optional fields:
    job_name, schedule, completed_at, duration_ms, stdout, stderr, metadata
"""
from __future__ import annotations

import json
import logging
import os
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Any

from silentwatch_mcp.analysis import (
    compute_overdue_state,
    detect_silent_fail_indicators,
)
from silentwatch_mcp.backends.base import CronBackend
from silentwatch_mcp.types import CronJob, CronRun, RunStatus

logger = logging.getLogger(__name__)

OUTPUT_SNIPPET_MAX_CHARS = 500
"""Cap stdout/stderr captured in CronRun.output_snippet to keep responses small."""


class OpenClawJsonlBackend(CronBackend):
    """Parses OpenClaw cron run JSONL files.

    Configuration via environment:
        SILENTWATCH_OPENCLAW_LOGS — directory containing *.jsonl files
                             (default: ~/.openclaw/cron-runs)

    File naming: `<job_id>.jsonl` — one file per cron job.
    Each line is a single run record (newline-delimited JSON).

    Malformed lines are skipped with a warning; never raise on a single bad line.
    Missing files return empty results, not errors.
    """

    name = "openclaw-jsonl"

    def __init__(self, logs_dir: Path | None = None) -> None:
        if logs_dir is not None:
            self.logs_dir = Path(logs_dir)
        else:
            logs_path = os.environ.get(
                "SILENTWATCH_OPENCLAW_LOGS",
                str(Path.home() / ".openclaw" / "cron-runs"),
            )
            self.logs_dir = Path(logs_path)

        if not self.logs_dir.exists():
            logger.warning(
                "SILENTWATCH_OPENCLAW_LOGS=%s does not exist. Backend will return empty data "
                "until logs appear. Switch to SILENTWATCH_BACKEND=mock for development.",
                self.logs_dir,
            )

    async def list_jobs(self) -> list[CronJob]:
        if not self.logs_dir.exists():
            return []

        jobs: list[CronJob] = []
        for jsonl_file in sorted(self.logs_dir.glob("*.jsonl")):
            job_id = jsonl_file.stem
            runs = self._parse_runs(jsonl_file, limit=200)
            if not runs:
                continue
            jobs.append(self._build_job_summary(job_id, runs))
        return jobs

    async def get_job_runs(self, job_id: str, limit: int = 100) -> list[CronRun]:
        jsonl_file = self.logs_dir / f"{job_id}.jsonl"
        if not jsonl_file.exists():
            return []
        return self._parse_runs(jsonl_file, limit=limit)

    async def tail_logs(self, job_id: str, lines: int = 50) -> list[str]:
        # No separate log surface — synthesize from run records.
        runs = await self.get_job_runs(job_id, limit=lines)
        out: list[str] = []
        for run in runs:
            ts = run.started_at.isoformat()
            status = run.status.value
            out.append(
                f"{ts} [{status.upper()}] run_id={run.run_id} "
                f"exit={run.exit_code} duration_ms={run.duration_ms}"
            )
            if run.output_snippet:
                snippet = run.output_snippet[:200].replace("\n", " ")
                out.append(f"{ts} [OUTPUT] {snippet}")
        return out[-lines:]

    # ────────────────── parsing ──────────────────

    def _parse_runs(self, jsonl_file: Path, limit: int) -> list[CronRun]:
        """Read JSONL, return up to `limit` newest runs with silent-fail status filled."""
        raw_runs: list[CronRun] = []
        try:
            with jsonl_file.open(encoding="utf-8") as f:
                for line_num, line in enumerate(f, start=1):
                    stripped = line.strip()
                    if not stripped:
                        continue
                    try:
                        record = json.loads(stripped)
                    except json.JSONDecodeError as exc:
                        logger.warning(
                            "Skipping malformed JSON at %s:%d: %s",
                            jsonl_file.name, line_num, exc,
                        )
                        continue
                    try:
                        run = self._record_to_run(record)
                    except (KeyError, ValueError, TypeError) as exc:
                        logger.warning(
                            "Skipping invalid run record at %s:%d: %s",
                            jsonl_file.name, line_num, exc,
                        )
                        continue
                    raw_runs.append(run)
        except OSError as exc:
            logger.error("Failed to read %s: %s", jsonl_file, exc)
            return []

        # Newest first by start time
        raw_runs.sort(key=lambda r: r.started_at, reverse=True)
        capped = raw_runs[:limit]

        # Enrich with silent-fail detection (each run gets the others as history)
        return self._enrich_with_silent_fail_detection(capped)

    @staticmethod
    def _record_to_run(record: dict[str, Any]) -> CronRun:
        """Convert a JSONL line dict into a CronRun. Raises KeyError on missing required fields."""
        run_id = str(record["run_id"])
        job_id = str(record["job_id"])
        started_at = _parse_iso(record["started_at"])
        exit_code = int(record["exit_code"]) if record.get("exit_code") is not None else None

        completed_at = (
            _parse_iso(record["completed_at"])
            if record.get("completed_at")
            else None
        )
        duration_ms = record.get("duration_ms")
        if duration_ms is not None:
            duration_ms = int(duration_ms)

        stdout = record.get("stdout", "") or ""
        stderr = record.get("stderr", "") or ""
        # Prefer stdout for snippet; fall back to stderr
        snippet_source = stdout if stdout.strip() else stderr
        snippet = snippet_source[:OUTPUT_SNIPPET_MAX_CHARS]

        # Schedule is per-run metadata for historical accuracy (jobs may change schedule)
        metadata = {str(k): str(v) for k, v in record.get("metadata", {}).items()}
        if "schedule" in record:
            metadata.setdefault("schedule", str(record["schedule"]))

        return CronRun(
            run_id=run_id,
            job_id=job_id,
            job_name=record.get("job_name"),
            started_at=started_at,
            completed_at=completed_at,
            duration_ms=duration_ms,
            exit_code=exit_code,
            status=RunStatus.UNKNOWN,  # filled in enrichment pass
            silent_fail_indicators=[],
            output_snippet=snippet,
            metadata=metadata,
        )

    @staticmethod
    def _enrich_with_silent_fail_detection(runs: list[CronRun]) -> list[CronRun]:
        """Apply silent-fail rules to each run, set status, return new CronRun list.

        CronRun is frozen; we reconstruct each one with the computed status/indicators.
        """
        result: list[CronRun] = []
        for run in runs:
            others = [r for r in runs if r.run_id != run.run_id]
            indicators = detect_silent_fail_indicators(run, historical_runs=others)

            if run.exit_code is None:
                status = RunStatus.UNKNOWN
            elif run.exit_code != 0:
                status = RunStatus.FAILURE
            elif indicators:
                status = RunStatus.SILENT_FAILURE
            else:
                status = RunStatus.SUCCESS

            result.append(
                run.model_copy(
                    update={
                        "status": status,
                        "silent_fail_indicators": indicators,
                    }
                )
            )
        return result

    @staticmethod
    def _build_job_summary(job_id: str, runs: list[CronRun]) -> CronJob:
        """Aggregate a job's runs into a CronJob summary. Assumes runs newest-first, non-empty."""
        last_run = runs[0]
        last_success = next(
            (r for r in runs if r.status == RunStatus.SUCCESS),
            None,
        )

        cutoff_24h = datetime.now(UTC) - timedelta(hours=24)
        runs_24h = [r for r in runs if r.started_at >= cutoff_24h]
        successes_24h = [r for r in runs_24h if r.status == RunStatus.SUCCESS]
        silent_fails_24h = [r for r in runs_24h if r.status == RunStatus.SILENT_FAILURE]

        # Job name: first non-None job_name across runs
        job_name = (
            last_run.job_name
            or next((r.job_name for r in runs if r.job_name), None)
            or job_id
        )

        # Schedule: from any run's metadata
        schedule = (
            last_run.metadata.get("schedule")
            or next(
                (r.metadata.get("schedule") for r in runs if r.metadata.get("schedule")),
                None,
            )
            or "unknown"
        )

        is_overdue, overdue_by_minutes, next_expected_run_at = compute_overdue_state(
            schedule=schedule,
            last_run_at=last_run.started_at,
        )

        return CronJob(
            id=job_id,
            name=job_name,
            schedule=schedule,
            last_run_at=last_run.started_at,
            last_run_status=last_run.status,
            last_success_at=last_success.started_at if last_success else None,
            runs_24h=len(runs_24h),
            successes_24h=len(successes_24h),
            silent_fail_count_24h=len(silent_fails_24h),
            is_overdue=is_overdue,
            overdue_by_minutes=overdue_by_minutes,
            next_expected_run_at=next_expected_run_at,
            metadata=dict(last_run.metadata),
        )


def _parse_iso(value: Any) -> datetime:
    """Parse an ISO 8601 timestamp; tolerate trailing Z."""
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=UTC)
        return value
    if not isinstance(value, str):
        raise ValueError(f"Expected ISO timestamp string, got {type(value).__name__}")
    s = value.strip()
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    parsed = datetime.fromisoformat(s)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=UTC)
    return parsed

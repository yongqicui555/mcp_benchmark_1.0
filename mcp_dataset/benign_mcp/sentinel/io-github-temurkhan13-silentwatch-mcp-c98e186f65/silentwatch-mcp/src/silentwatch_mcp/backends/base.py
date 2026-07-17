"""Abstract base class for cron backends.

Every backend implements 3 core methods. Higher-level analysis (silent-fail detection,
overdue detection, success-rate calculation) lives in `analysis.py` and consumes the
data backends produce; backends don't need to implement that logic themselves.
"""
from __future__ import annotations

from abc import ABC, abstractmethod

from silentwatch_mcp.types import CronJob, CronRun


class CronBackend(ABC):
    """Contract every cron backend must satisfy."""

    name: str = "base"
    """Backend identifier — also the value of SILENTWATCH_BACKEND that selects it."""

    @abstractmethod
    async def list_jobs(self) -> list[CronJob]:
        """Return all known cron jobs with summary state.

        Backends should populate at minimum: id, name, schedule, last_run_at,
        last_run_status. Other fields can default if the backend doesn't have them.
        """

    @abstractmethod
    async def get_job_runs(self, job_id: str, limit: int = 100) -> list[CronRun]:
        """Return up to `limit` recent runs for a single job, newest first.

        Used by both `get_job_runs` tool and analysis (silent-fail rate calculation
        consumes run histories). Backends should return at least exit_code, started_at,
        and a representative output_snippet.
        """

    @abstractmethod
    async def tail_logs(self, job_id: str, lines: int = 50) -> list[str]:
        """Return up to `lines` recent log output lines for a job, newest last.

        For backends that don't maintain a separate log surface (e.g., mock or
        openclaw-jsonl which puts output in run records), implementations can
        synthesize this from `get_job_runs` outputs.
        """

    async def get_run_by_id(self, run_id: str) -> CronRun | None:
        """Return a single run by its run_id, or None if not found.

        Default implementation: scan every job's recent-run window for a
        matching run_id. Backends with a more efficient lookup path
        (e.g., a flat run-log file or an indexed store) should override.

        Used to back the `cron://run/{id}` resource (added v1.0.7).
        """
        jobs = await self.list_jobs()
        for job in jobs:
            runs = await self.get_job_runs(job.id, limit=200)
            for run in runs:
                if run.run_id == run_id:
                    return run
        return None

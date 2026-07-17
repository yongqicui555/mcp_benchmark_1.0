"""Systemd timers backend — parses `systemctl list-timers` + `journalctl`.

Scope:
    - Enumerate scheduled jobs via `systemctl list-timers --all --output=json`
    - Per-unit run history via `journalctl -u <unit> --output=json -n <limit>`
    - Map systemd timer state to MCP types

Platform: Linux only (systems with systemd). On other platforms returns empty.

Discovery:
    - `systemctl list-timers --all` returns: NEXT, LEFT, LAST, PASSED, UNIT, ACTIVATES
    - We use UNIT (the .timer name) as the job_id, ACTIVATES is the .service that runs.
"""
from __future__ import annotations

import json
import logging
import os
import shutil
import subprocess
from datetime import UTC, datetime
from typing import Any

from silentwatch_mcp.analysis import compute_overdue_state
from silentwatch_mcp.backends.base import CronBackend
from silentwatch_mcp.types import CronJob, CronRun, RunStatus

logger = logging.getLogger(__name__)


class SystemdBackend(CronBackend):
    """Reads scheduled jobs from systemd timers.

    Configuration via environment:
        SILENTWATCH_SYSTEMD_USER — if set to "1", uses `systemctl --user`
                                 instead of system-wide
    """

    name = "systemd"

    def __init__(
        self,
        systemctl_cmd: str = "systemctl",
        journalctl_cmd: str = "journalctl",
        user_mode: bool | None = None,
    ) -> None:
        self.systemctl_cmd = systemctl_cmd
        self.journalctl_cmd = journalctl_cmd
        if user_mode is None:
            self.user_mode = os.environ.get("SILENTWATCH_SYSTEMD_USER", "0") == "1"
        else:
            self.user_mode = user_mode

    async def list_jobs(self) -> list[CronJob]:
        if shutil.which(self.systemctl_cmd) is None:
            logger.debug("systemctl not found; SystemdBackend returns empty")
            return []

        timers = self._list_timers()
        if not timers:
            return []

        jobs: list[CronJob] = []
        for timer in timers:
            unit_name = timer.get("unit", "")
            if not unit_name:
                continue

            activates = timer.get("activates", "")
            next_run = self._parse_systemctl_time(timer.get("next", ""))
            last_run = self._parse_systemctl_time(timer.get("last", ""))

            # Determine schedule: systemctl doesn't directly report the OnCalendar string
            # in list-timers output. Best we can do: present "see systemd timer" placeholder
            # OR query the unit file via `systemctl cat <unit>` (more expensive).
            schedule = self._get_schedule(unit_name) or "systemd-timer"

            is_overdue, overdue_by, computed_next = compute_overdue_state(
                schedule=schedule,
                last_run_at=last_run,
            )

            jobs.append(
                CronJob(
                    id=f"systemd-{unit_name}",
                    name=activates or unit_name,
                    schedule=schedule,
                    last_run_at=last_run,
                    last_run_status=RunStatus.UNKNOWN if last_run else None,
                    last_success_at=None,
                    runs_24h=0,
                    successes_24h=0,
                    silent_fail_count_24h=0,
                    is_overdue=is_overdue,
                    overdue_by_minutes=overdue_by,
                    next_expected_run_at=computed_next or next_run,
                    metadata={
                        "unit": unit_name,
                        "activates": activates,
                        "passed": str(timer.get("passed", "")),
                    },
                )
            )
        return jobs

    async def get_job_runs(self, job_id: str, limit: int = 100) -> list[CronRun]:
        if shutil.which(self.journalctl_cmd) is None:
            return []
        unit_name = job_id.removeprefix("systemd-")
        # Get the .service unit (timer activates a service)
        # Look up the actual service unit
        timers = self._list_timers()
        match = next((t for t in timers if t.get("unit") == unit_name), None)
        if not match:
            return []
        service_unit = match.get("activates") or unit_name.replace(".timer", ".service")

        entries = self._journal_for_unit(service_unit, limit)
        runs: list[CronRun] = []
        for entry in entries:
            ts = self._parse_journal_timestamp(entry)
            if ts is None:
                continue
            message = entry.get("MESSAGE", "")
            # Heuristic: a journal entry per service start/stop. We only flag
            # "Started <unit>" or "Finished <unit>" or exit-status messages.
            exit_code = self._extract_exit_code(entry, message)
            status = RunStatus.SUCCESS if exit_code == 0 else (
                RunStatus.FAILURE if exit_code is not None else RunStatus.UNKNOWN
            )
            runs.append(
                CronRun(
                    run_id=f"journal-{entry.get('__REALTIME_TIMESTAMP', ts.timestamp())}",
                    job_id=job_id,
                    job_name=service_unit,
                    started_at=ts,
                    completed_at=None,
                    duration_ms=None,
                    exit_code=exit_code,
                    status=status,
                    silent_fail_indicators=[],
                    output_snippet=message[:500] if message else "",
                    metadata={"unit": service_unit},
                )
            )
        return runs[:limit]

    async def tail_logs(self, job_id: str, lines: int = 50) -> list[str]:
        runs = await self.get_job_runs(job_id, limit=lines)
        return [
            f"{r.started_at.isoformat()} [{r.status.value.upper()}] {r.output_snippet[:200]}"
            for r in runs
        ]

    # ────────────── subprocess wrappers ──────────────

    def _list_timers(self) -> list[dict[str, Any]]:
        cmd = [self.systemctl_cmd]
        if self.user_mode:
            cmd.append("--user")
        cmd.extend(["list-timers", "--all", "--output=json", "--no-pager"])
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=15,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.warning("Failed to run %s: %s", " ".join(cmd), exc)
            return []

        if result.returncode != 0:
            logger.warning(
                "systemctl list-timers exited %d: %s",
                result.returncode, result.stderr.strip(),
            )
            return []

        try:
            data = json.loads(result.stdout)
        except json.JSONDecodeError as exc:
            logger.warning("Cannot parse systemctl JSON: %s", exc)
            return []

        if not isinstance(data, list):
            return []
        return data

    def _journal_for_unit(self, unit: str, limit: int) -> list[dict[str, Any]]:
        cmd = [self.journalctl_cmd]
        if self.user_mode:
            cmd.append("--user")
        cmd.extend([
            "-u", unit,
            "--output=json",
            "-n", str(min(limit, 500)),
            "--no-pager",
        ])
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=20,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.warning("Failed to run %s: %s", " ".join(cmd), exc)
            return []

        if result.returncode != 0:
            return []

        entries: list[dict[str, Any]] = []
        for line in result.stdout.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
        return entries

    def _get_schedule(self, unit_name: str) -> str | None:
        """Query the timer unit's OnCalendar= setting via `systemctl show`."""
        cmd = [self.systemctl_cmd]
        if self.user_mode:
            cmd.append("--user")
        cmd.extend(["show", unit_name, "--property=TimersCalendar"])
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return None
        if result.returncode != 0:
            return None
        # Output: TimersCalendar={ OnCalendar=*-*-* 03:00:00 ; next=Sun 2026-05-04 03:00:00 UTC ; ... }
        match = self._extract_oncalendar(result.stdout)
        return match

    @staticmethod
    def _extract_oncalendar(systemctl_show_output: str) -> str | None:
        import re
        m = re.search(r"OnCalendar=([^;}\n]+)", systemctl_show_output)
        if m:
            return m.group(1).strip()
        return None

    @staticmethod
    def _parse_systemctl_time(value: str | int) -> datetime | None:
        if not value or value in ("n/a", "-"):
            return None
        # systemctl outputs like "Sun 2026-05-02 14:00:00 UTC" or ISO format with --output=json
        # In JSON mode, fields like "next" are integer timestamps in microseconds since epoch
        if isinstance(value, int):
            return datetime.fromtimestamp(value / 1_000_000, tz=UTC)
        try:
            # Try JSON-mode integer-as-string
            ts_us = int(value)
            return datetime.fromtimestamp(ts_us / 1_000_000, tz=UTC)
        except (ValueError, TypeError):
            pass
        # Fall back to parsing common systemctl text formats
        try:
            return datetime.strptime(value, "%a %Y-%m-%d %H:%M:%S %Z").replace(tzinfo=UTC)
        except ValueError:
            return None

    @staticmethod
    def _parse_journal_timestamp(entry: dict[str, Any]) -> datetime | None:
        ts_str = entry.get("__REALTIME_TIMESTAMP")
        if not ts_str:
            return None
        try:
            ts_us = int(ts_str)
            return datetime.fromtimestamp(ts_us / 1_000_000, tz=UTC)
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _extract_exit_code(entry: dict[str, Any], message: str) -> int | None:
        # systemd journal entries from .service may have EXIT_STATUS field
        exit_status = entry.get("EXIT_STATUS")
        if exit_status is not None:
            try:
                return int(exit_status)
            except (ValueError, TypeError):
                pass
        # Otherwise heuristic from message
        import re
        m = re.search(r"\b(?:exit|exit code|exited with code|status)[\s:=]+(\d+)\b", message, re.I)
        if m:
            return int(m.group(1))
        return None

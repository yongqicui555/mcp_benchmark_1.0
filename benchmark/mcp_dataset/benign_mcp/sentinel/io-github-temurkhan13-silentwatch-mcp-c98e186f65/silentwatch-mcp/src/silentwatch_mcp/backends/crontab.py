"""Crontab backend — parses `/etc/crontab` + per-user crontabs (Linux/Unix).

Scope:
    - Enumerate jobs by parsing crontab entries (5-field cron expressions + 6-field with seconds)
    - For per-user crontab, runs `crontab -l` (subprocess)
    - For system crontab, reads `/etc/crontab` if accessible
    - Last-run inference is best-effort: scans `/var/log/syslog` or `/var/log/cron` for
      `CRON[<pid>]:` entries matching the command. If no log access, last_run_at = None
      and the job will appear overdue (correct: we don't know it ran).

Platform: Linux/Unix. On Windows the `crontab` command doesn't exist; the backend
returns empty results without erroring.

For richer history, use the OpenClaw JSONL backend with a logging shim
(see `examples/openclaw-jsonl-shim.sh`).
"""
from __future__ import annotations

import logging
import os
import re
import shutil
import subprocess
from datetime import UTC, datetime, timedelta
from pathlib import Path

from silentwatch_mcp.analysis import compute_overdue_state
from silentwatch_mcp.backends.base import CronBackend
from silentwatch_mcp.types import CronJob, CronRun, RunStatus

logger = logging.getLogger(__name__)

DEFAULT_SYSLOG_PATHS = (
    "/var/log/syslog",
    "/var/log/cron",
    "/var/log/cron.log",
    "/var/log/messages",
)

# Crontab line format: <minute> <hour> <day> <month> <weekday> <command>
# Or with @yearly/@monthly/@weekly/@daily/@hourly/@reboot prefix
CRONTAB_LINE = re.compile(
    r"^\s*"
    r"(?:(?P<env>[A-Z_][A-Z0-9_]*\s*=.*)|"
    r"(?P<sched>(?:@[a-z]+|"
    r"(?:[\d*,/\-?]+\s+){4}[\d*,/\-?]+))"
    r"\s+(?:(?P<user>[\w-]+)\s+)?"
    r"(?P<cmd>.+))"
    r"\s*$"
)


class CrontabBackend(CronBackend):
    """Reads scheduled jobs from system + user crontabs.

    Configuration via environment:
        SILENTWATCH_CRONTAB_PATHS — comma-separated paths to system crontab files
                                 (default: /etc/crontab + /etc/cron.d/*)
        SILENTWATCH_CRONTAB_USERS — comma-separated usernames whose crontabs to enumerate
                                 (default: current user only)
        SILENTWATCH_SYSLOG — path to cron-log file for last-run inference
                               (default: try /var/log/syslog, /var/log/cron in order)
    """

    name = "crontab"

    def __init__(
        self,
        crontab_paths: list[Path] | None = None,
        users: list[str] | None = None,
        syslog_path: Path | None = None,
        crontab_cmd: str = "crontab",
    ) -> None:
        if crontab_paths is None:
            env_paths = os.environ.get("SILENTWATCH_CRONTAB_PATHS", "")
            if env_paths:
                self.crontab_paths = [Path(p.strip()) for p in env_paths.split(",") if p.strip()]
            else:
                self.crontab_paths = self._default_system_crontab_paths()
        else:
            self.crontab_paths = list(crontab_paths)

        if users is None:
            env_users = os.environ.get("SILENTWATCH_CRONTAB_USERS", "")
            if env_users:
                self.users = [u.strip() for u in env_users.split(",") if u.strip()]
            else:
                self.users = []  # empty = current user only
        else:
            self.users = list(users)

        if syslog_path is None:
            env_syslog = os.environ.get("SILENTWATCH_SYSLOG", "")
            if env_syslog:
                self.syslog_path: Path | None = Path(env_syslog)
            else:
                self.syslog_path = self._first_existing(DEFAULT_SYSLOG_PATHS)
        else:
            self.syslog_path = Path(syslog_path)

        self.crontab_cmd = crontab_cmd

    @staticmethod
    def _default_system_crontab_paths() -> list[Path]:
        paths = [Path("/etc/crontab")]
        cron_d = Path("/etc/cron.d")
        if cron_d.exists():
            paths.extend(sorted(cron_d.glob("*")))
        return paths

    @staticmethod
    def _first_existing(candidates: tuple[str, ...]) -> Path | None:
        for c in candidates:
            p = Path(c)
            if p.exists():
                return p
        return None

    async def list_jobs(self) -> list[CronJob]:
        entries = self._collect_entries()
        if not entries:
            return []

        jobs: list[CronJob] = []
        for job_id, schedule, command, source in entries:
            last_run_at = self._infer_last_run(job_id, command)
            is_overdue, overdue_by, next_run = compute_overdue_state(
                schedule=schedule,
                last_run_at=last_run_at,
            )

            jobs.append(
                CronJob(
                    id=job_id,
                    name=command if len(command) <= 60 else command[:57] + "...",
                    schedule=schedule,
                    last_run_at=last_run_at,
                    last_run_status=RunStatus.UNKNOWN if last_run_at else None,
                    last_success_at=None,  # crontab can't distinguish success without log parsing
                    runs_24h=0,  # not computed from crontab alone
                    successes_24h=0,
                    silent_fail_count_24h=0,
                    is_overdue=is_overdue,
                    overdue_by_minutes=overdue_by,
                    next_expected_run_at=next_run,
                    metadata={"source": source, "command": command},
                )
            )
        return jobs

    async def get_job_runs(self, job_id: str, limit: int = 100) -> list[CronRun]:
        # Crontab backend has no native run history. Last-run inference returns at most
        # one run per job (the most recent matching syslog entry). For richer history,
        # use the OpenClaw JSONL backend.
        entries = self._collect_entries()
        match = next(((s, c, src) for jid, s, c, src in entries if jid == job_id), None)
        if match is None:
            return []
        schedule, command, source = match

        last_run_at = self._infer_last_run(job_id, command)
        if last_run_at is None:
            return []

        return [
            CronRun(
                run_id=f"crontab-{job_id}-{int(last_run_at.timestamp())}",
                job_id=job_id,
                job_name=command[:60],
                started_at=last_run_at,
                completed_at=None,
                duration_ms=None,
                exit_code=None,
                status=RunStatus.UNKNOWN,
                silent_fail_indicators=[],
                output_snippet="",
                metadata={"source": source, "command": command},
            )
        ]

    async def tail_logs(self, job_id: str, lines: int = 50) -> list[str]:
        if self.syslog_path is None or not self.syslog_path.exists():
            return []
        try:
            content = self.syslog_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.warning("Cannot read %s: %s", self.syslog_path, exc)
            return []

        # Filter syslog lines mentioning CRON, then further by job_id heuristically
        cron_lines = [line for line in content.splitlines() if "CRON" in line and job_id in line]
        return cron_lines[-lines:]

    # ────────────── parsing helpers ──────────────

    def _collect_entries(self) -> list[tuple[str, str, str, str]]:
        """Collect (job_id, schedule, command, source) tuples from all configured sources."""
        entries: list[tuple[str, str, str, str]] = []

        # System crontab files (have user field)
        for crontab_path in self.crontab_paths:
            if not crontab_path.exists():
                continue
            try:
                content = crontab_path.read_text(encoding="utf-8", errors="replace")
            except OSError as exc:
                logger.warning("Cannot read %s: %s", crontab_path, exc)
                continue
            for entry in self._parse_crontab(content, has_user_field=True):
                schedule, _user, command = entry
                job_id = self._derive_job_id(schedule, command)
                entries.append((job_id, schedule, command, str(crontab_path)))

        # Per-user crontabs via `crontab -l`
        if shutil.which(self.crontab_cmd) is None:
            logger.debug("`%s` not found on PATH; skipping per-user crontab", self.crontab_cmd)
        else:
            user_list = self.users if self.users else [None]  # None = current user
            for user in user_list:
                user_content = self._run_crontab_l(user)
                if user_content is None:
                    continue
                for entry in self._parse_crontab(user_content, has_user_field=False):
                    schedule, _, command = entry
                    job_id = self._derive_job_id(schedule, command, user_prefix=user)
                    source = f"crontab -l (user: {user or 'current'})"
                    entries.append((job_id, schedule, command, source))

        return entries

    @staticmethod
    def _parse_crontab(content: str, *, has_user_field: bool) -> list[tuple[str, str | None, str]]:
        """Parse a crontab file into (schedule, user, command) tuples.

        `has_user_field=True` for /etc/crontab and /etc/cron.d/* (which have a user column);
        `False` for `crontab -l` output (no user column).
        """
        result: list[tuple[str, str | None, str]] = []
        for raw_line in content.splitlines():
            line = raw_line.strip()
            if not line or line.startswith("#"):
                continue
            # Skip env-var assignments (PATH=, MAILTO=, SHELL=)
            if "=" in line.split()[0]:
                continue

            # Detect @-prefix shortcuts (@hourly, @daily, etc.)
            if line.startswith("@"):
                parts = line.split(maxsplit=2 if has_user_field else 1)
                if has_user_field and len(parts) >= 3:
                    result.append((parts[0], parts[1], parts[2]))
                elif not has_user_field and len(parts) >= 2:
                    result.append((parts[0], None, parts[1]))
                continue

            # 5-field cron expression
            parts = line.split(maxsplit=6 if has_user_field else 5)
            if has_user_field and len(parts) >= 7:
                schedule = " ".join(parts[:5])
                user = parts[5]
                command = parts[6]
                result.append((schedule, user, command))
            elif not has_user_field and len(parts) >= 6:
                schedule = " ".join(parts[:5])
                command = parts[5]
                result.append((schedule, None, command))
        return result

    def _run_crontab_l(self, user: str | None) -> str | None:
        cmd = [self.crontab_cmd, "-l"]
        if user:
            cmd.extend(["-u", user])
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10,
                check=False,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as exc:
            logger.warning("Failed to run %s: %s", " ".join(cmd), exc)
            return None
        if result.returncode != 0:
            # Common case: "no crontab for $user" exits non-zero — not an error worth surfacing.
            logger.debug(
                "crontab -l exited %d (likely no crontab): %s",
                result.returncode, result.stderr.strip(),
            )
            return None
        return result.stdout

    @staticmethod
    def _derive_job_id(schedule: str, command: str, user_prefix: str | None = None) -> str:
        """Stable identifier for a job derived from its command (since crontab has no IDs)."""
        # Use first word of command (the executable) as the readable part
        first_word = command.split()[0] if command.split() else "unknown"
        executable = Path(first_word).name  # strip path
        # Add a short hash of the full command for disambiguation
        import hashlib
        digest = hashlib.sha256(f"{schedule} {command}".encode()).hexdigest()[:6]
        prefix = f"{user_prefix}-" if user_prefix else ""
        return f"crontab-{prefix}{executable}-{digest}"

    def _infer_last_run(self, job_id: str, command: str) -> datetime | None:
        """Best-effort inference of last-run from syslog. Returns None if no info."""
        if self.syslog_path is None or not self.syslog_path.exists():
            return None
        try:
            content = self.syslog_path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            logger.debug("Cannot read syslog %s: %s", self.syslog_path, exc)
            return None

        # Match the last CRON line referencing the command (heuristic)
        # Typical format: "May  2 14:00:01 host CRON[12345]: (user) CMD (the_command_here)"
        # We match by the executable path or first word of command.
        first_word = command.split()[0] if command.split() else ""
        if not first_word:
            return None

        latest: datetime | None = None
        for line in content.splitlines():
            if "CRON" not in line or first_word not in line:
                continue
            # Parse the leading timestamp; syslog format varies. Try common formats.
            ts = self._parse_syslog_timestamp(line)
            if ts and (latest is None or ts > latest):
                latest = ts
        return latest

    @staticmethod
    def _parse_syslog_timestamp(line: str) -> datetime | None:
        # Try ISO timestamp first (rsyslog default in newer distros): "2026-05-02T14:00:01.123Z"
        iso_match = re.match(
            r"^(?P<ts>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d+)?(?:Z|[+\-]\d{2}:?\d{2})?)",
            line,
        )
        if iso_match:
            ts = iso_match.group("ts")
            if ts.endswith("Z"):
                ts = ts[:-1] + "+00:00"
            try:
                parsed = datetime.fromisoformat(ts)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=UTC)
                return parsed
            except ValueError:
                pass

        # Legacy syslog: "May  2 14:00:01" — assume current year
        legacy_match = re.match(
            r"^(?P<mon>[A-Z][a-z]{2})\s+(?P<day>\d{1,2})\s+(?P<time>\d{2}:\d{2}:\d{2})",
            line,
        )
        if legacy_match:
            now = datetime.now(UTC)
            try:
                parsed = datetime.strptime(
                    f"{now.year} {legacy_match.group('mon')} "
                    f"{legacy_match.group('day')} {legacy_match.group('time')}",
                    "%Y %b %d %H:%M:%S",
                )
                # If the parsed date is in the future (e.g., logged Dec, now Jan), use last year
                parsed = parsed.replace(tzinfo=UTC)
                if parsed > now + timedelta(days=1):
                    parsed = parsed.replace(year=now.year - 1)
                return parsed
            except ValueError:
                pass

        return None

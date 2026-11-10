"""`python -m silentwatch_mcp monitor` — long-running NDJSON event stream.

Used by Aufgaard's monitor framework (and any other MCP-aware host that wants
inline notifications) to surface silent-failure detections as they happen.

Each detected silent failure becomes one NDJSON line on stdout. The Aufgaard
framework reads stdout line-by-line and forwards each event to the host as a
notification. Aufgaard's notification template references these fields:
``job_name``, ``pattern``, ``datetime``.

Behavior:

- On startup: runs ``build_silent_failure_report`` once against the configured
  backend and emits NDJSON for every flagged job (so the host gets immediate
  context on existing problems).
- Then enters a poll loop with the configured interval. Re-runs the report each
  cycle and emits NDJSON only for *new* detections (deduped by run_id).
- Exits cleanly on SIGTERM / Ctrl+C.

Backend selection mirrors the MCP server: ``SILENTWATCH_BACKEND``.

Args (all optional, accepted for compatibility with Aufgaard's monitor command):

- ``--tail`` — passthrough flag (currently no-op; future: switch to log-tailing
  mode for OpenClaw JSONL backend instead of polling)
- ``--interval <duration>`` — poll interval (e.g. ``60s``, ``5m``). Defaults to ``60s``.
- ``--format ndjson`` — output format (only ndjson is supported in v1)

Stdout: NDJSON, one JSON object per line, ``flush=True`` after every line so the
consumer sees events in real time.

Stderr: a single startup banner + occasional debug logs. Stdout is reserved for
the event stream.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import logging
import os
import sys
from datetime import datetime, timezone

from silentwatch_mcp import __version__
from silentwatch_mcp.analysis import build_silent_failure_report
from silentwatch_mcp.backends.crontab import CrontabBackend
from silentwatch_mcp.backends.mock import MockBackend
from silentwatch_mcp.backends.openclaw_jsonl import OpenClawJsonlBackend
from silentwatch_mcp.backends.systemd import SystemdBackend


logger = logging.getLogger(__name__)


def _build_backend(name: str):
    if name in {"openclaw-jsonl", "openclaw_jsonl"}:
        return OpenClawJsonlBackend()
    if name == "crontab":
        return CrontabBackend()
    if name == "systemd":
        return SystemdBackend()
    return MockBackend()


def _parse_duration(s: str) -> float:
    """Parse e.g. ``60s``, ``5m``, ``1h`` into seconds. Bare numbers = seconds."""
    s = s.strip().lower()
    if not s:
        return 60.0
    if s.endswith("ms"):
        return float(s[:-2]) / 1000.0
    if s.endswith("s"):
        return float(s[:-1])
    if s.endswith("m"):
        return float(s[:-1]) * 60.0
    if s.endswith("h"):
        return float(s[:-1]) * 3600.0
    return float(s)


def _emit(event: dict) -> None:
    """Write one NDJSON line to stdout."""
    print(json.dumps(event, default=str), flush=True)


async def _poll_once(backend, seen: set[str]) -> int:
    """One poll cycle. Emits NDJSON for any flagged jobs not already seen.

    Returns the count of new events emitted.
    """
    jobs = await backend.list_jobs()
    runs_by_job = {job.id: await backend.get_job_runs(job.id, limit=100) for job in jobs}
    report = build_silent_failure_report(jobs, runs_by_job, window_hours=24)

    new_count = 0
    for flag in report.jobs_flagged:
        # Dedupe by job_id + first-sample-run-id so a re-detected silent failure
        # for a NEW run still emits but a re-emission for the same run doesn't.
        key = f"{flag.job_id}:{flag.sample_run_ids[0] if flag.sample_run_ids else 'all'}"
        if key in seen:
            continue
        seen.add(key)
        new_count += 1
        _emit({
            "type": "silent_failure",
            "job_id": flag.job_id,
            "job_name": flag.job_name,
            "pattern": ",".join(i.value for i in flag.indicators),
            "silent_fail_count": flag.silent_fail_count,
            "total_runs": flag.total_runs,
            "silent_fail_rate": flag.silent_fail_rate,
            "sample_run_ids": flag.sample_run_ids,
            "datetime": datetime.now(timezone.utc).isoformat(),
            "severity": "high" if flag.silent_fail_rate >= 0.5 else "medium",
        })

    return new_count


async def _run_monitor(interval_seconds: float) -> int:
    backend_name = os.environ.get("SILENTWATCH_BACKEND", "mock")
    backend = _build_backend(backend_name)

    if not os.environ.get("SILENTWATCH_QUIET", "").strip() in {"1", "true", "yes"}:
        print(
            f"silentwatch-mcp v{__version__} monitor · backend={backend_name} · interval={interval_seconds:.0f}s · stdout=ndjson",
            file=sys.stderr,
            flush=True,
        )

    seen: set[str] = set()

    # Initial pass: emit current state
    try:
        n = await _poll_once(backend, seen)
        logger.debug("initial poll: %d new event(s)", n)
    except Exception:
        logger.exception("initial poll failed")

    # Heartbeat poll loop
    while True:
        try:
            await asyncio.sleep(interval_seconds)
            n = await _poll_once(backend, seen)
            if n > 0:
                logger.debug("poll: %d new event(s)", n)
        except asyncio.CancelledError:
            return 0
        except Exception:
            logger.exception("poll cycle failed; continuing")


def main() -> int:
    """Entry point for ``python -m silentwatch_mcp monitor``."""
    logging.basicConfig(
        level=os.environ.get("OPENCLAW_CRON_LOG_LEVEL", "WARNING"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,
    )

    parser = argparse.ArgumentParser(
        prog="silentwatch-mcp monitor",
        description="Long-running NDJSON event stream of silent-failure detections.",
    )
    parser.add_argument("--tail", action="store_true", help="Tail logs (passthrough; reserved for v2)")
    parser.add_argument("--interval", default="60s", help="Poll interval (default: 60s)")
    parser.add_argument(
        "--format",
        choices=["ndjson"],
        default="ndjson",
        help="Output format (only ndjson supported)",
    )

    # Strip the leading "monitor" subcommand if invoked via `python -m silentwatch_mcp monitor ...`
    args_list = sys.argv[1:]
    if args_list and args_list[0] == "monitor":
        args_list = args_list[1:]

    args = parser.parse_args(args_list)

    interval = _parse_duration(args.interval)

    try:
        return asyncio.run(_run_monitor(interval))
    except KeyboardInterrupt:
        return 0


if __name__ == "__main__":
    sys.exit(main())

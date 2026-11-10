"""`silentwatch-mcp-report` console script — print a one-page markdown report.

Runs against whichever backend is configured (defaults to `mock`), produces a
markdown summary on stdout suitable for piping into a file / doc / Slack
message / GitHub issue / chat. Same data the MCP server would expose via
`find_silent_failures`, but rendered for human eyeballs.

Backend selection mirrors the MCP server: ``SILENTWATCH_BACKEND`` env var.
"""
from __future__ import annotations

import asyncio
import os
import sys

from silentwatch_mcp import __version__
from silentwatch_mcp.analysis import build_silent_failure_report
from silentwatch_mcp.backends.crontab import CrontabBackend
from silentwatch_mcp.backends.mock import MockBackend
from silentwatch_mcp.backends.openclaw_jsonl import OpenClawJsonlBackend
from silentwatch_mcp.backends.systemd import SystemdBackend
from silentwatch_mcp.render import render_silent_failure_report


def _build_backend(name: str):
    if name in {"openclaw-jsonl", "openclaw_jsonl"}:
        return OpenClawJsonlBackend()
    if name == "crontab":
        return CrontabBackend()
    if name == "systemd":
        return SystemdBackend()
    return MockBackend()


async def _run() -> int:
    backend_name = os.environ.get("SILENTWATCH_BACKEND", "mock")
    backend = _build_backend(backend_name)

    jobs = await backend.list_jobs()
    runs_by_job = {job.id: await backend.get_job_runs(job.id, limit=200) for job in jobs}
    report = build_silent_failure_report(jobs, runs_by_job, window_hours=24)

    md = render_silent_failure_report(
        jobs=jobs,
        report=report,
        backend_name=backend_name,
        version=__version__,
    )
    print(md, file=sys.stdout)
    return 0


def main() -> None:
    # Force UTF-8 on stdout — markdown contains emoji + non-ASCII separators
    # which Windows cp1252 can't encode by default. Linux/Mac default to UTF-8
    # so this is a no-op there.
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except (AttributeError, OSError):
        pass
    sys.exit(asyncio.run(_run()))


if __name__ == "__main__":
    main()

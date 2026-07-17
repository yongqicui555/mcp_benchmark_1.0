"""MCP server — registers tools, resources, prompts; delegates to backends + analysis."""
from __future__ import annotations

import json
import logging
from typing import Any

from mcp.server import Server
from mcp.types import (
    GetPromptResult,
    Prompt,
    PromptArgument,
    PromptMessage,
    Resource,
    TextContent,
    Tool,
)
from pydantic import AnyUrl

from silentwatch_mcp.analysis import (
    build_job_status,
    build_silent_failure_report,
)
from silentwatch_mcp.backends import get_backend
from silentwatch_mcp.backends.base import CronBackend
from silentwatch_mcp.types import JobListResponse, JobLogTail, JobRunsResponse

logger = logging.getLogger(__name__)

SERVER_NAME = "silentwatch"


def build_server(backend_name: str = "mock") -> Server:
    """Construct a configured MCP server with the given backend selected."""
    backend: CronBackend = get_backend(backend_name)
    server: Server = Server(SERVER_NAME)

    # ─────────────────────────── Tools ───────────────────────────

    @server.list_tools()  # type: ignore[no-untyped-call, untyped-decorator]
    async def list_tools() -> list[Tool]:
        return [
            Tool(
                name="list_jobs",
                description=(
                    "Enumerate all known cron jobs with last-run summary. "
                    "Returns id, name, schedule, last run time + status, runs/successes "
                    "in last 24h, silent-fail count, overdue flag."
                ),
                inputSchema={"type": "object", "properties": {}, "required": []},
            ),
            Tool(
                name="get_job_status",
                description=(
                    "Detailed status for one job: last run, last success, success rates "
                    "over 24h + 7d, overdue state, silent-fail indicators on the last run."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string", "description": "Job identifier from list_jobs"}
                    },
                    "required": ["job_id"],
                },
            ),
            Tool(
                name="get_job_runs",
                description=(
                    "Recent run history for a job (newest first) with timing, exit code, "
                    "status, silent-fail indicators, output snippet."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string", "description": "Job identifier"},
                        "limit": {
                            "type": "integer",
                            "description": "Max runs to return (default 20, max 500)",
                            "default": 20,
                        },
                    },
                    "required": ["job_id"],
                },
            ),
            Tool(
                name="find_overdue_jobs",
                description=(
                    "Returns jobs whose schedule indicates they should have run but "
                    "haven't, beyond a grace window."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "grace_minutes": {
                            "type": "integer",
                            "description": "Tolerance to avoid flagging jobs about to run (default 5)",
                            "default": 5,
                        }
                    },
                    "required": [],
                },
            ),
            Tool(
                name="find_silent_failures",
                description=(
                    "Jobs that returned exit code 0 but output was flagged by silent-fail "
                    "rules (empty output, length anomaly, error keywords, duration anomaly)."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "window_hours": {
                            "type": "integer",
                            "description": "Lookback window in hours (default 24)",
                            "default": 24,
                        }
                    },
                    "required": [],
                },
            ),
            Tool(
                name="tail_job_logs",
                description="Most recent N log lines for a job (newest last).",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "job_id": {"type": "string"},
                        "lines": {"type": "integer", "default": 50},
                    },
                    "required": ["job_id"],
                },
            ),
        ]

    @server.call_tool()  # type: ignore[untyped-decorator]
    async def call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        logger.debug("call_tool name=%s args=%s", name, arguments)

        if name == "list_jobs":
            jobs = await backend.list_jobs()
            response = JobListResponse(jobs=jobs, total=len(jobs))
            return _serialize(response)

        if name == "get_job_status":
            job_id = arguments["job_id"]
            jobs = await backend.list_jobs()
            job = next((j for j in jobs if j.id == job_id), None)
            if job is None:
                return [TextContent(type="text", text=f'{{"error": "Unknown job_id: {job_id}"}}')]
            runs = await backend.get_job_runs(job_id, limit=200)
            status = build_job_status(job, runs)
            return _serialize(status)

        if name == "get_job_runs":
            job_id = arguments["job_id"]
            limit = min(int(arguments.get("limit", 20)), 500)
            runs = await backend.get_job_runs(job_id, limit=limit)
            runs_response = JobRunsResponse(job_id=job_id, runs=runs, total=len(runs))
            return _serialize(runs_response)

        if name == "find_overdue_jobs":
            jobs = await backend.list_jobs()
            overdue = [j for j in jobs if j.is_overdue]
            response = JobListResponse(jobs=overdue, total=len(overdue))
            return _serialize(response)

        if name == "find_silent_failures":
            window_hours = int(arguments.get("window_hours", 24))
            jobs = await backend.list_jobs()
            runs_by_job: dict[str, list[Any]] = {}
            for j in jobs:
                runs_by_job[j.id] = await backend.get_job_runs(j.id, limit=200)
            report = build_silent_failure_report(jobs, runs_by_job, window_hours=window_hours)
            return _serialize(report)

        if name == "tail_job_logs":
            job_id = arguments["job_id"]
            lines = int(arguments.get("lines", 50))
            log_lines = await backend.tail_logs(job_id, lines=lines)
            log_response = JobLogTail(job_id=job_id, lines=log_lines, total_lines_returned=len(log_lines))
            return _serialize(log_response)

        return [TextContent(type="text", text=f'{{"error": "Unknown tool: {name}"}}')]

    # ─────────────────────── Resources ────────────────────────

    @server.list_resources()  # type: ignore[no-untyped-call, untyped-decorator]
    async def list_resources() -> list[Resource]:
        jobs = await backend.list_jobs()
        resources: list[Resource] = [
            Resource(
                uri=AnyUrl("cron://jobs"),
                name="All cron jobs",
                description="JSON list of all known jobs with summary state",
                mimeType="application/json",
            )
        ]
        for j in jobs:
            resources.append(
                Resource(
                    uri=AnyUrl(f"cron://job/{j.id}"),
                    name=f"Job: {j.name}",
                    description=f"Manifest + run history for {j.id}",
                    mimeType="application/json",
                )
            )
        return resources

    @server.read_resource()  # type: ignore[no-untyped-call, untyped-decorator]
    async def read_resource(uri: str) -> str:
        # MCP wraps the URI as an AnyUrl pydantic type at request-deserialize time;
        # coerce back to str before calling string methods on it
        uri_s = str(uri)
        if uri_s == "cron://jobs":
            jobs = await backend.list_jobs()
            return json.dumps({"jobs": [j.model_dump(mode="json") for j in jobs]}, default=str)

        if uri_s.startswith("cron://job/"):
            job_id = uri_s[len("cron://job/"):]
            jobs = await backend.list_jobs()
            job = next((j for j in jobs if j.id == job_id), None)
            if job is None:
                return json.dumps({"error": f"Unknown job_id: {job_id}"})
            runs = await backend.get_job_runs(job_id, limit=100)
            return json.dumps(
                {
                    "job": job.model_dump(mode="json"),
                    "recent_runs": [r.model_dump(mode="json") for r in runs],
                },
                default=str,
            )

        if uri_s.startswith("cron://run/"):
            run_id = uri_s[len("cron://run/"):]
            if not run_id:
                return json.dumps({"error": "cron://run/{id} requires a run_id (got empty)"})
            run = await backend.get_run_by_id(run_id)
            if run is None:
                return json.dumps({"error": f"Unknown run_id: {run_id}"})
            return json.dumps(
                {
                    "run": run.model_dump(mode="json"),
                    "uri": uri_s,
                },
                default=str,
            )

        return json.dumps({"error": f"Unknown resource URI: {uri_s}"})

    # ──────────────────────── Prompts ────────────────────────

    @server.list_prompts()  # type: ignore[no-untyped-call, untyped-decorator]
    async def list_prompts() -> list[Prompt]:
        return [
            Prompt(
                name="diagnose-overdue",
                description="Diagnose why a specific cron job is overdue",
                arguments=[
                    PromptArgument(
                        name="job_id",
                        description="The overdue job's ID",
                        required=True,
                    )
                ],
            ),
            Prompt(
                name="summarize-cron-health",
                description="Daily digest of cron activity, anomalies, and silent failures",
                arguments=[],
            ),
        ]

    @server.get_prompt()  # type: ignore[no-untyped-call, untyped-decorator]
    async def get_prompt(name: str, arguments: dict[str, str] | None = None) -> GetPromptResult:
        arguments = arguments or {}
        if name == "diagnose-overdue":
            job_id = arguments.get("job_id", "<missing>")
            text = (
                f"Job `{job_id}` is overdue. Use the `get_job_status` and "
                f"`get_job_runs` tools to gather: last successful run timestamp, "
                f"recent run history, and any silent-fail indicators. Then propose "
                f"3 corrective actions ranked by likelihood, citing specific evidence "
                f"from the tool responses."
            )
            return GetPromptResult(
                description=f"Diagnostic for overdue job {job_id}",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=text),
                    )
                ],
            )

        if name == "summarize-cron-health":
            text = (
                "Use `list_jobs`, `find_overdue_jobs`, and `find_silent_failures` "
                "to summarize the last 24 hours of cron activity. Highlight: jobs "
                "with silent failures, overdue jobs, and any whose 24h success rate "
                "dropped vs the 7-day baseline. Format as a brief operational digest, "
                "max 200 words. End with the single highest-priority follow-up."
            )
            return GetPromptResult(
                description="Daily cron health digest",
                messages=[
                    PromptMessage(
                        role="user",
                        content=TextContent(type="text", text=text),
                    )
                ],
            )

        return GetPromptResult(
            description=f"Unknown prompt: {name}",
            messages=[
                PromptMessage(
                    role="user",
                    content=TextContent(type="text", text=f"Unknown prompt: {name}"),
                )
            ],
        )

    return server


def _serialize(model: Any) -> list[TextContent]:
    """Pydantic model → MCP TextContent (single block, JSON-serialized)."""
    return [TextContent(type="text", text=model.model_dump_json(indent=2))]

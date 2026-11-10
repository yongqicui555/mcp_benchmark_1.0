"""Tests for the MCP server — protocol wiring, tool registration, response shapes.

These tests verify the server constructs cleanly and registers the expected surface,
without booting the full stdio transport (that's covered by smoke tests).
"""
from __future__ import annotations

import json

import pytest

from silentwatch_mcp.server import build_server


def test_build_server_with_mock_backend_succeeds() -> None:
    server = build_server(backend_name="mock")
    assert server is not None
    assert server.name == "silentwatch"


def test_build_server_with_unknown_backend_raises() -> None:
    with pytest.raises(ValueError) as exc_info:
        build_server(backend_name="nonexistent")
    assert "Unknown backend" in str(exc_info.value)


@pytest.mark.asyncio
async def test_list_tools_registers_six_tools() -> None:
    """All 6 tools per SPEC.md must be registered."""
    server = build_server(backend_name="mock")
    handlers = server.request_handlers
    # The list_tools handler is registered against the ListToolsRequest type
    # We resolve by introspecting registered handlers.
    expected_tools = {
        "list_jobs",
        "get_job_status",
        "get_job_runs",
        "find_overdue_jobs",
        "find_silent_failures",
        "tail_job_logs",
    }
    # Use the server's notification handlers / tool registry to verify
    # If the MCP SDK exposes tools differently across versions, fall back to
    # structural assertion: handlers dict is populated.
    assert handlers, "Server should have registered request handlers"

    # Best-effort: invoke list_tools handler if accessible via registered handler
    from mcp.types import ListToolsRequest

    handler = handlers.get(ListToolsRequest)
    if handler is None:
        pytest.skip(
            "MCP SDK doesn't expose ListToolsRequest handler in this version; "
            "smoke test via stdio transport covers this case."
        )
    result = await handler(ListToolsRequest(method="tools/list"))
    tool_names = {t.name for t in result.root.tools}  # type: ignore[attr-defined]
    assert tool_names == expected_tools


@pytest.mark.asyncio
async def test_call_tool_list_jobs_returns_valid_json() -> None:
    """list_jobs response should be parseable JSON with the JobListResponse shape."""
    from mcp.types import CallToolRequest, CallToolRequestParams

    server = build_server(backend_name="mock")
    handlers = server.request_handlers

    handler = handlers.get(CallToolRequest)
    if handler is None:
        pytest.skip("MCP SDK doesn't expose CallToolRequest handler in this version")

    request = CallToolRequest(
        method="tools/call",
        params=CallToolRequestParams(name="list_jobs", arguments={}),
    )
    result = await handler(request)
    # Response is wrapped in result.root.content per MCP types
    content = result.root.content  # type: ignore[attr-defined]
    assert len(content) == 1
    parsed = json.loads(content[0].text)
    assert "jobs" in parsed
    assert "total" in parsed
    assert isinstance(parsed["jobs"], list)
    assert parsed["total"] == len(parsed["jobs"])


# ─────── Coverage gap fillers (overnight Phase 1B) ───────


@pytest.mark.asyncio
async def test_call_tool_get_job_status() -> None:
    """Coverage: server.py:143-151 — get_job_status dispatch."""
    from mcp.types import CallToolRequest, CallToolRequestParams

    server = build_server(backend_name="mock")
    handler = server.request_handlers[CallToolRequest]
    # Call list_jobs first to find an existing job_id
    list_result = await handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(name="list_jobs", arguments={}),
        )
    )
    jobs_payload = json.loads(list_result.root.content[0].text)
    assert jobs_payload["jobs"], "mock backend should expose at least one job"
    job_id = jobs_payload["jobs"][0]["id"]

    # Now call get_job_status
    result = await handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(
                name="get_job_status", arguments={"job_id": job_id}
            ),
        )
    )
    parsed = json.loads(result.root.content[0].text)
    # Response should be a JobStatus shape with the job + recent runs / state
    assert "id" in parsed or "job" in parsed or "job_id" in parsed


@pytest.mark.asyncio
async def test_call_tool_get_job_status_unknown_id() -> None:
    """Coverage: server.py:147-148 — unknown job_id returns error."""
    from mcp.types import CallToolRequest, CallToolRequestParams

    server = build_server(backend_name="mock")
    handler = server.request_handlers[CallToolRequest]
    result = await handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(
                name="get_job_status", arguments={"job_id": "no-such-job-12345"}
            ),
        )
    )
    parsed = json.loads(result.root.content[0].text)
    assert "error" in parsed
    assert "no-such-job-12345" in parsed["error"]


@pytest.mark.asyncio
async def test_call_tool_get_job_runs() -> None:
    """Coverage: server.py:153-158 — get_job_runs dispatch."""
    from mcp.types import CallToolRequest, CallToolRequestParams

    server = build_server(backend_name="mock")
    handler = server.request_handlers[CallToolRequest]
    list_result = await handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(name="list_jobs", arguments={}),
        )
    )
    jobs_payload = json.loads(list_result.root.content[0].text)
    job_id = jobs_payload["jobs"][0]["id"]

    result = await handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(
                name="get_job_runs", arguments={"job_id": job_id, "limit": 10}
            ),
        )
    )
    parsed = json.loads(result.root.content[0].text)
    assert "runs" in parsed
    assert "job_id" in parsed
    assert parsed["job_id"] == job_id


@pytest.mark.asyncio
async def test_call_tool_find_overdue_jobs() -> None:
    """Coverage: server.py:160-164 — find_overdue_jobs dispatch."""
    from mcp.types import CallToolRequest, CallToolRequestParams

    server = build_server(backend_name="mock")
    handler = server.request_handlers[CallToolRequest]
    result = await handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(name="find_overdue_jobs", arguments={}),
        )
    )
    parsed = json.loads(result.root.content[0].text)
    assert "jobs" in parsed
    assert "total" in parsed
    # All returned jobs (if any) should be overdue
    for j in parsed["jobs"]:
        assert j.get("is_overdue") is True


@pytest.mark.asyncio
async def test_call_tool_find_silent_failures() -> None:
    """Coverage: server.py:166-173 — find_silent_failures dispatch."""
    from mcp.types import CallToolRequest, CallToolRequestParams

    server = build_server(backend_name="mock")
    handler = server.request_handlers[CallToolRequest]
    result = await handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(
                name="find_silent_failures", arguments={"window_hours": 24}
            ),
        )
    )
    parsed = json.loads(result.root.content[0].text)
    # Report should have a structured shape — either silent_failures list or report fields
    assert isinstance(parsed, dict)


@pytest.mark.asyncio
async def test_call_tool_tail_job_logs() -> None:
    """Coverage: server.py:175-180 — tail_job_logs dispatch."""
    from mcp.types import CallToolRequest, CallToolRequestParams

    server = build_server(backend_name="mock")
    handler = server.request_handlers[CallToolRequest]
    list_result = await handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(name="list_jobs", arguments={}),
        )
    )
    jobs_payload = json.loads(list_result.root.content[0].text)
    job_id = jobs_payload["jobs"][0]["id"]

    result = await handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(
                name="tail_job_logs", arguments={"job_id": job_id, "lines": 20}
            ),
        )
    )
    parsed = json.loads(result.root.content[0].text)
    assert "lines" in parsed
    assert "job_id" in parsed


@pytest.mark.asyncio
async def test_call_tool_unknown_returns_error() -> None:
    """Coverage: server.py:182 — unknown tool fallback."""
    from mcp.types import CallToolRequest, CallToolRequestParams

    server = build_server(backend_name="mock")
    handler = server.request_handlers[CallToolRequest]
    result = await handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(name="not_a_real_tool", arguments={}),
        )
    )
    parsed = json.loads(result.root.content[0].text)
    assert "error" in parsed


@pytest.mark.asyncio
async def test_list_resources_includes_jobs_uri() -> None:
    """Coverage: server.py:186-206 — list_resources dispatch."""
    from mcp.types import ListResourcesRequest

    server = build_server(backend_name="mock")
    handler = server.request_handlers[ListResourcesRequest]
    result = await handler(ListResourcesRequest(method="resources/list"))
    uris = {str(r.uri) for r in result.root.resources}
    assert "cron://jobs" in uris
    # Mock backend should expose at least one per-job resource
    per_job = [u for u in uris if u.startswith("cron://job/")]
    assert len(per_job) >= 1


@pytest.mark.asyncio
async def test_read_resource_jobs_root() -> None:
    """Coverage: server.py:210-212 — cron://jobs URI dispatch."""
    from mcp.types import ReadResourceRequest, ReadResourceRequestParams
    from pydantic import AnyUrl

    server = build_server(backend_name="mock")
    handler = server.request_handlers[ReadResourceRequest]
    result = await handler(
        ReadResourceRequest(
            method="resources/read",
            params=ReadResourceRequestParams(uri=AnyUrl("cron://jobs")),
        )
    )
    text = result.root.contents[0].text
    parsed = json.loads(text)
    assert "jobs" in parsed
    assert isinstance(parsed["jobs"], list)


@pytest.mark.asyncio
async def test_read_resource_specific_job() -> None:
    """Coverage: server.py:214-227 — cron://job/{id} URI dispatch."""
    from mcp.types import (
        CallToolRequest,
        CallToolRequestParams,
        ReadResourceRequest,
        ReadResourceRequestParams,
    )
    from pydantic import AnyUrl

    server = build_server(backend_name="mock")
    list_handler = server.request_handlers[CallToolRequest]
    list_result = await list_handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(name="list_jobs", arguments={}),
        )
    )
    job_id = json.loads(list_result.root.content[0].text)["jobs"][0]["id"]

    handler = server.request_handlers[ReadResourceRequest]
    result = await handler(
        ReadResourceRequest(
            method="resources/read",
            params=ReadResourceRequestParams(uri=AnyUrl(f"cron://job/{job_id}")),
        )
    )
    parsed = json.loads(result.root.contents[0].text)
    assert "job" in parsed
    assert "recent_runs" in parsed


@pytest.mark.asyncio
async def test_read_resource_unknown_job_returns_error() -> None:
    """Coverage: server.py:217-219 — unknown job_id in resource URI."""
    from mcp.types import ReadResourceRequest, ReadResourceRequestParams
    from pydantic import AnyUrl

    server = build_server(backend_name="mock")
    handler = server.request_handlers[ReadResourceRequest]
    result = await handler(
        ReadResourceRequest(
            method="resources/read",
            params=ReadResourceRequestParams(uri=AnyUrl("cron://job/no-such-job-id")),
        )
    )
    parsed = json.loads(result.root.contents[0].text)
    assert "error" in parsed


@pytest.mark.asyncio
async def test_read_resource_run_unknown_id_returns_error() -> None:
    """v1.0.7: cron://run/{id} returns error when id doesn't match any known run."""
    from mcp.types import ReadResourceRequest, ReadResourceRequestParams
    from pydantic import AnyUrl

    server = build_server(backend_name="mock")
    handler = server.request_handlers[ReadResourceRequest]
    result = await handler(
        ReadResourceRequest(
            method="resources/read",
            params=ReadResourceRequestParams(uri=AnyUrl("cron://run/not-a-real-run-id")),
        )
    )
    parsed = json.loads(result.root.contents[0].text)
    assert "error" in parsed
    assert "not-a-real-run-id" in parsed["error"]


@pytest.mark.asyncio
async def test_read_resource_run_returns_real_run_v107() -> None:
    """v1.0.7: cron://run/{id} returns the actual run record when id matches.

    This was a placeholder error in v1.0.0–v1.0.6 ('not yet implemented'). v1.0.7
    backs the resource by a default get_run_by_id method on CronBackend that scans
    all jobs' run histories.
    """
    from mcp.types import (
        CallToolRequest,
        CallToolRequestParams,
        ReadResourceRequest,
        ReadResourceRequestParams,
    )
    from pydantic import AnyUrl

    server = build_server(backend_name="mock")
    # First, list jobs and grab a real run_id from the mock backend
    tool_handler = server.request_handlers[CallToolRequest]
    list_runs_result = await tool_handler(
        CallToolRequest(
            method="tools/call",
            params=CallToolRequestParams(
                name="get_job_runs",
                arguments={"job_id": "web-search-refresh", "limit": 5},
            ),
        )
    )
    runs_payload = json.loads(list_runs_result.root.content[0].text)
    real_run_id = runs_payload["runs"][0]["run_id"]

    # Now request the per-run resource for that real id
    handler = server.request_handlers[ReadResourceRequest]
    result = await handler(
        ReadResourceRequest(
            method="resources/read",
            params=ReadResourceRequestParams(uri=AnyUrl(f"cron://run/{real_run_id}")),
        )
    )
    parsed = json.loads(result.root.contents[0].text)
    assert "error" not in parsed, f"unexpected error: {parsed}"
    assert "run" in parsed
    assert parsed["run"]["run_id"] == real_run_id
    assert parsed["uri"] == f"cron://run/{real_run_id}"


@pytest.mark.asyncio
async def test_read_resource_run_empty_id_returns_error() -> None:
    """v1.0.7: cron://run/ (empty id) returns a clear error, not a crash."""
    from mcp.types import ReadResourceRequest, ReadResourceRequestParams
    from pydantic import AnyUrl

    server = build_server(backend_name="mock")
    handler = server.request_handlers[ReadResourceRequest]
    result = await handler(
        ReadResourceRequest(
            method="resources/read",
            params=ReadResourceRequestParams(uri=AnyUrl("cron://run/")),
        )
    )
    parsed = json.loads(result.root.contents[0].text)
    assert "error" in parsed


@pytest.mark.asyncio
async def test_read_resource_unknown_uri_returns_error() -> None:
    """Coverage: server.py:233 — unknown URI fallback."""
    from mcp.types import ReadResourceRequest, ReadResourceRequestParams
    from pydantic import AnyUrl

    server = build_server(backend_name="mock")
    handler = server.request_handlers[ReadResourceRequest]
    result = await handler(
        ReadResourceRequest(
            method="resources/read",
            params=ReadResourceRequestParams(uri=AnyUrl("cron://does-not-exist")),
        )
    )
    parsed = json.loads(result.root.contents[0].text)
    assert "error" in parsed


@pytest.mark.asyncio
async def test_list_prompts_returns_two() -> None:
    """Coverage: server.py:237-256 — list_prompts."""
    from mcp.types import ListPromptsRequest

    server = build_server(backend_name="mock")
    handler = server.request_handlers[ListPromptsRequest]
    result = await handler(ListPromptsRequest(method="prompts/list"))
    names = {p.name for p in result.root.prompts}
    assert names == {"diagnose-overdue", "summarize-cron-health"}


@pytest.mark.asyncio
@pytest.mark.parametrize("prompt_name", ["diagnose-overdue", "summarize-cron-health"])
async def test_get_prompt_returns_walkthrough_text(prompt_name: str) -> None:
    """Coverage: server.py:260-296 — both prompts dispatch."""
    from mcp.types import GetPromptRequest, GetPromptRequestParams

    server = build_server(backend_name="mock")
    handler = server.request_handlers[GetPromptRequest]
    args: dict[str, str] = {}
    if prompt_name == "diagnose-overdue":
        args = {"job_id": "test-job"}
    result = await handler(
        GetPromptRequest(
            method="prompts/get",
            params=GetPromptRequestParams(name=prompt_name, arguments=args),
        )
    )
    text = result.root.messages[0].content.text
    assert len(text) > 50


@pytest.mark.asyncio
async def test_get_prompt_unknown_returns_unknown() -> None:
    """Coverage: server.py:298 — unknown prompt fallback."""
    from mcp.types import GetPromptRequest, GetPromptRequestParams

    server = build_server(backend_name="mock")
    handler = server.request_handlers[GetPromptRequest]
    result = await handler(
        GetPromptRequest(
            method="prompts/get",
            params=GetPromptRequestParams(name="not-a-real-prompt", arguments={}),
        )
    )
    text = result.root.messages[0].content.text
    assert "Unknown prompt" in text or "not-a-real-prompt" in text

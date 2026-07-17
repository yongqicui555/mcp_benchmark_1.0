"""Tests for MinuetClient URL/param construction and error paths."""

from __future__ import annotations

import httpx
import pytest
import respx

from minuet_mcp.client import DEFAULT_BASE_URL, USER_AGENT, MinuetClient


def test_base_url_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("MINUET_API_URL", raising=False)
    assert MinuetClient().base_url == DEFAULT_BASE_URL


def test_base_url_env_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINUET_API_URL", "http://localhost:5000/")
    # Trailing slash should be stripped.
    assert MinuetClient().base_url == "http://localhost:5000"


def test_base_url_explicit_wins(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("MINUET_API_URL", "http://env.example")
    assert MinuetClient(base_url="http://explicit.example").base_url == "http://explicit.example"


@respx.mock
async def test_list_agents_builds_params() -> None:
    route = respx.get("https://minuet.ai/api/agents").mock(
        return_value=httpx.Response(200, json={"agents": []})
    )
    client = MinuetClient(base_url="https://minuet.ai")
    await client.list_agents(name="foo", active=True, limit=5)

    assert route.called
    request = route.calls.last.request
    assert request.url.params["name"] == "foo"
    assert request.url.params["active"] == "true"
    assert request.url.params["limit"] == "5"


@respx.mock
async def test_list_agents_omits_unset_params() -> None:
    route = respx.get("https://minuet.ai/api/agents").mock(
        return_value=httpx.Response(200, json={"agents": []})
    )
    await MinuetClient(base_url="https://minuet.ai").list_agents()

    assert route.called
    # No params should be attached when all args are None.
    assert str(route.calls.last.request.url) == "https://minuet.ai/api/agents"


@respx.mock
async def test_get_agent_url() -> None:
    route = respx.get("https://minuet.ai/api/agent/1:6817").mock(
        return_value=httpx.Response(200, json={"id": "1:6817"})
    )
    result = await MinuetClient(base_url="https://minuet.ai").get_agent("1:6817")

    assert route.called
    assert result == {"id": "1:6817"}


def test_user_agent_format() -> None:
    assert USER_AGENT.startswith("minuet-mcp/")
    # When installed via pyproject, version should be non-empty and numeric-ish.
    _, _, ver = USER_AGENT.partition("/")
    assert ver and ver != "0.0.0+local", "expected installed package version"


@respx.mock
async def test_user_agent_header_sent() -> None:
    route = respx.get("https://minuet.ai/api/relationships").mock(
        return_value=httpx.Response(200, json={"relationships": []})
    )
    await MinuetClient(base_url="https://minuet.ai").list_relationships()

    assert route.called
    assert route.calls.last.request.headers["user-agent"] == USER_AGENT


@respx.mock
async def test_http_error_propagates() -> None:
    respx.get("https://minuet.ai/api/agent/missing").mock(
        return_value=httpx.Response(404, json={"error": "not found"})
    )
    with pytest.raises(httpx.HTTPStatusError):
        await MinuetClient(base_url="https://minuet.ai").get_agent("missing")

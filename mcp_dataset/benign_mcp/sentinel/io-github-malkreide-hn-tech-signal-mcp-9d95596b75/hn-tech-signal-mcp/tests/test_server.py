"""Tests for hn-tech-signal-mcp server.

Run unit tests (no network):
    PYTHONPATH=src pytest tests/ -m "not live"

Run live integration tests:
    PYTHONPATH=src pytest tests/ -m "live"
"""

import json
from unittest.mock import MagicMock

import pytest

# ---------------------------------------------------------------------------
# Unit tests – no network calls
# ---------------------------------------------------------------------------


def test_imports():
    """Server module imports cleanly."""
    from hn_tech_signal_mcp.server import main, server

    assert server is not None
    assert callable(main)


def test_version():
    """Package version is defined."""
    import hn_tech_signal_mcp

    assert hn_tech_signal_mcp.__version__ == "0.2.1"


def test_constants():
    """Key constants are defined."""
    from hn_tech_signal_mcp.server import (
        ARXIV_AI_CATEGORIES,
        ARXIV_BASE_URL,
        GITHUB_BASE_URL,
        HN_BASE_URL,
        LOBSTERS_BASE_URL,
    )

    assert "hacker-news.firebaseio.com" in HN_BASE_URL
    assert "arxiv.org" in ARXIV_BASE_URL
    assert "lobste.rs" in LOBSTERS_BASE_URL
    assert "github.com" in GITHUB_BASE_URL
    assert "cs.AI" in ARXIV_AI_CATEGORIES
    assert "cs.LG" in ARXIV_AI_CATEGORIES
    assert "cs.CL" in ARXIV_AI_CATEGORIES


def test_ts_to_iso():
    """Timestamp conversion works."""
    from hn_tech_signal_mcp.server import _ts_to_iso

    # Real-world timestamp → formatted date
    result = _ts_to_iso(1700000000)
    assert "2023" in result
    assert "UTC" in result
    # None and 0 (falsy) → "unknown"
    assert _ts_to_iso(None) == "unknown"
    assert _ts_to_iso(0) == "unknown"


def test_handle_error_timeout():
    """Error handler formats timeout errors."""
    import httpx

    from hn_tech_signal_mcp.server import _handle_error

    e = httpx.TimeoutException("timed out")
    result = _handle_error(e)
    assert "timed out" in result.lower() or "timeout" in result.lower()


def test_handle_error_rate_limit():
    """Error handler advises on rate limits."""
    import httpx

    from hn_tech_signal_mcp.server import _handle_error

    mock_response = MagicMock()
    mock_response.status_code = 429
    e = httpx.HTTPStatusError("rate limited", request=MagicMock(), response=mock_response)
    result = _handle_error(e)
    assert "rate limit" in result.lower() or "429" in result


def test_format_hn_story():
    """HN story formatter produces expected fields."""
    from hn_tech_signal_mcp.server import _format_hn_story

    story = {
        "id": 12345,
        "title": "Test Story",
        "url": "https://example.com",
        "score": 42,
        "descendants": 7,
        "by": "testuser",
        "time": 1700000000,
    }
    result = _format_hn_story(story)
    assert result["id"] == 12345
    assert result["title"] == "Test Story"
    assert result["score"] == 42
    assert result["comments"] == 7
    assert "ycombinator.com" in result["hn_link"]


def test_cache_set_and_get():
    """Cache stores and retrieves values within TTL."""
    from hn_tech_signal_mcp.server import _cache_get, _cache_set

    _cache_set("test_key_unit", "test_value")
    result = _cache_get("test_key_unit", "hn_top")
    assert result == "test_value"


def test_cache_miss():
    """Cache returns None for unknown key."""
    from hn_tech_signal_mcp.server import _cache_get

    result = _cache_get("nonexistent_key_xyz_123", "hn_top")
    assert result is None


# Pydantic input validation tests


def test_hn_top_stories_input_defaults():
    from hn_tech_signal_mcp.server import HnTopStoriesInput

    m = HnTopStoriesInput()
    assert m.feed == "top"
    assert m.limit == 10
    assert m.min_score == 0


def test_hn_top_stories_input_invalid_feed():
    from pydantic import ValidationError

    from hn_tech_signal_mcp.server import HnTopStoriesInput

    with pytest.raises(ValidationError):
        HnTopStoriesInput(feed="invalid")


def test_arxiv_latest_input_invalid_category():
    from pydantic import ValidationError

    from hn_tech_signal_mcp.server import ArxivLatestInput

    with pytest.raises(ValidationError):
        ArxivLatestInput(categories=["not.a.cat"])


def test_arxiv_latest_input_valid():
    from hn_tech_signal_mcp.server import ArxivLatestInput

    m = ArxivLatestInput(categories=["cs.AI", "cs.CL"])
    assert "cs.AI" in m.categories


def test_github_input_invalid_sort():
    from pydantic import ValidationError

    from hn_tech_signal_mcp.server import GithubTrendingAiInput

    with pytest.raises(ValidationError):
        GithubTrendingAiInput(sort="popularity")


def test_hn_search_input_empty_query():
    from pydantic import ValidationError

    from hn_tech_signal_mcp.server import HnSearchInput

    with pytest.raises(ValidationError):
        HnSearchInput(query="")


# ---------------------------------------------------------------------------
# SEC-004 regression: arxiv_search.category must be whitelisted
# ---------------------------------------------------------------------------


def test_arxiv_search_input_invalid_category():
    from pydantic import ValidationError

    from hn_tech_signal_mcp.server import ArxivSearchInput

    with pytest.raises(ValidationError):
        ArxivSearchInput(query="LLM", category="not.a.cat")


def test_arxiv_search_input_valid_category():
    from hn_tech_signal_mcp.server import ArxivSearchInput

    m = ArxivSearchInput(query="LLM", category="cs.AI")
    assert m.category == "cs.AI"


def test_arxiv_search_input_empty_category_is_none():
    """Empty string should normalize to None for backwards compatibility."""
    from hn_tech_signal_mcp.server import ArxivSearchInput

    m = ArxivSearchInput(query="LLM", category="")
    assert m.category is None


# ---------------------------------------------------------------------------
# SCALE-001 regression: cache is LRU-bounded
# ---------------------------------------------------------------------------


def test_cache_evicts_oldest_when_full():
    from hn_tech_signal_mcp import server

    server._cache.clear()
    for i in range(server._CACHE_MAX_ENTRIES + 50):
        server._cache_set(f"k{i}", i)
    assert len(server._cache) == server._CACHE_MAX_ENTRIES
    assert "k0" not in server._cache
    assert f"k{server._CACHE_MAX_ENTRIES + 49}" in server._cache
    server._cache.clear()


# ---------------------------------------------------------------------------
# SDK-002 regression: server symbol exported, mcp removed
# ---------------------------------------------------------------------------


def test_server_symbol_replaces_mcp():
    from hn_tech_signal_mcp import server as srv

    assert hasattr(srv, "server")
    assert not hasattr(srv, "mcp")


# ---------------------------------------------------------------------------
# SDK-001 regression: no usage of deprecated datetime.utcnow()
# ---------------------------------------------------------------------------


def test_no_datetime_utcnow_in_source():
    """datetime.utcnow() is deprecated in Python 3.12+; ensure it's gone."""
    from pathlib import Path

    src = Path(__file__).parent.parent / "src" / "hn_tech_signal_mcp" / "server.py"
    assert "datetime.utcnow" not in src.read_text(), "datetime.utcnow() reintroduced"


def test_now_iso_is_timezone_aware():
    from hn_tech_signal_mcp.server import _now_iso

    s = _now_iso()
    assert s.endswith(" UTC")
    assert len(s) == len("YYYY-MM-DD HH:MM UTC")


# ---------------------------------------------------------------------------
# SEC-003 regression: XML parsing uses defusedxml
# ---------------------------------------------------------------------------


def test_xml_parser_is_defused():
    """arXiv XML must be parsed with defusedxml, not stdlib xml.etree."""
    from hn_tech_signal_mcp import server

    assert server._DefusedET.__name__.startswith("defusedxml"), (
        f"Expected defusedxml, got {server._DefusedET.__name__}"
    )


# ---------------------------------------------------------------------------
# OBS-001 regression: errors are logged
# ---------------------------------------------------------------------------


def test_handle_error_logs_warning(caplog):
    import logging

    import httpx

    from hn_tech_signal_mcp.server import _handle_error

    caplog.set_level(logging.WARNING, logger="hn-tech-signal-mcp")
    _handle_error(httpx.TimeoutException("test timeout"), source="UnitTest")
    assert any("UnitTest" in r.message and "TimeoutException" in r.message for r in caplog.records)


# ---------------------------------------------------------------------------
# SEC-001 regression: GITHUB_TOKEN must only be sent to api.github.com
# ---------------------------------------------------------------------------


def test_github_token_only_sent_to_github(monkeypatch):
    """Bearer header must only attach to github.com URLs."""
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_test_secret")
    from hn_tech_signal_mcp.server import GITHUB_BASE_URL, _headers_for

    for foreign in (
        "https://hacker-news.firebaseio.com/v0/topstories.json",
        "https://hn.algolia.com/api/v1/search",
        "https://export.arxiv.org/api/query",
        "https://lobste.rs/hottest.json",
    ):
        assert "Authorization" not in _headers_for(foreign), foreign

    gh = _headers_for(f"{GITHUB_BASE_URL}/search/repositories")
    assert gh["Authorization"] == "Bearer ghp_test_secret"


def test_no_auth_header_without_token(monkeypatch):
    """Without GITHUB_TOKEN no Authorization header anywhere."""
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    from hn_tech_signal_mcp.server import GITHUB_BASE_URL, _headers_for

    assert "Authorization" not in _headers_for(f"{GITHUB_BASE_URL}/search/repositories")
    assert "Authorization" not in _headers_for("https://export.arxiv.org/api/query")


# ---------------------------------------------------------------------------
# SEC-002 regression: streamable_http refuses public bind without bearer
# ---------------------------------------------------------------------------


def test_http_default_binds_loopback(monkeypatch):
    monkeypatch.delenv("MCP_HOST", raising=False)
    monkeypatch.delenv("MCP_PORT", raising=False)
    from hn_tech_signal_mcp.server import _resolve_http_bind

    host, port = _resolve_http_bind()
    assert host == "127.0.0.1"
    assert port == 8000


def test_http_refuses_public_bind_without_bearer(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.delenv("MCP_BEARER_TOKEN", raising=False)
    from hn_tech_signal_mcp.server import _resolve_http_bind

    with pytest.raises(RuntimeError, match="MCP_BEARER_TOKEN"):
        _resolve_http_bind()


def test_http_allows_public_bind_with_bearer(monkeypatch):
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_BEARER_TOKEN", "secret-xyz")
    from hn_tech_signal_mcp.server import _resolve_http_bind

    host, _ = _resolve_http_bind()
    assert host == "0.0.0.0"


def test_seven_tools_registered():
    """All 7 tools are registered on the server."""
    from hn_tech_signal_mcp.server import server

    tool_names = [t.name for t in server._tool_manager.list_tools()]
    expected = {
        "hn_top_stories",
        "hn_search",
        "arxiv_latest",
        "arxiv_search",
        "lobsters_hot",
        "github_trending_ai",
        "tech_signal_digest",
    }
    assert expected == set(tool_names), f"Unexpected tools: {set(tool_names) ^ expected}"


# ---------------------------------------------------------------------------
# Live integration tests – require network
# ---------------------------------------------------------------------------


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_hn_top_stories():
    """Live: fetch HN top stories."""
    from hn_tech_signal_mcp.server import HnTopStoriesInput, hn_top_stories

    result = await hn_top_stories(HnTopStoriesInput(limit=3))
    data = json.loads(result)
    assert data["count"] > 0
    assert len(data["stories"]) > 0
    assert data["stories"][0]["title"]


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_hn_search():
    """Live: search HN for AI content."""
    from hn_tech_signal_mcp.server import HnSearchInput, hn_search

    result = await hn_search(HnSearchInput(query="large language models", limit=3, days_back=30))
    data = json.loads(result)
    assert "hits" in data


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_arxiv_latest():
    """Live: fetch latest arXiv cs.AI papers."""
    from hn_tech_signal_mcp.server import ArxivLatestInput, arxiv_latest

    result = await arxiv_latest(ArxivLatestInput(categories=["cs.AI"], limit=3))
    data = json.loads(result)
    assert data["total_papers"] > 0
    papers = data["by_category"]["cs.AI"]
    assert len(papers) > 0
    assert papers[0]["title"]


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_arxiv_search():
    """Live: search arXiv for LLM papers."""
    from hn_tech_signal_mcp.server import ArxivSearchInput, arxiv_search

    result = await arxiv_search(ArxivSearchInput(query="LLM agents", limit=3))
    data = json.loads(result)
    assert data["count"] > 0


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_lobsters_hot():
    """Live: fetch Lobste.rs hottest stories."""
    from hn_tech_signal_mcp.server import LobstersHotInput, lobsters_hot

    result = await lobsters_hot(LobstersHotInput(limit=5))
    data = json.loads(result)
    assert data["count"] > 0
    assert data["stories"][0]["title"]


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_github_trending():
    """Live: fetch trending LLM repos on GitHub."""
    from hn_tech_signal_mcp.server import GithubTrendingAiInput, github_trending_ai

    result = await github_trending_ai(GithubTrendingAiInput(topic="llm", limit=3, min_stars=100))
    data = json.loads(result)
    assert data["count"] > 0
    assert data["repos"][0]["stars"] >= 100


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_digest():
    """Live: generate tech signal digest."""
    from hn_tech_signal_mcp.server import TechSignalDigestInput, tech_signal_digest

    result = await tech_signal_digest(
        TechSignalDigestInput(
            focus=None, hn_limit=3, arxiv_limit=3, lobsters_limit=3, github_limit=3
        )
    )
    data = json.loads(result)
    assert "sources" in data
    assert "hn" in data["sources"]
    assert "arxiv" in data["sources"]
    assert "lobsters" in data["sources"]
    assert "github" in data["sources"]

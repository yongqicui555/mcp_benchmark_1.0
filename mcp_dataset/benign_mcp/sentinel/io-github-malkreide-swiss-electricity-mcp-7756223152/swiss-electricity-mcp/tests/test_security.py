"""Security-hardening tests (audit Wave 2: SEC-004/005/018/021/022)."""

from __future__ import annotations

import httpx
import pytest
import respx

from swiss_electricity_mcp.api_client import (
    LINDAS_SPARQL,
    EgressNotAllowedError,
    ElComSparqlClient,
    _category_filter,
    _sparql_escape_literal,
    assert_url_allowed,
)
from swiss_electricity_mcp.tool_snapshot import (
    LOCK_PATH,
    build_lock,
    build_snapshot,
)


class TestEgressAllowList:
    """SEC-004 / SEC-005 / SEC-021."""

    def test_allowed_https_host_passes(self):
        assert_url_allowed("https://lindas.admin.ch/query")
        assert_url_allowed("https://opendata.swiss/api/3/action/package_search")

    def test_http_scheme_rejected(self):
        with pytest.raises(EgressNotAllowedError):
            assert_url_allowed("http://lindas.admin.ch/query")

    def test_non_https_schemes_rejected(self):
        for url in ("file:///etc/passwd", "gopher://x", "ftp://lindas.admin.ch/"):
            with pytest.raises(EgressNotAllowedError):
                assert_url_allowed(url)

    def test_unlisted_host_rejected(self):
        with pytest.raises(EgressNotAllowedError):
            assert_url_allowed("https://evil.example.com/steal")

    def test_metadata_endpoint_rejected(self):
        with pytest.raises(EgressNotAllowedError):
            assert_url_allowed("https://169.254.169.254/latest/meta-data/")


class TestSparqlInjection:
    """SEC-018."""

    def test_escape_doubles_backslash_and_quote(self):
        assert _sparql_escape_literal('a"b') == 'a\\"b'
        assert _sparql_escape_literal("a\\b") == "a\\\\b"

    def test_escape_rejects_control_chars(self):
        with pytest.raises(ValueError):
            _sparql_escape_literal("line1\nline2")

    def test_category_filter_whitelists(self):
        assert _category_filter("C3") == 'FILTER(STR(?categoryCode) = "C3")'
        assert _category_filter(None) == ""

    def test_category_filter_rejects_injection(self):
        with pytest.raises(ValueError):
            _category_filter('C3" } INJECT { ?s ?p ?o ')

    async def test_invalid_category_rejected_before_request(self):
        client = ElComSparqlClient()
        with pytest.raises(ValueError):
            # Must raise before any network call happens.
            await client.get_tariffs_by_municipality(bfs_nr=261, category='C3"}')

    @respx.mock
    async def test_canton_is_escaped_in_query(self):
        route = respx.get(LINDAS_SPARQL).mock(
            return_value=httpx.Response(200, json={"results": {"bindings": []}})
        )
        client = ElComSparqlClient()
        await client.get_median_canton(canton='Zuerich" } #')
        sent_query = route.calls.last.request.url.params["query"]
        # The injected double-quote must appear only in escaped form.
        assert '\\"' in sent_query
        assert '"} ' not in sent_query


class TestToolSnapshot:
    """SEC-022 — committed lock must match the live tool surface."""

    async def test_snapshot_matches_committed_lock(self):
        import json

        assert LOCK_PATH.exists(), "tool-definitions.lock.json is missing"
        committed = json.loads(LOCK_PATH.read_text(encoding="utf-8"))
        live = build_lock(await build_snapshot())
        assert live["sha256"] == committed["sha256"], (
            "Tool surface changed without updating the lock. If intentional, run "
            "`python -m swiss_electricity_mcp.tool_snapshot --write`."
        )
        assert live["tool_count"] == committed["tool_count"]

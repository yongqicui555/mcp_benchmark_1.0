"""Wave 5 tests: ARCH-003 (search not-found UX) and ARCH-007 (parallel compare)."""

from __future__ import annotations

import json
from types import SimpleNamespace

import httpx
import respx

from swiss_electricity_mcp.api_client import (
    LINDAS_SPARQL,
    ZURICH_OGD_CKAN,
    CkanDiscoveryClient,
    ElComSparqlClient,
    EnergyDashboardClient,
)
from swiss_electricity_mcp.server import (
    AppContext,
    consumption_search_zurich,
    tariff_compare_municipalities,
)

_ELCOM_ONE_ROW = {
    "results": {
        "bindings": [
            {
                "period": {
                    "value": "2025",
                    "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                },
                "categoryCode": {"value": "C3"},
                "munLabel": {"value": "Zuerich"},
                "total": {
                    "value": "23.45",
                    "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                },
            }
        ]
    }
}


class FakeCtx:
    """Minimal Context stand-in exposing lifespan-scoped clients (ARCH-004)."""

    def __init__(self) -> None:
        self.progress: list[tuple[int, int]] = []
        app = AppContext(
            dashboard=EnergyDashboardClient(),
            elcom=ElComSparqlClient(),
            ckan=CkanDiscoveryClient(),
        )
        self.request_context = SimpleNamespace(lifespan_context=app)

    async def info(self, *args, **kwargs) -> None:
        return None

    async def report_progress(self, progress: int, total: int) -> None:
        self.progress.append((progress, total))


class TestSearchNotFound:
    """ARCH-003 — zero hits must yield match_type=none + an actionable suggestion."""

    @respx.mock
    async def test_zero_hits_returns_suggestion(self):
        respx.get(f"{ZURICH_OGD_CKAN}/package_search").mock(
            return_value=httpx.Response(
                200, json={"success": True, "result": {"count": 0, "results": []}}
            )
        )
        out = await consumption_search_zurich(
            ctx=FakeCtx(), query="zzz-nope", response_format="json"
        )
        payload = json.loads(out)
        assert payload["match_type"] == "none"
        assert payload["suggestion"]
        assert payload["total_hits"] == 0

    @respx.mock
    async def test_hits_have_no_suggestion(self):
        respx.get(f"{ZURICH_OGD_CKAN}/package_search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "result": {
                        "count": 1,
                        "results": [{"name": "ds", "title": "Energie", "resources": []}],
                    },
                },
            )
        )
        payload = json.loads(
            await consumption_search_zurich(
                ctx=FakeCtx(), query="energie", response_format="json"
            )
        )
        assert payload["match_type"] == "results"
        assert payload["suggestion"] is None


class TestParallelCompare:
    """ARCH-007 — compare fetches municipalities concurrently."""

    @respx.mock
    async def test_compare_collects_all_rows_and_reports_progress(self):
        route = respx.get(LINDAS_SPARQL).mock(
            return_value=httpx.Response(200, json=_ELCOM_ONE_ROW)
        )
        ctx = FakeCtx()
        out = await tariff_compare_municipalities(
            ctx=ctx,
            bfs_numbers=[261, 1, 230],
            category="C3",
            period=2025,
            response_format="json",
        )
        payload = json.loads(out)
        assert len(payload["rows"]) == 3  # one row per municipality
        assert route.call_count == 3  # one upstream call each, run concurrently
        assert ctx.progress[-1] == (3, 3)  # progress completed

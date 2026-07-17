"""Live tests for swiss-electricity-mcp — hit the real upstream APIs.

These are excluded from CI (marker `live`). Run them manually / nightly:
    pytest tests/test_live.py -m live -v
"""

from __future__ import annotations

import pytest

from swiss_electricity_mcp.api_client import (
    CkanDiscoveryClient,
    ElComSparqlClient,
    EnergyDashboardClient,
)


@pytest.mark.live
class TestLiveEndpoints:
    async def test_energiedashboard_production_mix_live(self):
        client = EnergyDashboardClient()
        try:
            data, prov, _ = await client.get_production_mix()
            assert prov in {"live_api", "cached"}
            assert any(k.startswith("20") for k in data.keys())
        finally:
            await client.aclose()

    async def test_elcom_zurich_tariffs_live(self):
        client = ElComSparqlClient()
        try:
            bindings, prov, _ = await client.get_tariffs_by_municipality(
                bfs_nr=261, period_from=2019, period_to=2025, limit=10
            )
            assert prov in {"sparql", "cached"}
            assert len(bindings) >= 1
        finally:
            await client.aclose()

    async def test_opendata_swiss_bfe_search_live(self):
        client = CkanDiscoveryClient()
        try:
            data, prov, _ = await client.search_opendata_swiss(
                query="stromverbrauch", bfe_only=True
            )
            assert prov in {"live_api", "cached"}
            assert data.get("success") is True
        finally:
            await client.aclose()

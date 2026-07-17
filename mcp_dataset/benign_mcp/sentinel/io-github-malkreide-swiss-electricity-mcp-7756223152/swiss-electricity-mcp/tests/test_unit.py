"""Unit tests for swiss-electricity-mcp (mocked upstreams, CI default).

    pytest -m "not live"

Live tests live in tests/test_live.py.
"""

from __future__ import annotations

import asyncio

import httpx
import pytest
import respx

from swiss_electricity_mcp.api_client import (
    DASHBOARD_BASE,
    LINDAS_SPARQL,
    OPENDATA_SWISS_CKAN,
    CkanDiscoveryClient,
    ElComSparqlClient,
    EnergyDashboardClient,
    UpstreamUnreachableError,
    sparql_value,
)
from swiss_electricity_mcp.models import (
    ATTRIBUTION_BFE,
    ATTRIBUTION_ELCOM,
    ATTRIBUTION_OPENDATA_SWISS,
    ATTRIBUTION_ZURICH,
    ProductionMixResponse,
    TariffObservation,
)

# ============================================================================
# Fixtures
# ============================================================================

PRODUCTION_MIX_PAYLOAD = {
    "2022": {
        "kumuliertKernkraft": 23.1,
        "kumuliertFlusskraft": 15.5,
        "kumuliertSpeicherkraft": 18.0,
        "kumuliertWind": 0.1,
        "kumuliertPhotovoltaik": 4.1,
        "kumuliertThermische": 3.7,
        "kumuliertEigenproduktion": 64.5,
        "anteilKernkraft": 35.82,
        "anteilFlusskraft": 24.01,
        "anteilSpeicherkraft": 27.91,
        "anteilWind": 0.23,
        "anteilPhotovoltaik": 6.3,
        "anteilThermische": 5.72,
    },
    "2023": {
        "kumuliertKernkraft": 23.3,
        "kumuliertPhotovoltaik": 4.9,
        "kumuliertEigenproduktion": 72.7,
    },
}

CONSUMPTION_FORECAST_PAYLOAD = {
    "currentEntry": {
        "landesverbrauchPrognose": 161.4,
        "landesverbrauchPrognoseInFiveDays": 165.8,
        "trend": "down_strong",
        "trendRating": "positiv",
        "date": "2026-05-22",
    },
    "entries": [
        {
            "date": "2026-05-20",
            "landesverbrauchGeschaetzt": 172.3,
            "fiveYearMin": 163.7,
            "fiveYearMax": 184.0,
            "fiveYearMittelwert": 173.2,
        },
    ],
}

ELCOM_TARIFF_SPARQL_RESPONSE = {
    "head": {"vars": ["period", "categoryCode", "operator", "total"]},
    "results": {
        "bindings": [
            {
                "period": {
                    "type": "literal",
                    "value": "2025",
                    "datatype": "http://www.w3.org/2001/XMLSchema#integer",
                },
                "categoryCode": {"type": "literal", "value": "C3"},
                "operator": {
                    "type": "uri",
                    "value": "https://energy.ld.admin.ch/elcom/electricityprice/operator/565",
                },
                "operatorLabel": {"type": "literal", "value": "ewz Stadt Zuerich"},
                "total": {
                    "type": "literal",
                    "value": "23.45",
                    "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                },
                "energy": {
                    "type": "literal",
                    "value": "10.12",
                    "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                },
                "gridusage": {
                    "type": "literal",
                    "value": "8.55",
                    "datatype": "http://www.w3.org/2001/XMLSchema#decimal",
                },
                "munLabel": {"type": "literal", "value": "Zuerich"},
                "productLabel": {"type": "literal", "value": "standard"},
            }
        ]
    },
}


# ============================================================================
# Helpers
# ============================================================================


class TestSparqlValueHelper:
    def test_returns_none_for_missing_key(self):
        assert sparql_value({}, "x") is None

    def test_returns_none_for_empty_value(self):
        assert sparql_value({"x": {"value": ""}}, "x") is None

    def test_coerces_decimal_to_float(self):
        binding = {
            "x": {"value": "23.45", "datatype": "http://www.w3.org/2001/XMLSchema#decimal"}
        }
        assert sparql_value(binding, "x") == 23.45

    def test_coerces_integer(self):
        binding = {
            "x": {"value": "2025", "datatype": "http://www.w3.org/2001/XMLSchema#integer"}
        }
        assert sparql_value(binding, "x") == 2025

    def test_returns_string_when_no_datatype(self):
        assert sparql_value({"x": {"value": "Zuerich"}}, "x") == "Zuerich"


# ============================================================================
# Happy-path tests
# ============================================================================


class TestEnergyDashboardClient:
    @respx.mock
    async def test_production_mix_happy_path(self):
        respx.get(f"{DASHBOARD_BASE}/strom/strom-produktionsmix").mock(
            return_value=httpx.Response(200, json=PRODUCTION_MIX_PAYLOAD)
        )
        client = EnergyDashboardClient()
        try:
            data, prov, retrieved = await client.get_production_mix()
            assert prov == "live_api"
            assert data["2022"]["kumuliertKernkraft"] == 23.1
            assert retrieved.endswith("Z")
        finally:
            await client.aclose()

    @respx.mock
    async def test_cache_hit_returns_cached_provenance(self):
        respx.get(f"{DASHBOARD_BASE}/strom/strom-produktionsmix").mock(
            return_value=httpx.Response(200, json=PRODUCTION_MIX_PAYLOAD)
        )
        client = EnergyDashboardClient()
        try:
            _, prov1, _ = await client.get_production_mix()
            _, prov2, _ = await client.get_production_mix()
            assert prov1 == "live_api"
            assert prov2 == "cached"
        finally:
            await client.aclose()

    @respx.mock
    async def test_consumption_forecast(self):
        respx.get(
            f"{DASHBOARD_BASE}/strom/v2/strom-verbrauch/landesverbrauch-mit-prognose"
        ).mock(return_value=httpx.Response(200, json=CONSUMPTION_FORECAST_PAYLOAD))
        client = EnergyDashboardClient()
        try:
            data, _, _ = await client.get_consumption_forecast()
            assert data["currentEntry"]["landesverbrauchPrognose"] == 161.4
        finally:
            await client.aclose()


class TestElComSparqlClient:
    @respx.mock
    async def test_tariffs_by_municipality_happy(self):
        respx.get(LINDAS_SPARQL).mock(
            return_value=httpx.Response(200, json=ELCOM_TARIFF_SPARQL_RESPONSE)
        )
        client = ElComSparqlClient()
        try:
            bindings, prov, _ = await client.get_tariffs_by_municipality(
                bfs_nr=261, category="C3", period_from=2025, period_to=2025
            )
            assert prov == "sparql"
            assert len(bindings) == 1
            assert sparql_value(bindings[0], "total") == 23.45
        finally:
            await client.aclose()

    def test_categories_include_C3_school_reference(self):
        codes = [c["code"] for c in ElComSparqlClient.CATEGORIES]
        assert "C3" in codes
        c3 = next(c for c in ElComSparqlClient.CATEGORIES if c["code"] == "C3")
        assert "Schule" in c3["desc"]


class TestCkanDiscoveryClient:
    @respx.mock
    async def test_opendata_swiss_search(self):
        respx.get(f"{OPENDATA_SWISS_CKAN}/package_search").mock(
            return_value=httpx.Response(
                200,
                json={
                    "success": True,
                    "result": {
                        "count": 1,
                        "results": [
                            {
                                "name": "ds-1",
                                "title": {"de": "Stromverbrauch Schweiz"},
                                "description": {"de": "BFE-Dataset"},
                                "organization": {"name": "bundesamt-fur-energie-bfe"},
                                "resources": [{"id": "r1"}],
                            }
                        ],
                    },
                },
            )
        )
        client = CkanDiscoveryClient()
        try:
            data, prov, _ = await client.search_opendata_swiss(
                "stromverbrauch", bfe_only=True
            )
            assert prov == "live_api"
            assert data["result"]["count"] == 1
        finally:
            await client.aclose()


# ============================================================================
# Retry tests
# ============================================================================


class TestRetryBehaviour:
    @respx.mock
    async def test_retries_5xx_then_succeeds(self, monkeypatch):
        async def fake_sleep(_):
            return None
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        route = respx.get(f"{DASHBOARD_BASE}/strom/strom-produktionsmix")
        route.side_effect = [
            httpx.Response(503),
            httpx.Response(503),
            httpx.Response(200, json=PRODUCTION_MIX_PAYLOAD),
        ]
        client = EnergyDashboardClient()
        try:
            data, prov, _ = await client.get_production_mix()
            assert prov == "live_api"
            assert "2022" in data
            assert route.call_count == 3
        finally:
            await client.aclose()

    @respx.mock
    async def test_4xx_no_retry(self, monkeypatch):
        async def fake_sleep(_):
            return None
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        route = respx.get(f"{DASHBOARD_BASE}/strom/strom-produktionsmix")
        route.return_value = httpx.Response(404)
        client = EnergyDashboardClient()
        try:
            with pytest.raises(httpx.HTTPStatusError):
                await client.get_production_mix()
            assert route.call_count == 1
        finally:
            await client.aclose()

    @respx.mock
    async def test_429_does_retry(self, monkeypatch):
        async def fake_sleep(_):
            return None
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        route = respx.get(f"{DASHBOARD_BASE}/strom/strom-produktionsmix")
        route.side_effect = [
            httpx.Response(429),
            httpx.Response(200, json=PRODUCTION_MIX_PAYLOAD),
        ]
        client = EnergyDashboardClient()
        try:
            await client.get_production_mix()
            assert route.call_count == 2
        finally:
            await client.aclose()


# ============================================================================
# Timeout tests
# ============================================================================


class TestNetworkErrorHandling:
    @respx.mock
    async def test_timeout_raises_clean_error(self, monkeypatch):
        async def fake_sleep(_):
            return None
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        respx.get(f"{DASHBOARD_BASE}/strom/strom-produktionsmix").mock(
            side_effect=httpx.ConnectTimeout("upstream timeout")
        )
        client = EnergyDashboardClient()
        try:
            with pytest.raises(UpstreamUnreachableError) as exc_info:
                await client.get_production_mix()
            msg = str(exc_info.value)
            # OBS-002: generic message, no leaked internal repr / URL / host.
            assert "temporarily unavailable" in msg
            assert "ConnectTimeout" not in msg
            assert "energiedashboard" not in msg
        finally:
            await client.aclose()

    @respx.mock
    async def test_504_sparql_gateway_timeout_retries(self, monkeypatch):
        async def fake_sleep(_):
            return None
        monkeypatch.setattr(asyncio, "sleep", fake_sleep)
        route = respx.get(LINDAS_SPARQL)
        route.side_effect = [
            httpx.Response(504),
            httpx.Response(504),
            httpx.Response(200, json=ELCOM_TARIFF_SPARQL_RESPONSE),
        ]
        client = ElComSparqlClient()
        try:
            bindings, prov, _ = await client.get_tariffs_by_municipality(bfs_nr=261)
            assert prov == "sparql"
            assert len(bindings) == 1
            assert route.call_count == 3
        finally:
            await client.aclose()


# ============================================================================
# Envelope / attribution contract tests
# ============================================================================


class TestResponseEnvelope:
    def test_envelope_fields_present(self):
        response = ProductionMixResponse(
            source="Test",
            provenance="live_api",
            retrieved_at="2026-05-21T12:00:00Z",
            years=[],
        )
        dumped = response.model_dump()
        assert "source" in dumped
        assert "provenance" in dumped
        assert "retrieved_at" in dumped

    def test_attribution_strings_are_non_empty(self):
        for s in [
            ATTRIBUTION_BFE,
            ATTRIBUTION_ELCOM,
            ATTRIBUTION_OPENDATA_SWISS,
            ATTRIBUTION_ZURICH,
        ]:
            assert isinstance(s, str) and len(s) > 30
            assert "https://" in s

    def test_tariff_observation_validates(self):
        obs = TariffObservation(
            period=2025,
            municipality_bfs_nr=261,
            operator_id="565",
            category="C3",
            product="standard",
            total_rp_per_kwh=23.45,
        )
        assert obs.period == 2025
        assert obs.municipality_bfs_nr == 261

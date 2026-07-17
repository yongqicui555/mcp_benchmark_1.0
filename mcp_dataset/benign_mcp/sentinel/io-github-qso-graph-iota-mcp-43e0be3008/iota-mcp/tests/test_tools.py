"""L2 unit tests for iota-mcp — all 6 tools + helper functions.

Uses IOTA_MCP_MOCK=1 for tool-level tests (no iota-world.org API calls).
Direct unit tests on IOTAClient helper methods.

Test IDs: IOTA-L2-001 through IOTA-L2-045
"""

from __future__ import annotations

import os
import pytest

# Enable mock mode before importing anything
os.environ["IOTA_MCP_MOCK"] = "1"

from iota_mcp.client import IOTAClient


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    """Fresh IOTAClient instance with mock data loaded."""
    c = IOTAClient()
    c._ensure_loaded()
    return c


# ---------------------------------------------------------------------------
# IOTA-L2-001..005: Helper functions
# ---------------------------------------------------------------------------


class TestHelpers:
    def test_center_calculation(self, client):
        """IOTA-L2-001: Center from bounding box."""
        group = {
            "latitude_min": "-44.00", "latitude_max": "-10.00",
            "longitude_min": "113.00", "longitude_max": "154.00",
        }
        lat, lon = client._center(group)
        assert lat == pytest.approx(-27.0, abs=0.1)
        assert lon == pytest.approx(133.5, abs=0.1)

    def test_center_missing_data(self, client):
        """IOTA-L2-002: Missing bbox returns (0, 0)."""
        lat, lon = client._center({})
        assert lat == 0.0
        assert lon == 0.0

    def test_haversine_zero(self):
        """IOTA-L2-003: Same point → 0 km."""
        assert IOTAClient._haversine(0, 0, 0, 0) == 0.0

    def test_haversine_known(self):
        """IOTA-L2-004: Australia center → Hawaii center."""
        dist = IOTAClient._haversine(-27.0, 133.5, 20.5, -157.5)
        assert 8000 < dist < 10000

    def test_island_count(self, client):
        """IOTA-L2-005: Count islands across subgroups."""
        group = client._by_refno["OC-001"]
        assert client._island_count(group) == 2  # Australia + Tasmania


# ---------------------------------------------------------------------------
# IOTA-L2-010..015: lookup()
# ---------------------------------------------------------------------------


class TestLookup:
    def test_known_group(self, client):
        """IOTA-L2-010: OC-001 returns Australian Mainland."""
        result = client.lookup("OC-001")
        assert result["refno"] == "OC-001"
        assert result["name"] == "Australian Mainland"
        assert result["continent"] == "OC"

    def test_case_insensitive(self, client):
        """IOTA-L2-011: Lookup is case-insensitive."""
        result = client.lookup("oc-001")
        assert result["refno"] == "OC-001"

    def test_not_found(self, client):
        """IOTA-L2-012: Unknown refno returns error."""
        result = client.lookup("XX-999")
        assert "error" in result
        assert result["error"] == "Not found"

    def test_fields_present(self, client):
        """IOTA-L2-013: Lookup result has expected fields."""
        result = client.lookup("OC-001")
        for field in ("refno", "name", "dxcc_num", "continent", "latitude",
                       "longitude", "bbox", "island_count"):
            assert field in result, f"Missing field: {field}"

    def test_eu_multi_dxcc(self, client):
        """IOTA-L2-014: EU-005 has comma-separated DXCC."""
        result = client.lookup("EU-005")
        assert "223" in result["dxcc_num"]
        assert "114" in result["dxcc_num"]


# ---------------------------------------------------------------------------
# IOTA-L2-016..020: search()
# ---------------------------------------------------------------------------


class TestSearch:
    def test_search_by_group_name(self, client):
        """IOTA-L2-016: Search 'australian' finds OC-001."""
        results = client.search("australian")
        assert len(results) >= 1
        refnos = [r["refno"] for r in results]
        assert "OC-001" in refnos

    def test_search_by_island_name(self, client):
        """IOTA-L2-017: Search 'tasmania' finds OC-001."""
        results = client.search("tasmania")
        assert len(results) >= 1
        refnos = [r["refno"] for r in results]
        assert "OC-001" in refnos

    def test_search_hawaiian(self, client):
        """IOTA-L2-018: Search 'hawaiian' finds OC-019."""
        results = client.search("hawaiian")
        refnos = [r["refno"] for r in results]
        assert "OC-019" in refnos

    def test_search_empty_query(self, client):
        """IOTA-L2-019: Empty query returns empty list."""
        assert client.search("") == []

    def test_search_no_match(self, client):
        """IOTA-L2-020: Non-matching query returns empty."""
        assert client.search("zzzznotfound") == []

    def test_search_limit(self, client):
        """IOTA-L2-021: Limit parameter caps results."""
        results = client.search("island", limit=1)
        assert len(results) <= 1


# ---------------------------------------------------------------------------
# IOTA-L2-022..025: islands()
# ---------------------------------------------------------------------------


class TestIslands:
    def test_known_group(self, client):
        """IOTA-L2-022: OC-001 lists Australia + Tasmania."""
        result = client.islands("OC-001")
        assert result["refno"] == "OC-001"
        assert result["total_islands"] == 2
        assert len(result["subgroups"]) == 1

    def test_multi_subgroup(self, client):
        """IOTA-L2-023: EU-005 has 2 subgroups (England, Scotland)."""
        result = client.islands("EU-005")
        assert result["subgroup_count"] == 2

    def test_island_names(self, client):
        """IOTA-L2-024: OC-019 islands include Oahu and Maui."""
        result = client.islands("OC-019")
        islands = result["subgroups"][0]["islands"]
        names = [i["name"] for i in islands]
        assert "Oahu" in names
        assert "Maui" in names

    def test_not_found(self, client):
        """IOTA-L2-025: Unknown refno returns error."""
        result = client.islands("XX-999")
        assert "error" in result


# ---------------------------------------------------------------------------
# IOTA-L2-026..030: dxcc_lookup()
# ---------------------------------------------------------------------------


class TestDxccLookup:
    def test_dxcc_to_iota(self, client):
        """IOTA-L2-026: DXCC 150 → OC-001 (Australia)."""
        result = client.dxcc_lookup(dxcc_num="150")
        assert result["dxcc_num"] == "150"
        assert result["iota_count"] >= 1
        refnos = [g["refno"] for g in result["groups"]]
        assert "OC-001" in refnos

    def test_iota_to_dxcc(self, client):
        """IOTA-L2-027: OC-001 → DXCC 150."""
        result = client.dxcc_lookup(refno="OC-001")
        assert "150" in result["dxcc_entities"]

    def test_multi_dxcc(self, client):
        """IOTA-L2-028: EU-005 maps to DXCC 223 and 114."""
        result = client.dxcc_lookup(refno="EU-005")
        assert "223" in result["dxcc_entities"]
        assert "114" in result["dxcc_entities"]

    def test_no_params_error(self, client):
        """IOTA-L2-029: No params returns error."""
        result = client.dxcc_lookup()
        assert "error" in result

    def test_unknown_dxcc(self, client):
        """IOTA-L2-030: Unknown DXCC returns 0 groups."""
        result = client.dxcc_lookup(dxcc_num="9999")
        assert result["iota_count"] == 0


# ---------------------------------------------------------------------------
# IOTA-L2-031..035: stats()
# ---------------------------------------------------------------------------


class TestStats:
    def test_returns_totals(self, client):
        """IOTA-L2-031: stats() returns group and island totals."""
        result = client.stats()
        assert result["total_groups"] == 4  # Mock has 4 groups
        assert result["total_islands"] > 0

    def test_continent_breakdown(self, client):
        """IOTA-L2-032: stats() has continent breakdown."""
        result = client.stats()
        continents = result["groups_by_continent"]
        assert "OC" in continents
        assert "EU" in continents
        assert "AF" in continents

    def test_most_credited(self, client):
        """IOTA-L2-033: Most credited group identified."""
        result = client.stats()
        assert result["most_credited"]["refno"] != ""
        assert result["most_credited"]["pc_credited"] > 0

    def test_least_credited(self, client):
        """IOTA-L2-034: Least credited group identified."""
        result = client.stats()
        assert result["least_credited"]["refno"] != ""
        assert result["least_credited"]["pc_credited"] > 0

    def test_dxcc_count(self, client):
        """IOTA-L2-035: DXCC entity count from mock data."""
        result = client.stats()
        assert result["total_dxcc_entities"] >= 4  # 150, 110, 223, 114, 411


# ---------------------------------------------------------------------------
# IOTA-L2-036..040: nearby()
# ---------------------------------------------------------------------------


class TestNearby:
    def test_returns_sorted(self, client):
        """IOTA-L2-036: nearby() returns groups sorted by distance."""
        results = client.nearby(latitude=-27.0, longitude=133.5)
        if len(results) > 1:
            distances = [r["distance_km"] for r in results]
            assert distances == sorted(distances)

    def test_australia_nearest(self, client):
        """IOTA-L2-037: From Australia center, OC-001 is nearest."""
        results = client.nearby(latitude=-27.0, longitude=133.5)
        assert results[0]["refno"] == "OC-001"
        assert results[0]["distance_km"] < 100  # Very close to center

    def test_hawaii_nearest(self, client):
        """IOTA-L2-038: From Hawaii, OC-019 is nearest."""
        results = client.nearby(latitude=20.5, longitude=-157.5)
        assert results[0]["refno"] == "OC-019"

    def test_limit_respected(self, client):
        """IOTA-L2-039: Limit parameter caps results."""
        results = client.nearby(latitude=0, longitude=0, limit=2)
        assert len(results) <= 2

    def test_distance_field(self, client):
        """IOTA-L2-040: Each result has distance_km field."""
        results = client.nearby(latitude=0, longitude=0)
        for r in results:
            assert "distance_km" in r
            assert isinstance(r["distance_km"], float)


# ---------------------------------------------------------------------------
# IOTA-L2-041..045: Data loading and caching
# ---------------------------------------------------------------------------


class TestDataLoading:
    def test_indexes_built(self, client):
        """IOTA-L2-041: Mock data builds all indexes."""
        assert len(client._by_refno) == 4
        assert len(client._by_dxcc) >= 4
        assert len(client._name_index) == 4
        assert len(client._island_index) > 0

    def test_ensure_loaded_cached(self, client):
        """IOTA-L2-042: _ensure_loaded doesn't reload within TTL."""
        loaded_at = client._loaded_at
        client._ensure_loaded()
        assert client._loaded_at == loaded_at  # Same timestamp

    def test_format_group(self, client):
        """IOTA-L2-043: _format_group produces correct output."""
        group = client._by_refno["OC-001"]
        formatted = client._format_group(group)
        assert formatted["refno"] == "OC-001"
        assert formatted["continent"] == "OC"
        assert "bbox" in formatted
        assert formatted["island_count"] == 2

    def test_island_index_content(self, client):
        """IOTA-L2-044: Island index includes Tasmania."""
        island_names = [name for name, _, _ in client._island_index]
        assert "tasmania" in island_names

    def test_dxcc_index_bidirectional(self, client):
        """IOTA-L2-045: DXCC index includes both fulllist and map entries."""
        # DXCC 150 appears in both fulllist and dxcc_map
        assert "150" in client._by_dxcc
        assert "OC-001" in client._by_dxcc["150"]


# ---------------------------------------------------------------------------
# IOTA-L2-046..050: get_version_info — fleet identity attestation
# ---------------------------------------------------------------------------


class TestGetVersionInfo:
    """Tracks IONIS-AI/ionis-devel#49 — fleet get_version_info convention."""

    def test_returns_service_name(self):
        """IOTA-L2-046: payload includes service_name = 'iota-mcp'."""
        from iota_mcp.server import _version_info_payload

        assert _version_info_payload()["service_name"] == "iota-mcp"

    def test_returns_service_version(self):
        """IOTA-L2-047: service_version matches package __version__."""
        from iota_mcp import __version__
        from iota_mcp.server import _version_info_payload

        assert _version_info_payload()["service_version"] == __version__

    def test_returns_spec_version(self):
        """IOTA-L2-048: spec_version pins the IOTA programme data revision."""
        from iota_mcp.server import _version_info_payload

        assert _version_info_payload()["spec_version"] == "iota-programme-v1"

    def test_payload_keys_are_required_set(self):
        """IOTA-L2-049: payload has the required keys (no extras yet)."""
        from iota_mcp.server import _version_info_payload

        result = _version_info_payload()
        required = {"service_name", "service_version", "spec_version"}
        assert required.issubset(set(result.keys()))

    def test_all_values_are_strings(self):
        """IOTA-L2-050: all returned values are strings (JSON-safe envelope)."""
        from iota_mcp.server import _version_info_payload

        result = _version_info_payload()
        for k in ("service_name", "service_version", "spec_version"):
            assert isinstance(result[k], str), f"{k} should be str, got {type(result[k])}"
            assert result[k], f"{k} should be non-empty"

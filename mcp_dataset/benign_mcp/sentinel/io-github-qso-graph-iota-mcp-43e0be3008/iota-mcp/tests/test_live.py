"""L3 live integration tests for iota-mcp against iota-world.org.

Run with: pytest tests/test_live.py --live
"""
import os
import pytest

from iota_mcp.client import IOTAClient

# Ensure we are NOT in mock mode
assert os.environ.get("IOTA_MCP_MOCK") != "1", "Live tests must not run with IOTA_MCP_MOCK=1"

# Known-good reference values
KNOWN_IOTA = "OC-001"       # Australian Mainland — will always exist
KNOWN_DXCC = "150"          # Australia
HAWAII_LAT = 20.5
HAWAII_LON = -157.5


@pytest.fixture(scope="module")
def client():
    """Shared IOTAClient instance — data cached for 24h after first load."""
    return IOTAClient()


# ------------------------------------------------------------------
# IOTA-L3-001: Lookup a known IOTA group
# ------------------------------------------------------------------
@pytest.mark.live
def test_lookup_live(client):
    """IOTA-L3-001: lookup(OC-001) returns Australian Mainland with correct fields."""
    result = client.lookup(KNOWN_IOTA)

    assert "error" not in result, f"Lookup failed: {result}"
    assert result["refno"] == KNOWN_IOTA
    assert "australia" in result["name"].lower()
    assert result["continent"] == "OC"
    assert result["dxcc_num"], "dxcc_num must be non-empty"
    assert isinstance(result["island_count"], int)
    assert result["island_count"] > 0


# ------------------------------------------------------------------
# IOTA-L3-002: Lookup is case-insensitive
# ------------------------------------------------------------------
@pytest.mark.live
def test_lookup_case_insensitive_live(client):
    """IOTA-L3-002: lookup('oc-001') returns same result as lookup('OC-001')."""
    upper = client.lookup("OC-001")
    lower = client.lookup("oc-001")

    assert "error" not in upper
    assert "error" not in lower
    assert upper["refno"] == lower["refno"]
    assert upper["name"] == lower["name"]
    assert upper["dxcc_num"] == lower["dxcc_num"]
    assert upper["continent"] == lower["continent"]


# ------------------------------------------------------------------
# IOTA-L3-003: Lookup a non-existent reference returns error
# ------------------------------------------------------------------
@pytest.mark.live
def test_lookup_not_found_live(client):
    """IOTA-L3-003: lookup('ZZ-999') returns an error dict."""
    result = client.lookup("ZZ-999")
    assert "error" in result


# ------------------------------------------------------------------
# IOTA-L3-004: Search by name
# ------------------------------------------------------------------
@pytest.mark.live
def test_search_live(client):
    """IOTA-L3-004: search('australia') returns results containing OC-001."""
    results = client.search("australia")

    assert len(results) > 0, "Search for 'australia' returned no results"
    refnos = [r["refno"] for r in results]
    assert KNOWN_IOTA in refnos, f"OC-001 not found in search results: {refnos}"


# ------------------------------------------------------------------
# IOTA-L3-005: Search returns limited results
# ------------------------------------------------------------------
@pytest.mark.live
def test_search_limit_live(client):
    """IOTA-L3-005: search with limit=5 returns at most 5 results."""
    results = client.search("island", limit=5)
    assert len(results) <= 5


# ------------------------------------------------------------------
# IOTA-L3-006: Islands listing
# ------------------------------------------------------------------
@pytest.mark.live
def test_islands_live(client):
    """IOTA-L3-006: islands(OC-001) returns subgroups with island names."""
    result = client.islands(KNOWN_IOTA)

    assert "error" not in result, f"Islands lookup failed: {result}"
    assert result["refno"] == KNOWN_IOTA
    assert "australia" in result["group_name"].lower()
    assert result["total_islands"] > 0
    assert len(result["subgroups"]) > 0

    # Each subgroup should have islands
    for sg in result["subgroups"]:
        assert "subref" in sg
        assert "name" in sg
        assert "islands" in sg
        for island in sg["islands"]:
            assert "id" in island
            assert "name" in island
            assert island["name"], "Island name must not be empty"


# ------------------------------------------------------------------
# IOTA-L3-007: DXCC lookup by number
# ------------------------------------------------------------------
@pytest.mark.live
def test_dxcc_lookup_live(client):
    """IOTA-L3-007: dxcc_lookup(dxcc_num='150') returns groups containing OC-001."""
    result = client.dxcc_lookup(dxcc_num=KNOWN_DXCC)

    assert "error" not in result, f"DXCC lookup failed: {result}"
    assert result["dxcc_num"] == KNOWN_DXCC
    assert result["iota_count"] > 0

    refnos = [g["refno"] for g in result["groups"]]
    assert KNOWN_IOTA in refnos, f"OC-001 not in DXCC 150 groups: {refnos}"


# ------------------------------------------------------------------
# IOTA-L3-008: DXCC reverse lookup (refno -> DXCC)
# ------------------------------------------------------------------
@pytest.mark.live
def test_dxcc_reverse_lookup_live(client):
    """IOTA-L3-008: dxcc_lookup(refno='OC-001') returns DXCC entity list."""
    result = client.dxcc_lookup(refno=KNOWN_IOTA)

    assert "error" not in result, f"Reverse DXCC lookup failed: {result}"
    assert result["refno"] == KNOWN_IOTA
    assert len(result["dxcc_entities"]) > 0
    assert KNOWN_DXCC in result["dxcc_entities"]


# ------------------------------------------------------------------
# IOTA-L3-009: Programme statistics
# ------------------------------------------------------------------
@pytest.mark.live
def test_stats_live(client):
    """IOTA-L3-009: stats() returns plausible programme totals."""
    result = client.stats()

    assert result["total_groups"] > 1000, f"Expected >1000 groups, got {result['total_groups']}"
    assert result["total_islands"] > 0
    assert result["total_dxcc_entities"] > 0

    # Continent breakdown
    continents = result["groups_by_continent"]
    assert len(continents) > 0, "No continent data"
    for prefix in ("AF", "AN", "AS", "EU", "NA", "OC", "SA"):
        assert prefix in continents, f"Missing continent {prefix}"
        assert continents[prefix] > 0

    # Most/least credited
    assert result["most_credited"]["refno"]
    assert result["most_credited"]["pc_credited"] > 0
    assert result["least_credited"]["refno"]
    assert result["least_credited"]["pc_credited"] > 0


# ------------------------------------------------------------------
# IOTA-L3-010: Nearby search from Australia center
# ------------------------------------------------------------------
@pytest.mark.live
def test_nearby_live(client):
    """IOTA-L3-010: nearby(-27.0, 133.5) returns sorted results, OC-001 near top."""
    results = client.nearby(latitude=-27.0, longitude=133.5)

    assert len(results) > 0, "Nearby returned no results"

    # Results must be sorted by distance
    distances = [r["distance_km"] for r in results]
    assert distances == sorted(distances), "Results not sorted by distance"

    # OC-001 should be first or near the top (center of Australia)
    refnos = [r["refno"] for r in results[:5]]
    assert KNOWN_IOTA in refnos, f"OC-001 not in top 5 nearby results: {refnos}"


# ------------------------------------------------------------------
# IOTA-L3-011: Nearby search from Hawaii
# ------------------------------------------------------------------
@pytest.mark.live
def test_nearby_hawaii_live(client):
    """IOTA-L3-011: nearby(20.5, -157.5) returns OC-019 (Hawaii) near top."""
    results = client.nearby(latitude=HAWAII_LAT, longitude=HAWAII_LON)

    assert len(results) > 0
    refnos = [r["refno"] for r in results[:5]]
    assert "OC-019" in refnos, f"OC-019 not in top 5 near Hawaii: {refnos}"

    # All entries should have distance_km
    for r in results:
        assert "distance_km" in r
        assert isinstance(r["distance_km"], float)
        assert r["distance_km"] >= 0


# ------------------------------------------------------------------
# IOTA-L3-012: Nearby respects limit parameter
# ------------------------------------------------------------------
@pytest.mark.live
def test_nearby_limit_live(client):
    """IOTA-L3-012: nearby with limit=3 returns at most 3 results."""
    results = client.nearby(latitude=0.0, longitude=0.0, limit=3)
    assert len(results) <= 3

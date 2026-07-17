"""Tests für parlament-mcp Server.

Alle Tests nutzen gemockte HTTP-Antworten (kein Netzwerkzugriff nötig).
Live-Tests sind mit @pytest.mark.live markiert und in CI ausgeschlossen.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from parlament_mcp.server import (
    GetSessionsInput,
    SearchBusinessInput,
    SearchMembersInput,
    _fmt_business,
    _parse_date,
    parlament_get_sessions,
    parlament_search_business,
    parlament_search_members,
)

# ─────────────────────────── Unit-Tests (kein Netzwerk) ────────────────────────


def test_parse_date_valid():
    """OData-Datum korrekt in ISO-String umwandeln."""
    assert _parse_date("/Date(1735689600000)/") == "2025-01-01"


def test_parse_date_none():
    """None ergibt leeren String."""
    assert _parse_date(None) == ""


def test_parse_date_empty():
    """Leerer String ergibt leeren String."""
    assert _parse_date("") == ""


def test_fmt_business_basic():
    """Geschäft-Dict korrekt aufbereiten."""
    raw = {
        "ID": 20261009,
        "BusinessShortNumber": "26.1009",
        "BusinessTypeName": "Anfrage",
        "Title": "Künstliche Intelligenz und digitale Infrastruktur",
        "BusinessStatusText": "Eingereicht",
        "BusinessStatusDate": "/Date(1735689600000)/",
        "SubmittedBy": "Müller Hans",
        "SubmissionDate": "/Date(1735689600000)/",
        "SubmissionCouncilAbbreviation": "NR",
        "ResponsibleDepartmentAbbreviation": None,
        "Description": "Kurzbeschreibung",
        "TagNames": None,
    }
    result = _fmt_business(raw)
    assert result["id"] == 20261009
    assert result["type"] == "Anfrage"
    assert "Intelligenz" in result["title"]


# ─────────────────────────── Integrationstests (gemockte HTTP) ─────────────────

MOCK_BUSINESS = [
    {
        "ID": 20261009,
        "BusinessShortNumber": "26.1009",
        "BusinessTypeName": "Anfrage",
        "Title": "Künstliche Intelligenz und digitale Infrastruktur",
        "BusinessStatusText": "Eingereicht",
        "BusinessStatusDate": "/Date(1735689600000)/",
        "SubmittedBy": "Test Person",
        "SubmissionDate": "/Date(1735689600000)/",
        "SubmissionCouncilAbbreviation": "NR",
        "SubmissionCouncilName": "Nationalrat",
        "ResponsibleDepartmentAbbreviation": "UVEK",
        "ResponsibleDepartmentName": "UVEK",
        "Description": "Testbeschreibung",
        "TagNames": "KI, Digitalisierung",
    }
]

MOCK_MEMBER = [
    {
        "ID": 4300,
        "FirstName": "Anna",
        "LastName": "Tester",
        "CouncilAbbreviation": "NR",
        "CantonAbbreviation": "ZH",
        "PartyAbbreviation": "SP",
        "ParlGroupAbbreviation": "S",
        "Active": True,
        "DateJoining": "/Date(1609459200000)/",
    }
]

MOCK_SESSION = [
    {
        "ID": 5212,
        "SessionName": "Sommersession 2025",
        "Abbreviation": "SS25",
        "StartDate": "/Date(1748736000000)/",
        "EndDate": "/Date(1749945600000)/",
        "TypeName": "Ordentliche Session",
        "LegislativePeriodNumber": 52,
    }
]


@pytest.fixture
def mock_odata():
    """_odata_get mocken, um Testdaten zurückzugeben."""
    with patch("parlament_mcp.server._odata_get", new_callable=AsyncMock) as mock:
        yield mock


@pytest.mark.asyncio
async def test_search_business_fields(mock_odata):
    """Vorstoss-Suche: strukturierte Felder prüfen."""
    mock_odata.return_value = MOCK_BUSINESS
    params = SearchBusinessInput(keyword="KI", keyword2="Schule", status="Eingereicht")
    result = await parlament_search_business(params)
    assert result.count == 1
    assert "Künstliche Intelligenz" in result.results[0].title
    assert result.results[0].status == "Eingereicht"
    assert result.results[0].url and "AffairId=" in result.results[0].url


@pytest.mark.asyncio
async def test_search_business_envelope(mock_odata):
    """Vorstoss-Suche: Envelope (source/license/match_type) prüfen."""
    mock_odata.return_value = MOCK_BUSINESS
    result = await parlament_search_business(SearchBusinessInput(keyword="KI"))
    assert result.count == 1
    assert result.results[0].type == "Anfrage"
    assert result.source.startswith("Curia Vista")
    assert result.license == "CC BY 4.0"
    assert result.match_type == "exact"


@pytest.mark.asyncio
async def test_search_business_empty(mock_odata):
    """Vorstoss-Suche: Leeres Ergebnis → match_type none + Vorschläge."""
    mock_odata.return_value = []
    result = await parlament_search_business(SearchBusinessInput(keyword="xyz_nonexistent_12345"))
    assert result.match_type == "none"
    assert result.count == 0
    assert "Keine Vorstösse" in result.note
    assert result.suggestions


@pytest.mark.asyncio
async def test_search_members_zh(mock_odata):
    """Ratsmitglieder-Suche: Zürcher Mitglieder finden."""
    mock_odata.return_value = MOCK_MEMBER
    result = await parlament_search_members(SearchMembersInput(canton="ZH"))
    assert result.results[0].name == "Anna Tester"
    assert result.results[0].canton == "ZH"


@pytest.mark.asyncio
async def test_get_sessions(mock_odata):
    """Sessionen auflisten: Ergebnisse prüfen."""
    mock_odata.return_value = MOCK_SESSION
    result = await parlament_get_sessions(GetSessionsInput())
    assert "Sommersession" in result.results[0].name


# ─────────────────────────── Live-Tests (echte API, CI-ausgeschlossen) ─────────


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_search_ki():
    """Live: Suche nach 'Künstliche Intelligenz'-Vorstössen."""
    result = await parlament_search_business(
        SearchBusinessInput(keyword="Künstliche Intelligenz", limit=5)
    )
    assert result.count >= 0
    assert result.match_type in ("exact", "none")


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_zh_members():
    """Live: Aktive Zürcher Ratsmitglieder abrufen."""
    result = await parlament_search_members(
        SearchMembersInput(canton="ZH", active_only=True, limit=5)
    )
    assert all(m.canton == "ZH" for m in result.results)


@pytest.mark.live
@pytest.mark.asyncio
async def test_live_sessions():
    """Live: Aktuelle Sessionen auflisten."""
    result = await parlament_get_sessions(GetSessionsInput(limit=5))
    assert result.count >= 1

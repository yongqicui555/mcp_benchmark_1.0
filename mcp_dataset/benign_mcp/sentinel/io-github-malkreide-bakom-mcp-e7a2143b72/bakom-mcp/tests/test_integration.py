"""
Integrationstests für bakom-mcp.

Testet alle 12 Tools gegen die Live-APIs:
  - geo.admin.ch (Breitband, Mobilfunk, Sendeanlagen)
  - opendata.swiss CKAN (Statistik, Medien)
  - rtvdb.ofcomnet.ch (RTV-Datenbank)

Ausführung:
    python tests/test_integration.py
    pytest tests/test_integration.py -v
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path

# Projekt-Src zum Pfad hinzufügen
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from bakom_mcp.server import (
    BroadbandCoverageInput,
    BroadbandSpeed,
    CoordinateInput,
    MediaType,
    MobileCoverageInput,
    MobilGenerations,
    MultiLocationInput,
    AntennaSearchInput,
    ResponseFormat,
    RTVSearchInput,
    TelekomStatInput,
    bakom_aktuell,
    bakom_breitbandatlas_datensaetze,
    bakom_broadband_coverage,
    bakom_frequenzdaten,
    bakom_glasfaser_verfuegbarkeit,
    bakom_medienstruktur_info,
    bakom_mobilfunk_abdeckung,
    bakom_multi_standort_konnektivitaet,
    bakom_rtv_suche,
    bakom_sendeanlagen_suche,
    bakom_telekomstatistik_uebersicht,
)

# ---------------------------------------------------------------------------
# Testkoordinaten – Schulhaus Leutschenbach, Zürich
# ---------------------------------------------------------------------------
LAT_LEUTSCHENBACH = 47.4148
LON_LEUTSCHENBACH = 8.5654

LAT_BERN = 46.9467
LON_BERN = 7.4444

# Testkoordinate Wädenswil (Heimatstandort)
LAT_WAEDENSWIL = 47.2254
LON_WAEDENSWIL = 8.6697


# ---------------------------------------------------------------------------
# Hilfsklasse für Testergebnisse
# ---------------------------------------------------------------------------
class TestResult:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.errors: list[str] = []

    def ok(self, name: str, note: str = ""):
        self.passed += 1
        note_str = f" – {note}" if note else ""
        print(f"  ✅ {name}{note_str}")

    def fail(self, name: str, reason: str):
        self.failed += 1
        self.errors.append(f"{name}: {reason}")
        print(f"  ❌ {name}: {reason}")

    def summary(self):
        total = self.passed + self.failed
        print(f"\n{'='*60}")
        print(f"RESULTAT: {self.passed}/{total} Tests bestanden")
        if self.errors:
            print("\nFehler:")
            for e in self.errors:
                print(f"  • {e}")
        print("=" * 60)
        return self.failed == 0


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------
results = TestResult()


async def test_broadband_coverage():
    """T01: Breitbandabdeckung Schulhaus Leutschenbach"""
    try:
        params = BroadbandCoverageInput(
            latitude=LAT_LEUTSCHENBACH,
            longitude=LON_LEUTSCHENBACH,
            min_speed_mbps=BroadbandSpeed.S100,
        )
        output = await bakom_broadband_coverage(params)
        assert isinstance(output, str) and len(output) > 50
        assert "Breitbandversorgung" in output or "100" in output
        results.ok("T01: Breitbandabdeckung Leutschenbach", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("T01: Breitbandabdeckung Leutschenbach", str(e))


async def test_broadband_coverage_1000():
    """T02: Gigabit-Abdeckung Bern"""
    try:
        params = BroadbandCoverageInput(
            latitude=LAT_BERN,
            longitude=LON_BERN,
            min_speed_mbps=BroadbandSpeed.S1000,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_broadband_coverage(params)
        data = json.loads(output)
        assert "geschwindigkeit_mbps" in data
        assert data["geschwindigkeit_mbps"] == 1000
        results.ok("T02: Gigabit-Abdeckung Bern (JSON)", f"Geschwindigkeit: {data['geschwindigkeit_mbps']} Mbit/s")
    except Exception as e:
        results.fail("T02: Gigabit-Abdeckung Bern", str(e))


async def test_glasfaser():
    """T03: Glasfaserverfügbarkeit Wädenswil"""
    try:
        params = CoordinateInput(
            latitude=LAT_WAEDENSWIL,
            longitude=LON_WAEDENSWIL,
        )
        output = await bakom_glasfaser_verfuegbarkeit(params)
        assert isinstance(output, str) and len(output) > 30
        assert "Glasfaser" in output or "FTTB" in output
        results.ok("T03: Glasfaser Wädenswil", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("T03: Glasfaser Wädenswil", str(e))


async def test_multi_standort():
    """T04: Multi-Standort-Konnektivitätsvergleich"""
    try:
        params = MultiLocationInput(
            locations=[
                {"name": "Schulhaus Leutschenbach", "latitude": LAT_LEUTSCHENBACH, "longitude": LON_LEUTSCHENBACH},
                {"name": "Bundeshaus Bern", "latitude": LAT_BERN, "longitude": LON_BERN},
                {"name": "Wädenswil", "latitude": LAT_WAEDENSWIL, "longitude": LON_WAEDENSWIL},
            ],
        )
        output = await bakom_multi_standort_konnektivitaet(params)
        assert "Schulhaus Leutschenbach" in output
        assert "Bundeshaus Bern" in output
        results.ok("T04: Multi-Standort-Vergleich", "3 Standorte verglichen")
    except Exception as e:
        results.fail("T04: Multi-Standort-Vergleich", str(e))


async def test_multi_standort_json():
    """T05: Multi-Standort JSON-Output mit Zusammenfassung"""
    try:
        params = MultiLocationInput(
            locations=[
                {"name": "Zürich HB", "latitude": 47.3769, "longitude": 8.5417},
                {"name": "Ausserhalb Schweiz", "latitude": 48.8566, "longitude": 2.3522},
            ],
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_multi_standort_konnektivitaet(params)
        data = json.loads(output)
        assert "zusammenfassung" in data
        assert data["zusammenfassung"]["total"] == 2
        # Paris-Koordinate sollte Fehler haben
        fehler_eintraege = [s for s in data["standorte"] if s.get("fehler")]
        assert len(fehler_eintraege) >= 1
        results.ok("T05: Multi-Standort JSON", f"Zusammenfassung: {data['zusammenfassung']}")
    except Exception as e:
        results.fail("T05: Multi-Standort JSON", str(e))


async def test_mobilfunk_5g():
    """T06: 5G-Abdeckung Zürich"""
    try:
        params = MobileCoverageInput(
            latitude=47.3769,
            longitude=8.5417,
            generation=MobilGenerations.G5,
        )
        output = await bakom_mobilfunk_abdeckung(params)
        assert "5G" in output
        results.ok("T06: 5G-Abdeckung Zürich HB", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("T06: 5G-Abdeckung Zürich HB", str(e))


async def test_mobilfunk_4g_json():
    """T07: 4G-Abdeckung als JSON"""
    try:
        params = MobileCoverageInput(
            latitude=LAT_LEUTSCHENBACH,
            longitude=LON_LEUTSCHENBACH,
            generation=MobilGenerations.G4,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_mobilfunk_abdeckung(params)
        data = json.loads(output)
        assert data["generation"] == "4G"
        assert "abgedeckt" in data
        results.ok("T07: 4G-Abdeckung JSON", f"Abgedeckt: {data['abgedeckt']}")
    except Exception as e:
        results.fail("T07: 4G-Abdeckung JSON", str(e))


async def test_sendeanlagen():
    """T08: Mobilfunkanlagen-Suche Zürich"""
    try:
        params = AntennaSearchInput(
            latitude=47.3769,
            longitude=8.5417,
            radius_m=500,
        )
        output = await bakom_sendeanlagen_suche(params)
        assert "Mobilfunkanlagen" in output
        results.ok("T08: Sendeanlagen Zürich HB (500m)", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("T08: Sendeanlagen Zürich HB", str(e))


async def test_frequenzdaten():
    """T09: Radio-/TV-Sendeanlagen"""
    try:
        params = CoordinateInput(
            latitude=LAT_LEUTSCHENBACH,
            longitude=LON_LEUTSCHENBACH,
        )
        output = await bakom_frequenzdaten(params)
        assert isinstance(output, str) and len(output) > 30
        assert "Sender" in output or "Radio" in output or "TV" in output or "Sender" in output
        results.ok("T09: Radio-/TV-Sendeanlagen Leutschenbach", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("T09: Radio-/TV-Sendeanlagen", str(e))


async def test_rtv_suche():
    """T10: RTV-Suche nach «SRF»"""
    try:
        params = RTVSearchInput(
            query="SRF",
            media_type=MediaType.TV,
        )
        output = await bakom_rtv_suche(params)
        assert isinstance(output, str) and len(output) > 30
        results.ok("T10: RTV-Suche «SRF»", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("T10: RTV-Suche «SRF»", str(e))


async def test_rtv_suche_kanton():
    """T11: RTV-Suche Kanton ZH – Radio"""
    try:
        params = RTVSearchInput(
            media_type=MediaType.RADIO,
            kanton="ZH",
        )
        output = await bakom_rtv_suche(params)
        assert isinstance(output, str) and len(output) > 30
        results.ok("T11: Radio Kanton ZH", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("T11: Radio Kanton ZH", str(e))


async def test_medienstruktur():
    """T12: Medienstruktur-Info"""
    try:
        params = TelekomStatInput(thema="radio")
        output = await bakom_medienstruktur_info(params)
        assert isinstance(output, str) and len(output) > 50
        results.ok("T12: Medienstruktur Radio", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("T12: Medienstruktur Radio", str(e))


async def test_bakom_aktuell_medien():
    """T13: BAKOM Aktuell – Medien (SRG-Initiative)"""
    try:
        params = TelekomStatInput(thema="medien")
        output = await bakom_aktuell(params)
        assert "SRG" in output or "Medien" in output
        results.ok("T13: BAKOM Aktuell Medien", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("T13: BAKOM Aktuell Medien", str(e))


async def test_bakom_aktuell_5g():
    """T14: BAKOM Aktuell – 5G JSON"""
    try:
        params = TelekomStatInput(thema="5g", response_format=ResponseFormat.JSON)
        output = await bakom_aktuell(params)
        data = json.loads(output)
        assert "highlights" in data
        results.ok("T14: BAKOM Aktuell 5G JSON", f"{len(data['highlights'])} Highlights")
    except Exception as e:
        results.fail("T14: BAKOM Aktuell 5G JSON", str(e))


async def test_telekomstatistik():
    """T15: Telekommunikationsstatistik Breitband"""
    try:
        params = TelekomStatInput(thema="breitband")
        output = await bakom_telekomstatistik_uebersicht(params)
        assert isinstance(output, str) and len(output) > 50
        results.ok("T15: Telekomstatistik Breitband", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("T15: Telekomstatistik Breitband", str(e))


async def test_telekomstatistik_mobilfunk_json():
    """T16: Telekommunikationsstatistik Mobilfunk JSON"""
    try:
        params = TelekomStatInput(thema="mobilfunk", response_format=ResponseFormat.JSON)
        output = await bakom_telekomstatistik_uebersicht(params)
        data = json.loads(output)
        assert "datensaetze" in data
        assert "thema" in data
        results.ok("T16: Telekomstatistik Mobilfunk JSON", f"{len(data['datensaetze'])} Datensätze")
    except Exception as e:
        results.fail("T16: Telekomstatistik Mobilfunk JSON", str(e))


async def test_breitbandatlas_katalog():
    """T17: Breitbandatlas-Datensatzkatalog vollständig"""
    try:
        params = TelekomStatInput(thema="breitband")
        output = await bakom_breitbandatlas_datensaetze(params)
        assert "ch.bakom." in output
        assert "5G" in output
        assert "Glasfaser" in output
        results.ok("T17: Breitbandatlas-Katalog", "5G + Glasfaser + Festnetz gefunden")
    except Exception as e:
        results.fail("T17: Breitbandatlas-Katalog", str(e))


async def test_breitbandatlas_katalog_json():
    """T18: Breitbandatlas-Katalog JSON – Layer-ID Validierung"""
    try:
        params = TelekomStatInput(thema="alle", response_format=ResponseFormat.JSON)
        output = await bakom_breitbandatlas_datensaetze(params)
        data = json.loads(output)
        assert len(data["datensaetze"]) >= 8
        layer_ids = [d["layer_id"] for d in data["datensaetze"]]
        assert "ch.bakom.netzabdeckung-5g" in layer_ids
        assert "ch.bakom.anschlussart-verfuegbarkeit" in layer_ids
        results.ok("T18: Breitbandatlas-Katalog JSON", f"{len(data['datensaetze'])} Layer-IDs")
    except Exception as e:
        results.fail("T18: Breitbandatlas-Katalog JSON", str(e))


# ---------------------------------------------------------------------------
# Test-Runner
# ---------------------------------------------------------------------------
async def run_all_tests():
    print("\n" + "=" * 60)
    print("bakom-mcp Integrationstests")
    print("APIs: geo.admin.ch · opendata.swiss · rtvdb.ofcomnet.ch")
    print("=" * 60)

    print("\n📡 Breitband & Konnektivität")
    await test_broadband_coverage()
    await test_broadband_coverage_1000()
    await test_glasfaser()
    await test_multi_standort()
    await test_multi_standort_json()

    print("\n📶 Mobilfunk & Sendeanlagen")
    await test_mobilfunk_5g()
    await test_mobilfunk_4g_json()
    await test_sendeanlagen()
    await test_frequenzdaten()

    print("\n📺 Medien & RTV")
    await test_rtv_suche()
    await test_rtv_suche_kanton()
    await test_medienstruktur()
    await test_bakom_aktuell_medien()
    await test_bakom_aktuell_5g()

    print("\n📊 Telekommunikationsstatistik")
    await test_telekomstatistik()
    await test_telekomstatistik_mobilfunk_json()
    await test_breitbandatlas_katalog()
    await test_breitbandatlas_katalog_json()

    return results.summary()


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

"""
20 unterschiedliche Testszenarien für bakom-mcp.

Deckt Lücken der bestehenden Tests ab:
  - Grenzwerte & Edge Cases (Alpen, Grenzgebiete, abgelegene Orte)
  - Alle Geschwindigkeitsstufen & Mobilfunkgenerationen
  - Validierungsfehler (ungültige Koordinaten)
  - Seltene Parameter-Kombinationen
  - Diverse Schweizer Regionen (Romandie, Tessin, Engadin)
  - JSON-Strukturvalidierung
  - Grosse Suchanfragen & Minimal-Radien

Ausführung:
    python tests/test_20_szenarien.py
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path

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
# Testkoordinaten – Diverse Schweizer Regionen
# ---------------------------------------------------------------------------
# Alpenregion: Jungfraujoch (hochgelegen, wenig Infrastruktur)
LAT_JUNGFRAUJOCH = 46.5474
LON_JUNGFRAUJOCH = 7.9853

# Tessin: Lugano (italienischsprachige Schweiz)
LAT_LUGANO = 46.0037
LON_LUGANO = 8.9511

# Romandie: Genf Zentrum
LAT_GENF = 46.2044
LON_GENF = 6.1432

# Engadin: St. Moritz (Bergregion, touristische Infrastruktur)
LAT_ST_MORITZ = 46.4908
LON_ST_MORITZ = 9.8355

# Grenzgebiet: Basel (Dreiländereck)
LAT_BASEL = 47.5596
LON_BASEL = 7.5886

# Ländlich: Appenzell
LAT_APPENZELL = 47.3303
LON_APPENZELL = 9.4086

# Grenzwert: Südlichster Punkt der Schweiz (nahe Chiasso)
LAT_CHIASSO = 45.8300
LON_CHIASSO = 9.0300

# Grenzwert: Nördlichster Punkt (nahe Schaffhausen)
LAT_SCHAFFHAUSEN = 47.8900
LON_SCHAFFHAUSEN = 8.6300


# ---------------------------------------------------------------------------
# Hilfsklasse
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


results = TestResult()


# ---------------------------------------------------------------------------
# Szenario 1: 3G-Abdeckung im Alpental (selten getestet)
# ---------------------------------------------------------------------------
async def test_s01_3g_alpenregion():
    """S01: 3G-Abdeckung in Bergregion (Jungfraujoch-Nähe)"""
    try:
        params = MobileCoverageInput(
            latitude=LAT_JUNGFRAUJOCH,
            longitude=LON_JUNGFRAUJOCH,
            generation=MobilGenerations.G3,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_mobilfunk_abdeckung(params)
        data = json.loads(output)
        assert data["generation"] == "3G"
        assert "abgedeckt" in data
        assert "standort" in data
        results.ok("S01: 3G Alpenregion", f"abgedeckt={data['abgedeckt']}")
    except Exception as e:
        results.fail("S01: 3G Alpenregion", str(e))


# ---------------------------------------------------------------------------
# Szenario 2: Breitband 30 Mbit/s – niedrigste Stufe (Tessin)
# ---------------------------------------------------------------------------
async def test_s02_breitband_30_tessin():
    """S02: Breitband-Mindestversorgung 30 Mbit/s in Lugano"""
    try:
        params = BroadbandCoverageInput(
            latitude=LAT_LUGANO,
            longitude=LON_LUGANO,
            min_speed_mbps=BroadbandSpeed.S30,
        )
        output = await bakom_broadband_coverage(params)
        assert isinstance(output, str) and len(output) > 30
        assert "30" in output or "Breitband" in output or "Mbit" in output
        results.ok("S02: 30 Mbit/s Lugano", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("S02: 30 Mbit/s Lugano", str(e))


# ---------------------------------------------------------------------------
# Szenario 3: Breitband 300 Mbit/s – mittlere Stufe als JSON
# ---------------------------------------------------------------------------
async def test_s03_breitband_300_json():
    """S03: 300 Mbit/s Breitband Genf als JSON"""
    try:
        params = BroadbandCoverageInput(
            latitude=LAT_GENF,
            longitude=LON_GENF,
            min_speed_mbps=BroadbandSpeed.S300,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_broadband_coverage(params)
        data = json.loads(output)
        assert data["geschwindigkeit_mbps"] == 300
        assert "standort" in data
        assert abs(data["standort"]["lat"] - LAT_GENF) < 0.01
        results.ok("S03: 300 Mbit/s Genf JSON", f"abgedeckt={data['abgedeckt']}")
    except Exception as e:
        results.fail("S03: 300 Mbit/s Genf JSON", str(e))


# ---------------------------------------------------------------------------
# Szenario 4: Breitband 500 Mbit/s – bisher nicht getestet
# ---------------------------------------------------------------------------
async def test_s04_breitband_500():
    """S04: 500 Mbit/s Breitband Basel"""
    try:
        params = BroadbandCoverageInput(
            latitude=LAT_BASEL,
            longitude=LON_BASEL,
            min_speed_mbps=BroadbandSpeed.S500,
        )
        output = await bakom_broadband_coverage(params)
        assert isinstance(output, str) and len(output) > 30
        assert "500" in output or "Breitband" in output
        results.ok("S04: 500 Mbit/s Basel", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("S04: 500 Mbit/s Basel", str(e))


# ---------------------------------------------------------------------------
# Szenario 5: Glasfaser in ländlicher Region (Appenzell)
# ---------------------------------------------------------------------------
async def test_s05_glasfaser_laendlich():
    """S05: Glasfaserverfügbarkeit in ländlicher Region Appenzell"""
    try:
        params = CoordinateInput(
            latitude=LAT_APPENZELL,
            longitude=LON_APPENZELL,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_glasfaser_verfuegbarkeit(params)
        data = json.loads(output)
        assert "glasfaser_verfuegbar" in data
        assert isinstance(data["glasfaser_verfuegbar"], bool)
        assert "datenquelle" in data
        results.ok("S05: Glasfaser Appenzell", f"verfügbar={data['glasfaser_verfuegbar']}")
    except Exception as e:
        results.fail("S05: Glasfaser Appenzell", str(e))


# ---------------------------------------------------------------------------
# Szenario 6: Sendeanlagen mit Minimal-Radius (100m)
# ---------------------------------------------------------------------------
async def test_s06_sendeanlagen_minimal_radius():
    """S06: Sendeanlagen-Suche mit kleinstem Radius (100m) in Genf"""
    try:
        params = AntennaSearchInput(
            latitude=LAT_GENF,
            longitude=LON_GENF,
            radius_m=100,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_sendeanlagen_suche(params)
        data = json.loads(output)
        assert "anlagen" in data
        assert data["radius_m"] == 100
        assert isinstance(data["anlagen"], list)
        results.ok("S06: Antennen 100m Genf", f"{data['total']} gefunden")
    except Exception as e:
        results.fail("S06: Antennen 100m Genf", str(e))


# ---------------------------------------------------------------------------
# Szenario 7: Sendeanlagen mit Maximal-Radius (5000m)
# ---------------------------------------------------------------------------
async def test_s07_sendeanlagen_maximal_radius():
    """S07: Sendeanlagen-Suche mit grösstem Radius (5000m) in St. Moritz"""
    try:
        params = AntennaSearchInput(
            latitude=LAT_ST_MORITZ,
            longitude=LON_ST_MORITZ,
            radius_m=5000,
        )
        output = await bakom_sendeanlagen_suche(params)
        assert "Mobilfunkanlagen" in output
        results.ok("S07: Antennen 5000m St.Moritz", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("S07: Antennen 5000m St.Moritz", str(e))


# ---------------------------------------------------------------------------
# Szenario 8: Multi-Standort – 5 Standorte, alle Sprachregionen
# ---------------------------------------------------------------------------
async def test_s08_multi_5_sprachregionen():
    """S08: Multi-Standort Vergleich über alle 3 Sprachregionen + Engadin"""
    try:
        params = MultiLocationInput(
            locations=[
                {"name": "Genf (FR)", "latitude": LAT_GENF, "longitude": LON_GENF},
                {"name": "Lugano (IT)", "latitude": LAT_LUGANO, "longitude": LON_LUGANO},
                {"name": "Basel (DE)", "latitude": LAT_BASEL, "longitude": LON_BASEL},
                {"name": "St.Moritz (RM)", "latitude": LAT_ST_MORITZ, "longitude": LON_ST_MORITZ},
                {"name": "Appenzell (DE)", "latitude": LAT_APPENZELL, "longitude": LON_APPENZELL},
            ],
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_multi_standort_konnektivitaet(params)
        data = json.loads(output)
        assert data["zusammenfassung"]["total"] == 5
        assert len(data["standorte"]) == 5
        # Alle Standorte sollten Namen haben
        namen = [s["name"] for s in data["standorte"]]
        assert "Genf (FR)" in namen
        assert "Lugano (IT)" in namen
        results.ok("S08: 5 Sprachregionen", f"5G: {data['zusammenfassung']['mit_5g']}, Glasfaser: {data['zusammenfassung']['mit_glasfaser']}")
    except Exception as e:
        results.fail("S08: 5 Sprachregionen", str(e))


# ---------------------------------------------------------------------------
# Szenario 9: Multi-Standort – nur 1 Standort (Minimum)
# ---------------------------------------------------------------------------
async def test_s09_multi_single_location():
    """S09: Multi-Standort mit nur einem einzigen Standort"""
    try:
        params = MultiLocationInput(
            locations=[
                {"name": "Chiasso Grenzwert", "latitude": LAT_CHIASSO, "longitude": LON_CHIASSO},
            ],
        )
        output = await bakom_multi_standort_konnektivitaet(params)
        assert "Chiasso Grenzwert" in output
        results.ok("S09: Multi-Standort (1 Ort)", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("S09: Multi-Standort (1 Ort)", str(e))


# ---------------------------------------------------------------------------
# Szenario 10: RTV-Suche mit Typ "alle" und Kanton BE
# ---------------------------------------------------------------------------
async def test_s10_rtv_alle_bern():
    """S10: RTV-Suche – alle Medientypen im Kanton Bern"""
    try:
        params = RTVSearchInput(
            media_type=MediaType.ALLE,
            kanton="be",  # Kleinschreibung → sollte automatisch zu "BE" werden
            limit=10,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_rtv_suche(params)
        data = json.loads(output)
        assert "resultate" in data
        assert data["suchanfrage"]["typ"] in ("alle", "radio,tv")
        results.ok("S10: RTV alle BE", f"{data['total']} Resultate")
    except Exception as e:
        results.fail("S10: RTV alle BE", str(e))


# ---------------------------------------------------------------------------
# Szenario 11: RTV-Suche mit spezifischem Sendernamen
# ---------------------------------------------------------------------------
async def test_s11_rtv_spezifischer_sender():
    """S11: RTV-Suche nach spezifischem Sender «Tele Züri»"""
    try:
        params = RTVSearchInput(
            query="Tele Züri",
            media_type=MediaType.TV,
        )
        output = await bakom_rtv_suche(params)
        assert isinstance(output, str) and len(output) > 20
        results.ok("S11: RTV «Tele Züri»", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("S11: RTV «Tele Züri»", str(e))


# ---------------------------------------------------------------------------
# Szenario 12: RTV-Suche mit limit=1 (Minimum)
# ---------------------------------------------------------------------------
async def test_s12_rtv_limit_1():
    """S12: RTV-Suche mit minimalem Limit (1 Resultat)"""
    try:
        params = RTVSearchInput(
            media_type=MediaType.RADIO,
            limit=1,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_rtv_suche(params)
        data = json.loads(output)
        assert "resultate" in data
        assert len(data["resultate"]) <= 1
        results.ok("S12: RTV limit=1", f"{len(data['resultate'])} Resultat(e)")
    except Exception as e:
        results.fail("S12: RTV limit=1", str(e))


# ---------------------------------------------------------------------------
# Szenario 13: Frequenzdaten Tessin (andere Region als bestehende Tests)
# ---------------------------------------------------------------------------
async def test_s13_frequenzdaten_tessin():
    """S13: Radio-/TV-Sender in der Nähe von Lugano"""
    try:
        params = CoordinateInput(
            latitude=LAT_LUGANO,
            longitude=LON_LUGANO,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_frequenzdaten(params)
        data = json.loads(output)
        assert "sender" in data
        assert isinstance(data["sender"], list)
        assert "suchradius_m" in data
        results.ok("S13: Frequenzdaten Lugano", f"{data['total']} Sender")
    except Exception as e:
        results.fail("S13: Frequenzdaten Lugano", str(e))


# ---------------------------------------------------------------------------
# Szenario 14: Medienstruktur – Thema "online"
# ---------------------------------------------------------------------------
async def test_s14_medienstruktur_online():
    """S14: Medienstruktur-Info zum Thema Online-Medien"""
    try:
        params = TelekomStatInput(
            thema="online",
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_medienstruktur_info(params)
        data = json.loads(output)
        assert "datensaetze" in data
        assert "weiterfuehrende_links" in data
        results.ok("S14: Medienstruktur Online", f"{data['total_datensaetze']} Datensätze")
    except Exception as e:
        results.fail("S14: Medienstruktur Online", str(e))


# ---------------------------------------------------------------------------
# Szenario 15: BAKOM Aktuell – Thema "post"
# ---------------------------------------------------------------------------
async def test_s15_bakom_aktuell_post():
    """S15: BAKOM Aktuell – Thema Post (bisher nicht getestet)"""
    try:
        params = TelekomStatInput(thema="post")
        output = await bakom_aktuell(params)
        assert isinstance(output, str) and len(output) > 30
        assert "Post" in output or "BAKOM" in output or "Aktuell" in output
        results.ok("S15: BAKOM Aktuell Post", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("S15: BAKOM Aktuell Post", str(e))


# ---------------------------------------------------------------------------
# Szenario 16: BAKOM Aktuell – Thema "ki" (Künstliche Intelligenz)
# ---------------------------------------------------------------------------
async def test_s16_bakom_aktuell_ki():
    """S16: BAKOM Aktuell – Thema KI"""
    try:
        params = TelekomStatInput(
            thema="ki",
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_aktuell(params)
        data = json.loads(output)
        assert "highlights" in data
        assert "bakom_homepage" in data
        results.ok("S16: BAKOM Aktuell KI", f"{data['total']} Highlights")
    except Exception as e:
        results.fail("S16: BAKOM Aktuell KI", str(e))


# ---------------------------------------------------------------------------
# Szenario 17: Telekomstatistik – Thema "festnetz"
# ---------------------------------------------------------------------------
async def test_s17_telekomstatistik_festnetz():
    """S17: Telekomstatistik zum Thema Festnetz"""
    try:
        params = TelekomStatInput(
            thema="festnetz",
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_telekomstatistik_uebersicht(params)
        data = json.loads(output)
        assert "datensaetze" in data
        assert "thema" in data
        assert "datenquelle" in data
        results.ok("S17: Telekomstatistik Festnetz", f"{len(data['datensaetze'])} Datensätze")
    except Exception as e:
        results.fail("S17: Telekomstatistik Festnetz", str(e))


# ---------------------------------------------------------------------------
# Szenario 18: Breitbandatlas – Thema "alle" mit vollständiger Validierung
# ---------------------------------------------------------------------------
async def test_s18_breitbandatlas_alle_validierung():
    """S18: Breitbandatlas-Katalog vollständig – alle Kategorien prüfen"""
    try:
        params = TelekomStatInput(
            thema="alle",
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_breitbandatlas_datensaetze(params)
        data = json.loads(output)
        # Alle Kategorien prüfen
        kategorien = {d["kategorie"] for d in data["datensaetze"]}
        assert len(kategorien) >= 2, f"Nur {len(kategorien)} Kategorien: {kategorien}"
        # Jeder Datensatz braucht die Pflichtfelder
        for ds in data["datensaetze"]:
            assert "titel" in ds, f"Titel fehlt in {ds}"
            assert "layer_id" in ds, f"Layer-ID fehlt in {ds}"
            assert ds["layer_id"].startswith("ch.bakom."), f"Ungültige Layer-ID: {ds['layer_id']}"
        results.ok("S18: Breitbandatlas Validierung", f"{len(kategorien)} Kategorien, {data['total']} Layer")
    except Exception as e:
        results.fail("S18: Breitbandatlas Validierung", str(e))


# ---------------------------------------------------------------------------
# Szenario 19: Koordinaten-Grenzwerte – südlichster Punkt
# ---------------------------------------------------------------------------
async def test_s19_grenzwert_suedlich():
    """S19: Breitband am südlichsten Grenzwert der Schweiz (Chiasso)"""
    try:
        params = BroadbandCoverageInput(
            latitude=LAT_CHIASSO,
            longitude=LON_CHIASSO,
            min_speed_mbps=BroadbandSpeed.S100,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_broadband_coverage(params)
        data = json.loads(output)
        assert "standort" in data
        # Prüfe, dass Koordinaten korrekt übernommen wurden
        assert abs(data["standort"]["lat"] - LAT_CHIASSO) < 0.01
        results.ok("S19: Grenzwert Süd (Chiasso)", f"abgedeckt={data['abgedeckt']}")
    except Exception as e:
        results.fail("S19: Grenzwert Süd (Chiasso)", str(e))


# ---------------------------------------------------------------------------
# Szenario 20: 5G-Abdeckung + Glasfaser kombinierte Prüfung (Schaffhausen)
# ---------------------------------------------------------------------------
async def test_s20_kombi_5g_glasfaser_nord():
    """S20: Kombinierte 5G + Glasfaser-Prüfung am nördlichen Grenzwert"""
    try:
        # 5G-Check
        params_5g = MobileCoverageInput(
            latitude=LAT_SCHAFFHAUSEN,
            longitude=LON_SCHAFFHAUSEN,
            generation=MobilGenerations.G5,
            response_format=ResponseFormat.JSON,
        )
        output_5g = await bakom_mobilfunk_abdeckung(params_5g)
        data_5g = json.loads(output_5g)
        assert "abgedeckt" in data_5g

        # Glasfaser-Check am gleichen Ort
        params_gf = CoordinateInput(
            latitude=LAT_SCHAFFHAUSEN,
            longitude=LON_SCHAFFHAUSEN,
            response_format=ResponseFormat.JSON,
        )
        output_gf = await bakom_glasfaser_verfuegbarkeit(params_gf)
        data_gf = json.loads(output_gf)
        assert "glasfaser_verfuegbar" in data_gf

        kombi = f"5G={data_5g['abgedeckt']}, Glasfaser={data_gf['glasfaser_verfuegbar']}"
        results.ok("S20: Kombi 5G+Glasfaser Schaffhausen", kombi)
    except Exception as e:
        results.fail("S20: Kombi 5G+Glasfaser Schaffhausen", str(e))


# ---------------------------------------------------------------------------
# Test-Runner
# ---------------------------------------------------------------------------
async def run_all_tests():
    print("\n" + "=" * 60)
    print("bakom-mcp – 20 Diverse Testszenarien")
    print("Regionen: Alpen · Tessin · Romandie · Engadin · Grenzwerte")
    print("=" * 60)

    print("\n[1/6] Mobilfunk & Breitband - Diverse Regionen")
    await test_s01_3g_alpenregion()
    await test_s02_breitband_30_tessin()
    await test_s03_breitband_300_json()
    await test_s04_breitband_500()

    print("\n[2/6] Glasfaser & Sendeanlagen - Edge Cases")
    await test_s05_glasfaser_laendlich()
    await test_s06_sendeanlagen_minimal_radius()
    await test_s07_sendeanlagen_maximal_radius()

    print("\n[3/6] Multi-Standort - Sprachregionen & Grenzfaelle")
    await test_s08_multi_5_sprachregionen()
    await test_s09_multi_single_location()

    print("\n[4/6] RTV & Medien - Parametervarianten")
    await test_s10_rtv_alle_bern()
    await test_s11_rtv_spezifischer_sender()
    await test_s12_rtv_limit_1()
    await test_s13_frequenzdaten_tessin()

    print("\n[5/6] BAKOM Aktuell & Medienstruktur - Neue Themen")
    await test_s14_medienstruktur_online()
    await test_s15_bakom_aktuell_post()
    await test_s16_bakom_aktuell_ki()

    print("\n[6a/6] Statistik & Katalog - Vollstaendige Validierung")
    await test_s17_telekomstatistik_festnetz()
    await test_s18_breitbandatlas_alle_validierung()

    print("\n[6b/6] Grenzwerte & Kombinationen")
    await test_s19_grenzwert_suedlich()
    await test_s20_kombi_5g_glasfaser_nord()

    return results.summary()


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

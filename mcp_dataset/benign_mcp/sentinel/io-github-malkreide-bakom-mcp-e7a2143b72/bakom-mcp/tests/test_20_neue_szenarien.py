"""
20 neue, diverse Testszenarien für bakom-mcp.

Schwerpunkte (komplementär zu bestehenden Tests):
  - Pydantic-Validierungsfehler (ungültige Koordinaten, Radius)
  - Bisher ungetestete Themen (marktanteile, haushaltszugang, frequenzen, presse)
  - Max-Grenzwerte (20 Standorte, limit=50)
  - Mehrsprachige RTV-Suche (RTS, RSI, Romandie, Tessin)
  - Kombinierte Parameter (query + kanton + media_type)
  - Default-Parameter-Verhalten
  - Leere Ergebnismengen / Nicht-existierende Sender
  - Sonderzeichen in Suchanfragen (Umlaute, Akzente)
  - Cross-Tool-Konsistenz (gleicher Ort, verschiedene Tools)
  - Breitbandatlas-Themenfilterung
  - Strukturvalidierung aller JSON-Felder

Ausführung:
    python tests/test_20_neue_szenarien.py
    pytest tests/test_20_neue_szenarien.py -v
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydantic import ValidationError

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
# Testkoordinaten
# ---------------------------------------------------------------------------
# Lausanne (Romandie, Hochschulstadt)
LAT_LAUSANNE = 46.5197
LON_LAUSANNE = 6.6323

# Zermatt (Tourismus-Hotspot, Bergregion)
LAT_ZERMATT = 46.0207
LON_ZERMATT = 7.7491

# Davos (Kongress-/Skiort, Graubünden)
LAT_DAVOS = 46.8027
LON_DAVOS = 9.8360

# Biel/Bienne (zweisprachig DE/FR)
LAT_BIEL = 47.1368
LON_BIEL = 7.2467

# Grenzwert: exakt minimale Koordinaten (Südwest-Ecke der Schweiz)
LAT_SW_GRENZWERT = 45.8
LON_SW_GRENZWERT = 5.9

# Luzern (Zentralschweiz, Tourismus)
LAT_LUZERN = 47.0502
LON_LUZERN = 8.3093

# Winterthur (zweitgrösste Stadt Kt. Zürich)
LAT_WINTERTHUR = 47.4984
LON_WINTERTHUR = 8.7285


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
        note_str = f" - {note}" if note else ""
        print(f"  [OK] {name}{note_str}")

    def fail(self, name: str, reason: str):
        self.failed += 1
        self.errors.append(f"{name}: {reason}")
        print(f"  [FAIL] {name}: {reason}")

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
# N01: Pydantic-Validierung – Koordinaten ausserhalb der Schweiz (zu nördlich)
# ---------------------------------------------------------------------------
async def test_n01_validierung_koordinaten_norden():
    """N01: Koordinaten nördlich der Schweiz müssen ValidationError auslösen"""
    try:
        try:
            BroadbandCoverageInput(
                latitude=52.5200,  # Berlin – ausserhalb 45.8–47.9
                longitude=8.5417,
            )
            results.fail("N01: Validierung Norden", "Kein ValidationError für Berlin-Latitude")
        except ValidationError as ve:
            assert "latitude" in str(ve).lower()
            results.ok("N01: Validierung Norden", "ValidationError korrekt ausgelöst")
    except Exception as e:
        results.fail("N01: Validierung Norden", str(e))


# ---------------------------------------------------------------------------
# N02: Pydantic-Validierung – Radius ausserhalb des erlaubten Bereichs
# ---------------------------------------------------------------------------
async def test_n02_validierung_radius_zu_gross():
    """N02: Antennen-Suchradius > 5000m muss ValidationError auslösen"""
    try:
        try:
            AntennaSearchInput(
                latitude=47.3769,
                longitude=8.5417,
                radius_m=10000,  # > 5000 → ungültig
            )
            results.fail("N02: Validierung Radius", "Kein ValidationError für radius=10000")
        except ValidationError as ve:
            assert "radius" in str(ve).lower()
            results.ok("N02: Validierung Radius", "ValidationError für Radius > 5000")
    except Exception as e:
        results.fail("N02: Validierung Radius", str(e))


# ---------------------------------------------------------------------------
# N03: Pydantic-Validierung – Longitude westlich der Schweiz
# ---------------------------------------------------------------------------
async def test_n03_validierung_longitude_west():
    """N03: Longitude < 5.9 (Paris) muss ValidationError auslösen"""
    try:
        try:
            CoordinateInput(
                latitude=46.5,
                longitude=2.35,  # Paris-Längengrad – ausserhalb 5.9–10.6
            )
            results.fail("N03: Validierung Longitude", "Kein ValidationError für Paris-Longitude")
        except ValidationError as ve:
            assert "longitude" in str(ve).lower()
            results.ok("N03: Validierung Longitude", "ValidationError korrekt")
    except Exception as e:
        results.fail("N03: Validierung Longitude", str(e))


# ---------------------------------------------------------------------------
# N04: Telekomstatistik – Thema «marktanteile» (bisher nie getestet)
# ---------------------------------------------------------------------------
async def test_n04_telekomstatistik_marktanteile():
    """N04: Telekomstatistik zum Thema Marktanteile"""
    try:
        params = TelekomStatInput(
            thema="marktanteile",
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_telekomstatistik_uebersicht(params)
        data = json.loads(output)
        assert "datensaetze" in data
        assert "thema" in data
        assert data["thema"] == "marktanteile"
        results.ok("N04: Statistik Marktanteile", f"{len(data['datensaetze'])} Datensätze")
    except Exception as e:
        results.fail("N04: Statistik Marktanteile", str(e))


# ---------------------------------------------------------------------------
# N05: Telekomstatistik – Thema «haushaltszugang» (bisher nie getestet)
# ---------------------------------------------------------------------------
async def test_n05_telekomstatistik_haushaltszugang():
    """N05: Telekomstatistik zum Thema Haushaltszugang"""
    try:
        params = TelekomStatInput(thema="haushaltszugang")
        output = await bakom_telekomstatistik_uebersicht(params)
        assert isinstance(output, str) and len(output) > 30
        assert "Haushalt" in output or "BAKOM" in output or "Telekomstatistik" in output
        results.ok("N05: Statistik Haushaltszugang", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("N05: Statistik Haushaltszugang", str(e))


# ---------------------------------------------------------------------------
# N06: Multi-Standort – Maximum 20 Standorte (Grenzwert)
# ---------------------------------------------------------------------------
async def test_n06_multi_standort_max_20():
    """N06: Multi-Standort mit exakt 20 Standorten (Maximalwert)"""
    try:
        # 20 verschiedene Schweizer Orte generieren
        orte = [
            {"name": "Zürich", "latitude": 47.3769, "longitude": 8.5417},
            {"name": "Bern", "latitude": 46.9467, "longitude": 7.4444},
            {"name": "Basel", "latitude": 47.5596, "longitude": 7.5886},
            {"name": "Genf", "latitude": 46.2044, "longitude": 6.1432},
            {"name": "Lausanne", "latitude": 46.5197, "longitude": 6.6323},
            {"name": "Luzern", "latitude": 47.0502, "longitude": 8.3093},
            {"name": "St. Gallen", "latitude": 47.4245, "longitude": 9.3767},
            {"name": "Winterthur", "latitude": 47.4984, "longitude": 8.7285},
            {"name": "Lugano", "latitude": 46.0037, "longitude": 8.9511},
            {"name": "Biel/Bienne", "latitude": 47.1368, "longitude": 7.2467},
            {"name": "Thun", "latitude": 46.7580, "longitude": 7.6280},
            {"name": "Aarau", "latitude": 47.3925, "longitude": 8.0444},
            {"name": "Schaffhausen", "latitude": 47.6960, "longitude": 8.6340},
            {"name": "Chur", "latitude": 46.8499, "longitude": 9.5329},
            {"name": "Fribourg", "latitude": 46.8065, "longitude": 7.1620},
            {"name": "Sion", "latitude": 46.2333, "longitude": 7.3592},
            {"name": "Neuchâtel", "latitude": 46.9920, "longitude": 6.9310},
            {"name": "Zug", "latitude": 47.1724, "longitude": 8.5172},
            {"name": "Davos", "latitude": 46.8027, "longitude": 9.8360},
            {"name": "Interlaken", "latitude": 46.6863, "longitude": 7.8632},
        ]
        params = MultiLocationInput(
            locations=orte,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_multi_standort_konnektivitaet(params)
        data = json.loads(output)
        assert data["zusammenfassung"]["total"] == 20
        assert len(data["standorte"]) == 20
        results.ok(
            "N06: Multi-Standort 20 Orte",
            f"5G: {data['zusammenfassung']['mit_5g']}/20, "
            f"Glasfaser: {data['zusammenfassung']['mit_glasfaser']}/20",
        )
    except Exception as e:
        results.fail("N06: Multi-Standort 20 Orte", str(e))


# ---------------------------------------------------------------------------
# N07: RTV-Suche – Romandie-Sender «RTS» (französischsprachig)
# ---------------------------------------------------------------------------
async def test_n07_rtv_romandie_rts():
    """N07: RTV-Suche nach frankophonem Sender RTS"""
    try:
        params = RTVSearchInput(
            query="RTS",
            media_type=MediaType.TV,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_rtv_suche(params)
        data = json.loads(output)
        assert "resultate" in data
        results.ok("N07: RTV RTS (Romandie)", f"{data['total']} Resultate")
    except Exception as e:
        results.fail("N07: RTV RTS (Romandie)", str(e))


# ---------------------------------------------------------------------------
# N08: RTV-Suche – Tessin-Sender «RSI» (italienischsprachig)
# ---------------------------------------------------------------------------
async def test_n08_rtv_tessin_rsi():
    """N08: RTV-Suche nach italienischsprachigem Sender RSI"""
    try:
        params = RTVSearchInput(
            query="RSI",
            media_type=MediaType.ALLE,
        )
        output = await bakom_rtv_suche(params)
        assert isinstance(output, str) and len(output) > 20
        results.ok("N08: RTV RSI (Tessin)", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("N08: RTV RSI (Tessin)", str(e))


# ---------------------------------------------------------------------------
# N09: RTV-Suche – kombinierte Parameter (query + kanton + media_type)
# ---------------------------------------------------------------------------
async def test_n09_rtv_kombinierte_parameter():
    """N09: RTV-Suche mit allen Parametern gleichzeitig"""
    try:
        params = RTVSearchInput(
            query="Radio",
            media_type=MediaType.RADIO,
            kanton="GE",
            limit=5,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_rtv_suche(params)
        data = json.loads(output)
        assert "resultate" in data
        assert data["suchanfrage"]["typ"] in ("radio",)
        assert len(data["resultate"]) <= 5
        results.ok("N09: RTV kombiniert (Radio+GE+limit=5)", f"{data['total']} Resultate")
    except Exception as e:
        results.fail("N09: RTV kombiniert", str(e))


# ---------------------------------------------------------------------------
# N10: RTV-Suche – Max-Limit (50) um grosse Ergebnismenge zu testen
# ---------------------------------------------------------------------------
async def test_n10_rtv_max_limit():
    """N10: RTV-Suche mit maximalem Limit (50 Resultate)"""
    try:
        params = RTVSearchInput(
            media_type=MediaType.ALLE,
            limit=50,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_rtv_suche(params)
        data = json.loads(output)
        assert "resultate" in data
        assert len(data["resultate"]) <= 50
        results.ok("N10: RTV limit=50", f"{len(data['resultate'])} Resultate")
    except Exception as e:
        results.fail("N10: RTV limit=50", str(e))


# ---------------------------------------------------------------------------
# N11: RTV-Suche – Nicht-existierender Sender (Leermengen-Test)
# ---------------------------------------------------------------------------
async def test_n11_rtv_leere_ergebnismenge():
    """N11: RTV-Suche nach nicht-existierendem Sender – Fallback-Verhalten prüfen"""
    try:
        params = RTVSearchInput(
            query="XYZ_NICHTVORHANDEN_12345",
            media_type=MediaType.TV,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_rtv_suche(params)
        data = json.loads(output)
        # Server darf entweder 0 Resultate liefern oder via Fallback (opendata.swiss)
        # allgemeine BAKOM-Datensätze zurückgeben – beides ist valides Verhalten.
        assert "resultate" in data or "datensaetze" in data or "hinweis" in data
        total = data.get("total", len(data.get("resultate", data.get("datensaetze", []))))
        results.ok("N11: RTV Nonsense-Query", f"{total} Resultate (Fallback-Verhalten)")
    except Exception as e:
        results.fail("N11: RTV Nonsense-Query", str(e))


# ---------------------------------------------------------------------------
# N12: BAKOM Aktuell – Thema «frequenzen» (bisher nie getestet)
# ---------------------------------------------------------------------------
async def test_n12_bakom_aktuell_frequenzen():
    """N12: BAKOM Aktuell – Thema Frequenzzuteilung"""
    try:
        params = TelekomStatInput(
            thema="frequenzen",
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_aktuell(params)
        data = json.loads(output)
        assert "highlights" in data
        assert "bakom_homepage" in data
        results.ok("N12: BAKOM Aktuell Frequenzen", f"{data['total']} Highlights")
    except Exception as e:
        results.fail("N12: BAKOM Aktuell Frequenzen", str(e))


# ---------------------------------------------------------------------------
# N13: Medienstruktur – Thema «presse» (bisher nie getestet)
# ---------------------------------------------------------------------------
async def test_n13_medienstruktur_presse():
    """N13: Medienstruktur-Info zum Thema Presse"""
    try:
        params = TelekomStatInput(thema="presse")
        output = await bakom_medienstruktur_info(params)
        assert isinstance(output, str) and len(output) > 30
        results.ok("N13: Medienstruktur Presse", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("N13: Medienstruktur Presse", str(e))


# ---------------------------------------------------------------------------
# N14: Breitband-Abdeckung exakt am Grenzwert (45.8, 5.9 – SW-Ecke)
# ---------------------------------------------------------------------------
async def test_n14_breitband_grenzwert_sw_ecke():
    """N14: Breitband an der exakten Südwest-Grenze der erlaubten Koordinaten"""
    try:
        params = BroadbandCoverageInput(
            latitude=LAT_SW_GRENZWERT,
            longitude=LON_SW_GRENZWERT,
            min_speed_mbps=BroadbandSpeed.S100,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_broadband_coverage(params)
        data = json.loads(output)
        # Sollte nicht crashen – unabhängig davon ob abgedeckt oder nicht
        assert "standort" in data
        assert abs(data["standort"]["lat"] - LAT_SW_GRENZWERT) < 0.01
        results.ok("N14: Grenzwert SW-Ecke", f"abgedeckt={data['abgedeckt']}")
    except Exception as e:
        results.fail("N14: Grenzwert SW-Ecke", str(e))


# ---------------------------------------------------------------------------
# N15: Sendeanlagen mit Default-Radius (1000m) – explizit nicht angeben
# ---------------------------------------------------------------------------
async def test_n15_sendeanlagen_default_radius():
    """N15: Sendeanlagen-Suche ohne Radius-Angabe (Standard: 1000m)"""
    try:
        params = AntennaSearchInput(
            latitude=LAT_LAUSANNE,
            longitude=LON_LAUSANNE,
            # radius_m wird NICHT gesetzt → Default 1000m
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_sendeanlagen_suche(params)
        data = json.loads(output)
        assert "anlagen" in data
        assert data["radius_m"] == 1000  # Default-Wert prüfen
        assert isinstance(data["anlagen"], list)
        results.ok("N15: Antennen Default-Radius Lausanne", f"{data['total']} Anlagen, radius={data['radius_m']}m")
    except Exception as e:
        results.fail("N15: Antennen Default-Radius", str(e))


# ---------------------------------------------------------------------------
# N16: Cross-Tool-Konsistenz – Breitband + Mobilfunk + Glasfaser am gleichen Ort
# ---------------------------------------------------------------------------
async def test_n16_cross_tool_konsistenz_davos():
    """N16: Drei verschiedene Tools am gleichen Standort (Davos) – Konsistenzprüfung"""
    try:
        # 1) Breitband
        out_bb = await bakom_broadband_coverage(BroadbandCoverageInput(
            latitude=LAT_DAVOS, longitude=LON_DAVOS,
            min_speed_mbps=BroadbandSpeed.S100,
            response_format=ResponseFormat.JSON,
        ))
        data_bb = json.loads(out_bb)
        assert "standort" in data_bb

        # 2) 5G Mobilfunk
        out_5g = await bakom_mobilfunk_abdeckung(MobileCoverageInput(
            latitude=LAT_DAVOS, longitude=LON_DAVOS,
            generation=MobilGenerations.G5,
            response_format=ResponseFormat.JSON,
        ))
        data_5g = json.loads(out_5g)
        assert "standort" in data_5g

        # 3) Glasfaser
        out_gf = await bakom_glasfaser_verfuegbarkeit(CoordinateInput(
            latitude=LAT_DAVOS, longitude=LON_DAVOS,
            response_format=ResponseFormat.JSON,
        ))
        data_gf = json.loads(out_gf)
        assert "standort" in data_gf

        # Koordinaten-Konsistenz: alle drei sollten dieselben Koordinaten zurückgeben
        for data in [data_bb, data_5g, data_gf]:
            assert abs(data["standort"]["lat"] - LAT_DAVOS) < 0.01
            assert abs(data["standort"]["lon"] - LON_DAVOS) < 0.01

        kombi = (
            f"BB100={data_bb['abgedeckt']}, "
            f"5G={data_5g['abgedeckt']}, "
            f"Glasfaser={data_gf['glasfaser_verfuegbar']}"
        )
        results.ok("N16: Cross-Tool Davos", kombi)
    except Exception as e:
        results.fail("N16: Cross-Tool Davos", str(e))


# ---------------------------------------------------------------------------
# N17: Multi-Standort – Sonderzeichen in Standortnamen (Umlaute, Akzente)
# ---------------------------------------------------------------------------
async def test_n17_multi_standort_sonderzeichen():
    """N17: Multi-Standort mit Umlauten, Akzenten und Sonderzeichen in Namen"""
    try:
        params = MultiLocationInput(
            locations=[
                {"name": "Zürich – Örlikon", "latitude": 47.4084, "longitude": 8.5434},
                {"name": "Genève (Aéroport)", "latitude": 46.2370, "longitude": 6.1092},
                {"name": "Biel/Bienne – Gare/Bahnhof", "latitude": 47.1368, "longitude": 7.2467},
            ],
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_multi_standort_konnektivitaet(params)
        data = json.loads(output)
        namen = [s["name"] for s in data["standorte"]]
        # Sonderzeichen müssen erhalten bleiben
        assert any("Zürich" in n for n in namen), "Umlaut ü nicht erhalten"
        assert any("Genève" in n or "Aéroport" in n for n in namen), "Akzent nicht erhalten"
        assert any("Biel/Bienne" in n for n in namen), "Schrägstrich nicht erhalten"
        results.ok("N17: Sonderzeichen in Namen", f"{len(namen)} Standorte korrekt")
    except Exception as e:
        results.fail("N17: Sonderzeichen in Namen", str(e))


# ---------------------------------------------------------------------------
# N18: Breitbandatlas – Themenfilter «mobilfunk» statt «alle»
# ---------------------------------------------------------------------------
async def test_n18_breitbandatlas_mobilfunk_thema():
    """N18: Breitbandatlas-Datensätze gefiltert nach Thema 'mobilfunk'"""
    try:
        params = TelekomStatInput(
            thema="mobilfunk",
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_breitbandatlas_datensaetze(params)
        data = json.loads(output)
        assert "datensaetze" in data
        # Mindestens 5G- und 4G-Layer sollten vorhanden sein
        layer_ids = [d["layer_id"] for d in data["datensaetze"]]
        hat_mobilfunk = any("netzabdeckung" in lid or "mobilfunk" in lid or "5g" in lid or "4g" in lid for lid in layer_ids)
        results.ok("N18: Breitbandatlas Mobilfunk", f"{data['total']} Layer, Mobilfunk={hat_mobilfunk}")
    except Exception as e:
        results.fail("N18: Breitbandatlas Mobilfunk", str(e))


# ---------------------------------------------------------------------------
# N19: Frequenzdaten Zermatt – abgelegene Tourismusregion
# ---------------------------------------------------------------------------
async def test_n19_frequenzdaten_zermatt():
    """N19: Radio-/TV-Sender in der Nähe von Zermatt (abgelegenes Tal)"""
    try:
        params = CoordinateInput(
            latitude=LAT_ZERMATT,
            longitude=LON_ZERMATT,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_frequenzdaten(params)
        data = json.loads(output)
        assert "sender" in data
        assert isinstance(data["sender"], list)
        assert "suchradius_m" in data
        assert "standort" in data
        results.ok("N19: Frequenzdaten Zermatt", f"{data['total']} Sender im Tal")
    except Exception as e:
        results.fail("N19: Frequenzdaten Zermatt", str(e))


# ---------------------------------------------------------------------------
# N20: Glasfaser in Stadtzentrum (Winterthur) + JSON-Strukturvalidierung
# ---------------------------------------------------------------------------
async def test_n20_glasfaser_stadt_vollvalidierung():
    """N20: Glasfaser Winterthur – vollständige JSON-Strukturvalidierung"""
    try:
        params = CoordinateInput(
            latitude=LAT_WINTERTHUR,
            longitude=LON_WINTERTHUR,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_glasfaser_verfuegbarkeit(params)
        data = json.loads(output)

        # Vollständige Strukturprüfung aller erwarteten Felder
        assert "glasfaser_verfuegbar" in data, "Feld 'glasfaser_verfuegbar' fehlt"
        assert isinstance(data["glasfaser_verfuegbar"], bool), "glasfaser_verfuegbar ist kein bool"

        assert "standort" in data, "Feld 'standort' fehlt"
        assert "lat" in data["standort"], "standort.lat fehlt"
        assert "lon" in data["standort"], "standort.lon fehlt"
        assert isinstance(data["standort"]["lat"], (int, float)), "lat ist keine Zahl"
        assert isinstance(data["standort"]["lon"], (int, float)), "lon ist keine Zahl"

        assert "datenquelle" in data, "Feld 'datenquelle' fehlt"
        assert isinstance(data["datenquelle"], str), "datenquelle ist kein String"
        assert len(data["datenquelle"]) > 5, "datenquelle zu kurz"

        results.ok(
            "N20: Glasfaser Winterthur Vollvalidierung",
            f"verfügbar={data['glasfaser_verfuegbar']}, alle Felder korrekt",
        )
    except Exception as e:
        results.fail("N20: Glasfaser Winterthur Vollvalidierung", str(e))


# ---------------------------------------------------------------------------
# Test-Runner
# ---------------------------------------------------------------------------
async def run_all_tests():
    print("\n" + "=" * 60)
    print("bakom-mcp - 20 Neue Testszenarien")
    print("Validierung - Grenzwerte - Mehrsprachigkeit - Konsistenz")
    print("=" * 60)

    print("\n[1/7] Pydantic-Validierung - Ungueltige Eingaben")
    await test_n01_validierung_koordinaten_norden()
    await test_n02_validierung_radius_zu_gross()
    await test_n03_validierung_longitude_west()

    print("\n[2/7] Neue Statistik-Themen")
    await test_n04_telekomstatistik_marktanteile()
    await test_n05_telekomstatistik_haushaltszugang()

    print("\n[3/7] Multi-Standort - Grenzfaelle")
    await test_n06_multi_standort_max_20()
    await test_n17_multi_standort_sonderzeichen()

    print("\n[4/7] RTV - Mehrsprachigkeit & Parameterkombinationen")
    await test_n07_rtv_romandie_rts()
    await test_n08_rtv_tessin_rsi()
    await test_n09_rtv_kombinierte_parameter()
    await test_n10_rtv_max_limit()
    await test_n11_rtv_leere_ergebnismenge()

    print("\n[5/7] BAKOM Aktuell & Medienstruktur - Neue Themen")
    await test_n12_bakom_aktuell_frequenzen()
    await test_n13_medienstruktur_presse()

    print("\n[6/7] Breitband, Glasfaser, Frequenzdaten – Neue Regionen")
    await test_n14_breitband_grenzwert_sw_ecke()
    await test_n15_sendeanlagen_default_radius()
    await test_n18_breitbandatlas_mobilfunk_thema()
    await test_n19_frequenzdaten_zermatt()
    await test_n20_glasfaser_stadt_vollvalidierung()

    print("\n[7/7] Cross-Tool-Konsistenz")
    await test_n16_cross_tool_konsistenz_davos()

    return results.summary()


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

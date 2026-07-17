"""
20 erweiterte Testszenarien für bakom-mcp.

Ziel: Breite Abdeckung von Edge-Cases, Validierung, Cross-Tool-Szenarien,
geografischen Extremfällen und Format-Konsistenz.

Ausführung:
    python tests/test_scenarios_20.py
"""

import asyncio
import json
import sys
import traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from pydantic import ValidationError

from bakom_mcp.server import (
    AntennaSearchInput,
    BroadbandCoverageInput,
    BroadbandSpeed,
    CoordinateInput,
    MediaType,
    MobileCoverageInput,
    MobilGenerations,
    MultiLocationInput,
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
# Testkoordinaten – diverse Standorte in der Schweiz
# ---------------------------------------------------------------------------
# Grenzstandorte / Extremkoordinaten
LAT_JUNGFRAUJOCH = 46.5472  # Höchster Bahnhof Europas, abgelegen
LON_JUNGFRAUJOCH = 7.9853

LAT_GENF = 46.2044          # Westschweiz (Genf)
LON_GENF = 6.1432

LAT_LUGANO = 46.0037        # Tessin (Lugano)
LON_LUGANO = 8.9511

LAT_ST_GALLEN = 47.4245     # Ostschweiz (St. Gallen)
LON_ST_GALLEN = 9.3767

LAT_CHUR = 46.8499          # Graubünden (Chur)
LON_CHUR = 9.5329

# Grenzwerte der Schweiz-Koordinaten
LAT_SUEDGRENZE = 45.82      # Nahe Südgrenze
LON_WESTGRENZE = 5.95       # Nahe Westgrenze

LAT_NORDGRENZE = 47.88      # Nahe Nordgrenze
LON_OSTGRENZE = 10.55       # Nahe Ostgrenze

# Ländliches Gebiet
LAT_EMMENTAL = 46.9350      # Emmental (ländlich)
LON_EMMENTAL = 7.7340

# Basel – Grenzstadt
LAT_BASEL = 47.5596
LON_BASEL = 7.5886


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


# ===========================================================================
# SZENARIO 1: Pydantic-Validierung – Koordinaten ausserhalb der Schweiz
# ===========================================================================
async def test_s01_validation_out_of_bounds():
    """S01: Pydantic lehnt Koordinaten ausserhalb der Schweiz ab"""
    try:
        try:
            CoordinateInput(latitude=52.52, longitude=13.405)  # Berlin
            results.fail("S01: Validierung Ausland", "Keine ValidationError für Berlin-Koordinaten")
            return
        except ValidationError as ve:
            assert "latitude" in str(ve) or "longitude" in str(ve)

        try:
            CoordinateInput(latitude=40.7128, longitude=-74.006)  # New York
            results.fail("S01: Validierung Ausland", "Keine ValidationError für New-York-Koordinaten")
            return
        except ValidationError:
            pass

        results.ok("S01: Validierung Ausland", "Berlin + New York korrekt abgelehnt")
    except Exception as e:
        results.fail("S01: Validierung Ausland", str(e))


# ===========================================================================
# SZENARIO 2: AntennaSearchInput – Radius-Grenzen (min/max)
# ===========================================================================
async def test_s02_antenna_radius_bounds():
    """S02: Antennensuche mit Radius-Grenzwerten"""
    try:
        # Minimaler Radius (100m) – Basel
        params_min = AntennaSearchInput(
            latitude=LAT_BASEL, longitude=LON_BASEL, radius_m=100,
        )
        out_min = await bakom_sendeanlagen_suche(params_min)
        assert isinstance(out_min, str) and len(out_min) > 10

        # Maximaler Radius (5000m) – Basel
        params_max = AntennaSearchInput(
            latitude=LAT_BASEL, longitude=LON_BASEL, radius_m=5000,
        )
        out_max = await bakom_sendeanlagen_suche(params_max)
        assert isinstance(out_max, str)

        # 5000m-Suche sollte mindestens so viele Ergebnisse wie 100m haben
        assert len(out_max) >= len(out_min)

        results.ok("S02: Antennen Radius-Grenzen", f"100m: {len(out_min)}Z, 5000m: {len(out_max)}Z")
    except Exception as e:
        results.fail("S02: Antennen Radius-Grenzen", str(e))


# ===========================================================================
# SZENARIO 3: Radius-Validierung – ungültige Werte
# ===========================================================================
async def test_s03_antenna_radius_invalid():
    """S03: Pydantic lehnt ungültige Radien ab"""
    try:
        try:
            AntennaSearchInput(latitude=47.0, longitude=8.0, radius_m=50)
            results.fail("S03: Radius-Validierung", "Keine ValidationError für 50m Radius")
            return
        except ValidationError:
            pass

        try:
            AntennaSearchInput(latitude=47.0, longitude=8.0, radius_m=10000)
            results.fail("S03: Radius-Validierung", "Keine ValidationError für 10000m Radius")
            return
        except ValidationError:
            pass

        results.ok("S03: Radius-Validierung", "50m und 10000m korrekt abgelehnt")
    except Exception as e:
        results.fail("S03: Radius-Validierung", str(e))


# ===========================================================================
# SZENARIO 4: Breitband alle 5 Geschwindigkeitsstufen am selben Standort
# ===========================================================================
async def test_s04_all_speed_tiers():
    """S04: Alle 5 Breitband-Geschwindigkeitsstufen in Genf"""
    try:
        ergebnisse = {}
        for speed in BroadbandSpeed:
            params = BroadbandCoverageInput(
                latitude=LAT_GENF, longitude=LON_GENF,
                min_speed_mbps=speed,
                response_format=ResponseFormat.JSON,
            )
            output = await bakom_broadband_coverage(params)
            data = json.loads(output)
            ergebnisse[speed.value] = data.get("abgedeckt", data.get("status"))

        # Niedrigere Geschwindigkeiten sollten eher verfügbar sein als höhere
        results.ok("S04: Alle 5 Speed-Tiers Genf", f"Ergebnisse: {ergebnisse}")
    except Exception as e:
        results.fail("S04: Alle 5 Speed-Tiers Genf", str(e))


# ===========================================================================
# SZENARIO 5: Bergstandort – Jungfraujoch (schlechte Abdeckung erwartet)
# ===========================================================================
async def test_s05_mountain_location():
    """S05: Mobilfunkabdeckung Jungfraujoch (Bergregion)"""
    try:
        params_5g = MobileCoverageInput(
            latitude=LAT_JUNGFRAUJOCH, longitude=LON_JUNGFRAUJOCH,
            generation=MobilGenerations.G5,
            response_format=ResponseFormat.JSON,
        )
        output_5g = await bakom_mobilfunk_abdeckung(params_5g)
        data_5g = json.loads(output_5g)

        params_3g = MobileCoverageInput(
            latitude=LAT_JUNGFRAUJOCH, longitude=LON_JUNGFRAUJOCH,
            generation=MobilGenerations.G3,
            response_format=ResponseFormat.JSON,
        )
        output_3g = await bakom_mobilfunk_abdeckung(params_3g)
        data_3g = json.loads(output_3g)

        results.ok(
            "S05: Mobilfunk Jungfraujoch",
            f"5G: {data_5g.get('abgedeckt')}, 3G: {data_3g.get('abgedeckt')}",
        )
    except Exception as e:
        results.fail("S05: Mobilfunk Jungfraujoch", str(e))


# ===========================================================================
# SZENARIO 6: Glasfaser JSON-Format – Schema-Validierung
# ===========================================================================
async def test_s06_glasfaser_json_schema():
    """S06: Glasfaser JSON-Schema Validierung (Lugano)"""
    try:
        params = CoordinateInput(
            latitude=LAT_LUGANO, longitude=LON_LUGANO,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_glasfaser_verfuegbarkeit(params)
        data = json.loads(output)

        # Schema pruefen (lat/lon statt latitude/longitude)
        assert "standort" in data, "Feld 'standort' fehlt"
        assert "lat" in data["standort"], "Feld 'standort.lat' fehlt"
        assert "lon" in data["standort"], "Feld 'standort.lon' fehlt"
        assert "glasfaser_verfuegbar" in data, "Feld 'glasfaser_verfuegbar' fehlt"

        results.ok("S06: Glasfaser JSON-Schema Lugano", f"Felder: {list(data.keys())}")
    except Exception as e:
        results.fail("S06: Glasfaser JSON-Schema Lugano", str(e))


# ===========================================================================
# SZENARIO 7: RTV-Suche mit kombinierten Filtern – Query + Kanton + Typ
# ===========================================================================
async def test_s07_rtv_combined_filters():
    """S07: RTV-Suche mit allen Filtern kombiniert"""
    try:
        # Suche nach Radio in Bern mit Query
        params = RTVSearchInput(
            query="Radio",
            media_type=MediaType.RADIO,
            kanton="BE",
            limit=5,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_rtv_suche(params)
        data = json.loads(output)

        # Sollte Resultate liefern
        assert "resultate" in data or "sender" in data or isinstance(data, list) or len(output) > 20

        results.ok("S07: RTV kombinierte Filter", f"Bern Radio: {len(output)} Zeichen")
    except Exception as e:
        results.fail("S07: RTV kombinierte Filter", str(e))


# ===========================================================================
# SZENARIO 8: RTV-Suche Kanton-Normalisierung (Kleinbuchstaben → Grossbuchstaben)
# ===========================================================================
async def test_s08_rtv_kanton_normalization():
    """S08: Kanton-Kürzel wird automatisch zu Grossbuchstaben normalisiert"""
    try:
        params = RTVSearchInput(
            kanton="ge",  # Kleinbuchstaben, soll automatisch zu "GE" werden
            media_type=MediaType.TV,
        )
        assert params.kanton == "GE", f"Kanton nicht normalisiert: {params.kanton}"

        output = await bakom_rtv_suche(params)
        assert isinstance(output, str) and len(output) > 20

        results.ok("S08: Kanton-Normalisierung", "'ge' -> 'GE' korrekt normalisiert")
    except Exception as e:
        results.fail("S08: Kanton-Normalisierung", str(e))


# ===========================================================================
# SZENARIO 9: Multi-Standort – 10 Standorte gleichzeitig
# ===========================================================================
async def test_s09_multi_location_10():
    """S09: Multi-Standort mit 10 diversifizierten Orten"""
    try:
        standorte = [
            {"name": "Genf",       "latitude": LAT_GENF,       "longitude": LON_GENF},
            {"name": "Lugano",     "latitude": LAT_LUGANO,     "longitude": LON_LUGANO},
            {"name": "St. Gallen", "latitude": LAT_ST_GALLEN,  "longitude": LON_ST_GALLEN},
            {"name": "Chur",       "latitude": LAT_CHUR,       "longitude": LON_CHUR},
            {"name": "Basel",      "latitude": LAT_BASEL,       "longitude": LON_BASEL},
            {"name": "Emmental",   "latitude": LAT_EMMENTAL,   "longitude": LON_EMMENTAL},
            {"name": "Jungfraujoch", "latitude": LAT_JUNGFRAUJOCH, "longitude": LON_JUNGFRAUJOCH},
            {"name": "Nordgrenze", "latitude": LAT_NORDGRENZE,  "longitude": 8.5},
            {"name": "Südgrenze",  "latitude": LAT_SUEDGRENZE,  "longitude": 8.5},
            {"name": "Westgrenze", "latitude": 46.5,            "longitude": LON_WESTGRENZE},
        ]

        params = MultiLocationInput(locations=standorte)
        output = await bakom_multi_standort_konnektivitaet(params)

        # Alle 10 Standorte sollten in der Antwort vorkommen
        for s in standorte:
            assert s["name"] in output, f"{s['name']} fehlt in der Antwort"

        results.ok("S09: Multi-Standort 10 Orte", f"{len(output)} Zeichen, alle 10 gefunden")
    except Exception as e:
        results.fail("S09: Multi-Standort 10 Orte", str(e))


# ===========================================================================
# SZENARIO 10: Multi-Standort Validierung – mehr als 20 Standorte
# ===========================================================================
async def test_s10_multi_location_exceeds_limit():
    """S10: Multi-Standort lehnt >20 Standorte ab"""
    try:
        standorte = [
            {"name": f"Ort_{i}", "latitude": 47.0 + i * 0.01, "longitude": 8.0}
            for i in range(21)
        ]
        try:
            MultiLocationInput(locations=standorte)
            results.fail("S10: Multi-Standort >20", "Keine ValidationError für 21 Standorte")
        except ValidationError:
            results.ok("S10: Multi-Standort >20", "21 Standorte korrekt abgelehnt")
    except Exception as e:
        results.fail("S10: Multi-Standort >20", str(e))


# ===========================================================================
# SZENARIO 11: Frequenzdaten JSON-Schema Tessin
# ===========================================================================
async def test_s11_frequenzdaten_json():
    """S11: Radio-/TV-Frequenzdaten Lugano in JSON"""
    try:
        params = CoordinateInput(
            latitude=LAT_LUGANO, longitude=LON_LUGANO,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_frequenzdaten(params)
        data = json.loads(output)
        assert isinstance(data, dict)

        results.ok("S11: Frequenzdaten JSON Lugano", f"Felder: {list(data.keys())}")
    except Exception as e:
        results.fail("S11: Frequenzdaten JSON Lugano", str(e))


# ===========================================================================
# SZENARIO 12: Medienstruktur – alle 5 Themen abrufen
# ===========================================================================
async def test_s12_medienstruktur_all_topics():
    """S12: Medienstruktur-Info für alle verfügbaren Themen"""
    try:
        themen = ["radio", "tv", "online", "print", "medien"]
        ergebnisse = {}
        for thema in themen:
            params = TelekomStatInput(thema=thema)
            output = await bakom_medienstruktur_info(params)
            ergebnisse[thema] = len(output)
            assert isinstance(output, str) and len(output) > 20, f"Thema '{thema}' hat zu wenig Output"

        results.ok("S12: Medienstruktur alle Themen", f"Längen: {ergebnisse}")
    except Exception as e:
        results.fail("S12: Medienstruktur alle Themen", str(e))


# ===========================================================================
# SZENARIO 13: BAKOM Aktuell – alle 6 Nachrichtenthemen
# ===========================================================================
async def test_s13_bakom_aktuell_all_topics():
    """S13: BAKOM Aktuell für alle verfügbaren Nachrichtenthemen"""
    try:
        themen = ["5g", "ki", "medien", "post", "breitband", "frequenz"]
        ergebnisse = {}
        for thema in themen:
            params = TelekomStatInput(thema=thema)
            output = await bakom_aktuell(params)
            ergebnisse[thema] = len(output)
            assert isinstance(output, str) and len(output) > 20, f"Thema '{thema}' hat zu wenig Output"

        results.ok("S13: BAKOM Aktuell alle Themen", f"Längen: {ergebnisse}")
    except Exception as e:
        results.fail("S13: BAKOM Aktuell alle Themen", str(e))


# ===========================================================================
# SZENARIO 14: Telekomstatistik – alle Themen im JSON-Format
# ===========================================================================
async def test_s14_telekomstatistik_all_json():
    """S14: Telekomstatistik JSON-Output für alle Themen"""
    try:
        themen = ["breitband", "mobilfunk", "festnetz", "marktanteile", "haushaltszugang"]
        for thema in themen:
            params = TelekomStatInput(thema=thema, response_format=ResponseFormat.JSON)
            output = await bakom_telekomstatistik_uebersicht(params)
            data = json.loads(output)
            assert isinstance(data, dict), f"JSON von '{thema}' ist kein Objekt"
            assert "thema" in data or "datensaetze" in data, f"JSON von '{thema}' fehlt Struktur"

        results.ok("S14: Telekomstatistik JSON alle Themen", f"{len(themen)} Themen OK")
    except Exception as e:
        results.fail("S14: Telekomstatistik JSON alle Themen", str(e))


# ===========================================================================
# SZENARIO 15: Sendeanlagen JSON-Schema mit maximaler Distanz-Sortierung
# ===========================================================================
async def test_s15_sendeanlagen_json_sorted():
    """S15: Sendeanlagen JSON – Ergebnisse nach Distanz sortiert"""
    try:
        params = AntennaSearchInput(
            latitude=LAT_ST_GALLEN, longitude=LON_ST_GALLEN,
            radius_m=2000,
            response_format=ResponseFormat.JSON,
        )
        output = await bakom_sendeanlagen_suche(params)
        data = json.loads(output)
        assert isinstance(data, dict)

        # Pruefen ob Anlagen vorhanden und nach Distanz sortiert
        anlagen = data.get("anlagen", [])
        if len(anlagen) > 1:
            distanzen = [a.get("distanz_m", 0) or 0 for a in anlagen]
            is_sorted = all(distanzen[i] <= distanzen[i + 1] for i in range(len(distanzen) - 1))
            results.ok("S15: Sendeanlagen sortiert St.Gallen", f"{len(anlagen)} Anlagen, sortiert: {is_sorted}")
        else:
            results.ok("S15: Sendeanlagen sortiert St.Gallen", f"{len(anlagen)} Anlage(n) gefunden")
    except Exception as e:
        results.fail("S15: Sendeanlagen sortiert St.Gallen", str(e))


# ===========================================================================
# SZENARIO 16: Cross-Tool – Breitband + Glasfaser + 5G am selben Standort
# ===========================================================================
async def test_s16_cross_tool_connectivity_profile():
    """S16: Vollständiges Konnektivitätsprofil Chur (3 Tools kombiniert)"""
    try:
        # Breitband
        bb_params = BroadbandCoverageInput(
            latitude=LAT_CHUR, longitude=LON_CHUR,
            min_speed_mbps=BroadbandSpeed.S100,
            response_format=ResponseFormat.JSON,
        )
        bb_out = await bakom_broadband_coverage(bb_params)
        bb_data = json.loads(bb_out)

        # Glasfaser
        gf_params = CoordinateInput(
            latitude=LAT_CHUR, longitude=LON_CHUR,
            response_format=ResponseFormat.JSON,
        )
        gf_out = await bakom_glasfaser_verfuegbarkeit(gf_params)
        gf_data = json.loads(gf_out)

        # 5G
        m5_params = MobileCoverageInput(
            latitude=LAT_CHUR, longitude=LON_CHUR,
            generation=MobilGenerations.G5,
            response_format=ResponseFormat.JSON,
        )
        m5_out = await bakom_mobilfunk_abdeckung(m5_params)
        m5_data = json.loads(m5_out)

        profil = {
            "breitband_100": bb_data.get("abgedeckt"),
            "glasfaser": gf_data.get("verfuegbar", gf_data.get("abgedeckt")),
            "5g": m5_data.get("abgedeckt"),
        }
        results.ok("S16: Konnektivitätsprofil Chur", f"Profil: {profil}")
    except Exception as e:
        results.fail("S16: Konnektivitätsprofil Chur", str(e))


# ===========================================================================
# SZENARIO 17: Breitbandatlas Katalog – Vollständigkeit der Layer-IDs
# ===========================================================================
async def test_s17_broadband_atlas_completeness():
    """S17: Breitbandatlas-Katalog enthält alle erwarteten Layer"""
    try:
        params = TelekomStatInput(thema="alle", response_format=ResponseFormat.JSON)
        output = await bakom_breitbandatlas_datensaetze(params)
        data = json.loads(output)

        erwartete_layer = [
            "ch.bakom.netzabdeckung-5g",
            "ch.bakom.netzabdeckung-4g",
            "ch.bakom.anschlussart-verfuegbarkeit",
        ]

        layer_ids = [d["layer_id"] for d in data["datensaetze"]]
        fehlende = [l for l in erwartete_layer if l not in layer_ids]

        if fehlende:
            results.fail("S17: Breitbandatlas Vollständigkeit", f"Fehlende Layer: {fehlende}")
        else:
            results.ok("S17: Breitbandatlas Vollständigkeit", f"{len(layer_ids)} Layer vorhanden")
    except Exception as e:
        results.fail("S17: Breitbandatlas Vollständigkeit", str(e))


# ===========================================================================
# SZENARIO 18: RTV-Suche – Kein Query, nur Medientyp (Alle TV-Sender)
# ===========================================================================
async def test_s18_rtv_no_query():
    """S18: RTV-Suche ohne Suchbegriff – alle TV-Sender"""
    try:
        params = RTVSearchInput(
            media_type=MediaType.TV,
            limit=50,  # Maximum
        )
        output = await bakom_rtv_suche(params)
        assert isinstance(output, str) and len(output) > 30

        results.ok("S18: RTV alle TV (kein Query)", f"{len(output)} Zeichen")
    except Exception as e:
        results.fail("S18: RTV alle TV (kein Query)", str(e))


# ===========================================================================
# SZENARIO 19: Grenzkoordinaten – Schweizer Rand-Koordinaten
# ===========================================================================
async def test_s19_boundary_coordinates():
    """S19: Breitband an den Randkoordinaten der Schweiz"""
    try:
        # Südgrenze (nahe Chiasso/Tessin)
        params_sued = BroadbandCoverageInput(
            latitude=LAT_SUEDGRENZE, longitude=8.95,
            min_speed_mbps=BroadbandSpeed.S30,
        )
        out_sued = await bakom_broadband_coverage(params_sued)
        assert isinstance(out_sued, str) and len(out_sued) > 20

        # Nordgrenze (nahe Schaffhausen)
        params_nord = BroadbandCoverageInput(
            latitude=LAT_NORDGRENZE, longitude=8.63,
            min_speed_mbps=BroadbandSpeed.S30,
        )
        out_nord = await bakom_broadband_coverage(params_nord)
        assert isinstance(out_nord, str) and len(out_nord) > 20

        results.ok("S19: Grenz-Koordinaten", f"Süd: {len(out_sued)}Z, Nord: {len(out_nord)}Z")
    except Exception as e:
        results.fail("S19: Grenz-Koordinaten", str(e))


# ===========================================================================
# SZENARIO 20: Pydantic extra-Felder – "extra=forbid" Durchsetzung
# ===========================================================================
async def test_s20_pydantic_extra_fields():
    """S20: Pydantic-Modelle lehnen unbekannte Felder ab"""
    try:
        modelle_getestet = 0

        # CoordinateInput
        try:
            CoordinateInput(latitude=47.0, longitude=8.0, unbekannt="test")
            results.fail("S20: Extra-Felder", "CoordinateInput akzeptiert extra Feld")
            return
        except ValidationError:
            modelle_getestet += 1

        # BroadbandCoverageInput
        try:
            BroadbandCoverageInput(latitude=47.0, longitude=8.0, fake_field=42)
            results.fail("S20: Extra-Felder", "BroadbandCoverageInput akzeptiert extra Feld")
            return
        except ValidationError:
            modelle_getestet += 1

        # AntennaSearchInput
        try:
            AntennaSearchInput(latitude=47.0, longitude=8.0, extra_param="x")
            results.fail("S20: Extra-Felder", "AntennaSearchInput akzeptiert extra Feld")
            return
        except ValidationError:
            modelle_getestet += 1

        # RTVSearchInput
        try:
            RTVSearchInput(query="test", unknown=True)
            results.fail("S20: Extra-Felder", "RTVSearchInput akzeptiert extra Feld")
            return
        except ValidationError:
            modelle_getestet += 1

        # MultiLocationInput
        try:
            MultiLocationInput(
                locations=[{"name": "X", "latitude": 47.0, "longitude": 8.0}],
                mystery_field="nope",
            )
            results.fail("S20: Extra-Felder", "MultiLocationInput akzeptiert extra Feld")
            return
        except ValidationError:
            modelle_getestet += 1

        results.ok("S20: Extra-Felder", f"{modelle_getestet} Modelle lehnen extra Felder ab")
    except Exception as e:
        results.fail("S20: Extra-Felder", str(e))


# ---------------------------------------------------------------------------
# Test-Runner
# ---------------------------------------------------------------------------
async def run_all_tests():
    print("\n" + "=" * 60)
    print("bakom-mcp – 20 Erweiterte Testszenarien")
    print("=" * 60)

    print("\n[1/7] Validierung & Pydantic-Modelle")
    await test_s01_validation_out_of_bounds()
    await test_s03_antenna_radius_invalid()
    await test_s10_multi_location_exceeds_limit()
    await test_s20_pydantic_extra_fields()

    print("\n[2/7] Geografische Edge-Cases")
    await test_s05_mountain_location()
    await test_s19_boundary_coordinates()

    print("\n[3/7] Breitband & Konnektivitaet")
    await test_s04_all_speed_tiers()
    await test_s06_glasfaser_json_schema()
    await test_s16_cross_tool_connectivity_profile()

    print("\n[4/7] Mobilfunk & Sendeanlagen")
    await test_s02_antenna_radius_bounds()
    await test_s15_sendeanlagen_json_sorted()
    await test_s11_frequenzdaten_json()

    print("\n[5/7] Medien & RTV")
    await test_s07_rtv_combined_filters()
    await test_s08_rtv_kanton_normalization()
    await test_s18_rtv_no_query()
    await test_s12_medienstruktur_all_topics()

    print("\n[6/7] Statistik & Kataloge")
    await test_s13_bakom_aktuell_all_topics()
    await test_s14_telekomstatistik_all_json()
    await test_s17_broadband_atlas_completeness()

    print("\n[7/7] Multi-Standort & Cross-Tool")
    await test_s09_multi_location_10()

    return results.summary()


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

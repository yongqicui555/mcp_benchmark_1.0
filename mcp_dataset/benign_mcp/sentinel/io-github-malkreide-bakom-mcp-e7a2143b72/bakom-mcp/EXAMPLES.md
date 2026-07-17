# Use Cases & Examples — bakom-mcp

Real-world queries by audience. Indicate per example whether an API key is required.

## 🏫 Bildung & Schule
Lehrpersonen, Schulbehörden, Fachreferent:innen

**Glasfaseranschluss an Schulstandorten prüfen**
«Welche unserer Schulhäuser in Zürich haben bereits einen Glasfaseranschluss (FTTB/FTTH)? Bitte überprüfe die Standorte an der Limmatstrasse 114 (47.3822, 8.5323) und Hirschengraben 46 (47.3734, 8.5487).»
→ `bakom_multi_standort_konnektivitaet(locations=[{"name": "Limmatstrasse 114", "latitude": 47.3822, "longitude": 8.5323}, {"name": "Hirschengraben 46", "latitude": 47.3734, "longitude": 8.5487}])`
Warum nützlich: Erlaubt Schulbehörden, die digitale Infrastruktur verschiedener Schulstandorte schnell zu vergleichen, um Investitionen in die Digitalisierung gezielt zu planen.

**Medienkompetenz im Unterricht: Regionale TV- und Radiosender analysieren**
«Welche lokalen Fernseh- und Radiosender gibt es eigentlich im Kanton Bern? Suche nach lizenzierten Sendern, die wir im Medienunterricht behandeln könnten.»
→ `bakom_rtv_suche(kanton="BE", media_type="alle", limit=20)`
Warum nützlich: Hilft Lehrpersonen bei der Vorbereitung von Unterrichtsmaterialien zur Schweizer Medienlandschaft durch konkrete, lokale Praxisbeispiele.

## 👨👩👧 Eltern & Schulgemeinde
Elternräte, interessierte Erziehungsberechtigte

**Mobilfunkabdeckung und 5G am Wohnort**
«Wir ziehen demnächst um (47.4148, 8.5654). Wie gut ist dort die 5G-Mobilfunkabdeckung im Aussenbereich?»
→ `bakom_mobilfunk_abdeckung(latitude=47.4148, longitude=8.5654, generation="5G")`
Warum nützlich: Bietet Familien eine rasche Entscheidungshilfe bei der Wohnortwahl oder beim Abschluss von Mobilfunkabos für ihre Kinder.

**Sendeanlagen in der Nähe des Kindergartens**
«Gibt es Mobilfunk- oder andere Sendeanlagen im Umkreis von 500 Metern um den Kindergarten an unserem neuen Wohnort (47.3769, 8.5417)?»
→ `bakom_sendeanlagen_suche(latitude=47.3769, longitude=8.5417, radius_m=500)`
Warum nützlich: Beantwortet konkrete Gesundheits- und Infrastrukturfragen besorgter Eltern auf Basis offizieller BAKOM-Geodaten.

## 🗳️ Bevölkerung & öffentliches Interesse
Allgemeine Öffentlichkeit, politisch und gesellschaftlich Interessierte

**Medienstruktur und Presseförderung verstehen**
«Wo finde ich aktuelle Berichte oder Datensätze des BAKOM zur Schweizer Medienstruktur und Presseförderung?»
→ `bakom_medienstruktur_info(thema="medien")`
Warum nützlich: Fördert die politische Meinungsbildung durch direkten Zugang zu offiziellen Strukturberichten vor medienpolitischen Abstimmungen.

**Konnektivität und schnelles Internet prüfen**
«Ist an meiner Adresse (46.9479, 7.4446) eigentlich Internet mit einer Geschwindigkeit von mindestens 1000 Mbit/s verfügbar?»
→ `bakom_broadband_coverage(latitude=46.9479, longitude=7.4446, min_speed_mbps="1000")`
Warum nützlich: Schafft Transparenz über den Breitbandausbau in der Schweiz und hilft Konsument:innen bei der Providerwahl.

## 🤖 KI-Interessierte & Entwickler:innen
MCP-Enthusiast:innen, Forscher:innen, Prompt Engineers, öffentliche Verwaltung

**Breitband-Katalog explorieren**
«Zeige mir alle verfügbaren Datensätze aus dem BAKOM Breitbandatlas, die auf opendata.swiss veröffentlicht sind.»
→ `bakom_breitbandatlas_datensaetze(thema="breitband")`
Warum nützlich: Bietet Data Scientists und Entwickler:innen einen schnellen Überblick über verfügbare OGD-Layer für eigene GIS-Analysen.

**Portfolio-Synergie: Schulstandorte und Glasfaserabdeckung kombinieren**
«Hole dir zuerst die Adressen und Koordinaten von drei Schulhäusern in der Stadt Zürich (via zurich-opendata-mcp). Überprüfe danach, ob diese Standorte bereits mit Glasfaser erschlossen sind.»
→ `zurich_suche_datensaetze(query="Schulhäuser")`
→ `bakom_multi_standort_konnektivitaet(locations=[{"name": "Schulhaus A", "latitude": 47.37, "longitude": 8.54}, {"name": "Schulhaus B", "latitude": 47.38, "longitude": 8.53}])`
Warum nützlich: Demonstriert die Leistungsfähigkeit von MCP-Servern durch die Verknüpfung kommunaler Adressdaten (https://github.com/malkreide/zurich-opendata-mcp) mit eidgenössischen Infrastrukturdaten.

## 🔧 Technische Referenz: Tool-Auswahl nach Anwendungsfall

| Ich möchte… | Tool(s) | Auth nötig? |
|-------------|---------|-------------|
| prüfen, ob an einem Standort Glasfaser verfügbar ist | `bakom_glasfaser_verfuegbarkeit` | Nein |
| die Festnetz-Breitbandversorgung (Mbit/s) abfragen | `bakom_broadband_coverage` | Nein |
| die Infrastruktur mehrerer Standorte vergleichen | `bakom_multi_standort_konnektivitaet` | Nein |
| die 5G/4G/3G Abdeckung an einem Ort prüfen | `bakom_mobilfunk_abdeckung` | Nein |
| Sendeanlagen/Antennen in meiner Nähe finden | `bakom_sendeanlagen_suche`, `bakom_frequenzdaten` | Nein |
| nach lizenzierten Radio- und TV-Sendern suchen | `bakom_rtv_suche` | Nein |
| Telekom- und Breitbandstatistiken explorieren | `bakom_telekomstatistik_uebersicht` | Nein |
| Medienberichte und Strukturdaten abfragen | `bakom_medienstruktur_info` | Nein |
| aktuelle Themen des BAKOM abrufen | `bakom_aktuell` | Nein |
| alle Layer des Breitbandatlas anzeigen | `bakom_breitbandatlas_datensaetze` | Nein |

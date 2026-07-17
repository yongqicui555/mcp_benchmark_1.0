# Use Cases & Beispiele — swiss-cultural-heritage-mcp

Hier finden Sie praxisnahe Anwendungsbeispiele für verschiedene Zielgruppen. 
**Authentifizierung:** Für keinen dieser Aufrufe wird ein API-Key benötigt (alle Daten sind Open Data).

---

### 🏫 Bildung & Schule
*Lehrpersonen, Schulbehörden, Fachreferent:innen*

**Unterrichtsmaterialien zur Schweizer Geschichte**
«Suche im Nationalmuseum nach Datensätzen zum Thema Mittelalter für den Geschichtsunterricht.»
→ `heritage_search_museum_datasets(query="Mittelalter")`
*Warum nützlich:* Lehrpersonen finden schnell authentische Quellen und Sammlungsobjekte (z. B. Waffen, Münzen, Siegel) zur Veranschaulichung im Unterricht.

**Recherche zu regionalen Künstlerinnen und Künstlern**
«Zeige mir Schweizer Kunstschaffende mit Geburtsort im Kanton Bern.»
→ `heritage_search_artists(region="Bern")`
*Warum nützlich:* Ermöglicht Fachreferent:innen für Bildnerisches Gestalten die gezielte Einbindung lokaler Kunstschaffender in den Lehrplan. Die Volltextsuche deckt auch Berufsbezeichnungen ab (z. B. `query="Bildhauer"`).

---

### 👨‍👩‍👧 Eltern & Schulgemeinde
*Elternräte, interessierte Erziehungsberechtigte*

**Literatur zur Schulwahl und Bildungspolitik**
«Finde Publikationen in der Nationalbibliothek zum Thema Volksschule Zürich ab dem Jahr 2020.»
→ `heritage_search_helveticat(query="Volksschule Zürich", from_date="2020")`
*Warum nützlich:* Eltern können sich gezielt in aktuelle Literatur und Berichte zu regionalen Bildungsthemen einlesen, um fundierte Entscheidungen zu treffen.

**Kulturelle Ausflugsziele in der Region**
«Gibt es in den Sammlungen des Nationalmuseums Objekte aus der Region Winterthur, die wir mit den Kindern besichtigen könnten?»
→ `heritage_search_museum_datasets(query="Winterthur")`
*Warum nützlich:* Hilft Familien bei der Planung von kulturell und historisch interessanten Ausflügen mit konkretem Bezug zum eigenen Wohnort.

---

### 🗳️ Bevölkerung & öffentliches Interesse
*Allgemeine Öffentlichkeit, politisch und gesellschaftlich Interessierte*

**Biografische Recherche zu bekannten Persönlichkeiten**
«Suche alle verfügbaren biografischen Informationen zur Künstlerin Sophie Taeuber-Arp.»
→ `heritage_search_artists(query="Sophie Taeuber-Arp")`
→ `heritage_get_artist(artist_id="<HAUPTNR aus dem Suchergebnis>")`
*Warum nützlich:* Interessierte Bürgerinnen und Bürger erhalten direkten, verlässlichen Zugang zu den kuratierten Lebensdaten bedeutender Schweizer Persönlichkeiten.

**Quellenübergreifende Kulturrecherche**
«Finde alles, was in den Schweizer Kulturerbe-Datenbanken zu Ferdinand Hodler vorhanden ist.»
→ `heritage_cross_search(query="Ferdinand Hodler")`
*Warum nützlich:* Bietet der Öffentlichkeit einen zentralen Einstiegspunkt, um Gemälde, Biografien und Publikationen zu einem Thema über alle drei Institutionen hinweg auf einmal zu finden.

---

### 🤖 KI-Interessierte & Entwickler:innen
*MCP-Enthusiast:innen, Forscher:innen, Prompt Engineers, öffentliche Verwaltung*

**Metadaten-Analyse für Datensätze**
«Liste alle verfügbaren OAI-PMH-Sets der Nationalbibliothek auf und durchsuche danach das Set 'swissbook' nach Publikationen zur KI-Ethik.»
→ `heritage_list_nb_collections()`
→ `heritage_search_helveticat(query="KI-Ethik", set_spec="swissbook")`
*Warum nützlich:* Entwickler:innen können die Struktur der OAI-PMH-Schnittstelle explorieren und gezielt Sammlungen für die automatisierte Metadaten-Extraktion nutzen.

**Kulturhistorische Verknüpfung (Multi-Server)**
«Suche im 'swiss-cultural-heritage-mcp' nach historischen Datensätzen zur Schweizer Eisenbahn und vergleiche die Entwicklung mit aktuellen Mobilitätsdaten aus dem 'swiss-road-mobility-mcp' (z. B. ASTRA-Verkehrszählungen).»
→ `heritage_search_museum_datasets(query="Eisenbahn")`
→ `astra_get_traffic_counters(canton="ZH")` *(aus [swiss-road-mobility-mcp](https://github.com/malkreide/swiss-road-mobility-mcp))*
*Warum nützlich:* Demonstriert die Stärke des MCP-Ökosystems durch die Verknüpfung von historischem Kulturgut mit gegenwärtigen Infrastrukturdaten für umfassende Analysen.

---

### 🔧 Technische Referenz: Tool-Auswahl nach Anwendungsfall

| Ich möchte… | Tool(s) | Auth nötig? |
|-------------|---------|-------------|
| **Künstler:innen nach Name/Ort finden** | `heritage_search_artists` | Nein |
| **Ein vollständiges Künstler:innen-Profil abrufen** | `heritage_get_artist` | Nein |
| **Datensätze des Nationalmuseums suchen** | `heritage_search_museum_datasets` | Nein |
| **Objekte in einer Museums-Sammlung ansehen** | `heritage_browse_collection` | Nein |
| **Literatur in der Nationalbibliothek finden** | `heritage_search_helveticat` | Nein |
| **Alle verfügbaren NB-Sammlungen auflisten** | `heritage_list_nb_collections` | Nein |
| **Alle drei Quellen gleichzeitig durchsuchen** | `heritage_cross_search` | Nein |

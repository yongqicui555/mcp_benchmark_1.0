# Use Cases & Examples — zh-education-mcp

Real-world queries by audience. Indicate per example whether an API key is required.

## 🏫 Bildung & Schule
Lehrpersonen, Schulbehörden, Fachreferent:innen

### Analyse des Sekundarstufen-Profils
«Wie hat sich der Anteil von Sek A und Sek B Schülerinnen und Schülern in Winterthur im letzten Jahr entwickelt?»

→ `zh_edu_sek1_profil(schulgemeinde="Winterthur")`
*Auth: nicht erforderlich*

**Warum nützlich:** Erlaubt Schulleitungen und Bildungsdirektionen eine datengestützte Ressourcenplanung für Lehrkräfte und Schulraum basierend auf dem Anforderungsniveau der Lernenden.

### Mittelschul-Auswertung nach Geschlecht und Schultyp
«Zeige mir die neusten Zahlen zu den Mittelschulen im Kanton Zürich. Wie verteilen sich die Lernenden am Gymnasium im Vergleich zur Fachmittelschule (FMS)?»

→ `zh_edu_mittelschulen(mittelschultyp="Gymnasium")`
→ `zh_edu_mittelschulen(mittelschultyp="FMS")`
*Auth: nicht erforderlich*

**Warum nützlich:** Unterstützt Berufsberatungen und Mittelschulbehörden beim Erkennen von kantonalen Trends in der nachobligatorischen Schulbildung und bei der strategischen Planung.

## 👨‍👩‍👧 Eltern & Schulgemeinde
Elternräte, interessierte Erziehungsberechtigte

### Lernenden-Trend im eigenen Schulkreis
«Wir wohnen in Zürich-Letzi. Wie haben sich die Schülerzahlen in unserem Schulkreis in den letzten 5 Jahren verändert?»

→ `zh_edu_schulkreis_trend(schulgemeinde="Zürich-Letzi", letzte_n_jahre=5)`
*Auth: nicht erforderlich*

**Warum nützlich:** Bietet Elternräten Transparenz über das Wachstum in ihrem Quartier und liefert stichhaltige, datenbasierte Argumente für Diskussionen um nötige Schulhausbauten.

### Gymnasiale Maturitätsquote der Wohngemeinde
«Wie hoch ist die Maturitätsquote in Uster im Vergleich zum gesamten Bezirk Uster?»

→ `zh_edu_maturitaetsquote(gemeinde="Uster")`
→ `zh_edu_maturitaetsquote(bezirk="Uster")`
*Auth: nicht erforderlich*

**Warum nützlich:** Hilft Eltern, die Bildungschancen und den Übertrittsdruck in ihrer Wohngemeinde besser einzuordnen und mit der regionalen Umgebung zu vergleichen.

## 🗳️ Bevölkerung & öffentliches Interesse
Allgemeine Öffentlichkeit, politisch und gesellschaftlich Interessierte

### Kantonsweite Übersicht der Lernenden
«Wie viele Lernende gibt es aktuell im Kanton Zürich über alle Schulstufen hinweg?»

→ `zh_edu_overview()`
*Auth: nicht erforderlich*

**Warum nützlich:** Liefert Medienschaffenden und politisch Interessierten sofort verifizierte, aggregierte Kennzahlen für journalistische Artikel oder parlamentarische Vorstösse zum Thema Bildung.

### Kulturelle Vielfalt an den Schulen
«Welche Staatsangehörigkeiten sind an den Schulen in Schlieren am häufigsten vertreten?»

→ `zh_edu_staatsangehoerigkeiten(schulgemeinde="Schlieren", top_n=5)`
*Auth: nicht erforderlich*

**Warum nützlich:** Fördert eine faktenbasierte Diskussion über Integration und die demografische Zusammensetzung in einzelnen Gemeinden.

## 🤖 KI-Interessierte & Entwickler:innen
MCP-Enthusiast:innen, Forscher:innen, Prompt Engineers, öffentliche Verwaltung

### Bildungs- und Infrastrukturanalyse (Multi-Server)
«Wie hoch ist die Maturitätsquote in der Stadt Zürich und welche offenen Parkplatzdaten stehen für städtische Infrastrukturprojekte zur Verfügung?»

→ `zh_edu_maturitaetsquote(gemeinde="Zürich")`
→ `zrh_parkhaeuser_live()` *(via [zurich-opendata-mcp](https://github.com/malkreide/zurich-opendata-mcp))*
*Auth: nicht erforderlich*

**Warum nützlich:** Kombiniert Bildungsdaten mit städtischer Infrastruktur, was für komplexe Data-Science-Projekte zur Stadtentwicklung oder Smart-City-Initiativen äusserst wertvoll ist.

### Historische Schulgebäude und heutige Schülerzahlen (Multi-Server)
«Gibt es in der Gemeinde Winterthur denkmalgeschützte Schulhäuser und wie viele Lernende verzeichnet die Gemeinde heute?»

→ `zh_edu_wohnort_trend(gebiet="Winterthur", letzte_n_jahre=1)`
→ `sch_search_monuments(query="Schulhaus Winterthur")` *(via [swiss-cultural-heritage-mcp](https://github.com/malkreide/swiss-cultural-heritage-mcp))*
*Auth: nicht erforderlich*

**Warum nützlich:** Demonstriert die Verknüpfung von aktuellem demografischem Druck mit historischer Bausubstanz für automatisierte Analysen in der kantonalen Denkmalpflege oder Bauplanung.

## 🔧 Technische Referenz: Tool-Auswahl nach Anwendungsfall

| Ich möchte… | Tool(s) | Auth nötig? |
|-------------|---------|-------------|
| **gültige Schulgemeinden-Namen für Abfragen finden** | `zh_edu_list_schulgemeinden` | Nein |
| **wissen, wie sich Schülerzahlen regional entwickeln** | `zh_edu_schulkreis_trend` | Nein |
| **die Aufteilung auf Sek A, B und C analysieren** | `zh_edu_sek1_profil` | Nein |
| **kantonale Totale aller Bildungsstufen abrufen** | `zh_edu_overview` | Nein |
| **die demografische Zusammensetzung (Nationalitäten) untersuchen** | `zh_edu_staatsangehoerigkeiten` | Nein |
| **Maturitätsquoten auf Gemeinde- oder Bezirksebene vergleichen** | `zh_edu_maturitaetsquote` | Nein |
| **Trends basierend auf dem Wohnort statt dem Schulort ermitteln** | `zh_edu_wohnort_trend` | Nein |
| **Statistiken zu Gymnasien und Fachmittelschulen abrufen** | `zh_edu_mittelschulen` | Nein |

# Use Cases & Beispiele — hn-tech-signal-mcp

Reale Suchanfragen nach Zielgruppe. Für alle Anwendungsfälle gilt: Es ist standardmässig kein API-Key erforderlich (ein `GITHUB_TOKEN` ist optional für höhere Rate-Limits bei GitHub-Abfragen).

## 🏫 Bildung & Schule
Lehrpersonen, Schulbehörden, Fachreferent:innen

### Aktuelle Entwicklungen in der Bildungstechnologie verfolgen
«Welche neuen Papers gibt es auf arXiv zum Thema Künstliche Intelligenz im Bildungsbereich oder adaptives Lernen?»

→ `arxiv_search`(query="artificial intelligence education adaptive learning", category="cs.AI", limit=5)

**Warum nützlich:** Fachreferent:innen können so frühzeitig erkennen, welche neuen KI-Technologien auf das Schulsystem zukommen könnten, noch bevor sie in Massenmedien besprochen werden.

### Open-Source-Tools für den Unterricht finden
«Gibt es auf GitHub aktuell trendende Repositories zum Thema EdTech oder Lernsoftware, die viele Sterne haben?»

→ `github_trending_ai`(topic="edtech", sort="stars", limit=5)

**Warum nützlich:** Informatiklehrpersonen können so neue, beliebte Open-Source-Lösungen für den direkten Einsatz im Unterricht entdecken und evaluieren.

## 👨‍👩‍👧 Eltern & Schulgemeinde
Elternräte, interessierte Erziehungsberechtigte

### Verständnis für KI-Diskussionen aufbauen
«Was diskutiert die Tech-Community auf HackerNews aktuell über Bildschirmzeit, Social Media und die Auswirkungen auf Kinder?»

→ `hn_search`(query="screen time social media kids", limit=5, days_back=90)

**Warum nützlich:** Elternräte erhalten so Einblick in die ungefilterten Diskussionen von Technologie-Entwicklern selbst, um eigene Argumente für Elterndiskussionen an der Schule zu schärfen.

### Einordnung neuer Tech-Trends
«Gibt es aktuelle Diskussionen auf Lobste.rs zum Thema Datenschutz bei Apps für Kinder oder im Schulbereich?»

→ `lobsters_hot`(limit=10, tag_filter="privacy")

**Warum nützlich:** Hilft interessierten Eltern zu verstehen, wie Sicherheitsexpert:innen und Entwickler:innen die Datenschutzrisiken aktueller Technologien einschätzen.

## 🗳️ Bevölkerung & öffentliches Interesse
Allgemeine Öffentlichkeit, politisch und gesellschaftlich Interessierte

### Tägliches Tech-Briefing zu gesellschaftlichen Themen
«Erstelle mir ein kompaktes Tech-Signal-Digest über die heutigen Diskussionen und Entwicklungen im Bereich KI-Regulierung und Open Source.»

→ `tech_signal_digest`(focus="regulation open source", hn_limit=3, arxiv_limit=3, lobsters_limit=3, github_limit=3)

**Warum nützlich:** Bietet politisch interessierten Bürger:innen einen schnellen, fundierten Überblick über die globalen Tech-Trends, die zukünftige politische Debatten in der Schweiz prägen werden.

### Technologische Debatten historisch einordnen
«Wie hat sich die HackerNews-Diskussion zum Thema Vorratsdatenspeicherung oder Überwachung in den letzten Monaten entwickelt?»

→ `hn_search`(query="surveillance data retention", limit=10, days_back=180)

**Warum nützlich:** Zivilgesellschaftliche Akteure können so Argumente und technische Perspektiven der Entwickler-Community zu gesellschaftspolitisch relevanten Themen recherchieren.

## 🤖 KI-Interessierte & Entwickler:innen
MCP-Enthusiast:innen, Forscher:innen, Prompt Engineers, öffentliche Verwaltung

### Neueste KI-Agenten-Architekturen finden
«Welche aktuellen Paper in cs.LG und cs.AI beschäftigen sich mit Agentic Workflows, und welche passenden Frameworks trenden gerade auf GitHub?»

→ `arxiv_search`(query="agentic workflows LLM", category="cs.AI", limit=5)
→ `github_trending_ai`(topic="ai-agents", sort="updated", limit=5)

**Warum nützlich:** Entwickler:innen können so die Lücke zwischen neuester akademischer Forschung und direkt anwendbarem Open-Source-Code schliessen.

### Multi-Server: Globaler Diskurs vs. Schweizer Medien
«Was sind die aktuellsten Tech-Diskussionen zum Thema Datenschutz und KI auf HackerNews, und wie wird das parallel in den Schweizer Medien thematisiert?»

→ `hn_search`(query="AI data privacy", limit=5, days_back=7)
→ `srf_news_search`(query="KI Datenschutz") *(über [news-monitor-mcp](https://github.com/malkreide/news-monitor-mcp))*

**Warum nützlich:** Demonstriert die Leistungsfähigkeit, den globalen englischsprachigen Tech-Diskurs direkt mit der lokalen Schweizer Medienresonanz zu verknüpfen, um eine umfassende Situationsanalyse zu erstellen.

## 🔧 Technische Referenz: Tool-Auswahl nach Anwendungsfall

| Ich möchte… | Tool(s) | Auth nötig? |
| :--- | :--- | :--- |
| ...die aktuellsten KI/ML-Paper aus spezifischen Forschungskategorien (z.B. cs.AI) sehen | `arxiv_latest` | Nein |
| ...die wissenschaftliche arXiv-Datenbank nach bestimmten Stichworten durchsuchen | `arxiv_search` | Nein |
| ...die aktuellen Top-Stories oder neuesten Beiträge auf HackerNews lesen | `hn_top_stories` | Nein |
| ...die gesamte HackerNews-Historie nach spezifischen Themen durchsuchen | `hn_search` | Nein |
| ...die am heissesten diskutierten, kuratierten Stories auf Lobste.rs sehen | `lobsters_hot` | Nein |
| ...auf GitHub nach trendenden Repositories zu einem bestimmten Topic suchen | `github_trending_ai` | Nein (Optional `GITHUB_TOKEN`) |
| ...ein kompaktes Briefing über alle vier Quellen (arXiv, HN, Lobste.rs, GitHub) erhalten | `tech_signal_digest` | Nein |

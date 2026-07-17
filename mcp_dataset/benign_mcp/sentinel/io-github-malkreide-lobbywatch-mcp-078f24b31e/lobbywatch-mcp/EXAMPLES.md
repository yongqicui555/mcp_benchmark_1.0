# Use Cases & Examples — lobbywatch-mcp

Real-world queries by audience. Indicate per example whether an API key is required.

> **Hinweis zur Authentifizierung:** Der `lobbywatch-mcp` Server benötigt **keinen API-Key** und keine Authentifizierung für den Zugriff auf die öffentlichen Daten.

### 🏫 Bildung & Schule
Lehrpersonen, Schulbehörden, Fachreferent:innen

**Interessenbindungen im Bildungswesen**
«Welche Mitglieder der nationalrätlichen Bildungskommission (WBK-N) haben deklarierte Interessenbindungen zu Bildungsverlagen oder privaten Bildungsträgern?»
→ `search_parlamentarier_nach_branche(branche_query="Bildung", kommission="WBK-N")`
Warum nützlich: Erlaubt Lehrpersonen und Schulbehörden, mögliche Befangenheiten bei bildungspolitischen Entscheidungen zu erkennen.

**Transparenz bei Bildungspolitiker:innen**
«Wie transparent sind die Mitglieder der Bildungskommission (WBK-N) bezüglich ihrer Entschädigungen bei Nebeneinkünften?»
→ `get_transparenzquote(kommission="WBK-N")`
Warum nützlich: Zeigt auf, wie offen die zuständigen Politiker:innen ihre finanziellen Interessen im Bildungsbereich deklarieren.

### 👨‍👩‍👧 Eltern & Schulgemeinde
Elternräte, interessierte Erziehungsberechtigte

**Verbindungen zu Krankenkassen**
«Gibt es Parlamentarier aus meinem Kanton, die bezahlte Mandate bei Krankenkassen haben, und wie beeinflusst das familienpolitische Vorlagen?»
→ `search_parlamentarier_nach_branche(branche_query="Krankenkasse")`
Warum nützlich: Hilft Eltern, die Hintergründe von Entscheidungen zu Gesundheits- und Prämienfragen zu verstehen.

**Einfluss von Familienorganisationen**
«Welche Nationalräte sind mit Lobbygruppen aus dem Bereich Familie oder Kinderbetreuung verbunden?»
→ `search_parlamentarier_nach_branche(branche_query="Familie")`
Warum nützlich: Macht sichtbar, welche Politiker:innen direkte Verbindungen zu familienpolitischen Interessenvertretungen pflegen.

### 🗳️ Bevölkerung & öffentliches Interesse
Allgemeine Öffentlichkeit, politisch und gesellschaftlich Interessierte

**Ranking der Interessenbindungen**
«Welche Nationalrätinnen oder Ständeräte haben am meisten bezahlte Nebenmandate (hauptberufliche Interessenbindungen)?»
→ `get_ranking(kriterium="anzahl_hauptberuflich", limit=10)`
Warum nützlich: Bietet der Öffentlichkeit einen klaren Überblick über die politische Unabhängigkeit und mögliche zeitliche Überbelastung von Gewählten.

**Überprüfung einer Lobbygruppe**
«Wer sitzt für den Verband 'economiesuisse' im Parlament und welche Organisationen sind damit verknüpft?»
→ `get_lobbygruppe(name_or_id="economiesuisse")`
Warum nützlich: Schafft Transparenz über den direkten Einfluss grosser Wirtschaftsverbände auf die Gesetzgebung.

### 🤖 KI-Interessierte & Entwickler:innen
MCP-Enthusiast:innen, Forscher:innen, Prompt Engineers, öffentliche Verwaltung

**Analyse politischer Netzwerke (mit parlament-mcp)**
«Finde heraus, wer für 'economiesuisse' lobbyiert, und suche dann mit parlament-mcp nach Vorstössen dieser Personen zum Thema Unternehmenssteuern.»
→ `get_lobbygruppe(name_or_id="economiesuisse")` (lobbywatch-mcp)
→ `search_affairs(query="Unternehmenssteuer")` (parlament-mcp: https://github.com/malkreide/parlament-mcp)
Warum nützlich: Demonstriert die mächtige Kombination von Lobby-Netzwerken mit tatsächlichem Abstimmungs- und Vorstossverhalten.

**Branchen-Profiling und parlamentarisches Wirken**
«Welche Politiker:innen sind im Bereich 'Pharma' aktiv und welche Vorstösse haben sie in der letzten Session eingereicht?»
→ `search_parlamentarier_nach_branche(branche_query="Pharma")` (lobbywatch-mcp)
→ `get_parlamentarier(name_or_id="[Name]")` (lobbywatch-mcp)
Warum nützlich: Verbindet finanzielle Interessen direkt mit parlamentarischem Handeln durch serverübergreifende oder kombinierte Abfragen.

### 🔧 Technische Referenz: Tool-Auswahl nach Anwendungsfall

| Ich möchte… | Tool(s) | Auth nötig? |
| :--- | :--- | :--- |
| **das vollständige Profil eines Politikers abrufen** | `get_parlamentarier` | Nein |
| **alle Nebenmandate einer Person auflisten** | `list_interessenbindungen` | Nein |
| **nach Branchen oder Themen suchen** | `search_parlamentarier_nach_branche` | Nein |
| **das Netzwerk einer Lobbygruppe analysieren** | `get_lobbygruppe` | Nein |
| **Ranglisten nach Anzahl Mandaten erstellen** | `get_ranking` | Nein |
| **die Transparenz einer Kommission auswerten** | `get_transparenzquote` | Nein |
| **den lokalen Datenbestand aktualisieren** | `refresh_dump` / `dump_status` | Nein |

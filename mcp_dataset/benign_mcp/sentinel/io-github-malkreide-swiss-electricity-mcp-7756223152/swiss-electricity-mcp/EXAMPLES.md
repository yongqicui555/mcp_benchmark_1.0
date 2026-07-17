# EXAMPLES.md — `swiss-electricity-mcp` in der Praxis

> Vier Zielgruppen, vier Sprachen, dieselben zwölf Tools.

Stromdaten sind technisch — die Fragen dahinter sind es nicht. Eine Lehrperson fragt anders als ein Stadtrat, eine Mutter anders als eine ML-Entwicklerin. Dieser Leitfaden zeigt für jede Gruppe **drei realistische Anwendungsfälle** mit konkretem Prompt, Tool-Aufruf und erwartetem Mehrwert.

**Eselsbrücke zum Tool-Set:** Drei Domänen wie ein Stromzähler — **Produktion** (was kommt rein, `dashboard_*`), **Preis** (was zahle ich, `tariff_*`), **Verbrauch** (was geht raus, `consumption_*`).

---

## 🎓 Zielgruppe 1 — Bildung (Lehrpersonen, Schulleitungen, Pädagogik)

Schulgebäude sind als Verbrauchskategorie **C3** klassifiziert (≈ 150 000 kWh/Jahr) — die ElCom hat dafür einen eigenen Referenzwert. Das ist die kleinste Schraube, die Hausdienst, Schulleitung und Pädagogik gemeinsam drehen können.

### 1.1 Liegenschafts-Briefing: «Wo stehen unsere Stromkosten?»

**Wer fragt:** Schulleitung, Bereich Infrastruktur
**Prompt an Claude:**
> «Wie haben sich die ewz-Stromtarife für unser Schulhaus (Kategorie C3) seit 2019 entwickelt? Vergleich zum Schweizer Median bitte.»

**Tool-Sequenz:**
```
tariff_get_by_municipality(bfs_number=261, category="C3", year_from=2019, year_to=2024)
tariff_get_median_swiss(category="C3", year_from=2019, year_to=2024)
```

**Was zurückkommt:** Eine Jahresreihe mit dem ewz-Gesamttarif (aufgeschlüsselt nach Energie + Netznutzung + KEV + Abgaben) und der CH-Median als Referenzlinie. Damit lässt sich in einer Sitzung beantworten: **«Sind wir teurer oder günstiger als der Durchschnitt, und seit wann?»**

### 1.2 Energiewende im Unterricht (Sek I / Sek II)

**Wer fragt:** Geografielehrperson, Klasse 8. Schuljahr
**Prompt an Claude:**
> «Zeig mir den aktuellen Strom-Produktionsmix der Schweiz. Wie viel Prozent stammen 2024 aus Wasserkraft, Kernkraft, Sonne und Wind?»

**Tool-Sequenz:**
```
dashboard_get_production_mix(year=2024)
```

**Didaktischer Nutzen:** Statt einer veralteten Schulbuch-Grafik bekommt die Klasse die echten BFE-Zahlen — mit `provenance: live_api` und `retrieved_at`-Zeitstempel. **Quellenkritik wird konkret:** «Diese Zahl ist heute um 14:32 Uhr beim Bundesamt für Energie abgeholt worden.»

### 1.3 Nachhaltigkeitsprojekt: Schweizer Wasserkraft-Speicher als «Akku»

**Wer fragt:** Klasse erarbeitet Klima-Projekt
**Prompt an Claude:**
> «Wie voll sind die Schweizer Speicherseen aktuell? Welche Region hat am wenigsten gespeichert?»

**Tool-Sequenz:**
```
dashboard_get_storage_lakes()
```

**Eselsbrücke für die Klasse:** Speicherseen = der **Stromakku der Schweiz**. Vier Akku-Zellen (Wallis, Tessin, Graubünden, Zentral/Ost) — wenn eine schwächelt, merkt das ganze Land im Winter. So wird Versorgungssicherheit greifbar.

---

## 👨‍👩‍👧 Zielgruppe 2 — Eltern und Erziehungsberechtigte

Eltern fragen nicht nach SPARQL oder CKAN. Sie fragen nach **ihrer Stromrechnung**, **dem Schulweg ihres Kindes** und nach **Verständlichkeit**, wenn die Schule über Nachhaltigkeit kommuniziert.

### 2.1 «Was kostet Strom bei uns — und ist das viel?»

**Wer fragt:** Eltern aus Affoltern, die einen Strompreisvergleich für die Haushaltsplanung wollen
**Prompt an Claude:**
> «Wie hoch ist der Stromtarif für einen typischen Haushalt mit 4500 kWh/Jahr in der Stadt Zürich, und wie liegt das im Schweizer Vergleich?»

**Tool-Sequenz:**
```
tariff_get_by_municipality(bfs_number=261, category="H4", year=2024)
tariff_get_median_swiss(category="H4", year=2024)
```

**Eselsbrücke H4:** Die Haushaltskategorien gehen von **H1 (1-Personen-Wohnung)** bis **H8 (grosses Einfamilienhaus mit Wärmepumpe)**. **H4 ≈ 4-Zimmer-Wohnung mit Elektroherd**, der typische Mittelwert.

### 2.2 «Was bedeutet ‹erneuerbar› im Schweizer Strom konkret?»

**Wer fragt:** Mutter, deren Kind in der Schule über Klimaschutz lernt
**Prompt an Claude:**
> «Mein Kind soll für die Schule den Schweizer Strommix erklären. Bitte einfach und mit aktuellen Zahlen.»

**Tool-Sequenz:**
```
dashboard_get_production_mix(year=2024)
```

**Pädagogischer Hebel:** Claude liefert nicht nur die Zahl, sondern auch die Quelle (BFE) und das Datum — Eltern können dem Kind zeigen, **wie verlässliche Information entsteht**. Das ist Medienkompetenz im Alltag.

### 2.3 Schule vs. Wohnort: Wo ist der Strom günstiger?

**Wer fragt:** Familie pendelt zwischen Winterthur und Zürich (Patchwork)
**Prompt an Claude:**
> «Vergleich bitte die Stromtarife von Winterthur und Zürich für einen Standard-Haushalt 2024.»

**Tool-Sequenz:**
```
tariff_compare_municipalities(bfs_numbers=[261, 230], category="H4", year=2024)
```

**Was sichtbar wird:** Zwei Städte, oft sehr unterschiedliche Tarife — weil zwei Netzbetreiber (ewz vs. Stadtwerk Winterthur) mit eigenen Kosten kalkulieren. Greifbar wird so: **Strompreis ist nicht national, sondern lokal**.

---

## 🏛️ Zielgruppe 3 — Bevölkerung, Stadtverwaltung, KI-Fachgruppe

Hier sitzen Geschäftsleitung, Stadtrats-Beilagen, Mediendossiers und das Schulamt selbst. Anforderungen: **belastbar, zitierfähig, vergleichbar.**

### 3.1 GL-Briefing: Tarif-Entwicklung Zürich vs. Peer-Städte

**Wer fragt:** Direktion Schulamt, vor einer GL-Sitzung
**Prompt an Claude:**
> «Erstell mir eine GL-Folie: Stromtarif für Schulgebäude (C3) in Zürich, Winterthur, Bern, Basel und Genf seit 2020. Mit Quellenangabe.»

**Tool-Sequenz:**
```
tariff_compare_municipalities(
  bfs_numbers=[261, 230, 351, 2701, 6621],
  category="C3",
  year_from=2020,
  year_to=2024
)
```

**Mehrwert:** Eine einzige Abfrage liefert die Tabelle plus die ElCom-Attribution direkt aus dem Envelope — **keine manuelle Quellenrecherche, keine Excel-Bastelei.** Folie steht in fünf Minuten.

### 3.2 Stadtrats-Anfrage: Wo positioniert sich ewz?

**Wer fragt:** Kommunikation Schulamt, vor einer parlamentarischen Anfrage
**Prompt an Claude:**
> «Wie liegt der ewz-Tarif für Schulen im Vergleich zum Kanton Zürich und zur ganzen Schweiz?»

**Tool-Sequenz:**
```
tariff_get_by_municipality(bfs_number=261, category="C3", year=2024)
tariff_get_median_canton(canton="Zürich", category="C3", year=2024)
tariff_get_median_swiss(category="C3", year=2024)
```

**Drei Zahlen, drei Provenance-Stempel** — politische Debatte auf belastbarer Faktenbasis statt auf Schätzungen.

### 3.3 Versorgungssicherheits-Monitoring fürs Dashboard

**Wer fragt:** KI-Fachgruppe Stadtverwaltung Zürich, Stromversorgungs-Monitor
**Prompt an Claude:**
> «Status aller Energiedatenquellen prüfen und den aktuellen Speicherseen-Stand abrufen.»

**Tool-Sequenz:**
```
electricity_check_status()
dashboard_get_storage_lakes()
```

**Operativer Nutzen:** Vor jedem Monitoring-Lauf erst Liveness-Check (sind alle vier Upstreams gesund?), dann die fachliche Abfrage. So unterscheidet ein produktives Dashboard **«keine Daten verfügbar»** sauber von **«Daten sind verfügbar und zeigen einen tiefen Stand»**.

---

## 🛠️ Zielgruppe 4 — KI-Entwickler:innen und Portfolio-Maintainer

Technisches Publikum: andere MCP-Maintainer im Portfolio, Mitglieder der KI-Fachgruppe mit Code-Background, externe Partner, die ähnliche Server für andere Kantone bauen wollen.

### 4.1 Multi-Server-Komposition (Portfolio-Synergie)

**Wer fragt:** Entwicklerin baut eine Energie-Klima-Analyse über mehrere MCP-Server
**Prompt an Claude:**
> «Korreliere den Schweizer Stromverbrauch der letzten 7 Tage mit der Temperatur in Zürich.»

**Tool-Sequenz (zwei Server, ein Workflow):**
```
swiss-electricity-mcp:  dashboard_get_consumption_forecast()
meteoswiss-mcp:         get_temperature_history(station="ZRH", days=7)
```

**Pattern:** Jeder Server liefert ein **Pydantic-Envelope** mit eigenständiger Attribution — bei der Verkettung bleiben beide Quellen sauber zitierfähig. Das ist der Grund, warum **Domänen-Trennung** (Strom vs. Wetter vs. Geo) klüger ist als ein Monster-Server.

### 4.2 Eigene LLM-Pipeline via Streamable HTTP

**Wer fragt:** Entwickler will den Server in eine n8n/LangChain-Pipeline einbinden
**Setup:**
```bash
SWISS_ELECTRICITY_TRANSPORT=streamable-http \
SWISS_ELECTRICITY_HOST=0.0.0.0 \
SWISS_ELECTRICITY_PORT=8000 \
swiss-electricity-mcp
```

**Endpoint:** `http://<host>:8000/sse`

**Was beachten:** Keine Authentication erforderlich (no-auth-first Design). Wenn der Server cloud-deployed wird (Render.com, Railway, Fly.io), **Rate-Limiting auf Reverse-Proxy-Ebene** einziehen — der LINDAS-Upstream hat selbst kein hartes Limit, aber ein versehentlich öffentlich gemachter Server kann Quellen-Belastung verursachen.

### 4.3 Provenance-Disziplin nachnutzen

**Wer fragt:** Maintainer eines neuen Portfolio-Servers für einen anderen Kanton
**Lernen aus dem Code:**
```python
# api_client.py — der zentrale Envelope
ResponseEnvelope(
    source="Daten: ElCom (LINDAS SPARQL Endpoint)",
    provenance=Provenance.SPARQL,
    retrieved_at=datetime.now(UTC),
    data=...
)
```

**Drei Felder, ein Versprechen:** Wer das Envelope-Pattern erbt, kann **keine Daten ohne Quelle ausliefern**. Für jeden neuen Server im Portfolio ist das die billigste Versicherung gegen Halluzinationen und Audit-Probleme.

**Retry-Policy zum Nachbauen:**
- 5xx + 429 → Retry mit exponentiellem Backoff (2 s / 4 s / 8 s, max. 3 Versuche)
- 4xx (ausser 429) → sofort raise (permanenter Client-Fehler)
- Netzwerkfehler → `UpstreamUnreachableError`

Das ist nicht über-engineered — es ist das **Minimum**, das produktive MCP-Server brauchen, sobald sie nicht mehr nur lokal laufen.

---

## 🧭 Schnell-Navigation: Welches Tool für welche Frage?

| Frage | Tool | Domäne |
|---|---|---|
| «Was zahlen wir im Schulhaus?» | `tariff_get_by_municipality` | Preis |
| «Wie liegen wir im Vergleich?» | `tariff_compare_municipalities` / `tariff_get_median_*` | Preis |
| «Was kommt aus welcher Quelle?» | `dashboard_get_production_mix` | Produktion |
| «Reicht der Strom im Winter?» | `dashboard_get_storage_lakes` | Produktion |
| «Wie entwickelt sich der Endverbraucher-Preis?» | `dashboard_get_consumer_price_index` | Preis |
| «Wie viel verbraucht die Schweiz heute?» | `dashboard_get_consumption_forecast` | Verbrauch |
| «Gibt es Roh-Zeitreihen für meinen Use Case?» | `consumption_search_*` | Verbrauch |
| «Sind die Datenquellen gerade gesund?» | `electricity_check_status` | Status |

---

## ⚠️ Was dieser Server **nicht** kann

Erwartungs-Management ist wichtiger als Funktions-Werbung:

- **Keine Echtzeit-Smart-Meter-Daten einzelner Gebäude** — ElCom-Tarife sind aggregiert pro Gemeinde und Kategorie, nicht pro Stromzähler.
- **Keine kantonalen Förderprogramm-Daten** — dafür wäre eher `fedlex-mcp` (Rechtsgrundlagen) oder ein zukünftiger `swiss-energy-funding-mcp` zuständig.
- **Keine PV-Anlage-Auslegung oder Eigenverbrauchsoptimierung** — der Server liefert Marktdaten, keine Engineering-Berechnungen.
- **Keine Garantie auf «aktuellstes Jahr»** — ElCom publiziert Tarife mit 6–12 Monaten Lag. In Q2 2026 ist 2026 typischerweise noch nicht final verfügbar.

**Eselsbrücke fürs Erwartungs-Management:** Der Server ist ein **Beobachter**, kein Berater — er liefert Daten in höchster Qualität, die Entscheidung trifft der Mensch.

---

*Teil des [Swiss Public Data MCP Portfolio](https://github.com/malkreide). Bei Fragen oder neuen Use Cases: Issue auf GitHub oder direkt an die KI-Fachgruppe Stadtverwaltung Zürich.*

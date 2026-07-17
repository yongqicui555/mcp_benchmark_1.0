# Design: Safety & Limits Section + Demo SVG Assets

**Date:** 2026-04-13
**Repos:** `swiss-cultural-heritage-mcp` + `zurich-opendata-mcp` (both simultaneously)
**Status:** Approved

---

## Scope

Two additions to both MCP server repos in the Swiss Public Data MCP Portfolio:

1. **Safety & Limits section** — a short, standalone README section aimed at institutional reviewers and directory sites
2. **Demo SVG asset** — a Chat-Mock-style SVG showing `User → Tool Call → Claude response`, embedded directly in the README

---

## Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Target repos | Both simultaneously | Portfolio consistency |
| Asset format | SVG | Git-versionable, renders natively on GitHub and LinkedIn previews |
| SVG visual style | Terminal / Chat-Mock | Readable at README scale; developers immediately recognise MCP tool-call pattern |
| Approach | Compact Safety + one SVG per repo | Minimal diff, maximum impact; no extra files/folders beyond `docs/assets/` |

---

## 1. Safety & Limits Section

### Placement
Directly before `## Known Limitations` in both `README.md` and `README.de.md` of each repo.

### Content — swiss-cultural-heritage-mcp (EN)

```markdown
## Safety & Limits

- **Read-only:** All tools perform HTTP GET requests only — no data is written, modified, or deleted.
- **No personal data:** The APIs return institutional records (artworks, publications, artists). No personally identifiable information (PII) is processed or stored by this server.
- **Rate limits:** SIK-ISEA and OAI-PMH endpoints are not rate-limit-documented; use `limit` parameters conservatively. The server enforces a 30s timeout per request.
- **Data freshness:** Records reflect the upstream source at query time. No caching is performed by this server.
- **Terms of service:** Data is subject to the ToS of each source — [SIK-ISEA](https://www.sik-isea.ch), [opendata.swiss](https://opendata.swiss/terms-of-use), [Nationalbibliothek OAI-PMH](https://www.nb.admin.ch/). All data is published under open licenses (CC0 / CC BY).
- **No guarantees:** This server is a community project, not affiliated with SIK-ISEA, SNM, or NB. Availability depends on upstream APIs.
```

### Content — swiss-cultural-heritage-mcp (DE)

```markdown
## Sicherheit & Grenzen

- **Nur-Lesen:** Alle Tools verwenden ausschliesslich HTTP-GET-Anfragen — es werden keine Daten geschrieben, verändert oder gelöscht.
- **Keine Personendaten:** Die APIs liefern institutionelle Datensätze (Kunstwerke, Publikationen, Künstlerbiografien). Keine personenbezogenen Daten werden durch diesen Server verarbeitet oder gespeichert.
- **Rate Limits:** SIK-ISEA- und OAI-PMH-Endpunkte sind nicht explizit rate-limitiert; `limit`-Parameter konservativ einsetzen. Der Server erzwingt ein 30-Sekunden-Timeout pro Anfrage.
- **Datenaktualität:** Datensätze spiegeln den Upstream-Stand zum Abfragezeitpunkt wider. Dieser Server nimmt kein Caching vor.
- **Nutzungsbedingungen:** Die Daten unterliegen den Nutzungsbedingungen der jeweiligen Quelle — [SIK-ISEA](https://www.sik-isea.ch), [opendata.swiss](https://opendata.swiss/de/terms-of-use), [Nationalbibliothek OAI-PMH](https://www.nb.admin.ch/). Alle Daten sind unter offenen Lizenzen veröffentlicht (CC0 / CC BY).
- **Keine Gewähr:** Dieses Projekt ist eine Community-Initiative ohne Verbindung zu SIK-ISEA, SNM oder NB. Verfügbarkeit hängt von den vorgelagerten APIs ab.
```

### Content — zurich-opendata-mcp (EN)

Same structure, adapted sources:
- ToS links: CKAN (data.stadt-zuerich.ch), ParkenDD, gemeinderat-zuerich.ch
- License note: CC0 (Stadt Zürich "Open by Default" since 2021)
- Rate limits: ParkenDD free tier; CKAN Solr search conservative use

### Content — zurich-opendata-mcp (DE)

German translation of the above, same bullet structure.

---

## 2. Demo SVG Assets

### File paths
- `swiss-cultural-heritage-mcp/docs/assets/demo.svg`
- `zurich-opendata-mcp/docs/assets/demo.svg`

### README embedding
Added directly after the "Anchor demo query" block in each README, before the first `---` separator:

```markdown
### Demo

![Demo: Claude using heritage_cross_search](docs/assets/demo.svg)
```

### Visual specification

**Dimensions:** 640 × 240px  
**Background:** `#0d1117` (GitHub Dark)  
**Font:** `monospace`, 13px  
**Three panels stacked vertically, each with a 3px left border:**

| Panel | Left border | Label | Content |
|-------|------------|-------|---------|
| User message | `#58a6ff` (blue) | `💬 You` | Natural language query |
| Tool call | `#e3b341` (amber) | `🔧 Tool Call` | Function name + key args in monospace |
| Claude response | `#3fb950` (green) | `🤖 Claude` | 2-line answer excerpt |

### Query content

**swiss-cultural-heritage-mcp:**
- User: *"Who is Ferdinand Hodler and what works does the Nationalmuseum have from him?"*
- Tool: `heritage_cross_search(query="Ferdinand Hodler", sources=["sik_isea","snm","nb"])`
- Response: *"Ferdinand Hodler (1853–1918) was one of Switzerland's most important painters. The Nationalmuseum holds 3 objects... SIK-ISEA lists 47 biographical references."*

**zurich-opendata-mcp:**
- User: *"How many free parking spots are in Zurich right now, and what's the air quality like?"*
- Tool: `zurich_parking_live()` + `zurich_air_quality(parameter="PM10", limit=3)`
- Response: *"Currently 1,243 free spots across 36 garages (67% occupied). PM10 at 12 µg/m³ — well below WHO threshold. Good conditions today."*

---

## Implementation Steps

1. Create `docs/assets/` directory in both repos
2. Write `demo.svg` for `swiss-cultural-heritage-mcp`
3. Write `demo.svg` for `zurich-opendata-mcp`
4. Insert Safety & Limits section in `swiss-cultural-heritage-mcp/README.md`
5. Insert Safety & Limits section in `swiss-cultural-heritage-mcp/README.de.md`
6. Insert Safety & Limits section in `zurich-opendata-mcp/README.md`
7. Insert Safety & Limits section in `zurich-opendata-mcp/README.de.md`
8. Add demo embedding after anchor-query block in all 4 README files
9. Verify SVGs render correctly (width, text wrapping)

---

## Out of Scope

- Animated SVGs (CSS animation not reliable across all GitHub markdown renderers)
- Shared portfolio-level safety doc (adds indirection, worse UX)
- Actual live screenshots (SVG is maintenance-free and version-controlled)

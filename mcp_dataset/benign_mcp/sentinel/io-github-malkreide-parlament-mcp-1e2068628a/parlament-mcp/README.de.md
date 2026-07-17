[🇬🇧 English Version](README.md)

# 🏛️ parlament-mcp

[![CI](https://github.com/malkreide/parlament-mcp/actions/workflows/ci.yml/badge.svg)](https://github.com/malkreide/parlament-mcp/actions/workflows/ci.yml)
[![PyPI version](https://badge.fury.io/py/parlament-mcp.svg)](https://badge.fury.io/py/parlament-mcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Swiss Public Data MCP Portfolio](https://img.shields.io/badge/Portfolio-Swiss%20Public%20Data%20MCP-blue)](https://github.com/malkreide)

> **Teil des [Swiss Public Data MCP Portfolio](https://github.com/malkreide)** –
> KI-Modelle mit Schweizer Öffentlichkeitsdaten verbinden.

Ein MCP-Server, der KI-Modelle mit dem **Schweizer Bundesrat und Bundesversammlung** verbindet –
über die [Curia Vista OData-API](https://ws.parlament.ch/odata.svc/) (`ws.parlament.ch`).
Zugriff auf Vorstösse, Abstimmungen, Ratsmitglieder, Sessionen und Debatten-Transkripte –
**ohne API-Schlüssel** (Phase 1 – No-Auth-First).

---

## 🎯 Anker-Demo-Abfrage

> *«Welche Vorstösse zu KI in der Schule sind hängig?»*
> → `parlament_search_business(keyword="KI", keyword2="Schule", status="Eingereicht")`
>
> [→ Weitere Anwendungsbeispiele nach Zielgruppe →](EXAMPLES.md)

Ideal für die **KI-Fachgruppe Stadtverwaltung Zürich**: Offene Vorstösse zu KI in der Bildung,
Digitalisierungsinitiativen oder beliebigen Politikthemen – sofort abrufbar.

<p align="center">
  <img src="assets/demo.svg" alt="Demo: Claude fragt hängige KI-Vorstösse via MCP Tool Call ab" width="720">
</p>

---

## 🔧 Tools

| Tool | Beschreibung |
|---|---|
| `parlament_search_business` | Vorstösse nach Stichwort, Typ, Status, Rat, Datum suchen |
| `parlament_get_business` | Vollständige Details eines Vorstosses (Texte, BR-Antwort) |
| `parlament_search_members` | Ratsmitglieder nach Kanton (z.B. ZH), Partei, Rat finden |
| `parlament_get_votes` | Parlamentarische Abstimmungen mit Ja/Nein-Bedeutung |
| `parlament_get_sessions` | Aktuelle Sessionen mit IDs für Folgeabfragen |
| `parlament_get_transcripts` | Debatten-Auszüge nach Stichwort oder Redner (Amtliches Bulletin) |

---

## 🏗️ Architektur

```
┌──────────────────────────────────┐
│     MCP-Host (Claude Desktop /   │
│     Claude API / IDE)            │
└─────────────┬────────────────────┘
              │ MCP-Protokoll (JSON-RPC 2.0)
              │ Transport: stdio (lokal) / SSE (Cloud)
┌─────────────▼────────────────────┐
│         parlament-mcp            │
│   FastMCP · Python · Pydantic v2 │
└─────────────┬────────────────────┘
              │ HTTPS / OData v3
┌─────────────▼────────────────────┐
│  ws.parlament.ch / odata.svc     │
│  Curia Vista – Kein Auth nötig   │
│                                  │
│  Business · Vote · MemberCouncil │
│  Session · Transcript · ParlGroup│
└──────────────────────────────────┘
```

---

## 🚀 Installation

### Claude Desktop (stdio)

Ergänze `~/Library/Application Support/Claude/claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "parlament": {
      "command": "uvx",
      "args": ["parlament-mcp"]
    }
  }
}
```

Claude Desktop neu starten – fertig.

### Lokale Entwicklung

```bash
git clone https://github.com/malkreide/parlament-mcp
cd parlament-mcp
pip install -e .
python -m parlament_mcp.server
```

### Cloud / Railway (SSE)

```bash
MCP_TRANSPORT=sse MCP_HOST=0.0.0.0 PORT=8080 python -m parlament_mcp.server
# SSE-Endpunkt: http://dein-host:8080/sse
```

### Netzwerk-Bindung

Standardmässig bindet der Server an `127.0.0.1` (nur localhost). Setze
`MCP_HOST=0.0.0.0` **nur** im Container-/Cloud-Kontext (Docker, Railway,
Render, Kubernetes). Niemals lokal auf `0.0.0.0` binden – das exponiert den
Server im lokalen Netzwerk (NeighborJack-Risiko); ausserhalb eines erkannten
Containers gibt der Server eine Warnung aus.

Der Transport wird über `MCP_TRANSPORT` gewählt (`stdio` als Default, oder
`sse` / `streamable-http`); `--http` bleibt als Alias für `streamable-http`.

### Authentifizierung (optional)

Der HTTP-Transport ist standardmässig offen (öffentliche read-only Daten). Für
einen Bearer-Token-Zwang über die CORS/Auth-App-Factory `MCP_BEARER_TOKENS`
setzen:

```bash
MCP_BEARER_TOKENS="alice:tok_abc,bob:tok_def" MCP_ALLOWED_ORIGINS="https://claude.ai" \
  uvicorn parlament_mcp.server:create_http_app --factory --host 0.0.0.0 --port 8080
```

Jeder Request braucht dann `Authorization: Bearer <token>`; die Identität kommt
aus dem validierten Token, nicht aus einem Session-Header (siehe
[`docs/security.md`](docs/security.md)).

### Docker

```bash
docker compose up --build          # bindet nur 127.0.0.1:8080
# oder das gehärtete Image direkt bauen (non-root, read-only FS):
docker build -t parlament-mcp .
```

Kubernetes-Manifeste (gehärteter `securityContext`, Resource-Limits, Egress-
`NetworkPolicy`, `Mcp-Session-Id`-Sticky-Routing) liegen unter
[`deploy/k8s/`](deploy/k8s/); ein HAProxy-Stick-Table-Beispiel in
[`deploy/haproxy.cfg`](deploy/haproxy.cfg).

---

## 💡 Beispielabfragen

**KI und Schule – offene Vorstösse:**
```
parlament_search_business(keyword="Künstliche Intelligenz", keyword2="Bildung", status="Eingereicht")
```

**Alle Zürcher Ratsmitglieder:**
```
parlament_search_members(canton="ZH", active_only=True)
```

**Wie hat der Rat über Bildungsdigitalisierung abgestimmt?**
```
parlament_get_votes(keyword="Digitalisierung")
```

**Was hat Nationalrätin X zum Thema KI gesagt?**
```
parlament_get_transcripts(speaker_name="Müller", keyword="KI")
```

---

## 🔗 Synergien im Portfolio

| Partner-Server | Kombination |
|---|---|
| [`fedlex-mcp`](https://github.com/malkreide/fedlex-mcp) | Gesetzestext ↔ parlamentarische Debatte, die ihn geschaffen hat |
| [`zurich-opendata-mcp`](https://github.com/malkreide/zurich-opendata-mcp) | Städtische Daten ↔ kantonale/nationale Vorstösse |
| [`swiss-statistics-mcp`](https://github.com/malkreide/swiss-statistics-mcp) | Statistiken ↔ Vorstösse, die sich darauf beziehen |

**Power-Query-Beispiel:**
```
«Zeig mir alle Zürcher Vorstösse zu KI in der Bildung
 und verlinke die relevanten Bundesgesetze aus fedlex-mcp.»
```

---

## 📊 Datenquelle

- **API:** [ws.parlament.ch/odata.svc](https://ws.parlament.ch/odata.svc/)
- **Authentifizierung:** Keine (Phase 1 – No-Auth-First)
- **Protokoll:** OData v3 / JSON
- **Abdeckung:** Alle Parlamentsgeschäfte seit 1978; Abstimmungen und Transkripte
- **Aktualisierung:** Echtzeit (offizieller Datendienst des Bundes)

---

## 📜 Datenquellen & Lizenzen

| Quelle | Lizenz | Attribution |
|---|---|---|
| Curia Vista (ws.parlament.ch) | CC BY 4.0 | © Schweizer Parlament, CC BY 4.0 |

Jede Tool-Antwort ist ein typisiertes strukturiertes Objekt (FastMCP exponiert
das Output-Schema) mit `source`, `license`, `provenance`, `match_type` und
`count` plus typisierten `results`. Die Daten werden unverändert weitergegeben.

## 🧭 Phase

Dieser Server ist in **Phase 1 — Read-only Wrapper** (alle Tools
`readOnlyHint: true`, kein Write). Das Phasenmodell steht in
[`docs/roadmap.md`](docs/roadmap.md).

## 🔖 MCP-Protokoll-Version

Getestet/gepinnt gegen MCP-Spec **`2025-06-18`** (`PROTOCOL_VERSION` in
`src/parlament_mcp/config.py`). SDK-Updates kommen monatlich via Dependabot;
Spec-Bumps werden im [`CHANGELOG.md`](CHANGELOG.md) festgehalten.

## 🧱 MCP-Primitive

Phase 1 nutzt **nur Tools** — Begründung und Phase-2-Resources-Plan in
[`docs/adr/ADR-003-mcp-primitives.md`](docs/adr/ADR-003-mcp-primitives.md).

## 🏷️ Tool-Annotations

Alle Tools deklarieren explizite, verhaltenskonsistente Annotations:

| Tool | readOnly | destructive | idempotent | openWorld |
|---|:--:|:--:|:--:|:--:|
| `parlament_search_business`  | ✅ | — | ✅ | ✅ |
| `parlament_get_business`     | ✅ | — | ✅ | ✅ |
| `parlament_search_members`   | ✅ | — | ✅ | ✅ |
| `parlament_get_votes`        | ✅ | — | ✅ | ✅ |
| `parlament_get_sessions`     | ✅ | — | ✅ | ✅ |
| `parlament_get_transcripts`  | ✅ | — | ✅ | ✅ |

## 📈 Observability

Strukturierte JSON-Logs gehen auf **stderr** (stdout bleibt dem stdio-Protokoll
vorbehalten). OpenTelemetry-Tracing umschliesst jeden Tool-Call und
instrumentiert ausgehendes HTTP automatisch; mit gesetztem
`OTEL_EXPORTER_OTLP_ENDPOINT` (Extra `otel-export`) werden Spans exportiert.
Vollständige Security-Posture (Lethal-Trifecta-Bewertung, Egress-Allow-List,
Gateway-Härtung) in [`docs/security.md`](docs/security.md).

---

## 🛡️ Safety & Limits

| Aspekt | Details |
|--------|---------|
| **Zugriff** | Nur lesend (`readOnlyHint: true`) — der Server kann keine Daten ändern oder löschen |
| **Personendaten** | Parlamentsgeschäfte sind öffentliche Amtshandlungen (BGÖ). Es werden keine privaten Daten abgerufen oder gespeichert. |
| **Rate Limits** | Eingebaute Obergrenzen pro Abfrage: max. 100 Treffer (Geschäfte/Mitglieder), 50 (Abstimmungen/Transkripte), 10 (Sessionen) |
| **Timeout** | 20 Sekunden pro API-Aufruf |
| **Authentifizierung** | Keine API-Keys nötig — Curia Vista ist öffentlich zugänglich |
| **Datenquelle** | Offizieller Datendienst des Bundes (Schweizerische Parlamentsdienste) |
| **Nutzungsbedingungen** | Es gelten die ToS von [ws.parlament.ch](https://ws.parlament.ch/) — Schweizerische Parlamentsdienste |

---

## Bekannte Einschränkungen

- OData `substringof()`-Filter unterscheidet Gross-/Kleinschreibung bei manchen Feldern
- Transkript-Volltextsuche kann bei sehr breiten Abfragen langsam sein (`limit` verwenden)
- Session-Namen können für sehr aktuelle Sessionen `null` sein – stattdessen Session-ID nutzen
- Derzeit nur Sprache `DE` vollständig getestet (`FR`, `IT` verfügbar)

---

## Mitwirken

Siehe [CONTRIBUTING.de.md](CONTRIBUTING.de.md).

---

## Sicherheit

Siehe [SECURITY.de.md](SECURITY.de.md) für die Sicherheitsrichtlinie und
Sicherheitslage (Schwachstellenmeldung, Lethal-Trifecta-Bewertung, akzeptierte
Risiken).

---

## Lizenz

MIT © [Hayal Oezkan](https://github.com/malkreide) — siehe [LICENSE](LICENSE)

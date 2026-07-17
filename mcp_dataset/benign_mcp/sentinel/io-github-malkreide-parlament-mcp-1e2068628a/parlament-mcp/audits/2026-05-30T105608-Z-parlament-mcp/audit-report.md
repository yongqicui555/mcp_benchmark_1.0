# MCP-Server Audit-Report — `parlament-mcp`

**Audit-Datum:** 2026-05-30
**Skill-Version:** 1.0.0
**Catalog-Version:** 1.0.0 (catalog_hash 091f446b2796)

---

## 1. Executive Summary

Server `parlament-mcp` wurde gegen 44 anwendbare Best-Practice-Checks geprüft. 15 bestanden, 29 Findings dokumentiert (3 critical, 13 high, 13 medium, 0 low). Production-Readiness: NICHT erreicht — blockierend: SDK-001, SEC-016.

**Production-Readiness:** NO

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `parlament-mcp` |
| Audit-Datum | 2026-05-30 |
| Skill-Version | 1.0.0 |
| Catalog-Version | 1.0.0 (catalog_hash 091f446b2796) |
| transport | `dual` |
| auth_model | `none` |
| data_class | `Public Open Data` |
| write_capable | `False` |
| deployment | `['local-stdio', 'Railway']` |
| uses_sampling | `False` |
| tools_make_external_requests | `True` |
| stadt_zuerich_context | `False` |
| schulamt_context | `False` |
| data_source.is_swiss_open_data | `True` |

---

## 3. Applicability

### Status pro Kategorie

| Kategorie | Pass | Fail | Partial | Todo | N/A |
|---|---|---|---|---|---|
| ARCH | 6 | 0 | 5 | 0 | 0 |
| CH | 0 | 0 | 1 | 0 | 0 |
| OBS | 2 | 0 | 3 | 0 | 0 |
| OPS | 1 | 0 | 2 | 0 | 0 |
| SCALE | 0 | 0 | 5 | 0 | 0 |
| SDK | 0 | 1 | 3 | 0 | 0 |
| SEC | 6 | 1 | 8 | 0 | 0 |
| **Total** | **15** | **2** | **27** | **0** | **0** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| SEC-009 | SEC | critical | partial |
| SEC-016 | SEC | critical | fail |
| SEC-019 | SEC | critical | partial |
| ARCH-004 | ARCH | high | partial |
| OBS-001 | OBS | high | partial |
| OPS-001 | OPS | high | partial |
| OPS-003 | OPS | high | partial |
| SCALE-001 | SCALE | high | partial |
| SCALE-002 | SCALE | high | partial |
| SCALE-003 | SCALE | high | partial |
| SDK-001 | SDK | high | fail |
| SDK-004 | SDK | high | partial |
| SEC-007 | SEC | high | partial |
| SEC-018 | SEC | high | partial |
| SEC-021 | SEC | high | partial |
| SEC-022 | SEC | high | partial |
| ARCH-002 | ARCH | medium | partial |
| ARCH-003 | ARCH | medium | partial |
| ARCH-008 | ARCH | medium | partial |
| ARCH-012 | ARCH | medium | partial |
| CH-004 | CH | medium | partial |
| OBS-003 | OBS | medium | partial |
| OBS-006 | OBS | medium | partial |
| SCALE-004 | SCALE | medium | partial |
| SCALE-006 | SCALE | medium | partial |
| SDK-002 | SDK | medium | partial |
| SDK-003 | SDK | medium | partial |
| SEC-014 | SEC | medium | partial |
| SEC-015 | SEC | medium | partial |

**Gesamt:** 29 Findings

---

## 5. Detail-Findings

### ARCH-002

## Finding: ARCH-002 — Tool-Beschreibung mit Use-Case-Tags

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** ARCH-002
**Verification-Status:** partial

### Observed Behavior / Evidence
- Tool-Docstrings sind ausführlich (>100 Zeichen) und nennen Use-Cases prosaisch ('Anker-Abfrage…', server.py:318-326)

### Gaps vs. Best-Practice
- Keine strukturierten <use_case>/<important_notes>-Tags in den Beschreibungen

### Remediation
Siehe Check `ARCH-002` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### ARCH-003

## Finding: ARCH-003 — «Not Found» Anti-Pattern

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** ARCH-003
**Verification-Status:** partial

### Observed Behavior / Evidence
- Tools liefern handlungsorientierte deutsche Not-Found-Texte statt leerer Listen (z.B. 'Keine Vorstösse gefunden…', server.py:360)

### Gaps vs. Best-Practice
- Kein match_type-Feld (exact/fuzzy/none) und kein Fuzzy-/Vorschlags-Mechanismus bei leeren Treffern

### Remediation
Siehe Check `ARCH-003` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### ARCH-004

## Finding: ARCH-004 — Inversion of Control: Transport-agnostische Logik

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** ARCH-004
**Verification-Status:** partial

### Observed Behavior / Evidence
- Tool-Handler greifen nicht auf Transport-Internals (request.headers etc.) zu — rein Pydantic-Input-Modelle
- Dual-Transport unterstützt: stdio (Default) + streamable-http (server.py:751-758)

### Gaps vs. Best-Practice
- Keine Settings/BaseSettings — Konfiguration über Modul-Konstanten + sys.argv
- Transport-Auswahl via CLI-Flag '--http' statt ENV-Var; README behauptet MCP_TRANSPORT=sse, was der Code NICHT implementiert (Doku/Code-Mismatch)
- Kein gemeinsamer Lifespan-Setup

### Remediation
Siehe Check `ARCH-004` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M


### ARCH-008

## Finding: ARCH-008 — Drei MCP-Primitive nutzen

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** ARCH-008
**Verification-Status:** partial

### Observed Behavior / Evidence
- Server nutzt ausschliesslich das Tools-Primitiv (6 Tools), keine Resources/Prompts

### Gaps vs. Best-Practice
- Keine dokumentierte Begründung im README, warum nur Tools verwendet werden (Pass-Kriterium); read-only get_*-Tools sind Resource-Kandidaten

### Remediation
Siehe Check `ARCH-008` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M


### ARCH-012

## Finding: ARCH-012 — protocolVersion-Pinning + CHANGELOG

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** ARCH-012
**Verification-Status:** partial

### Observed Behavior / Evidence
- CHANGELOG.md im Keep-a-Changelog-Format mit SemVer-Bekenntnis (CHANGELOG.md:1-6)

### Gaps vs. Best-Practice
- protocolVersion nicht explizit gepinnt (grep protocol_version → nicht vorhanden) — nimmt SDK-Default
- Keine README-Sektion 'MCP Protocol Version' / Update-Policy
- Kein Dependabot/Renovate für monatliche SDK-Update-PRs

### Remediation
Siehe Check `ARCH-012` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### CH-004

## Finding: CH-004 — OGD-CH Lizenz-Compliance

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** CH-004
**Verification-Status:** partial

### Observed Behavior / Evidence
- README nennt die Datenquelle Curia Vista (parlament.ch) und liefert Curia-Vista-Deeplink pro Treffer (server.py:399)

### Gaps vs. Best-Practice
- Keine explizite Lizenz-/Attributions-Angabe (CC BY 4.0) im README
- Tool-Antworten enthalten kein dediziertes source/license-Feld

### Remediation
Siehe Check `CH-004` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### OBS-001

## Finding: OBS-001 — Protocol vs. Execution Errors

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** OBS-001
**Verification-Status:** partial

### Observed Behavior / Evidence
- Tools fangen Exceptions via _handle_error() und liefern handlungsorientierte Fehlertexte statt JSON-RPC-Errors (server.py:102-115, 356-357)
- Empty-Results werden als normaler Text zurückgegeben, nicht als Error

### Gaps vs. Best-Practice
- Fehler werden als plain str zurückgegeben, nicht mit isError:true-Konvention
- Keine standardisierten JSON-RPC-Fehlercodes (-326xx)
- Kein Test deckt den Execution-Error-Pfad ab (kein Test mockt eine Exception)

### Remediation
Siehe Check `OBS-001` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M


### OBS-003

## Finding: OBS-003 — Structured Logging RFC 5424

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** OBS-003
**Verification-Status:** partial

### Observed Behavior / Evidence
- Kein print() im Code → kein stdout-Konflikt (Synergie OBS-004)

### Gaps vs. Best-Practice
- Kein strukturierter Logger (structlog/loguru) als Dependency; Server loggt überhaupt nicht
- Empfehlung: structlog mit JSON-Output auf sys.stderr, bound context pro Tool-Call

### Remediation
Siehe Check `OBS-003` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### OBS-006

## Finding: OBS-006 — OpenTelemetry Tracing

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** OBS-006
**Verification-Status:** partial

### Observed Behavior / Evidence
- is_cloud_deployed=true → Check anwendbar

### Gaps vs. Best-Practice
- Kein OpenTelemetry-Setup (grep opentelemetry → nicht vorhanden); keine Tool-Call-Spans/Tracing
- Für Cloud-Forensik/Performance empfohlen, aber medium-Priorität

### Remediation
Siehe Check `OBS-006` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M


### OPS-001

## Finding: OPS-001 — Test-Strategie

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** OPS-001
**Verification-Status:** partial

### Observed Behavior / Evidence
- @pytest.mark.live-Marker genutzt + in pyproject registriert (pyproject.toml:59-61, tests/test_server.py:173)
- CI läuft 'pytest -m "not live"' (.github/workflows/ci.yml)
- Unit-Tests mit gemockten HTTP-Antworten (unittest.mock patch von _odata_get)

### Gaps vs. Best-Practice
- Nur ~3-4 von 6 Tools haben Unit-Tests (get_business, get_votes, get_transcripts ohne Test)
- respx ist Dev-Dependency, wird aber nicht genutzt (mock.patch statt respx)
- Kein separater nightly/manueller Live-Test-Workflow

### Remediation
Siehe Check `OPS-001` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M


### OPS-003

## Finding: OPS-003 — Phasenarchitektur

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** OPS-003
**Verification-Status:** partial

### Observed Behavior / Evidence
- Alle Tools readOnlyHint=True → konsistent mit Phase 1; README erwähnt 'Phase 1 – No-Auth-First'

### Gaps vs. Best-Practice
- Keine explizite Phase-Sektion/Status-Tabelle im README
- Kein docs/roadmap.md mit Phasen-Tasks und Übergangs-Voraussetzungen

### Remediation
Siehe Check `OPS-003` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SCALE-001

## Finding: SCALE-001 — Streamable HTTP für Cloud

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SCALE-001
**Verification-Status:** partial

### Observed Behavior / Evidence
- streamable-http-Transport für Cloud vorhanden (server.py:756); keine veraltete WebSocket-Implementierung

### Gaps vs. Best-Practice
- Transport-Auswahl via CLI-Flag '--http' statt ENV-Var MCP_TRANSPORT
- README dokumentiert 'MCP_TRANSPORT=sse PORT=8080' — entspricht NICHT dem Code (--http/--port)
- Kein Deployment-Manifest (railway.toml/render.yaml) das den Transport explizit setzt

### Remediation
Siehe Check `SCALE-001` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SCALE-002

## Finding: SCALE-002 — Stateful Load Balancing

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SCALE-002
**Verification-Status:** partial

### Observed Behavior / Evidence
- Tools sind zustandslose Read-Operationen ohne Subscriptions/Per-Session-Daten → Session-Verlust bei Pod-Switch ist verlustarm

### Gaps vs. Best-Practice
- Keine Sticky-Sessions und kein Shared-State-Session-Manager (Redis) konfiguriert
- Aktuell Single-Instance-tauglich; vor horizontaler Skalierung (>1 Replica) zwingend nachzurüsten

### Remediation
Siehe Check `SCALE-002` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M


### SCALE-003

## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SCALE-003
**Verification-Status:** partial

### Observed Behavior / Evidence
- Kein Mehr-Replica-Betrieb erkennbar; Single-Instance benötigt kein Edge-LB-Session-Routing

### Gaps vs. Best-Practice
- Keine HAProxy/NGINX/Ingress-Konfiguration für Mcp-Session-Id-Routing vorhanden
- Vor Skalierung gemeinsam mit SCALE-002 umzusetzen

### Remediation
Siehe Check `SCALE-003` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M


### SCALE-004

## Finding: SCALE-004 — Containerization mit Multi-Stage-Builds

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SCALE-004
**Verification-Status:** partial

### Observed Behavior / Evidence
- is_cloud_deployed=true → Check anwendbar

### Gaps vs. Best-Practice
- Kein Dockerfile vorhanden — kein Multi-Stage-Build, kein non-root USER, kein HEALTHCHECK
- Empfehlung: schlankes Multi-Stage-Dockerfile (Synergie SEC-007)

### Remediation
Siehe Check `SCALE-004` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SCALE-006

## Finding: SCALE-006 — Resource-Limits per Container

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SCALE-006
**Verification-Status:** partial

### Observed Behavior / Evidence
- is_cloud_deployed=true → Check anwendbar

### Gaps vs. Best-Practice
- Keine dokumentierten Resource-Limits (Memory/CPU/FD) — weder Manifest noch README
- Bei Railway via UI setzbar, sollte dokumentiert werden

### Remediation
Siehe Check `SCALE-006` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SDK-001

## Finding: SDK-001 — FastMCP Lifespan Management

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SDK-001
**Verification-Status:** fail

### Observed Behavior / Evidence
- Kein FastMCP-Lifespan (grep lifespan/asynccontextmanager → nicht vorhanden)
- httpx.AsyncClient wird PRO Tool-Call neu erstellt (server.py:94 und server.py:429) — exakt das Fail-Pattern des Checks

### Gaps vs. Best-Practice
- Kein Connection-Pooling → Performance-Einbusse und Leak-Gefahr bei Fehlern
- Remediation: @asynccontextmanager-Lifespan mit geteiltem httpx.AsyncClient in server.state, Cleanup im finally

### Remediation
Siehe Check `SDK-001` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SDK-002

## Finding: SDK-002 — Strukturierte Tool-Returns

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SDK-002
**Verification-Status:** partial

### Observed Behavior / Evidence
- Pydantic v2 als Dependency (pyproject.toml:32) und für alle Tool-INPUTS genutzt

### Gaps vs. Best-Practice
- Alle Tools haben Rückgabetyp '-> str' (Markdown/JSON-String) statt strukturierter BaseModel/TypedDict-Returns
- Kein konsistenter Response-Envelope mit source/provenance/count → FastMCP exponiert kein Output-Schema

### Remediation
Siehe Check `SDK-002` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SDK-003

## Finding: SDK-003 — Context Injection

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SDK-003
**Verification-Status:** partial

### Observed Behavior / Evidence
- Tools sind überwiegend schnelle Einzel-API-Calls (HTTP_TIMEOUT 20s)

### Gaps vs. Best-Practice
- Kein Tool deklariert ctx: Context → keine Progress-Reports/ctx.info-Logging
- Transcript-Suche kann laut README langsam sein → Progress-Reports wären sinnvoll

### Remediation
Siehe Check `SDK-003` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SDK-004

## Finding: SDK-004 — CORS Mcp-Session-Id Exposure

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SDK-004
**Verification-Status:** partial

### Observed Behavior / Evidence
- HTTP-Transport vorhanden; primärer Use-Case stdio (Claude Desktop) und server-seitig — dort kein CORS nötig

### Gaps vs. Best-Practice
- Keine CORSMiddleware/expose_headers-Konfiguration → Browser-basierte MCP-Clients können Mcp-Session-Id nicht lesen
- Mcp-Session-Id fehlt in expose_headers; relevant sobald Browser-Clients angebunden werden

### Remediation
Siehe Check `SDK-004` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SEC-007

## Finding: SEC-007 — Container-Sandboxing

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-007
**Verification-Status:** partial

### Observed Behavior / Evidence
- Read-only Public-Data-Server ohne Secrets → reduzierte Angriffsfläche bei Code-Kompromittierung

### Gaps vs. Best-Practice
- Kein Dockerfile/Container-Hardening vorhanden (kein non-root USER, kein read-only FS, keine Capability-Drops)
- Empfehlung: gehärtetes Multi-Stage-Dockerfile (Synergie SCALE-004) für Cloud-Deployment

### Remediation
Siehe Check `SEC-007` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SEC-009

## Finding: SEC-009 — Session-ID Cryptographic Binding

**Severity:** critical
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-009
**Verification-Status:** partial

### Observed Behavior / Evidence
- transport=dual → HTTP-Transport vorhanden; Session-ID-Generierung an FastMCP delegiert (kryptografisch sichere uuid4)
- Server ist read-only auf Public Open Data, kein Schreib-/Account-Zugriff

### Gaps vs. Best-Practice
- Kein kryptografisches Binding der Mcp-Session-Id an validierte User-Identität (mangels Auth nicht umsetzbar)
- Reales Hijacking-Risiko aktuell gering (keine privaten Daten, keine Write-Ops); wird kritisch, sobald Auth/PII hinzukommt

### Remediation
Siehe Check `SEC-009` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M


### SEC-014

## Finding: SEC-014 — Tool-Allow-Listing via Gateway

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-014
**Verification-Status:** partial

### Observed Behavior / Evidence
- Einzel-Server, kein Enterprise-Gateway-Kontext; alle Tools read-only Public Data → geringe Relevanz

### Gaps vs. Best-Practice
- Keine Tool-Allow-List/Group-Checks; relevant erst im Multi-Server-Gateway-Setup

### Remediation
Siehe Check `SEC-014` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
L


### SEC-015

## Finding: SEC-015 — Pre-Flight Tool-Poisoning Detection

**Severity:** medium
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-015
**Verification-Status:** partial

### Observed Behavior / Evidence
- Nur eigener, vertrauenswürdiger Server → Tool-Poisoning-Risiko aktuell niedrig

### Gaps vs. Best-Practice
- Keine Pre-Flight-Tool-Poisoning-Detection; wird relevant, sobald externe MCP-Server in ein Gateway integriert werden

### Remediation
Siehe Check `SEC-015` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M


### SEC-016

## Finding: SEC-016 — 0.0.0.0-Binding-Prevention (NeighborJack)

**Severity:** critical
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-016
**Verification-Status:** fail

### Observed Behavior / Evidence
- server.py:756: mcp.run(transport='streamable-http', host='0.0.0.0', port=port) — 0.0.0.0 als Code-Default hartcodiert
- Kein MCP_HOST-ENV-Override, kein 127.0.0.1-Default, keine Container-Differenzierung, keine Warnung beim Binding

### Gaps vs. Best-Practice
- NeighborJack-Risiko: lokal via --http gestarteter Server ist für das ganze Subnetz erreichbar
- Remediation: MCP_HOST-ENV mit Default 127.0.0.1, 0.0.0.0 nur im Dockerfile/Deploy-Manifest explizit

### Remediation
Siehe Check `SEC-016` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SEC-018

## Finding: SEC-018 — Input-Validation an Tool-Boundaries

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-018
**Verification-Status:** partial

### Observed Behavior / Evidence
- Alle Tools haben Pydantic-v2-Input-Modelle mit extra='forbid' (server.py:151,206,217,250,269,279)
- Numerische Felder mit ge/le-Constraints (limit ge=1/le=100, offset ge=0); String max_length; Datum mit Whitelist-Pattern (server.py:184)

### Gaps vs. Best-Practice
- model_config setzt strict=True NICHT → Pydantic-Coercion ('1'→1) aktiv
- Keine Tests gegen Input-Edge-Cases (zu lang, out-of-range, unbekannte Felder)

### Remediation
Siehe Check `SEC-018` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SEC-019

## Finding: SEC-019 — Lethal Trifecta vermeiden

**Severity:** critical
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-019
**Verification-Status:** partial

### Observed Behavior / Evidence
- Trifecta-Score ~1/3: liest nur Public Open Data (keine privaten Daten), read-only (keine externe Sende-/Write-Fähigkeit)
- Strukturell sicher — keine verbotene Kombination vorhanden

### Gaps vs. Best-Practice
- Keine dokumentierte Lethal-Trifecta-Bewertung im README/docs (Pass-Kriterium des Checks)

### Remediation
Siehe Check `SEC-019` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
S


### SEC-021

## Finding: SEC-021 — Egress-Allow-List

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-021
**Verification-Status:** partial

### Observed Behavior / Evidence
- De-facto Single-Host-Egress: Code kontaktiert ausschliesslich die hartcodierte BASE_URL ws.parlament.ch

### Gaps vs. Best-Practice
- Keine explizite Code-Layer Allow-List (frozenset) mit assert_host_allowed-Check
- Keine Network-Layer-Egress-Control (NetworkPolicy/Security Group)
- Keine docs/network-egress.md — reales Risiko gering (keine user-kontrollierten URLs)

### Remediation
Siehe Check `SEC-021` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M


### SEC-022

## Finding: SEC-022 — Tool-Hash-Pinning + Namespace

**Severity:** high
**Status:** open
**Server:** parlament-mcp
**Check-Reference:** SEC-022
**Verification-Status:** partial

### Observed Behavior / Evidence
- Konsistenter Namespace-Präfix 'parlament_' auf allen 6 Tools (server.py) → Cross-Server-Tool-Shadowing verhindert

### Gaps vs. Best-Practice
- Kein Tool-Definitions-Hash-Snapshot im Release-Workflow (Rug-Pull-Detection fehlt)
- CHANGELOG nennt keine Tool-Definition-Hashes/Änderungen

### Remediation
Siehe Check `SEC-022` im mcp-audit-skill-Katalog (Sektion *Remediation*) für das vollständige Pass-Pattern.

### Effort Estimate
M


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **SEC-009** (critical, partial)
2. **SEC-016** (critical, fail)
3. **SEC-019** (critical, partial)
4. **ARCH-004** (high, partial)
5. **OBS-001** (high, partial)
6. **OPS-001** (high, partial)
7. **OPS-003** (high, partial)
8. **SCALE-001** (high, partial)
9. **SCALE-002** (high, partial)
10. **SCALE-003** (high, partial)
11. **SDK-001** (high, fail)
12. **SDK-004** (high, partial)
13. **SEC-007** (high, partial)
14. **SEC-018** (high, partial)
15. **SEC-021** (high, partial)
16. **SEC-022** (high, partial)
17. **ARCH-002** (medium, partial)
18. **ARCH-003** (medium, partial)
19. **ARCH-008** (medium, partial)
20. **ARCH-012** (medium, partial)
21. **CH-004** (medium, partial)
22. **OBS-003** (medium, partial)
23. **OBS-006** (medium, partial)
24. **SCALE-004** (medium, partial)
25. **SCALE-006** (medium, partial)
26. **SDK-002** (medium, partial)
27. **SDK-003** (medium, partial)
28. **SEC-014** (medium, partial)
29. **SEC-015** (medium, partial)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |
| catalog_version | `1.0.0 (catalog_hash 091f446b2796)` |
| audit_date | `2026-05-30` |


_Generated by tools/build_report.py — do not edit by hand._

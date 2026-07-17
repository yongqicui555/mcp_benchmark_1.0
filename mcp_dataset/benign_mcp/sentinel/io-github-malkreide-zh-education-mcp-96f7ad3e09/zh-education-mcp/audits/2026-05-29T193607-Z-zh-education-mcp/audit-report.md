# MCP-Server Audit-Report — `zh-education-mcp`

**Audit-Datum:** 
**Skill-Version:** 1.0.0
**Catalog-Version:** ?

---

## 1. Executive Summary

Server `zh-education-mcp` wurde gegen 44 anwendbare Best-Practice-Checks geprüft. 13 bestanden, 31 Findings dokumentiert (2 critical, 15 high, 14 medium, 0 low). Production-Readiness: NICHT erreicht — blockierend: SCALE-002, SCALE-003, SDK-001, SDK-004, SEC-007.

**Production-Readiness:** NO

---

## 2. Profil-Snapshot

| Feld | Wert |
|---|---|
| Server-Name | `zh-education-mcp` |
| Audit-Datum | ? |
| Skill-Version | 1.0.0 |
| Catalog-Version | ? |
| transport | `dual` |
| auth_model | `none` |
| data_class | `Public Open Data` |
| write_capable | `False` |
| deployment | `['local-stdio', 'andere']` |
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
| ARCH | 5 | 2 | 4 | 0 | 0 |
| CH | 0 | 0 | 1 | 0 | 0 |
| OBS | 1 | 2 | 2 | 0 | 0 |
| OPS | 1 | 0 | 2 | 0 | 0 |
| SCALE | 0 | 4 | 1 | 0 | 0 |
| SDK | 0 | 2 | 2 | 0 | 0 |
| SEC | 6 | 3 | 6 | 0 | 0 |
| **Total** | **13** | **13** | **18** | **0** | **0** |

---

## 4. Findings-Übersicht

_Policy: `fail-or-partial`_

| ID | Category | Severity | Status |
|---|---|---|---|
| SEC-004 | SEC | critical | partial |
| SEC-009 | SEC | critical | partial |
| ARCH-004 | ARCH | high | partial |
| OBS-001 | OBS | high | partial |
| OBS-002 | OBS | high | partial |
| OPS-001 | OPS | high | partial |
| OPS-003 | OPS | high | partial |
| SCALE-001 | SCALE | high | partial |
| SCALE-002 | SCALE | high | fail |
| SCALE-003 | SCALE | high | fail |
| SDK-001 | SDK | high | fail |
| SDK-004 | SDK | high | fail |
| SEC-005 | SEC | high | partial |
| SEC-007 | SEC | high | fail |
| SEC-018 | SEC | high | partial |
| SEC-021 | SEC | high | partial |
| SEC-022 | SEC | high | partial |
| ARCH-003 | ARCH | medium | partial |
| ARCH-007 | ARCH | medium | partial |
| ARCH-008 | ARCH | medium | fail |
| ARCH-011 | ARCH | medium | partial |
| ARCH-012 | ARCH | medium | fail |
| CH-004 | CH | medium | partial |
| OBS-003 | OBS | medium | fail |
| OBS-006 | OBS | medium | fail |
| SCALE-004 | SCALE | medium | fail |
| SCALE-006 | SCALE | medium | fail |
| SDK-002 | SDK | medium | partial |
| SDK-003 | SDK | medium | partial |
| SEC-014 | SEC | medium | fail |
| SEC-015 | SEC | medium | fail |

**Gesamt:** 31 Findings

---

## 5. Detail-Findings

### ARCH-003

## Finding: ARCH-003 — «Not Found» Anti-Pattern: Heuristiken statt leerer Antworten

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** ARCH-003
**PDF-Reference:** Sec 2.2

### Observed Behavior / Evidence
- zh_edu_schulkreis_trend liefert Fuzzy-Vorschläge + Hinweis bei Not-Found (server.py:359-366)
- Mehrere Tools verweisen bei Not-Found auf zh_edu_list_schulgemeinden (server.py:516-519,585-589)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein match_type-Feld (exact/fuzzy/none) in den Antworten
- Fuzzy-Fallback nur in einem Tool; sek1_profil/staatsangehoerigkeiten geben Hinweis ohne Vorschläge

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### ARCH-004

## Finding: ARCH-004 — Inversion of Control: Transport-agnostische Server-Logik

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** ARCH-004
**PDF-Reference:** Sec 2.1

### Observed Behavior / Evidence
- Tool-Handler greifen nicht auf request zu; Logik ist transport-agnostisch
- stdio + streamable-http werden beide unterstützt (server.py:853-866)
- Identische Outputs unabhängig vom Transport

### Gaps (Abweichung vom Best-Practice-Katalog)
- Transport-Wahl über sys.argv-Parsing statt ENV-Var/Settings-Objekt (server.py:857-861)
- Konfiguration über globale Modul-Konstanten statt Pydantic-Settings (server.py:32-42)
- Kein ctx: Context in Handlern

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### ARCH-007

## Finding: ARCH-007 — Capability-Aggregation: Composability intern, Atomarität extern

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** ARCH-007
**PDF-Reference:** Sec 2.3

### Observed Behavior / Evidence
- Tools liefern abgeschlossene Resultate (Markdown-Tabellen/JSON), keine reinen IDs
- Aggregation pro Tool aus einem Endpunkt, gecacht

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine Provenance/source-Info in den aggregierten Outputs (Synergie CH-004/SDK-002)
- Keine asyncio.gather-Parallelisierung (aber auch nur 1 Fetch pro Tool)

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### ARCH-008

## Finding: ARCH-008 — Drei Primitive nutzen: Tools, Resources und Prompts

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** ARCH-008
**PDF-Reference:** Anhang A2

### Observed Behavior / Evidence
- Server exponiert ausschliesslich Tools — keine Resources, keine Prompts (server.py)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Weder ≥2 Primitive genutzt noch im README begründet, warum nur Tools
- Read-only/deterministische Tools (zh_edu_list_schulgemeinden) sind Resource-Migrations-Kandidaten

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### ARCH-011

## Finding: ARCH-011 — Standardisierte Repo-Struktur (src-Layout, tests, README.de.md)

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** ARCH-011
**PDF-Reference:** Anhang A8

### Observed Behavior / Evidence
- Pflicht-Files vorhanden: README.md, README.de.md, CHANGELOG.md, LICENSE, pyproject.toml
- src-Layout korrekt, tests/ und .github/workflows/ vorhanden
- CI (ci.yml) + publish.yml vorhanden; README.de.md parallel

### Gaps (Abweichung vom Best-Practice-Katalog)
- 8 Tools (>5) liegen in einer einzigen 867-Zeilen server.py ohne tools/-Aufteilung
- Abweichung von der tools/-Struktur nicht im README begründet

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### ARCH-012

## Finding: ARCH-012 — protocolVersion-Pinning + CHANGELOG + SDK-Update-Disziplin

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** ARCH-012
**PDF-Reference:** Anhang A9

### Observed Behavior / Evidence
- CHANGELOG.md im Keep-a-Changelog-Format vorhanden (CHANGELOG.md)

### Gaps (Abweichung vom Best-Practice-Katalog)
- protocolVersion nirgends explizit gepinnt (grep: keine Treffer)
- Keine README-Sektion 'MCP Protocol Version' und keine Update-Policy
- Kein Dependabot/Renovate für SDK-Updates
- CHANGELOG nennt keine Spec-Version-Bumps

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### CH-004

## Finding: CH-004 — OGD-CH Lizenz-Compliance: CC BY 4.0 Attribution

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** CH-004
**PDF-Reference:** Custom (OGD-CH-Richtlinien)

### Observed Behavior / Evidence
- README dokumentiert Quelle BISTA + CC BY 4.0 + Attributionstext (README.md Safety & Limits)
- Keine Lizenzkonflikte

### Gaps (Abweichung vom Best-Practice-Katalog)
- Tool-Antworten enthalten KEIN source-Feld mit Quelle/Lizenz — der LLM/Nutzer sieht die Attribution nicht zur Antwortzeit
- Keine Per-Datensatz-Provenance bei Aggregation
- CC-BY-Modifikationshinweis (Aggregation) fehlt in den Outputs

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### OBS-001

## Finding: OBS-001 — Protocol vs. Execution Errors: korrekte Trennung

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** OBS-001
**PDF-Reference:** Sec 6.1

### Observed Behavior / Evidence
- Tool-Handler fangen Exceptions ab und geben handlungsorientierte Strings zurück statt zu raisen (server.py:76-89,322-323)
- HTTP-Statuscode-spezifische Meldungen (404/429/502/503)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Fehler werden als normaler String zurückgegeben, nicht als isError:true tool-result
- Keine standardisierten JSON-RPC-Fehlercodes (-326xx/-320xx)
- Kein dedizierter Test für Protocol-Error-Pfad

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### OBS-002

## Finding: OBS-002 — Mask Error Details: keine Stacktraces / SQL ans LLM

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** OBS-002
**PDF-Reference:** Sec 6.2

### Observed Behavior / Evidence
- Keine traceback.format_exc()-Ausgaben in Tool-Returns
- Bekannte Fehlertypen liefern user-freundliche, sanitisierte Meldungen (server.py:78-86)

### Gaps (Abweichung vom Best-Practice-Katalog)
- FastMCP ohne mask_error_details=True initialisiert (server.py:29)
- Generischer Fallback leakt Exception-Detail an den LLM: f'...({type(e).__name__}): {e}' (server.py:89)
- Originalfehler landen nirgends in einem Server-Log (kein Logging vorhanden)

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### OBS-003

## Finding: OBS-003 — Structured Logging mit RFC 5424 Severity-Stufen

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** OBS-003
**PDF-Reference:** Sec 6.3

### Observed Behavior / Evidence
- Kein print() im src/ (gut für stdio)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein structured Logger (structlog/loguru) in dependencies
- Kein JSON/logfmt-Logging, keine Severity-Stufen, keine correlation_id/session-Bindung
- Tool-Calls werden überhaupt nicht geloggt

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### OBS-006

## Finding: OBS-006 — OpenTelemetry Distributed Tracing pro Tool-Call

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** OBS-006
**PDF-Reference:** Anhang B10

### Observed Behavior / Evidence
- Profil is_cloud_deployed=true ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein OpenTelemetry SDK / TracerProvider / OTLP-Exporter
- Keine Auto-Instrumentation für httpx
- Keine Spans pro Tool-Call

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### OPS-001

## Finding: OPS-001 — Test-Strategie: Unit-Tests mocked + Live-Tests gemarkert

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** OPS-001
**PDF-Reference:** Anhang C1

### Observed Behavior / Evidence
- respx-gemockte Unit-Tests vorhanden (tests/test_server.py)
- Live-Test mit @pytest.mark.live markiert; Marker in pyproject.toml registriert
- CI läuft pytest -m 'not live' (.github/workflows/ci.yml)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Nur 6 Unit-Tests gesamt statt ≥5 pro Tool (8 Tools)
- 3 Tools ohne Test: zh_edu_maturitaetsquote, zh_edu_wohnort_trend, zh_edu_mittelschulen
- Kein separater nightly/manueller Live-Test-Workflow

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### OPS-003

## Finding: OPS-003 — Phasenarchitektur: Read-only First, dann Write, dann Multi-Agent

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** OPS-003
**PDF-Reference:** Anhang C4

### Observed Behavior / Evidence
- Phase 1 (No-auth, read-only) explizit im CHANGELOG deklariert (CHANGELOG.md)
- Phase entspricht den Annotations (alle Tools read-only)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine explizite Phase-Sektion im README
- Kein Roadmap-File mit phasenspezifischen Tasks
- Phase-Übergangs-Voraussetzungen nicht dokumentiert

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SCALE-001

## Finding: SCALE-001 — Streamable HTTP statt stdio für Cloud-Deployments

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SCALE-001
**PDF-Reference:** Sec 5.1

### Observed Behavior / Evidence
- streamable-http-Transport implementiert (server.py:863-864)
- Cloud-Deployment nutzt --http (README Render-Anleitung); keine WebSocket-Implementierung

### Gaps (Abweichung vom Best-Practice-Katalog)
- Transport-Selektion über CLI-Flag --http statt ENV-Var
- README verweist auf .../sse-Endpoint, der Code startet aber transport='streamable-http' (bedient /mcp, nicht /sse) — Endpoint-Mismatch

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SCALE-002

## Finding: SCALE-002 — Stateful Load Balancing für Streamable HTTP / SSE

**Severity:** high
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SCALE-002
**PDF-Reference:** Sec 5.2

### Observed Behavior / Evidence
- Profil dual-transport ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine Sticky-Sessions / kein Shared-State-Session-Manager (Redis o.ä.) konfiguriert
- Keine Session-TTL definiert
- Kein Deployment-Manifest mit LB-Affinity

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SCALE-003

## Finding: SCALE-003 — Mcp-Session-Id Routing via Edge-LB (HAProxy Stick-Tables)

**Severity:** high
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SCALE-003
**PDF-Reference:** Sec 5.2

### Observed Behavior / Evidence
- Profil dual + is_cloud_deployed ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein Edge-LB liest Mcp-Session-Id; keine Stick-Table/Hash-Konfig
- Kein Failover-Verhalten getestet/dokumentiert

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SCALE-004

## Finding: SCALE-004 — Containerization mit Multi-Stage-Builds

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SCALE-004
**PDF-Reference:** Sec 5.3

### Observed Behavior / Evidence
- Profil is_cloud_deployed=true ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein Dockerfile im Repo (find: keine Treffer) — keine Multi-Stage-Builds, kein non-root USER, kein HEALTHCHECK

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SCALE-006

## Finding: SCALE-006 — Resource-Limits per Container (Memory, CPU, FDs)

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SCALE-006
**PDF-Reference:** Sec 5.3

### Observed Behavior / Evidence
- Profil is_cloud_deployed=true ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine Container-Resource-Limits (Memory/CPU/FD) — kein Dockerfile/k8s-Manifest vorhanden

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SDK-001

## Finding: SDK-001 — FastMCP Lifespan via @asynccontextmanager + AsyncExitStack

**Severity:** high
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SDK-001
**PDF-Reference:** Sec 3.1

### Observed Behavior / Evidence
- httpx.AsyncClient wird pro Request neu erzeugt (server.py:72, _http_get bei jedem Fetch aufgerufen)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine FastMCP lifespan/@asynccontextmanager (grep: none)
- Kein Connection-Pooling — Client pro Tool-Call statt einmalig im Lifespan
- Kein Cleanup-Pfad

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SDK-002

## Finding: SDK-002 — Pydantic v2 / TypedDict / Dataclass als Tool-Returns

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SDK-002
**PDF-Reference:** Sec 3.1

### Observed Behavior / Evidence
- Pydantic v2 in dependencies; Input-Modelle mit Field-Defaults und ConfigDict (server.py:133-268)
- ResponseFormat als StrEnum (Literal-artig)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Tools haben Return-Annotation -> str (Markdown/JSON-String) statt strukturierter BaseModel/TypedDict/dict-Rückgaben ⇒ kein Output-Schema für den LLM
- Kein konsistenter Response-Envelope (source/provenance/results/count)

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SDK-003

## Finding: SDK-003 — Context Injection für Progress Reports und Logging

**Severity:** medium
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SDK-003
**PDF-Reference:** Sec 3.1

### Observed Behavior / Evidence
- Operationen sind durch 24h-Cache meist schnell (server.py:53-66)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein Tool nutzt ctx: Context; keine ctx.report_progress() bei potenziell langem Cold-Fetch (Timeout 30s, server.py:33)
- Kein ctx.info()/ctx.warning()-Logging

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SDK-004

## Finding: SDK-004 — CORS Mcp-Session-Id Exposure bei HTTP/SSE

**Severity:** high
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SDK-004
**PDF-Reference:** Sec 3.1

### Observed Behavior / Evidence
- Profil Python + dual-transport ⇒ Check anwendbar; README bewirbt Browser-Zugang via claude.ai (README Cloud Deployment)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine CORS-Middleware konfiguriert (grep: none)
- expose_headers/allow_headers mit Mcp-Session-Id nicht gesetzt — Browser-Clients (claude.ai) brechen
- allow_origins nicht konfiguriert

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SEC-004

## Finding: SEC-004 — SSRF-Prevention: HTTPS-Enforcement + IP-Blocklisting

**Severity:** critical
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-004
**PDF-Reference:** Sec 4.4

### Observed Behavior / Evidence
- Alle ausgehenden Requests gehen an einen hartcodierten HTTPS-Host BISTA_API (server.py:32) — kein user-kontrollierter URL/Host ⇒ klassische SSRF nicht möglich
- Schema ist fix https://

### Gaps (Abweichung vom Best-Practice-Katalog)
- follow_redirects=True ohne Redirect-Host-Validierung (server.py:72) — Redirect-basierte SSRF theoretisch möglich
- Keine IP-Blocklist (169.254.169.254, loopback, link-local), keine DNS-Auflösungs-Kontrolle (TOCTOU)
- Residual-Risiko in der Praxis gering wegen fixem, vertrauenswürdigem Host

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SEC-005

## Finding: SEC-005 — DNS-Rebinding-Prevention: DNS-Pinning gegen TOCTOU

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-005
**PDF-Reference:** Sec 4.4

### Observed Behavior / Evidence
- Fixer, vertrauenswürdiger Host (BISTA) reduziert DNS-Rebinding-Risiko erheblich
- verify=False wird NICHT verwendet (grep: none)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein DNS-Pinning; httpx-Default impliziert separate Lookups
- follow_redirects=True erweitert die Lookup-Fläche
- Kein Test, der 1 DNS-Call pro Request verifiziert

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SEC-007

## Finding: SEC-007 — Container-Sandboxing: Docker / chroot mit minimalen Privilegien

**Severity:** high
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SEC-007
**PDF-Reference:** Sec 4.5

### Observed Behavior / Evidence
- Profil deployment enthält local-stdio + Cloud ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein Dockerfile/k8s-Manifest ⇒ kein non-root USER, kein readOnlyRootFilesystem, keine capabilities.drop, kein seccomp-Profil
- Cloud-Deployment ohne jegliche Sandboxing-Definition

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SEC-009

## Finding: SEC-009 — Session-ID Cryptographic Binding (user_id:session_id)

**Severity:** critical
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-009
**PDF-Reference:** Sec 4.6

### Observed Behavior / Evidence
- Kein eigenes Session-Handling — Session-IDs werden an den FastMCP-streamable-http-Stack delegiert (secrets-basiert)
- Datenklasse Public Open Data, read-only ⇒ Impact eines Session-Leaks minimal (nur öffentliche Daten)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine kryptografische Bindung Session-ID↔User, da auth_model=none (keine User-Identität vorhanden)
- Bei öffentlicher Cloud-Exposition ohne Auth: Endpoint für jeden erreichbar — akzeptabel nur für öffentliche read-only Daten, sonst Auth/Netzkontrolle nötig

### Effort Estimate
M  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SEC-014

## Finding: SEC-014 — Tool-Allow-Listing via MCP-Gateway-Pattern

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SEC-014
**PDF-Reference:** Sec 5.3

### Observed Behavior / Evidence
- Profil is_cloud_deployed=true ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine Tool-Allow-List / kein default-deny / kein MCP-Gateway
- Geringe Priorität: standalone, read-only, öffentliche Daten — Gateway-Pattern ist eher Portfolio-Ebene

### Effort Estimate
L  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SEC-015

## Finding: SEC-015 — Pre-Flight Tool-Poisoning Detection

**Severity:** medium
**Status:** open
**Check-Status:** fail
**Server:** zh-education-mcp
**Check-Reference:** SEC-015
**PDF-Reference:** Sec 5.3

### Observed Behavior / Evidence
- Profil is_cloud_deployed=true ⇒ Check anwendbar

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein Pre-Flight Tool-Poisoning-Detection-Layer
- Geringe Priorität für standalone Single-Purpose-Server; relevanter auf Gateway/Portfolio-Ebene

### Effort Estimate
L  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SEC-018

## Finding: SEC-018 — Input-Validation an Tool-Boundaries (Pydantic strict / Zod)

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-018
**PDF-Reference:** Sec 3 / Sec 4 (Defense-in-Depth)

### Observed Behavior / Evidence
- Alle Tool-Argumente über Pydantic-Modelle validiert (server.py:133-268)
- Numerische Felder mit ge/le (letzte_n_jahre ge=1 le=30; top_n ge=1 le=100)
- String-Felder mit min_length/max_length; ConfigDict(extra='forbid') konsequent gesetzt

### Gaps (Abweichung vom Best-Practice-Katalog)
- strict=True nicht gesetzt ⇒ Type-Coercion möglich
- Keine Whitelist-pattern auf String-Feldern
- Keine Edge-Case-Tests (zu lange Strings, Out-of-Range, unbekannte Felder)

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SEC-021

## Finding: SEC-021 — Egress-Allow-List: Code-Layer und Network-Layer

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-021
**PDF-Reference:** Anhang B5 + B12

### Observed Behavior / Evidence
- De-facto Single-Host-Egress: alle Requests gehen an hartcodiertes BISTA_API (server.py:32)

### Gaps (Abweichung vom Best-Practice-Katalog)
- Keine erzwungene Code-Layer-Allow-List (frozenset) und kein assert_host_allowed vor Requests
- Keine Network-Layer-Egress-Kontrolle dokumentiert
- follow_redirects=True kann den impliziten Single-Host umgehen

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


### SEC-022

## Finding: SEC-022 — Tool-Hash-Pinning + Namespace-Präfix gegen Rug Pull

**Severity:** high
**Status:** open
**Check-Status:** partial
**Server:** zh-education-mcp
**Check-Reference:** SEC-022
**PDF-Reference:** Anhang B4

### Observed Behavior / Evidence
- Konsistentes Namespace-Präfix zh_edu_ über alle Tools (server.py)
- CHANGELOG nennt Tools beim Namen; SemVer im CHANGELOG-Header erklärt

### Gaps (Abweichung vom Best-Practice-Katalog)
- Kein Hash-Snapshot der Tool-Definitionen bei Releases (Rug-Pull-Detection)
- Präfix nutzt zh_edu_ statt des empfohlenen <server>__<tool>-Schemas
- Keine User-Re-Approval-Hinweise bei Tool-Description-Änderungen

### Effort Estimate
S  (S < 1d · M 1-3d · L 1-2w · XL >2w)


---

## 6. Remediation-Plan

### Empfohlene Reihenfolge

1. **SEC-004** (critical, partial)
2. **SEC-009** (critical, partial)
3. **ARCH-004** (high, partial)
4. **OBS-001** (high, partial)
5. **OBS-002** (high, partial)
6. **OPS-001** (high, partial)
7. **OPS-003** (high, partial)
8. **SCALE-001** (high, partial)
9. **SCALE-002** (high, fail)
10. **SCALE-003** (high, fail)
11. **SDK-001** (high, fail)
12. **SDK-004** (high, fail)
13. **SEC-005** (high, partial)
14. **SEC-007** (high, fail)
15. **SEC-018** (high, partial)
16. **SEC-021** (high, partial)
17. **SEC-022** (high, partial)
18. **ARCH-003** (medium, partial)
19. **ARCH-007** (medium, partial)
20. **ARCH-008** (medium, fail)
21. **ARCH-011** (medium, partial)
22. **ARCH-012** (medium, fail)
23. **CH-004** (medium, partial)
24. **OBS-003** (medium, fail)
25. **OBS-006** (medium, fail)
26. **SCALE-004** (medium, fail)
27. **SCALE-006** (medium, fail)
28. **SDK-002** (medium, partial)
29. **SDK-003** (medium, partial)
30. **SEC-014** (medium, fail)
31. **SEC-015** (medium, fail)

---

## 7. Audit-Metadata

| Feld | Wert |
|---|---|
| skill_version | `1.0.0` |


_Generated by tools/build_report.py — do not edit by hand._

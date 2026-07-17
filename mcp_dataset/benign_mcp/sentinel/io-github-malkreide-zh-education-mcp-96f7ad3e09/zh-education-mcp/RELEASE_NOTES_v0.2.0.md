# zh-education-mcp v0.2.0 — Production Hardening

Erstes Production-Hardening-Release nach einem vollständigen MCP-Best-Practice-Audit.
Der Server ist jetzt für den dualen Betrieb (lokal stdio + Cloud HTTP) gehärtet.

**Audit-Verifikation:** 42/42 anwendbare Checks bestanden · 0 offene Findings · production-ready
(Skill v1.0.0, Catalog-Hash `091f446b`, Run `2026-05-30T072745-Z-zh-education-mcp`).

## ✨ Highlights

### Architektur & SDK
- ENV-basierte Konfiguration (`MCP_TRANSPORT` / `MCP_HOST` / `MCP_PORT` / `MCP_CORS_ORIGINS` / `MCP_STATELESS_HTTP`)
- `lifespan`-verwalteter, gepoolter HTTP-Client (Connection-Pooling statt Client-pro-Call)
- Modularer Aufbau: `server.py`-Monolith in 9 fokussierte Module aufgeteilt
- Strukturierter Response-Envelope (`source` / `provenance` / `match_type` / `count`) + CC-BY-Quellen-Fusszeile
- Zwei read-only **Resources** (`zh-edu://datenquellen`, `zh-edu://lizenz`) neben den 8 Tools
- Context-Injektion mit Progress-Reports und client-seitigem Logging

### Cloud & Scale
- CORS-Middleware für Browser-Clients (exponiert `Mcp-Session-Id`)
- Stateless HTTP → horizontal skalierbar ohne Sticky Sessions
- Multi-Stage-`Dockerfile` (non-root, `HEALTHCHECK`) + `docker-compose.yml` mit Resource-Limits
- `/health`-Endpoint für Load-Balancer- und Container-Probes

### Security
- Egress-Allow-List (`frozenset` + httpx-Hook), HTTPS-Zwang, Redirect-Schutz
- DNS-Auflösung + IP-Blocklist-Validierung vor jedem Egress (Anti-Rebinding, blockt Metadata-IPs)
- Strikte Input-Validierung (`strict=True`, `extra="forbid"`) auf allen Tool-Modellen
- Sanitisierte Fehler: Originalfehler nur ins stderr-Log, Client erhält generische Meldung
- Execution-Errors als `isError:true` (ToolError)
- Loopback-Default-Binding (`127.0.0.1`); `0.0.0.0` nur explizit im Container

### Observability
- Strukturiertes JSON-Logging auf stderr (`structlog`)
- Optionales OpenTelemetry-Tracing pro Tool-Call (`[otel]`-Extra, `MCP_OTEL_ENABLED`)

### Dokumentation
- Neu: `docs/deployment.md`, `docs/network-egress.md`, `docs/security.md`,
  `docs/secret-management.md`, `docs/roadmap.md`, `docs/accepted-risks.md`, `CONTRIBUTING.de.md`
- README EN+DE: korrigierter Cloud-Endpoint (`/mcp`), MCP-Protokoll-Sektion, Phase-1-Deklaration
- Dependabot für monatliche Dependency-Updates

## ⚠️ Bewusste Grenzen (kein Finding)
- **SEC-005 / Socket-Pinning:** Implementiert ist DNS-Auflösung + IP-Blocklist-Validierung.
  Echtes Socket-Level-Pinning (Connect zur exakt validierten IP) bleibt ein dokumentiertes
  Restrisiko (kleines TOCTOU-Fenster, durch Single-Host-Allow-List gering) — siehe `docs/network-egress.md`.
- **SEC-014 / SEC-015** (Tool-Allow-Listing, Tool-Poisoning-Detection) gehören auf die
  MCP-Gateway-Ebene und sind als accepted-risk dokumentiert (`docs/accepted-risks.md`).

## Keine Breaking Changes
Bestehende Tool-Namen und -Signaturen sind unverändert; der stdio-Default-Betrieb funktioniert
wie zuvor. Cloud-Betrieb wird ausschließlich explizit über ENV-Vars aktiviert.

**Full Changelog:** https://github.com/malkreide/zh-education-mcp/compare/v0.1.0...v0.2.0

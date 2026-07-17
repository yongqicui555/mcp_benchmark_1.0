# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.2.0] - 2026-05-30

Production-Hardening nach MCP-Best-Practice-Audit (Skill v1.0.0, Catalog-Hash `091f446b`).
Audit-Verifikation: **42/42 Checks bestanden · 0 Findings · production-ready** (Run `2026-05-30T072745-Z-zh-education-mcp`).

### Added
- ENV-basierte Konfiguration (`MCP_TRANSPORT`/`MCP_HOST`/`MCP_PORT`/`MCP_CORS_ORIGINS`/`MCP_STATELESS_HTTP`)
- `lifespan`-verwalteter, gepoolter HTTP-Client (Connection-Pooling)
- CORS-Middleware für HTTP-Transporte (exponiert `Mcp-Session-Id`)
- Stateless HTTP (kein Sticky-Session-Routing nötig)
- Multi-Stage-`Dockerfile` (non-root, HEALTHCHECK), `docker-compose.yml` mit Resource-Limits
- `/health`-Endpoint für Load-Balancer- und Container-Probes
- Egress-Allow-List (`frozenset` + httpx-Hook, HTTPS-Zwang, Redirect-Schutz)
- Strukturiertes JSON-Logging auf stderr (`structlog`)
- Strikte Input-Validierung (`strict=True`) auf allen Tool-Modellen
- Context-Injektion (`ctx`) mit Progress-Reports und Logging bei Tool-Calls
- Optionales OpenTelemetry-Tracing pro Tool-Call (`[otel]`-Extra, `MCP_OTEL_ENABLED`)
- DNS-Auflösung + IP-Blocklist-Validierung vor jedem Egress (Anti-Rebinding)
- Dokumentation: `docs/deployment.md`, `docs/network-egress.md`, `docs/security.md`, `docs/secret-management.md`, `docs/roadmap.md`, `docs/accepted-risks.md`, `CONTRIBUTING.de.md`
- Dependabot für monatliche Dependency-Updates

### Changed
- Fehlerbehandlung sanitisiert: Originalfehler nur ins stderr-Log, Client erhält generische Meldung
- Execution-Errors werden als `isError:true` (ToolError) statt als Erfolgs-String signalisiert
- README: Cloud-Endpoint korrigiert (`/mcp` statt `/sse`), Protokoll-/Phasen-Sektion ergänzt

### Security
- SSRF-/Egress-Härtung, Container-Sandboxing, CORS, strikte Validierung (siehe Audit-Findings W1–W3)

### Phase
- Phase 1 (read-only) bestätigt; siehe `docs/roadmap.md`

## [0.1.0] - 2026-04-01

### Added
- Initial release
- `zh_edu_list_schulgemeinden`: List all school communities and Schulkreise in Canton Zurich
- `zh_edu_schulkreis_trend`: Pupil trend by school district (anchor query: Schulkreis Letzi)
- `zh_edu_overview`: Canton-wide learner overview by school level (2000–present)
- `zh_edu_sek1_profil`: Secondary I profile per school community (Sek A/B/C breakdown)
- `zh_edu_staatsangehoerigkeiten`: Nationality structure of pupils per school community
- `zh_edu_maturitaetsquote`: Gymnasium graduation rates by municipality, district, canton
- `zh_edu_wohnort_trend`: Learner trend by place of residence (Bezirk / Gemeinde)
- `zh_edu_mittelschulen`: Secondary school statistics (Gymnasium, FMS, HMS)
- 24h in-memory cache matching annual BISTA update cycle (Stichtag 15. September)
- Dual transport: stdio (Claude Desktop) + SSE (cloud / Railway)
- Pydantic v2 input validation on all tools
- Bilingual documentation: README.md (EN) + README.de.md (DE)
- Mocked test suite with respx (6 unit tests)
- Phase 1: No-auth data sources only (BISTA public API)

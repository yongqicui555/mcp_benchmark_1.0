# Roadmap & Phasenarchitektur

Dieser Server folgt der Phasenarchitektur des Best-Practice-Katalogs (OPS-003):
Read-only zuerst, Schreibzugriffe erst nach Sicherheits-Review.

## Phase 1 — Read-only Wrapper  ✅ (aktuell)

- [x] 6 Tools, **alle** `readOnlyHint: true`
- [x] Pydantic-v2-Schemas mit Constraints + strikte numerische Validation (SEC-018)
- [x] Egress-Allow-List Code + Network-Layer (SEC-021)
- [x] Structured Logging auf stderr (OBS-003/004)
- [x] OpenTelemetry-Tracing pro Tool-Call (OBS-006)
- [x] Container-Sandboxing (Dockerfile non-root, read-only FS) (SEC-007/SCALE-004)
- [x] Audit-Lauf gegen `mcp-audit-skill` (siehe `audits/`)
- [x] Tool-Definition-Hash-Pinning (SEC-022)
- [x] Strukturierte, typisierte Tool-Returns mit Output-Schema (SDK-002)
- [x] Optionale Bearer-Auth + Session-Binding für HTTP (SEC-009, opt-in)

## Phase 2 — Semantic Layer  (geplant)

- [ ] Cross-Server-Federation mit `fedlex-mcp` / `zurich-opendata-mcp`
- [ ] Identity-Resolution (Vorstoss ↔ Urheber:in ↔ Gesetzestext)
- [ ] Optional: Resources-Primitive für statische Geschäfts-Dokumente (ARCH-008)
- [ ] weiterhin **kein** Write

**Übergang 1 → 2 erfordert:** abgeschlossener Audit (critical/high behoben),
Datenquellen-Lizenzdoku (CH-004) — beide erfüllt.

## Phase 3 — Write / Aktion  (frühestens, nur mit Auth)

- [ ] OAuth 2.1 + Resource Indicators, User-gebundenes Session-Binding (SEC-009)
- [ ] Idempotency-Keys + Compensating Actions
- [ ] MCP-Gateway mit Tool-Allow-List & Poisoning-Detection scharf (SEC-014/015)
- [ ] Stateful LB / Shared-State-Session-Store bei horizontaler Skalierung
      (SCALE-002/003 — siehe `adr/ADR-002-scaling.md`)

**Übergang 2 → 3 erfordert:** Sign-off Datenschutz + Threat-Model-Review.

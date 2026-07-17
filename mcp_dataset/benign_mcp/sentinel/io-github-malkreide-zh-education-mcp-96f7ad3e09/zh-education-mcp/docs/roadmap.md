# Roadmap & Phasenarchitektur

Der Server folgt der Phasenarchitektur *Read-only First* (Audit OPS-003).

## Phase 1 — Read-only (AKTUELL)

Nur lesende Tools gegen öffentliche BISTA-Open-Data. Alle Tools haben
`readOnlyHint: true`, `destructiveHint: false`.

- [x] 8 read-only Tools (Trends, Profile, Übersicht, Maturität, Nationalitäten, Mittelschulen)
- [x] stdio + Streamable HTTP (ENV-konfiguriert)
- [x] Security-Härtung: Egress-Allow-List, CORS, Container-Sandboxing, stateless HTTP
- [x] Strukturiertes Logging (stderr), strikte Input-Validierung

## Phase 2 — Write (nicht geplant)

Schreibende Operationen sind für diesen Statistik-Server **nicht vorgesehen**.
Voraussetzungen, falls sich das ändert:

- Audit-Run abgeschlossen, ISDS-Einstufung, DSG-Verarbeitungsverzeichnis
- HITL-Bestätigung (`ctx.elicit`) für jede schreibende Operation
- Idempotency-Keys / Compensating Actions

## Phase 3 — Multi-Source / Semantic Layer (nicht geplant)

- Semantic Layer, Identity-Resolution
- GL- + Datenschutzbeauftragte:r-Sign-off

> Phasenübergänge werden im [CHANGELOG](../CHANGELOG.md) dokumentiert.

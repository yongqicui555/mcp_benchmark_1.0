# Roadmap & Phase Model

This server follows the read-only-first phase architecture (audit finding `OPS-003`). The current phase is declared in the README and must match the actual tool annotations.

## Current phase

**Phase 1 — read-only.** Every tool is annotated `readOnlyHint: true`, `destructiveHint: false`. The server performs only HTTP GET requests against public open-data upstreams, processes no PII, and holds no persistent state.

## Phase 1 scope (done / in scope)

- 8 read-only tools across SIK-ISEA, Nationalmuseum (SNM) and Nationalbibliothek (NB)
- 2 resources, 2 prompts
- Dual transport (stdio + Streamable HTTP)
- Security controls: egress allow-list, `defusedxml`, Pydantic input validation, error masking, container hardening (see [`security.md`](security.md))

## Phase 2 — write-capable (NOT started)

Adding any write/mutating tool moves the server to Phase 2 and is **gated** on:

- [ ] Completed audit run with no open `critical`/`high` findings (see `audits/`)
- [ ] ISDS (Informationssicherheits- und Datenschutzkonzept) for the write surface
- [ ] revDSG processing record (Verarbeitungsverzeichnis) updated — see [`data-residency.md`](data-residency.md)
- [ ] Idempotency keys / compensating actions for every write tool (`ARCH-010`)
- [ ] Human-in-the-loop confirmation for destructive actions (`HITL-005`)
- [ ] Re-evaluation of the lethal-trifecta assessment in [`security.md`](security.md) (`SEC-019`)

## Phase 3 — multi-agent / semantic layer (NOT started)

Gated on Phase 2 completion plus a semantic layer, identity resolution, and management + data-protection-officer sign-off.

## Discipline

Phase transitions are recorded in [`CHANGELOG.md`](../CHANGELOG.md). A PR that adds a write tool without clearing the Phase 1 → 2 checklist above should be rejected in review.

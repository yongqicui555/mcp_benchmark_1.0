# Roadmap — `bag-epl-mcp`

Phased architecture: **read-only first**, then write, then multi-agent
(OPS-003). The current phase is declared in `epl_server_info` and the README.

## Phase 1 — Read-only access (current)

**Status:** active · all tools `readOnlyHint=true`, no write/destructive tools.

- SL website access + structured legal context (KVG/KLV/IVG/GgV, WZW criteria)
- GGSL and MiGeL information tools
- Transparency: SL pending applications (`epl_gesuchseingaenge`)
- Dual transport (stdio + Streamable HTTP), egress allow-list, structured logging

**Prerequisites already met:** input validation (Pydantic strict), security model
documented (`docs/SECURITY.md`), audit completed (`docs/audit/2026-06-01/`).

## Phase 2 — FHIR/IDMP API (planned, ~2025/2026)

Activate once the BAG publishes its FHIR/IDMP API for the ePL.

- Replace the `_sl_website_suche` fallback with real FHIR queries (`FHIR_BASE_URL`).
- Populate the response envelope `results`/`count`/`match_type` with live data.

**Transition gate (Phase 1 → 2), required sign-offs:**
- [ ] ISDS classification documented (if a non-public data class is introduced)
- [ ] DSG processing record (only if any personal data is touched — not expected)
- [ ] Re-run the mcp-audit-skill audit; address any new SEC/CH findings
- [ ] Pin/raise the supported MCP `protocolVersion` and verify SDK compatibility

## Phase 3 — Full ePL integration / multi-agent (vision, 2026/2027)

- MiGeL + Analysenliste (AL) via ePL-FHIR
- Semantic layer + identity resolution across the Swiss public-data portfolio

**Transition gate (Phase 2 → 3):**
- [ ] Semantic layer and identity-resolution design reviewed
- [ ] If write capability is ever added: idempotency keys, `destructiveHint`,
      and human-in-the-loop confirmation (currently out of scope — read-only)

## Versioning & protocol policy (ARCH-012)

- Supported MCP protocol version: **`2025-06-18`** (`PROTOCOL_VERSION` in
  `server.py`, surfaced via `epl_server_info`).
- SDK/dependency updates proposed monthly via Dependabot; review the MCP
  `protocolVersion` on every `mcp` SDK bump and note breaking changes in the
  `CHANGELOG`.

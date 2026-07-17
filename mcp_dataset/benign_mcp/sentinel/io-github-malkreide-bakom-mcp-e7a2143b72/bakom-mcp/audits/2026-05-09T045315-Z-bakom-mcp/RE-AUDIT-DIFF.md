# Re-Audit Diff — bakom-mcp

**Run 1:** 2026-05-08T044348-Z (initial audit)
**Run 2:** 2026-05-09T045315-Z (this re-audit)

## Headlines

| Metrik | Run 1 | Run 2 | Δ |
|---|---|---|---|
| Applicable | 36 | 36 | — |
| Pass | 15 | 26 | **+11** |
| Fail | 6 | 0 | **−6** ✅ |
| Partial | 13 | 8 | **−5** |
| TODO | 2 | 2 | — |
| Findings (fail+partial) | 19 | 8 | **−11** |
| Critical findings | 3 | 0 | **−3** ✅ |
| High findings | 8 | 0 | **−8** ✅ |
| Medium findings | 8 | 8 | — |
| Production-Ready | NO | **YES** ✅ | — |
| Blocking | OBS-002, SDK-001, SDK-004, SEC-007 | none | — |

## Status-Transitions per Check

### Closed in Re-Audit (11 Findings → Pass)

| ID | Severity | Run 1 | Run 2 | Remediation PR |
|---|---|---|---|---|
| ARCH-005 | critical | partial | **pass** | #13 |
| OBS-001 | high | partial | **pass** | #22 |
| OBS-002 | high | fail | **pass** | #17 |
| OBS-004 | critical | partial | **pass** | #14 |
| OPS-001 | high | partial | **pass** | #20 |
| SDK-001 | high | fail | **pass** | #18 |
| SDK-004 | high | fail | **pass** | #17 |
| SEC-005 | high | partial | **pass** | accepted-risk + #21 (Egress-Allowlist) |
| SEC-007 | high | fail | **pass** | #19 |
| SEC-016 | critical | partial | **pass** | #15 |
| SEC-021 | high | partial | **pass** | #21 |

### Carried Over (8 Findings, alle medium-partial → Phase 4 Backlog)

| ID | Severity | Status | Notiz |
|---|---|---|---|
| ARCH-003 | medium | partial | «Not Found»-Heuristiken offen |
| ARCH-008 | medium | partial | Keine `@mcp.prompt` |
| ARCH-012 | medium | partial | Kein Upper-Bound auf mcp-SDK |
| CH-004 | medium | partial | CC BY 4.0 Attribution-Footer |
| OBS-003 | medium | partial | Logger nun mit 3 Calls (war 0) — info-Logs pro Tool-Call fehlen |
| SDK-002 | medium | partial | Tool-Returns weiterhin `str` |
| SDK-003 | medium | partial | `Context` injiziert, aber `ctx.report_progress` ungenutzt |
| SEC-008 | medium | partial | README «What this does/does not» nice-to-have |

### Unchanged TODO (2 Items)

| ID | Severity | Reason |
|---|---|---|
| SCALE-002 | high | `is_cloud_deployed=false`; Mcp-Session-Id-Routing nicht relevant |
| SEC-009 | critical | `auth_model=none`; Cryptographic-Binding bei späterem Auth-Upgrade |

## Verdict

`bakom-mcp` ist nach 9 Remediation-PRs **production-ready** für die ursprünglich definierten Profile-Annahmen (`auth_model=none`, `data_class=Public Open Data`, `write_capable=false`).

Verbleibende 8 medium-Findings sind **kein Blocker für Production**, aber sinnvolle Phase-4-Verbesserungen (UX-Heuristiken, MCP-Prompts, Doku-Polishing, strukturierte Logs, Pydantic-Outputs, Progress-Reports). Diese können Sprint-für-Sprint abgearbeitet werden.

## Audit-Trail-Hinweise

- 9 Remediation-PRs (#13, #14, #15, #17, #18, #19, #20, #21, #22), alle gemerged.
- `accepted-risk` für SEC-005 dokumentiert in [Tracker-Comment #4411476485](https://github.com/malkreide/bakom-mcp/issues/8#issuecomment-4411476485).
- Keine Findings wurden hochgestuft (Severity-Eskalation); Re-Audit deckt sich mit Tracker.

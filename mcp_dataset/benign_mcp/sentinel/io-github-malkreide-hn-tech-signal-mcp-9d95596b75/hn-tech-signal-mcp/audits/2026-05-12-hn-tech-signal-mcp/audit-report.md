# MCP-Audit Report — hn-tech-signal-mcp

| Metadatum | Wert |
|---|---|
| **Server** | `hn-tech-signal-mcp` |
| **Version** | 0.1.0 (Alpha) |
| **Repository** | https://github.com/malkreide/hn-tech-signal-mcp |
| **Branch** | `claude/audit-mcp-skill-KxBMH` |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (Opus 4.7) |
| **Skill** | [mcp-audit-skill](https://github.com/malkreide/mcp-audit-skill) v0.5.0 |
| **Run-ID** | `audit-2026-05-12T00:00Z-hn-tech-signal-mcp` |

---

## Executive Summary

`hn-tech-signal-mcp` ist ein sauber strukturierter Read-Only-MCP-Server mit
guter Pydantic-Validierung und sinnvollem TTL-Cache, aber ein
**Critical-Befund (GITHUB_TOKEN-Leak an Drittanbieter)** und ein
**High-Befund (HTTP-Transport ohne Auth, ohne Bind-Restriktion)** blockieren
die Production-Readiness. Nach Fix der zwei Top-Findings ist der Server für
Stdio/Desktop-Use freigabefähig; Cloud-HTTP-Deployment erfordert zusätzlich die
mittel-priorisierten OBS/SDK-Fixes.

**Empfehlung:** **NOT production-ready** — Re-Audit nach Behebung von SEC-001
und SEC-002.

---

## Profile Snapshot

| Feld | Wert |
|---|---|
| Transport | stdio + streamable_http |
| Auth-Modell | none (öffentliche APIs); optional `GITHUB_TOKEN` für Upstream-Rate-Limit |
| Datenklasse | public_only (keine PII, keine CH-DSG-Relevanz) |
| Schreibzugriff | nein (alle Tools `readOnlyHint=True`) |
| Deployment | local_desktop + cloud_http |
| Sprache / Framework | Python ≥3.11 / `mcp.server.fastmcp` (Anthropic SDK) |
| Tools | 7 (HN×2, arXiv×2, Lobsters×1, GitHub×1, Digest×1) |
| Upstream-APIs | HN Firebase, HN Algolia, arXiv, Lobste.rs, GitHub |

---

## Applicability Matrix

| Kategorie | Im Katalog | Anwendbar | Pass | Fail |
|---|---:|---:|---:|---:|
| ARCH  | 12 | 10 |  9 | 1 |
| SDK   |  5 |  5 |  3 | 2 |
| SEC   | 23 | 14 | 10 | 4 |
| SCALE |  6 |  5 |  4 | 1 |
| OBS   |  6 |  5 |  4 | 1 |
| HITL  |  5 |  1 |  1 | 0 |
| CH    |  8 |  0 |  0 | 0 |
| OPS   |  3 |  3 |  1 | 2 |
| **Σ** | **68** | **43** | **32** | **11** |

CH-Kategorie vollständig N/A (öffentliche Drittland-Daten, keine Personendaten).

---

## Findings Overview

| ID | Titel | Severity | Effort | Status |
|---|---|---|---|---|
| [SEC-001](findings/SEC-001-token-leak.md) | GITHUB_TOKEN an HN/arXiv/Lobsters geleakt | **critical** | S | open |
| [SEC-002](findings/SEC-002-http-no-auth.md) | Streamable-HTTP ohne Auth, bindet 0.0.0.0 | **high** | M | open |
| [ARCH-001](findings/ARCH-001-wrong-dependency.md) | `fastmcp` deklariert, `mcp` importiert | medium | S | open |
| [SEC-003](findings/SEC-003-xxe.md) | Unsicheres `xml.etree`-Parsing für arXiv | medium | S | open |
| [SDK-001](findings/SDK-001-utcnow-deprecated.md) | `datetime.utcnow()` 6×, ab Py3.12 deprecated | medium | S | open |
| [OBS-001](findings/OBS-001-unused-logger.md) | Logger deklariert, nie benutzt | medium | S–M | open |
| [SEC-004](findings/SEC-004-arxiv-category-not-whitelisted.md) | `arxiv_search.category` ohne Whitelist | low | S | open |
| [SCALE-001](findings/SCALE-001-unbounded-cache.md) | In-Memory-Cache ohne Size-Cap | low | S | open |
| [OPS-001](findings/OPS-001-ci-no-lint.md) | CI ohne Lint/Coverage-Gate | low | S | open |
| [OPS-002](findings/OPS-002-no-security-policy.md) | Kein SECURITY.md / Dependabot / CODEOWNERS | low | S | open |
| [SDK-002](findings/SDK-002-fastmcp-tool-name-collision.md) | `mcp` als Variablenname schattet das Modul | low | S | open |

**Severity-Verteilung:** 1 critical, 1 high, 4 medium, 5 low.

---

## Detailed Findings

Vollständige Befunde (Observation, Evidence, Risk, Remediation-Diff, Effort,
Verification) in `findings/`:

- `findings/SEC-001-token-leak.md`
- `findings/SEC-002-http-no-auth.md`
- `findings/SEC-003-xxe.md`
- `findings/SEC-004-arxiv-category-not-whitelisted.md`
- `findings/ARCH-001-wrong-dependency.md`
- `findings/SDK-001-utcnow-deprecated.md`
- `findings/SDK-002-fastmcp-tool-name-collision.md`
- `findings/OBS-001-unused-logger.md`
- `findings/SCALE-001-unbounded-cache.md`
- `findings/OPS-001-ci-no-lint.md`
- `findings/OPS-002-no-security-policy.md`

---

## Remediation Plan

### Sprint 0 (Production-Blocker)

| # | Finding | Effort | Begründung |
|---|---|---|---|
| 1 | SEC-001 | S | Secret-Leak — sofort fixen |
| 2 | SEC-002 | M | Cloud-Deploy unsicher — bind + auth nötig vor erstem öffentlichen Deploy |

### Sprint 1 (Medium)

| # | Finding | Effort |
|---|---|---|
| 3 | ARCH-001 | S |
| 4 | SEC-003 (defusedxml) | S |
| 5 | SDK-001 (utcnow) | S |
| 6 | OBS-001 (Logging) | S–M |

### Sprint 2 (Polish)

| # | Finding | Effort |
|---|---|---|
| 7 | SEC-004 | S |
| 8 | SCALE-001 | S |
| 9 | OPS-001 (CI-Gates) | S |
| 10 | OPS-002 (Security-Policy, Dependabot) | S |
| 11 | SDK-002 (Naming) | S |

**Geschätzter Gesamt-Aufwand:** ≈ 3–4 Personentage für alle 11 Findings.

---

## Was gut ist (Hervorhebung)

- **Pydantic-Validierung durchgängig**: `extra="forbid"`, sinnvolle `ge/le`,
  `pattern`, `field_validator` für arXiv-Kategorien.
- **Tool-Annotationen vollständig**: `readOnlyHint`, `destructiveHint=False`,
  `idempotentHint=True`, `openWorldHint=True` für alle 7 Tools.
- **Async-Design korrekt**: `asyncio.gather` für parallele Upstream-Calls in
  `tech_signal_digest` und `arxiv_latest`.
- **PyPI Trusted Publisher (OIDC)** in `publish.yml` — kein Long-Lived-Token.
- **Caching mit TTL pro Kategorie** sinnvoll dimensioniert.
- **Tests trennen `live` vs. Unit** — CI deselected Network-Tests korrekt.
- **Cross-Platform-Doku** (de + en READMEs).

---

## Inapplicable Categories

- **CH (Swiss DSG/ISDS)** vollständig N/A: Der Server verarbeitet
  ausschliesslich öffentlich kuratierte Drittland-Inhalte (HN/arXiv/Lobsters/GitHub).
  Keine Personendaten im Sinne DSG Art. 5 lit. a.
- **HITL** weitgehend N/A: Alle Tools sind annotated `destructiveHint=False`,
  keine Confirm-Pfade nötig.

---

## Audit Metadata

| Feld | Wert |
|---|---|
| Skill-Version | mcp-audit-skill v0.5.0 (Single-Source: GitHub `main`) |
| Audit-Methodik | 7-Schritte-Prozess, Profile-vor-Checks |
| Checks im Katalog | 68 |
| Anwendbare Checks | 43 |
| Verifikationsmodi | Code-Review (Read), grep, statisches Pattern-Matching |
| Tools genutzt | Read, Bash (grep), WebFetch (Skill-Source) |
| Datenquelle Profil | Code-Inference (`pyproject.toml`, `server.py`, `README.md`) |
| Re-Audit empfohlen | nach Schliessung von SEC-001 + SEC-002, spätestens 2026-08-12 |

---

## Sign-Off

- [ ] Auditor: Findings reproduzierbar dokumentiert
- [ ] Maintainer (`@malkreide`): Remediation-Plan akzeptiert
- [ ] Produktions-Freigabe: **blocked** bis SEC-001 + SEC-002 closed

---

*Generiert via `mcp-audit-skill` aus https://github.com/malkreide/mcp-audit-skill,
remote-fetched während dieser Session (kein lokaler Skill-Clone vorhanden).*

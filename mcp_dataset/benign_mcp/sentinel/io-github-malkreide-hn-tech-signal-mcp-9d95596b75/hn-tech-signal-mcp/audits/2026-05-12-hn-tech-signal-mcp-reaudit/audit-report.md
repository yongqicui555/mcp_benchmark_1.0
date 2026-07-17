# MCP Re-Audit Report — hn-tech-signal-mcp

| Metadatum | Wert |
|---|---|
| **Server** | `hn-tech-signal-mcp` |
| **Audited HEAD** | `98fb4b0` (Merge PR #4) |
| **Repository** | https://github.com/malkreide/hn-tech-signal-mcp |
| **Re-Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (Opus 4.7) |
| **Skill** | [mcp-audit-skill](https://github.com/malkreide/mcp-audit-skill) v0.5.0 |
| **Run-ID** | `reaudit-2026-05-12T18:00Z-hn-tech-signal-mcp` |
| **Baseline-Audit** | `audits/2026-05-12-hn-tech-signal-mcp/` |

---

## Executive Summary

Alle 11 Findings des Baseline-Audits (1 critical, 1 high, 4 medium, 5 low) sind
durch die Sprint-PRs #2/#3/#4 geschlossen. Code-Inspektion und 30 Regressionstests
bestätigen die Fixes; CI-Gates (`ruff check`, `ruff format`, `pytest --cov-fail-under=45`)
sind aktiv. Ein neuer Low-Befund (OPS-003) wurde im Re-Audit entdeckt — kosmetisch,
nicht release-blockend.

**Empfehlung:** **production_ready = true**. Bereit für **v0.2.0-Release** gemäss
Schritt 7 des Audit-Prozesses.

---

## Profile (unverändert seit Baseline)

| Feld | Wert |
|---|---|
| Transport | stdio + streamable_http |
| Auth-Modell | none (öffentliche APIs) + optionaler `MCP_BEARER_TOKEN` für Cloud-Bind |
| Datenklasse | public_only |
| Schreibzugriff | nein |
| Tools | 7 (`@server.tool` — Variable umbenannt durch SDK-002) |

---

## Verification of Baseline Findings

| ID | Sev. | PR | Verifikation | Status |
|---|---|---:|---|---|
| **SEC-001** | critical | #2 | `_headers_for(url)` exists, `_build_headers` removed. Tests `test_github_token_only_sent_to_github` und `test_no_auth_header_without_token` grün. | **closed** |
| **SEC-002** | high | #2 | `_resolve_http_bind()` defaultet 127.0.0.1, blockt 0.0.0.0 ohne `MCP_BEARER_TOKEN`. Drei Regressionstests grün. Hinweis: in-process Bearer-Validation ist nicht implementiert (siehe Abschnitt «Defense-in-Depth»). | **closed*** |
| **ARCH-001** | medium | #3 | `pyproject.toml`: `mcp>=1.2.0` + `defusedxml>=0.7.1`; `fastmcp` entfernt. | **closed** |
| **SEC-003** | medium | #3 | `from defusedxml import ElementTree as _DefusedET`; `_DefusedET.fromstring(...)` ist die einzige Parse-Stelle. `test_xml_parser_is_defused` grün. | **closed** |
| **SDK-001** | medium | #3 | `grep -c datetime.utcnow src/` → 0. `_now_iso()`-Helper an einer Stelle, 6 Aufrufer migriert. `test_no_datetime_utcnow_in_source` grün. | **closed** |
| **OBS-001** | medium | #3 | `logger.warning` in `_handle_error`, `logger.debug` in HN-fetch-item, `logger.info` in `main()`. `logging.basicConfig` mit `LOG_LEVEL`-Env. `test_handle_error_logs_warning` grün. | **closed** |
| **SEC-004** | low | #4 | `@field_validator("category")` mit Whitelist + Empty-String-Normalisierung. Drei Regressionstests grün. | **closed** |
| **SCALE-001** | low | #4 | `_cache` ist `OrderedDict`, `_CACHE_MAX_ENTRIES = 512`, LRU-Eviction via `popitem(last=False)`. `test_cache_evicts_oldest_when_full` grün. | **closed** |
| **SDK-002** | low | #4 | `server = FastMCP(…)` ersetzt `mcp = …`, alle sieben `@server.tool` und beide Run-Calls aktualisiert. `test_server_symbol_replaces_mcp` grün. | **closed** |
| **OPS-001** | low | #4 | `ci.yml` ruft `ruff check`, `ruff format --check`, `pytest --cov-fail-under=45`. Lokal alle drei Gates grün. | **closed** |
| **OPS-002** | low | #4 | `SECURITY.md` (Vulnerability-Reporting), `.github/dependabot.yml` (pip wöchentlich + actions monatlich), `.github/CODEOWNERS`. | **closed** |

\* SEC-002 schliesst den Public-Bind-Footgun (Severity-HIGH-Risiko). Inbound-
Bearer-Validation ist ein optionaler Follow-up; das Deployment-Modell sieht
einen vorgeschalteten Reverse-Proxy vor, der TLS und Auth terminiert.

---

## New Findings

### OPS-003 (low) — CI `[dev]`-Extra existiert nicht, Fallback maskiert das

`.github/workflows/ci.yml:28-29` ruft `uv pip install -e ".[dev]" || uv pip install -e .`.
Da `pyproject.toml` kein `[project.optional-dependencies]`-Section deklariert,
schlägt der erste Befehl bei jedem Lauf still fehl. Reines Code-Smell-Issue,
kein Sicherheits- oder Korrektheits-Impact. Effort: **S**.

Details: `findings/OPS-003-ci-dev-extra-fallback.md`.

---

## Defense-in-Depth Follow-ups (Optional, kein Release-Blocker)

Diese Punkte sind keine Findings im Audit-Sinn — sie sind Hinweise für die
nächste Maintenance-Welle.

1. **Bearer-Token-Middleware** (SEC-002 Folge): aktuell verhindert der Guard
   nur, dass der Operator versehentlich auf 0.0.0.0 bindet. Echte Inbound-
   Validation muss der Reverse-Proxy übernehmen. Falls direkt-exposed gewünscht:
   FastMCP `auth=`-Parameter oder Starlette-Middleware ergänzen.
2. **Coverage 48.67 %** ist niedrig. Mit `respx` lassen sich die Tool-Bodies
   mocken. Sobald in Place, Threshold schrittweise auf 70 % anheben.
3. **`_ts_to_iso` enthält** einen redundanten `from datetime import timezone`
   (Modul-Top hat den Import schon). Pure Cosmetic.
4. **`mypy`/`pyright`** läuft nicht in CI. Bei wachsender Codebasis sinnvoll.

---

## Findings Overview (post-remediation)

| | Anzahl |
|---|---:|
| Baseline-Findings | 11 |
| Closed | **11** |
| Still open | 0 |
| Neu in Re-Audit | 1 (low) |
| Production-Blocker | **0** |

---

## Release Recommendation

`production_ready = true`. Vorgehen:

1. `src/hn_tech_signal_mcp/__init__.py` und `pyproject.toml`: Version `0.1.0` → `0.2.0`.
2. `CHANGELOG.md` `[Unreleased]` → `[0.2.0] — 2026-05-12` umstempeln.
3. Git-Tag `v0.2.0` setzen.
4. GitHub-Release publizieren → triggert `publish.yml` Trusted-Publisher-Workflow → PyPI.

OPS-003 kann **parallel oder nach** dem Release in einen kleinen Cleanup-PR.

---

## Audit Metadata

| Feld | Wert |
|---|---|
| Skill-Version | mcp-audit-skill v0.5.0 |
| Audit-Methodik | 7-Schritte-Prozess (Re-Audit-Modus) |
| Verifikationsmodi | Code-Grep, pytest, ruff |
| Tools genutzt | Bash, Read, Grep |
| Tests grün | 30 unit / 7 deselected (live) |
| Coverage | 48.67 % (≥ 45 % CI-Floor) |
| Ruff | clean (check + format) |
| Nächster Audit-Cycle | nach `v0.2.0`-Release; spätestens 2026-08-12 (90-Tage-Default) |

---

## Sign-Off

- [x] Auditor: alle 11 Baseline-Findings durch Code-Inspection und Tests verifiziert
- [ ] Maintainer (`@malkreide`): Release v0.2.0 freigegeben
- [ ] OPS-003 in Backlog / Cleanup-PR

---

*Re-Audit generiert via `mcp-audit-skill` aus
https://github.com/malkreide/mcp-audit-skill. Baseline-Audit-Findings unter
`audits/2026-05-12-hn-tech-signal-mcp/findings/` jetzt als `in-remediation`
markiert; nach Merge dieses Re-Audits können sie als `closed` umgestellt
werden (oder per Tooling automatisch aus `summary.json` synchronisiert).*

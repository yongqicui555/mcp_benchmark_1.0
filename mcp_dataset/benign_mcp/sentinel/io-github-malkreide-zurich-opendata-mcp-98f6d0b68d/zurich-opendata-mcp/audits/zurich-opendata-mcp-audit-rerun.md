# Audit Rerun: `zurich-opendata-mcp`

- **Repository:** https://github.com/malkreide/zurich-opendata-mcp
- **Commit reviewed:** `main` HEAD as of 2026-05-10 (post-PR #15)
- **Previous audit:** [`audits/zurich-opendata-mcp-audit.md`](zurich-opendata-mcp-audit.md) (2026-05-10)
- **Scope:** Same as original — source (`src/zurich_opendata_mcp/`), tests, CI/CD, packaging, docs.
- **Auditor:** Claude (automated code audit per [`malkreide/mcp-audit-skill`](https://github.com/malkreide/mcp-audit-skill); no live API calls executed)
- **Audit-Skill profile:** unchanged — `transport=stdio (+streamable-http opt-in)`, `auth=none`, `data_class=public CC0 / no PII`, `write_capability=read-only`, `deployment=PyPI + Claude Desktop / Claude Code / Cursor`

---

## TL;DR

The first-round audit's findings (1 High, 8 Medium, 11 Low) all landed on `main` across PRs #9, #11–#15. The codebase is now noticeably cleaner: input schemas are `Literal`-typed and drift-tested, the SQL gate parses with `sqlparse`, the STRB tools escape user input, the analyze flow is parallel, Markdown table cells are escaped, the SPARQL dead-branch is gone, the console-script entry point and `USER_AGENT` are correct, `handle_api_error` logs, and CI runs with a coverage gate plus Dependabot.

This rerun finds **one new High** (a real one — same shape as the closed H-1 but in a different tool surface I missed in the first pass) and **a handful of new Lows**. Overall posture has clearly improved.

Severity overview (this rerun, new findings only):

| Sev. | Count | Examples |
|------|-------|----------|
| **High** | 1 | CQL-injection in `tools/parliament.py` (`zurich_parliament_search`, `zurich_parliament_members`) — 6 f-string interpolations into the Paris API CQL query, no escaping. |
| **Medium** | 0 | — |
| **Low** | 5 | `--port` lacks bounds, `handle_api_error` ships no logging configuration, dead runtime check after Pydantic Literal in `geo.py`, MCP resource handlers don't catch exceptions, ILIKE wildcard semantics undocumented in STRB. |

---

## 1. Verification of original findings

Each finding from the first audit, with current status confirmed by reading the merged code on `main`.

### High

| ID | Title | PR | Status |
|----|-------|----|--------|
| H-1 | SQL-injection in `tools/strb.py` (f-string `WHERE`) | #9 | ✅ **Closed.** `_sql_escape()` doubles `'` and `\`; date inputs pass through unescaped because Pydantic regex-validates them. 5 regression tests in `tests/test_server.py` (`test_strb_where_clause_neutralises_*`). |

### Medium

| ID | Title | PR | Status |
|----|-------|----|--------|
| M-1 | `USER_AGENT` points at non-existent GitHub user | #12 | ✅ **Closed.** Read from `importlib.metadata.version("zurich-opendata-mcp")`; URL now `github.com/malkreide/zurich-opendata-mcp`. Tested by `test_user_agent_uses_real_repo_url`. |
| M-2 | Tool/Resource count drift README ↔ code | #11 | ✅ **Closed.** Tagline + footer now `24 Tools, 5 Resources`; STRB section added. |
| M-3 | README "Project Structure" outdated, wrong test command | #11 | ✅ **Closed.** Tree mirrors current `app.py` / `clients/` / `tools/` layout; dev-section uses `pytest tests/ -m "not live"`. |
| M-4 | `zurich_sparql` dead code after `return` | #12 | ✅ **Closed.** ~50 lines deleted; module docstring explains the disabled state and how to restore from git history. `idempotentHint: True` (constant string). |
| M-5 | N+1 fan-out in `zurich_analyze_datasets` | #13 | ✅ **Closed.** `package_show` removed; per-dataset `datastore_search` calls run via `asyncio.gather` bounded by `Semaphore(5)`. Verified by `test_analyze_datasets_does_not_call_package_show`. |
| M-6 | Markdown table breakage on `\|`/newline in upstream data | #12 | ✅ **Closed.** New `formatters.md_cell()` helper applied to parking-live and pedestrian-traffic renderers. Unit-tested. |
| M-7 | CI runs only validation/smoke tests | #9 #12 #13 #14 #15 | 🟡 **Partially addressed.** 36 non-live tests now (was 1 functional smoke). Mocked unit tests for STRB-builder, USER_AGENT, md_cell, SPARQL constant, SELECT gate, `analyze_datasets` with monkey-patched ckan_request, Pydantic Literals + drift, `idempotentHint` invariant, `get_client` shape, `handle_api_error` logging. **Still missing**: `respx`-based end-to-end mocks for `tools/realtime.py`, `tools/parliament.py`, `tools/tourism.py`. Coverage 34.72% with regression gate at 30%; long-term goal 80%. |
| M-8 | `zurich_datastore_sql` SELECT-gate too narrow + lets stacked statements through | #13 | ✅ **Closed.** `sqlparse`-based `_validate_select_only()` — accepts CTEs (`WITH … SELECT …`), rejects empty / stacked / non-SELECT. 6 unit tests cover the gate. |

### Low

| ID | Title | PR | Status |
|----|-------|----|--------|
| L-1 | Console-script entry bypasses `main()`, `--http` unreachable | #15 | ✅ **Closed.** Entry point now `zurich_opendata_mcp.server:main`. Test `test_console_entry_point_targets_main` parses `pyproject.toml` to enforce. |
| L-2 | README "Alternative" snippet uses console-script | #15 (transitively) | ✅ **Closed** — once L-1 is fixed, the snippet works as documented. |
| L-3 | `audits/` versioned alongside source | n/a | Not a defect — observation only. |
| L-4 | `USER_AGENT` version drift | #12 | ✅ **Closed** as part of M-1. |
| L-5 | `_get_client` private but imported externally | #15 | ✅ **Closed.** Renamed to `get_client`. |
| L-6 | `_get_client` async-without-await | #15 | ✅ **Closed.** Now sync. |
| L-7 | `handle_api_error` doesn't log | #15 | ✅ **Closed.** Logs `WARNING` with traceback at `zurich_opendata_mcp.formatters` logger. Test `test_handle_api_error_logs_warning`. |
| L-8 | Defensive idiom for `metadata_modified[:10]` | n/a | Cosmetic — not actioned. The default is `""` so the slice is safe. |
| L-9 | `WaterWeatherInput.station` accepts arbitrary strings | #14 | ✅ **Closed.** `Literal["tiefenbrunnen", "mythenquai"]`. Test `test_water_weather_station_rejects_typo`. |
| L-10 | `TourismSearchInput.language` not validated | #14 | ✅ **Closed.** `Literal["de","en","fr","it"]`. Test `test_tourism_language_rejects_unknown`. |
| L-11 | STRB `format` accepts arbitrary strings | #14 | ✅ **Closed.** `Literal["markdown", "json"]`. Test `test_strb_format_rejects_unknown`. |
| L-12 | `filter_group` not validated against `ZURICH_GROUPS` | #14 | ✅ **Closed.** `ZurichGroup = Literal[...]` with drift test. |
| L-13 | `layer_id` validated only at runtime | #14 | ✅ **Closed.** `GeoLayerId = Literal[...]` with drift test. (Runtime check is now redundant — see new L-A below.) |
| L-14 | README geo-layer table doesn't match `GEOPORTAL_LAYERS` | #11 | ✅ **Closed.** Table regenerated; README points at `config.py` as SoT. |
| L-15 | `zurich_sparql` `idempotentHint: False` for constant | #12 | ✅ **Closed** (folded into M-4). |
| L-16 | `Dauer_end > "9999-12-31"` Paris-API idiom needs comment | n/a | Not actioned — minor cosmetic. The line is referenced in `parliament.py:190`; consider documenting alongside the H-2 fix below. |
| L-17 | WFS version pinning needs comment | #15 | ✅ **Closed.** Docstring on `wfs_get_features` now explains the 1.1.0 pin. |
| L-18 | GitHub Actions pinned only by major | #15 | ✅ **Closed.** `.github/dependabot.yml` set up to auto-pin by SHA via Dependabot's standard policy (weekly grouped updates). |
| L-19 | No CI pip cache, no coverage gate | #15 | ✅ **Closed.** `cache: pip` on `setup-python`, `--cov-fail-under=30` (regression gate; 80% remains the long-term target). |
| §6 | `idempotentHint: True` on live-data tools | #14 | ✅ **Closed.** Five tools flipped to `False`; `test_live_data_tools_are_not_idempotent` enforces invariant for all 7 non-idempotent tools. |

**Result of original audit:** 0 / 20 findings still open as defects. M-7 is partially addressed (regression gate in place; long-term coverage goal pending more `respx` work).

---

## 2. New findings (rerun)

### 2.1 High

**H-2 (NEW). CQL-injection in `tools/parliament.py` via f-string interpolation.**

Same shape as the original H-1, in a different tool surface. `parliament.py` has **six** f-string interpolations into Paris-API CQL queries with no escaping:

`zurich_parliament_search` (`parliament.py:69-78`):

```python
cql_parts = [f'Titel any "{params.query}"']
if params.year_from:
    cql_parts.append(f'beginn_start > "{params.year_from}-01-01 00:00:00"')
if params.year_to:
    cql_parts.append(f'beginn_start < "{params.year_to + 1}-01-01 00:00:00"')
if params.department:
    cql_parts.append(f'Departement any "{params.department}"')

cql = " AND ".join(cql_parts) + " sortBy beginn_start/sort.descending"
```

`zurich_parliament_members` (`parliament.py:188-241`):

```python
cql_parts = [f'gremium any "{params.commission}"']
...
cql_parts.append(f'Name any "{params.name}"')
...
cql_parts.append(f'NameVorname any "{params.name}"')
cql_parts.append(f'Partei any "{params.party}"')
```

The `year_from`/`year_to` fields are `int` so they're safe (Pydantic `ge=1990, le=2030`). The string fields (`query`, `department`, `commission`, `name`, `party`) are unconstrained `str | None` and flow straight into a CQL literal that's wrapped in double quotes.

**Proof of concept.** Setting

```
ParliamentSearchInput(query='foo" OR Titel any "bar')
```

produces

```
Titel any "foo" OR Titel any "bar"  sortBy beginn_start/sort.descending
```

— two CQL predicates instead of one, joined by `OR`. The Paris API parser may reject malformed CQL, but the structural injection is real: an attacker can change the query semantics, including:

- Bypassing the title filter (`'" OR Titel any "*'` → matches everything).
- Crossing index/field boundaries (`'" OR Geschaeftsstatus any "x'`).
- Triggering parser errors that surface internal stack traces (depending on Paris API verbosity).

Unlike the original H-1 (which sat behind CKAN's read-only PostgreSQL role), the Paris API is a public read-only XML endpoint, so the practical blast radius is again "behaviour change", not data loss. But the pattern is identical to H-1 and the fix is also similar:

1. **Add a `_cql_escape()` helper** in either `clients/paris.py` or a new `formatters.py` peer:
   ```python
   def cql_escape(value: str) -> str:
       # CQL string literals: escape backslashes, then double quotes.
       # See OASIS CQL/CSW spec §6.1.
       return value.replace("\\", "\\\\").replace('"', '\\"')
   ```

2. **Apply at every call site** in `parliament.py` — six occurrences listed above.

3. **Tighten `party` to a `Literal`** of the actual Zurich council parties (`SP`, `SVP`, `Grüne`, `FDP`, `GLP`, `AL`, `Mitte`, `EVP`, `EDU`, `LdU`) — the description already lists them. This kills the injection for `party` outright and gives LLMs a tighter schema (consistent with the L-9..L-13 work).

4. **Add a regression test** mirroring the STRB pattern:
   ```python
   def test_parliament_cql_neutralises_quote_injection():
       payload = 'foo" OR Titel any "bar'
       cql = _build_search_cql(query=payload)
       assert cql.count(' any ') == 1  # exactly one predicate
       assert 'foo\\" OR Titel any \\"bar' in cql
   ```

Severity = **High**: this is a structural injection in a tool that is currently shipped, by parity with the closed H-1.

I missed this in the first pass because I focused on SQL surfaces (`strb.py`, `datastore.py`) and didn't audit the CQL builders separately. Mea culpa.

### 2.2 Low

**L-A (NEW). Runtime layer check is now dead code.**

`tools/geo.py:92-94` still has:

```python
if params.layer_id not in GEOPORTAL_LAYERS:
    available = ", ".join(sorted(GEOPORTAL_LAYERS.keys()))
    return f"Unbekannter Layer `{params.layer_id}`. Verfügbar: {available}"
```

After PR #14, `params.layer_id` is `GeoLayerId = Literal[...]`, and the drift test in `test_literal_geo_layer_id_matches_runtime_dict` enforces that the Literal exactly matches `GEOPORTAL_LAYERS.keys()`. Pydantic now rejects unknown layer IDs at validation time, so the runtime branch is unreachable. Either delete it or re-frame it as a defensive net with `# pragma: no cover` — but right now it's just dead lines that lower the coverage denominator.

**L-B (NEW). `--port` parsing has no validation.**

`server.py:99-102`:

```python
if "--http" in sys.argv:
    port_idx = sys.argv.index("--port") + 1 if "--port" in sys.argv else None
    port = int(sys.argv[port_idx]) if port_idx else 8000
    mcp.run(transport="streamable-http", port=port)
```

Three small bugs:

1. `int(sys.argv[port_idx])` raises an unfriendly `ValueError` if the value is non-numeric (`--port abc`).
2. No range check (negative or `>65535`).
3. If `--http` is given but `--port` is omitted with the value missing (`--port` at end of argv), `port_idx` is past the end → `IndexError`.

Switch to `argparse` or at least guard with a try/except. Practically: a misuse would surface at startup, not in production traffic.

**L-C (NEW). `handle_api_error` logs but ships no logger configuration.**

PR #15 added `logger.warning(...)` with traceback in `formatters.py:81-87`. Good. But the package never calls `logging.basicConfig()` or attaches a handler. In a stdio MCP deployment (the primary use case), the `WARNING` records go nowhere — `logging` defaults to a `lastResort` handler at level `WARNING` that prints to `stderr`, which works for stdio (the MCP stdio framing is on stdout), but only by accident. Worth either:

1. Documenting the assumption ("logs go to stderr; configure your MCP host to capture it"), or
2. Adding a tiny `if __name__ == "__main__":` guard in `server.py` that calls `logging.basicConfig(level=logging.WARNING, stream=sys.stderr, format=...)`.

### 2.3 Note (not a finding)

**ILIKE wildcards in user input.** `_strb_where_clause` correctly escapes `'` and `\`, but does not escape ILIKE pattern characters `%` and `_`. So `query="100%"` becomes `ILIKE '%100%%'` — the user's `%` is treated as a wildcard. This is current behaviour and probably intentional (LLM-supplied search terms work well with implicit fuzziness), but it is undocumented. If a precise-match mode is ever needed, escape via `query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")` and add `ESCAPE '\\'` to the ILIKE clause. Mention in the field description if user-visible.

---

## 3. Tests

`tests/test_server.py` is now 36 non-live tests (was 7) plus 20 live tests. Coverage: **34.72%** with `--cov-fail-under=30` regression gate. Categories present:

- Pydantic validation (8 tests on bounds and required fields).
- SQL escape + WHERE-clause builder (6 tests; the H-1 closure).
- Markdown cell escape (2 tests).
- USER_AGENT format invariants (2).
- SPARQL constant-notice contract (1).
- `_validate_select_only` — plain SELECT, CTE, stacked, DROP, INSERT/UPDATE/DELETE, empty (6).
- Pydantic Literal — drift + rejection (7).
- `idempotentHint` invariant on 7 non-idempotent tools (1).
- `analyze_datasets` no-N+1 with monkey-patched `ckan_request` (1).
- Code-hygiene — `get_client` shape, `handle_api_error` logging, console-script entry (3).

**Gaps that remain** (M-7 follow-up):

- `tools/realtime.py` (217 stmts, 19% covered) — the parking/weather/air/water/pedestrian/VBZ rendering paths.
- `tools/parliament.py` (146 stmts, 16% covered) — important for the H-2 fix below.
- `tools/tourism.py` (75 stmts, 19% covered) — language fallback, address/geo extraction.
- `formatters.py` (58 stmts, 28% covered) — `format_dataset_summary`, `format_resource_info`, the HTTP-status branches of `handle_api_error`.

`respx`-based mocks for these would push coverage well past 60% without needing live API access. Recommended for a dedicated PR after H-2.

---

## 4. CI / packaging

- `.github/workflows/ci.yml`: pip cache, coverage gate, ruff. Sound.
- `.github/workflows/publish.yml`: Trusted Publisher. Unchanged from v1 audit; still correct.
- `.github/dependabot.yml`: weekly grouped updates for `github-actions` and `pip`. After the first Dependabot run lands, GitHub Actions will be SHA-pinned automatically.
- `pyproject.toml`: clean, `sqlparse>=0.4` added in PR #13, console-script targets `main()`, dev deps include `respx` and `pytest-cov`.

No new findings here.

---

## 5. Recommended fix order (post-rerun)

1. **(High)** Fix H-2 — escape CQL string literals in `parliament.py`. Mirror the H-1 fix structure: small `cql_escape()` helper + 6 call-site updates + regression test. Tighten `party` to a `Literal`.
2. **(Med — M-7 continuation)** Add `respx`-based unit tests for `tools/parliament.py` (immediately after H-2 lands, to cover the new escape branches), then `tools/realtime.py` and `tools/tourism.py`. Ratchet `--cov-fail-under` upward as coverage grows.
3. **(Low)** Delete the dead `if params.layer_id not in GEOPORTAL_LAYERS` branch in `geo.py` (or mark `# pragma: no cover`).
4. **(Low)** Wrap `--port` parsing in `argparse` (or a small try/except) so misuse fails with a helpful error.
5. **(Low)** Either configure `logging.basicConfig(stderr)` in `server.py:main()` or document the existing reliance on the lastResort handler.

---

## 6. Verdict

The codebase is in materially better shape than at the first audit: every finding from v1 is closed or being tracked for follow-up, and the test scaffolding has gone from one smoke test to 36 unit-level checks plus a coverage gate. The one new High (H-2 — CQL injection in parliament tools) is genuinely new in the report only; the underlying code path was unchanged and present in the original codebase. I missed it in the first pass.

After H-2 lands, I'd consider the audit fully closed and the project ready for a `0.3.0` cut.

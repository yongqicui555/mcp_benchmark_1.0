# Audit: `zurich-opendata-mcp`

- **Repository:** https://github.com/malkreide/zurich-opendata-mcp
- **Commit reviewed:** `claude/audit-mcp-skill-6Vuon` HEAD as of 2026-05-10
- **Version:** 0.2.0 (declared in `pyproject.toml`); `[Unreleased]` block in `CHANGELOG.md` covers a large refactor of `server.py` into `tools/` + `clients/`
- **Scope:** Source (`src/zurich_opendata_mcp/`), tests, CI/CD, packaging, documentation
- **Auditor:** Claude (automated code audit per [`malkreide/mcp-audit-skill`](https://github.com/malkreide/mcp-audit-skill); no live API calls executed)
- **Audit-Skill profile:** `transport=stdio (+streamable-http opt-in)`, `auth=none`, `data_class=public CC0 / no PII`, `write_capability=read-only`, `deployment=PyPI + Claude Desktop / Claude Code / Cursor`

---

## TL;DR

`zurich-opendata-mcp` is a well-organized read-only MCP server fronting six City-of-Zurich open APIs. The recent refactor from a monolithic `server.py` into `tools/` and `clients/` packages is clean, the Pydantic input models are tight, and the threat surface is intentionally minimal (no auth, no writes, public CC0 data). The most important issue is **a real SQL-injection in the new `strb.py` tools** — title and department filters are interpolated into raw SQL via f-strings, despite a perfectly fine parameterised `datastore_search` alternative being used elsewhere in the codebase. Beyond that the findings are mostly doc-drift and code hygiene: tool/resource counts disagree between code and README, the SPARQL tool ships ~50 lines of unreachable code, and `zurich_analyze_datasets` does an N+1 fan-out against CKAN.

Severity overview:

| Sev. | Count | Examples |
|------|-------|----------|
| **Critical** | 0 | — |
| **High** | 1 | SQL-injection via f-string interpolation in `strb.py` (`query`, `departement`) |
| **Medium** | 7 | Tool/Resource count drift, README structure outdated, `zurich_sparql` dead code, N+1 in `zurich_analyze_datasets`, Markdown table breakage on user-controlled strings, USER_AGENT URL points at non-existent repo, no unit tests with mocks |
| **Low** | 11 | Version drift in `USER_AGENT`, `_get_client` is "private" but imported from four modules, no `Literal` constraints on station/language/format, README geo-layer list does not match `GEOPORTAL_LAYERS`, CI actions not pinned by SHA, no coverage gate, `filter_group` not validated, etc. |

---

## 1. Repository structure & packaging

**Strengths**

- Modern `src/`-layout, hatchling backend (`pyproject.toml:1-3`), Python 3.11–3.13 in classifiers and CI matrix.
- Refactor in the unreleased block is a real improvement: `app.py` holds the shared `FastMCP` instance, `tools/` modules register themselves via decorator side-effects on import (`server.py:24-34`), and `server.py` keeps re-exports for back-compat (`server.py:38-92`). No import cycles, no global mutation.
- Bilingual docs (`README.md` / `README.de.md`), `CHANGELOG.md` follows Keep-a-Changelog with `[Unreleased]` and dated `[0.1.0]` / `[0.2.0]` blocks.
- `.gitignore` covers `__pycache__`, dist/build, venvs, `.env`, coverage — adequate.
- Trusted-publisher PyPI workflow with `id-token: write` and `pypa/gh-action-pypi-publish@release/v1` (`.github/workflows/publish.yml:39-50`) — best practice, no long-lived tokens.
- `[project.scripts] zurich-opendata-mcp = "zurich_opendata_mcp.server:mcp.run"` (`pyproject.toml:48`) is functional but bypasses the `main()` function in `server.py:95-104` (see L-1 below).

**Issues**

- **L-1.** `[project.scripts] zurich-opendata-mcp = "zurich_opendata_mcp.server:mcp.run"` (`pyproject.toml:48`) points at the bound `mcp.run` method, which is `def run(self, transport: str = "stdio", ...)`. That works for the default stdio transport, but the `--http`/`--port` CLI flags handled in `server.py:99-102` are unreachable from the published console-script. Either change the entry point to `zurich_opendata_mcp.server:main` (the function does exist), or remove the HTTP flag from any user-facing docs that describe the console-script.
- **L-2.** `claude_desktop_config.json` references `"command": "python", "args": ["-m", "zurich_opendata_mcp.server"]`, which works because `server.py` has an `if __name__ == "__main__": main()` guard. That's fine, but the `README.md:107-115` "Alternative" snippet uses `"command": "zurich-opendata-mcp"` — see L-1; it would silently lose `--http`.
- **L-3.** `.gitignore` is fine, but `audits/` is committed (good — that's where this report goes) while `audits/bakom-mcp-audit.md` was added after the public release of v0.2.0 with no CHANGELOG note. Not a defect, just observe that audit reports are now versioned alongside source.

---

## 2. Configuration & shared infra (`config.py`, `http_client.py`, `formatters.py`, `app.py`)

The config module is a clean static-data file: endpoint URLs, layer maps, group lists, resource UUIDs.

### 2.1 Issues

- **M-1. `USER_AGENT` points to a non-existent GitHub user.**
  `config.py:14` declares `USER_AGENT = "ZurichOpenDataMCP/0.3 (MCP Server; +https://github.com/schulamt-zurich)"`. The repository is `malkreide/zurich-opendata-mcp`; `github.com/schulamt-zurich` does not exist. Two consequences: (a) upstream operators who look at access logs cannot reach the maintainer, and (b) the convention is to point at the canonical repo URL. Update to `+https://github.com/malkreide/zurich-opendata-mcp` (or the PyPI page).
- **L-4. Version drift in `USER_AGENT`.** Same line says `ZurichOpenDataMCP/0.3` while `pyproject.toml:8` is `0.2.0` and `server.py:3` advertises `v0.2.0`. Either source the version from `importlib.metadata.version("zurich-opendata-mcp")` once at import-time, or sync the constant on every release.
- **L-5. `_get_client` is module-private but imported from four modules.**
  `http_client.py:12` defines `async def _get_client()` with a leading underscore (PEP 8: "module private"). It is then imported from `clients/wfs.py:8`, `clients/sparql.py:8`, `clients/paris.py:8`. Either drop the underscore (`get_client`) or move the function next to its callers. As-is, every linter run that enables `WPS440`/`SLF001` would flag it.
- **L-6. `_get_client` is `async` but does no `await`.** The function is plain factory code (`config dict` → `httpx.AsyncClient(...)`); making it a coroutine forces every caller to `await await_client()` and adds a useless event-loop hop. Make it synchronous; the four call-sites then become `async with _get_client() as client:`.
- **L-7. `handle_api_error` does not log.**
  `formatters.py:67-81` returns a translated string for HTTP 404/403/429/timeouts, but nothing is logged. With no logger anywhere in the package, swallowed errors have no audit trail in stdio deployments. Adding `logging.getLogger(__name__).warning("…", exc_info=True)` in the catch-all branch would surface upstream API outages without changing tool output.
- **L-8.** `format_dataset_summary` (`formatters.py:20`) does `dataset.get("metadata_modified", "")[:10]` — safe because the default is `""`, but it relies on an implicit assumption that CKAN never returns `None` for that field. The neighbouring line uses the more defensive `(dataset.get("notes") or "")[:300]` pattern. Adopting the same idiom would be one fewer trap in case CKAN changes.

---

## 3. Tools

### 3.1 High-severity findings

**H-1. SQL-injection in `strb.py` via f-string interpolation.**

`tools/strb.py:15-31` builds the `WHERE` clause with raw f-strings:

```python
def _strb_where_clause(query=None, departement=None, datum_von=None, datum_bis=None) -> str:
    conditions: list[str] = []
    if query:
        conditions.append(f"\"Titel\" ILIKE '%{query}%'")
    if departement:
        conditions.append(f"\"Federfuhrendes Departement\" ILIKE '%{departement}%'")
    if datum_von:
        conditions.append(f"\"Beschlussdatum\" >= '{datum_von}'")
    if datum_bis:
        conditions.append(f"\"Beschlussdatum\" <= '{datum_bis}'")
    return " AND ".join(conditions) if conditions else "TRUE"
```

The `datum_von`/`datum_bis` Pydantic fields have a `pattern=r"^\d{4}-\d{2}-\d{2}$"` regex (`strb.py:110-115`, `228-233`), so they are safe. **`query` and `departement` are not.** A request such as

```
SearchSTRBInput(query="x%' OR 1=1 OR '%")
```

produces

```
"Titel" ILIKE '%x%' OR 1=1 OR '%%'
```

— a syntactically valid `WHERE` that returns every row in the resource. More aggressive payloads (`'; SELECT pg_sleep(30) --`, `' UNION SELECT 1,2,3,4,5 --`) reach the CKAN `datastore_search_sql` endpoint, which in turn forwards to PostgreSQL under a read-only role. The blast radius is therefore limited to (a) SELECT-style read amplification across other public DataStore resources, (b) error-based information leakage, and (c) wall-clock DoS via `pg_sleep` / Cartesian products. **It does not give write access** because CKAN's `datastore_search_sql` server-side rejects non-`SELECT` statements at the role level.

That said, the audit-skill rule is *"validate at boundaries"*: the input boundary is the MCP tool call, and a tool that constructs raw SQL from LLM-supplied strings is a textbook injection regardless of how restricted the back-end role happens to be. The fix is also cheap — every other STRB code path already has the right primitive: `ckan_request("datastore_search", {"resource_id": …, "filters": {…}, "q": …})` (used at `strb.py:350-357` for the single-record lookup). Replace `_strb_where_clause` + `_strb_query` with `datastore_search` calls that pass `q=query` and `filters={"Federfuhrendes Departement": ...}`, and keep raw SQL only for the count query (where the `WHERE` clause is already validated). If raw SQL must stay (e.g. to support `datum_von`/`datum_bis` ranges that `filters=` cannot express), escape via `query.replace("'", "''").replace("\\", "\\\\")` *and* whitelist `query`/`departement` to a safe character class — the current code does neither.

Recommended priority: fix before the next release. Add a regression test that asserts `query="x' OR '1'='1"` returns the same count as a literal-only search.

### 3.2 Medium-severity findings

**M-2. Tool count drift between code and README.**

Counting `@mcp.tool` decorators across `tools/`:

| Module | Tools |
|--------|------:|
| `catalog.py` | 7 (`zurich_search_datasets`, `zurich_get_dataset`, `zurich_list_categories`, `zurich_list_tags`, `zurich_analyze_datasets`, `zurich_catalog_stats`, `zurich_find_school_data`) |
| `datastore.py` | 2 (`zurich_datastore_query`, `zurich_datastore_sql`) |
| `realtime.py` | 6 (`zurich_parking_live`, `zurich_weather_live`, `zurich_air_quality`, `zurich_water_weather`, `zurich_pedestrian_traffic`, `zurich_vbz_passengers`) |
| `geo.py` | 2 (`zurich_geo_layers`, `zurich_geo_features`) |
| `parliament.py` | 2 (`zurich_parliament_search`, `zurich_parliament_members`) |
| `tourism.py` | 1 (`zurich_tourism`) |
| `sparql.py` | 1 (`zurich_sparql`, but see M-4 below) |
| `strb.py` | 3 (`search_stadtratsbeschluesse`, `get_beschluesse_by_departement`, `get_stadtratsbeschluss_detail`) |
| **Total** | **24** |

`README.md:5,16,274` and several inline taglines say "20 Tools, 6 Resources, 6 APIs". The actual numbers are **24 tools and 5 resources** (resources counted from `tools/resources.py`: `zurich://dataset/{name}`, `zurich://category/{group_id}`, `zurich://parking`, `zurich://geo/{layer_id}`, `zurich://tourism/categories`). LLM clients use the README-quoted taglines to set expectations, and the STRB tools (added after the v0.2.0 release based on the `[Unreleased]` block in `CHANGELOG.md`) are not listed in any of the feature sections of the README. Update the badge text, the prose ("20 Tools" → "24"), and add a §"Stadtratsbeschlüsse (STRB)" section with the three new tools and the `35c97bec-…` resource ID.

**M-3. README "Project Structure" section is outdated.**

`README.md:222-238` still describes the pre-refactor layout:

```
├── src/zurich_opendata_mcp/
│   ├── __init__.py          # Package
│   ├── server.py            # MCP Server with 20 tools & 6 resources
│   └── api_client.py        # HTTP client for 6 APIs
├── tests/
│   └── test_integration.py  # 20 integration tests
```

The `[Unreleased]` block in `CHANGELOG.md` already documents the move to `app.py`, `config.py`, `http_client.py`, `formatters.py`, `clients/{wfs,paris,tourism,sparql}.py`, `tools/{catalog,datastore,realtime,geo,parliament,tourism,sparql,strb,resources}.py`. The README needs to follow. Same goes for `README.md:247` which says `python tests/test_integration.py` — the file is `tests/test_server.py`, and tests should be run as `pytest tests/ -m live`, not as a script (the file has no `if __name__ == "__main__":` runner).

**M-4. `zurich_sparql` ships ~50 lines of unreachable dead code.**

`tools/sparql.py:41-58` is a "the endpoint is not productive" notice that returns immediately:

```python
async def zurich_sparql(params: SparqlQueryInput) -> str:
    return (
        "⚠️ **SPARQL-Endpunkt nicht produktiv**\n\n"
        ...
    )
    # ── Original-Implementation (deaktiviert bis Endpunkt produktiv) ──
    try:
        ...
```

Lines 59-105 are unreachable. Also: the docstring accurately warns about the disabled state, but the tool annotation is `idempotentHint: False` (`sparql.py:37`) — wrong, since the function is now a constant string. And the input model still validates `min_length=10, max_length=5000` — pure ceremony. Either:

1. Delete the dead branch (preferred — version control retains it).
2. Gate it behind an env var (`if os.getenv("ZURICH_SPARQL_LIVE"): …`) and surface that in the docstring.
3. Remove the tool entirely until the endpoint is productive and ship without it.

**M-5. `zurich_analyze_datasets` is N+1 against CKAN.**

`tools/catalog.py:294-372` does one `package_search` call, then for **each** of `max_datasets` (≤20) hits it issues:

- `package_show` (line 323) to enrich resources, **even though `package_search` already returns `resources` in each entry** — the enrichment step duplicates data that's almost always already present.
- A second `datastore_search` (line 352) to fetch field info.

Worst case: `max_datasets=20` triggers up to 41 sequential CKAN requests for a single tool call. That fans out to upstream load (CKAN does not document a rate limit, but Solr-backed package_search is the most expensive endpoint). Recommend:

- Use the `resources` returned by `package_search` directly; only call `package_show` if that field is empty.
- Run the per-dataset `datastore_search` calls with `asyncio.gather` and a small semaphore to bound concurrency.
- Lower the default `max_datasets` from 5 to e.g. 3 for the LLM-facing path.

**M-6. Markdown tables break on `|` and newlines in user-controlled strings.**

Several tools render upstream data straight into Markdown table cells:

- `tools/realtime.py:64` — parking-lot `name` from ParkenDD (line 58: `name = lot.get("name", "?")`).
- `tools/realtime.py:413` — pedestrian `weather_condition` and `location_name` from the hystreet DataStore.

A `|` or embedded newline in any of those values shifts table columns and corrupts the response. The fix is one line:

```python
def _md_cell(s: object) -> str:
    return str(s).replace("|", "\\|").replace("\n", " ").replace("\r", "")
```

— apply at every `f"| ... |"` line that includes external data. Today that's the parking-live and pedestrian-traffic tables.

**M-7. CI runs only validation/smoke tests; everything else is live-only.**

`pyproject.toml:62-65` registers the `live` marker correctly, and `.github/workflows/ci.yml:30` runs `pytest -m "not live"`. But of the 21 tests in `tests/test_server.py`, **20 are decorated `@pytest.mark.live`** — only one smoke test (`test_server_module_exposes_mcp_instance`, line 53) and ~5 Pydantic validation tests run in CI. Practical effect:

- Every refactor (e.g. the `server.py` → `tools/`+`clients/` split documented in `[Unreleased]`) is shipped without any unit-level coverage of the tool logic.
- Bugs that depend on input transformation (the SQL-injection in H-1; the JSON-filter parsing in `tools/datastore.py:65-74`; the language-fallback chain in `tools/tourism.py:97-119`) cannot be caught locally.

The tool logic is straightforwardly mockable with `respx` (already a dev dependency, `pyproject.toml:42`). Concrete recommendation: write unit tests for at minimum (a) the STRB SQL builder once it is parameterised, (b) the JSON-filter validation in `zurich_datastore_query`, (c) the SQL-statement gate in `zurich_datastore_sql:146` (it currently lets `select…` lowercase pass but not e.g. `WITH x AS (SELECT …) SELECT …` — a CTE is a valid SELECT but starts with `WITH`).

**M-8. `zurich_datastore_sql` SELECT-only gate is too narrow.**

`tools/datastore.py:146-150` bounces anything that doesn't start with `SELECT`:

```python
if not params.sql.strip().upper().startswith("SELECT"):
    return "Fehler: Nur SELECT-Abfragen sind erlaubt. ..."
```

Two issues: (1) a legitimate read-only CTE query starting with `WITH …` is rejected; (2) a malicious `SELECT 1; DROP TABLE …` slips through (because the gate only checks the first token). The CKAN datastore endpoint enforces read-only at the role level so the second case fails server-side anyway, but as a *client-side* guard the check is mis-shaped. Either drop it (rely on the back-end) and document that, or replace it with a proper sqlparse-based check that splits statements and verifies each is `SELECT`/`WITH`.

### 3.3 Low-severity findings

- **L-9.** `tools/realtime.py:286-287` — `WaterWeatherInput.station: str` accepts arbitrary strings and silently maps anything not containing `"tiefen"` to Mythenquai (`realtime.py:310`). A typo like `station="Tienfenbrunnen"` returns Mythenquai data. Use `station: Literal["tiefenbrunnen", "mythenquai"]` and let Pydantic reject typos.
- **L-10.** `tools/tourism.py:31-34` — `language: str = "de"` likewise unconstrained. `language="zh"` returns mostly empty fields because `name.get("zh", "")` falls back to empty. Tighten to `Literal["de","en","fr","it"]`.
- **L-11.** `tools/strb.py:124-126` and `:241-244` — `format: str | None = "markdown"` accepts anything; non-`"json"` is silently treated as Markdown (`strb.py:183` checks `params.format == "json"` only). Use `Literal["markdown","json"]` and remove the `| None`.
- **L-12.** `tools/catalog.py:31-33` — `filter_group` is described in the docstring as "Verfügbar: arbeit-und-erwerb, basiskarten, …" (the contents of `ZURICH_GROUPS`), but the value is not validated against the list at runtime. Passing `filter_group="schule"` silently returns 0 results (CKAN treats it as a filter on a non-existent group). Either restrict via `Literal[...]` (preferred — keeps `ZURICH_GROUPS` as the single source of truth) or validate explicitly and return a friendly error listing the legal values.
- **L-13.** `tools/geo.py:53` — `layer_id` is described as "Layer-ID. Verfügbar: …" but again only validated at runtime in `:92-94`. Same recommendation as L-12; the layer set is small and stable.
- **L-14.** README "📍 Available Geo Layers" table (`README.md:204-219`) does not match `GEOPORTAL_LAYERS` in `config.py:39-54`:
  - README lists `schulwege` ("School routes and safe paths"); config maps it to `Schulweguebergaenge / poi_schulweg_att` ("Schulweg-Übergänge und Gefahrenstellen"). Different concept.
  - README lists `quartiere`, `sportanlagen`, `veloparkierung`, `lehrpfade`, `familienberatung`, `kreisbuero`, `sammelstelle`, `zweiradparkierung`. Config has `lehrpfade`, `familienberatung`, `kreisbuero`, `sammelstelle`, `sport`, `velopruefstrecken`, plus `stimmlokale`, `sozialzentrum` that the README does not mention.
  - No `quartiere`, `sportanlagen`, `veloparkierung`, `zweiradparkierung` in code.
  Net effect: ~7 of 14 README entries are mis-named or missing. Generate the table from `GEOPORTAL_LAYERS` at doc-build time, or at minimum sync once.
- **L-15.** `tools/sparql.py:37` — `idempotentHint: False` for a function that returns a constant string. Should be `True`.
- **L-16.** `tools/parliament.py:191` — `cql_parts.append('Dauer_end > "9999-12-31 00:00:00"')` is a Paris-API idiom for "no end date set". Document it inline — without context this looks like a typo for "active before year 9999".
- **L-17.** `clients/wfs.py:23` uses `version=1.1.0` (matches the typename casing). Stadt Zürich's WFS also serves 2.0.0; not a defect, but the WFS server in `2.0.0` rejects `typename` (parameter is `typenames` plural). Pin once.
- **L-18.** `.github/workflows/ci.yml:17,20` — third-party actions are pinned only by major (`@v5`, `@v6`). For supply-chain hardening the GitHub-recommended posture is to pin by commit SHA (`actions/checkout@<sha>`). Same for `publish.yml:13,16,27,43`. Defensible default for a public package.
- **L-19.** `.github/workflows/ci.yml` does not cache `pip` (cf. `actions/setup-python@v6` `cache: pip` flag) and does not gate on coverage. Once unit tests with mocks exist (M-7), add `pytest --cov=src --cov-fail-under=70` or similar.

---

## 4. Tests

`tests/test_server.py` is short, well-organised, and uses `pytest.mark.live` correctly. Issues:

- **(see M-7)** the `live` partition is so dominant that CI is effectively a "does the package import" gate.
- `test_search_datasets_input_rejects_out_of_range_rows` (line 222-226) tests `rows=100` is rejected; the limit is `le=50` (catalog.py:25). Good.
- `test_get_dataset_input_strips_whitespace` (line 229-231) verifies `model_config = ConfigDict(str_strip_whitespace=True)` — small but valuable.
- No tests for any of the three STRB tools or for the `zurich_sparql` deactivated state. Both are recent additions.
- `tests/test_server.py:11-48` imports symbols re-exported by `server.py`; the re-exports exist for back-compat but the test could equally well import from `zurich_opendata_mcp.tools.catalog` etc. directly. Lower priority.

---

## 5. CI/CD

- `ci.yml` — Python 3.11/3.12/3.13 matrix, `pip install -e ".[dev]"`, then `pytest -m "not live"` and `ruff check`. Sound shape; see M-7 / L-18 / L-19.
- `publish.yml` — Trusted Publisher (OIDC) workflow: builds with `python -m build`, uploads as artifact, downloads in a separate job that has `id-token: write`, publishes via `pypa/gh-action-pypi-publish@release/v1`. This is the correct pattern.
  - Suggestion: add a TestPyPI publish on release-candidate tags (e.g. `v0.3.0rc1`) so failures land in TestPyPI before the real release.
- Neither workflow runs the live test suite. Given the upstream APIs are public, an *opt-in* nightly schedule (`workflow_dispatch` + `schedule:`) that runs `pytest -m live` would catch upstream schema changes (e.g. CKAN resource UUIDs being rotated) without burdening every PR. Cheap to add.

---

## 6. Security & data handling

- All data is OGD/CC0; no secrets, no auth tokens. Threat surface is intentionally minimal.
- **H-1 above** is the one real vulnerability (SQL-injection bounded by CKAN's read-only role).
- `httpx.AsyncClient` is constructed with `timeout=30.0`, custom `User-Agent`, and `follow_redirects=True` (`http_client.py:14-18`). No proxy bypass, no `verify=False` — defaults are correct for OGD endpoints over HTTPS.
- `formatters.handle_api_error` returns translated, fixed-form strings for the common HTTP codes; the catch-all branch returns `f"{prefix}{type(e).__name__}: {e}"` — which can include the raw httpx error message. For `httpx.ConnectError` that includes the upstream hostname/IP, which is fine here (all endpoints are public), but for any future endpoint that resolves to an internal host it would leak that host. Worth a comment.
- No file-system writes, no shell-out, no `eval`.
- All tools have `readOnlyHint: True` and `destructiveHint: False` (correct).
- **`idempotentHint`** is set inconsistently:
  - Tools that return live data with timestamps (`zurich_parking_live`, `zurich_datastore_sql`) are correctly marked `idempotentHint: False`.
  - `zurich_weather_live`, `zurich_air_quality`, `zurich_water_weather`, `zurich_pedestrian_traffic`, `zurich_vbz_passengers` are marked `idempotentHint: True` despite returning timestamps that change on every call. By the MCP definition (same input → same output), these are *not* idempotent. Mark them all `False`, or document why a probabilistic-stale read is acceptable here. (This is a Low finding — it doesn't change tool behaviour, only client caching/replay heuristics.)

---

## 7. Documentation

- READMEs are clear, well-structured, bilingual.
- **(M-2, M-3, L-14)** — taglines, project-structure block, and geo-layer table need a sweep against the post-refactor reality.
- `CHANGELOG.md` follows Keep-a-Changelog. The `[Unreleased]` block is healthy. When the STRB work + this audit's fixes ship, cut a `0.3.0` and move the block.
- `CONTRIBUTING.md` was not in scope for this audit but is referenced from the README; verify that any commands documented there still match the post-refactor module layout.

---

## 8. Recommended fix order

1. **(High)** Replace raw SQL in `tools/strb.py` with `datastore_search` + `filters`/`q`. Add a regression test that asserts injection-style payloads return the same row count as a literal-only search. (H-1)
2. **(Med)** Sync `README.md` with reality: tool count (24), resource count (5), project-structure tree, test invocation (`pytest`), and the STRB section. Regenerate the geo-layer table from `GEOPORTAL_LAYERS`. (M-2, M-3, L-14)
3. **(Med)** Decide on `zurich_sparql`: delete the dead branch, gate it behind an env var, or remove the tool until productive. Fix the `idempotentHint` either way. (M-4, L-15)
4. **(Med)** Add unit tests with `respx` for the STRB SQL builder, the `datastore_query` JSON-filter validation, and the SELECT-gate in `zurich_datastore_sql`. (M-7, M-8)
5. **(Med)** Reduce CKAN fan-out in `zurich_analyze_datasets` and escape Markdown table cells in parking/pedestrian renderers. (M-5, M-6)
6. **(Med)** Update `USER_AGENT` to the real repo URL and source the version from `importlib.metadata`. (M-1, L-4)
7. **(Low)** Tighten Pydantic input types (`Literal` for station/language/format/filter_group/layer_id), drop the `_get_client` underscore or stop importing it externally, sync `idempotentHint` for live-data tools, pin GitHub Actions by SHA, add CI cache and a coverage gate, add an opt-in nightly live-test workflow. (L-5 through L-19)

---

## 9. Verdict

The code base is healthy and the refactor in `[Unreleased]` was the right move — the new module layout is small, decoupled, and easy to extend. **One real bug needs to land before the next release: the SQL-injection in `strb.py` (H-1).** Everything else is presentation, hygiene, and testability. With H-1 fixed and items 2–4 above shipped, this server is in good shape for a `0.3.0` cut.

The CKAN/ParkenDD/WFS/Paris/ZT integrations themselves are simple GETs with appropriate timeouts and no auth surface — no security-critical findings outside H-1.

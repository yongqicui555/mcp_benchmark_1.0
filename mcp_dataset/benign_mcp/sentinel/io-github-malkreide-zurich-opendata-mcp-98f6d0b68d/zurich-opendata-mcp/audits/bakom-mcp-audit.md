# Audit: `bakom-mcp`

- **Repository:** https://github.com/malkreide/bakom-mcp
- **Commit reviewed:** `main` HEAD as of 2026-05-08
- **Version:** 1.0.0 (released 2026-03-13)
- **Scope:** Source (`src/bakom_mcp/`), tests, CI/CD, packaging, documentation
- **Auditor:** Claude (automated code audit, no live API calls executed)

---

## TL;DR

`bakom-mcp` is a clean, well-packaged MCP server in Python with sensible structure, bilingual docs, and a working CI/PyPI pipeline. The project surface is solid, but the **core data-access logic contains layer-ID inconsistencies that almost certainly break the three most prominent coverage tools** (broadband, mobile, fibre). Several bugs (mutable shared state in `bakom_aktuell`, schema/code mismatches, an undocumented missing tool) would surface as soon as the live tests are actually executed against geo.admin.ch. The test suite is large but heavily duplicated and not properly integrated with `pytest` markers.

Severity overview:

| Sev. | Count | Examples |
|------|-------|----------|
| **High** | 4 | Wrong WMS layer IDs (broadband/mobile/fibre); shared-state bug in `bakom_aktuell` |
| **Medium** | 7 | Tool count mismatch, missing tool, schema mismatches, manual coord validation, import in hot loop |
| **Low** | 9 | Unused constants/logger, redundant test files, future-dated static content, docstring drift |

---

## 1. Repository structure & packaging

**Strengths**

- Modern `src/`-layout with `py.typed` marker and `hatchling` backend (`pyproject.toml:1-57`).
- Python 3.11–3.13 declared and tested in CI matrix.
- Dependencies are minimal and modern (`mcp[cli]>=1.3.0`, `httpx>=0.27`, `pydantic>=2.7`).
- Bilingual `README.md` / `README.de.md`, plus `CHANGELOG.md`, `CONTRIBUTING.md`, `LICENSE` (MIT), `EXAMPLES.md`.
- Distinct `[project.optional-dependencies] dev` group.
- Trusted-publisher PyPI workflow with `id-token: write` (no long-lived tokens) — best practice.
- `bakom-mcp` console-script entry point; supports both `stdio` and `streamable-http` transports.

**Issues**

- **L-1.** `[project.scripts] bakom-mcp = "bakom_mcp.server:mcp.run"` (`pyproject.toml:49`) points to a *bound method*. This will run with `transport="stdio"`, but it bypasses the `__main__` block in `server.py`, so the `--http` CLI flag is unreachable from the published console script. Either drop `--http` from documentation as console-script behaviour, or add a real `main()` that parses `argv`.
- **L-2.** Author email in `pyproject.toml:13` is a Stadt-Zürich municipal address. Consider using a project mailbox or alias to avoid coupling personal/institutional identity with PyPI metadata.
- **L-3.** `.gitignore` covers Python and editor artefacts but not `.env`, `*.local`, or coverage reports — minor.

---

## 2. Server logic (`src/bakom_mcp/server.py`)

The file is one 1755-line module. Splitting models, helpers, and tools into submodules would help future maintainers, but is not required at this size.

### 2.1 High-severity bugs

**H-1. WMS layer IDs do not match the catalogue (broken broadband coverage).**
`bakom_broadband_coverage` (line 446–453) maps speeds to:

```python
speed_to_layer = {
    "30":  "ch.bakom.downlink30",
    "100": "ch.bakom.downlink100",
    ...
}
```

but the same project's own catalogue (`bakom_breitbandatlas_datensaetze`, lines 1565–1597) lists the canonical IDs as `ch.bakom.verfuegbarkeit-einzelner-technologien_30 … _1000`. The `ch.bakom.downlink*` IDs do not appear anywhere on geo.admin.ch's known layer list. Result: every call to `bakom_broadband_coverage` will likely receive an empty/error WMS response, which `_wms_abgedeckt` swallows as `False` (line 327–329), so the tool will report **"not covered" for every Swiss address**. Recommend:

1. Replace the hard-coded map with the catalogue layer IDs.
2. Make `_wms_abgedeckt` distinguish *"layer returned no features"* from *"layer does not exist / HTTP error"* (currently both → `False`).

**H-2. Mobile-coverage tool also uses wrong layer prefix.**
`bakom_mobilfunk_abdeckung` (line 717–722) uses `ch.bakom.mobilnetz-{5g,4g,3g}`, while the constants block (line 49–51) and the catalogue (line 1544/1551/1558) use `ch.bakom.netzabdeckung-{5g,4g,3g}`. `bakom_multi_standort_konnektivitaet` (line 621) uses yet another variant. Same outcome as H-1: silently returns "not covered".

**H-3. Fibre tool layer ID inconsistent with its own catalogue.**
`bakom_glasfaser_verfuegbarkeit` (line 522) queries `ch.bakom.anschlussart-glasfaser`, while the catalogue and module constant use `ch.bakom.anschlussart-verfuegbarkeit` (line 1600, 51). One of these is wrong; based on BAKOM's published layer list the catalogue value is the canonical one.

> Combined effect of H-1/2/3: the three "anchor demo" coverage tools advertised at the top of the README are almost certainly non-functional in production. Add at least one *negative* test (a Zurich downtown address that *must* return `5G covered = True`) to the live-test matrix to catch regressions.

**H-4. `bakom_aktuell` mutates static module state.**
Lines 1269–1320 define a constant dict `highlights_db`. After the static lookup, the code does:

```python
highlights = highlights_db.get(matched_key or "medien", [])
...
for ds in datasets:
    highlights.append(...)            # appends INTO highlights_db["medien"], etc.
```

Each invocation grows the shared list, so the second call returns first-call's opendata.swiss enrichments plus its own. Over time `bakom://info` and `bakom_aktuell` outputs become unbounded. Fix: `highlights = list(highlights_db.get(...))` or build a fresh list.

### 2.2 Medium-severity issues

**M-1. Tool count mismatch.** Module docstring (`__init__.py` and `server.py:8-11`) and `README.md:120` state "12 tools in 4 categories". Actually `@mcp.tool` is declared 11 times. The README also lists `bakom_check_api_status` (README:152) which is **not implemented anywhere**. Either implement it (a simple HEAD-check across the three upstream APIs) or remove the row.

**M-2. Documented schemas don't match actual returns.** Several tool docstrings advertise rich schemas that the implementation never produces:

| Tool | Doc claims | Actual return |
|------|------------|---------------|
| `bakom_broadband_coverage` | `abdeckung_prozent`, `glasfaser_verfuegbar`, `technologien` | only `abgedeckt: bool` + metadata |
| `bakom_glasfaser_verfuegbarkeit` | `fttb_verfuegbar`, `ftth_verfuegbar`, `anbieter_anzahl` | only `glasfaser_verfuegbar: bool` |
| `bakom_mobilfunk_abdeckung` | `anbieter_anzahl: int` | not present |

LLM clients use docstrings to plan tool calls; mis-described return shapes degrade tool selection and can produce hallucinated downstream reasoning. Either implement the richer parsing (the geo.admin.ch `identify` response has per-operator features for mobile coverage) or trim the docstrings to match the code.

**M-3. Single `TelekomStatInput` model used across tools with conflicting allowed values.** The `thema` field's description (`server.py:222`) lists `'breitband','mobilfunk','festnetz','marktanteile','haushaltszugang'`, but `bakom_aktuell` matches `'5g','ki','medien','post'` and `bakom_medienstruktur_info` expects `'radio','tv','online','print'`. LLMs will pick the wrong vocabulary. Split into one Pydantic model per tool or move the allowed-values list into each tool's docstring.

**M-4. Manual coordinate validation in `bakom_multi_standort_konnektivitaet`.** Lines 600–617 hand-roll bounds checks on `loc.get("latitude", 0)` instead of relying on Pydantic. Missing keys silently default to `0` and pass through validators; malformed list entries (e.g. `{"name": "x"}`) are not rejected. Define a nested `LocationItem(BaseModel)` with the same WGS84 ranges and use `list[LocationItem]`.

**M-5. `import math` inside a hot loop.** `bakom_sendeanlagen_suche` line 833–838 imports `math` per result. Move to module top-level.

**M-6. CI test command runs all tests against live APIs.** `.github/workflows/ci.yml:42` invokes `pytest tests/ -m "not live"`, but no test in any of the four test files is marked `@pytest.mark.live`. Every "test" hits geo.admin.ch / opendata.swiss / rtvdb.ofcomnet.ch directly via the real tool functions. The CI matrix will therefore (a) consume upstream-API quota on every PR push, and (b) be flaky whenever one of those services is degraded. Either:

- Add `@pytest.mark.live` to the existing tests and write proper unit tests with `respx` / `httpx.MockTransport`, **or**
- Rename the CI step to "live integration" and accept the flakiness.

The `CONTRIBUTING.md:103-119` already promises this split — the implementation just hasn't followed.

**M-7. `_wms_abgedeckt` swallows all exceptions.** Lines 323–329 collapse `non-200`, JSON-decode error, and "no features" into the same `False`. This is the mechanism that hides H-1/H-2/H-3 from users. At minimum, log the failure (`logger` is defined but never used — see L-4 below).

### 2.3 Low-severity issues

- **L-4.** `logger = logging.getLogger("bakom_mcp")` is created at line 29 and never called. Either remove or instrument the helpers (`_geo_identify`, `_wms_abgedeckt`, `_handle_api_error`).
- **L-5.** Module-level constants `GEO_ADMIN_IDENTIFY`, `GEO_ADMIN_FIND`, `BAKOM_INFOMAILING`, `LAYER_BROADBAND_5G/4G`, `LAYER_BROADBAND_FESTNETZ`, `DEFAULT_LIMIT`, `MAX_LIMIT` are defined and never referenced. Delete or use them (preferable for the layer IDs — see H-1/2/3 fix).
- **L-6.** `bakom_aktuell` annotation `idempotentHint: False` (line 1242) differs from every other tool in the file. If it is intentional (because of opendata.swiss enrichment), document why; otherwise align with the rest.
- **L-7.** `bakom_aktuell.highlights_db` contains future-dated entries (`KI-Gipfel 2027`, `Vergabe der Mobilfunkfrequenzen 2029`). For deterministic LLM use this is fine, but ship a `last_updated` field so callers can decide how stale the static block is.
- **L-8.** Markdown emitted by tools interpolates user-supplied strings (e.g. `loc["name"]`, RTV `name`, `betreiber`) directly into Markdown table cells. A `|` or newline in user input breaks the table. Cheap fix: `s.replace("|", "/").replace("\n", " ")` before formatting.
- **L-9.** `BroadbandSpeed` is a `StrEnum` with values `"30"`, `"100"`, …; the call sites use `int(params.min_speed_mbps.value)` and string keys interchangeably. Works, but using a plain `Literal[30,100,300,500,1000]` would be cleaner and removes the `int(... .value)` dance.
- **L-10.** `_wgs84_to_lv95_approx` and the `_geo_identify` reframe call coexist: most tools use the local approximation while `_geo_identify` (which is itself unused) calls the official reframe API. Pick one path. The approximation is documented as ±1m horizontal, which is fine for a 250×250m raster but not advertised in the docstrings.
- **L-11.** No `pytest.ini` `markers` registration → `pytest -m "not live"` emits `PytestUnknownMarkWarning`.
- **L-12.** Status badge `![CI](.../ci.yml/badge.svg)` in `README.md:10` does not pin a branch. If `develop` ever differs from `main`, the badge will mislead viewers.

---

## 3. Test suite

`tests/` contains four files totalling ~2,300 lines:

| File | Lines | Purpose |
|------|-------|---------|
| `test_integration.py` | 405 | 18 named scenarios, custom `TestResult` |
| `test_20_szenarien.py` | 591 | "20 scenarios", custom runner |
| `test_20_neue_szenarien.py` | 641 | "20 new scenarios", custom runner |
| `test_scenarios_20.py` | 686 | "20 extended scenarios", custom runner |

**Issues**

- **M-8.** All four files use a hand-rolled `TestResult.ok/fail` pattern with `try/except` around each scenario instead of `assert`. A failed assertion is reported as "ok – passed" if the wrapping `try` doesn't raise. This means a regression that returns `"Fehler: …"` from `_handle_api_error` (e.g. when a layer 404s) will be counted as a *passing* test because the function still returns a non-empty string. Two of the high-severity bugs above (H-1/2/3) survive precisely because the tests only assert "is `str`, length > 30".
- **M-9.** Three of the four files are near-duplicates ("20 Szenarien", "20 neue Szenarien", "Scenarios 20"). Pick one canonical structure (recommend `pytest`-native parametrised tests) and delete the rest.
- **L-13.** `sys.path.insert` at file top (line 21–23 in each test file) is a workaround for a missing `conftest.py`. Add `conftest.py` with `pythonpath = ["src"]` or rely on the editable install.

---

## 4. CI/CD

- `.github/workflows/ci.yml` is sound: matrix testing, ruff lint, syntax-compile, import-test, pytest. Suggestions:
  - Cache `pip` / `uv` to speed up matrix builds.
  - Add a `coverage` job (e.g. `pytest --cov=bakom_mcp --cov-fail-under=80`) — once unit tests with mocks exist (M-6).
  - Pin third-party actions by SHA, not just by `@v5/@v4`, to mitigate supply-chain risk (this is a low-volume package, but a defensible default).
- `.github/workflows/publish.yml` uses Trusted Publisher (`id-token: write`) with the official `pypa/gh-action-pypi-publish@release/v1` — looks correct. Consider also publishing to TestPyPI on release-candidate tags.
- The env var `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: "true"` is present in both workflows. Once GitHub deprecates Node 20 actions this is forward-looking; keep it.

---

## 5. Security & data handling

- All data is OGD/CC0; no secrets, no auth tokens — the threat surface is intentionally tiny.
- `_handle_api_error` (line 371) only returns a stringified exception type/message — no traceback leakage.
- `bakom_multi_standort_konnektivitaet` exposes `str(e)[:100]` (line 643). Truncation is good; consider also stripping URL fragments to avoid leaking internal IPs/paths.
- Inputs are bounded via Pydantic (lat 45.8–47.9, lon 5.9–10.6, radius 100–5000m, list ≤20). No risk of unbounded outbound fan-out.
- `httpx.AsyncClient()` is created without a custom `transport`, `verify=`, or proxy config — defaults are fine for OGD endpoints.
- No filesystem or shell side-effects; tools are read-only as advertised in MCP annotations (`readOnlyHint: True`).

No security-critical findings.

---

## 6. Documentation

- READMEs are clear, well-structured, and bilingual.
- `CONTRIBUTING.md` describes a `live` pytest marker that is not implemented (M-6).
- `CHANGELOG.md` follows Keep-a-Changelog. Consider adding an `[Unreleased]` block when work resumes.
- `EXAMPLES.md` (not reviewed in detail) is referenced from the README — ensure example calls cite tool names that actually exist (`bakom_check_api_status` does not).

---

## 7. Recommended fix order

1. **(High)** Reconcile every layer ID against the catalogue in `bakom_breitbandatlas_datensaetze`; introduce a single `LAYERS = {...}` source of truth and import it from each tool. Add a regression test that hits `ch.bakom.netzabdeckung-5g` for Zürich HB and asserts coverage = `True`.
2. **(High)** Stop mutating `highlights_db` in `bakom_aktuell`.
3. **(High)** Add real failure modes to `_wms_abgedeckt` and surface them via `logger.warning` so silent breakage like H-1/2/3 cannot recur.
4. **(Med)** Split unit vs. live tests; mark live tests with `@pytest.mark.live`; collapse the three duplicate scenario files into one parametrised pytest module.
5. **(Med)** Either implement `bakom_check_api_status` or remove it from the README.
6. **(Med)** Tighten Pydantic models: per-tool `thema` enums, `LocationItem` for `MultiLocationInput`.
7. **(Low)** Clean up unused constants, unused logger, `import math` inside loop, schema/docstring drift.

---

## 8. Verdict

The packaging, documentation surface, and CI scaffolding for `bakom-mcp` are above average for a 1.0.0 MCP server. However, **the project ships with a high probability that its three flagship coverage tools never return real data**, and the current test design cannot detect this. Fixing the layer-ID truth source (item 1 above) and rewriting `_wms_abgedeckt` to stop swallowing failures would unblock the rest. With those two fixes plus the cleanup in §7, the project is in good shape for a 1.1.0 release.

# Finding — OPS-001 / Test strategy

**Check:** OPS-001 — Unit/live separation, mocking, CI gating
**Status:** PASS (with minor improvement)
**Severity:** informational
**File:** `tests/test_server.py`, `pyproject.toml:60-66`, `.github/workflows/ci.yml`

## Evidence

- ✅ `respx` used for HTTP mocking (`with respx.mock: …`)
- ✅ `@pytest.mark.live` decorator applied to 5 live tests (lines 620, 636, 645)
- ✅ Marker registered in `pyproject.toml`:
  ```toml
  markers = ["live: live API tests (skipped in CI by default)"]
  ```
- ✅ CI excludes live tests: `pytest tests/ -m "not live"` (`.github/workflows/ci.yml:30`)
- ✅ Matrix tests on Python 3.11 / 3.12 / 3.13
- ✅ Ruff lint runs in CI
- ✅ 38 unit cases covering utilities, input-model validation, integration with mocked HTTP, partial-failure resilience for cross-search

### Minor — layout

OPS-001 prefers separate files (`tests/test_unit.py`, `tests/test_live.py`). This repo merges both into a single `test_server.py` using class-level grouping plus marker. This is a defensible variant — separation is by marker, not file — and is **not a blocker**.

## Remediation (optional)

- Split into `tests/test_unit.py` and `tests/test_live.py` for stricter conformance to OPS-001 layout. Pure refactor, no behaviour change.
- Add a nightly GitHub Actions workflow that runs `pytest -m live` to detect upstream schema drift early.

**Effort:** XS

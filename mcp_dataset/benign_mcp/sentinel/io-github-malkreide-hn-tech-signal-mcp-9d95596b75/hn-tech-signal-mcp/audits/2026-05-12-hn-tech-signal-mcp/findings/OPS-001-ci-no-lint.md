# Finding: OPS-001 — CI führt weder Linter noch Coverage aus

| Feld | Wert |
|---|---|
| **Severity** | **low** |
| **Status** | closed (re-audit 2026-05-12) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `OPS-002` (CI Quality Gates) |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`pyproject.toml:58-61` konfiguriert ruff (`E`, `F`, `I`, `N`, `W`-Regeln,
line-length 100). `.github/workflows/ci.yml` ruft ruff **nie** auf — nur
`pytest -m "not live"`. Coverage wird nicht gemessen. `mypy`/`pyright` fehlen
trotz vollständiger Type-Hints.

### Expected Behavior

CI-Pipeline mit drei Gates: Lint (ruff check + ruff format --check), Typecheck (mypy oder pyright), Tests (pytest). Optional Coverage-Threshold ≥ 80 %.

### Evidence

- `pyproject.toml:55-61` — ruff konfiguriert
- `.github/workflows/ci.yml:33-34` — nur Test-Step, kein Lint-Step

### Risk Description

- Drift zwischen lokaler Entwicklung und CI: Lint-Failures fallen erst beim Reviewer auf.
- Style-Inkonsistenzen akkumulieren über Zeit.
- Type-Bugs (z. B. `Optional[X]` vs. `X | None`) entgehen.

### Remediation

```diff
       - name: Install test deps
         run: uv pip install --system pytest pytest-asyncio respx

+      - name: Lint (ruff)
+        run: |
+          uv pip install --system ruff
+          ruff check src tests
+          ruff format --check src tests
+
       - name: Run unit tests (no network)
-        run: PYTHONPATH=src pytest tests/ -m "not live" -v
+        run: PYTHONPATH=src pytest tests/ -m "not live" -v --cov=hn_tech_signal_mcp --cov-fail-under=70
```

### Effort Estimate

**S** — ~1 Stunde.

### Verification After Fix

- PR mit Lint-Verstoss schlägt CI ab
- Coverage-Badge im README möglich

# Finding: OPS-003 — CI `[dev]`-Extra existiert nicht, Fallback maskiert das

| Feld | Wert |
|---|---|
| **Severity** | **low** |
| **Status** | open (neu im Re-Audit) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `OPS-002` (CI Quality Gates) — Folge-Finding |
| **Audit-Datum** | 2026-05-12 (Re-Audit) |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`.github/workflows/ci.yml:28-29`:

```yaml
- name: Install dependencies
  run: uv pip install --system -e ".[dev]" || uv pip install --system -e .
```

`pyproject.toml` deklariert kein `[project.optional-dependencies]`-Section. Der
erste Befehl schlägt deshalb bei jedem CI-Lauf stillschweigend fehl, der
Fallback installiert ohne Extras. Funktional korrekt, aber:

- Wenn jemand später wirklich einen `[dev]`-Extra braucht und ihn falsch
  konfiguriert, fällt der Fehler nicht auf.
- Die Intention der Zeile ist aus dem Code allein nicht ersichtlich.

### Expected Behavior

Entweder den Extra in `pyproject.toml` definieren, oder den Fallback entfernen
und nur `uv pip install --system -e .` ausführen.

### Evidence

- `.github/workflows/ci.yml:28-29`
- `grep optional-dependencies pyproject.toml` → keine Treffer

### Risk Description

Reines Maintainability-Issue. Kein Sicherheits- oder Korrektheits-Impact.

### Remediation

Option A — Extra entfernen:

```diff
       - name: Install dependencies
-        run: uv pip install --system -e ".[dev]" || uv pip install --system -e .
+        run: uv pip install --system -e .
```

Option B — Extra definieren und in der Test-Deps-Zeile konsolidieren:

```diff
 [project]
 ...
+
+[project.optional-dependencies]
+dev = ["pytest>=8", "pytest-asyncio", "pytest-cov", "respx", "ruff"]
```

```diff
-      - name: Install test deps
-        run: uv pip install --system pytest pytest-asyncio pytest-cov respx ruff
+      # test deps come from the [dev] extra
```

### Effort Estimate

**S** — < 15 Minuten.

### Verification After Fix

- CI-Log enthält keinen Fehler in der Install-Step
- `uv pip install -e ".[dev]"` lokal funktioniert

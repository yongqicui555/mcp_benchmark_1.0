# Finding: ARCH-001 — Falsche/fehlende Dependency: `fastmcp` deklariert, `mcp` importiert

| Feld | Wert |
|---|---|
| **Severity** | **medium** |
| **Status** | closed (re-audit 2026-05-12) |
| **Server** | `hn-tech-signal-mcp` |
| **Check-Reference** | `ARCH-003` / `SDK-001` (Dependency Declaration Honesty) |
| **Audit-Datum** | 2026-05-12 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

`pyproject.toml:31-35` deklariert:

```toml
dependencies = [
    "fastmcp>=2.0.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]
```

`fastmcp` ist das eigenständige Paket von Jeremy Lowin (PyPI: `fastmcp`). Im
Code wird aber das **offizielle Anthropic-MCP-SDK** verwendet:

```python
# src/hn_tech_signal_mcp/server.py:30
from mcp.server.fastmcp import FastMCP
```

`mcp.server.fastmcp` lebt im PyPI-Paket `mcp`, **nicht** in `fastmcp`. Das
Paket `mcp` ist nicht als direkte Dependency deklariert — es zieht aktuell nur
transitiv via `fastmcp` ein (sofern `fastmcp>=2` `mcp` als Abhängigkeit
mitführt; das ist jedoch nicht garantiert über zukünftige Versionen).

### Expected Behavior

Eine Dependency-Deklaration spiegelt die tatsächlichen Imports.

```toml
dependencies = [
    "mcp>=1.2.0",
    "httpx>=0.27.0",
    "pydantic>=2.0.0",
]
```

`fastmcp` entfernen, oder — falls bewusst beide verwendet werden — beide
explizit listen.

### Evidence

- `pyproject.toml:33` — `"fastmcp>=2.0.0"`
- `src/hn_tech_signal_mcp/server.py:30` — `from mcp.server.fastmcp import FastMCP`
- `grep -rn "from fastmcp\|import fastmcp" src/` — keine Treffer

### Risk Description

- **Bruchgefahr bei Updates:** Wenn `fastmcp` v3 die transitive `mcp`-Abhängigkeit ändert oder entfernt, bricht der Build geräuschlos. Reproduzierbare Installs sind nicht garantiert.
- **Sicherheits-Auditing:** SBOM und Dependabot listen `fastmcp`, obwohl der relevante Angriffsvektor `mcp` ist.
- **Erwartungsbruch für Contributors:** Ein neuer Maintainer sucht in der `fastmcp`-Codebasis nach `FastMCP`.

### Remediation

```diff
 dependencies = [
-    "fastmcp>=2.0.0",
+    "mcp>=1.2.0",
     "httpx>=0.27.0",
     "pydantic>=2.0.0",
 ]
```

Anschliessend `uv pip install -e .` und Test-Suite ausführen.

### Effort Estimate

**S** — 10 Minuten.

### Verification After Fix

- `pytest tests/ -m "not live"` grün
- `pip show fastmcp` schlägt fehl, `pip show mcp` listet die Lib

# Finding: ARCH-012 — protocolVersion-Pinning fehlt

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `ARCH-012` |
| **Audit-Datum** | 2026-05-09 |

### Observed Behavior

- pyproject.toml: `mcp[cli]>=1.3.0` — kein Upper-Bound
- `grep protocolVersion src/`: 0 Treffer
- CHANGELOG.md erwähnt MCP-Spec-Version nicht

### Expected Behavior

- Dependency mit Upper-Bound oder mindestens Version-Range, die Major-Versionsprünge verhindert
- Code-Kommentar oder Konstante `MCP_PROTOCOL_VERSION = "2025-06-18"`
- CHANGELOG-Notiz bei jedem mcp-SDK-Update

### Evidence

```toml
# pyproject.toml
dependencies = [
    "mcp[cli]>=1.3.0",  # ← kein Upper-Bound
]
```

### Risk Description

mcp-SDK 2.x wäre ein Major-Bump und könnte Breaking-Changes mit sich bringen. Aktuelles Pin lässt Pip jede Version nehmen — Reproducibility-Risiko bei späteren Installationen.

### Remediation

```toml
dependencies = [
    "mcp[cli]>=1.3.0,<2.0",
    "httpx>=0.27.0,<1.0",
    "pydantic>=2.7.0,<3.0",
]
```

Optional: `MCP_PROTOCOL_VERSION` als Konstante in `server.py` und CI-Test, der `mcp.__version__` verifiziert.

### Effort Estimate

**S** — pyproject-Edit + CHANGELOG-Note.

### Verification After Fix

Re-Audit ARCH-012, `pip install` zeigt Upper-Bound.

## Finding: SCALE-004 — Containerization mit Multi-Stage-Builds

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Check-Status** | fail |
| **Server** | `swiss-electricity-mcp` |
| **Check-Reference** | `SCALE-004` |
| **PDF-Reference** | Sec 5.3 |
| **Audit-Datum** | 2026-06-03 |
| **Auditor** | mcp-audit-skill v1.0.0 (Katalog v0.5.0) |

### Observed Behavior

- is_cloud_deployed=true -> Containerization anwendbar

### Gaps / Abweichung vom Pass-Kriterium

- Kein Dockerfile im Repo - kein Multi-Stage-Build, kein slim/alpine-Base, kein non-root USER, kein HEALTHCHECK

### Risk Description

Container-Images für MCP-Server sind oft 800 MB – 1.5 GB gross, weil Build-Toolchains (gcc, Rust, npm-build-deps) im finalen Image bleiben. Multi-Stage-Builds trennen Build und Runtime: das finale Image enthält nur den fertigen Server plus minimale Runtime-Dependencies (typischerweise 80–150 MB).

### Remediation

```diff
- FROM python:3.11
- WORKDIR /app
- COPY . .
- RUN pip install -e .
- CMD ["python", "-m", "server"]
+ FROM python:3.11-slim AS builder
+ WORKDIR /build
+ COPY pyproject.toml .
+ COPY src/ ./src/
+ RUN pip install --no-cache-dir --user -e .
+
+ FROM python:3.11-slim AS runtime
+ COPY --from=builder /root/.local /root/.local
+ COPY src/ /app/src/
+ WORKDIR /app
+ ENV PATH=/root/.local/bin:$PATH PYTHONUNBUFFERED=1
+ USER nobody
+ HEALTHCHECK CMD curl -f http://localhost:8000/healthz || exit 1
+ CMD ["python", "-m", "server"]
```

### Effort Estimate

S — < 1 Tag.

### Verification After Fix

- Re-Audit von `SCALE-004` via `/audit-mcp`
- Pytest-/grep-Guard gegen das Anti-Pattern (wo automatisierbar)

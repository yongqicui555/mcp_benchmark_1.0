# Finding: SEC-007 — Kein Container-Sandboxing

| Feld | Wert |
|---|---|
| **Severity** | high |
| **Status** | open |
| **Server** | `bakom-mcp` |
| **Check-Reference** | `SEC-007` |
| **Audit-Datum** | 2026-05-08 |

### Observed Behavior

- Kein Dockerfile im Repo
- Kein docker-compose.yml
- README dokumentiert nur uvx/pip-Install

### Expected Behavior

Ein minimaler Container (slim-bullseye / distroless) mit:
- Non-root user
- Read-only filesystem
- Egress-Limits (Network-Layer-Allow-List)
- Resource-Limits (memory, CPU)

### Evidence

- `ls Dockerfile* docker-compose*`: keine Treffer
- `grep -i docker README.md`: 0 Treffer

### Risk Description

- Bei Local-stdio-Use ist der Sandbox-Layer unverzichtbar weniger relevant (User-Trust für eigene Maschine).
- **Bei Cloud-Deployment** (HTTP-Modus): kein Container = direkter Host-Process auf der Cloud-VM = volle System-Privilegien beim Crash mit Code-Execution-CVE in Dependency.
- Anti-Shadow-MCP-Compliance (Enterprise) verlangt Container.

### Remediation

```dockerfile
# Dockerfile
FROM python:3.11-slim-bullseye AS builder
WORKDIR /build
COPY pyproject.toml .
RUN pip install --no-cache-dir -e .

FROM python:3.11-slim-bullseye
RUN useradd --uid 10001 --no-create-home --shell /sbin/nologin bakom
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY src/ /app/src/
USER bakom
ENV PYTHONPATH=/app/src
EXPOSE 8050
CMD ["python", "-m", "bakom_mcp.server", "--http"]
```

`docker-compose.yml`:

```yaml
services:
  bakom-mcp:
    build: .
    read_only: true
    cap_drop: [ALL]
    security_opt: [no-new-privileges]
    mem_limit: 256m
    cpus: 0.5
```

### Effort Estimate

**M** — 1 Tag Dockerfile + Compose + CI-Build-Job.

### Verification After Fix

`docker build .` succeeds. `docker inspect` zeigt non-root user + read_only.

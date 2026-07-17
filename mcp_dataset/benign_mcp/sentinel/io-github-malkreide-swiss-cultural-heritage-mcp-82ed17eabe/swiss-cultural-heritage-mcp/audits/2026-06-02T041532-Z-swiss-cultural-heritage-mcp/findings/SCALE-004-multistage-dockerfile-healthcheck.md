## Finding: SCALE-004 — Containerization: Multi-Stage-Build + HEALTHCHECK

| Feld | Wert |
|---|---|
| **Severity** | medium |
| **Status** | open |
| **Server** | `swiss-cultural-heritage-mcp` |
| **Check-Reference** | `SCALE-004` |
| **PDF-Reference** | Sec 5.x |
| **Audit-Datum** | 2026-06-02 |
| **Auditor** | Claude (mcp-audit-skill) |

### Observed Behavior

- Dockerfile uses a slim base (python:3.13-slim) and a non-root user UID 10001 (Dockerfile)

### Gaps vs. Pass Criteria

- Single-stage build (one FROM, no AS builder/runtime split)
- No HEALTHCHECK directive in the Dockerfile (a /health route exists in-app)

### Expected Behavior

Dockerfile with >=2 named stages (builder/runtime), slim/alpine final base, non-root user, and a HEALTHCHECK directive; final image < 200 MB.

### Risk Description

A single-stage image can carry build artefacts into the runtime layer (larger surface); a missing HEALTHCHECK means orchestrators cannot detect a wedged process.

### Remediation

Split the Dockerfile into `AS builder` (pip install/wheel) and `AS runtime` (copy site-packages only); add `HEALTHCHECK --interval=30s CMD python -c "import urllib.request,sys; urllib.request.urlopen('http://127.0.0.1:8000/health')"` (or curl).

### Effort Estimate

**S**  (S < 1d · M 1–3d · L 1–2w · XL > 2w)

### Verification After Fix

Re-run check `SCALE-004` from the mcp-audit-skill catalog; add/adjust the pytest case noted in the remediation where applicable.

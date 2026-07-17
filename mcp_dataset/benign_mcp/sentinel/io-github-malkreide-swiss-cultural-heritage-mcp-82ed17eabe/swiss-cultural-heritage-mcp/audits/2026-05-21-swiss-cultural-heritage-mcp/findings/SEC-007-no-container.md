# Finding — SEC-007 / Container sandboxing

**Check:** SEC-007 — Container sandbox (Docker hardening / non-root / read-only FS)
**Status:** FAIL
**Severity:** medium
**Files:** repository root (no `Dockerfile`), `README.md:131-141`

## Evidence

- No `Dockerfile` exists in the repository.
- The README's "Cloud Deployment" section relies on Render's buildpack, which runs the process as a non-root user by default but provides no documented seccomp profile, no read-only root filesystem, no capability drop, and no Kubernetes `SecurityContext` (because Render is not Kubernetes).
- For local stdio installs (`uvx swiss-cultural-heritage-mcp`) the server runs with full user privileges and full filesystem access — relevant given the audit framework's threat model of compromised server code reaching `~/.ssh`, `~/.aws`, etc.

## Impact

- Defense-in-depth gap as catalogued in SEC-007. Severity is `medium` here (not `critical`) because:
  - No write tools, no destructive tools, no PII, no credentials handled by this server
  - Egress is limited to three known hosts (when SEC-021 is fixed)
- However, any future tool that touches the local filesystem or shells out would inherit a non-sandboxed environment

## Remediation

1. Add a minimal `Dockerfile`:
   ```dockerfile
   FROM python:3.13-slim
   RUN useradd -u 10001 -m app
   WORKDIR /app
   COPY pyproject.toml ./
   COPY src ./src
   RUN pip install --no-cache-dir .
   USER 10001
   ENV PYTHONUNBUFFERED=1
   CMD ["python", "-m", "swiss_cultural_heritage_mcp.server", "--http", "--port", "8000"]
   ```
2. Add a `docs/security.md` documenting:
   - Non-root UID ≥ 10000
   - Recommendation to deploy with `readOnlyRootFilesystem: true` and `cap_drop: [ALL]` on platforms that support it (k8s, Fly.io, Cloud Run)
   - Default `seccomp=RuntimeDefault`
3. Reference SEC-007 in the security doc so future contributors can reproduce the rationale.

**Effort:** S (≤ 1 day)

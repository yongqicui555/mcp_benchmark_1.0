# Container image for swiss-cultural-heritage-mcp.
#
# Multi-stage build (audit findings SCALE-004 / SEC-007 / SEC-016):
#   - builder stage compiles/installs deps; runtime stage carries only the
#     installed packages — no pip cache, no build tooling in the final layer
#   - non-root user (UID 10001)
#   - HEALTHCHECK wired to the in-app /health route for the orchestrator
#   - MCP_HOST=0.0.0.0 set ONLY here, so the container is reachable behind the
#     platform LB while the code default stays 127.0.0.1 (no NeighborJack)
#
# Recommended platform settings on Kubernetes / Cloud Run / Fly.io:
#   readOnlyRootFilesystem: true
#   allowPrivilegeEscalation: false
#   capabilities.drop: ["ALL"]
#   seccompProfile: RuntimeDefault
#   resources: { requests: {cpu: 100m, memory: 128Mi}, limits: {cpu: 500m, memory: 256Mi} }

# ─────────────────────────── Stage 1: builder ──────────────────────────────────
FROM python:3.14-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /build

COPY pyproject.toml README.md LICENSE ./
COPY src ./src

# Install into an isolated prefix that the runtime stage copies wholesale.
RUN pip install --no-cache-dir --prefix=/install .

# ─────────────────────────── Stage 2: runtime ──────────────────────────────────
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

WORKDIR /app

COPY --from=builder /install /usr/local

RUN useradd --create-home --uid 10001 --shell /usr/sbin/nologin app
USER 10001

EXPOSE 8000

# SCALE-004: liveness probe against the in-app /health endpoint.
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD python -c "import sys,urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2).status == 200 else 1)"

CMD ["python", "-m", "swiss_cultural_heritage_mcp.server", "--http", "--port", "8000"]

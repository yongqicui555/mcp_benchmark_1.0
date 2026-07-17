# ───────────────────────── Stage 1: builder ─────────────────────────
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src

# In ein isoliertes Prefix installieren, das in die Runtime-Stage kopiert wird.
RUN pip install --prefix=/install .

# ───────────────────────── Stage 2: runtime ─────────────────────────
FROM python:3.12-slim AS runtime

# Non-root User (SEC-007: kein root im Container).
RUN useradd --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser

COPY --from=builder /install /usr/local

# Cloud-Defaults: HTTP-Transport, Binding auf alle Interfaces NUR im Container
# (lokal bleibt der Code-Default 127.0.0.1 — siehe SEC-016).
ENV MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000 \
    MCP_STATELESS_HTTP=true \
    PYTHONUNBUFFERED=1

EXPOSE 8000
USER 10001

# Health-Probe für LB / Orchestrator (SCALE-004) — nutzt /health-Endpoint.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health').status==200 else 1)"]

ENTRYPOINT ["zh-education-mcp"]

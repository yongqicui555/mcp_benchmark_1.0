# ─────────────────────────── Build-Stage ───────────────────────────────────────
FROM python:3.11-slim AS builder
WORKDIR /build
COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/
RUN pip install --no-cache-dir --user .

# ─────────────────────────── Runtime-Stage ─────────────────────────────────────
FROM python:3.11-slim AS runtime

# Non-root User mit hoher UID (SEC-007).
RUN useradd --uid 10001 --create-home --shell /usr/sbin/nologin mcp

COPY --from=builder /root/.local /home/mcp/.local
WORKDIR /app

ENV PATH=/home/mcp/.local/bin:$PATH \
    PYTHONUNBUFFERED=1 \
    PYTHONUTF8=1 \
    MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8080

USER 10001
EXPOSE 8080

# Liveness: TCP-Connect auf den MCP-Port (SCALE-004).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,socket; socket.create_connection(('127.0.0.1', int(os.environ.get('MCP_PORT','8080'))), timeout=3)" || exit 1

CMD ["python", "-m", "parlament_mcp.server"]

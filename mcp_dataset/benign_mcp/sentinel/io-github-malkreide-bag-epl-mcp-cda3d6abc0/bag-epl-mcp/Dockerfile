# ── Multi-Stage-Build (SCALE-004) ───────────────────────────────────────────────
# Stage 1: Abhaengigkeiten in ein venv installieren.
FROM python:3.12-slim AS builder

WORKDIR /app
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1

# Nur die fuer den Build noetigen Dateien kopieren (siehe .dockerignore).
COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --upgrade pip \
    && /opt/venv/bin/pip install ".[http]"

# ── Stage 2: schlankes Runtime-Image ────────────────────────────────────────────
FROM python:3.12-slim AS runtime

# SEC-007: Non-Root-User (UID >= 10000), keine Root-Rechte zur Laufzeit.
RUN groupadd -r -g 10001 app && useradd -r -g app -u 10001 -d /home/app -m app

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    MCP_TRANSPORT=streamable-http \
    MCP_HOST=0.0.0.0 \
    MCP_PORT=8000

USER app
EXPOSE 8000

# SCALE-004: HEALTHCHECK fuer Load-Balancer-Integration (nutzt /healthz).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:%s/healthz' % os.environ.get('MCP_PORT','8000'), timeout=3)" || exit 1

CMD ["python", "-m", "bag_epl_mcp.server"]

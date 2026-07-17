# syntax=docker/dockerfile:1.7
# bakom-mcp container — minimal, non-root, read-only-friendly.
#
# Stage 1: Build — installiert Dependencies in ein virtuelles env
# Stage 2: Runtime — distroless-naehe slim-bullseye ohne Build-Toolchain.

FROM python:3.11-slim-bullseye AS builder

WORKDIR /build

# Build-Dependencies fuer pure-python wheels
RUN pip install --no-cache-dir --upgrade pip uv

COPY pyproject.toml README.md LICENSE ./
COPY src/ ./src/

# Wheel bauen, dann in /opt/venv installieren
RUN uv venv /opt/venv && \
    . /opt/venv/bin/activate && \
    uv pip install --no-cache-dir .

# ---------------------------------------------------------------------------

FROM python:3.11-slim-bullseye AS runtime

# Non-root user (UID 10001 — ausserhalb klassischer Reservierungen)
RUN groupadd --system --gid 10001 bakom && \
    useradd --system --uid 10001 --gid bakom --no-create-home --shell /sbin/nologin bakom

# Virtuelles env aus Builder uebernehmen
COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    BAKOM_MCP_HOST=0.0.0.0 \
    BAKOM_MCP_PORT=8050

USER bakom
EXPOSE 8050

# HEALTHCHECK gegen den Streamable-HTTP-Endpoint.
# /mcp gibt 405 fuer GET ohne Session, das ist der erwartete "alive"-Indikator.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,sys; \
r = urllib.request.urlopen('http://127.0.0.1:8050/mcp', timeout=3); \
sys.exit(0 if r.status in (200, 405, 406) else 1)" || exit 1

# Default: Streamable-HTTP — fuer stdio-Mode wuerde man den Container
# nicht via docker run starten, sondern direkt via uvx auf dem Host.
CMD ["python", "-m", "bakom_mcp.server", "--http"]

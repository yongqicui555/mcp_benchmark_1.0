# syntax=docker/dockerfile:1.7
#
# Multi-stage build for lobbywatch-mcp (audit SCALE-004, SEC-007, SCALE-006).
# Hardening goals:
#   - Non-root runtime user (uid/gid 1000)
#   - read-only rootfs compatible (cache lives in /home/lobbywatch/.cache,
#     mount as tmpfs in compose/k8s)
#   - No build toolchain or apt cache in the runtime image
#   - Image small enough for routine pulls (~80 MB on python:slim)

ARG PYTHON_VERSION=3.13

# ---------------------------------------------------------------------------
# Builder: install the project into an isolated venv we can copy out.
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /build

# Install into a venv so we can COPY just /opt/venv to the runtime image.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy only what hatchling needs to build the wheel.
COPY pyproject.toml README.md LICENSE ./
COPY src ./src

RUN pip install --no-cache-dir .

# ---------------------------------------------------------------------------
# Runtime: minimal image, non-root user, no build tools.
# ---------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

LABEL org.opencontainers.image.source="https://github.com/malkreide/lobbywatch-mcp" \
      org.opencontainers.image.description="MCP server for the Lobbywatch.ch lobby database" \
      org.opencontainers.image.licenses="MIT"

# Create a fixed-uid non-root user. uid 1000 is the convention; matches the
# default Pod SecurityContext in most k8s presets and avoids volume-permission
# surprises on host-mount setups.
RUN groupadd --system --gid 1000 lobbywatch \
 && useradd --system --uid 1000 --gid 1000 \
        --home-dir /home/lobbywatch --shell /sbin/nologin lobbywatch \
 && mkdir -p /home/lobbywatch/.cache/lobbywatch-mcp \
 && chown -R lobbywatch:lobbywatch /home/lobbywatch

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    LOBBYWATCH_MCP_TRANSPORT=http \
    LOBBYWATCH_MCP_HOST=0.0.0.0 \
    LOBBYWATCH_MCP_PORT=8000 \
    LOBBYWATCH_MCP_CACHE_DIR=/home/lobbywatch/.cache/lobbywatch-mcp

USER 1000:1000
WORKDIR /home/lobbywatch
EXPOSE 8000

# In-image healthcheck: ensure the entry point still imports cleanly.
# This is intentionally lightweight — full liveness/readiness probes belong on
# the orchestrator (see docs/deployment.md).
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import lobbywatch_mcp" || exit 1

ENTRYPOINT ["lobbywatch-mcp"]

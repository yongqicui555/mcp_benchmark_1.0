# syntax=docker/dockerfile:1

# ---- Stage 1: builder -------------------------------------------------------
FROM python:3.12-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /build

# Build a self-contained virtualenv so the runtime image stays minimal.
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install .

# ---- Stage 2: runtime -------------------------------------------------------
FROM python:3.12-slim AS runtime

# Non-root user (UID >= 10000) — no shell, no home write access.
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin appuser

COPY --from=builder /opt/venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    SWISS_ELECTRICITY_TRANSPORT=streamable-http \
    SWISS_ELECTRICITY_HOST=0.0.0.0 \
    SWISS_ELECTRICITY_PORT=8000

USER appuser
EXPOSE 8000

# Liveness: the streamable-http endpoint responds on /mcp.
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request,os; \
urllib.request.urlopen('http://127.0.0.1:'+os.environ.get('SWISS_ELECTRICITY_PORT','8000')+'/mcp', timeout=4)" \
    || exit 1

ENTRYPOINT ["swiss-electricity-mcp"]

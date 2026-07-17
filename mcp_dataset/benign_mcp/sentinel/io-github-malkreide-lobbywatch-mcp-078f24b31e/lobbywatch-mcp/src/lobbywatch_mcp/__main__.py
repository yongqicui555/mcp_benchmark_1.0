"""CLI entry point for lobbywatch-mcp.

Transport selection follows the Swiss Public Data MCP Portfolio convention:
set ``LOBBYWATCH_MCP_TRANSPORT`` to ``stdio`` (default), ``http`` or ``sse``.

Observability env vars (audit OBS-003, OBS-006):
    LOBBYWATCH_MCP_LOG_FORMAT    text | json    (default: text)
    LOBBYWATCH_MCP_LOG_LEVEL     DEBUG | INFO | WARNING | ERROR  (default: INFO)
    LOBBYWATCH_MCP_OTEL_ENABLED  0 | 1          (default: 0)
    LOBBYWATCH_MCP_OTEL_ENDPOINT URL of OTLP/HTTP collector (optional)

For HTTP/SSE deployments, optional CORS configuration via
``LOBBYWATCH_MCP_CORS_ORIGINS`` (comma-separated origin list, e.g.
``"https://app.example.ch,https://inspector.local"``). When set, a Starlette
``CORSMiddleware`` wraps the FastMCP ASGI app and exposes ``Mcp-Session-Id``
to browser clients (audit SDK-004). Without the env var no CORS headers are
emitted — the safe default.
"""

from __future__ import annotations

import logging
import os

from lobbywatch_mcp._observability import configure_logging, configure_tracing
from lobbywatch_mcp.server import build_server

logger = logging.getLogger(__name__)


def _parse_cors_origins() -> list[str]:
    raw = os.getenv("LOBBYWATCH_MCP_CORS_ORIGINS", "").strip()
    if not raw:
        return []
    return [origin.strip() for origin in raw.split(",") if origin.strip()]


def _run_asgi(transport: str, host: str, port: int) -> None:
    """Run the streamable-http or sse ASGI app under uvicorn, optionally
    wrapped with CORSMiddleware (audit SDK-004).
    """
    import uvicorn

    mcp = build_server()
    if transport == "http":
        app = mcp.streamable_http_app()
    else:
        app = mcp.sse_app()

    cors_origins = _parse_cors_origins()
    if cors_origins:
        from starlette.middleware.cors import CORSMiddleware

        app = CORSMiddleware(
            app,
            allow_origins=cors_origins,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "Mcp-Session-Id", "Authorization"],
            expose_headers=["Mcp-Session-Id"],
            allow_credentials=False,
            max_age=600,
        )
        logger.info("CORS enabled for origins: %s", cors_origins)

    uvicorn.run(app, host=host, port=port, log_config=None)


def main() -> None:
    configure_logging()
    configure_tracing()

    transport = os.getenv("LOBBYWATCH_MCP_TRANSPORT", "stdio").lower()

    if transport in ("http", "sse"):
        host = os.getenv("LOBBYWATCH_MCP_HOST", "127.0.0.1")
        port = int(os.getenv("LOBBYWATCH_MCP_PORT", "8000"))
        _run_asgi(transport, host, port)
        return

    # Default: stdio. No HTTP surface, no CORS, no port binding.
    mcp = build_server()
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

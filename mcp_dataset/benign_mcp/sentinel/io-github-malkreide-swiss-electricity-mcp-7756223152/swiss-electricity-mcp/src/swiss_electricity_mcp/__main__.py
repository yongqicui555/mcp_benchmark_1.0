"""Entrypoint for swiss-electricity-mcp.

Transport selected via SWISS_ELECTRICITY_TRANSPORT env var:
- stdio (default): for Claude Desktop and local IDE clients
- streamable-http: for cloud / remote deployments (Render, Railway, etc.)

The HTTP host defaults to 127.0.0.1 (loopback only). Bind to all interfaces
explicitly via SWISS_ELECTRICITY_HOST=0.0.0.0 inside a container only — never
as the implicit default (NeighborJack / SEC-016).

For browser-based clients, allowed CORS origins are configured via
SWISS_ELECTRICITY_CORS_ORIGINS (comma-separated). The default is empty
(same-origin only) — never a wildcard (SDK-004).

All configuration is read through the Settings object in config.py (ARCH-004).
"""

from __future__ import annotations

from starlette.applications import Starlette
from starlette.middleware.cors import CORSMiddleware

from .config import get_settings
from .server import mcp


def build_http_app(origins: list[str] | None = None) -> Starlette:
    """Build the Streamable-HTTP app with CORS that exposes Mcp-Session-Id.

    `expose_headers` must include `Mcp-Session-Id` so browser clients can read
    the session id from the response; `allow_headers` must include it so they
    can send it back on follow-up requests (SDK-004).
    """
    if origins is None:
        origins = get_settings().cors_origins
    app = mcp.streamable_http_app()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,  # explicit list, never "*"
        allow_methods=["GET", "POST", "DELETE", "OPTIONS"],
        allow_headers=["Mcp-Session-Id", "Content-Type"],
        expose_headers=["Mcp-Session-Id"],
        allow_credentials=bool(origins),
    )
    return app


def main() -> None:
    settings = get_settings()
    if settings.transport.lower() in {"http", "streamable-http", "sse"}:
        import uvicorn

        mcp.settings.host = settings.host
        mcp.settings.port = settings.port
        uvicorn.run(build_http_app(), host=settings.host, port=settings.port)
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

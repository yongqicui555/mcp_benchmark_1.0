"""Youfiliate MCP Server — Smart Links management via MCP protocol.

Entry point for the MCP server. Supports two transports:
  - stdio (default, for local dev / Claude Desktop subprocess)
  - streamable-http (for remote deployment)

Auth:
  - stdio: uses `YOUFILIATE_API_KEY` env var (one user per process).
  - streamable-http: reads `Authorization: Bearer <key>` per request, so
    a single deployment can serve many users. The env var, if set, is
    used only as a fallback for unauthenticated requests.

Usage:
  youfiliate-mcp                            # stdio (default)
  youfiliate-mcp --transport streamable-http # HTTP on port 8080
"""

from __future__ import annotations

import argparse
import logging
import sys

from mcp.server.fastmcp import FastMCP

from .auth import AuthManager
from .client import YoufiliateClient
from .config import settings
from .middleware import BearerAuthMiddleware
from .resources import register_resources
from .tools.analytics import register_analytics_tools
from .tools.migrations import register_migration_tools
from .tools.preferences import register_preferences_tools
from .tools.smart_links import register_smart_link_tools
from .tools.youtube import register_youtube_tools

# Configure logging to stderr (stdio transport uses stdout for MCP)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stderr,
)
logger = logging.getLogger("youfiliate_mcp")


def create_server(host: str = "127.0.0.1", port: int = 8080) -> FastMCP:
    """Create and configure the MCP server with all tools and resources."""
    # Parse allowed origins for DNS rebinding protection in HTTP transport
    allowed_origins = [
        o.strip()
        for o in settings.allowed_origins.split(",")
        if o.strip()
    ] or None

    mcp = FastMCP(
        "youfiliate_mcp",
        host=host,
        port=port,
        stateless_http=True,
        json_response=True,
        **({"allowed_origins": allowed_origins} if allowed_origins else {}),
    )

    # Create shared auth manager and API client. In HTTP mode the auth
    # manager picks up each request's Bearer token via a ContextVar set by
    # BearerAuthMiddleware; in stdio mode it falls back to the env var.
    auth = AuthManager()
    client = YoufiliateClient(auth=auth)

    # Register all tools (18 total)
    register_smart_link_tools(mcp, client)      # 5 tools
    register_analytics_tools(mcp, client)        # 3 tools
    register_preferences_tools(mcp, client)      # 2 tools
    register_youtube_tools(mcp, client)           # 3 tools
    register_migration_tools(mcp, client)         # 5 tools

    # Register all resources (4 total)
    register_resources(mcp, client)

    logger.info(
        "Youfiliate MCP server initialized: 18 tools, 4 resources"
    )

    return mcp


def _run_streamable_http(mcp: FastMCP, host: str, port: int) -> None:
    """Run the MCP server over streamable-http with Bearer auth middleware.

    We build the Starlette app ourselves so we can install
    `BearerAuthMiddleware` in front of it, then hand it to uvicorn.
    """
    import uvicorn

    app = mcp.streamable_http_app()
    app.add_middleware(BearerAuthMiddleware)

    logger.info(f"Starting Youfiliate MCP server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, log_level="info")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Youfiliate MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "streamable-http"],
        default=settings.transport,
        help="Transport mode (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=settings.port,
        help="Port for streamable-http transport (default: 8080)",
    )
    parser.add_argument(
        "--host",
        default=settings.host,
        help="Host binding (default: 127.0.0.1)",
    )
    args = parser.parse_args()

    server = create_server(host=args.host, port=args.port)

    if args.transport == "streamable-http":
        _run_streamable_http(server, args.host, args.port)
    else:
        logger.info("Starting Youfiliate MCP server (stdio transport)")
        server.run(transport="stdio")


if __name__ == "__main__":
    main()

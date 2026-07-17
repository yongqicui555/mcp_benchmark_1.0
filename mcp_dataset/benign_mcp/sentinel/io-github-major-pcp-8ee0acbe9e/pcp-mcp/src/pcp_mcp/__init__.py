"""PCP MCP Server - Performance Co-Pilot metrics via Model Context Protocol."""

from __future__ import annotations

import argparse
import os


def main() -> None:
    """Run the PCP MCP server."""
    parser = argparse.ArgumentParser(
        description="PCP MCP Server - Performance Co-Pilot Metrics",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Environment Variables:
  PCP_HOST          pmproxy host (default: localhost)
  PCP_PORT          pmproxy port (default: 44322)
  PCP_TARGET_HOST   Target pmcd host to monitor (default: localhost)
  PCP_USE_TLS       Use HTTPS for pmproxy connection (default: false)
  PCP_TLS_VERIFY    Verify TLS certificates (default: true)
  PCP_TLS_CA_BUNDLE Path to custom CA bundle for TLS (optional)
  PCP_TIMEOUT       Request timeout in seconds (default: 30)
  PCP_USERNAME      HTTP basic auth user (optional)
  PCP_PASSWORD      HTTP basic auth password (optional)
  PCP_ALLOWED_HOSTS Comma-separated hostspecs allowed via host parameter (optional)
                    If not set, only target_host is allowed. Use '*' for any host.

Examples:
  # Monitor localhost (default)
  pcp-mcp

  # Monitor a remote host
  PCP_TARGET_HOST=webserver1.example.com pcp-mcp

  # Connect to pmproxy on a different host
  PCP_HOST=metrics.example.com pcp-mcp

  # Use SSE transport
  pcp-mcp --transport sse
""",
    )
    parser.add_argument(
        "--target-host",
        help="Target pmcd host to monitor (overrides PCP_TARGET_HOST)",
    )
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse", "streamable-http"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    args = parser.parse_args()

    if args.target_host:
        os.environ["PCP_TARGET_HOST"] = args.target_host

    from pcp_mcp.server import create_server

    server = create_server()
    server.run(transport=args.transport)


__all__ = ["main"]

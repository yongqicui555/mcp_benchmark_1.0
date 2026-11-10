"""Entry point for `python -m silentwatch_mcp` and the console script."""
from __future__ import annotations

import asyncio
import logging
import os
import sys

from silentwatch_mcp import __version__
from silentwatch_mcp.server import build_server

logger = logging.getLogger(__name__)


def _emit_startup_banner(backend_name: str) -> None:
    """Print a one-line value-prove banner to stderr at startup.

    Runs once on server initialization. Goes to stderr (stdout is reserved for
    MCP JSON-RPC protocol traffic). Suppressible via `SILENTWATCH_QUIET=1` env var
    for users who pipe stderr to a log file and want it terse.
    """
    if os.environ.get("SILENTWATCH_QUIET", "").strip() in {"1", "true", "yes"}:
        return
    banner = (
        f"silentwatch-mcp v{__version__} ready · "
        f"catches cron silent failures (exit-0+empty-stdout, drift, missed runs) · "
        f"7 textbook patterns · backend={backend_name}"
    )
    print(banner, file=sys.stderr, flush=True)


def main() -> None:
    """Run the MCP server over stdio, OR dispatch to a subcommand.

    Subcommands:
    - ``monitor [args]`` → long-running NDJSON event stream (used by Aufgaard's
      monitor framework). See ``silentwatch_mcp.monitor``.

    With no subcommand: runs the MCP server (the original behavior).
    """
    # Subcommand dispatch
    if len(sys.argv) >= 2 and sys.argv[1] == "monitor":
        from silentwatch_mcp.monitor import main as monitor_main
        sys.exit(monitor_main())

    logging.basicConfig(
        level=os.environ.get("OPENCLAW_CRON_LOG_LEVEL", "INFO"),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        stream=sys.stderr,  # MCP uses stdout for protocol; logs MUST go to stderr
    )

    backend_name = os.environ.get("SILENTWATCH_BACKEND", "mock")
    _emit_startup_banner(backend_name)
    logger.info("Starting silentwatch-mcp with backend=%s", backend_name)

    try:
        server = build_server(backend_name=backend_name)
        asyncio.run(_run_stdio(server))
    except KeyboardInterrupt:
        logger.info("Shutting down on KeyboardInterrupt")
        sys.exit(0)
    except Exception:
        logger.exception("Fatal error in MCP server")
        sys.exit(1)


async def _run_stdio(server: object) -> None:
    """Run the server over stdio transport.

    Imported lazily so `python -m silentwatch_mcp --help` works without
    requiring the mcp package to be importable (useful in CI for fast smoke tests).
    """
    from mcp.server.stdio import stdio_server

    async with stdio_server() as (read_stream, write_stream):
        await server.run(  # type: ignore[attr-defined]
            read_stream,
            write_stream,
            server.create_initialization_options(),  # type: ignore[attr-defined]
        )


if __name__ == "__main__":
    main()

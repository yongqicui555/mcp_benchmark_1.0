"""Strukturiertes Logging auf stderr (OBS-003 + OBS-004).

structlog mit JSON-Output. Der Logger schreibt **ausschliesslich** auf stderr —
stdout bleibt für den stdio-JSON-RPC-Protokoll-Stream reserviert (OBS-004).
"""

from __future__ import annotations

import logging
import sys

import structlog

_configured = False


def configure_logging(level: str = "INFO", json_logs: bool = True) -> None:
    """structlog idempotent konfigurieren. Sicher mehrfach aufrufbar."""
    global _configured
    if _configured:
        return

    logging.basicConfig(
        stream=sys.stderr,
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(message)s",
    )

    processors: list = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
    ]
    processors.append(
        structlog.processors.JSONRenderer()
        if json_logs
        else structlog.dev.ConsoleRenderer()
    )

    structlog.configure(
        processors=processors,
        # PrintLoggerFactory(file=sys.stderr) garantiert stderr — niemals stdout.
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, level.upper(), logging.INFO)
        ),
        cache_logger_on_first_use=True,
    )
    _configured = True


def get_logger(name: str = "parlament_mcp"):
    """Gebundenen structlog-Logger zurückgeben (konfiguriert bei Bedarf)."""
    if not _configured:
        configure_logging()
    return structlog.get_logger(name)

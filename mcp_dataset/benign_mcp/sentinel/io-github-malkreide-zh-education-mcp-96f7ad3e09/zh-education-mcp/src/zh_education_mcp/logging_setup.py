"""Strukturiertes Logging auf stderr (OBS-003/OBS-004).

stdout bleibt dem MCP-Protokoll vorbehalten; Logs gehen als JSON auf stderr.
"""

from __future__ import annotations

import sys

import structlog

structlog.configure(
    processors=[
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.WriteLoggerFactory(file=sys.stderr),
    cache_logger_on_first_use=True,
)

log = structlog.get_logger("zh_education_mcp")

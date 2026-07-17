"""Central configuration constants for lobbywatch-mcp.

All data URLs and provenance strings are defined here so attribution
(CC BY-SA 4.0) is consistent across every tool response.
"""

from __future__ import annotations

import os
from pathlib import Path

# Primary source: weekly aggregated JSON dump (reliable).
DUMP_URL = (
    "https://cms.lobbywatch.ch/sites/lobbywatch.ch/files/exports/"
    "lobbywatch_export_aggregated.json.zip"
)

# File inside the dump zip that holds parlamentarier with nested relations.
DUMP_INNER_FILE = "aggregated_essential_parlamentarier_nested.json"

# Fallback: live REST interface (dataIF). Use only for tables that return data
# reliably (e.g. interessengruppe, branche) or for the /search endpoint.
API_BASE = "https://cms.lobbywatch.ch/de/data/interface/v1/json"

# How long to trust the cached dump before re-downloading. The upstream export
# runs weekly on Monday morning, so 24 h is a pragmatic default.
CACHE_TTL_SECONDS = int(os.getenv("LOBBYWATCH_MCP_CACHE_TTL", str(24 * 60 * 60)))

# Directory where the downloaded dump is cached between runs.
CACHE_DIR = Path(
    os.getenv("LOBBYWATCH_MCP_CACHE_DIR", str(Path.home() / ".cache" / "lobbywatch-mcp"))
)

# HTTP timeout for all outbound requests.
HTTP_TIMEOUT_SECONDS = float(os.getenv("LOBBYWATCH_MCP_HTTP_TIMEOUT", "60"))

# User-Agent identifying this client to Lobbywatch server logs.
USER_AGENT = "lobbywatch-mcp/0.3.1 (+https://github.com/malkreide/lobbywatch-mcp)"

# Attribution snippet attached to every response. Non-negotiable: the dataset
# is licensed CC BY-SA 4.0 and requires credit.
ATTRIBUTION = (
    "Data: Lobbywatch.ch — CC BY-SA 4.0 (https://creativecommons.org/licenses/by-sa/4.0/). "
    "Not an official register; community-researched records."
)

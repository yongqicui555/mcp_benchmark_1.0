"""Databricks WorkspaceClient configuration and tool filtering."""

from __future__ import annotations

import os
from functools import lru_cache

from databricks.sdk import WorkspaceClient


@lru_cache(maxsize=1)
def get_workspace_client() -> WorkspaceClient:
    """Get or create a cached WorkspaceClient.

    Auth is fully delegated to the SDK's unified auth mechanism.
    Supports: PAT, OAuth M2M, Azure AD, Azure CLI, Databricks CLI profile,
    Google credentials, and more — all auto-detected.
    """
    return WorkspaceClient()


def get_tool_filter() -> tuple[set[str] | None, set[str] | None]:
    """Get tool include/exclude filters from environment variables.

    Returns:
        (include_set, exclude_set) — at most one will be non-None.
        If both are None, all tools are registered.

    Environment variables:
        DATABRICKS_MCP_TOOLS_INCLUDE: Comma-separated module names to include
        DATABRICKS_MCP_TOOLS_EXCLUDE: Comma-separated module names to exclude
    """
    include = os.environ.get("DATABRICKS_MCP_TOOLS_INCLUDE")
    exclude = os.environ.get("DATABRICKS_MCP_TOOLS_EXCLUDE")

    include_set = {s.strip() for s in include.split(",") if s.strip()} if include else None
    exclude_set = {s.strip() for s in exclude.split(",") if s.strip()} if exclude else None

    # INCLUDE takes precedence if both are set
    if include_set and exclude_set:
        exclude_set = None

    return include_set, exclude_set


def is_module_enabled(module_name: str) -> bool:
    """Check whether a tool module should be registered based on filters."""
    include_set, exclude_set = get_tool_filter()

    if include_set is not None:
        return module_name in include_set
    if exclude_set is not None:
        return module_name not in exclude_set
    return True

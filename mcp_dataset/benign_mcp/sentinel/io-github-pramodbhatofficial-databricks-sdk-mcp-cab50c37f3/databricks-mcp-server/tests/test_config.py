"""Tests for databricks_mcp.config — get_tool_filter() and is_module_enabled()."""

import os
from unittest.mock import patch

import pytest

from databricks_mcp.config import get_tool_filter, is_module_enabled


# ---------------------------------------------------------------------------
# get_tool_filter()
# ---------------------------------------------------------------------------

class TestGetToolFilter:
    """Verify environment-based tool filtering logic."""

    def test_no_env_vars_returns_none_none(self) -> None:
        """When neither INCLUDE nor EXCLUDE is set, both are None."""
        with patch.dict(os.environ, {}, clear=True):
            include, exclude = get_tool_filter()
            assert include is None
            assert exclude is None

    def test_include_only(self) -> None:
        """INCLUDE env var parses comma-separated module names."""
        with patch.dict(os.environ, {"DATABRICKS_MCP_TOOLS_INCLUDE": "sql,compute,jobs"}, clear=True):
            include, exclude = get_tool_filter()
            assert include == {"sql", "compute", "jobs"}
            assert exclude is None

    def test_exclude_only(self) -> None:
        """EXCLUDE env var parses comma-separated module names."""
        with patch.dict(os.environ, {"DATABRICKS_MCP_TOOLS_EXCLUDE": "genie,sharing"}, clear=True):
            include, exclude = get_tool_filter()
            assert include is None
            assert exclude == {"genie", "sharing"}

    def test_include_takes_precedence_over_exclude(self) -> None:
        """When both INCLUDE and EXCLUDE are set, INCLUDE wins and EXCLUDE is cleared."""
        env = {
            "DATABRICKS_MCP_TOOLS_INCLUDE": "sql",
            "DATABRICKS_MCP_TOOLS_EXCLUDE": "compute",
        }
        with patch.dict(os.environ, env, clear=True):
            include, exclude = get_tool_filter()
            assert include == {"sql"}
            assert exclude is None

    def test_whitespace_trimmed(self) -> None:
        """Leading/trailing whitespace in comma-separated values is stripped."""
        with patch.dict(os.environ, {"DATABRICKS_MCP_TOOLS_INCLUDE": " sql , compute "}, clear=True):
            include, _ = get_tool_filter()
            assert include == {"sql", "compute"}

    def test_empty_string_returns_none(self) -> None:
        """An empty INCLUDE value produces None, not an empty set."""
        with patch.dict(os.environ, {"DATABRICKS_MCP_TOOLS_INCLUDE": ""}, clear=True):
            include, exclude = get_tool_filter()
            assert include is None
            assert exclude is None

    def test_empty_exclude_returns_none(self) -> None:
        """An empty EXCLUDE value produces None, not an empty set."""
        with patch.dict(os.environ, {"DATABRICKS_MCP_TOOLS_EXCLUDE": ""}, clear=True):
            include, exclude = get_tool_filter()
            assert include is None
            assert exclude is None

    def test_trailing_comma_ignored(self) -> None:
        """Trailing commas don't produce empty-string entries."""
        with patch.dict(os.environ, {"DATABRICKS_MCP_TOOLS_INCLUDE": "sql,compute,"}, clear=True):
            include, _ = get_tool_filter()
            assert include == {"sql", "compute"}


# ---------------------------------------------------------------------------
# is_module_enabled()
# ---------------------------------------------------------------------------

class TestIsModuleEnabled:
    """Verify per-module enablement checks."""

    def test_all_enabled_by_default(self) -> None:
        """No filters means every module is enabled."""
        with patch.dict(os.environ, {}, clear=True):
            assert is_module_enabled("sql") is True
            assert is_module_enabled("compute") is True
            assert is_module_enabled("anything") is True

    def test_include_filter_allows_listed(self) -> None:
        """Only modules in the INCLUDE list are enabled."""
        with patch.dict(os.environ, {"DATABRICKS_MCP_TOOLS_INCLUDE": "sql,compute"}, clear=True):
            assert is_module_enabled("sql") is True
            assert is_module_enabled("compute") is True
            assert is_module_enabled("jobs") is False
            assert is_module_enabled("genie") is False

    def test_exclude_filter_blocks_listed(self) -> None:
        """Modules in the EXCLUDE list are disabled; all others are enabled."""
        with patch.dict(os.environ, {"DATABRICKS_MCP_TOOLS_EXCLUDE": "genie,sharing"}, clear=True):
            assert is_module_enabled("genie") is False
            assert is_module_enabled("sharing") is False
            assert is_module_enabled("sql") is True
            assert is_module_enabled("compute") is True

    def test_include_overrides_exclude(self) -> None:
        """When both filters are set, only INCLUDE matters."""
        env = {
            "DATABRICKS_MCP_TOOLS_INCLUDE": "sql",
            "DATABRICKS_MCP_TOOLS_EXCLUDE": "sql",
        }
        with patch.dict(os.environ, env, clear=True):
            # sql is in INCLUDE, so it's enabled despite also being in EXCLUDE
            assert is_module_enabled("sql") is True
            # compute is not in INCLUDE, so it's disabled
            assert is_module_enabled("compute") is False

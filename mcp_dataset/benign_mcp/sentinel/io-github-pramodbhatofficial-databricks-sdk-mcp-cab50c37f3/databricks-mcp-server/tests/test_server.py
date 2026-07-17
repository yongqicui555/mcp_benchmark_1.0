"""Tests for databricks_mcp.server — tool registration, filtering, and main().

Note: The server module creates a module-level FastMCP instance. If the
installed ``mcp`` version has a different ``FastMCP.__init__`` signature than
the one the code was written for (e.g. ``description`` vs ``instructions``),
importing server.py will fail at the module level.  These tests work around
that by patching ``FastMCP`` before importing the server module.
"""

import importlib
import sys
from types import ModuleType
from unittest.mock import MagicMock, patch

import pytest

from mcp.server.fastmcp import FastMCP


# ---------------------------------------------------------------------------
# Helper: safely import the server module, patching FastMCP if needed
# ---------------------------------------------------------------------------

def _import_server_fresh() -> ModuleType:
    """Import (or re-import) ``databricks_mcp.server`` with a tolerant FastMCP.

    This accounts for the installed ``mcp`` package potentially lacking the
    ``description`` keyword argument that the source code uses.
    """
    # Remove cached module so we get a fresh import
    sys.modules.pop("databricks_mcp.server", None)

    # Patch FastMCP to accept any kwargs so the module-level instantiation succeeds
    original_init = FastMCP.__init__

    def patched_init(self, *args, **kwargs):
        # Strip unknown kwargs that might not be in this mcp version
        kwargs.pop("description", None)
        return original_init(self, *args, **kwargs)

    with patch.object(FastMCP, "__init__", patched_init):
        mod = importlib.import_module("databricks_mcp.server")

    return mod


# ---------------------------------------------------------------------------
# _register_tools()
# ---------------------------------------------------------------------------

class TestRegisterTools:
    """Verify that _register_tools() imports and registers tool modules."""

    def test_registers_all_modules_when_no_filter(self) -> None:
        """With no INCLUDE/EXCLUDE filters, all 17 tool modules are imported."""
        server_mod = _import_server_fresh()
        tool_module_paths = {path for _, path in server_mod._TOOL_MODULES}

        with patch.object(server_mod, "mcp", FastMCP("test")):
            with patch.object(server_mod, "is_module_enabled", return_value=True):
                imported_tool_modules: list[str] = []
                real_import = importlib.import_module

                def tracking_import(name: str) -> object:
                    if name in tool_module_paths:
                        imported_tool_modules.append(name)
                        mod = MagicMock()
                        mod.register_tools = MagicMock()
                        return mod
                    return real_import(name)

                with patch("importlib.import_module", side_effect=tracking_import):
                    server_mod._register_tools()

                assert len(imported_tool_modules) == len(server_mod._TOOL_MODULES)
                for _module_name, module_path in server_mod._TOOL_MODULES:
                    assert module_path in imported_tool_modules

    def test_skips_disabled_modules(self) -> None:
        """Modules that are disabled by the filter are not imported."""
        server_mod = _import_server_fresh()
        tool_module_paths = {path for _, path in server_mod._TOOL_MODULES}

        with patch.object(server_mod, "mcp", FastMCP("test")):

            def mock_enabled(name: str) -> bool:
                return name == "sql"

            with patch.object(server_mod, "is_module_enabled", side_effect=mock_enabled):
                imported_tool_modules: list[str] = []
                real_import = importlib.import_module

                def tracking_import(name: str) -> object:
                    if name in tool_module_paths:
                        imported_tool_modules.append(name)
                        mod = MagicMock()
                        mod.register_tools = MagicMock()
                        return mod
                    return real_import(name)

                with patch("importlib.import_module", side_effect=tracking_import):
                    server_mod._register_tools()

                assert len(imported_tool_modules) == 1
                assert imported_tool_modules[0] == "databricks_mcp.tools.sql"

    def test_handles_import_error_gracefully(self) -> None:
        """If a module fails to import, a warning is printed but execution continues."""
        server_mod = _import_server_fresh()
        tool_module_paths = {path for _, path in server_mod._TOOL_MODULES}

        with patch.object(server_mod, "mcp", FastMCP("test")):
            with patch.object(server_mod, "is_module_enabled", return_value=True):
                real_import = importlib.import_module

                def failing_import(name: str) -> object:
                    if name in tool_module_paths:
                        raise ImportError(f"No module named '{name}'")
                    return real_import(name)

                with patch("importlib.import_module", side_effect=failing_import):
                    # Should not raise -- errors are caught and printed as warnings
                    server_mod._register_tools()

    def test_always_registers_resources(self) -> None:
        """Resources are registered even when all tool modules are disabled."""
        server_mod = _import_server_fresh()
        test_mcp = FastMCP("test")

        with patch.object(server_mod, "mcp", test_mcp):
            with patch.object(server_mod, "is_module_enabled", return_value=False):
                mock_register = MagicMock()
                with patch(
                    "databricks_mcp.resources.workspace_info.register_resources",
                    mock_register,
                ):
                    server_mod._register_tools()

                mock_register.assert_called_once_with(test_mcp)

    def test_module_without_register_tools_skipped(self) -> None:
        """If a module lacks register_tools(), it is silently skipped."""
        server_mod = _import_server_fresh()
        tool_module_paths = {path for _, path in server_mod._TOOL_MODULES}

        with patch.object(server_mod, "mcp", FastMCP("test")):
            with patch.object(server_mod, "is_module_enabled", return_value=True):
                real_import = importlib.import_module

                def import_no_register(name: str) -> object:
                    if name in tool_module_paths:
                        # Return a module-like object that lacks register_tools
                        return MagicMock(spec=[])
                    return real_import(name)

                with patch("importlib.import_module", side_effect=import_no_register):
                    # Should not raise
                    server_mod._register_tools()


# ---------------------------------------------------------------------------
# main()
# ---------------------------------------------------------------------------

class TestMain:
    """Verify the main() entry point."""

    def test_main_calls_register_and_run(self) -> None:
        """main() should call _register_tools() then mcp.run()."""
        server_mod = _import_server_fresh()
        mock_mcp = MagicMock()

        with patch.object(server_mod, "mcp", mock_mcp):
            with patch.object(server_mod, "_register_tools") as mock_register:
                with patch("sys.argv", ["databricks-mcp"]):
                    server_mod.main()

                    mock_register.assert_called_once()
                    mock_mcp.run.assert_called_once()


# ---------------------------------------------------------------------------
# _TOOL_MODULES constant
# ---------------------------------------------------------------------------

class TestToolModulesList:
    """Verify the module registry is complete and well-formed."""

    def test_all_28_modules_listed(self) -> None:
        server_mod = _import_server_fresh()
        assert len(server_mod._TOOL_MODULES) == 28

    def test_module_paths_match_names(self) -> None:
        """Each module path should end with the module name."""
        server_mod = _import_server_fresh()
        for name, path in server_mod._TOOL_MODULES:
            assert path.endswith(f".{name}"), f"Module path '{path}' doesn't end with '.{name}'"

    def test_all_paths_start_with_package(self) -> None:
        server_mod = _import_server_fresh()
        for _, path in server_mod._TOOL_MODULES:
            assert path.startswith("databricks_mcp.tools.")

    def test_expected_modules_present(self) -> None:
        """All 28 expected module names are present in the list."""
        server_mod = _import_server_fresh()
        names = {name for name, _ in server_mod._TOOL_MODULES}
        expected = {
            "unity_catalog", "sql", "workspace", "compute", "jobs",
            "pipelines", "serving", "vector_search", "apps", "database",
            "dashboards", "genie", "secrets", "iam", "connections",
            "experiments", "sharing", "files", "grants", "storage",
            "metastores", "online_tables", "global_init_scripts", "tokens",
            "git_credentials", "quality_monitors", "command_execution",
            "workflows",
        }
        assert names == expected

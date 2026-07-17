"""Tests for databricks_mcp.tools.unity_catalog — Unity Catalog management tools.

Tests cover catalog, schema, table, volume, function, and registered model
operations.  Every tool is tested for its happy path (correct SDK method called)
and error handling (format_error return).
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from mcp.server.fastmcp import FastMCP

from databricks_mcp.tools.unity_catalog import register_tools


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_tool_fn(mcp: FastMCP, name: str):
    """Retrieve a registered tool's underlying function by name."""
    tool = mcp._tool_manager.get_tool(name)
    assert tool is not None, f"Tool '{name}' not found in registered tools"
    return tool.fn


def _tool_names(mcp: FastMCP) -> set[str]:
    """Return the set of all registered tool names."""
    return {t.name for t in mcp._tool_manager.list_tools()}


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class TestRegistration:
    """Verify register_tools() adds all expected tools."""

    def test_all_tools_registered(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        names = _tool_names(mcp)

        expected = {
            # Catalogs
            "databricks_list_catalogs",
            "databricks_get_catalog",
            "databricks_create_catalog",
            "databricks_delete_catalog",
            # Schemas
            "databricks_list_schemas",
            "databricks_get_schema",
            "databricks_create_schema",
            "databricks_delete_schema",
            # Tables
            "databricks_list_tables",
            "databricks_get_table",
            "databricks_delete_table",
            # Volumes
            "databricks_list_volumes",
            "databricks_create_volume",
            "databricks_delete_volume",
            # Functions
            "databricks_list_functions",
            "databricks_get_function",
            "databricks_delete_function",
            # Registered Models
            "databricks_list_registered_models",
            "databricks_get_registered_model",
        }
        assert expected.issubset(names), f"Missing tools: {expected - names}"


# ---------------------------------------------------------------------------
# Catalog tools
# ---------------------------------------------------------------------------

class TestCatalogTools:
    """Test catalog CRUD operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_catalogs(self) -> None:
        self.client.catalogs.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_catalogs")
        result = fn()
        self.client.catalogs.list.assert_called_once()
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed == []

    def test_get_catalog(self) -> None:
        mock_catalog = SimpleNamespace(name="my_catalog", owner="admin")
        self.client.catalogs.get.return_value = mock_catalog
        fn = _get_tool_fn(self.mcp, "databricks_get_catalog")
        result = fn(name="my_catalog")
        self.client.catalogs.get.assert_called_once_with("my_catalog")
        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["name"] == "my_catalog"

    def test_create_catalog(self) -> None:
        mock_result = SimpleNamespace(name="new_cat", owner="admin")
        self.client.catalogs.create.return_value = mock_result
        fn = _get_tool_fn(self.mcp, "databricks_create_catalog")
        result = fn(name="new_cat", comment="test catalog")
        self.client.catalogs.create.assert_called_once_with(name="new_cat", comment="test catalog")

    def test_create_catalog_default_comment(self) -> None:
        mock_result = SimpleNamespace(name="cat")
        self.client.catalogs.create.return_value = mock_result
        fn = _get_tool_fn(self.mcp, "databricks_create_catalog")
        result = fn(name="cat")
        self.client.catalogs.create.assert_called_once_with(name="cat", comment="")

    def test_delete_catalog(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_delete_catalog")
        result = fn(name="old_cat")
        self.client.catalogs.delete.assert_called_once_with("old_cat", force=False)
        assert "deleted successfully" in result

    def test_delete_catalog_force(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_delete_catalog")
        result = fn(name="old_cat", force=True)
        self.client.catalogs.delete.assert_called_once_with("old_cat", force=True)
        assert "deleted successfully" in result

    def test_list_catalogs_error(self) -> None:
        self.client.catalogs.list.side_effect = RuntimeError("connection failed")
        fn = _get_tool_fn(self.mcp, "databricks_list_catalogs")
        result = fn()
        assert "RuntimeError" in result
        assert "connection failed" in result

    def test_get_catalog_error_with_error_code(self) -> None:
        err = RuntimeError("not found")
        err.error_code = "RESOURCE_DOES_NOT_EXIST"  # type: ignore[attr-defined]
        self.client.catalogs.get.side_effect = err
        fn = _get_tool_fn(self.mcp, "databricks_get_catalog")
        result = fn(name="bad")
        assert "RESOURCE_DOES_NOT_EXIST" in result


# ---------------------------------------------------------------------------
# Schema tools
# ---------------------------------------------------------------------------

class TestSchemaTools:
    """Test schema CRUD operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_schemas(self) -> None:
        self.client.schemas.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_schemas")
        result = fn(catalog_name="my_catalog")
        self.client.schemas.list.assert_called_once_with(catalog_name="my_catalog")

    def test_get_schema(self) -> None:
        mock_schema = SimpleNamespace(name="my_schema", catalog_name="cat")
        self.client.schemas.get.return_value = mock_schema
        fn = _get_tool_fn(self.mcp, "databricks_get_schema")
        result = fn(full_name="cat.schema")
        self.client.schemas.get.assert_called_once_with("cat.schema")

    def test_create_schema(self) -> None:
        mock_result = SimpleNamespace(name="new_schema", catalog_name="cat")
        self.client.schemas.create.return_value = mock_result
        fn = _get_tool_fn(self.mcp, "databricks_create_schema")
        result = fn(name="new_schema", catalog_name="cat", comment="desc")
        self.client.schemas.create.assert_called_once_with(
            name="new_schema", catalog_name="cat", comment="desc"
        )

    def test_delete_schema(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_delete_schema")
        result = fn(full_name="cat.old_schema")
        self.client.schemas.delete.assert_called_once_with("cat.old_schema")
        assert "deleted successfully" in result

    def test_list_schemas_error(self) -> None:
        self.client.schemas.list.side_effect = ValueError("bad catalog")
        fn = _get_tool_fn(self.mcp, "databricks_list_schemas")
        result = fn(catalog_name="bad")
        assert "ValueError" in result


# ---------------------------------------------------------------------------
# Table tools
# ---------------------------------------------------------------------------

class TestTableTools:
    """Test table list, get, and delete operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_tables(self) -> None:
        self.client.tables.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_tables")
        result = fn(catalog_name="cat", schema_name="sch")
        self.client.tables.list.assert_called_once_with(catalog_name="cat", schema_name="sch")

    def test_get_table(self) -> None:
        mock_table = SimpleNamespace(name="tbl", table_type="MANAGED")
        self.client.tables.get.return_value = mock_table
        fn = _get_tool_fn(self.mcp, "databricks_get_table")
        result = fn(full_name="cat.sch.tbl")
        self.client.tables.get.assert_called_once_with("cat.sch.tbl")

    def test_delete_table(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_delete_table")
        result = fn(full_name="cat.sch.tbl")
        self.client.tables.delete.assert_called_once_with("cat.sch.tbl")
        assert "deleted successfully" in result


# ---------------------------------------------------------------------------
# Volume tools
# ---------------------------------------------------------------------------

class TestVolumeTools:
    """Test volume list, create, and delete operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_volumes(self) -> None:
        self.client.volumes.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_volumes")
        result = fn(catalog_name="cat", schema_name="sch")
        self.client.volumes.list.assert_called_once_with(catalog_name="cat", schema_name="sch")

    def test_create_volume(self) -> None:
        mock_result = SimpleNamespace(name="vol", catalog_name="cat", schema_name="sch")
        self.client.volumes.create.return_value = mock_result
        fn = _get_tool_fn(self.mcp, "databricks_create_volume")

        # Patch VolumeType since it's imported inside the function
        with patch("databricks.sdk.service.catalog.VolumeType") as MockVolumeType:
            MockVolumeType.return_value = "MANAGED"
            result = fn(name="vol", catalog_name="cat", schema_name="sch")
            self.client.volumes.create.assert_called_once_with(
                name="vol",
                catalog_name="cat",
                schema_name="sch",
                volume_type="MANAGED",
                comment="",
            )

    def test_delete_volume(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_delete_volume")
        result = fn(full_name="cat.sch.vol")
        self.client.volumes.delete.assert_called_once_with("cat.sch.vol")
        assert "deleted successfully" in result


# ---------------------------------------------------------------------------
# Function tools
# ---------------------------------------------------------------------------

class TestFunctionTools:
    """Test UDF list, get, and delete operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_functions(self) -> None:
        self.client.functions.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_functions")
        result = fn(catalog_name="cat", schema_name="sch")
        self.client.functions.list.assert_called_once_with(catalog_name="cat", schema_name="sch")

    def test_get_function(self) -> None:
        mock_func = SimpleNamespace(name="my_func", catalog_name="cat")
        self.client.functions.get.return_value = mock_func
        fn = _get_tool_fn(self.mcp, "databricks_get_function")
        result = fn(full_name="cat.sch.my_func")
        self.client.functions.get.assert_called_once_with("cat.sch.my_func")

    def test_delete_function(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_delete_function")
        result = fn(full_name="cat.sch.my_func")
        self.client.functions.delete.assert_called_once_with("cat.sch.my_func")
        assert "deleted successfully" in result


# ---------------------------------------------------------------------------
# Registered Model tools
# ---------------------------------------------------------------------------

class TestRegisteredModelTools:
    """Test registered model list and get operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_registered_models_no_filter(self) -> None:
        self.client.registered_models.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_registered_models")
        result = fn()
        # No kwargs when both catalog_name and schema_name are empty
        self.client.registered_models.list.assert_called_once_with()

    def test_list_registered_models_with_catalog(self) -> None:
        self.client.registered_models.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_registered_models")
        result = fn(catalog_name="cat")
        self.client.registered_models.list.assert_called_once_with(catalog_name="cat")

    def test_list_registered_models_with_catalog_and_schema(self) -> None:
        self.client.registered_models.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_registered_models")
        result = fn(catalog_name="cat", schema_name="sch")
        self.client.registered_models.list.assert_called_once_with(
            catalog_name="cat", schema_name="sch"
        )

    def test_get_registered_model(self) -> None:
        mock_model = SimpleNamespace(name="my_model", owner="admin")
        self.client.registered_models.get.return_value = mock_model
        fn = _get_tool_fn(self.mcp, "databricks_get_registered_model")
        result = fn(full_name="cat.sch.my_model")
        self.client.registered_models.get.assert_called_once_with("cat.sch.my_model")

    def test_list_registered_models_error(self) -> None:
        self.client.registered_models.list.side_effect = ConnectionError("timeout")
        fn = _get_tool_fn(self.mcp, "databricks_list_registered_models")
        result = fn()
        assert "ConnectionError" in result
        assert "timeout" in result

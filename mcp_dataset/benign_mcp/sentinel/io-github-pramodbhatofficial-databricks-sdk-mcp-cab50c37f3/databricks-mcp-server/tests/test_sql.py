"""Tests for databricks_mcp.tools.sql — SQL warehouse, statement, query, alert, and history tools.

Tests cover the key SQL operations: warehouse CRUD, SQL execution,
saved queries, alerts, and query history.
"""

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from mcp.server.fastmcp import FastMCP

from databricks_mcp.tools.sql import register_tools


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
    """Verify register_tools() adds all expected SQL tools."""

    def test_all_tools_registered(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        names = _tool_names(mcp)

        expected = {
            # Warehouses
            "databricks_list_warehouses",
            "databricks_get_warehouse",
            "databricks_create_warehouse",
            "databricks_start_warehouse",
            "databricks_stop_warehouse",
            "databricks_delete_warehouse",
            # Statement execution
            "databricks_execute_sql",
            "databricks_get_statement_status",
            "databricks_cancel_statement",
            # Queries
            "databricks_list_queries",
            "databricks_create_query",
            # Alerts
            "databricks_list_alerts",
            "databricks_create_alert",
            # History
            "databricks_list_query_history",
        }
        assert expected.issubset(names), f"Missing tools: {expected - names}"


# ---------------------------------------------------------------------------
# Warehouse tools
# ---------------------------------------------------------------------------

class TestWarehouseTools:
    """Test SQL warehouse CRUD and lifecycle operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_warehouses(self) -> None:
        self.client.warehouses.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_warehouses")
        result = fn()
        self.client.warehouses.list.assert_called_once()
        parsed = json.loads(result)
        assert parsed == []

    def test_get_warehouse(self) -> None:
        mock_wh = SimpleNamespace(id="abc123", name="dev-warehouse", state="RUNNING")
        self.client.warehouses.get.return_value = mock_wh
        fn = _get_tool_fn(self.mcp, "databricks_get_warehouse")
        result = fn(id="abc123")
        self.client.warehouses.get.assert_called_once_with("abc123")

    def test_create_warehouse_defaults(self) -> None:
        mock_result = SimpleNamespace(id="new-wh", name="test-wh")
        self.client.warehouses.create.return_value = mock_result
        fn = _get_tool_fn(self.mcp, "databricks_create_warehouse")
        result = fn(name="test-wh")
        self.client.warehouses.create.assert_called_once_with(
            name="test-wh",
            cluster_size="2X-Small",
            max_num_clusters=1,
            auto_stop_mins=15,
        )

    def test_create_warehouse_custom(self) -> None:
        mock_result = SimpleNamespace(id="new-wh", name="big-wh")
        self.client.warehouses.create.return_value = mock_result
        fn = _get_tool_fn(self.mcp, "databricks_create_warehouse")
        result = fn(name="big-wh", cluster_size="Large", max_num_clusters=5, auto_stop_mins=30)
        self.client.warehouses.create.assert_called_once_with(
            name="big-wh",
            cluster_size="Large",
            max_num_clusters=5,
            auto_stop_mins=30,
        )

    def test_start_warehouse(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_start_warehouse")
        result = fn(id="wh-1")
        self.client.warehouses.start.assert_called_once_with("wh-1")
        assert "start initiated" in result

    def test_stop_warehouse(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_stop_warehouse")
        result = fn(id="wh-1")
        self.client.warehouses.stop.assert_called_once_with("wh-1")
        assert "stop initiated" in result

    def test_delete_warehouse(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_delete_warehouse")
        result = fn(id="wh-1")
        self.client.warehouses.delete.assert_called_once_with("wh-1")
        assert "deleted successfully" in result

    def test_list_warehouses_error(self) -> None:
        self.client.warehouses.list.side_effect = RuntimeError("auth failed")
        fn = _get_tool_fn(self.mcp, "databricks_list_warehouses")
        result = fn()
        assert "RuntimeError" in result
        assert "auth failed" in result


# ---------------------------------------------------------------------------
# Statement Execution tools
# ---------------------------------------------------------------------------

class TestStatementExecutionTools:
    """Test SQL statement execution, status, and cancellation."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_execute_sql_minimal(self) -> None:
        """Execute SQL with only required arguments."""
        mock_result = SimpleNamespace(status="SUCCEEDED", data=[[1, 2]])
        self.client.statement_execution.execute_statement.return_value = mock_result

        fn = _get_tool_fn(self.mcp, "databricks_execute_sql")

        with patch("databricks.sdk.service.sql.Disposition") as MockDisp, \
             patch("databricks.sdk.service.sql.Format") as MockFmt:
            MockDisp.INLINE = "INLINE"
            MockFmt.JSON_ARRAY = "JSON_ARRAY"
            result = fn(warehouse_id="wh-1", statement="SELECT 1")

        self.client.statement_execution.execute_statement.assert_called_once()
        call_kwargs = self.client.statement_execution.execute_statement.call_args[1]
        assert call_kwargs["warehouse_id"] == "wh-1"
        assert call_kwargs["statement"] == "SELECT 1"
        assert call_kwargs["wait_timeout"] == "50s"
        # catalog and schema should NOT be in kwargs when empty
        assert "catalog" not in call_kwargs
        assert "schema" not in call_kwargs

    def test_execute_sql_with_catalog_and_schema(self) -> None:
        """Execute SQL with optional catalog and schema."""
        mock_result = SimpleNamespace(status="SUCCEEDED")
        self.client.statement_execution.execute_statement.return_value = mock_result

        fn = _get_tool_fn(self.mcp, "databricks_execute_sql")

        with patch("databricks.sdk.service.sql.Disposition") as MockDisp, \
             patch("databricks.sdk.service.sql.Format") as MockFmt:
            MockDisp.INLINE = "INLINE"
            MockFmt.JSON_ARRAY = "JSON_ARRAY"
            result = fn(
                warehouse_id="wh-1",
                statement="SELECT * FROM t",
                catalog="my_cat",
                schema="my_sch",
            )

        call_kwargs = self.client.statement_execution.execute_statement.call_args[1]
        assert call_kwargs["catalog"] == "my_cat"
        assert call_kwargs["schema"] == "my_sch"

    def test_execute_sql_error(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_execute_sql")
        with patch("databricks.sdk.service.sql.Disposition") as MockDisp, \
             patch("databricks.sdk.service.sql.Format") as MockFmt:
            MockDisp.INLINE = "INLINE"
            MockFmt.JSON_ARRAY = "JSON_ARRAY"
            self.client.statement_execution.execute_statement.side_effect = RuntimeError("warehouse not found")
            result = fn(warehouse_id="bad", statement="SELECT 1")

        assert "RuntimeError" in result
        assert "warehouse not found" in result

    def test_get_statement_status(self) -> None:
        mock_result = SimpleNamespace(status="RUNNING")
        self.client.statement_execution.get_statement.return_value = mock_result
        fn = _get_tool_fn(self.mcp, "databricks_get_statement_status")
        result = fn(statement_id="stmt-1")
        self.client.statement_execution.get_statement.assert_called_once_with("stmt-1")

    def test_cancel_statement(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_cancel_statement")
        result = fn(statement_id="stmt-1")
        self.client.statement_execution.cancel_execution.assert_called_once_with("stmt-1")
        assert "Cancellation requested" in result


# ---------------------------------------------------------------------------
# Saved Query tools
# ---------------------------------------------------------------------------

class TestQueryTools:
    """Test saved SQL query operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_queries(self) -> None:
        self.client.queries.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_queries")
        result = fn()
        self.client.queries.list.assert_called_once()

    def test_create_query(self) -> None:
        mock_result = SimpleNamespace(id="q-1", display_name="my query")
        self.client.queries.create.return_value = mock_result

        fn = _get_tool_fn(self.mcp, "databricks_create_query")
        with patch("databricks.sdk.service.sql.CreateQueryRequestQuery") as MockQuery:
            MockQuery.return_value = "query_obj"
            result = fn(
                name="my query",
                query_text="SELECT * FROM t",
                warehouse_id="wh-1",
                description="desc",
            )
            MockQuery.assert_called_once_with(
                display_name="my query",
                query_text="SELECT * FROM t",
                warehouse_id="wh-1",
                description="desc",
            )
        self.client.queries.create.assert_called_once_with(query="query_obj")


# ---------------------------------------------------------------------------
# Alert tools
# ---------------------------------------------------------------------------

class TestAlertTools:
    """Test SQL alert operations."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_alerts(self) -> None:
        self.client.alerts.list.return_value = iter([])
        fn = _get_tool_fn(self.mcp, "databricks_list_alerts")
        result = fn()
        self.client.alerts.list.assert_called_once()

    def test_create_alert(self) -> None:
        mock_result = SimpleNamespace(id="alert-1", name="my alert")
        self.client.alerts.create.return_value = mock_result

        fn = _get_tool_fn(self.mcp, "databricks_create_alert")
        result = fn(name="my alert", query_id="q-1", condition="value > 100")
        # The condition parameter is described but not passed to the SDK in the current impl
        self.client.alerts.create.assert_called_once_with(name="my alert", query_id="q-1")


# ---------------------------------------------------------------------------
# Query History tools
# ---------------------------------------------------------------------------

class TestQueryHistoryTools:
    """Test query history listing."""

    @pytest.fixture(autouse=True)
    def _register(self, mcp: FastMCP, patched_client: MagicMock) -> None:
        register_tools(mcp)
        self.mcp = mcp
        self.client = patched_client

    def test_list_query_history_no_filter(self) -> None:
        mock_result = SimpleNamespace(res=[])
        self.client.query_history.list.return_value = mock_result

        fn = _get_tool_fn(self.mcp, "databricks_list_query_history")
        # ListQueryHistoryRequest may not exist in all SDK versions; create=True
        # allows the patch to succeed even if the attribute is missing.
        with patch("databricks.sdk.service.sql.ListQueryHistoryRequest", create=True) as MockReq, \
             patch("databricks.sdk.service.sql.QueryFilter"):
            MockReq.return_value = "request_obj"
            result = fn()
            # max_results defaults to 25
            MockReq.assert_called_once_with(max_results=25)
        self.client.query_history.list.assert_called_once_with("request_obj")

    def test_list_query_history_with_warehouse(self) -> None:
        mock_result = SimpleNamespace(res=[])
        self.client.query_history.list.return_value = mock_result

        fn = _get_tool_fn(self.mcp, "databricks_list_query_history")
        with patch("databricks.sdk.service.sql.ListQueryHistoryRequest", create=True) as MockReq, \
             patch("databricks.sdk.service.sql.QueryFilter") as MockFilter:
            MockReq.return_value = "request_obj"
            MockFilter.return_value = "filter_obj"
            result = fn(warehouse_id="wh-1", max_results=10)
            MockFilter.assert_called_once_with(warehouse_ids=["wh-1"])
            MockReq.assert_called_once_with(filter_by="filter_obj", max_results=10)

    def test_list_query_history_max_results_capped(self) -> None:
        """max_results is capped at 25 even if a higher value is passed."""
        mock_result = SimpleNamespace(res=[])
        self.client.query_history.list.return_value = mock_result

        fn = _get_tool_fn(self.mcp, "databricks_list_query_history")
        with patch("databricks.sdk.service.sql.ListQueryHistoryRequest", create=True) as MockReq, \
             patch("databricks.sdk.service.sql.QueryFilter"):
            MockReq.return_value = "request_obj"
            result = fn(max_results=100)
            MockReq.assert_called_once_with(max_results=25)

    def test_list_query_history_error(self) -> None:
        fn = _get_tool_fn(self.mcp, "databricks_list_query_history")
        with patch("databricks.sdk.service.sql.ListQueryHistoryRequest", create=True) as MockReq, \
             patch("databricks.sdk.service.sql.QueryFilter"):
            MockReq.return_value = "request_obj"
            self.client.query_history.list.side_effect = RuntimeError("forbidden")
            result = fn()
        assert "RuntimeError" in result
        assert "forbidden" in result

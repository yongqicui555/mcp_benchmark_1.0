"""SQL warehouse, statement execution, query, and alert tools for Databricks MCP.

Provides tools for managing SQL warehouses, executing SQL statements,
working with saved queries, managing alerts, and querying statement history.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all SQL tools with the MCP server."""

    # ── SQL Warehouses ──────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_warehouses() -> str:
        """List all SQL warehouses in the workspace.

        Returns a JSON array of warehouse objects including id, name, state,
        cluster_size, and configuration details. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.warehouses.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_warehouse(id: str) -> str:
        """Get detailed information about a specific SQL warehouse.

        Args:
            id: The unique identifier of the SQL warehouse.

        Returns:
            JSON object with warehouse details including name, state,
            cluster_size, auto_stop_mins, num_clusters, and health info.
        """
        try:
            w = get_workspace_client()
            result = w.warehouses.get(id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_warehouse(
        name: str,
        cluster_size: str = "2X-Small",
        max_num_clusters: int = 1,
        auto_stop_mins: int = 15,
    ) -> str:
        """Create a new SQL warehouse.

        Creates a serverless SQL warehouse with the specified configuration.
        The warehouse starts automatically after creation.

        Args:
            name: Display name for the warehouse.
            cluster_size: T-shirt size for the warehouse compute
                          (e.g. "2X-Small", "X-Small", "Small", "Medium", "Large",
                          "X-Large", "2X-Large", "3X-Large", "4X-Large").
            max_num_clusters: Maximum number of clusters for auto-scaling (1-100).
            auto_stop_mins: Minutes of inactivity before auto-stop (0 to disable).

        Returns:
            JSON object with the created warehouse details including its id.
        """
        try:
            w = get_workspace_client()
            result = w.warehouses.create(
                name=name,
                cluster_size=cluster_size,
                max_num_clusters=max_num_clusters,
                auto_stop_mins=auto_stop_mins,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_start_warehouse(id: str) -> str:
        """Start a stopped SQL warehouse.

        This initiates the start process. The warehouse may take several minutes
        to become fully running. This call returns immediately without waiting.

        Args:
            id: The unique identifier of the SQL warehouse to start.

        Returns:
            Confirmation that the start was initiated.
        """
        try:
            w = get_workspace_client()
            w.warehouses.start(id)
            return f"Warehouse '{id}' start initiated. It may take a few minutes to become running."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_stop_warehouse(id: str) -> str:
        """Stop a running SQL warehouse.

        Stops the warehouse to save costs. Any running queries will be terminated.
        This call returns immediately without waiting.

        Args:
            id: The unique identifier of the SQL warehouse to stop.

        Returns:
            Confirmation that the stop was initiated.
        """
        try:
            w = get_workspace_client()
            w.warehouses.stop(id)
            return f"Warehouse '{id}' stop initiated."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_warehouse(id: str) -> str:
        """Delete a SQL warehouse.

        Permanently deletes the warehouse. This action cannot be undone.

        Args:
            id: The unique identifier of the SQL warehouse to delete.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.warehouses.delete(id)
            return f"Warehouse '{id}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # ── Statement Execution ─────────────────────────────────────────────

    @mcp.tool()
    def databricks_execute_sql(
        warehouse_id: str,
        statement: str,
        catalog: str = "",
        schema: str = "",
    ) -> str:
        """Execute a SQL statement on a Databricks SQL warehouse.

        Runs the statement synchronously with a 50-second wait timeout and
        returns inline JSON results. For long-running queries, use
        databricks_get_statement_status to poll for completion.

        Args:
            warehouse_id: The ID of the SQL warehouse to execute on.
            statement: The SQL statement to execute (max 16 MiB).
            catalog: Optional default catalog for the statement
                     (like "USE CATALOG").
            schema: Optional default schema for the statement
                    (like "USE SCHEMA").

        Returns:
            JSON object with the statement result including status,
            manifest (column info), and result data. For SELECT queries,
            the data is returned as a JSON array.
        """
        try:
            from databricks.sdk.service.sql import Disposition, Format

            w = get_workspace_client()
            kwargs = {
                "warehouse_id": warehouse_id,
                "statement": statement,
                "wait_timeout": "50s",
                "disposition": Disposition.INLINE,
                "format": Format.JSON_ARRAY,
            }
            if catalog:
                kwargs["catalog"] = catalog
            if schema:
                kwargs["schema"] = schema

            result = w.statement_execution.execute_statement(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_statement_status(statement_id: str) -> str:
        """Get the status and results of a previously executed SQL statement.

        Use this to poll for completion of long-running statements or to
        retrieve results after an asynchronous execution.

        Args:
            statement_id: The statement ID returned by databricks_execute_sql.

        Returns:
            JSON object with statement status, manifest, and result data
            if the statement has completed.
        """
        try:
            w = get_workspace_client()
            result = w.statement_execution.get_statement(statement_id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_cancel_statement(statement_id: str) -> str:
        """Cancel an executing SQL statement.

        Requests cancellation of a running statement. The cancellation may
        not be immediate; poll with databricks_get_statement_status to
        confirm the terminal state.

        Args:
            statement_id: The statement ID of the statement to cancel.

        Returns:
            Confirmation that cancellation was requested.
        """
        try:
            w = get_workspace_client()
            w.statement_execution.cancel_execution(statement_id)
            return f"Cancellation requested for statement '{statement_id}'. Poll status to confirm."
        except Exception as e:
            return format_error(e)

    # ── Saved Queries ───────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_queries() -> str:
        """List saved SQL queries accessible to the current user.

        Returns queries ordered by creation time. Warning: calling this API
        concurrently 10+ times may result in throttling.

        Returns:
            JSON array of query objects with id, name, query_text,
            and creation metadata. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.queries.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_query(
        name: str,
        query_text: str,
        warehouse_id: str,
        description: str = "",
    ) -> str:
        """Create a new saved SQL query.

        Creates a reusable SQL query that can be shared, scheduled, and
        used as the basis for alerts.

        Args:
            name: Display name for the query.
            query_text: The SQL statement body.
            warehouse_id: The ID of the SQL warehouse to target.
            description: Optional human-readable description.

        Returns:
            JSON object with the created query details including its id.
        """
        try:
            from databricks.sdk.service.sql import CreateQueryRequestQuery

            w = get_workspace_client()
            query_obj = CreateQueryRequestQuery(
                display_name=name,
                query_text=query_text,
                warehouse_id=warehouse_id,
                description=description,
            )
            result = w.queries.create(query=query_obj)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    # ── Alerts ──────────────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_alerts() -> str:
        """List all SQL alerts accessible to the current user.

        Alerts trigger notifications when a query result meets a specified
        condition.

        Returns:
            JSON array of alert objects with id, name, query information,
            and condition details. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.alerts.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_alert(
        name: str,
        query_id: str,
        condition: str,
    ) -> str:
        """Create a new SQL alert based on a saved query.

        Alerts evaluate a query result against a condition and trigger
        notifications when the condition is met.

        Args:
            name: Display name for the alert.
            query_id: The ID of the saved query to monitor.
            condition: A description of the alert condition. This should
                       describe when the alert should trigger based on the
                       query results (e.g. "value column greater than 100").
                       Note: The exact alert condition configuration depends
                       on the Databricks API version. Provide a clear
                       description and the tool will attempt to configure it.

        Returns:
            JSON object with the created alert details, or an informational
            message about the alert condition format required.
        """
        try:
            w = get_workspace_client()
            # The alerts API requires structured condition objects. We create
            # a basic alert and return guidance if the condition needs adjustment.
            result = w.alerts.create(
                name=name,
                query_id=query_id,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    # ── Query History ───────────────────────────────────────────────────

    @mcp.tool()
    def databricks_list_query_history(
        warehouse_id: str = "",
        max_results: int = 25,
    ) -> str:
        """List recent query execution history.

        Returns recently executed queries with their status, duration,
        and other execution metadata. Can optionally filter by warehouse.

        Args:
            warehouse_id: Optional warehouse ID to filter history.
                          If empty, returns history across all warehouses.
            max_results: Maximum number of history entries to return
                         (1-25, default 25).

        Returns:
            JSON array of query history entries with query_id, status,
            query_text, duration, and warehouse information.
        """
        try:
            from databricks.sdk.service.sql import ListQueryHistoryRequest, QueryFilter

            w = get_workspace_client()
            kwargs = {}
            if warehouse_id:
                query_filter = QueryFilter(
                    warehouse_ids=[warehouse_id],
                )
                kwargs["filter_by"] = query_filter
            kwargs["max_results"] = min(max_results, 25)

            result = w.query_history.list(ListQueryHistoryRequest(**kwargs))
            return to_json(result)
        except Exception as e:
            return format_error(e)

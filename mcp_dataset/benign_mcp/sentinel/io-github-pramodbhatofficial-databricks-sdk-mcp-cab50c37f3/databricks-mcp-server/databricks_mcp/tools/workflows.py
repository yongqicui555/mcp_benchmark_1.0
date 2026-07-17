"""High-level workflow tools that combine multiple Databricks operations.

These composite tools reduce round-trips by performing several SDK calls
in a single invocation, making common multi-step workflows more efficient.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register composite workflow tools with the MCP server."""

    @mcp.tool()
    def databricks_workspace_status() -> str:
        """Get a comprehensive status overview of the Databricks workspace.

        Returns a health dashboard showing the status of clusters, warehouses,
        jobs, serving endpoints, and catalog access -- all in one call.
        """
        try:
            w = get_workspace_client()
            status: dict = {}

            # Auth check
            try:
                me = w.current_user.me()
                status["auth"] = {"status": "ok", "user": me.user_name}
            except Exception as e:
                status["auth"] = {"status": "error", "error": str(e)}

            # Clusters
            try:
                clusters = list(w.clusters.list())
                running = [
                    c for c in clusters
                    if hasattr(c, "state") and str(getattr(c, "state", "")).upper() == "RUNNING"
                ]
                status["clusters"] = {
                    "total": len(clusters),
                    "running": len(running),
                    "terminated": len(clusters) - len(running),
                }
            except Exception:
                status["clusters"] = {"status": "unavailable"}

            # SQL Warehouses
            try:
                warehouses = list(w.warehouses.list())
                active = [
                    wh for wh in warehouses
                    if hasattr(wh, "state") and str(getattr(wh, "state", "")).upper() == "RUNNING"
                ]
                status["sql_warehouses"] = {
                    "total": len(warehouses),
                    "running": len(active),
                }
            except Exception:
                status["sql_warehouses"] = {"status": "unavailable"}

            # Jobs (capped at 100 to avoid large responses)
            try:
                jobs = paginate(w.jobs.list(), max_items=100)
                status["jobs"] = {"total": len(jobs)}
            except Exception:
                status["jobs"] = {"status": "unavailable"}

            # Serving endpoints
            try:
                endpoints = list(w.serving_endpoints.list())
                ready = [
                    ep for ep in endpoints
                    if hasattr(ep, "state")
                    and hasattr(ep.state, "ready")
                    and str(getattr(ep.state, "ready", "")).upper() == "READY"
                ]
                status["serving_endpoints"] = {
                    "total": len(endpoints),
                    "ready": len(ready),
                }
            except Exception:
                status["serving_endpoints"] = {"status": "unavailable"}

            # Unity Catalogs (capped at 50)
            try:
                catalogs = paginate(w.catalogs.list(), max_items=50)
                status["catalogs"] = {"total": len(catalogs)}
            except Exception:
                status["catalogs"] = {"status": "unavailable"}

            return to_json(status)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_setup_schema(
        catalog_name: str,
        schema_name: str,
        comment: str = "",
        create_catalog: bool = False,
    ) -> str:
        """Create a catalog (optionally) and schema in one step.

        Useful for quickly setting up a new data area. Creates the catalog
        if requested, then creates the schema within it.

        Args:
            catalog_name: Name of the parent catalog.
            schema_name: Name of the schema to create.
            comment: Optional description for the schema.
            create_catalog: If True, create the catalog first (skips if it already exists).
        """
        try:
            w = get_workspace_client()
            results: dict = {"steps": []}

            if create_catalog:
                try:
                    w.catalogs.create(name=catalog_name)
                    results["steps"].append({
                        "action": "create_catalog",
                        "status": "created",
                        "name": catalog_name,
                    })
                except Exception as e:
                    if "already exists" in str(e).lower():
                        results["steps"].append({
                            "action": "create_catalog",
                            "status": "already_exists",
                            "name": catalog_name,
                        })
                    else:
                        raise

            kwargs: dict = {"name": schema_name, "catalog_name": catalog_name}
            if comment:
                kwargs["comment"] = comment
            w.schemas.create(**kwargs)
            results["steps"].append({
                "action": "create_schema",
                "status": "created",
                "full_name": f"{catalog_name}.{schema_name}",
            })
            results["schema"] = {
                "catalog": catalog_name,
                "schema": schema_name,
                "full_name": f"{catalog_name}.{schema_name}",
            }

            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_query_as_markdown(
        warehouse_id: str,
        sql: str,
        catalog: str = "",
        schema: str = "",
    ) -> str:
        """Execute a SQL query and return results formatted as a markdown table.

        Combines SQL execution with result formatting for easy display.
        Results are limited to 100 rows.

        Args:
            warehouse_id: ID of the SQL warehouse to use.
            sql: The SQL statement to execute.
            catalog: Optional catalog context for the query.
            schema: Optional schema context for the query.
        """
        try:
            from databricks.sdk.service.sql import Disposition, Format

            w = get_workspace_client()
            kwargs: dict = {
                "warehouse_id": warehouse_id,
                "statement": sql,
                "disposition": Disposition.INLINE,
                "format": Format.JSON_ARRAY,
                "wait_timeout": "50s",
            }
            if catalog:
                kwargs["catalog"] = catalog
            if schema:
                kwargs["schema"] = schema

            response = w.statement_execution.execute_statement(**kwargs)

            # Extract columns and data from the response
            result = response.result
            if not result or not result.data_array:
                return "Query returned no results."

            columns = (
                [col.name for col in result.manifest.schema.columns]
                if result.manifest
                else []
            )
            rows = result.data_array

            if not columns:
                return to_json(response)

            # Build a markdown-formatted table
            max_rows = 100
            header = "| " + " | ".join(columns) + " |"
            separator = "| " + " | ".join(["---"] * len(columns)) + " |"
            body_rows = []
            for row in rows[:max_rows]:
                cells = [str(v) if v is not None else "NULL" for v in row]
                body_rows.append("| " + " | ".join(cells) + " |")

            table = "\n".join([header, separator, *body_rows])

            meta = f"\n\n*{len(rows)} rows returned"
            if len(rows) > max_rows:
                meta += f" (showing first {max_rows})"
            meta += "*"

            return table + meta
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_find_and_start_warehouse() -> str:
        """Find an available SQL warehouse and start it if needed.

        Looks for running warehouses first. If none are running, finds a
        stopped warehouse and starts it. Returns the warehouse ID ready for queries.
        """
        try:
            w = get_workspace_client()
            warehouses = list(w.warehouses.list())

            if not warehouses:
                return to_json({"error": "No SQL warehouses found in workspace. Create one first."})

            # Prefer an already-running warehouse
            for wh in warehouses:
                state = str(getattr(wh, "state", "")).upper()
                if state == "RUNNING":
                    return to_json({
                        "warehouse_id": wh.id,
                        "name": wh.name,
                        "state": "RUNNING",
                        "message": f"Warehouse '{wh.name}' is already running and ready for queries.",
                    })

            # No running warehouse found; start the first stopped one
            for wh in warehouses:
                state = str(getattr(wh, "state", "")).upper()
                if state in ("STOPPED", "STOPPING"):
                    w.warehouses.start(id=wh.id)
                    return to_json({
                        "warehouse_id": wh.id,
                        "name": wh.name,
                        "state": "STARTING",
                        "message": f"Starting warehouse '{wh.name}'. Check status with databricks_get_warehouse.",
                    })

            # All warehouses are in transitional states
            return to_json({
                "warehouses": [
                    {"id": wh.id, "name": wh.name, "state": str(getattr(wh, "state", "unknown"))}
                    for wh in warehouses
                ],
                "message": "No startable warehouses found. All are in transitional states.",
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_table_preview(
        table_name: str,
        warehouse_id: str = "",
        limit: int = 10,
    ) -> str:
        """Preview a table's schema and sample data in one call.

        Gets the table metadata (columns, types) and runs a SELECT query
        to show sample rows. If no warehouse_id is provided, finds a running
        warehouse automatically.

        Args:
            table_name: Full three-level table name (catalog.schema.table).
            warehouse_id: SQL warehouse ID to use. If empty, finds one automatically.
            limit: Number of sample rows to return. Defaults to 10.
        """
        try:
            from databricks.sdk.service.sql import Disposition, Format

            w = get_workspace_client()
            result: dict = {"table_name": table_name}

            # Get table metadata (columns, types)
            try:
                table_info = w.tables.get(table_name)
                if table_info.columns:
                    result["columns"] = [
                        {
                            "name": col.name,
                            "type": str(
                                getattr(col, "type_name", getattr(col, "type_text", "unknown"))
                            ),
                        }
                        for col in table_info.columns
                    ]
                    result["column_count"] = len(table_info.columns)
            except Exception:
                result["metadata"] = "Could not retrieve table metadata"

            # Resolve a warehouse ID if the caller did not provide one
            wh_id = warehouse_id
            if not wh_id:
                warehouses = list(w.warehouses.list())
                for wh in warehouses:
                    if str(getattr(wh, "state", "")).upper() == "RUNNING":
                        wh_id = wh.id
                        break

            if not wh_id:
                result["sample_data"] = (
                    "No running SQL warehouse found. Provide a warehouse_id or start one."
                )
                return to_json(result)

            # Query sample rows
            response = w.statement_execution.execute_statement(
                warehouse_id=wh_id,
                statement=f"SELECT * FROM {table_name} LIMIT {limit}",
                disposition=Disposition.INLINE,
                format=Format.JSON_ARRAY,
                wait_timeout="30s",
            )
            if response.result and response.result.data_array:
                columns = (
                    [col.name for col in response.result.manifest.schema.columns]
                    if response.result.manifest
                    else []
                )
                result["sample_data"] = {
                    "columns": columns,
                    "rows": response.result.data_array[:limit],
                    "row_count": len(response.result.data_array),
                }
            else:
                result["sample_data"] = "No data returned"

            return to_json(result)
        except Exception as e:
            return format_error(e)

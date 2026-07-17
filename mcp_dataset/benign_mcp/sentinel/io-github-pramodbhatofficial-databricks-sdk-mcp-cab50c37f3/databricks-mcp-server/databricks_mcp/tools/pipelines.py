"""Tools for managing Databricks DLT (Delta Live Tables) / Lakeflow pipelines.

DLT pipelines define declarative data transformations that automatically manage
data quality, schema evolution, and incremental processing. Pipelines can run
in triggered mode (one-time refresh) or continuous mode (streaming).

Each pipeline consists of one or more libraries (notebooks or files) that define
the transformation logic using DLT-specific APIs.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all DLT pipeline management tools with the MCP server."""

    @mcp.tool()
    def databricks_list_pipelines(max_results: int = 25) -> str:
        """List DLT pipelines in the workspace.

        Returns summary information for each pipeline including name, ID,
        state (IDLE, RUNNING, FAILED), target schema, and creation time.

        Args:
            max_results: Maximum number of pipelines to return. Defaults to 25.
        """
        try:
            w = get_workspace_client()
            pipelines = paginate(
                w.pipelines.list_pipelines(max_results=max_results),
                max_items=max_results,
            )
            return to_json({"pipelines": pipelines, "count": len(pipelines)})
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_pipeline(pipeline_id: str) -> str:
        """Get detailed information about a specific DLT pipeline.

        Returns the full pipeline configuration including name, target schema,
        catalog, libraries, clusters, current state, last update status, and
        health metrics.

        Args:
            pipeline_id: The unique identifier of the pipeline (UUID format).
        """
        try:
            w = get_workspace_client()
            pipeline = w.pipelines.get(pipeline_id)
            return to_json(pipeline)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_pipeline(
        name: str,
        target: str = "",
        catalog: str = "",
        notebook_path: str = "",
        continuous: bool = False,
    ) -> str:
        """Create a new DLT pipeline.

        Creates a pipeline that runs transformation logic defined in a notebook.
        The pipeline manages the lifecycle of the output Delta tables automatically.

        For Unity Catalog pipelines, provide both catalog and target (schema).
        For Hive metastore pipelines, provide only target (schema name).

        Args:
            name: Human-readable name for the pipeline.
            target: Target schema name where output tables are created. For Unity
                    Catalog, this is the schema within the specified catalog.
                    For Hive metastore, this is the database name.
            catalog: Unity Catalog catalog name. When set, the pipeline publishes
                     tables to Unity Catalog under catalog.target. Leave empty for
                     Hive metastore pipelines.
            notebook_path: Workspace path to the notebook containing DLT
                           transformation definitions (e.g.
                           "/Users/user@example.com/etl_pipeline"). If empty,
                           the pipeline is created without libraries and must
                           be configured separately.
            continuous: If True, the pipeline runs continuously in streaming mode,
                        processing new data as it arrives. If False (default), the
                        pipeline runs in triggered mode (one-time refresh per update).
        """
        try:
            from databricks.sdk.service.pipelines import (
                NotebookLibrary,
                PipelineLibrary,
            )

            w = get_workspace_client()

            kwargs: dict = {
                "name": name,
                "continuous": continuous,
            }

            if target:
                kwargs["target"] = target
            if catalog:
                kwargs["catalog"] = catalog

            # Add notebook as a pipeline library if provided
            if notebook_path:
                kwargs["libraries"] = [
                    PipelineLibrary(
                        notebook=NotebookLibrary(path=notebook_path)
                    )
                ]

            result = w.pipelines.create(**kwargs)
            return to_json({
                "pipeline_id": result.pipeline_id,
                "name": name,
                "continuous": continuous,
                "message": (
                    f"Pipeline '{name}' created with ID {result.pipeline_id}. "
                    "Use databricks_start_pipeline to trigger the first update."
                ),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_pipeline(
        pipeline_id: str,
        name: str = "",
        target: str = "",
        catalog: str = "",
    ) -> str:
        """Update an existing DLT pipeline configuration.

        Modifies the pipeline's metadata fields. Only non-empty parameters are
        updated; empty strings are ignored. To modify libraries or cluster config,
        use the Databricks UI or API directly.

        Note: The pipeline must be stopped before updating. If the pipeline is
        running, stop it first with databricks_stop_pipeline.

        Args:
            pipeline_id: The unique identifier of the pipeline to update.
            name: New name for the pipeline. Leave empty to keep the current name.
            target: New target schema. Leave empty to keep the current target.
            catalog: New Unity Catalog catalog. Leave empty to keep the current catalog.
        """
        try:
            w = get_workspace_client()

            kwargs: dict = {"pipeline_id": pipeline_id}
            if name:
                kwargs["name"] = name
            if target:
                kwargs["target"] = target
            if catalog:
                kwargs["catalog"] = catalog

            # Only proceed if there is something to update
            if len(kwargs) == 1:
                return to_json({
                    "status": "no_change",
                    "pipeline_id": pipeline_id,
                    "message": "No fields to update. Provide at least one of: name, target, catalog.",
                })

            w.pipelines.update(**kwargs)
            return to_json({
                "status": "updated",
                "pipeline_id": pipeline_id,
                "updated_fields": {k: v for k, v in kwargs.items() if k != "pipeline_id"},
                "message": f"Pipeline {pipeline_id} updated successfully.",
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_pipeline(pipeline_id: str) -> str:
        """Delete a DLT pipeline.

        Permanently removes the pipeline definition. If the pipeline is running,
        it is stopped first. The output Delta tables created by the pipeline are
        NOT deleted. This action cannot be undone.

        Args:
            pipeline_id: The unique identifier of the pipeline to delete.
        """
        try:
            w = get_workspace_client()
            w.pipelines.delete(pipeline_id)
            return to_json({
                "status": "deleted",
                "pipeline_id": pipeline_id,
                "message": (
                    f"Pipeline {pipeline_id} has been deleted. "
                    "Output tables were not affected."
                ),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_start_pipeline(pipeline_id: str, full_refresh: bool = False) -> str:
        """Start a pipeline update (data refresh).

        Triggers the pipeline to process data. The update runs asynchronously --
        this tool returns immediately without waiting for completion. Use
        databricks_get_pipeline to check the pipeline state.

        Args:
            pipeline_id: The unique identifier of the pipeline to start.
            full_refresh: If True, reprocesses all data from scratch, dropping and
                          recreating all output tables. If False (default), performs
                          an incremental update processing only new or changed data.
                          Use full_refresh when schema changes have been made or
                          data needs to be recomputed.
        """
        try:
            w = get_workspace_client()
            response = w.pipelines.start_update(
                pipeline_id=pipeline_id,
                full_refresh=full_refresh,
            )
            return to_json({
                "status": "started",
                "pipeline_id": pipeline_id,
                "update_id": getattr(response, "update_id", None),
                "full_refresh": full_refresh,
                "message": (
                    f"Pipeline {pipeline_id} update started"
                    f"{' (full refresh)' if full_refresh else ''}. "
                    "Use databricks_get_pipeline to check progress."
                ),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_stop_pipeline(pipeline_id: str) -> str:
        """Stop a running pipeline.

        Sends a stop request to the pipeline. The pipeline finishes processing
        its current micro-batch (if any) and then stops. For continuous pipelines,
        this halts streaming. For triggered pipelines, this cancels the current
        update.

        Args:
            pipeline_id: The unique identifier of the pipeline to stop.
        """
        try:
            w = get_workspace_client()
            w.pipelines.stop(pipeline_id)
            return to_json({
                "status": "stopping",
                "pipeline_id": pipeline_id,
                "message": (
                    f"Stop request sent for pipeline {pipeline_id}. "
                    "Use databricks_get_pipeline to verify it has stopped."
                ),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_pipeline_events(pipeline_id: str, max_results: int = 25) -> str:
        """List recent events for a DLT pipeline.

        Returns pipeline events in reverse chronological order. Events include
        update starts/completions, data quality violations, errors, schema changes,
        and flow progress. Useful for monitoring and debugging pipeline behavior.

        Args:
            pipeline_id: The unique identifier of the pipeline.
            max_results: Maximum number of events to return. Defaults to 25.
        """
        try:
            w = get_workspace_client()
            events = paginate(
                w.pipelines.list_pipeline_events(
                    pipeline_id=pipeline_id,
                    max_results=max_results,
                ),
                max_items=max_results,
            )
            return to_json({
                "pipeline_id": pipeline_id,
                "events": events,
                "count": len(events),
            })
        except Exception as e:
            return format_error(e)

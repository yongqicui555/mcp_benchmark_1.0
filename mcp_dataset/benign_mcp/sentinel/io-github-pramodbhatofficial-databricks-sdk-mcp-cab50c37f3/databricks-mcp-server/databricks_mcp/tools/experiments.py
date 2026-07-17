"""MLflow experiment and run management tools for Databricks MCP.

Provides tools for managing MLflow experiments and runs tracked within the
Databricks workspace. Experiments group related ML training runs, and each
run tracks parameters, metrics, artifacts, and model outputs.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all MLflow experiment tools with the MCP server."""

    # -- Experiments -----------------------------------------------------------

    @mcp.tool()
    def databricks_list_experiments(max_results: int = 25) -> str:
        """List MLflow experiments in the workspace.

        Returns experiments ordered by creation time (newest first). Each
        experiment contains one or more runs that track ML training iterations.

        Args:
            max_results: Maximum number of experiments to return (default 25).

        Returns:
            JSON array of experiment objects, each containing experiment_id,
            name, artifact_location, lifecycle_stage, last_update_time,
            and creation_time.
        """
        try:
            w = get_workspace_client()
            results = paginate(
                w.experiments.list_experiments(max_results=max_results),
                max_items=max_results,
            )
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_experiment(experiment_id: str) -> str:
        """Get detailed information about a specific MLflow experiment.

        Args:
            experiment_id: The numeric ID of the experiment to retrieve
                           (e.g. "123456789").

        Returns:
            JSON object with full experiment details including experiment_id,
            name, artifact_location, lifecycle_stage, tags, and timestamps.
        """
        try:
            w = get_workspace_client()
            result = w.experiments.get_experiment(experiment_id=experiment_id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_experiment(name: str, artifact_location: str = "") -> str:
        """Create a new MLflow experiment.

        Creates an experiment as a container for ML training runs. The name
        must be unique and typically follows a path-like convention
        (e.g. "/Users/user@example.com/my-experiment").

        Args:
            name: Unique name for the experiment. Workspace experiments
                  typically use paths like "/Users/email/experiment-name"
                  or "/Shared/team/experiment-name".
            artifact_location: Optional root artifact URI for the experiment.
                               If not provided, the default workspace artifact
                               location is used. Example:
                               "dbfs:/databricks/mlflow-tracking/12345".

        Returns:
            JSON object with the created experiment's experiment_id.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {"name": name}
            if artifact_location:
                kwargs["artifact_location"] = artifact_location
            result = w.experiments.create_experiment(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_experiment(experiment_id: str) -> str:
        """Mark an MLflow experiment as deleted (soft delete).

        The experiment is moved to a trash state and can be restored within
        the retention period. All runs within the experiment are also marked
        as deleted. The caller must be the experiment owner or a workspace
        admin.

        Args:
            experiment_id: The numeric ID of the experiment to delete.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.experiments.delete_experiment(experiment_id=experiment_id)
            return f"Experiment '{experiment_id}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # -- Runs ------------------------------------------------------------------

    @mcp.tool()
    def databricks_search_runs(
        experiment_ids: str,
        filter_string: str = "",
        max_results: int = 25,
        order_by: str = "",
    ) -> str:
        """Search for MLflow runs across one or more experiments.

        Supports filtering by metrics, parameters, tags, and run attributes
        using the MLflow search syntax.

        Args:
            experiment_ids: Comma-separated list of experiment IDs to search
                            within (e.g. "123,456,789").
            filter_string: Optional MLflow filter expression. Examples:
                           - 'metrics.rmse < 0.5'
                           - 'params.learning_rate = "0.01"'
                           - 'tags.mlflow.source.type = "NOTEBOOK"'
                           - 'attributes.status = "FINISHED"'
                           Leave empty to return all runs.
            max_results: Maximum number of runs to return (default 25).
            order_by: Optional comma-separated list of columns to order by.
                      Prefix with "+" for ascending or "-" for descending.
                      Examples: "metrics.rmse ASC", "start_time DESC".

        Returns:
            JSON array of run objects, each containing run_id, experiment_id,
            status, start_time, end_time, metrics, params, and tags.
        """
        try:
            w = get_workspace_client()
            ids = [eid.strip() for eid in experiment_ids.split(",") if eid.strip()]
            kwargs: dict = {
                "experiment_ids": ids,
                "max_results": max_results,
            }
            if filter_string:
                kwargs["filter_string"] = filter_string
            if order_by:
                kwargs["order_by"] = [col.strip() for col in order_by.split(",") if col.strip()]
            results = paginate(w.experiments.search_runs(**kwargs), max_items=max_results)
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_run(run_id: str) -> str:
        """Get detailed information about a specific MLflow run.

        Args:
            run_id: The UUID of the run to retrieve (e.g.
                    "a1b2c3d4e5f6a7b8c9d0e1f2a3b4c5d6").

        Returns:
            JSON object with full run details including run_id, experiment_id,
            status, start_time, end_time, metrics, params, tags, and
            artifact_uri.
        """
        try:
            w = get_workspace_client()
            result = w.experiments.get_run(run_id=run_id)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    # -- Run Logging -----------------------------------------------------------

    @mcp.tool()
    def databricks_log_metric(run_id: str, key: str, value: float, step: int = 0) -> str:
        """Log a metric value for an MLflow run.

        Metrics are numeric measurements that track model performance over time.
        Multiple values can be logged for the same key at different steps to
        record training curves and convergence behavior.

        Args:
            run_id: The UUID of the run to log the metric to.
            key: Name of the metric (e.g. "rmse", "accuracy", "loss").
            value: Numeric value of the metric at this step.
            step: Optional integer step number for tracking metrics over time.
                  Defaults to 0. Use sequential step values to record training
                  progress (e.g. epoch number or batch count).

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.experiments.log_metric(run_id=run_id, key=key, value=value, step=step)
            return f"Metric '{key}={value}' logged at step {step} for run '{run_id}'."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_log_param(run_id: str, key: str, value: str) -> str:
        """Log a parameter for an MLflow run.

        Parameters are key-value pairs that capture the configuration used
        for a training run (e.g. hyperparameters, data paths, model type).
        Each key can only be logged once per run.

        Args:
            run_id: The UUID of the run to log the parameter to.
            key: Name of the parameter (e.g. "learning_rate", "batch_size",
                 "model_type").
            value: String value of the parameter. Numeric values should be
                   passed as strings (e.g. "0.001", "32").

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.experiments.log_param(run_id=run_id, key=key, value=value)
            return f"Parameter '{key}={value}' logged for run '{run_id}'."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_run(
        experiment_id: str,
        run_name: str = "",
        start_time: int = 0,
    ) -> str:
        """Create a new MLflow run within an experiment.

        Creates a run to track an ML training iteration. After creation,
        use databricks_log_metric and databricks_log_param to record
        metrics and parameters, and databricks_update_run to mark the
        run as finished.

        Args:
            experiment_id: The numeric ID of the experiment to create the
                           run in.
            run_name: Optional display name for the run. If empty, MLflow
                      assigns a random name.
            start_time: Optional Unix timestamp in milliseconds for the
                        run start time. If 0, the current time is used.

        Returns:
            JSON object with the created run's details including run_id.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {"experiment_id": experiment_id}
            if run_name:
                kwargs["run_name"] = run_name
            if start_time > 0:
                kwargs["start_time"] = start_time
            result = w.experiments.create_run(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_run(
        run_id: str,
        status: str = "",
        end_time: int = 0,
    ) -> str:
        """Update the status of an MLflow run.

        Typically used to mark a run as FINISHED, FAILED, or KILLED after
        training completes. Can also set the end time.

        Args:
            run_id: The UUID of the run to update.
            status: New status for the run. Valid values: "RUNNING",
                    "SCHEDULED", "FINISHED", "FAILED", "KILLED".
                    If empty, the status is not changed.
            end_time: Optional Unix timestamp in milliseconds for the run
                      end time. If 0, the end time is not set.

        Returns:
            JSON object with the updated run info.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {"run_id": run_id}
            if status:
                from databricks.sdk.service.ml import UpdateRunStatus
                kwargs["status"] = UpdateRunStatus(status)
            if end_time > 0:
                kwargs["end_time"] = end_time
            result = w.experiments.update_run(**kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_run(run_id: str) -> str:
        """Mark an MLflow run as deleted (soft delete).

        The run is moved to a trash state and can be restored within the
        retention period. The caller must be the run owner or a workspace
        admin.

        Args:
            run_id: The UUID of the run to delete.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.experiments.delete_run(run_id=run_id)
            return f"Run '{run_id}' deleted successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_restore_experiment(experiment_id: str) -> str:
        """Restore a previously deleted MLflow experiment.

        Recovers an experiment that was soft-deleted via
        databricks_delete_experiment. All runs within the experiment
        are also restored.

        Args:
            experiment_id: The numeric ID of the experiment to restore.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.experiments.restore_experiment(experiment_id=experiment_id)
            return f"Experiment '{experiment_id}' restored successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_search_experiments(
        filter_string: str = "",
        max_results: int = 25,
    ) -> str:
        """Search for MLflow experiments using filter expressions.

        Supports filtering by experiment attributes and tags using the
        MLflow search syntax.

        Args:
            filter_string: Optional filter expression. Examples:
                           - 'name = "my-experiment"'
                           - 'tags.team = "ml-eng"'
                           - 'attributes.lifecycle_stage = "active"'
                           Leave empty to return all experiments.
            max_results: Maximum number of experiments to return
                         (default 25).

        Returns:
            JSON array of matching experiment objects with experiment_id,
            name, artifact_location, lifecycle_stage, and tags.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {"max_results": max_results}
            if filter_string:
                kwargs["filter_string"] = filter_string
            results = paginate(
                w.experiments.search_experiments(**kwargs),
                max_items=max_results,
            )
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_artifacts(run_id: str, path: str = "") -> str:
        """List artifacts associated with an MLflow run.

        Returns the files and directories stored as artifacts for the
        specified run. Artifacts include model files, data files, plots,
        and any other files logged during the run.

        Args:
            run_id: The UUID of the run whose artifacts to list.
            path: Optional relative path within the artifact directory.
                  If empty, lists artifacts at the root level.

        Returns:
            JSON array of artifact objects, each containing file_path,
            is_dir, and file_size.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {"run_id": run_id}
            if path:
                kwargs["path"] = path
            results = paginate(w.experiments.list_artifacts(**kwargs))
            return to_json({"run_id": run_id, "artifacts": results, "count": len(results)})
        except Exception as e:
            return format_error(e)

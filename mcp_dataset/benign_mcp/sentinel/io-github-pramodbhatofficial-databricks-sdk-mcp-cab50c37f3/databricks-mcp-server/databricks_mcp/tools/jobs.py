"""Tools for managing Databricks Jobs and Runs.

Jobs are the primary mechanism for scheduling and orchestrating data processing,
ML training, and ETL workloads on Databricks. Each job consists of one or more
tasks that can run notebooks, Python scripts, JARs, or SQL queries.

Runs represent individual executions of a job, either triggered manually,
by schedule, or via API.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all job and run management tools with the MCP server."""

    @mcp.tool()
    def databricks_list_jobs(limit: int = 25, name: str = "") -> str:
        """List jobs in the workspace.

        Returns job definitions including name, schedule, tasks, and cluster
        configuration. Results are paginated; use the limit parameter to control
        how many jobs are returned.

        Args:
            limit: Maximum number of jobs to return. Must be between 1 and 100.
                   Defaults to 25.
            name: Optional filter to return only jobs whose name contains this
                  string (case-insensitive partial match).
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {}
            if name:
                kwargs["name"] = name
            jobs = paginate(w.jobs.list(**kwargs), max_items=limit)
            return to_json({"jobs": jobs, "count": len(jobs)})
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_job(job_id: int) -> str:
        """Get detailed information about a specific job.

        Returns the full job definition including all tasks, cluster configuration,
        schedule, email notifications, and access control settings.

        Args:
            job_id: The unique numeric identifier of the job.
        """
        try:
            w = get_workspace_client()
            job = w.jobs.get(job_id)
            return to_json(job)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_job(
        name: str,
        task_key: str,
        notebook_path: str = "",
        python_file: str = "",
        cluster_id: str = "",
    ) -> str:
        """Create a new job with a single task.

        Creates a simple job with either a notebook task or a Python script task.
        Exactly one of notebook_path or python_file must be provided.

        For more complex job configurations (multi-task, schedules, etc.), use the
        Databricks UI or API directly.

        Args:
            name: Human-readable name for the job. Does not need to be unique.
            task_key: Unique key for the task within this job. Used to identify
                      the task in multi-task jobs and in run output. Must consist
                      of alphanumeric characters, dashes, and underscores.
            notebook_path: Workspace path to the notebook to run (e.g.
                           "/Users/user@example.com/my_notebook"). Provide this
                           for notebook tasks. Mutually exclusive with python_file.
            python_file: Path to a Python file in DBFS, workspace, or cloud storage
                         (e.g. "dbfs:/scripts/etl.py"). Provide this for Spark
                         Python tasks. Mutually exclusive with notebook_path.
            cluster_id: ID of an existing all-purpose cluster to run the task on.
                        If omitted, the job will require a job cluster or serverless
                        compute configuration to be added separately.
        """
        try:
            from databricks.sdk.service.jobs import (
                NotebookTask,
                SparkPythonTask,
                Task,
            )

            w = get_workspace_client()

            # Validate that exactly one task type is specified
            if notebook_path and python_file:
                return format_error(ValueError(
                    "Provide either notebook_path or python_file, not both."
                ))
            if not notebook_path and not python_file:
                return format_error(ValueError(
                    "Provide either notebook_path or python_file."
                ))

            # Build the task definition
            task_kwargs: dict = {
                "task_key": task_key,
            }
            if cluster_id:
                task_kwargs["existing_cluster_id"] = cluster_id

            if notebook_path:
                task_kwargs["notebook_task"] = NotebookTask(notebook_path=notebook_path)
            else:
                task_kwargs["spark_python_task"] = SparkPythonTask(python_file=python_file)

            job = w.jobs.create(
                name=name,
                tasks=[Task(**task_kwargs)],
            )
            return to_json({
                "job_id": job.job_id,
                "name": name,
                "task_key": task_key,
                "message": f"Job '{name}' created successfully with ID {job.job_id}.",
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_job(job_id: int) -> str:
        """Delete a job and all its associated runs.

        Permanently removes the job definition. Active runs are cancelled.
        This action cannot be undone.

        Args:
            job_id: The unique numeric identifier of the job to delete.
        """
        try:
            w = get_workspace_client()
            w.jobs.delete(job_id)
            return to_json({
                "status": "deleted",
                "job_id": job_id,
                "message": f"Job {job_id} has been deleted.",
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_run_job(job_id: int) -> str:
        """Trigger a new run of an existing job.

        Starts the job immediately with its default parameters. The run executes
        asynchronously -- this tool returns the run ID without waiting for
        completion. Use databricks_get_run to check run status.

        Args:
            job_id: The unique numeric identifier of the job to run.
        """
        try:
            w = get_workspace_client()
            waiter = w.jobs.run_now(job_id)
            return to_json({
                "status": "triggered",
                "run_id": waiter.run_id,
                "job_id": job_id,
                "message": (
                    f"Job {job_id} triggered. Run ID: {waiter.run_id}. "
                    "Use databricks_get_run to check status."
                ),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_runs(job_id: int = 0, limit: int = 25) -> str:
        """List job runs, optionally filtered by job ID.

        Returns runs in descending order by start time. Each run includes
        status, start/end times, task results, and error messages if any.

        Args:
            job_id: Filter runs to this specific job. If 0 or omitted, returns
                    runs across all jobs.
            limit: Maximum number of runs to return. Must be between 1 and 100.
                   Defaults to 25.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {"limit": min(limit, 25)}
            if job_id > 0:
                kwargs["job_id"] = job_id
            runs = paginate(w.jobs.list_runs(**kwargs), max_items=limit)
            return to_json({"runs": runs, "count": len(runs)})
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_run(run_id: int) -> str:
        """Get detailed information about a specific job run.

        Returns the full run details including state (PENDING, RUNNING,
        TERMINATED, SKIPPED, INTERNAL_ERROR), task results, cluster info,
        start/end times, and any error messages.

        Args:
            run_id: The unique numeric identifier of the run.
        """
        try:
            w = get_workspace_client()
            run = w.jobs.get_run(run_id)
            return to_json(run)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_cancel_run(run_id: int) -> str:
        """Cancel an active job run.

        Sends a cancellation request. The run is cancelled asynchronously,
        so it may still appear as RUNNING briefly after this call. This tool
        returns immediately without waiting for the run to terminate.

        Args:
            run_id: The unique numeric identifier of the run to cancel.
        """
        try:
            w = get_workspace_client()
            w.jobs.cancel_run(run_id)
            # Return immediately without blocking on .result()
            return to_json({
                "status": "cancelling",
                "run_id": run_id,
                "message": (
                    f"Cancellation requested for run {run_id}. "
                    "Use databricks_get_run to verify termination."
                ),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_run_output(run_id: int) -> str:
        """Get the output of a completed job run.

        Returns the output produced by the run, which varies by task type:
        - Notebook tasks: notebook output and exit value
        - Python tasks: stdout/stderr logs
        - SQL tasks: query results

        Only available for completed runs.

        Args:
            run_id: The unique numeric identifier of the run.
        """
        try:
            w = get_workspace_client()
            output = w.jobs.get_run_output(run_id)
            return to_json(output)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_export_run(run_id: int) -> str:
        """Export the content of a job run.

        Exports the run's notebook content (for notebook tasks) in HTML format.
        This includes cell outputs, visualizations, and any dashboard views
        generated during the run.

        Args:
            run_id: The unique numeric identifier of the run to export.
        """
        try:
            w = get_workspace_client()
            export = w.jobs.export_run(run_id)
            return to_json(export)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_job(job_id: int, new_settings: str) -> str:
        """Update the settings of an existing job.

        Replaces the job settings with the provided configuration. Use
        databricks_get_job to retrieve the current settings, modify them,
        and pass the updated JSON back.

        Args:
            job_id: The unique numeric identifier of the job to update.
            new_settings: JSON string containing the new job settings.
                          Must be a valid JobSettings object serialized as JSON.
                          Example: '{"name": "updated-job", "timeout_seconds": 3600}'
        """
        try:
            from databricks.sdk.service.jobs import JobSettings

            w = get_workspace_client()
            parsed = json.loads(new_settings)
            settings = JobSettings.from_dict(parsed)
            w.jobs.update(job_id=job_id, new_settings=settings)
            return to_json({
                "status": "updated",
                "job_id": job_id,
                "message": f"Job {job_id} settings have been updated.",
            })
        except json.JSONDecodeError as e:
            return format_error(ValueError(f"Invalid JSON in 'new_settings' parameter: {e}"))
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_cancel_all_runs(job_id: int) -> str:
        """Cancel all active runs of a job.

        Sends cancellation requests for all currently active runs of the
        specified job. Runs are cancelled asynchronously, so they may
        still appear as RUNNING briefly after this call.

        Args:
            job_id: The unique numeric identifier of the job whose runs
                    should be cancelled.
        """
        try:
            w = get_workspace_client()
            w.jobs.cancel_all_runs(job_id=job_id)
            return to_json({
                "status": "cancelling",
                "job_id": job_id,
                "message": (
                    f"Cancellation requested for all active runs of job {job_id}. "
                    "Use databricks_list_runs to verify termination."
                ),
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_repair_run(run_id: int, rerun_tasks: str = "") -> str:
        """Repair a failed job run by re-running specific tasks.

        Re-executes failed or skipped tasks within a completed run. This is
        useful for recovering from transient failures without re-running the
        entire job. Only tasks in a FAILED, TIMED_OUT, or CANCELED state
        can be repaired.

        Args:
            run_id: The unique numeric identifier of the run to repair.
            rerun_tasks: Comma-separated list of task keys to re-run
                         (e.g. "task_1,task_2,task_3"). If empty, all
                         failed tasks are re-run.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {"run_id": run_id}
            if rerun_tasks:
                kwargs["rerun_tasks"] = [t.strip() for t in rerun_tasks.split(",") if t.strip()]
            result = w.jobs.repair_run(**kwargs)
            return to_json({
                "status": "repairing",
                "run_id": run_id,
                "repair_id": getattr(result, "repair_id", None),
                "message": (
                    f"Repair initiated for run {run_id}. "
                    "Use databricks_get_run to check progress."
                ),
            })
        except Exception as e:
            return format_error(e)

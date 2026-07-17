"""Command execution tools for Databricks MCP.

Provides tools for creating execution contexts on running clusters and
executing commands interactively. This enables running Python, SQL, Scala,
and R code on a cluster through the Databricks Command Execution API.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all command execution tools with the MCP server."""

    # ── Execution Contexts ───────────────────────────────────────────────

    @mcp.tool()
    def databricks_create_execution_context(
        cluster_id: str,
        language: str = "python",
    ) -> str:
        """Create an execution context on a running cluster.

        An execution context is a stateful session on a cluster where
        commands can be executed. Variables and state persist across
        commands within the same context. The cluster must be in the
        RUNNING state.

        Args:
            cluster_id: The unique identifier of a running cluster.
            language: Programming language for the context. One of
                      "python", "sql", "scala", or "r". Defaults to
                      "python".

        Returns:
            JSON object with the context details including id (the
            context_id to use in subsequent commands).
        """
        try:
            from databricks.sdk.service.compute import Language

            w = get_workspace_client()
            result = w.command_execution.create(
                cluster_id=cluster_id,
                language=Language(language),
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_execute_command(
        cluster_id: str,
        context_id: str,
        language: str,
        command: str,
    ) -> str:
        """Execute a command in an existing execution context.

        Submits a command for asynchronous execution on the cluster.
        Returns immediately with a command ID that can be polled for
        status and results using databricks_command_status.

        Args:
            cluster_id: The unique identifier of the cluster.
            context_id: The execution context ID returned by
                        databricks_create_execution_context.
            language: Programming language of the command. One of
                      "python", "sql", "scala", or "r".
            command: The code to execute (e.g. "print('hello')" for
                     Python or "SELECT 1" for SQL).

        Returns:
            JSON object with the command submission details including
            id (the command_id to check status with).
        """
        try:
            from databricks.sdk.service.compute import Language

            w = get_workspace_client()
            result = w.command_execution.execute(
                cluster_id=cluster_id,
                context_id=context_id,
                language=Language(language),
                command=command,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_command_status(
        cluster_id: str,
        context_id: str,
        command_id: str,
    ) -> str:
        """Check the status and results of an executed command.

        Polls the execution status of a previously submitted command.
        When the command completes, the response includes the output
        results or error details.

        Args:
            cluster_id: The unique identifier of the cluster.
            context_id: The execution context ID.
            command_id: The command ID returned by databricks_execute_command.

        Returns:
            JSON object with status (Queued, Running, Cancelling,
            Finished, Cancelled, Error) and results when available.
            Results include data, result_type, and any error information.
        """
        try:
            w = get_workspace_client()
            result = w.command_execution.command_status(
                cluster_id=cluster_id,
                context_id=context_id,
                command_id=command_id,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_destroy_execution_context(
        cluster_id: str,
        context_id: str,
    ) -> str:
        """Destroy an execution context on a cluster.

        Releases the resources associated with the context. Any running
        commands in the context will be cancelled. It is good practice
        to destroy contexts when they are no longer needed.

        Args:
            cluster_id: The unique identifier of the cluster.
            context_id: The execution context ID to destroy.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.command_execution.destroy(
                cluster_id=cluster_id,
                context_id=context_id,
            )
            return f"Execution context '{context_id}' on cluster '{cluster_id}' destroyed successfully."
        except Exception as e:
            return format_error(e)

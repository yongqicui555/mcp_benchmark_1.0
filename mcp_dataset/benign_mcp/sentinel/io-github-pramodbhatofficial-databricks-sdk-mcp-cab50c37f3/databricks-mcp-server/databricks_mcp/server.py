"""Databricks MCP Server — comprehensive tool access to all Databricks services."""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import is_module_enabled

mcp = FastMCP(
    "databricks",
    description="Comprehensive MCP server for Databricks. Provides tools for Unity Catalog, SQL, "
    "compute, jobs, pipelines, serving endpoints, vector search, apps, Lakebase, dashboards, "
    "Genie, secrets, IAM, connections, experiments, Delta Sharing, files (DBFS & Volumes), "
    "grants, storage credentials, external locations, metastores, online tables, global init "
    "scripts, tokens, Git credentials, quality monitors, and command execution.",
)

# Register tool modules conditionally based on DATABRICKS_MCP_TOOLS_INCLUDE/EXCLUDE
_TOOL_MODULES = [
    ("unity_catalog", "databricks_mcp.tools.unity_catalog"),
    ("sql", "databricks_mcp.tools.sql"),
    ("workspace", "databricks_mcp.tools.workspace"),
    ("compute", "databricks_mcp.tools.compute"),
    ("jobs", "databricks_mcp.tools.jobs"),
    ("pipelines", "databricks_mcp.tools.pipelines"),
    ("serving", "databricks_mcp.tools.serving"),
    ("vector_search", "databricks_mcp.tools.vector_search"),
    ("apps", "databricks_mcp.tools.apps"),
    ("database", "databricks_mcp.tools.database"),
    ("dashboards", "databricks_mcp.tools.dashboards"),
    ("genie", "databricks_mcp.tools.genie"),
    ("secrets", "databricks_mcp.tools.secrets"),
    ("iam", "databricks_mcp.tools.iam"),
    ("connections", "databricks_mcp.tools.connections"),
    ("experiments", "databricks_mcp.tools.experiments"),
    ("sharing", "databricks_mcp.tools.sharing"),
    ("files", "databricks_mcp.tools.files"),
    ("grants", "databricks_mcp.tools.grants"),
    ("storage", "databricks_mcp.tools.storage"),
    ("metastores", "databricks_mcp.tools.metastores"),
    ("online_tables", "databricks_mcp.tools.online_tables"),
    ("global_init_scripts", "databricks_mcp.tools.global_init_scripts"),
    ("tokens", "databricks_mcp.tools.tokens"),
    ("git_credentials", "databricks_mcp.tools.git_credentials"),
    ("quality_monitors", "databricks_mcp.tools.quality_monitors"),
    ("command_execution", "databricks_mcp.tools.command_execution"),
    ("workflows", "databricks_mcp.tools.workflows"),
]


def _register_tools() -> None:
    """Import and register all enabled tool modules."""
    import importlib

    for module_name, module_path in _TOOL_MODULES:
        if is_module_enabled(module_name):
            try:
                mod = importlib.import_module(module_path)
                # Each module has a register_tools(mcp) function
                if hasattr(mod, "register_tools"):
                    mod.register_tools(mcp)
            except ImportError as e:
                import sys

                print(f"Warning: Failed to import {module_path}: {e}", file=sys.stderr)

    # Always register resources
    from databricks_mcp.resources.workspace_info import register_resources

    register_resources(mcp)

    # Always register prompt templates
    from databricks_mcp.prompts import register_prompts

    register_prompts(mcp)


def main() -> None:
    """Entry point for the databricks-mcp command."""
    import argparse

    parser = argparse.ArgumentParser(description="Databricks MCP Server")
    parser.add_argument(
        "--transport",
        choices=["stdio", "sse"],
        default="stdio",
        help="Transport protocol (default: stdio)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8080,
        help="Port for SSE transport (default: 8080)",
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host for SSE transport (default: 0.0.0.0)",
    )
    args = parser.parse_args()

    _register_tools()

    if args.transport == "sse":
        # Configure host/port on the FastMCP settings before starting SSE
        mcp.settings.host = args.host
        mcp.settings.port = args.port
        mcp.run(transport="sse")
    else:
        mcp.run()


if __name__ == "__main__":
    main()

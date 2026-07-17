"""MCP resources providing read-only Databricks workspace context and tool discovery."""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, to_json

# Tool catalog: maps each module to its description and common tasks
_TOOL_CATALOG = {
    "unity_catalog": {
        "description": "Catalogs, schemas, tables, volumes, functions, registered models",
        "use_when": [
            "exploring data assets",
            "creating or managing catalogs/schemas/tables",
            "managing ML model registry",
            "browsing the data lakehouse",
        ],
    },
    "sql": {
        "description": "SQL warehouses, statement execution, queries, alerts, history",
        "use_when": [
            "running SQL queries",
            "managing SQL warehouses (start/stop/create)",
            "checking query history",
            "creating saved queries or alerts",
        ],
    },
    "workspace": {
        "description": "Notebooks, workspace files, directories, Git repos",
        "use_when": [
            "browsing workspace objects",
            "importing/exporting notebooks",
            "managing Git repos in the workspace",
        ],
    },
    "compute": {
        "description": "Clusters, instance pools, cluster policies, node types",
        "use_when": [
            "creating or managing compute clusters",
            "starting/stopping/resizing clusters",
            "managing instance pools",
            "checking available node types or Spark versions",
        ],
    },
    "jobs": {
        "description": "Jobs, runs, task orchestration",
        "use_when": [
            "creating or scheduling jobs",
            "triggering job runs",
            "monitoring run status",
            "repairing failed runs",
        ],
    },
    "pipelines": {
        "description": "DLT / Lakeflow declarative pipelines",
        "use_when": [
            "managing Delta Live Tables pipelines",
            "starting/stopping pipeline updates",
            "checking pipeline events",
        ],
    },
    "serving": {
        "description": "Model serving endpoints, model versions, OpenAPI specs",
        "use_when": [
            "deploying ML models for inference",
            "querying serving endpoints",
            "managing model serving configurations",
        ],
    },
    "vector_search": {
        "description": "Vector search endpoints and indexes (DELTA_SYNC, DIRECT_ACCESS)",
        "use_when": [
            "building RAG applications",
            "creating or querying vector indexes",
            "similarity search over embeddings",
        ],
    },
    "apps": {
        "description": "Databricks Apps lifecycle (create, deploy, start, stop)",
        "use_when": [
            "deploying web applications on Databricks",
            "managing app deployments",
            "checking app status",
        ],
    },
    "database": {
        "description": "Lakebase PostgreSQL instances, catalogs, tables, credentials",
        "use_when": [
            "managing Lakebase PostgreSQL databases",
            "creating database instances",
            "generating database credentials",
        ],
    },
    "dashboards": {
        "description": "Lakeview AI/BI dashboards (create, publish, migrate)",
        "use_when": [
            "creating or managing AI/BI dashboards",
            "publishing dashboards",
            "migrating classic dashboards to Lakeview",
        ],
    },
    "genie": {
        "description": "Genie AI/BI natural language conversations",
        "use_when": [
            "asking natural language questions about data",
            "using Genie spaces for data exploration",
        ],
    },
    "secrets": {
        "description": "Secret scopes, secrets, ACLs",
        "use_when": [
            "storing sensitive credentials",
            "managing secret scopes and access control",
        ],
    },
    "iam": {
        "description": "Users, groups, service principals, permissions, current user",
        "use_when": [
            "managing workspace users and groups",
            "setting object permissions",
            "managing service principals",
            "checking who the current user is",
        ],
    },
    "connections": {
        "description": "External connections (Lakehouse Federation)",
        "use_when": [
            "connecting to external databases",
            "managing Lakehouse Federation connections",
        ],
    },
    "experiments": {
        "description": "MLflow experiments, runs, metrics, params, artifacts",
        "use_when": [
            "tracking ML experiments",
            "logging metrics and parameters",
            "searching experiment runs",
            "managing ML model lifecycle",
        ],
    },
    "sharing": {
        "description": "Delta Sharing shares, recipients, providers",
        "use_when": [
            "sharing data across organizations",
            "managing Delta Sharing recipients and providers",
        ],
    },
    "files": {
        "description": "DBFS and UC Volumes file operations (upload, download, list)",
        "use_when": [
            "uploading or downloading files",
            "browsing DBFS or UC Volumes",
            "managing file storage",
        ],
    },
    "grants": {
        "description": "Unity Catalog permission grants (GRANT/REVOKE)",
        "use_when": [
            "granting or revoking permissions on UC objects",
            "checking effective permissions",
            "data governance and access control",
        ],
    },
    "storage": {
        "description": "Storage credentials and external locations",
        "use_when": [
            "configuring cloud storage access",
            "managing storage credentials (AWS/Azure/GCP)",
            "creating external locations for UC",
        ],
    },
    "metastores": {
        "description": "Unity Catalog metastore management",
        "use_when": [
            "managing UC metastores",
            "assigning metastores to workspaces",
            "checking current metastore configuration",
        ],
    },
    "online_tables": {
        "description": "Online tables for low-latency feature serving",
        "use_when": [
            "creating online tables for real-time inference",
            "managing feature serving infrastructure",
        ],
    },
    "global_init_scripts": {
        "description": "Workspace-wide initialization scripts",
        "use_when": [
            "managing scripts that run on all cluster startups",
            "installing workspace-wide packages",
        ],
    },
    "tokens": {
        "description": "Personal access token management",
        "use_when": [
            "creating or revoking PATs",
            "admin token management across users",
        ],
    },
    "git_credentials": {
        "description": "Git credentials for Databricks Repos",
        "use_when": [
            "configuring Git authentication for repos",
            "managing Git provider credentials",
        ],
    },
    "quality_monitors": {
        "description": "Data quality monitoring, drift detection, profiling",
        "use_when": [
            "monitoring data quality on tables",
            "detecting data drift",
            "running quality metric refreshes",
        ],
    },
    "command_execution": {
        "description": "Interactive command execution on clusters (Python, SQL, Scala, R)",
        "use_when": [
            "running ad-hoc code on a cluster",
            "interactive debugging",
            "executing commands without creating a job",
        ],
    },
}

# Role-based presets mapping role to recommended modules
_ROLE_PRESETS = {
    "data_engineer": {
        "description": "Data pipeline development and management",
        "modules": ["unity_catalog", "sql", "compute", "jobs", "pipelines", "files", "quality_monitors"],
    },
    "ml_engineer": {
        "description": "ML model training, serving, and monitoring",
        "modules": ["serving", "vector_search", "experiments", "compute", "unity_catalog", "online_tables", "files"],
    },
    "platform_admin": {
        "description": "Workspace administration and security",
        "modules": ["iam", "secrets", "tokens", "metastores", "compute", "global_init_scripts", "grants", "storage"],
    },
    "app_developer": {
        "description": "Application development on Databricks",
        "modules": ["apps", "database", "sql", "files", "serving", "secrets"],
    },
    "data_analyst": {
        "description": "Data exploration and dashboarding",
        "modules": ["sql", "unity_catalog", "dashboards", "genie", "workspace"],
    },
    "minimal": {
        "description": "Lightweight: just SQL and data catalog",
        "modules": ["sql", "unity_catalog"],
    },
}


def register_resources(mcp: FastMCP) -> None:
    """Register workspace info and tool guide resources."""

    @mcp.resource("databricks://workspace/info")
    def workspace_info() -> str:
        """Get current Databricks workspace information: URL, cloud provider, and current user."""
        try:
            w = get_workspace_client()
            me = w.current_user.me()
            config = w.config

            info = {
                "host": config.host,
                "user": {
                    "user_name": me.user_name,
                    "display_name": me.display_name,
                    "id": me.id,
                },
                "auth_type": config.auth_type,
            }
            return to_json(info)
        except Exception as e:
            return f"Error getting workspace info: {format_error(e)}"

    @mcp.resource("databricks://tools/guide")
    def tools_guide() -> str:
        """Get the tool discovery guide: what each module does and when to use it.

        Read this resource first to understand which Databricks tools are available
        and pick the right ones for your task. Includes role-based presets.
        """
        guide = {
            "instructions": (
                "This server provides Databricks tools organized by module. "
                "Each module covers a specific service area. Use this guide to find "
                "the right tools for your task. Tool names are prefixed with 'databricks_'."
            ),
            "modules": _TOOL_CATALOG,
            "role_presets": _ROLE_PRESETS,
            "tips": [
                "Start with the module most relevant to your task.",
                "For data exploration: unity_catalog + sql.",
                "For ML workflows: experiments + serving + vector_search.",
                "For admin tasks: iam + secrets + tokens + metastores.",
                "Use databricks_get_current_user to check your identity and permissions.",
                "Use databricks_execute_sql for quick data queries without needing a cluster.",
                "Use databricks_execute_command for interactive code on a running cluster.",
            ],
        }
        return json.dumps(guide, indent=2)

    @mcp.tool()
    def databricks_tool_guide(task: str = "", role: str = "") -> str:
        """Find the right Databricks tools for a task or role.

        Call this tool when you're unsure which Databricks tools to use.
        Provide either a task description or a role name to get recommendations.

        Args:
            task: Describe what you want to do (e.g. "run a SQL query",
                  "deploy an ML model", "create a user"). Leave empty to
                  see all modules.
            role: One of: data_engineer, ml_engineer, platform_admin,
                  app_developer, data_analyst, minimal. Returns the
                  recommended module set for that role.

        Returns:
            JSON with recommended modules and their descriptions.
        """
        if role and role in _ROLE_PRESETS:
            preset = _ROLE_PRESETS[role]
            modules = {
                name: _TOOL_CATALOG[name]
                for name in preset["modules"]
                if name in _TOOL_CATALOG
            }
            return json.dumps({
                "role": role,
                "description": preset["description"],
                "recommended_modules": modules,
                "env_config": f"DATABRICKS_MCP_TOOLS_INCLUDE={','.join(preset['modules'])}",
            }, indent=2)

        if task:
            task_lower = task.lower()
            matches = {}
            for name, info in _TOOL_CATALOG.items():
                for use_case in info["use_when"]:
                    if any(word in use_case.lower() for word in task_lower.split()):
                        matches[name] = info
                        break
                # Also check description
                if name not in matches and any(
                    word in info["description"].lower() for word in task_lower.split()
                ):
                    matches[name] = info

            if matches:
                return json.dumps({
                    "task": task,
                    "matching_modules": matches,
                    "tool_prefix": "databricks_",
                    "hint": "Tool names start with 'databricks_' followed by the action.",
                }, indent=2)
            else:
                return json.dumps({
                    "task": task,
                    "message": "No exact match found. Here are all available modules.",
                    "all_modules": {
                        name: info["description"] for name, info in _TOOL_CATALOG.items()
                    },
                }, indent=2)

        # No task or role: return full catalog
        return json.dumps({
            "all_modules": {name: info["description"] for name, info in _TOOL_CATALOG.items()},
            "role_presets": {
                name: preset["description"] for name, preset in _ROLE_PRESETS.items()
            },
            "hint": "Call with task='your task' or role='data_engineer' for specific recommendations.",
        }, indent=2)

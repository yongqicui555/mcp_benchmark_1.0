"""MCP prompt templates for guided Databricks workflows.

Each prompt returns a structured set of instructions that guide an agent
through a multi-step workflow using the available Databricks tools.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP


def register_prompts(mcp: FastMCP) -> None:
    """Register workflow prompt templates with the MCP server."""

    @mcp.prompt()
    def explore_data_catalog(catalog_name: str = "") -> str:
        """Explore the Unity Catalog data assets systematically."""
        if catalog_name:
            return (
                f"I want to explore the data in catalog '{catalog_name}'. Please:\n"
                f"1. Call databricks_get_catalog(name='{catalog_name}') to see catalog details\n"
                f"2. Call databricks_list_schemas(catalog_name='{catalog_name}') to list all schemas\n"
                "3. For each schema, call databricks_list_tables to see the tables\n"
                "4. For the most interesting tables, call databricks_get_table to see columns and stats\n"
                "5. Summarize what data is available, organized by schema"
            )
        return (
            "I want to explore the data catalog. Please:\n"
            "1. Call databricks_list_catalogs() to see all available catalogs\n"
            "2. For each catalog, call databricks_list_schemas to see schemas\n"
            "3. Pick the most relevant schemas and call databricks_list_tables\n"
            "4. For key tables, call databricks_get_table to see columns and stats\n"
            "5. Provide a summary of the data landscape"
        )

    @mcp.prompt()
    def debug_failing_job(job_id: str) -> str:
        """Diagnose why a Databricks job is failing."""
        return (
            f"Job {job_id} is failing. Please diagnose the issue:\n"
            f"1. Call databricks_get_job(job_id={job_id}) to see the job configuration\n"
            f"2. Call databricks_list_runs(job_id={job_id}) to find recent failed runs\n"
            "3. For the most recent failed run, call databricks_get_run to see the error state\n"
            "4. Call databricks_get_run_output for the failed run to see error messages and logs\n"
            "5. Check if the cluster used is still available (databricks_get_cluster if cluster_id is specified)\n"
            "6. Summarize the root cause and suggest a fix\n"
            "7. If appropriate, offer to repair the run with databricks_repair_run"
        )

    @mcp.prompt()
    def setup_ml_experiment(experiment_name: str, description: str = "") -> str:
        """Set up a new MLflow experiment with best practices."""
        desc_part = f" with description '{description}'" if description else ""
        return (
            f"Set up a new ML experiment called '{experiment_name}'{desc_part}. Please:\n"
            f"1. Call databricks_create_experiment(name='{experiment_name}')\n"
            "2. Confirm the experiment was created and note the experiment_id\n"
            "3. Explain how to log runs, metrics, and parameters using:\n"
            "   - databricks_create_run to start a run\n"
            "   - databricks_log_metric / databricks_log_param to track values\n"
            "   - databricks_update_run to mark it as finished\n"
            "4. Suggest a good experiment structure (naming conventions, key metrics to track)"
        )

    @mcp.prompt()
    def deploy_model(model_name: str, version: str = "1") -> str:
        """Deploy a registered model to a serving endpoint."""
        return (
            f"Deploy model '{model_name}' version {version} to a serving endpoint. Please:\n"
            f"1. Call databricks_get_registered_model(full_name='{model_name}') to verify it exists\n"
            f"2. Call databricks_list_model_versions(full_model_name='{model_name}') to check available versions\n"
            "3. Create a serving endpoint with databricks_create_serving_endpoint:\n"
            f"   - name: derive from the model name (lowercase, hyphens)\n"
            f"   - model_name: '{model_name}'\n"
            f"   - model_version: '{version}'\n"
            "   - workload_size: 'Small' (can scale later)\n"
            "   - scale_to_zero: true (cost-effective)\n"
            "4. Monitor the deployment with databricks_get_serving_endpoint\n"
            "5. Once ready, show how to query it with databricks_query_serving_endpoint"
        )

    @mcp.prompt()
    def setup_data_pipeline(
        source_table: str,
        target_schema: str = "",
    ) -> str:
        """Plan and create a data pipeline for a source table."""
        return (
            f"Set up a data pipeline for source table '{source_table}'. Please:\n"
            f"1. Call databricks_get_table(full_name='{source_table}') to understand the source data\n"
            "2. Check available SQL warehouses with databricks_list_warehouses\n"
            "3. If no warehouse is running, start one with databricks_start_warehouse\n"
            f"4. Run a sample query with databricks_execute_sql to preview the data:\n"
            f"   SELECT * FROM {source_table} LIMIT 10\n"
            "5. Suggest a transformation pipeline:\n"
            "   - What cleaning/transformations are needed\n"
            "   - Target table structure\n"
            "   - Whether to use a DLT pipeline or a job\n"
            "6. Offer to create the pipeline or job"
        )

    @mcp.prompt()
    def workspace_health_check() -> str:
        """Run a comprehensive health check on the Databricks workspace."""
        return (
            "Run a health check on this Databricks workspace. Please check:\n"
            "1. Call databricks_get_current_user() to confirm authentication\n"
            "2. Call databricks_list_clusters() -- report how many are running vs terminated\n"
            "3. Call databricks_list_warehouses() -- report status of each warehouse\n"
            "4. Call databricks_list_jobs() -- count total jobs, check for any with recent failures\n"
            "5. Call databricks_list_serving_endpoints() -- report endpoint health\n"
            "6. Call databricks_list_catalogs() -- verify Unity Catalog access\n"
            "7. Provide a summary dashboard:\n"
            "   - Auth: OK/FAIL\n"
            "   - Clusters: X running, Y terminated\n"
            "   - Warehouses: X active\n"
            "   - Jobs: X total, Y with recent failures\n"
            "   - Endpoints: X serving\n"
            "   - Catalogs: X accessible"
        )

    @mcp.prompt()
    def query_data(question: str) -> str:
        """Answer a natural language question about the data using SQL."""
        return (
            f"The user wants to know: '{question}'\n\n"
            "Please answer this by querying the data:\n"
            "1. First, explore the catalog to find relevant tables:\n"
            "   - Call databricks_list_catalogs, then databricks_list_schemas and databricks_list_tables\n"
            "   - Use databricks_get_table to check column names and types\n"
            "2. Find a running SQL warehouse with databricks_list_warehouses\n"
            "   - If none are running, start one\n"
            "3. Write and execute a SQL query with databricks_execute_sql\n"
            "4. Present the results clearly, answering the original question\n"
            "5. If the first query doesn't fully answer the question, refine and re-query"
        )

    @mcp.prompt()
    def manage_permissions(object_type: str, object_name: str) -> str:
        """Review and manage permissions on a Databricks object."""
        return (
            f"Review and manage permissions for {object_type} '{object_name}'. Please:\n"
            f"1. Get current grants with databricks_get_grants(securable_type='{object_type}', "
            f"full_name='{object_name}')\n"
            f"2. Get effective grants with databricks_get_effective_grants(securable_type='{object_type}', "
            f"full_name='{object_name}')\n"
            "3. List all workspace users and groups relevant to this object:\n"
            "   - databricks_list_users and databricks_list_groups\n"
            "4. Present a clear permissions matrix showing who has what access\n"
            "5. Ask if any permissions should be added, changed, or revoked\n"
            "6. If changes are requested, use databricks_update_grants to apply them"
        )

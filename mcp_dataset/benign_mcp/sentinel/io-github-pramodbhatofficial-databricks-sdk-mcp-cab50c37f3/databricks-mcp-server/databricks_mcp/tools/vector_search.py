"""Tools for managing Databricks Vector Search endpoints and indexes.

Vector Search enables similarity search over embeddings stored in Delta tables.
It supports two index types:
- DELTA_SYNC: Automatically syncs embeddings from a source Delta table, with
  optional managed embedding computation via a model serving endpoint.
- DIRECT_ACCESS: Allows direct read/write of vectors and metadata through the API,
  without a backing Delta table.
"""

from __future__ import annotations

import json

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all vector search tools with the MCP server."""

    @mcp.tool()
    def databricks_list_vector_search_endpoints() -> str:
        """List all vector search endpoints in the workspace.

        Vector search endpoints are the compute resources that host vector search
        indexes. Returns name, state, creation time, and endpoint type for each.
        """
        try:
            w = get_workspace_client()
            endpoints = paginate(w.vector_search_endpoints.list_endpoints(), max_items=100)
            return to_json({"endpoints": endpoints, "count": len(endpoints)})
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_vector_search_endpoint(
        name: str,
        endpoint_type: str = "STANDARD",
    ) -> str:
        """Create a new vector search endpoint.

        Provisions compute resources for hosting vector search indexes. The endpoint
        starts provisioning immediately. This tool returns without waiting for the
        endpoint to become ONLINE (which can take several minutes).

        Args:
            name: Unique name for the vector search endpoint.
            endpoint_type: Type of endpoint to create. Currently only "STANDARD" is
                           supported. Defaults to "STANDARD".
        """
        try:
            from databricks.sdk.service.vectorsearch import EndpointType

            w = get_workspace_client()
            w.vector_search_endpoints.create_endpoint(
                name=name,
                endpoint_type=EndpointType[endpoint_type],
            )
            # Return immediately without blocking on .result()
            return to_json({
                "status": "provisioning",
                "name": name,
                "endpoint_type": endpoint_type,
                "message": (
                    f"Vector search endpoint '{name}' creation initiated. "
                    "Use databricks_get_vector_search_endpoint to check status."
                ),
            })
        except KeyError:
            return format_error(ValueError(
                f"Invalid endpoint_type '{endpoint_type}'. Supported values: STANDARD"
            ))
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_vector_search_endpoint(name: str) -> str:
        """Get detailed information about a vector search endpoint.

        Returns the endpoint configuration, current state (PROVISIONING, ONLINE,
        OFFLINE), and associated metadata.

        Args:
            name: Name of the vector search endpoint.
        """
        try:
            w = get_workspace_client()
            endpoint = w.vector_search_endpoints.get_endpoint(endpoint_name=name)
            return to_json(endpoint)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_vector_search_endpoint(name: str) -> str:
        """Delete a vector search endpoint.

        Permanently removes the endpoint and all its compute resources. All indexes
        hosted on this endpoint must be deleted first, or the operation will fail.

        Args:
            name: Name of the vector search endpoint to delete.
        """
        try:
            w = get_workspace_client()
            w.vector_search_endpoints.delete_endpoint(endpoint_name=name)
            return to_json({
                "status": "deleted",
                "name": name,
                "message": f"Vector search endpoint '{name}' has been deleted.",
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_list_vector_search_indexes(endpoint_name: str) -> str:
        """List all vector search indexes hosted on a specific endpoint.

        Returns summary information for each index including name, type, status,
        and the source table (for DELTA_SYNC indexes).

        Args:
            endpoint_name: Name of the vector search endpoint whose indexes to list.
        """
        try:
            w = get_workspace_client()
            indexes = paginate(w.vector_search_indexes.list_indexes(endpoint_name=endpoint_name), max_items=100)
            return to_json({"endpoint": endpoint_name, "indexes": indexes, "count": len(indexes)})
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_vector_search_index(
        name: str,
        endpoint_name: str,
        primary_key: str,
        index_type: str = "DELTA_SYNC",
        source_table_name: str = "",
        embedding_dimension: int = 0,
        embedding_model_endpoint_name: str = "",
    ) -> str:
        """Create a new vector search index.

        Creates an index on the specified endpoint. The index type determines the
        required parameters:

        For DELTA_SYNC indexes (auto-sync from a Delta table):
        - source_table_name is required
        - Optionally specify embedding_model_endpoint_name to have Databricks
          compute embeddings automatically from a text column

        For DIRECT_ACCESS indexes (manual vector management via API):
        - embedding_dimension is required (e.g. 1536 for OpenAI, 768 for BGE)
        - No source table is needed; vectors are inserted via the API

        Args:
            name: Full three-level name for the index (catalog.schema.index_name).
            endpoint_name: Name of the vector search endpoint to host this index.
            primary_key: Column name to use as the primary key for the index.
            index_type: Type of index. Either "DELTA_SYNC" or "DIRECT_ACCESS".
                        Defaults to "DELTA_SYNC".
            source_table_name: Full name of the source Delta table (required for
                               DELTA_SYNC). Format: "catalog.schema.table".
            embedding_dimension: Dimensionality of embedding vectors (required for
                                 DIRECT_ACCESS). Common values: 768, 1024, 1536.
            embedding_model_endpoint_name: Name of a serving endpoint that computes
                                           embeddings (optional, for DELTA_SYNC only).
        """
        try:
            from databricks.sdk.service.vectorsearch import (
                DeltaSyncVectorIndexSpecRequest,
                DirectAccessVectorIndexSpec,
                EmbeddingSourceColumn,
                VectorIndexType,
            )

            w = get_workspace_client()

            delta_sync_spec = None
            direct_access_spec = None

            if index_type == "DELTA_SYNC":
                if not source_table_name:
                    return format_error(ValueError(
                        "source_table_name is required for DELTA_SYNC index type."
                    ))
                spec_kwargs: dict = {
                    "source_table": source_table_name,
                    "pipeline_type": "TRIGGERED",
                }
                # If a model endpoint is provided, configure managed embeddings
                if embedding_model_endpoint_name:
                    spec_kwargs["embedding_source_columns"] = [
                        EmbeddingSourceColumn(
                            name=primary_key,
                            embedding_model_endpoint_name=embedding_model_endpoint_name,
                        )
                    ]
                delta_sync_spec = DeltaSyncVectorIndexSpecRequest(**spec_kwargs)

            elif index_type == "DIRECT_ACCESS":
                if embedding_dimension <= 0:
                    return format_error(ValueError(
                        "embedding_dimension must be a positive integer for DIRECT_ACCESS index type."
                    ))
                direct_access_spec = DirectAccessVectorIndexSpec(
                    embedding_dimension=embedding_dimension,
                )
            else:
                return format_error(ValueError(
                    f"Invalid index_type '{index_type}'. Must be 'DELTA_SYNC' or 'DIRECT_ACCESS'."
                ))

            index = w.vector_search_indexes.create_index(
                name=name,
                endpoint_name=endpoint_name,
                primary_key=primary_key,
                index_type=VectorIndexType[index_type],
                delta_sync_index_spec=delta_sync_spec,
                direct_access_index_spec=direct_access_spec,
            )
            return to_json(index)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_vector_search_index(name: str) -> str:
        """Delete a vector search index.

        Permanently removes the index and its data. For DELTA_SYNC indexes, the
        source Delta table is NOT affected. This action cannot be undone.

        Args:
            name: Full three-level name of the index to delete (catalog.schema.index_name).
        """
        try:
            w = get_workspace_client()
            w.vector_search_indexes.delete_index(index_name=name)
            return to_json({
                "status": "deleted",
                "name": name,
                "message": f"Vector search index '{name}' has been deleted.",
            })
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_query_vector_search_index(
        index_name: str,
        query_text: str = "",
        query_vector: str = "",
        columns: str = "",
        num_results: int = 10,
        filters_json: str = "",
    ) -> str:
        """Query a vector search index for similar items.

        Performs approximate nearest neighbor (ANN) search to find vectors similar
        to the provided query. Provide either query_text (for indexes with a managed
        embedding model) or query_vector (for self-managed embeddings).

        Args:
            index_name: Full three-level name of the index to query.
            query_text: Text query string. Used with DELTA_SYNC indexes that have
                        a configured embedding model endpoint. The text is automatically
                        embedded before searching.
            query_vector: JSON array string of floats representing the query embedding
                          vector. Example: "[0.1, 0.2, 0.3, ...]". Required for
                          DIRECT_ACCESS indexes and DELTA_SYNC indexes without a
                          managed embedding model.
            columns: Comma-separated list of column names to include in results.
                     Example: "id,text,score". If empty, returns all columns.
            num_results: Maximum number of results to return. Defaults to 10.
            filters_json: Optional JSON string of filter conditions. Example:
                          '{"category": "science", "year >=": 2020}'. Supports
                          operators: =, <, >, <=, >=.
        """
        try:
            w = get_workspace_client()

            # Parse columns into a list
            column_list = [c.strip() for c in columns.split(",") if c.strip()] if columns else []
            if not column_list:
                return format_error(ValueError(
                    "columns parameter is required. Provide a comma-separated list of column names."
                ))

            kwargs: dict = {
                "index_name": index_name,
                "columns": column_list,
                "num_results": num_results,
            }

            # Set query method: text or vector
            if query_text:
                kwargs["query_text"] = query_text
            elif query_vector:
                try:
                    kwargs["query_vector"] = json.loads(query_vector)
                except json.JSONDecodeError as e:
                    return format_error(ValueError(f"Invalid JSON in 'query_vector': {e}"))

            # Set optional filters
            if filters_json:
                kwargs["filters_json"] = filters_json

            response = w.vector_search_indexes.query_index(**kwargs)
            return to_json(response)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_vector_search_index(index_name: str) -> str:
        """Get detailed information about a specific vector search index.

        Returns the index configuration including type (DELTA_SYNC or
        DIRECT_ACCESS), status, endpoint, primary key, embedding source,
        and sync pipeline details.

        Args:
            index_name: Full three-level name of the index
                        (catalog.schema.index_name).

        Returns:
            JSON object with full index details including name, endpoint_name,
            index_type, primary_key, and status.
        """
        try:
            w = get_workspace_client()
            result = w.vector_search_indexes.get_index(index_name=index_name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_sync_vector_search_index(index_name: str) -> str:
        """Trigger a sync of a DELTA_SYNC vector search index.

        Forces the index to re-sync with its source Delta table. This is
        useful when the source table has been updated and you want the
        index to reflect the latest data immediately rather than waiting
        for the next scheduled sync.

        Only applicable to DELTA_SYNC indexes. DIRECT_ACCESS indexes do
        not support this operation.

        Args:
            index_name: Full three-level name of the index
                        (catalog.schema.index_name).

        Returns:
            Confirmation that the sync has been initiated.
        """
        try:
            w = get_workspace_client()
            w.vector_search_indexes.sync_index(index_name=index_name)
            return to_json({
                "status": "syncing",
                "index_name": index_name,
                "message": (
                    f"Sync initiated for vector search index '{index_name}'. "
                    "Use databricks_get_vector_search_index to check sync status."
                ),
            })
        except Exception as e:
            return format_error(e)

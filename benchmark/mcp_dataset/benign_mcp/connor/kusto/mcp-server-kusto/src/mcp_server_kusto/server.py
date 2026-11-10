import logging

from mcp.server.models import InitializationOptions
import mcp.types as types
from mcp.server import NotificationOptions, Server
import mcp.server.stdio
from typing import Any, List
from azure.kusto.data import KustoClient, KustoConnectionStringBuilder
import os

# init logger
if not os.path.exists('logs'):
    os.makedirs('logs')
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    filename='logs/mcp_kusto_server.log')
logger = logging.getLogger('mcp_kusto_server')

logger.info("Starting MCP Kusto Server")


class KustoDatabase:
    def __init__(self, cluster: str, client_id: str = None, client_secret: str = None, authority_id: str = None):
        """
        initialize kusto connect string builder
        :param cluster:adx cluster url
        :param client_id: azure service principal client id
        :param client_secret: azure service principal client secret
        :param authority_id: azure tenant id
        """

        # if cluster url starts with http:// which means using local adx emulator, therefore use no authentication
        if cluster.startswith("http://"):
            self.kcsb = KustoConnectionStringBuilder.with_no_authentication(cluster)
        elif client_id is None or client_secret is None or authority_id is None:
            raise ValueError("Client id, client secret and authority id are required")
        else:
            self.kcsb = KustoConnectionStringBuilder.with_aad_application_key_authentication(cluster, client_id,
                                                                                             client_secret,
                                                                                             authority_id)

    def list_internal_tables(self, database: str) -> List[str]:
        """
        List all internal tables in the database
        :param database:adx database name
        :return: the list of internal tables in the database
        """
        try:
            with KustoClient(self.kcsb) as kusto_client:
                response = kusto_client.execute(database, ".show tables")
                tables = [row[0] for row in response.primary_results[0]]
            return tables
        except Exception as e:
            logger.error(f"Error listing tables: {e}")

    def list_external_tables(self, database: str) -> List[str]:
        """
        List all external tables in the database
        :param database: adx database name
        :return: the list of external tables in the database
        """
        try:
            with KustoClient(self.kcsb) as kusto_client:
                response = kusto_client.execute(database, ".show external tables")
                tables = [row[0] for row in response.primary_results[0]]
            return tables
        except Exception as e:
            logger.error(f"Error listing external tables: {e}")

    def list_materialized_views(self, database: str) -> List[str]:
        """
        List all materialized views in the database
        :param database: adx database name
        :return: the list of materialized views in the database
        """
        try:
            with KustoClient(self.kcsb) as kusto_client:
                response = kusto_client.execute(database, ".show materialized-views")
                tables = [row[0] for row in response.primary_results[0]]
            return tables
        except Exception as e:
            logger.error(f"Error listing materialized views: {e}")

    def execute_query_internal_table(self, database: str, query: str) -> List[str]:
        """
        Execute a kql query to internal table or materialized view
        :param database:adx database name
        :param query:query to execute
        :return:results of the query
        """
        logger.debug(f"Executing query: {query}")
        if query.startswith("."):
            raise ValueError("Should not use management commands")
        try:
            with KustoClient(self.kcsb) as kusto_client:
                response = kusto_client.execute(database, query)
            return response.primary_results[0]
        except Exception as e:
            logger.error(f"Error executing query: {e}")

    def execute_query_external_table(self, database: str, query: str) -> List[str]:
        """
        Execute a kql query to external table
        :param database: adx database name
        :param query: query to execute
        :return: results of the query
        """
        logger.debug(f"Executing query: {query}")
        if query.startswith("."):
            raise ValueError("Should not use management commands")
        try:
            with KustoClient(self.kcsb) as kusto_client:
                # replace table name with external_table("table_name") to execute query
                table_name = query.split("|")[0].strip()
                query = query.replace(table_name, f'external_table("{table_name}")')
                response = kusto_client.execute(database, query)
            return response.primary_results[0]
        except Exception as e:
            logger.error(f"Error executing query: {e}")

    def retrieve_internal_table_schema(self, database: str, table: str) -> List[str]:
        """
        Get the schema of an internal table or materialized view
        :param database: adx database name
        :param table: target table
        :return: the schema of the table or materialized view
        """
        try:
            with KustoClient(self.kcsb) as kusto_client:
                response = kusto_client.execute(database, f"{table} | getschema")
            return response.primary_results[0]
        except Exception as e:
            logger.error(f"Error retrieving table schema: {e}")

    def retrieve_external_table_schema(self, database: str, table: str) -> List[str]:
        """
        Get the schema of an external table
        :param database: adx database name
        :param table: target table
        :return: the schema of the table
        """
        try:
            with KustoClient(self.kcsb) as kusto_client:
                response = kusto_client.execute(database, f"external_table(\"{table}\") | getschema")
            return response.primary_results[0]
        except Exception as e:
            logger.error(f"Error retrieving table schema: {e}")


async def main(cluster: str, authority_id: str = None, client_id: str = None, client_secret: str = None):
    server = Server("kusto-manager")
    kusto_database = KustoDatabase(cluster, client_id, client_secret, authority_id)

    # define the tools
    tool_list = [
        types.Tool(
            name="list_internal_tables",
            description="List all internal tables in the database",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {"type": "string"},
                },
                "required": ["database"]
            }
        ),
        types.Tool(
            name="list_external_tables",
            description="List all external tables in the database",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {"type": "string"},
                },
                "required": ["database"]
            }
        ),
        types.Tool(
            name="list_materialized_views",
            description="List all materialized views in the database",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {"type": "string"},
                },
                "required": ["database"]
            }
        ),
        types.Tool(
            name="execute_query_internal_table",
            description="Execute a kql query to internal table or materialized view",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {"type": "string"},
                    "query": {"type": "string"},
                },
                "required": ["database", "query"]
            }
        ),
        types.Tool(
            name="execute_query_external_table",
            description="Execute a kql query to external table",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {"type": "string"},
                    "query": {"type": "string"},
                },
                "required": ["database", "query"]
            }
        ),
        types.Tool(
            name="retrieve_internal_table_schema",
            description="Get the schema of a table or materialized view",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {"type": "string"},
                    "table": {"type": "string"},
                },
                "required": ["database", "table"]
            }
        ),
        types.Tool(
            name="retrieve_external_table_schema",
            description="Get the schema of an external table",
            inputSchema={
                "type": "object",
                "properties": {
                    "database": {"type": "string"},
                    "table": {"type": "string"},
                },
                "required": ["database", "table"]
            }
        )
    ]
    tool_name_list = [tool.name for tool in tool_list]

    @server.list_tools()
    async def handle_list_tools() -> list[types.Tool]:
        return tool_list

    @server.call_tool()
    async def handle_call_tool(
            name: str, arguments: dict[str, Any] | None
    ) -> list[types.TextContent | types.ImageContent | types.EmbeddedResource]:
        if name not in tool_name_list:
            raise ValueError(f"Unknown tool: {name}")

        if not arguments or "database" not in arguments:
            raise ValueError("Missing database argument")
        database = arguments["database"]

        if name == "list_internal_tables":
            results = kusto_database.list_internal_tables(database=database)
            return [types.TextContent(type="text", text=str(results))]
        elif name == "list_external_tables":
            results = kusto_database.list_external_tables(database=database)
            return [types.TextContent(type="text", text=str(results))]
        elif name == "list_materialized_views":
            results = kusto_database.list_materialized_views(database=database)
            return [types.TextContent(type="text", text=str(results))]
        elif name == "execute_query_internal_table":
            if "query" not in arguments:
                raise ValueError("Missing database or query argument")
            results = kusto_database.execute_query_internal_table(database=database,
                                                                  query=arguments["query"])
            return [types.TextContent(type="text", text=str(results))]
        elif name == "execute_query_external_table":
            if "query" not in arguments:
                raise ValueError("Missing database or query argument")
            results = kusto_database.execute_query_external_table(database=database,
                                                                  query=arguments["query"])
            return [types.TextContent(type="text", text=str(results))]
        elif name == "retrieve_table_schema":
            if "table" not in arguments:
                raise ValueError("Missing database or table argument")
            results = kusto_database.retrieve_internal_table_schema(database=database,
                                                                    table=arguments["table"])
            return [types.TextContent(type="text", text=str(results))]
        elif name == "retrieve_external_table_schema":
            if "table" not in arguments:
                raise ValueError("Missing database or table argument")
            results = kusto_database.retrieve_external_table_schema(database=database,
                                                                    table=arguments["table"])
            return [types.TextContent(type="text", text=str(results))]

    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="kusto",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )

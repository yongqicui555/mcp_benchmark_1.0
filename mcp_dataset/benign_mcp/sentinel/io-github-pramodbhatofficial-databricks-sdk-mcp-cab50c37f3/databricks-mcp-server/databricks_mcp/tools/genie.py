"""Databricks Genie AI/BI conversation tools.

Provides MCP tools for interacting with Genie, Databricks' AI-powered
natural language interface for business intelligence. Genie allows users
to ask questions about their data in plain English and receive SQL-backed
answers from configured Genie Spaces.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all Databricks Genie AI/BI tools with the MCP server."""

    @mcp.tool()
    def databricks_genie_start_conversation(space_id: str, content: str) -> str:
        """Start a new Genie AI/BI conversation with a question.

        Initiates a new conversation in the specified Genie Space by asking
        a natural language question about your data. Genie will interpret
        the question, generate SQL, and produce an answer.

        This is an asynchronous operation. The response includes conversation
        and message IDs that can be used to retrieve the result once processing
        completes. Use databricks_genie_get_message to poll for the answer.

        Args:
            space_id: The ID of the Genie Space to start the conversation in.
                      Genie Spaces are configured with specific data sources
                      and context for answering questions.
            content: The natural language question to ask (e.g., "What were
                     total sales last quarter?" or "Show me the top 10
                     customers by revenue").

        Returns:
            JSON object with conversation_id and message_id for tracking
            the response. Use these IDs with databricks_genie_get_message
            to retrieve the answer.
        """
        try:
            w = get_workspace_client()
            # Initiate conversation without waiting for completion
            wait_obj = w.genie.start_conversation(
                space_id=space_id,
                content=content,
            )
            # Extract identifiers from the wait object for tracking
            response = {
                "status": "processing",
                "message": "Conversation started. Use databricks_genie_get_message "
                           "to check for the response.",
                "space_id": space_id,
            }
            # The wait object contains conversation_id and message_id
            if hasattr(wait_obj, 'conversation_id'):
                response["conversation_id"] = wait_obj.conversation_id
            if hasattr(wait_obj, 'message_id'):
                response["message_id"] = wait_obj.message_id
            # Also check the response attribute for nested IDs
            if hasattr(wait_obj, 'response') and wait_obj.response is not None:
                resp = wait_obj.response
                if hasattr(resp, 'conversation_id'):
                    response["conversation_id"] = resp.conversation_id
                if hasattr(resp, 'message_id'):
                    response["message_id"] = resp.message_id
            return to_json(response)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_genie_create_message(
        space_id: str,
        conversation_id: str,
        content: str,
    ) -> str:
        """Send a follow-up message in an existing Genie conversation.

        Adds a new question or follow-up to an existing Genie conversation.
        Genie uses all previous messages in the conversation as context when
        generating its response, enabling multi-turn data exploration.

        This is an asynchronous operation. Use databricks_genie_get_message
        to poll for the answer.

        Args:
            space_id: The ID of the Genie Space containing the conversation.
            conversation_id: The ID of the existing conversation to continue.
            content: The follow-up question or refinement (e.g., "Break that
                     down by region" or "Show only results from last month").

        Returns:
            JSON object with the message_id for tracking the response.
            Use databricks_genie_get_message to retrieve the answer.
        """
        try:
            w = get_workspace_client()
            # Initiate message creation without waiting for completion
            wait_obj = w.genie.create_message(
                space_id=space_id,
                conversation_id=conversation_id,
                content=content,
            )
            response = {
                "status": "processing",
                "message": "Follow-up message sent. Use databricks_genie_get_message "
                           "to check for the response.",
                "space_id": space_id,
                "conversation_id": conversation_id,
            }
            # Extract message_id from the wait object
            if hasattr(wait_obj, 'message_id'):
                response["message_id"] = wait_obj.message_id
            if hasattr(wait_obj, 'response') and wait_obj.response is not None:
                resp = wait_obj.response
                if hasattr(resp, 'id'):
                    response["message_id"] = resp.id
                if hasattr(resp, 'message_id'):
                    response["message_id"] = resp.message_id
            return to_json(response)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_genie_get_message(
        space_id: str,
        conversation_id: str,
        message_id: str,
    ) -> str:
        """Get a Genie message and its response.

        Retrieves a specific message from a Genie conversation, including
        the AI-generated response, any SQL query that was generated, and
        the status of the message processing.

        Poll this endpoint after starting a conversation or sending a message
        to check if the response is ready. The message status will indicate
        whether processing is complete.

        Args:
            space_id: The ID of the Genie Space containing the conversation.
            conversation_id: The ID of the conversation containing the message.
            message_id: The ID of the specific message to retrieve.

        Returns:
            JSON object with the message details including status, content,
            generated SQL query (if applicable), and any attachments with
            query results.
        """
        try:
            w = get_workspace_client()
            result = w.genie.get_message(
                space_id=space_id,
                conversation_id=conversation_id,
                message_id=message_id,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_genie_get_message_query_result(
        space_id: str,
        conversation_id: str,
        message_id: str,
    ) -> str:
        """Get the SQL query result from a Genie message.

        Retrieves the tabular data result from a Genie message's generated
        SQL query. Use this after a message has been processed to get the
        actual data rows returned by the query.

        Note: This requires the message to have completed processing and
        to have generated a SQL query with results. Check the message
        status first with databricks_genie_get_message.

        Args:
            space_id: The ID of the Genie Space containing the conversation.
            conversation_id: The ID of the conversation containing the message.
            message_id: The ID of the message whose query result to retrieve.

        Returns:
            JSON object with the query result data including column schema
            and row data.
        """
        try:
            w = get_workspace_client()
            result = w.genie.get_message_query_result(
                space_id=space_id,
                conversation_id=conversation_id,
                message_id=message_id,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_genie_execute_message_query(
        space_id: str,
        conversation_id: str,
        message_id: str,
    ) -> str:
        """Re-execute the SQL query from a Genie message.

        Re-runs the SQL query that was generated for a specific Genie message.
        This is useful when you want to get fresh results for a previously
        asked question, or when the original query execution timed out.

        Args:
            space_id: The ID of the Genie Space containing the conversation.
            conversation_id: The ID of the conversation containing the message.
            message_id: The ID of the message whose query to re-execute.

        Returns:
            JSON object with the re-executed query result including updated
            column schema and row data.
        """
        try:
            w = get_workspace_client()
            result = w.genie.execute_message_query(
                space_id=space_id,
                conversation_id=conversation_id,
                message_id=message_id,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

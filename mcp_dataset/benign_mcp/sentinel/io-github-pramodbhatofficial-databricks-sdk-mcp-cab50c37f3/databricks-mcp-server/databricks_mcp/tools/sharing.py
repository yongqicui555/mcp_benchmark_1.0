"""Delta Sharing management tools for Databricks MCP.

Provides tools for managing shares and recipients in Delta Sharing.
Shares define collections of tables and schemas that can be shared with
external organizations, while recipients represent the external parties
who consume the shared data.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from databricks_mcp.config import get_workspace_client
from databricks_mcp.utils import format_error, paginate, to_json


def register_tools(mcp: FastMCP) -> None:
    """Register all Delta Sharing tools with the MCP server."""

    # -- Shares ----------------------------------------------------------------

    @mcp.tool()
    def databricks_list_shares() -> str:
        """List all Delta Sharing shares in the metastore.

        Shares are named objects that contain a collection of tables and
        schemas from one or more catalogs. They define what data is available
        for sharing with external recipients.

        Returns:
            JSON array of share objects, each containing name, owner,
            comment, and created/updated timestamps. Results are capped
            at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.shares.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_share(name: str) -> str:
        """Get detailed information about a specific share.

        Returns the share definition including all tables and schemas that
        are part of the share.

        Args:
            name: The name of the share to retrieve.

        Returns:
            JSON object with full share details including name, owner,
            comment, objects (shared tables and schemas), created_at,
            and updated_at.
        """
        try:
            w = get_workspace_client()
            result = w.shares.get(name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_share(name: str, comment: str = "") -> str:
        """Create a new Delta Sharing share.

        Creates an empty share that can later have tables and schemas added
        to it. The caller must have the CREATE_SHARE privilege on the
        metastore.

        Args:
            name: Unique name for the new share within the metastore.
            comment: Optional human-readable description of the share and
                     the data it will contain.

        Returns:
            JSON object with the created share's details.
        """
        try:
            w = get_workspace_client()
            result = w.shares.create(name=name, comment=comment)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    # -- Recipients ------------------------------------------------------------

    @mcp.tool()
    def databricks_list_recipients() -> str:
        """List all Delta Sharing recipients in the metastore.

        Recipients represent external organizations or users who are authorized
        to consume shared data. Each recipient has an authentication type and
        associated credentials or tokens.

        Returns:
            JSON array of recipient objects, each containing name,
            authentication_type, comment, sharing_code (if TOKEN auth),
            and activation status. Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.recipients.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_create_recipient(
        name: str,
        authentication_type: str = "TOKEN",
        comment: str = "",
    ) -> str:
        """Create a new Delta Sharing recipient.

        Creates a recipient that can be granted access to shares. The caller
        must have the CREATE_RECIPIENT privilege on the metastore.

        Args:
            name: Unique name for the recipient within the metastore.
            authentication_type: Authentication method for the recipient.
                                 Valid values:
                                 - "TOKEN" (default): Bearer token authentication.
                                   A sharing token is generated automatically and
                                   must be sent to the recipient out of band.
                                 - "DATABRICKS": Databricks-to-Databricks sharing.
                                   The recipient authenticates using their own
                                   Databricks identity.
            comment: Optional human-readable description of the recipient and
                     the organization they represent.

        Returns:
            JSON object with the created recipient's details, including the
            activation URL and sharing token (for TOKEN authentication).
        """
        try:
            from databricks.sdk.service.sharing import AuthenticationType

            w = get_workspace_client()
            result = w.recipients.create(
                name=name,
                authentication_type=AuthenticationType[authentication_type],
                comment=comment,
            )
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_update_share(name: str, comment: str = "", owner: str = "") -> str:
        """Update properties of an existing Delta Sharing share.

        The caller must be the share owner or a metastore admin. Only
        non-empty fields are updated; other fields remain unchanged.

        Args:
            name: The name of the share to update.
            comment: Optional new description for the share. If empty,
                     the comment is not changed.
            owner: Optional new owner for the share. If empty, the owner
                   is not changed.

        Returns:
            JSON object with the updated share's details.
        """
        try:
            w = get_workspace_client()
            kwargs: dict = {}
            if comment:
                kwargs["comment"] = comment
            if owner:
                kwargs["owner"] = owner
            if not kwargs:
                return to_json({
                    "status": "no_change",
                    "message": "No fields provided to update. Specify comment and/or owner.",
                })
            result = w.shares.update(name=name, **kwargs)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_share(name: str) -> str:
        """Delete a Delta Sharing share.

        Permanently removes the share. Recipients who had access to this
        share will no longer be able to query its tables. The underlying
        tables are not affected.

        Args:
            name: The name of the share to delete.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.shares.delete(name)
            return f"Share '{name}' deleted successfully."
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_recipient(name: str) -> str:
        """Get detailed information about a specific Delta Sharing recipient.

        Returns the recipient definition including authentication type,
        activation status, sharing tokens, and associated shares.

        Args:
            name: The name of the recipient to retrieve.

        Returns:
            JSON object with full recipient details including name,
            authentication_type, comment, activation_url, and tokens.
        """
        try:
            w = get_workspace_client()
            result = w.recipients.get(name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_delete_recipient(name: str) -> str:
        """Delete a Delta Sharing recipient.

        Permanently removes the recipient. They will no longer be able to
        access any shares they were previously granted. This action cannot
        be undone.

        Args:
            name: The name of the recipient to delete.

        Returns:
            Confirmation message on success.
        """
        try:
            w = get_workspace_client()
            w.recipients.delete(name)
            return f"Recipient '{name}' deleted successfully."
        except Exception as e:
            return format_error(e)

    # -- Providers ---------------------------------------------------------

    @mcp.tool()
    def databricks_list_providers() -> str:
        """List all Delta Sharing providers in the metastore.

        Providers represent external organizations that share data with
        your metastore via Delta Sharing. Each provider can expose one
        or more shares.

        Returns:
            JSON array of provider objects, each containing name, comment,
            authentication_type, and recipient profile information.
            Results are capped at 100 items.
        """
        try:
            w = get_workspace_client()
            results = paginate(w.providers.list())
            return to_json(results)
        except Exception as e:
            return format_error(e)

    @mcp.tool()
    def databricks_get_provider(name: str) -> str:
        """Get detailed information about a specific Delta Sharing provider.

        Returns the provider definition including authentication type,
        recipient profile, and available shares.

        Args:
            name: The name of the provider to retrieve.

        Returns:
            JSON object with full provider details including name, comment,
            authentication_type, and recipient_profile.
        """
        try:
            w = get_workspace_client()
            result = w.providers.get(name)
            return to_json(result)
        except Exception as e:
            return format_error(e)

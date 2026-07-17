"""YouTube OAuth tools (3 tools).

Tools:
  - youfiliate_get_youtube_status
  - youfiliate_connect_youtube
  - youfiliate_disconnect_youtube
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import YoufiliateClient, make_api_call
from ..schemas.common import ResponseFormat
from ..schemas.youtube import (
    ConnectYouTubeInput,
    DisconnectYouTubeInput,
    GetYouTubeStatusInput,
)


def register_youtube_tools(mcp: FastMCP, client: YoufiliateClient) -> None:
    """Register YouTube OAuth tools."""

    @mcp.tool(
        name="youfiliate_get_youtube_status",
        annotations={
            "title": "Get YouTube Connection Status",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_get_youtube_status(params: GetYouTubeStatusInput) -> str:
        """Check if your YouTube account is connected.

        Returns connection status, channel name, and scope information.
        Does NOT modify any data or initiate any connections.

        Common errors:
        - Not connected: use `youfiliate_connect_youtube` to connect.
        """
        ok, result = await make_api_call(
            client, "GET", "/api/smart-links/youtube-oauth/"
        )
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        connected = result.get("connected", False)
        if not connected:
            return (
                "# YouTube Connection\n\n"
                "**Status**: Not connected\n\n"
                "Use `youfiliate_connect_youtube` to link your YouTube account. "
                "This is required for the auto-migration feature."
            )

        lines = [
            "# YouTube Connection",
            "",
            "**Status**: Connected",
            f"- **Channel**: {result.get('channel_name', 'N/A')}",
            f"- **Channel ID**: {result.get('channel_id', 'N/A')}",
            f"- **Scopes**: {', '.join(result.get('scopes', []))}",
            f"- **Token Expires**: {result.get('token_expiry', 'N/A')}",
            "",
        ]
        return "\n".join(lines)

    @mcp.tool(
        name="youfiliate_connect_youtube",
        annotations={
            "title": "Connect YouTube Account",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def youfiliate_connect_youtube(params: ConnectYouTubeInput) -> str:
        """Initiate YouTube OAuth connection. Returns a URL the user must open in their browser.

        The user must open the returned URL in their web browser to authorize
        Youfiliate to access their YouTube channel. The OAuth callback is handled
        in the browser — this tool only returns the authorization URL.

        Does NOT read or modify any YouTube data. The OAuth flow is completed
        in the user's browser.

        Common errors:
        - Already connected: disconnect first with `youfiliate_disconnect_youtube`.
        """
        ok, result = await make_api_call(
            client, "POST", "/api/smart-links/youtube-oauth/connect/"
        )
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        auth_url = result.get("auth_url", result.get("authorization_url", ""))
        return (
            "# Connect YouTube\n\n"
            "Please open the following URL in your browser to authorize Youfiliate:\n\n"
            f"**{auth_url}**\n\n"
            "After authorizing, you'll be redirected back to Youfiliate. "
            "Then use `youfiliate_get_youtube_status` to verify the connection."
        )

    @mcp.tool(
        name="youfiliate_disconnect_youtube",
        annotations={
            "title": "Disconnect YouTube Account",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_disconnect_youtube(params: DisconnectYouTubeInput) -> str:
        """Disconnect your YouTube account from Youfiliate.

        IMPORTANT: Always confirm with the user before executing this action.
        The `confirm` parameter must be set to true. This removes stored OAuth
        tokens. You will need to reconnect to use the auto-migration feature.

        Does NOT modify any YouTube data or video descriptions.

        Common errors:
        - Not connected: no YouTube account to disconnect.
        - confirm=False: you must set confirm=True after getting user confirmation.
        """
        if not params.confirm:
            return (
                "Disconnection requires confirmation. Please confirm with the user "
                "that they want to disconnect their YouTube account, then call again "
                "with confirm=True."
            )

        ok, result = await make_api_call(
            client, "DELETE", "/api/smart-links/youtube-oauth/disconnect/"
        )
        if not ok:
            return result

        return (
            "YouTube account has been disconnected. OAuth tokens have been removed.\n\n"
            "To use the auto-migration feature again, reconnect with "
            "`youfiliate_connect_youtube`."
        )

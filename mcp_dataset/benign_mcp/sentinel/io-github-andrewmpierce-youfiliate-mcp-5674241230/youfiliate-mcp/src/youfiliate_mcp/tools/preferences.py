"""Preferences tools (2 tools).

Tools:
  - youfiliate_get_preferences
  - youfiliate_update_preferences
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import YoufiliateClient, make_api_call
from ..schemas.analytics import GetPreferencesInput, UpdatePreferencesInput
from ..schemas.common import ResponseFormat


def _format_preferences_markdown(data: dict[str, Any]) -> str:
    """Format preferences as markdown."""
    lines = [
        "# Your Smart Link Preferences",
        "",
        f"- **Default Redirect Type**: {data.get('default_redirect_type', '302')}",
        f"- **Geo-Targeting Enabled by Default**: {data.get('default_geo_rules_enabled', False)}",
        f"- **Deep Linking Enabled by Default**: {data.get('default_deep_linking_enabled', False)}",
        "",
    ]
    return "\n".join(lines)


def register_preferences_tools(mcp: FastMCP, client: YoufiliateClient) -> None:
    """Register preferences tools."""

    @mcp.tool(
        name="youfiliate_get_preferences",
        annotations={
            "title": "Get Preferences",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_get_preferences(params: GetPreferencesInput) -> str:
        """Get your current smart link preferences/defaults.

        Returns default settings applied to newly created smart links.
        Does NOT create or modify any data.
        """
        ok, result = await make_api_call(
            client, "GET", "/api/smart-links/preferences/"
        )
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        return _format_preferences_markdown(result)

    @mcp.tool(
        name="youfiliate_update_preferences",
        annotations={
            "title": "Update Preferences",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_update_preferences(params: UpdatePreferencesInput) -> str:
        """Update your smart link preferences/defaults.

        Changes apply to newly created links only — existing links are
        not affected. Does NOT delete any data.

        Common errors:
        - Invalid redirect_type: must be '301' or '302'.
        """
        body: dict[str, Any] = {}
        if params.default_redirect_type is not None:
            body["default_redirect_type"] = params.default_redirect_type
        if params.default_geo_rules_enabled is not None:
            body["default_geo_rules_enabled"] = params.default_geo_rules_enabled
        if params.default_deep_linking_enabled is not None:
            body["default_deep_linking_enabled"] = params.default_deep_linking_enabled

        if not body:
            return "Error: No preferences to update. Provide at least one field."

        ok, result = await make_api_call(
            client, "PATCH", "/api/smart-links/preferences/", json=body
        )
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        return "# Preferences Updated\n\n" + _format_preferences_markdown(result)

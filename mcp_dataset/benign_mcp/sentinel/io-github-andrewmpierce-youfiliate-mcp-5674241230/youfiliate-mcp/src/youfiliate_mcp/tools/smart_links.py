"""Smart link CRUD tools (5 tools).

Tools:
  - youfiliate_create_smart_link
  - youfiliate_list_smart_links
  - youfiliate_get_smart_link
  - youfiliate_update_smart_link
  - youfiliate_delete_smart_link
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import YoufiliateClient, make_api_call
from ..config import settings as app_settings
from ..schemas.common import ResponseFormat, format_pagination_header
from ..schemas.smart_links import (
    CreateSmartLinkInput,
    DeleteSmartLinkInput,
    GetSmartLinkInput,
    ListSmartLinksInput,
    UpdateSmartLinkInput,
)

TRUNCATION_MSG = "\n\n[Truncated — use filters or pagination to narrow results]"


def _truncate(text: str) -> str:
    limit = app_settings.max_response_chars
    if len(text) > limit:
        return text[:limit] + TRUNCATION_MSG
    return text


def _format_smart_link_markdown(link: dict[str, Any]) -> str:
    """Format a single smart link as markdown."""
    lines = [
        f"## {link.get('title') or link.get('slug', 'Untitled')}",
        "",
        f"- **ID**: `{link.get('id', 'N/A')}`",
        f"- **Short URL**: youfil.to/{link.get('slug', '')}",
        f"- **Destination**: {link.get('default_url', 'N/A')}",
        f"- **Redirect**: {link.get('redirect_type', '302')}",
        f"- **Health**: {link.get('health_status', 'unknown')}",
        f"- **Clicks**: {link.get('total_clicks', 0)} total, {link.get('daily_clicks', 0)} today",
        f"- **Created**: {link.get('created_at', 'N/A')}",
    ]

    geo_rules = link.get("geo_rules", [])
    if geo_rules:
        lines.append(f"- **Geo Rules** ({len(geo_rules)}):")
        for rule in geo_rules:
            lines.append(f"  - {rule.get('country_code', '??')}: {rule.get('destination_url', '')}")

    deep = link.get("deep_link_config")
    if deep:
        lines.append("- **Deep Linking**: Enabled")
        if deep.get("ios_app_url"):
            lines.append(f"  - iOS: {deep['ios_app_url']}")
        if deep.get("android_app_url"):
            lines.append(f"  - Android: {deep['android_app_url']}")

    lines.append("")
    return "\n".join(lines)


def register_smart_link_tools(mcp: FastMCP, client: YoufiliateClient) -> None:
    """Register all 5 smart link CRUD tools on the MCP server."""

    @mcp.tool(
        name="youfiliate_create_smart_link",
        annotations={
            "title": "Create Smart Link",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": False,
            "openWorldHint": False,
        },
    )
    async def youfiliate_create_smart_link(params: CreateSmartLinkInput) -> str:
        """Create a new geo-targeted smart link with an optional custom slug.

        Creates a smart link that redirects visitors to the destination URL.
        Optionally configure country-specific geo rules and deep linking for
        iOS/Android apps. Does NOT modify any existing links.

        Returns the created smart link details including its short URL
        (youfil.to/<slug>).

        Common errors:
        - Slug already taken: choose a different slug or omit for auto-generation.
        - Plan limit reached: upgrade your plan to create more links.
        - Invalid URL: ensure the destination URL is a valid HTTP/HTTPS URL.
        """
        body: dict[str, Any] = {"default_url": str(params.default_url)}
        if params.slug is not None:
            body["slug"] = params.slug
        if params.title is not None:
            body["title"] = params.title
        body["redirect_type"] = params.redirect_type
        if params.geo_rules:
            body["geo_rules"] = [r.model_dump() for r in params.geo_rules]
        if params.deep_link_config:
            body["deep_link_config"] = params.deep_link_config.model_dump(exclude_none=True)

        ok, result = await make_api_call(client, "POST", "/api/smart-links/", json=body)
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return _truncate(json.dumps(result, indent=2))

        return _truncate(
            "# Smart Link Created\n\n" + _format_smart_link_markdown(result)
        )

    @mcp.tool(
        name="youfiliate_list_smart_links",
        annotations={
            "title": "List Smart Links",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_list_smart_links(params: ListSmartLinksInput) -> str:
        """List your smart links with optional filtering, search, and pagination.

        Returns a paginated list of smart links. Use filters to narrow results.
        Does NOT create or modify any links.

        Args:
            params: Filters include health_status, search (title/URL), ordering,
                    limit (1-100, default 20), and offset.

        Common errors:
        - No links found: you may not have created any links yet.
        """
        query: dict[str, Any] = {
            "limit": params.limit,
            "offset": params.offset,
        }
        if params.health_status:
            query["health_status"] = params.health_status
        if params.search:
            query["search"] = params.search
        if params.ordering:
            query["ordering"] = params.ordering

        ok, result = await make_api_call(client, "GET", "/api/smart-links/", params=query)
        if not ok:
            return result

        # DRF paginated response
        if isinstance(result, dict) and "results" in result:
            items = result["results"]
            total = result.get("count", len(items))
        elif isinstance(result, list):
            items = result
            total = len(items)
        else:
            items = []
            total = 0

        if params.response_format == ResponseFormat.JSON:
            return _truncate(json.dumps({
                "total": total,
                "count": len(items),
                "offset": params.offset,
                "items": items,
                "has_more": total > params.offset + len(items),
                "next_offset": params.offset + len(items) if total > params.offset + len(items) else None,
            }, indent=2))

        if not items:
            return "No smart links found. Create one with `youfiliate_create_smart_link`."

        lines = [
            "# Smart Links",
            "",
            format_pagination_header(total, params.offset, len(items)),
            "",
        ]
        for link in items:
            lines.append(_format_smart_link_markdown(link))

        return _truncate("\n".join(lines))

    @mcp.tool(
        name="youfiliate_get_smart_link",
        annotations={
            "title": "Get Smart Link Details",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_get_smart_link(params: GetSmartLinkInput) -> str:
        """Get full details of a single smart link by ID.

        Returns all configuration including geo rules, deep link config,
        and click stats. Does NOT modify the link.

        Common errors:
        - Smart link not found: check the ID or use `youfiliate_list_smart_links`.
        """
        ok, result = await make_api_call(client, "GET", f"/api/smart-links/{params.id}/")
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return _truncate(json.dumps(result, indent=2))

        return _truncate(
            "# Smart Link Details\n\n" + _format_smart_link_markdown(result)
        )

    @mcp.tool(
        name="youfiliate_update_smart_link",
        annotations={
            "title": "Update Smart Link",
            "readOnlyHint": False,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_update_smart_link(params: UpdateSmartLinkInput) -> str:
        """Update an existing smart link (partial update — only provided fields change).

        You can update the destination URL, slug, title, redirect type,
        geo rules, or deep link config. Geo rules are replaced entirely
        (not merged). Does NOT delete the link.

        Common errors:
        - Smart link not found: check the ID.
        - Slug already taken: choose a different slug.
        """
        body: dict[str, Any] = {}
        if params.default_url is not None:
            body["default_url"] = str(params.default_url)
        if params.slug is not None:
            body["slug"] = params.slug
        if params.title is not None:
            body["title"] = params.title
        if params.redirect_type is not None:
            body["redirect_type"] = params.redirect_type
        if params.geo_rules is not None:
            body["geo_rules"] = [r.model_dump() for r in params.geo_rules]
        if params.deep_link_config is not None:
            body["deep_link_config"] = params.deep_link_config.model_dump(exclude_none=True)

        if not body:
            return "Error: No fields to update. Provide at least one field to change."

        ok, result = await make_api_call(
            client, "PATCH", f"/api/smart-links/{params.id}/", json=body
        )
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return _truncate(json.dumps(result, indent=2))

        return _truncate(
            "# Smart Link Updated\n\n" + _format_smart_link_markdown(result)
        )

    @mcp.tool(
        name="youfiliate_delete_smart_link",
        annotations={
            "title": "Delete Smart Link",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_delete_smart_link(params: DeleteSmartLinkInput) -> str:
        """Delete a smart link permanently. The short URL will stop working.

        IMPORTANT: Always confirm with the user before executing this action.
        The `confirm` parameter must be set to true. This is a destructive
        action that cannot be undone — the slug becomes available for reuse
        after a cooldown period.

        Does NOT affect other links or YouTube descriptions.

        Common errors:
        - Smart link not found: check the ID.
        - confirm=False: you must set confirm=True after getting user confirmation.
        """
        if not params.confirm:
            return (
                "Deletion requires confirmation. Please confirm with the user that they "
                "want to delete this smart link, then call again with confirm=True."
            )

        ok, result = await make_api_call(
            client, "DELETE", f"/api/smart-links/{params.id}/"
        )
        if not ok:
            return result

        return f"Smart link `{params.id}` has been deleted. The short URL will no longer redirect."

"""YouTube description migration tools (5 tools).

Tools:
  - youfiliate_preview_migration
  - youfiliate_start_migration
  - youfiliate_get_migration_status
  - youfiliate_list_migrations
  - youfiliate_rollback_migration
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..client import YoufiliateClient, make_api_call
from ..config import settings as app_settings
from ..schemas.common import ResponseFormat, format_pagination_header
from ..schemas.migrations import (
    GetMigrationStatusInput,
    ListMigrationsInput,
    PreviewMigrationInput,
    RollbackMigrationInput,
    StartMigrationInput,
)


def _truncate(text: str) -> str:
    limit = app_settings.max_response_chars
    if len(text) > limit:
        return text[:limit] + "\n\n[Truncated — use filters or pagination to narrow results]"
    return text


def _format_migration_markdown(m: dict[str, Any]) -> str:
    """Format a single migration as markdown."""
    lines = [
        f"## Migration {m.get('id', 'N/A')[:8]}...",
        "",
        f"- **Status**: {m.get('status', 'unknown')}",
        f"- **Mode**: {m.get('conversion_mode', 'N/A')}",
        f"- **Auto Geo Rules**: {m.get('auto_geo_rules', 'N/A')}",
        f"- **Videos**: {m.get('videos_processed', 0)}/{m.get('videos_total', 0)}",
        f"- **Links Created**: {m.get('links_created', 0)}",
        f"- **Links Skipped**: {m.get('links_skipped', 0)}",
        f"- **Created**: {m.get('created_at', 'N/A')}",
    ]
    if m.get("error_message"):
        lines.append(f"- **Error**: {m['error_message']}")
    lines.append("")
    return "\n".join(lines)


def register_migration_tools(mcp: FastMCP, client: YoufiliateClient) -> None:
    """Register migration tools."""

    @mcp.tool(
        name="youfiliate_preview_migration",
        annotations={
            "title": "Preview Migration",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_preview_migration(params: PreviewMigrationInput) -> str:
        """Preview a YouTube description migration without making changes.

        Performs a dry-run analysis showing how many videos and links would be
        affected. Does NOT modify any data or YouTube descriptions. Requires
        a connected YouTube account.

        Common errors:
        - YouTube not connected: connect first with `youfiliate_connect_youtube`.
        """
        body = {
            "conversion_mode": params.conversion_mode,
            "auto_geo_rules": params.auto_geo_rules,
        }
        ok, result = await make_api_call(
            client, "POST", "/api/smart-links/migrations/preview/", json=body
        )
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        lines = [
            "# Migration Preview",
            "",
            f"- **Videos to Process**: {result.get('videos_count', 0)}",
            f"- **Links to Convert**: {result.get('links_count', 0)}",
            f"- **Conversion Mode**: {result.get('conversion_mode', params.conversion_mode)}",
            f"- **Auto Geo Rules**: {result.get('auto_geo_rules', params.auto_geo_rules)}",
            "",
        ]

        videos = result.get("videos", [])
        if videos:
            lines.append("## Videos")
            for v in videos[:20]:
                lines.append(
                    f"- {v.get('title', 'Untitled')} — "
                    f"{v.get('links_count', 0)} links"
                )
            if len(videos) > 20:
                lines.append(f"  ...and {len(videos) - 20} more")
            lines.append("")

        lines.append(
            "To start the migration, use `youfiliate_start_migration` "
            "with confirm=True after confirming with the user."
        )

        return _truncate("\n".join(lines))

    @mcp.tool(
        name="youfiliate_start_migration",
        annotations={
            "title": "Start YouTube Migration",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def youfiliate_start_migration(params: StartMigrationInput) -> str:
        """Start a YouTube description migration to convert links to smart links.

        IMPORTANT: This modifies YouTube video descriptions. Always confirm with
        the user before executing. Describe the scope (number of videos/links
        affected from the preview) and ask for explicit confirmation.

        The migration runs asynchronously. Use `youfiliate_get_migration_status`
        to track progress.

        Requires a connected YouTube account.

        Common errors:
        - YouTube not connected: connect first.
        - Migration already in progress: wait for it to complete.
        - confirm=False: must set confirm=True after user confirmation.
        """
        if not params.confirm:
            return (
                "Migration requires confirmation. Please:\n"
                "1. Run `youfiliate_preview_migration` to see the scope\n"
                "2. Show the user how many videos/links will be affected\n"
                "3. Ask for explicit confirmation\n"
                "4. Call again with confirm=True"
            )

        body = {
            "conversion_mode": params.conversion_mode,
            "auto_geo_rules": params.auto_geo_rules,
        }
        ok, result = await make_api_call(
            client, "POST", "/api/smart-links/migrations/", json=body
        )
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return json.dumps(result, indent=2)

        mid = result.get("id", "N/A")
        return (
            "# Migration Started\n\n"
            f"Migration ID: `{mid}`\n\n"
            f"Status: {result.get('status', 'pending')}\n\n"
            "The migration is running in the background. "
            f"Use `youfiliate_get_migration_status` with id='{mid}' to track progress."
        )

    @mcp.tool(
        name="youfiliate_get_migration_status",
        annotations={
            "title": "Get Migration Status",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_get_migration_status(params: GetMigrationStatusInput) -> str:
        """Get the status and progress of a specific migration.

        Returns detailed status including videos processed, links created,
        and any errors. Does NOT modify any data.

        Common errors:
        - Migration not found: check the ID or use `youfiliate_list_migrations`.
        """
        ok, result = await make_api_call(
            client, "GET", f"/api/smart-links/migrations/{params.id}/"
        )
        if not ok:
            return result

        if params.response_format == ResponseFormat.JSON:
            return _truncate(json.dumps(result, indent=2))

        return _truncate(
            "# Migration Status\n\n" + _format_migration_markdown(result)
        )

    @mcp.tool(
        name="youfiliate_list_migrations",
        annotations={
            "title": "List Migrations",
            "readOnlyHint": True,
            "destructiveHint": False,
            "idempotentHint": True,
            "openWorldHint": False,
        },
    )
    async def youfiliate_list_migrations(params: ListMigrationsInput) -> str:
        """List your YouTube description migrations with pagination.

        Returns a paginated list of all migrations. Does NOT modify any data.
        """
        ok, result = await make_api_call(
            client,
            "GET",
            "/api/smart-links/migrations/",
            params={"limit": params.limit, "offset": params.offset},
        )
        if not ok:
            return result

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
            return "No migrations found. Use `youfiliate_preview_migration` to plan one."

        lines = [
            "# Migrations",
            "",
            format_pagination_header(total, params.offset, len(items)),
            "",
        ]
        for m in items:
            lines.append(_format_migration_markdown(m))

        return _truncate("\n".join(lines))

    @mcp.tool(
        name="youfiliate_rollback_migration",
        annotations={
            "title": "Rollback Migration",
            "readOnlyHint": False,
            "destructiveHint": True,
            "idempotentHint": False,
            "openWorldHint": True,
        },
    )
    async def youfiliate_rollback_migration(params: RollbackMigrationInput) -> str:
        """Roll back a completed migration, restoring original YouTube descriptions.

        IMPORTANT: This modifies YouTube video descriptions. Always confirm with
        the user before executing. This reverts all video descriptions to their
        pre-migration state.

        The rollback runs asynchronously. Requires a connected YouTube account.

        Common errors:
        - Migration not found or not in a rollback-eligible state.
        - YouTube not connected: reconnect first.
        - confirm=False: must set confirm=True after user confirmation.
        """
        if not params.confirm:
            return (
                "Rollback requires confirmation. Please confirm with the user "
                "that they want to revert their YouTube video descriptions to "
                "the pre-migration state, then call again with confirm=True."
            )

        ok, result = await make_api_call(
            client, "POST", f"/api/smart-links/migrations/{params.id}/rollback/"
        )
        if not ok:
            return result

        return (
            f"# Rollback Started\n\n"
            f"Migration `{params.id}` is being rolled back. "
            f"Original descriptions will be restored.\n\n"
            f"Use `youfiliate_get_migration_status` to track rollback progress."
        )

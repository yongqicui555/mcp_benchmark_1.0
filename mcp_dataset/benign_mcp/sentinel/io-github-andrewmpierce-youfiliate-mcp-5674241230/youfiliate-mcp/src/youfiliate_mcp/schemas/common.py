"""Shared schema models used across multiple tools."""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


# Reusable UUID pattern for all id fields (prevents path traversal)
UUID_PATTERN = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"

# URL must be http or https (blocks javascript:, file://, data: schemes)
HTTP_URL_PATTERN = r"^https?://.+"


class ResponseFormat(str, Enum):
    """Output format for tool responses."""
    MARKDOWN = "markdown"
    JSON = "json"


class PaginatedInput(BaseModel):
    """Base model for paginated list inputs."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    limit: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Maximum results to return (1-100, default 20)",
    )
    offset: int = Field(
        default=0,
        ge=0,
        description="Number of results to skip for pagination (default 0)",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' (default) or 'json'",
    )


def format_pagination_header(total: int, offset: int, count: int) -> str:
    """Build a pagination summary line for markdown output."""
    start = offset + 1
    end = offset + count
    parts = [f"Total: {total}", f"Showing: {start}-{end}"]
    if offset + count < total:
        parts.append(f"Next offset: {offset + count}")
    return " | ".join(parts)

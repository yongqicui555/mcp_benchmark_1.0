"""Pydantic input schemas for YouTube migration tools."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import UUID_PATTERN, PaginatedInput, ResponseFormat


class PreviewMigrationInput(BaseModel):
    """Input for previewing a YouTube description migration."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    conversion_mode: Literal["all", "affiliate_only"] = Field(
        "affiliate_only",
        description="Which links to convert: 'all' converts every link, 'affiliate_only' only converts detected affiliate links",
    )
    auto_geo_rules: bool = Field(
        True,
        description="Whether to auto-generate geo rules (e.g., Amazon international storefronts)",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class StartMigrationInput(BaseModel):
    """Input for starting a YouTube description migration."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    conversion_mode: Literal["all", "affiliate_only"] = Field(
        "affiliate_only",
        description="Which links to convert",
    )
    auto_geo_rules: bool = Field(
        True,
        description="Whether to auto-generate geo rules",
    )
    confirm: bool = Field(
        False,
        description="Must be set to true to confirm migration. IMPORTANT: This modifies YouTube video descriptions. Always describe the scope (number of videos/links) and ask for explicit user confirmation before setting this to true.",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class GetMigrationStatusInput(BaseModel):
    """Input for getting a specific migration's status."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(
        ...,
        pattern=UUID_PATTERN,
        description="Migration UUID",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class ListMigrationsInput(PaginatedInput):
    """Input for listing migrations."""
    pass


class RollbackMigrationInput(BaseModel):
    """Input for rolling back a migration."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(
        ...,
        pattern=UUID_PATTERN,
        description="Migration UUID to roll back",
    )
    confirm: bool = Field(
        False,
        description="Must be set to true to confirm rollback. IMPORTANT: This reverts YouTube video descriptions to their pre-migration state. Always confirm with the user before setting this to true.",
    )

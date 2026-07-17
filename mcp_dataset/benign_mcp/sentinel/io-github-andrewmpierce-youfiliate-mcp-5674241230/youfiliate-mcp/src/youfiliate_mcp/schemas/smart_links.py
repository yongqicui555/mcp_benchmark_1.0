"""Pydantic input schemas for smart link tools."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, HttpUrl

from .common import HTTP_URL_PATTERN, UUID_PATTERN, PaginatedInput, ResponseFormat


class GeoRuleInput(BaseModel):
    """Country-specific destination URL."""
    model_config = ConfigDict(extra="forbid")

    country_code: str = Field(
        ...,
        pattern=r"^[A-Z]{2}$",
        description="ISO 3166-1 alpha-2 country code (e.g., 'GB', 'DE', 'JP')",
    )
    destination_url: str = Field(
        ...,
        pattern=HTTP_URL_PATTERN,
        description="URL to redirect visitors from this country to",
    )


class DeepLinkConfigInput(BaseModel):
    """iOS/Android app-opening configuration."""
    model_config = ConfigDict(extra="forbid")

    ios_app_url: Optional[str] = Field(
        None,
        description="iOS app deep link URL (e.g., 'amazon://...')",
    )
    ios_fallback_url: Optional[str] = Field(
        None,
        description="Fallback URL if iOS app is not installed",
    )
    android_app_url: Optional[str] = Field(
        None,
        description="Android app deep link URL",
    )
    android_fallback_url: Optional[str] = Field(
        None,
        description="Fallback URL if Android app is not installed",
    )


class CreateSmartLinkInput(BaseModel):
    """Input for creating a new smart link."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    default_url: str = Field(
        ...,
        pattern=HTTP_URL_PATTERN,
        description="The destination URL for this smart link",
    )
    slug: Optional[str] = Field(
        None,
        pattern=r"^[a-z0-9-]+$",
        max_length=50,
        description="Custom short URL slug (auto-generated if omitted). Lowercase alphanumeric + hyphens only.",
    )
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="Human-readable label for this link",
    )
    redirect_type: Literal["301", "302"] = Field(
        "302",
        description="HTTP redirect type. Use 302 (default) for links that may change, 301 for permanent.",
    )
    geo_rules: Optional[list[GeoRuleInput]] = Field(
        None,
        description="Country-specific destination URLs for geo-targeting",
    )
    deep_link_config: Optional[DeepLinkConfigInput] = Field(
        None,
        description="iOS/Android app-opening configuration",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class ListSmartLinksInput(PaginatedInput):
    """Input for listing smart links with optional filters."""

    health_status: Optional[Literal["healthy", "broken", "unknown"]] = Field(
        None,
        description="Filter by health status",
    )
    search: Optional[str] = Field(
        None,
        description="Search by title or URL",
    )
    ordering: Optional[Literal[
        "created_at", "-created_at",
        "total_clicks", "-total_clicks",
        "daily_clicks", "-daily_clicks",
        "weekly_clicks", "-weekly_clicks",
        "title", "-title",
    ]] = Field(
        None,
        description="Sort field (e.g., '-created_at', 'total_clicks', '-total_clicks')",
    )


class GetSmartLinkInput(BaseModel):
    """Input for getting a single smart link."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(
        ...,
        pattern=UUID_PATTERN,
        description="Smart link UUID",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class UpdateSmartLinkInput(BaseModel):
    """Input for updating a smart link (partial update)."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(
        ...,
        pattern=UUID_PATTERN,
        description="Smart link UUID to update",
    )
    default_url: Optional[str] = Field(
        None,
        pattern=HTTP_URL_PATTERN,
        description="New destination URL",
    )
    slug: Optional[str] = Field(
        None,
        pattern=r"^[a-z0-9-]+$",
        max_length=50,
        description="New custom slug",
    )
    title: Optional[str] = Field(
        None,
        max_length=200,
        description="New title/label",
    )
    redirect_type: Optional[Literal["301", "302"]] = Field(
        None,
        description="New redirect type",
    )
    geo_rules: Optional[list[GeoRuleInput]] = Field(
        None,
        description="Replace geo rules (full replacement, not merge)",
    )
    deep_link_config: Optional[DeepLinkConfigInput] = Field(
        None,
        description="Replace deep link config",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class DeleteSmartLinkInput(BaseModel):
    """Input for deleting a smart link."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(
        ...,
        pattern=UUID_PATTERN,
        description="Smart link UUID to delete",
    )
    confirm: bool = Field(
        False,
        description="Must be set to true to confirm deletion. IMPORTANT: Always confirm with the user before setting this to true.",
    )

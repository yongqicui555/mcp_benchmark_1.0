"""Pydantic input schemas for analytics and preferences tools."""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .common import UUID_PATTERN, ResponseFormat


class GetSmartLinkStatsInput(BaseModel):
    """Input for getting click analytics for a single smart link."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(
        ...,
        pattern=UUID_PATTERN,
        description="Smart link UUID",
    )
    period: Literal["7d", "30d", "90d", "all"] = Field(
        "30d",
        description="Time period for stats: '7d', '30d', '90d', or 'all'",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class GetAggregateStatsInput(BaseModel):
    """Input for getting aggregate analytics across all smart links."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    period: Literal["7d", "30d", "90d", "all"] = Field(
        "30d",
        description="Time period for stats: '7d', '30d', '90d', or 'all'",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class CheckLinkHealthInput(BaseModel):
    """Input for triggering a health check on a smart link."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    id: str = Field(
        ...,
        pattern=UUID_PATTERN,
        description="Smart link UUID to check",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class GetPreferencesInput(BaseModel):
    """Input for getting user preferences."""
    model_config = ConfigDict(extra="forbid")

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class UpdatePreferencesInput(BaseModel):
    """Input for updating user preferences."""
    model_config = ConfigDict(str_strip_whitespace=True, extra="forbid")

    default_redirect_type: Optional[Literal["301", "302"]] = Field(
        None,
        description="Default redirect type for new smart links",
    )
    default_geo_rules_enabled: Optional[bool] = Field(
        None,
        description="Whether geo-targeting is enabled by default for new links",
    )
    default_deep_linking_enabled: Optional[bool] = Field(
        None,
        description="Whether deep linking is enabled by default for new links",
    )
    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )

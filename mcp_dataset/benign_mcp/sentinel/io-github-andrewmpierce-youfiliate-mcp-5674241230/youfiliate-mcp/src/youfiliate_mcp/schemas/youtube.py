"""Pydantic input schemas for YouTube OAuth tools."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from .common import ResponseFormat


class GetYouTubeStatusInput(BaseModel):
    """Input for checking YouTube connection status."""
    model_config = ConfigDict(extra="forbid")

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class ConnectYouTubeInput(BaseModel):
    """Input for initiating YouTube OAuth connection."""
    model_config = ConfigDict(extra="forbid")

    response_format: ResponseFormat = Field(
        default=ResponseFormat.MARKDOWN,
        description="Output format: 'markdown' or 'json'",
    )


class DisconnectYouTubeInput(BaseModel):
    """Input for disconnecting YouTube account."""
    model_config = ConfigDict(extra="forbid")

    confirm: bool = Field(
        False,
        description="Must be set to true to confirm disconnection. IMPORTANT: Always confirm with the user before setting this to true.",
    )

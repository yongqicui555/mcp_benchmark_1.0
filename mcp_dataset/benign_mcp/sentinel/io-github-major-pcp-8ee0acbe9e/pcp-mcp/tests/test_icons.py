"""Tests for icons and tags module."""

import pytest
from mcp.types import Icon

from pcp_mcp import icons


class TestIcons:
    @pytest.mark.parametrize(
        "icon_name",
        [
            "ICON_METRICS",
            "ICON_SEARCH",
            "ICON_INFO",
            "ICON_SYSTEM",
            "ICON_PROCESS",
            "ICON_HEALTH",
            "ICON_CATALOG",
            "ICON_NAMESPACE",
            "ICON_DIAGNOSE",
            "ICON_CPU",
            "ICON_MEMORY",
            "ICON_DISK",
            "ICON_NETWORK",
        ],
    )
    def test_icon_is_valid_mcp_icon(self, icon_name: str) -> None:
        icon = getattr(icons, icon_name)
        assert isinstance(icon, Icon)
        assert icon.src.startswith("data:,")
        assert icon.mimeType == "text/plain"


class TestTags:
    @pytest.mark.parametrize(
        "tag_name",
        [
            "TAGS_METRICS",
            "TAGS_SYSTEM",
            "TAGS_PROCESS",
            "TAGS_HEALTH",
            "TAGS_CATALOG",
            "TAGS_DISCOVERY",
            "TAGS_CPU",
            "TAGS_MEMORY",
            "TAGS_DISK",
            "TAGS_NETWORK",
            "TAGS_DIAGNOSE",
        ],
    )
    def test_tags_are_string_sets(self, tag_name: str) -> None:
        tags = getattr(icons, tag_name)
        assert isinstance(tags, set)
        assert all(isinstance(t, str) for t in tags)
        assert len(tags) >= 1

    def test_tags_can_be_combined(self) -> None:
        combined = icons.TAGS_METRICS | icons.TAGS_DISCOVERY
        assert "metrics" in combined
        assert "discovery" in combined

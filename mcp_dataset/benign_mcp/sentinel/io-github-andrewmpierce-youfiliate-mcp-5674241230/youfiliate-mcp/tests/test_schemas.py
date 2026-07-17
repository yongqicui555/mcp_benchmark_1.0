"""Tests for Pydantic input schema validation."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from youfiliate_mcp.schemas.smart_links import (
    CreateSmartLinkInput,
    DeleteSmartLinkInput,
    GeoRuleInput,
    ListSmartLinksInput,
    UpdateSmartLinkInput,
)
from youfiliate_mcp.schemas.analytics import (
    GetSmartLinkStatsInput,
    UpdatePreferencesInput,
)
from youfiliate_mcp.schemas.migrations import (
    PreviewMigrationInput,
    StartMigrationInput,
)


class TestCreateSmartLinkInput:
    def test_valid_minimal(self) -> None:
        params = CreateSmartLinkInput(default_url="https://amazon.com/dp/B09V3KXJPB")
        assert params.redirect_type == "302"
        assert params.slug is None

    def test_valid_full(self) -> None:
        params = CreateSmartLinkInput(
            default_url="https://amazon.com/dp/B09V3KXJPB",
            slug="my-link",
            title="Test Link",
            redirect_type="301",
            geo_rules=[{"country_code": "GB", "destination_url": "https://amazon.co.uk/dp/B09V3KXJPB"}],
        )
        assert params.slug == "my-link"
        assert len(params.geo_rules) == 1

    def test_invalid_slug_uppercase(self) -> None:
        with pytest.raises(ValidationError) as exc_info:
            CreateSmartLinkInput(
                default_url="https://amazon.com/dp/B09V3KXJPB",
                slug="My-Link",
            )
        assert "slug" in str(exc_info.value)

    def test_invalid_slug_spaces(self) -> None:
        with pytest.raises(ValidationError):
            CreateSmartLinkInput(
                default_url="https://amazon.com/dp/B09V3KXJPB",
                slug="my link",
            )

    def test_slug_too_long(self) -> None:
        with pytest.raises(ValidationError):
            CreateSmartLinkInput(
                default_url="https://amazon.com",
                slug="a" * 51,
            )

    def test_invalid_redirect_type(self) -> None:
        with pytest.raises(ValidationError):
            CreateSmartLinkInput(
                default_url="https://amazon.com",
                redirect_type="307",
            )

    def test_extra_fields_rejected(self) -> None:
        with pytest.raises(ValidationError):
            CreateSmartLinkInput(
                default_url="https://amazon.com",
                unknown_field="bad",
            )


class TestGeoRuleInput:
    def test_valid(self) -> None:
        rule = GeoRuleInput(country_code="GB", destination_url="https://amazon.co.uk")
        assert rule.country_code == "GB"

    def test_invalid_country_code_lowercase(self) -> None:
        with pytest.raises(ValidationError):
            GeoRuleInput(country_code="gb", destination_url="https://amazon.co.uk")

    def test_invalid_country_code_length(self) -> None:
        with pytest.raises(ValidationError):
            GeoRuleInput(country_code="GBR", destination_url="https://amazon.co.uk")


class TestListSmartLinksInput:
    def test_defaults(self) -> None:
        params = ListSmartLinksInput()
        assert params.limit == 20
        assert params.offset == 0

    def test_limit_bounds(self) -> None:
        with pytest.raises(ValidationError):
            ListSmartLinksInput(limit=0)
        with pytest.raises(ValidationError):
            ListSmartLinksInput(limit=101)

    def test_negative_offset(self) -> None:
        with pytest.raises(ValidationError):
            ListSmartLinksInput(offset=-1)

    def test_valid_health_status(self) -> None:
        params = ListSmartLinksInput(health_status="broken")
        assert params.health_status == "broken"

    def test_invalid_health_status(self) -> None:
        with pytest.raises(ValidationError):
            ListSmartLinksInput(health_status="invalid")


class TestDeleteSmartLinkInput:
    def test_confirm_defaults_false(self) -> None:
        params = DeleteSmartLinkInput(id="00000000-0000-0000-0000-000000000000")
        assert params.confirm is False


class TestUpdateSmartLinkInput:
    def test_all_none(self) -> None:
        """All optional fields can be None (validation is in the tool)."""
        params = UpdateSmartLinkInput(id="00000000-0000-0000-0000-000000000000")
        assert params.default_url is None
        assert params.slug is None


class TestGetSmartLinkStatsInput:
    def test_valid_periods(self) -> None:
        for period in ("7d", "30d", "90d", "all"):
            params = GetSmartLinkStatsInput(id="00000000-0000-0000-0000-000000000000", period=period)
            assert params.period == period

    def test_invalid_period(self) -> None:
        with pytest.raises(ValidationError):
            GetSmartLinkStatsInput(id="00000000-0000-0000-0000-000000000000", period="1y")


class TestStartMigrationInput:
    def test_confirm_defaults_false(self) -> None:
        params = StartMigrationInput()
        assert params.confirm is False

    def test_valid_conversion_modes(self) -> None:
        for mode in ("all", "affiliate_only"):
            params = StartMigrationInput(conversion_mode=mode)
            assert params.conversion_mode == mode

    def test_invalid_conversion_mode(self) -> None:
        with pytest.raises(ValidationError):
            StartMigrationInput(conversion_mode="invalid")

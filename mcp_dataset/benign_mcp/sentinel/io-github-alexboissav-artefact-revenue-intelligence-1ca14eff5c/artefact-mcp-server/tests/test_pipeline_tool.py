"""Tests for score_pipeline tool."""

import pytest

from artefact_mcp.tools.pipeline import score_pipeline


class TestScorePipelineTool:
    def test_sample_pipeline(self):
        result = score_pipeline(source="sample")
        assert result["total_deals"] == 8
        assert result["total_value"] > 0
        assert 0 <= result["health_score"] <= 100
        assert result["health_label"] in ("Healthy", "Warning", "Critical")

    def test_velocity_metrics(self):
        result = score_pipeline(source="sample")
        assert "velocity" in result
        velocity = result["velocity"]
        assert "avg_days_per_stage" in velocity
        assert "bottleneck_stage" in velocity
        assert "overall_cycle_days" in velocity
        assert isinstance(velocity["overall_cycle_days"], int)

    def test_conversion_rates(self):
        result = score_pipeline(source="sample")
        assert "conversion_rates" in result
        rates = result["conversion_rates"]
        for key, value in rates.items():
            assert "->" in key
            assert 0 <= value <= 100

    def test_at_risk_deals(self):
        result = score_pipeline(source="sample")
        assert "at_risk_deals" in result
        # Sample data includes stalled deals
        assert len(result["at_risk_deals"]) > 0
        for deal in result["at_risk_deals"]:
            assert "name" in deal
            assert "risk_reasons" in deal
            assert len(deal["risk_reasons"]) > 0

    def test_stage_distribution(self):
        result = score_pipeline(source="sample")
        assert "stage_distribution" in result
        total_count = sum(s["count"] for s in result["stage_distribution"].values())
        assert total_count == 8

    def test_invalid_source(self):
        with pytest.raises(ValueError, match="Invalid source"):
            score_pipeline(source="invalid")

    def test_hubspot_without_client(self):
        with pytest.raises(ValueError, match="HubSpot client required"):
            score_pipeline(source="hubspot")

"""Tests for value engine analysis tool."""

import pytest

from artefact_mcp.tools.engines import analyze_engine, ENGINE_DEFINITIONS


class TestAnalyzeEngine:
    def test_growth_engine(self):
        result = analyze_engine(engine_type="growth", source="sample")
        assert result["engine"]["type"] == "growth"
        assert result["engine"]["label"] == "Growth Engine"
        assert "analysis" in result
        assert "health_score" in result["analysis"]
        assert 0 <= result["analysis"]["health_score"] <= 100

    def test_fulfillment_engine(self):
        result = analyze_engine(engine_type="fulfillment", source="sample")
        assert result["engine"]["type"] == "fulfillment"
        assert result["engine"]["label"] == "Fulfillment Engine"
        assert "analysis" in result
        assert "data_gaps" in result["analysis"]

    def test_innovation_engine(self):
        result = analyze_engine(engine_type="innovation", source="sample")
        assert result["engine"]["type"] == "innovation"
        assert result["engine"]["label"] == "Innovation Engine"
        assert "analysis" in result
        assert "data_gaps" in result["analysis"]

    def test_engine_definition_fields(self):
        for engine_type in ENGINE_DEFINITIONS:
            result = analyze_engine(engine_type=engine_type, source="sample")
            engine = result["engine"]
            assert "type" in engine
            assert "label" in engine
            assert "purpose" in engine
            assert "artefact_pillars" in engine
            assert "stages" in engine
            assert "key_metrics" in engine
            assert len(engine["stages"]) > 0
            assert len(engine["key_metrics"]) > 0

    def test_growth_engine_metrics(self):
        result = analyze_engine(engine_type="growth", source="sample")
        metrics = result["analysis"]["metrics"]
        assert "pipeline_volume" in metrics
        assert "avg_conversion_rate" in metrics
        assert "cycle_days" in metrics
        assert "deal_progression" in metrics

    def test_growth_engine_signals(self):
        result = analyze_engine(engine_type="growth", source="sample")
        signals = result["analysis"].get("signals", [])
        for signal in signals:
            assert signal["signal_type"] in (
                "conversion_drop_off", "velocity_anomaly", "win_loss_pattern"
            )

    def test_methodology_resource_reference(self):
        result = analyze_engine(engine_type="growth", source="sample")
        assert result["methodology_resource"] == "methodology://value-engines"

    def test_invalid_engine_type(self):
        with pytest.raises(ValueError, match="Invalid engine_type"):
            analyze_engine(engine_type="invalid", source="sample")

    def test_invalid_source(self):
        with pytest.raises(ValueError, match="Invalid source"):
            analyze_engine(engine_type="growth", source="invalid")

    def test_hubspot_without_client(self):
        with pytest.raises(ValueError, match="HubSpot client required"):
            analyze_engine(engine_type="growth", source="hubspot")

    def test_deals_analyzed_count(self):
        result = analyze_engine(engine_type="growth", source="sample")
        assert result["deals_analyzed"] == 8

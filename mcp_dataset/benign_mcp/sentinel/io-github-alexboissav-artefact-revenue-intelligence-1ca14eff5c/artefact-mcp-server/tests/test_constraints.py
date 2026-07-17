"""Tests for constraint identification tool."""

import pytest

from artefact_mcp.tools.constraints import (
    identify_dominant_constraint,
    CONSTRAINTS,
    BENCHMARKS,
)


class TestIdentifyDominantConstraint:
    def test_sample_constraint(self):
        result = identify_dominant_constraint(source="sample")
        assert "dominant_constraint" in result
        assert "constraint_ranking" in result
        assert "revenue_formula" in result
        assert "pipeline_summary" in result
        assert "recommended_focus" in result

    def test_dominant_constraint_structure(self):
        result = identify_dominant_constraint(source="sample")
        dominant = result["dominant_constraint"]
        assert "constraint" in dominant
        assert "label" in dominant
        assert "severity_score" in dominant
        assert "description" in dominant
        assert "symptoms" in dominant
        assert "engine_focus" in dominant
        assert "wbd_levers" in dominant
        assert "hormozi_lever" in dominant
        assert dominant["constraint"] in CONSTRAINTS

    def test_constraint_ranking_complete(self):
        result = identify_dominant_constraint(source="sample")
        ranking = result["constraint_ranking"]
        assert len(ranking) == 4
        constraint_names = {r["constraint"] for r in ranking}
        assert constraint_names == set(CONSTRAINTS.keys())

    def test_ranking_sorted_by_severity(self):
        result = identify_dominant_constraint(source="sample")
        ranking = result["constraint_ranking"]
        for i in range(len(ranking) - 1):
            assert ranking[i]["severity_score"] >= ranking[i + 1]["severity_score"]

    def test_revenue_formula_breakdown(self):
        result = identify_dominant_constraint(source="sample")
        formula = result["revenue_formula"]
        assert "formula" in formula
        assert "components" in formula
        assert "traffic" in formula["components"]
        assert "conversion_rates" in formula["components"]
        assert "acv" in formula["components"]

    def test_pipeline_summary(self):
        result = identify_dominant_constraint(source="sample")
        summary = result["pipeline_summary"]
        assert summary["total_deals"] == 8
        assert summary["total_value"] > 0
        assert 0 <= summary["at_risk_pct"] <= 100

    def test_with_quota(self):
        result = identify_dominant_constraint(source="sample", quota=500000)
        summary = result["pipeline_summary"]
        assert summary["coverage_ratio"] is not None
        assert summary["coverage_ratio"] > 0

    def test_without_quota(self):
        result = identify_dominant_constraint(source="sample")
        summary = result["pipeline_summary"]
        assert summary["coverage_ratio"] is None

    def test_invalid_source(self):
        with pytest.raises(ValueError, match="Invalid source"):
            identify_dominant_constraint(source="invalid")

    def test_hubspot_without_client(self):
        with pytest.raises(ValueError, match="HubSpot client required"):
            identify_dominant_constraint(source="hubspot")

    def test_recommended_focus_not_empty(self):
        result = identify_dominant_constraint(source="sample")
        assert len(result["recommended_focus"]) > 20

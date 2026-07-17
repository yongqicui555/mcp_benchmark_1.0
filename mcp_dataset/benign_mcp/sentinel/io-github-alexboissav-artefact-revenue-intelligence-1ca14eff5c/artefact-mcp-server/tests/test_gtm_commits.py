"""Tests for GTM commit drafting tool."""

import pytest

from artefact_mcp.tools.gtm_commits import (
    propose_gtm_change,
    ENTITY_TYPES,
    SIGNAL_TYPES,
)


class TestProposeGTMChange:
    def test_basic_proposal(self):
        result = propose_gtm_change(
            entity_type="icp",
            change_description="Narrow ICP to SaaS companies with 50-200 employees",
        )
        assert "commit_proposal" in result
        assert "next_steps" in result
        proposal = result["commit_proposal"]
        assert proposal["status"] == "draft"
        assert "intent" in proposal
        assert "diff" in proposal
        assert "impact_surface" in proposal
        assert "risk" in proposal
        assert "evidence" in proposal
        assert "measurement_plan" in proposal

    def test_proposal_with_signal(self):
        result = propose_gtm_change(
            entity_type="scoring_model",
            change_description="Increase industry weight from 2.0 to 2.5 pts for SaaS",
            signal_type="win_loss_pattern",
            signal_data={"win_rate_saas": 0.45, "win_rate_other": 0.22},
        )
        proposal = result["commit_proposal"]
        evidence = proposal["evidence"]
        assert evidence["signal_type"] == "win_loss_pattern"
        assert evidence["evidence_quality"] == "signal-backed"
        assert evidence["signal_data"]["win_rate_saas"] == 0.45

    def test_proposal_without_signal(self):
        result = propose_gtm_change(
            entity_type="playbook",
            change_description="Add discovery call script for manufacturing prospects",
        )
        evidence = result["commit_proposal"]["evidence"]
        assert evidence["signal_type"] is None
        assert evidence["evidence_quality"] == "manual"

    def test_proposal_with_diff(self):
        result = propose_gtm_change(
            entity_type="pipeline_stage",
            change_description="Add Champion Identified as exit criterion for SQL stage",
            current_state="SQL stage has 3 exit criteria: budget, authority, need",
            proposed_state="SQL stage has 4 exit criteria: budget, authority, need, champion identified",
        )
        diff = result["commit_proposal"]["diff"]
        assert diff["has_structured_diff"] is True
        assert "budget" in diff["before"]
        assert "champion" in diff["after"]

    def test_risk_assessment(self):
        # High-risk entity types
        result = propose_gtm_change(
            entity_type="pipeline_stage",
            change_description="Restructure pipeline from 5 to 4 stages",
        )
        risk = result["commit_proposal"]["risk"]
        assert risk["level"] == "high"
        assert risk["requires_approval"] is True

        # Low-risk entity types (no escalation keywords)
        result = propose_gtm_change(
            entity_type="playbook",
            change_description="Document the discovery call flow",
        )
        risk = result["commit_proposal"]["risk"]
        assert risk["level"] == "low"

    def test_measurement_plan(self):
        result = propose_gtm_change(
            entity_type="icp",
            change_description="Test ICP refinement",
        )
        measurement = result["commit_proposal"]["measurement_plan"]
        assert "metrics_to_watch" in measurement
        assert "measurement_window_days" in measurement
        assert "review_date" in measurement
        assert "success_criteria" in measurement
        assert len(measurement["metrics_to_watch"]) > 0

    def test_impact_surface(self):
        result = propose_gtm_change(
            entity_type="positioning",
            change_description="Update value proposition messaging",
        )
        impact = result["commit_proposal"]["impact_surface"]
        assert len(impact["affected_systems"]) > 0

    def test_all_entity_types(self):
        for entity_type in ENTITY_TYPES:
            result = propose_gtm_change(
                entity_type=entity_type,
                change_description=f"Test change for {entity_type}",
            )
            assert result["commit_proposal"]["intent"]["entity_type"] == entity_type

    def test_invalid_entity_type(self):
        with pytest.raises(ValueError, match="Invalid entity_type"):
            propose_gtm_change(
                entity_type="invalid",
                change_description="Test",
            )

    def test_invalid_signal_type(self):
        with pytest.raises(ValueError, match="Invalid signal_type"):
            propose_gtm_change(
                entity_type="icp",
                change_description="Test",
                signal_type="invalid_signal",
            )

    def test_methodology_resource_reference(self):
        result = propose_gtm_change(
            entity_type="icp",
            change_description="Test",
        )
        assert result["methodology_resource"] == "methodology://gtm-commit-anatomy"

    def test_next_steps_include_reviewers(self):
        result = propose_gtm_change(
            entity_type="pipeline_stage",
            change_description="Add new pipeline stage",
        )
        next_steps = result["next_steps"]
        assert any("Reviewers" in step for step in next_steps)

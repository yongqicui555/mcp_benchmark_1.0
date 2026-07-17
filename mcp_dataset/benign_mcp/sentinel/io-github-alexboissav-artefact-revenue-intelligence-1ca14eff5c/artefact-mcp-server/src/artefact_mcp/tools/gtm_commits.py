"""
GTM Commit Drafting

Enables AI agents to propose structured GTM changes following the
GTM OS commit anatomy. Every change is evidence-backed, diffable,
and includes impact analysis and measurement plan.

Commit Anatomy (5 components):
  1. Intent — Why this change
  2. Diff — What changes (structured before/after)
  3. Impact Surface — What downstream systems are affected
  4. Risk Level — Low/medium/high based on blast radius
  5. Evidence — The signal that triggered the change
  6. Measurement Plan — What metric should move, and by when

This tool does NOT write to the CRO app — it outputs a commit proposal
that a human reviews and approves.
"""

from datetime import datetime, timedelta
from typing import Optional

from artefact_mcp.tools.signals import SIGNAL_TYPES


# --- GTM Entity Types ---

ENTITY_TYPES = {
    "icp": {
        "label": "ICP Definition",
        "impact_surfaces": ["Qualification criteria", "Lead scoring", "Marketing targeting", "Sales playbooks"],
    },
    "persona": {
        "label": "Buyer Persona",
        "impact_surfaces": ["Messaging", "Content strategy", "Sales enablement", "Campaign targeting"],
    },
    "positioning": {
        "label": "Positioning & Messaging",
        "impact_surfaces": ["Website copy", "Sales decks", "Ad creative", "Email sequences"],
    },
    "pipeline_stage": {
        "label": "Pipeline Stage Configuration",
        "impact_surfaces": ["CRM automation", "Reporting", "Forecasting", "Sales process"],
    },
    "exit_criteria": {
        "label": "Stage Exit Criteria",
        "impact_surfaces": ["Deal qualification", "Pipeline hygiene", "Forecast accuracy"],
    },
    "gtm_motion": {
        "label": "GTM Motion",
        "impact_surfaces": ["Channel strategy", "Budget allocation", "Team structure", "Campaign cadence"],
    },
    "scoring_model": {
        "label": "Scoring Model",
        "impact_surfaces": ["Lead qualification", "Deal prioritization", "Resource allocation"],
    },
    "playbook": {
        "label": "Sales Playbook",
        "impact_surfaces": ["Sales execution", "Onboarding", "Training materials"],
    },
}

# Risk assessment based on entity type and change magnitude
RISK_FACTORS = {
    "icp": {"base_risk": "medium", "blast_radius": "high"},
    "persona": {"base_risk": "low", "blast_radius": "medium"},
    "positioning": {"base_risk": "medium", "blast_radius": "high"},
    "pipeline_stage": {"base_risk": "high", "blast_radius": "high"},
    "exit_criteria": {"base_risk": "medium", "blast_radius": "medium"},
    "gtm_motion": {"base_risk": "high", "blast_radius": "high"},
    "scoring_model": {"base_risk": "medium", "blast_radius": "medium"},
    "playbook": {"base_risk": "low", "blast_radius": "low"},
}


def _assess_risk(
    entity_type: str,
    change_description: str,
) -> dict:
    """Assess the risk level of a proposed GTM change."""
    risk_info = RISK_FACTORS.get(entity_type, {"base_risk": "medium", "blast_radius": "medium"})
    base_risk = risk_info["base_risk"]
    blast_radius = risk_info["blast_radius"]

    # Escalate risk for certain keywords
    high_risk_keywords = ["remove", "delete", "replace", "restructure", "migrate", "overhaul"]
    medium_risk_keywords = ["add", "modify", "update", "adjust", "refine"]

    desc_lower = change_description.lower()
    for keyword in high_risk_keywords:
        if keyword in desc_lower:
            base_risk = "high"
            break

    if base_risk != "high":
        for keyword in medium_risk_keywords:
            if keyword in desc_lower:
                base_risk = "medium" if base_risk == "low" else base_risk
                break

    return {
        "level": base_risk,
        "blast_radius": blast_radius,
        "requires_approval": base_risk in ("medium", "high"),
        "recommended_reviewers": _get_reviewers(entity_type, base_risk),
    }


def _get_reviewers(entity_type: str, risk_level: str) -> list[str]:
    """Determine who should review this change."""
    reviewers = []

    if entity_type in ("icp", "persona", "positioning"):
        reviewers.append("Marketing Lead")
    if entity_type in ("pipeline_stage", "exit_criteria", "gtm_motion"):
        reviewers.append("RevOps Lead")
    if entity_type in ("scoring_model", "playbook"):
        reviewers.append("Sales Lead")

    if risk_level == "high":
        reviewers.append("CEO / CRO")

    return reviewers if reviewers else ["GTM Lead"]


def _generate_measurement_plan(
    entity_type: str,
    change_description: str,
) -> dict:
    """Generate a measurement plan for the proposed change."""
    now = datetime.now()

    # Default measurement windows
    measurement_window = {
        "icp": 90,
        "persona": 60,
        "positioning": 60,
        "pipeline_stage": 30,
        "exit_criteria": 30,
        "gtm_motion": 90,
        "scoring_model": 60,
        "playbook": 45,
    }

    days = measurement_window.get(entity_type, 60)
    review_date = (now + timedelta(days=days)).strftime("%Y-%m-%d")

    # Metrics to watch based on entity type
    metrics_map = {
        "icp": ["Win rate by ICP tier", "Pipeline quality score", "Qualified lead volume"],
        "persona": ["Content engagement by persona", "Meeting conversion rate", "Persona match accuracy"],
        "positioning": ["Website conversion rate", "Demo request volume", "Win rate vs. competitors"],
        "pipeline_stage": ["Stage conversion rates", "Pipeline velocity", "Forecast accuracy"],
        "exit_criteria": ["Stage pass rate", "Deal progression speed", "False advancement rate"],
        "gtm_motion": ["Pipeline generated by channel", "CAC by motion", "Lead velocity rate"],
        "scoring_model": ["Score-to-outcome correlation", "Tier distribution health", "Score calibration accuracy"],
        "playbook": ["Playbook adoption rate", "Rep performance variance", "Ramp time"],
    }

    return {
        "metrics_to_watch": metrics_map.get(entity_type, ["Overall pipeline health"]),
        "measurement_window_days": days,
        "review_date": review_date,
        "success_criteria": (
            f"Review impact on {', '.join(metrics_map.get(entity_type, ['pipeline health'])[:2])} "
            f"by {review_date}. If metrics improve, commit to production. "
            "If neutral or negative, revert and investigate."
        ),
    }


def propose_gtm_change(
    entity_type: str,
    change_description: str,
    current_state: Optional[str] = None,
    proposed_state: Optional[str] = None,
    signal_type: Optional[str] = None,
    signal_data: Optional[dict] = None,
) -> dict:
    """Draft a structured GTM commit proposal.

    Generates a commit that follows the GTM OS anatomy: Intent, Diff,
    Impact Surface, Risk Level, Evidence, and Measurement Plan.

    Args:
        entity_type: What's being changed — "icp", "persona", "positioning",
            "pipeline_stage", "exit_criteria", "gtm_motion", "scoring_model", "playbook".
        change_description: Human-readable description of the proposed change.
        current_state: Optional description of the current state (before).
        proposed_state: Optional description of the proposed state (after).
        signal_type: Signal type that triggered this change (from the 6-type taxonomy).
        signal_data: Structured evidence data from signal detection.

    Returns:
        Structured commit proposal with all 5 anatomy components.
    """
    if entity_type not in ENTITY_TYPES:
        raise ValueError(
            f"Invalid entity_type: {entity_type}. "
            f"Valid types: {', '.join(ENTITY_TYPES.keys())}"
        )

    if signal_type and signal_type not in SIGNAL_TYPES:
        raise ValueError(
            f"Invalid signal_type: {signal_type}. "
            f"Valid types: {', '.join(SIGNAL_TYPES.keys())}"
        )

    now = datetime.now()
    entity_info = ENTITY_TYPES[entity_type]

    # 1. Intent
    intent = {
        "description": change_description,
        "entity_type": entity_type,
        "entity_label": entity_info["label"],
        "rationale": (
            f"Proposed change to {entity_info['label'].lower()} "
            f"based on {'signal evidence' if signal_type else 'manual analysis'}."
        ),
    }

    # 2. Diff
    diff = {
        "entity_type": entity_type,
        "entity_label": entity_info["label"],
        "before": current_state or "(current state not provided — include for full diff)",
        "after": proposed_state or "(proposed state not provided — include for full diff)",
        "has_structured_diff": bool(current_state and proposed_state),
    }

    # 3. Impact Surface
    impact_surface = {
        "affected_systems": entity_info["impact_surfaces"],
        "downstream_effects": (
            f"Changes to {entity_info['label'].lower()} may affect: "
            f"{', '.join(entity_info['impact_surfaces'])}."
        ),
    }

    # 4. Risk Level
    risk = _assess_risk(entity_type, change_description)

    # 5. Evidence
    evidence = {
        "signal_type": signal_type,
        "signal_label": SIGNAL_TYPES[signal_type]["label"] if signal_type else None,
        "signal_data": signal_data,
        "evidence_quality": "signal-backed" if signal_type else "manual",
        "evidence_note": (
            f"Triggered by {SIGNAL_TYPES[signal_type]['label']} signal"
            if signal_type
            else "No signal evidence attached — this is a manual proposal"
        ),
    }

    # 6. Measurement Plan
    measurement = _generate_measurement_plan(entity_type, change_description)

    return {
        "commit_proposal": {
            "id": f"draft-{now.strftime('%Y%m%d-%H%M%S')}-{entity_type}",
            "status": "draft",
            "created_at": now.isoformat(),
            "intent": intent,
            "diff": diff,
            "impact_surface": impact_surface,
            "risk": risk,
            "evidence": evidence,
            "measurement_plan": measurement,
        },
        "next_steps": [
            "Review the commit proposal with the recommended reviewers",
            f"Reviewers: {', '.join(risk['recommended_reviewers'])}",
            "If approved, apply the change in the CRO app or HubSpot",
            f"Set a calendar reminder for {measurement['review_date']} to measure impact",
            f"Watch metrics: {', '.join(measurement['metrics_to_watch'][:3])}",
        ],
        "methodology_resource": "methodology://gtm-commit-anatomy",
    }

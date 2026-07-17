"""
qualify_prospect tool

Scores a prospect/company against the Artefact 14.5-point ICP model.
Accepts a HubSpot company ID or manual company data dict.
"""

from typing import Optional

from artefact_mcp.core.icp_scorer import ICPScorer
from artefact_mcp.core.hubspot_client import HubSpotClient


def qualify_prospect(
    company_id: Optional[str] = None,
    company_data: Optional[dict] = None,
    hubspot_client: Optional[HubSpotClient] = None,
    scoring_config: Optional[dict] = None,
) -> dict:
    """Score a prospect against the 14.5-point ICP model.

    Args:
        company_id: HubSpot company ID. If provided, fetches data from HubSpot.
        company_data: Manual dict with company attributes. Used if company_id is None.
        hubspot_client: Pre-configured HubSpotClient (required if company_id given).
        scoring_config: Optional overrides for scoring parameters. Keys:
            primary_industries, adjacent_industries, excluded_industries,
            revenue_range ([min, max]), employee_range ([min, max]),
            primary_geography, secondary_geography.

    Returns:
        Full scoring result dict.
    """
    if not company_id and not company_data:
        raise ValueError("Either company_id or company_data must be provided.")

    scorer = ICPScorer(scoring_config=scoring_config)

    hubspot_only = False
    if company_id:
        if not hubspot_client:
            raise ValueError(
                "HubSpot client required when using company_id. "
                "Set HUBSPOT_API_KEY environment variable."
            )
        hs_data = hubspot_client.fetch_company(company_id)

        # Merge: HubSpot firmographic data + any behavioral/strategic overrides from company_data
        overrides = company_data or {}
        company_data = {
            "company_name": hs_data.get("name", "Unknown"),
            "hubspot_id": company_id,
            "industry": hs_data.get("industry", ""),
            "annual_revenue": hs_data.get("annual_revenue"),
            "employee_count": hs_data.get("employee_count"),
            "geography": hs_data.get("geography", ""),
            "tech_stack": overrides.get("tech_stack", []),
            "growth_signals": overrides.get("growth_signals", []),
            "content_engagement": overrides.get("content_engagement", "none"),
            "purchase_history": overrides.get("purchase_history", "never"),
            "decision_maker_access": overrides.get("decision_maker_access", "none"),
            "budget_authority": overrides.get("budget_authority", "none"),
            "strategic_alignment": overrides.get("strategic_alignment", "misaligned"),
        }
        # Track if behavioral/strategic were provided or defaulted
        hubspot_only = not any(
            overrides.get(k)
            for k in ("tech_stack", "growth_signals", "content_engagement",
                      "decision_maker_access", "budget_authority", "strategic_alignment")
        )

    result = scorer.score_company(company_data)

    output = {
        "company": {
            "name": company_data.get("company_name", company_data.get("name", "Unknown")),
            "hubspot_id": company_data.get("hubspot_id"),
            "industry": company_data.get("industry"),
        },
        "total_score": result.total_score,
        "tier": result.tier,
        "breakdown": result.breakdown,
        "exclusion_check": result.exclusion_check,
        "recommended_action": result.recommended_action,
        "engagement_strategy": result.engagement_strategy,
    }

    # Warn when only firmographic data is available
    if hubspot_only:
        output["_incomplete_score"] = {
            "warning": (
                "Score is based on firmographic data only (max ~5/14.5). "
                "Behavioral Fit and Strategic Fit scored 0 because HubSpot doesn't "
                "store these fields natively."
            ),
            "missing_fields": [
                "tech_stack", "growth_signals", "content_engagement",
                "decision_maker_access", "budget_authority", "strategic_alignment",
            ],
            "how_to_fix": (
                "Re-run with company_data containing the missing fields alongside company_id. "
                "Example: qualify(company_id='123', company_data='{\"tech_stack\": [\"HubSpot\"], "
                "\"decision_maker_access\": \"c_suite\", \"budget_authority\": \"dedicated\", "
                "\"strategic_alignment\": \"strong\"}')"
            ),
        }

    # Hint about scoring_config when using defaults
    if not scoring_config:
        output["_scoring_note"] = (
            "Scored using the default B2B model. "
            "Pass scoring_config to customize industries, revenue range, "
            "geography, and exclusions for your business."
        )

    # Constraint context — how this prospect relates to scaling constraints
    output["constraint_context"] = _assess_constraint_relevance(
        company_data, result.total_score, result.tier
    )

    return output


def _assess_constraint_relevance(
    company_data: dict,
    total_score: float,
    tier: dict,
) -> dict:
    """Assess how a prospect relates to the 4 scaling constraints.

    Helps AI agents understand whether qualifying this prospect
    addresses the dominant constraint.
    """
    tier_number = tier.get("number", 4)

    # Infer which constraints this prospect could help with
    relevance = []

    # High-score prospects help conversion (better qualification = better win rate)
    if tier_number <= 2:
        relevance.append({
            "constraint": "conversion",
            "relevance": "high",
            "reason": (
                f"Tier {tier_number} prospect ({total_score}/14.5) — "
                "high-fit prospects convert at 2-3x the rate of low-fit. "
                "Pursuing this prospect directly improves win rate."
            ),
        })

    # Large deal values help profitability
    revenue = company_data.get("annual_revenue")
    if revenue and revenue > 10_000_000:
        relevance.append({
            "constraint": "profitability",
            "relevance": "high",
            "reason": (
                f"Annual revenue ${revenue:,.0f} — larger companies typically "
                "support higher ACVs, improving unit economics."
            ),
        })
    elif revenue and revenue > 5_000_000:
        relevance.append({
            "constraint": "profitability",
            "relevance": "medium",
            "reason": (
                f"Annual revenue ${revenue:,.0f} — mid-market company "
                "with solid ACV potential."
            ),
        })

    # Strategic alignment helps all constraints
    alignment = company_data.get("strategic_alignment", "")
    if alignment == "strong":
        relevance.append({
            "constraint": "delivery",
            "relevance": "medium",
            "reason": (
                "Strong strategic alignment — aligned clients are easier to deliver for "
                "(faster onboarding, less scope creep, higher NRR)."
            ),
        })

    if not relevance:
        relevance.append({
            "constraint": "lead_generation",
            "relevance": "low",
            "reason": (
                f"Tier {tier_number} prospect — pursuing low-fit prospects "
                "doesn't address conversion or profitability constraints. "
                "Focus resources on higher-tier leads."
            ),
        })

    return {
        "prospect_constraint_fit": relevance,
        "recommendation": (
            f"This Tier {tier_number} prospect "
            + (
                "directly addresses conversion constraints — pursue with priority."
                if tier_number <= 2
                else "may not address your dominant constraint. "
                "Consider opportunity cost vs. higher-tier prospects."
            )
        ),
    }

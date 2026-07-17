"""
Dominant Constraint Identification

Analyzes pipeline data to determine which of the 4 scaling constraints
(Lead Generation, Conversion, Delivery, Profitability) is the dominant
bottleneck limiting revenue growth.

Based on:
- Hormozi's 4 Constraints framework
- Winning by Design Revenue Architecture (multiplicative pipeline model)
- Artefact Formula methodology

Revenue Formula: Traffic × CR1 × CR2 × CR3 × ACV × (1/Churn)
"""

from datetime import datetime
from typing import Optional

from artefact_mcp.core.hubspot_client import HubSpotClient
from artefact_mcp.tools.pipeline import (
    _get_sample_deals,
    _calculate_velocity,
    _find_at_risk_deals,
    DEFAULT_STAGE_ORDER,
    STAGE_LABELS,
)


# --- Constraint Definitions ---

CONSTRAINTS = {
    "lead_generation": {
        "label": "Lead Generation",
        "description": "Not enough prospects entering the pipeline",
        "symptoms": [
            "Pipeline below 3x coverage of quota",
            "Sales team has idle capacity",
            "Marketing channels producing fewer leads",
            "No referral or partner engine",
        ],
        "engine_focus": "Growth Engine (early stages)",
        "wbd_levers": ["VM1 (Visitors)", "CR1 (Visit → Lead)"],
        "hormozi_lever": "Traffic",
    },
    "conversion": {
        "label": "Conversion",
        "description": "Prospects enter but don't buy",
        "symptoms": [
            "Win rate below 20%",
            "Deals stall at specific pipeline stages",
            "Long sales cycles vs. industry norms",
            "Frequent 'not now' or 'too expensive' responses",
        ],
        "engine_focus": "Growth Engine (late stages)",
        "wbd_levers": ["CR2-CR5 (Lead → Won)"],
        "hormozi_lever": "Conversion",
    },
    "delivery": {
        "label": "Delivery",
        "description": "Can't fulfill at scale — quality drops with growth",
        "symptoms": [
            "Turning away business due to capacity",
            "Client satisfaction declining with growth",
            "Delivery timelines slipping",
            "Key-person dependency",
        ],
        "engine_focus": "Fulfillment Engine",
        "wbd_levers": ["NRR (Retention Formula)"],
        "hormozi_lever": "Churn (inverse)",
    },
    "profitability": {
        "label": "Profitability",
        "description": "Revenue grows but profit doesn't",
        "symptoms": [
            "Gross margin below 50%",
            "Revenue requires proportional team growth",
            "Discounting to close deals",
            "Overhead growing faster than revenue",
        ],
        "engine_focus": "All engines (efficiency focus)",
        "wbd_levers": ["ACV", "NRR"],
        "hormozi_lever": "Price",
    },
}

# Benchmarks for constraint detection
BENCHMARKS = {
    "pipeline_coverage_ratio": 3.0,  # 3x quota coverage is healthy
    "win_rate": 25.0,  # % - B2B average
    "avg_conversion_rate": 50.0,  # % between stages
    "avg_deal_value": 30000,  # $ - B2B service benchmark
    "cycle_days": 90,  # days - B2B benchmark
    "at_risk_threshold": 30.0,  # % of deals at risk
    "early_stage_concentration": 60.0,  # % of deals in first 2 stages
}


def _calculate_constraint_scores(
    deals: list[dict],
    velocity: dict,
    at_risk: list[dict],
    stage_order: list[str],
    stage_labels: dict[str, str],
) -> dict:
    """Calculate severity scores for each constraint based on pipeline data.

    Returns dict mapping constraint name to severity score (0-100, higher = more severe).
    """
    total = len(deals)
    if total == 0:
        return {c: 50 for c in CONSTRAINTS}  # Neutral when no data

    scores: dict[str, float] = {
        "lead_generation": 0,
        "conversion": 0,
        "delivery": 0,
        "profitability": 0,
    }

    # --- Lead Generation signals ---
    # Low deal count = potential lead gen problem
    if total < 5:
        scores["lead_generation"] += 40
    elif total < 10:
        scores["lead_generation"] += 20
    elif total < 15:
        scores["lead_generation"] += 10

    # Pipeline value concentration in early stages
    early_stages = stage_order[:2] if len(stage_order) >= 2 else stage_order[:1]
    early_count = sum(1 for d in deals if d.get("stage") in early_stages)
    early_pct = early_count / total * 100 if total > 0 else 0

    # Few deals in early stages could mean lead gen issue
    late_stages = stage_order[2:] if len(stage_order) > 2 else []
    late_count = sum(1 for d in deals if d.get("stage") in late_stages)

    if early_count == 0 and late_count > 0:
        # No new deals coming in — lead gen is drying up
        scores["lead_generation"] += 30
    elif total < 8:
        scores["lead_generation"] += 15

    # --- Conversion signals ---
    conversion_rates = velocity.get("conversion_rates", {})
    if conversion_rates:
        rates = list(conversion_rates.values())
        avg_rate = sum(rates) / len(rates) if rates else 0

        # Low average conversion rate
        if avg_rate < 25:
            scores["conversion"] += 40
        elif avg_rate < 40:
            scores["conversion"] += 25
        elif avg_rate < BENCHMARKS["avg_conversion_rate"]:
            scores["conversion"] += 10

        # Any single stage with very low conversion
        min_rate = min(rates) if rates else 0
        if min_rate < 20:
            scores["conversion"] += 20
        elif min_rate < 30:
            scores["conversion"] += 10

    # High at-risk percentage suggests conversion problems
    at_risk_pct = len(at_risk) / total * 100
    if at_risk_pct > BENCHMARKS["at_risk_threshold"]:
        scores["conversion"] += 20
    elif at_risk_pct > 20:
        scores["conversion"] += 10

    # Slow velocity = conversion friction
    cycle_days = velocity.get("overall_cycle_days", 0)
    if cycle_days > BENCHMARKS["cycle_days"] * 2:
        scores["conversion"] += 20
    elif cycle_days > BENCHMARKS["cycle_days"]:
        scores["conversion"] += 10

    # Many deals concentrated early = they enter but don't advance
    if early_pct > BENCHMARKS["early_stage_concentration"]:
        scores["conversion"] += 15

    # --- Delivery signals ---
    # Delivery constraints are harder to detect from pipeline data alone
    # We look for signs of overloaded capacity
    total_value = sum(d.get("amount", 0) for d in deals)
    avg_deal_value = total_value / total if total > 0 else 0

    # Very high pipeline value relative to deal count may suggest capacity strain
    late_value = sum(d.get("amount", 0) for d in deals if d.get("stage") in late_stages)
    if late_stages and late_count > 3 and late_value > total_value * 0.5:
        scores["delivery"] += 15  # Lots of value about to close — can you deliver?

    # --- Profitability signals ---
    # Low deal values relative to benchmark
    if avg_deal_value < BENCHMARKS["avg_deal_value"] * 0.5:
        scores["profitability"] += 25
    elif avg_deal_value < BENCHMARKS["avg_deal_value"]:
        scores["profitability"] += 10

    # Many small deals = potential profitability issue
    small_deals = sum(1 for d in deals if d.get("amount", 0) < BENCHMARKS["avg_deal_value"] * 0.3)
    if small_deals / total > 0.5:
        scores["profitability"] += 15

    # Normalize scores to 0-100 range
    max_score = max(scores.values()) if scores.values() else 1
    if max_score > 0:
        for k in scores:
            scores[k] = round(min(100, scores[k] / max_score * 100), 1)

    return scores


def _build_revenue_formula_breakdown(
    deals: list[dict],
    velocity: dict,
    stage_order: list[str],
    stage_labels: dict[str, str],
) -> dict:
    """Build the Revenue Formula breakdown with gap-to-benchmark analysis."""
    total = len(deals)
    total_value = sum(d.get("amount", 0) for d in deals)
    avg_deal_value = total_value / total if total > 0 else 0

    # Extract conversion rates
    conversion_rates = velocity.get("conversion_rates", {})

    # Map to revenue formula stages
    formula_stages = []
    rate_list = list(conversion_rates.items())

    for i, (transition, rate) in enumerate(rate_list):
        cr_label = f"CR{i + 1}"
        benchmark = BENCHMARKS["avg_conversion_rate"]

        gap = benchmark - rate
        gap_pct = round(gap / benchmark * 100, 1) if benchmark > 0 else 0

        formula_stages.append({
            "label": cr_label,
            "transition": transition,
            "current_rate": rate,
            "benchmark": benchmark,
            "gap": round(gap, 1),
            "gap_pct": gap_pct,
            "status": "above" if rate >= benchmark else "below",
        })

    # Find weakest link
    weakest = None
    if formula_stages:
        below_benchmark = [s for s in formula_stages if s["status"] == "below"]
        if below_benchmark:
            weakest = max(below_benchmark, key=lambda s: s["gap"])

    return {
        "formula": "Revenue = Traffic × CR1 × CR2 × ... × CRn × ACV × (1/Churn)",
        "components": {
            "traffic": {
                "label": "Pipeline Volume (Traffic)",
                "current": total,
                "note": f"{total} active deals in pipeline",
            },
            "conversion_rates": formula_stages,
            "acv": {
                "label": "Average Contract Value",
                "current": round(avg_deal_value, 2),
                "benchmark": BENCHMARKS["avg_deal_value"],
                "gap": round(BENCHMARKS["avg_deal_value"] - avg_deal_value, 2),
            },
        },
        "weakest_link": weakest,
        "compound_improvement_note": (
            "The formula is multiplicative — a 10% improvement at the weakest link "
            "often yields more revenue than doubling traffic. "
            "Focus improvement efforts on the conversion rate with the biggest gap to benchmark."
        ),
    }


def identify_dominant_constraint(
    source: str = "hubspot",
    hubspot_client: Optional[HubSpotClient] = None,
    pipeline_id: Optional[str] = None,
    quota: Optional[float] = None,
) -> dict:
    """Identify the dominant scaling constraint from pipeline data.

    Analyzes pipeline coverage, conversion rates, velocity, and win rates
    to determine which of the 4 constraints is bottlenecking revenue.

    Args:
        source: "hubspot" for live data, "sample" for built-in demo data.
        hubspot_client: Pre-configured HubSpotClient (required for source="hubspot").
        pipeline_id: Optional pipeline ID filter.
        quota: Optional quarterly revenue quota for coverage calculation.

    Returns:
        Dict with dominant constraint, severity scores, revenue formula breakdown,
        and recommended actions.
    """
    now = datetime.now()

    if source == "sample":
        deals = _get_sample_deals()
    elif source == "hubspot":
        if not hubspot_client:
            raise ValueError(
                "HubSpot client required for source='hubspot'. "
                "Set HUBSPOT_API_KEY environment variable."
            )
        deals = hubspot_client.fetch_open_deals(pipeline_id)
    else:
        raise ValueError(f"Invalid source: {source}. Use 'hubspot' or 'sample'.")

    if not deals:
        return {
            "dominant_constraint": None,
            "analysis": "Insufficient data — no deals found in pipeline.",
            "deals_analyzed": 0,
        }

    # Auto-detect pipeline stages
    stage_order = DEFAULT_STAGE_ORDER
    stage_labels = STAGE_LABELS

    if source == "hubspot" and hubspot_client:
        try:
            hs_stages = hubspot_client.fetch_pipeline_stages(pipeline_id or "default")
            if hs_stages:
                stage_order = [s["id"] for s in hs_stages]
                stage_labels = {s["id"]: s["label"] for s in hs_stages}
        except (ValueError, Exception):
            pass

    # Calculate velocity and risk
    velocity = _calculate_velocity(deals, now, stage_order, stage_labels)
    at_risk = _find_at_risk_deals(deals, now, stage_labels)

    # Score each constraint
    constraint_scores = _calculate_constraint_scores(
        deals, velocity, at_risk, stage_order, stage_labels
    )

    # Identify dominant constraint
    dominant_key = max(constraint_scores, key=constraint_scores.get)
    dominant_info = CONSTRAINTS[dominant_key]
    dominant_score = constraint_scores[dominant_key]

    # Build revenue formula breakdown
    revenue_formula = _build_revenue_formula_breakdown(
        deals, velocity, stage_order, stage_labels
    )

    # Pipeline coverage
    total_value = sum(d.get("amount", 0) for d in deals)
    coverage_ratio = None
    if quota and quota > 0:
        coverage_ratio = round(total_value / quota, 2)

    # Build constraint ranking
    ranking = sorted(
        [
            {
                "constraint": key,
                "label": CONSTRAINTS[key]["label"],
                "severity_score": score,
                "description": CONSTRAINTS[key]["description"],
                "engine_focus": CONSTRAINTS[key]["engine_focus"],
                "hormozi_lever": CONSTRAINTS[key]["hormozi_lever"],
            }
            for key, score in constraint_scores.items()
        ],
        key=lambda x: x["severity_score"],
        reverse=True,
    )

    return {
        "dominant_constraint": {
            "constraint": dominant_key,
            "label": dominant_info["label"],
            "severity_score": dominant_score,
            "description": dominant_info["description"],
            "symptoms": dominant_info["symptoms"],
            "engine_focus": dominant_info["engine_focus"],
            "wbd_levers": dominant_info["wbd_levers"],
            "hormozi_lever": dominant_info["hormozi_lever"],
        },
        "constraint_ranking": ranking,
        "revenue_formula": revenue_formula,
        "pipeline_summary": {
            "total_deals": len(deals),
            "total_value": round(total_value, 2),
            "avg_deal_value": round(total_value / len(deals), 2) if deals else 0,
            "at_risk_count": len(at_risk),
            "at_risk_pct": round(len(at_risk) / len(deals) * 100, 1) if deals else 0,
            "cycle_days": velocity.get("overall_cycle_days", 0),
            "bottleneck_stage": velocity.get("bottleneck_stage"),
            "coverage_ratio": coverage_ratio,
        },
        "recommended_focus": (
            f"Your dominant constraint is {dominant_info['label']}. "
            f"Focus on the {dominant_info['engine_focus']} — "
            f"specifically the {dominant_info['hormozi_lever']} lever "
            f"({', '.join(dominant_info['wbd_levers'])} in the Revenue Formula)."
        ),
        "analysis_date": now.strftime("%Y-%m-%d"),
    }

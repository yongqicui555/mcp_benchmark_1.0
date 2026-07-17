"""
Value Engine Analysis

Implements the 3-engine model from the GTM Operating System:
  1. Growth Engine (Customer Acquisition)
  2. Fulfillment Engine (Value Delivery)
  3. Innovation Engine (Product/Service Improvement)

Each engine has its own stages, metrics, and health scoring.
Maps to Artefact Formula pillars.
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
from artefact_mcp.tools.signals import detect_signals


# --- Engine Definitions ---

ENGINE_DEFINITIONS = {
    "growth": {
        "label": "Growth Engine",
        "purpose": "How new customers are acquired — awareness through conversion",
        "artefact_pillars": ["Revenue Intelligence", "Customer Intelligence"],
        "stages": [
            {"name": "Create Demand", "description": "Generate awareness in ungated channels"},
            {"name": "Capture Demand", "description": "Buyer intent becomes visible"},
            {"name": "Convert", "description": "First transaction occurs"},
        ],
        "key_metrics": [
            "CR1 (Visit → Lead)",
            "CR2 (Lead → Qualified)",
            "Win Rate",
            "Cycle Time (days)",
            "Pipeline Coverage Ratio",
        ],
        "health_factors": [
            "pipeline_volume",
            "conversion_rates",
            "velocity",
            "deal_progression",
        ],
    },
    "fulfillment": {
        "label": "Fulfillment Engine",
        "purpose": "How customers receive promised value — onboarding through expansion",
        "artefact_pillars": ["Execution Intelligence", "Customer Intelligence"],
        "stages": [
            {"name": "Onboard", "description": "Client setup, data connections, kickoff"},
            {"name": "Deliver", "description": "Core service execution against SOW"},
            {"name": "Activate", "description": "Client achieves first meaningful outcome"},
            {"name": "Review", "description": "QBR, performance tracking, satisfaction"},
            {"name": "Renew", "description": "Contract renewal conversation"},
            {"name": "Expand", "description": "Upsell, cross-sell, deeper implementation"},
        ],
        "key_metrics": [
            "Net Revenue Retention (NRR)",
            "Gross Retention Rate",
            "Time to First Value",
            "Client Satisfaction Score",
            "Expansion Revenue %",
        ],
        "health_factors": [
            "retention_signals",
            "expansion_potential",
            "delivery_capacity",
        ],
    },
    "innovation": {
        "label": "Innovation Engine",
        "purpose": "How products and services are improved over time",
        "artefact_pillars": ["Performance Intelligence"],
        "stages": [
            {"name": "Gather", "description": "Collect insights from clients, market, team"},
            {"name": "Prioritize", "description": "Evaluate against strategic goals"},
            {"name": "Build/Test", "description": "Develop and validate improvements"},
            {"name": "Launch", "description": "Roll out to clients and market"},
        ],
        "key_metrics": [
            "Feedback Items Collected",
            "Features Shipped per Quarter",
            "Client Adoption Rate",
            "Innovation ROI",
        ],
        "health_factors": [
            "feedback_volume",
            "iteration_speed",
            "adoption_rate",
        ],
    },
}


def _analyze_growth_engine(
    deals: list[dict],
    velocity: dict,
    at_risk: list[dict],
    stage_order: list[str],
    stage_labels: dict[str, str],
    signals: list[dict],
) -> dict:
    """Analyze the Growth Engine from pipeline data."""
    total = len(deals)
    total_value = sum(d.get("amount", 0) for d in deals)

    # Score Growth Engine health (0-100)
    health_score = 100

    # Pipeline volume check
    if total < 5:
        health_score -= 30
        volume_status = "critical"
        volume_note = f"Only {total} active deals — pipeline is dangerously thin"
    elif total < 10:
        health_score -= 15
        volume_status = "warning"
        volume_note = f"{total} active deals — below healthy threshold"
    else:
        volume_status = "healthy"
        volume_note = f"{total} active deals in pipeline"

    # Conversion rate health
    conversion_rates = velocity.get("conversion_rates", {})
    rates = list(conversion_rates.values())
    avg_rate = sum(rates) / len(rates) if rates else 0

    if avg_rate < 25:
        health_score -= 30
        conversion_status = "critical"
    elif avg_rate < 40:
        health_score -= 15
        conversion_status = "warning"
    else:
        conversion_status = "healthy"

    # Velocity health
    cycle_days = velocity.get("overall_cycle_days", 0)
    if cycle_days > 180:
        health_score -= 20
        velocity_status = "critical"
    elif cycle_days > 90:
        health_score -= 10
        velocity_status = "warning"
    else:
        velocity_status = "healthy"

    # Deal progression (are deals moving through stages?)
    early_stages = stage_order[:2] if len(stage_order) >= 2 else stage_order
    early_count = sum(1 for d in deals if d.get("stage") in early_stages)
    early_pct = early_count / total * 100 if total > 0 else 0

    if early_pct > 70:
        health_score -= 15
        progression_status = "warning"
        progression_note = f"{early_pct:.0f}% of deals stuck in early stages"
    else:
        progression_status = "healthy"
        progression_note = "Deals are distributed across stages"

    health_score = max(0, min(100, health_score))

    # Filter growth-relevant signals
    growth_signals = [
        s for s in signals
        if s["signal_type"] in ("conversion_drop_off", "velocity_anomaly", "win_loss_pattern")
    ]

    return {
        "health_score": health_score,
        "health_label": "Healthy" if health_score >= 70 else ("Warning" if health_score >= 40 else "Critical"),
        "metrics": {
            "pipeline_volume": {
                "value": total,
                "status": volume_status,
                "note": volume_note,
            },
            "total_pipeline_value": round(total_value, 2),
            "avg_conversion_rate": round(avg_rate, 1),
            "conversion_status": conversion_status,
            "conversion_rates": conversion_rates,
            "cycle_days": cycle_days,
            "velocity_status": velocity_status,
            "bottleneck_stage": velocity.get("bottleneck_stage"),
            "deal_progression": {
                "early_stage_pct": round(early_pct, 1),
                "status": progression_status,
                "note": progression_note,
            },
            "at_risk_deals": len(at_risk),
        },
        "signals": growth_signals[:5],
    }


def _analyze_fulfillment_engine(deals: list[dict], signals: list[dict]) -> dict:
    """Analyze the Fulfillment Engine.

    Note: Full fulfillment analysis requires post-sale data (NRR, retention, CSAT)
    which isn't available from pipeline data alone. This provides what's inferable
    from pre-sale data and signals.
    """
    total = len(deals)
    total_value = sum(d.get("amount", 0) for d in deals)
    avg_deal_value = total_value / total if total > 0 else 0

    # Infer fulfillment capacity from pipeline pressure
    health_score = 70  # Neutral starting point — limited data

    # High pipeline value about to close = fulfillment pressure
    late_stage_value = 0
    late_deal_count = 0
    if len(DEFAULT_STAGE_ORDER) > 2:
        late_stages = DEFAULT_STAGE_ORDER[-2:]
        for d in deals:
            if d.get("stage") in late_stages:
                late_stage_value += d.get("amount", 0)
                late_deal_count += 1

    capacity_note = "Insufficient pipeline data for full fulfillment analysis"
    if late_deal_count > 3:
        health_score -= 10
        capacity_note = (
            f"{late_deal_count} deals ({late_stage_value:,.0f}) in late stages — "
            "ensure delivery capacity can handle incoming closings"
        )
    elif late_deal_count > 0:
        capacity_note = (
            f"{late_deal_count} deal(s) approaching close — delivery team should be briefed"
        )

    health_score = max(0, min(100, health_score))

    return {
        "health_score": health_score,
        "health_label": "Healthy" if health_score >= 70 else ("Warning" if health_score >= 40 else "Critical"),
        "metrics": {
            "avg_deal_value": round(avg_deal_value, 2),
            "late_stage_deals": late_deal_count,
            "late_stage_value": round(late_stage_value, 2),
            "capacity_pressure": capacity_note,
        },
        "data_gaps": [
            "Net Revenue Retention (NRR) — requires post-sale data",
            "Gross Retention Rate — requires renewal tracking",
            "Time to First Value — requires onboarding data",
            "Client Satisfaction Score — requires CSAT surveys",
            "Expansion Revenue % — requires upsell tracking",
        ],
        "recommendation": (
            "Connect post-sale data (renewals, CSAT, NRR) for full Fulfillment Engine analysis. "
            "Current analysis is limited to pre-sale pipeline indicators."
        ),
        "signals": [],
    }


def _analyze_innovation_engine(signals: list[dict]) -> dict:
    """Analyze the Innovation Engine.

    The Innovation Engine is least observable from pipeline data.
    Returns framework and data gap guidance.
    """
    # Data quality signals can indicate innovation needs
    dq_signals = [s for s in signals if s["signal_type"] == "data_quality"]

    health_score = 60  # Neutral — insufficient data by default

    return {
        "health_score": health_score,
        "health_label": "Insufficient Data",
        "metrics": {
            "data_quality_signals": len(dq_signals),
        },
        "data_gaps": [
            "Feedback Items Collected — requires feedback system integration",
            "Features Shipped per Quarter — requires release tracking",
            "Client Adoption Rate — requires usage analytics",
            "Innovation ROI — requires feature-revenue attribution",
        ],
        "recommendation": (
            "The Innovation Engine requires feedback loop data (client requests, "
            "feature adoption, release velocity) that isn't available from pipeline data alone. "
            "Consider integrating product analytics and feedback tools."
        ),
        "signals": dq_signals[:3],
    }


def analyze_engine(
    engine_type: str,
    source: str = "hubspot",
    hubspot_client: Optional[HubSpotClient] = None,
    pipeline_id: Optional[str] = None,
) -> dict:
    """Analyze a specific Value Engine and return engine-specific health metrics.

    Args:
        engine_type: Which engine to analyze — "growth", "fulfillment", or "innovation".
        source: "hubspot" for live data, "sample" for built-in demo data.
        hubspot_client: Pre-configured HubSpotClient (required for source="hubspot").
        pipeline_id: Optional pipeline ID filter.

    Returns:
        Engine-specific health score, metrics, signals, and recommendations.
    """
    if engine_type not in ENGINE_DEFINITIONS:
        raise ValueError(
            f"Invalid engine_type: {engine_type}. "
            "Use 'growth', 'fulfillment', or 'innovation'."
        )

    now = datetime.now()
    engine_def = ENGINE_DEFINITIONS[engine_type]

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

    # Run signal detection for engine context
    signal_result = detect_signals(source=source, hubspot_client=hubspot_client, pipeline_id=pipeline_id)
    all_signals = signal_result.get("signals", [])

    # Calculate velocity and risk (needed for growth engine)
    velocity = _calculate_velocity(deals, now, stage_order, stage_labels) if deals else {}
    at_risk = _find_at_risk_deals(deals, now, stage_labels) if deals else []

    # Analyze the specific engine
    if engine_type == "growth":
        engine_analysis = _analyze_growth_engine(
            deals, velocity, at_risk, stage_order, stage_labels, all_signals
        )
    elif engine_type == "fulfillment":
        engine_analysis = _analyze_fulfillment_engine(deals, all_signals)
    else:  # innovation
        engine_analysis = _analyze_innovation_engine(all_signals)

    return {
        "engine": {
            "type": engine_type,
            "label": engine_def["label"],
            "purpose": engine_def["purpose"],
            "artefact_pillars": engine_def["artefact_pillars"],
            "stages": engine_def["stages"],
            "key_metrics": engine_def["key_metrics"],
        },
        "analysis": engine_analysis,
        "analysis_date": now.strftime("%Y-%m-%d"),
        "deals_analyzed": len(deals),
        "methodology_resource": "methodology://value-engines",
    }

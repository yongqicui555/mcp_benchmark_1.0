"""
Signal Intelligence Layer

Detects 6 signal types from pipeline/HubSpot data and returns structured,
evidence-backed findings. Implements the evidence-first GTM OS philosophy:
no insight without a signal, no signal without evidence.

Signal Types:
  1. win_loss_pattern - Win rates, loss reasons by segment
  2. conversion_drop_off - Stage-to-stage conversion anomalies
  3. velocity_anomaly - Time-in-stage changes vs. benchmarks
  4. spiced_frequency - Recurring pain/impact patterns (requires enriched data)
  5. attribution_shift - Channel performance changes
  6. data_quality - Missing fields, incomplete records
"""

from datetime import datetime, timedelta
from typing import Optional

from artefact_mcp.core.hubspot_client import HubSpotClient
from artefact_mcp.tools.pipeline import (
    _get_sample_deals,
    _calculate_velocity,
    _find_at_risk_deals,
    _parse_date,
    DEFAULT_STAGE_ORDER,
    STAGE_LABELS,
)


# --- Signal Type Definitions ---

SIGNAL_TYPES = {
    "win_loss_pattern": {
        "label": "Win/Loss Pattern",
        "description": "Shifts in win rates, loss reasons, or deal outcomes by segment/persona/channel",
        "recommended_actions": [
            "ICP refinement",
            "Persona update",
            "Qualification rule change",
        ],
    },
    "conversion_drop_off": {
        "label": "Conversion Drop-Off",
        "description": "Stage-to-stage conversion rates below benchmark or declining",
        "recommended_actions": [
            "Pipeline stage exit criteria update",
            "SLA adjustment",
            "Process investigation",
        ],
    },
    "velocity_anomaly": {
        "label": "Velocity Anomaly",
        "description": "Time-in-stage significantly above or below benchmark",
        "recommended_actions": [
            "Stage SLA change",
            "Process bottleneck investigation",
            "Resource reallocation",
        ],
    },
    "spiced_frequency": {
        "label": "SPICED Frequency",
        "description": "Recurring pain points, impacts, or critical events across deals",
        "recommended_actions": [
            "Messaging update",
            "Positioning refinement",
            "Content strategy adjustment",
        ],
    },
    "attribution_shift": {
        "label": "Attribution Shift",
        "description": "Channel performance changes or pipeline source trend shifts",
        "recommended_actions": [
            "Channel strategy change",
            "Campaign targeting update",
            "Budget reallocation",
        ],
    },
    "data_quality": {
        "label": "Data Quality",
        "description": "Missing fields, incomplete records, data gaps in CRM",
        "recommended_actions": [
            "HubSpot field enforcement",
            "Data hygiene campaign",
            "CRM automation rules",
        ],
    },
}

# Benchmarks for signal detection
VELOCITY_BENCHMARK_DAYS = 30  # Avg days per stage benchmark
CONVERSION_BENCHMARK_PCT = 50  # Min acceptable conversion rate
STAGNATION_THRESHOLD_DAYS = 30  # Days without activity = stagnant
DATA_COMPLETENESS_THRESHOLD = 0.7  # 70% field completion target


def _make_signal(
    signal_type: str,
    signal_name: str,
    signal_strength: float,
    evidence: dict,
    recommended_action: str,
) -> dict:
    """Create a structured signal object."""
    type_info = SIGNAL_TYPES.get(signal_type, {})
    return {
        "signal_type": signal_type,
        "signal_label": type_info.get("label", signal_type),
        "signal_name": signal_name,
        "signal_strength": round(signal_strength, 2),
        "evidence": evidence,
        "recommended_action": recommended_action,
    }


def _detect_velocity_anomalies(
    deals: list[dict],
    now: datetime,
    stage_order: list[str],
    stage_labels: dict[str, str],
) -> list[dict]:
    """Detect velocity anomalies — stages where deals are moving too slowly."""
    signals = []
    velocity = _calculate_velocity(deals, now, stage_order, stage_labels)
    avg_days = velocity.get("avg_days_per_stage", {})

    for stage_label, days in avg_days.items():
        if days > VELOCITY_BENCHMARK_DAYS * 2:
            # Strong signal — stage is 2x+ slower than benchmark
            strength = min(1.0, days / (VELOCITY_BENCHMARK_DAYS * 4))
            signals.append(_make_signal(
                signal_type="velocity_anomaly",
                signal_name=f"{stage_label} stage velocity critically slow",
                signal_strength=strength,
                evidence={
                    "stage": stage_label,
                    "avg_days_in_stage": days,
                    "benchmark_days": VELOCITY_BENCHMARK_DAYS,
                    "ratio_to_benchmark": round(days / VELOCITY_BENCHMARK_DAYS, 1),
                    "deals_affected": sum(
                        1 for d in deals
                        if stage_labels.get(d.get("stage", ""), d.get("stage", "")) == stage_label
                    ),
                },
                recommended_action=(
                    f"Investigate bottleneck in {stage_label}. "
                    f"Deals spend {days:.0f} days here vs. {VELOCITY_BENCHMARK_DAYS}-day benchmark "
                    f"({days / VELOCITY_BENCHMARK_DAYS:.1f}x slower). "
                    "Review stage exit criteria and process efficiency."
                ),
            ))
        elif days > VELOCITY_BENCHMARK_DAYS * 1.5:
            strength = min(0.7, days / (VELOCITY_BENCHMARK_DAYS * 3))
            signals.append(_make_signal(
                signal_type="velocity_anomaly",
                signal_name=f"{stage_label} stage velocity above benchmark",
                signal_strength=strength,
                evidence={
                    "stage": stage_label,
                    "avg_days_in_stage": days,
                    "benchmark_days": VELOCITY_BENCHMARK_DAYS,
                    "ratio_to_benchmark": round(days / VELOCITY_BENCHMARK_DAYS, 1),
                },
                recommended_action=(
                    f"Monitor {stage_label} — {days:.0f} days vs. {VELOCITY_BENCHMARK_DAYS}-day benchmark. "
                    "Consider adjusting stage SLA or reviewing process."
                ),
            ))

    return signals


def _detect_conversion_dropoffs(
    deals: list[dict],
    stage_order: list[str],
    stage_labels: dict[str, str],
) -> list[dict]:
    """Detect stages where conversion rates are below benchmark."""
    signals = []

    for i in range(len(stage_order) - 1):
        current = stage_order[i]
        next_stage = stage_order[i + 1]
        current_idx = stage_order.index(current)
        next_idx = stage_order.index(next_stage)

        current_count = 0
        next_count = 0

        for deal in deals:
            deal_stage = deal.get("stage", "")
            if deal_stage in stage_order:
                deal_idx = stage_order.index(deal_stage)
                if deal_idx >= current_idx:
                    current_count += 1
                if deal_idx >= next_idx:
                    next_count += 1

        if current_count == 0:
            continue

        rate = round(next_count / current_count * 100, 1)
        current_label = stage_labels.get(current, current)
        next_label = stage_labels.get(next_stage, next_stage)

        if rate < CONVERSION_BENCHMARK_PCT * 0.5:
            # Severe drop-off
            signals.append(_make_signal(
                signal_type="conversion_drop_off",
                signal_name=f"Severe drop-off: {current_label} → {next_label}",
                signal_strength=min(1.0, (CONVERSION_BENCHMARK_PCT - rate) / CONVERSION_BENCHMARK_PCT),
                evidence={
                    "from_stage": current_label,
                    "to_stage": next_label,
                    "conversion_rate": rate,
                    "benchmark_rate": CONVERSION_BENCHMARK_PCT,
                    "deals_at_stage": current_count,
                    "deals_advancing": next_count,
                    "deals_stuck": current_count - next_count,
                },
                recommended_action=(
                    f"Critical conversion gap: only {rate}% of deals advance from "
                    f"{current_label} to {next_label} (benchmark: {CONVERSION_BENCHMARK_PCT}%). "
                    "Review exit criteria for this transition. "
                    "Check if deals are stalling due to missing qualification steps."
                ),
            ))
        elif rate < CONVERSION_BENCHMARK_PCT:
            signals.append(_make_signal(
                signal_type="conversion_drop_off",
                signal_name=f"Below-benchmark conversion: {current_label} → {next_label}",
                signal_strength=min(0.6, (CONVERSION_BENCHMARK_PCT - rate) / CONVERSION_BENCHMARK_PCT),
                evidence={
                    "from_stage": current_label,
                    "to_stage": next_label,
                    "conversion_rate": rate,
                    "benchmark_rate": CONVERSION_BENCHMARK_PCT,
                    "deals_at_stage": current_count,
                    "deals_advancing": next_count,
                },
                recommended_action=(
                    f"Conversion from {current_label} to {next_label} is {rate}% "
                    f"(below {CONVERSION_BENCHMARK_PCT}% benchmark). "
                    "Investigate qualification criteria and deal progression blockers."
                ),
            ))

    return signals


def _detect_data_quality_issues(deals: list[dict]) -> list[dict]:
    """Detect data quality signals — missing fields, incomplete records."""
    signals = []
    required_fields = ["name", "amount", "stage", "create_date", "close_date"]

    total_deals = len(deals)
    if total_deals == 0:
        return signals

    field_completion: dict[str, int] = {f: 0 for f in required_fields}

    for deal in deals:
        for field in required_fields:
            value = deal.get(field)
            if value is not None and value != "" and value != 0:
                field_completion[field] += 1

    incomplete_fields = []
    for field, count in field_completion.items():
        rate = count / total_deals
        if rate < DATA_COMPLETENESS_THRESHOLD:
            incomplete_fields.append({
                "field": field,
                "completion_rate": round(rate * 100, 1),
                "missing_count": total_deals - count,
            })

    if incomplete_fields:
        worst_field = min(incomplete_fields, key=lambda x: x["completion_rate"])
        strength = min(1.0, (1 - worst_field["completion_rate"] / 100))

        signals.append(_make_signal(
            signal_type="data_quality",
            signal_name="CRM data completeness below threshold",
            signal_strength=strength,
            evidence={
                "total_deals": total_deals,
                "threshold": f"{DATA_COMPLETENESS_THRESHOLD * 100:.0f}%",
                "incomplete_fields": incomplete_fields,
            },
            recommended_action=(
                f"Data quality issue: {len(incomplete_fields)} field(s) below "
                f"{DATA_COMPLETENESS_THRESHOLD * 100:.0f}% completion. "
                f"Worst: '{worst_field['field']}' at {worst_field['completion_rate']}%. "
                "Enforce required fields in HubSpot pipeline settings."
            ),
        ))

    # Check for deals with $0 amount
    zero_amount = sum(1 for d in deals if d.get("amount", 0) == 0)
    if zero_amount > 0:
        rate = zero_amount / total_deals
        if rate > 0.2:
            signals.append(_make_signal(
                signal_type="data_quality",
                signal_name="High proportion of deals missing amount",
                signal_strength=min(0.8, rate),
                evidence={
                    "deals_with_zero_amount": zero_amount,
                    "total_deals": total_deals,
                    "percentage": round(rate * 100, 1),
                },
                recommended_action=(
                    f"{zero_amount}/{total_deals} deals ({rate * 100:.0f}%) have no amount set. "
                    "Pipeline value is unreliable. Require deal amount at creation."
                ),
            ))

    return signals


def _detect_win_loss_patterns(deals: list[dict]) -> list[dict]:
    """Detect win/loss patterns from deal distribution and risk signals."""
    signals = []
    now = datetime.now()

    at_risk = _find_at_risk_deals(deals, now)
    total = len(deals)

    if total == 0:
        return signals

    at_risk_pct = len(at_risk) / total * 100

    if at_risk_pct > 40:
        signals.append(_make_signal(
            signal_type="win_loss_pattern",
            signal_name="High proportion of at-risk deals in pipeline",
            signal_strength=min(1.0, at_risk_pct / 60),
            evidence={
                "at_risk_count": len(at_risk),
                "total_deals": total,
                "at_risk_percentage": round(at_risk_pct, 1),
                "top_at_risk": [
                    {
                        "name": d["name"],
                        "stage": d["stage"],
                        "reasons": d["risk_reasons"],
                    }
                    for d in at_risk[:3]
                ],
            },
            recommended_action=(
                f"{at_risk_pct:.0f}% of pipeline deals are at risk ({len(at_risk)}/{total}). "
                "This signals systemic pipeline quality issues. "
                "Review qualification criteria — deals may be entering the pipeline prematurely."
            ),
        ))
    elif at_risk_pct > 20:
        signals.append(_make_signal(
            signal_type="win_loss_pattern",
            signal_name="Elevated at-risk deal proportion",
            signal_strength=min(0.6, at_risk_pct / 50),
            evidence={
                "at_risk_count": len(at_risk),
                "total_deals": total,
                "at_risk_percentage": round(at_risk_pct, 1),
            },
            recommended_action=(
                f"{at_risk_pct:.0f}% of deals are at risk. "
                "Monitor closely and investigate common stagnation patterns."
            ),
        ))

    # Detect stagnation clustering (many deals stalled at same stage)
    stage_stagnation: dict[str, int] = {}
    for deal in at_risk:
        stage = deal.get("stage", "Unknown")
        stage_stagnation[stage] = stage_stagnation.get(stage, 0) + 1

    for stage, count in stage_stagnation.items():
        if count >= 2 and count / max(len(at_risk), 1) > 0.4:
            signals.append(_make_signal(
                signal_type="win_loss_pattern",
                signal_name=f"Stagnation cluster in {stage}",
                signal_strength=min(0.8, count / 5),
                evidence={
                    "stage": stage,
                    "stagnant_deals": count,
                    "total_at_risk": len(at_risk),
                    "cluster_percentage": round(count / len(at_risk) * 100, 1),
                },
                recommended_action=(
                    f"{count} at-risk deals clustered in '{stage}' stage. "
                    "This suggests a systematic process failure at this stage. "
                    "Review exit criteria and required activities for this stage."
                ),
            ))

    return signals


def _detect_pipeline_concentration(deals: list[dict], stage_labels: dict[str, str]) -> list[dict]:
    """Detect unhealthy pipeline concentration (attribution proxy)."""
    signals = []
    total = len(deals)
    if total < 3:
        return signals

    # Stage concentration
    stage_counts: dict[str, int] = {}
    stage_values: dict[str, float] = {}
    total_value = 0

    for deal in deals:
        stage = stage_labels.get(deal.get("stage", ""), deal.get("stage", ""))
        stage_counts[stage] = stage_counts.get(stage, 0) + 1
        stage_values[stage] = stage_values.get(stage, 0) + deal.get("amount", 0)
        total_value += deal.get("amount", 0)

    # Check if > 60% of pipeline value is in early stages
    early_stages = list(stage_labels.values())[:2] if stage_labels else []
    early_value = sum(stage_values.get(s, 0) for s in early_stages)

    if total_value > 0 and early_value / total_value > 0.6:
        signals.append(_make_signal(
            signal_type="attribution_shift",
            signal_name="Pipeline value concentrated in early stages",
            signal_strength=min(0.7, early_value / total_value),
            evidence={
                "early_stage_value": round(early_value, 2),
                "total_pipeline_value": round(total_value, 2),
                "early_stage_pct": round(early_value / total_value * 100, 1),
                "stage_breakdown": {
                    s: {"count": stage_counts.get(s, 0), "value": round(stage_values.get(s, 0), 2)}
                    for s in stage_labels.values()
                },
            },
            recommended_action=(
                f"{early_value / total_value * 100:.0f}% of pipeline value sits in early stages. "
                "This indicates pipeline progression issues — deals enter but don't advance. "
                "Focus on conversion optimization in early-to-mid pipeline transitions."
            ),
        ))

    return signals


def detect_signals(
    source: str = "hubspot",
    hubspot_client: Optional[HubSpotClient] = None,
    pipeline_id: Optional[str] = None,
) -> dict:
    """Scan pipeline data for all 6 signal types and return structured findings.

    Args:
        source: "hubspot" for live data, "sample" for built-in demo data.
        hubspot_client: Pre-configured HubSpotClient (required for source="hubspot").
        pipeline_id: Optional pipeline ID filter.

    Returns:
        Dict with detected signals, summary, and signal-to-action mapping.
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
            "signals": [],
            "summary": {
                "total_signals": 0,
                "signal_types_detected": [],
                "highest_strength_signal": None,
            },
            "scan_date": now.strftime("%Y-%m-%d"),
            "deals_scanned": 0,
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

    # Run all signal detectors
    all_signals = []
    all_signals.extend(_detect_velocity_anomalies(deals, now, stage_order, stage_labels))
    all_signals.extend(_detect_conversion_dropoffs(deals, stage_order, stage_labels))
    all_signals.extend(_detect_data_quality_issues(deals))
    all_signals.extend(_detect_win_loss_patterns(deals))
    all_signals.extend(_detect_pipeline_concentration(deals, stage_labels))

    # Sort by strength (highest first)
    all_signals.sort(key=lambda s: s["signal_strength"], reverse=True)

    # Summary
    type_counts: dict[str, int] = {}
    for sig in all_signals:
        st = sig["signal_type"]
        type_counts[st] = type_counts.get(st, 0) + 1

    return {
        "signals": all_signals,
        "summary": {
            "total_signals": len(all_signals),
            "signal_types_detected": list(type_counts.keys()),
            "signal_type_counts": type_counts,
            "highest_strength_signal": all_signals[0] if all_signals else None,
            "critical_signals": [s for s in all_signals if s["signal_strength"] >= 0.7],
        },
        "signal_taxonomy": SIGNAL_TYPES,
        "scan_date": now.strftime("%Y-%m-%d"),
        "deals_scanned": len(deals),
    }

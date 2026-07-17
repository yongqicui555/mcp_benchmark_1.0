"""
score_pipeline tool

Analyzes pipeline health by calculating velocity metrics, conversion rates,
bottleneck identification, and at-risk deal detection.

Ported from useDealVelocity.ts (artefact-grow).
"""

from datetime import datetime
from typing import Optional

from artefact_mcp.core.hubspot_client import HubSpotClient


def _sample_deal_date(days_ago: int) -> str:
    """Generate a date string relative to today."""
    from datetime import timedelta
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def _future_date(days_ahead: int) -> str:
    """Generate a future date string relative to today."""
    from datetime import timedelta
    return (datetime.now() + timedelta(days=days_ahead)).strftime("%Y-%m-%d")


def _get_sample_deals() -> list[dict]:
    """Generate realistic sample deal data with relative dates."""
    return [
        {"id": "D001", "name": "Nextera Systems - Platform Implementation", "amount": 45000, "stage": "qualifiedtobuy", "pipeline": "default", "create_date": _sample_deal_date(100), "close_date": _future_date(35), "last_modified": _sample_deal_date(5)},
        {"id": "D002", "name": "Covalent Labs - Discovery", "amount": 28000, "stage": "appointmentscheduled", "pipeline": "default", "create_date": _sample_deal_date(30), "close_date": _future_date(60), "last_modified": _sample_deal_date(2)},
        {"id": "D003", "name": "Precision Components - Full Engagement", "amount": 92000, "stage": "presentationscheduled", "pipeline": "default", "create_date": _sample_deal_date(145), "close_date": _future_date(18), "last_modified": _sample_deal_date(20)},
        {"id": "D004", "name": "Bridgeport Advisory - Audit", "amount": 15000, "stage": "decisionmakerboughtin", "pipeline": "default", "create_date": _sample_deal_date(70), "close_date": _future_date(20), "last_modified": _sample_deal_date(9)},
        {"id": "D005", "name": "Clearpath Distribution - Pipeline Optimization", "amount": 38000, "stage": "qualifiedtobuy", "pipeline": "default", "create_date": _sample_deal_date(110), "close_date": _future_date(50), "last_modified": _sample_deal_date(26)},
        {"id": "D006", "name": "Harborstone Consulting - Stalled", "amount": 22000, "stage": "appointmentscheduled", "pipeline": "default", "create_date": _sample_deal_date(220), "close_date": _sample_deal_date(25), "last_modified": _sample_deal_date(110)},
        {"id": "D007", "name": "Vaulted Financial - Expansion", "amount": 65000, "stage": "contractsent", "pipeline": "default", "create_date": _sample_deal_date(175), "close_date": _future_date(10), "last_modified": _sample_deal_date(3)},
        {"id": "D008", "name": "Ironworks Building - Intro", "amount": 18000, "stage": "appointmentscheduled", "pipeline": "default", "create_date": _sample_deal_date(15), "close_date": _future_date(80), "last_modified": _sample_deal_date(7)},
    ]

# Default pipeline stage order (HubSpot default pipeline)
DEFAULT_STAGE_ORDER = [
    "appointmentscheduled",
    "qualifiedtobuy",
    "presentationscheduled",
    "decisionmakerboughtin",
    "contractsent",
]

STAGE_LABELS = {
    "appointmentscheduled": "Appointment Scheduled",
    "qualifiedtobuy": "Qualified to Buy",
    "presentationscheduled": "Presentation Scheduled",
    "decisionmakerboughtin": "Decision Maker Bought-In",
    "contractsent": "Contract Sent",
}


def _parse_date(value) -> Optional[datetime]:
    if not value:
        return None
    if isinstance(value, datetime):
        return value
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (ValueError, TypeError):
        try:
            return datetime.strptime(str(value), "%Y-%m-%d")
        except (ValueError, TypeError):
            return None


def _calculate_velocity(
    deals: list[dict],
    now: datetime,
    stage_order: list[str] | None = None,
    stage_labels: dict[str, str] | None = None,
) -> dict:
    """Calculate stage velocity metrics from deal data.

    Estimates time-in-stage based on deal creation date and current stage,
    since HubSpot stage history requires per-deal API calls.

    Args:
        deals: List of deal dicts.
        now: Current datetime.
        stage_order: Ordered list of stage IDs. Falls back to DEFAULT_STAGE_ORDER.
        stage_labels: Map of stage ID to display label. Falls back to STAGE_LABELS.
    """
    _order = stage_order or DEFAULT_STAGE_ORDER
    _labels = stage_labels or STAGE_LABELS

    stage_durations: dict[str, list[int]] = {}
    deal_stages: dict[str, set[str]] = {}

    for deal in deals:
        stage = deal.get("stage", "")
        create_date = _parse_date(deal.get("create_date"))
        last_modified = _parse_date(deal.get("last_modified"))

        if not stage or not create_date:
            continue

        # Track which deals are in which stages
        if stage not in deal_stages:
            deal_stages[stage] = set()
        deal_stages[stage].add(deal.get("id", ""))

        # Calculate days in current stage (from last modified as proxy)
        ref_date = last_modified or now
        if ref_date.tzinfo and not now.tzinfo:
            ref_date = ref_date.replace(tzinfo=None)
        days = max((now - create_date.replace(tzinfo=None)).days, 0)

        if stage not in stage_durations:
            stage_durations[stage] = []
        stage_durations[stage].append(days)

    # Average days per stage
    avg_days: dict[str, float] = {}
    max_avg = 0.0
    bottleneck = None

    for stage in _order:
        if stage in stage_durations:
            durations = stage_durations[stage]
            avg = sum(durations) / len(durations)
            avg_days[_labels.get(stage, stage)] = round(avg, 1)
            if avg > max_avg:
                max_avg = avg
                bottleneck = _labels.get(stage, stage)

    overall = round(sum(avg_days.values()), 0)

    # Conversion rates (deals that moved past each stage)
    conversion_rates: dict[str, float] = {}
    for i in range(len(_order) - 1):
        current = _order[i]
        next_stage = _order[i + 1]

        # Deals at or past current stage
        current_count = 0
        next_count = 0
        current_idx = _order.index(current)
        next_idx = _order.index(next_stage)

        for deal in deals:
            deal_stage = deal.get("stage", "")
            if deal_stage in _order:
                deal_idx = _order.index(deal_stage)
                if deal_idx >= current_idx:
                    current_count += 1
                if deal_idx >= next_idx:
                    next_count += 1

        rate = round(next_count / current_count * 100) if current_count > 0 else 0
        label = f"{_labels.get(current, current)} -> {_labels.get(next_stage, next_stage)}"
        conversion_rates[label] = rate

    return {
        "avg_days_per_stage": avg_days,
        "bottleneck_stage": bottleneck,
        "overall_cycle_days": int(overall),
        "conversion_rates": conversion_rates,
    }


def _find_at_risk_deals(
    deals: list[dict],
    now: datetime,
    stage_labels: dict[str, str] | None = None,
) -> list[dict]:
    """Identify deals that are at risk based on age and stagnation."""
    _labels = stage_labels or STAGE_LABELS
    at_risk = []

    for deal in deals:
        create_date = _parse_date(deal.get("create_date"))
        last_modified = _parse_date(deal.get("last_modified"))
        close_date = _parse_date(deal.get("close_date"))

        if not create_date:
            continue

        # Days since last activity
        ref = last_modified or create_date
        if ref.tzinfo:
            ref = ref.replace(tzinfo=None)
        days_stagnant = (now - ref).days

        # Days since creation
        cd = create_date.replace(tzinfo=None) if create_date.tzinfo else create_date
        days_total = (now - cd).days

        # Past close date?
        past_due = False
        if close_date:
            cld = close_date.replace(tzinfo=None) if close_date.tzinfo else close_date
            past_due = now > cld

        risk_reasons = []
        if days_stagnant > 30:
            risk_reasons.append(f"No activity for {days_stagnant} days")
        if past_due:
            risk_reasons.append("Past expected close date")
        if days_total > 180:
            risk_reasons.append(f"Open for {days_total} days (>6 months)")

        if risk_reasons:
            at_risk.append({
                "id": deal.get("id"),
                "name": deal.get("name"),
                "days_in_pipeline": days_total,
                "stage": _labels.get(deal.get("stage", ""), deal.get("stage", "")),
                "amount": deal.get("amount", 0),
                "risk_reasons": risk_reasons,
            })

    at_risk.sort(key=lambda x: len(x["risk_reasons"]), reverse=True)
    return at_risk


def _calculate_health_score(
    deals: list[dict], velocity: dict, at_risk: list[dict]
) -> tuple[int, str]:
    """Calculate overall pipeline health score (0-100)."""
    if not deals:
        return 0, "Critical"

    score = 100

    # Penalty for at-risk deals
    risk_pct = len(at_risk) / len(deals) * 100
    if risk_pct > 50:
        score -= 40
    elif risk_pct > 30:
        score -= 25
    elif risk_pct > 15:
        score -= 10

    # Penalty for slow velocity
    cycle = velocity.get("overall_cycle_days", 0)
    if cycle > 180:
        score -= 25
    elif cycle > 120:
        score -= 15
    elif cycle > 90:
        score -= 5

    # Penalty for low conversion rates
    rates = velocity.get("conversion_rates", {})
    if rates:
        avg_rate = sum(rates.values()) / len(rates)
        if avg_rate < 30:
            score -= 20
        elif avg_rate < 50:
            score -= 10

    # Bonus for deal count
    if len(deals) < 3:
        score -= 15  # Too few deals
    elif len(deals) >= 10:
        score += 5  # Healthy pipeline volume

    score = max(0, min(100, score))

    if score >= 70:
        label = "Healthy"
    elif score >= 40:
        label = "Warning"
    else:
        label = "Critical"

    return score, label


def _evaluate_exit_criteria(
    deals: list[dict],
    exit_criteria: list[dict],
    stage_labels: dict[str, str],
) -> dict:
    """Evaluate deals against structured exit criteria tests.

    Args:
        deals: List of deal dicts.
        exit_criteria: List of exit criterion dicts, each with:
            stage (stage ID), test_name, required_field, pass_condition.
        stage_labels: Stage ID to label mapping.

    Returns:
        Dict with per-deal test results and aggregate pass rates.
    """
    if not exit_criteria:
        return {}

    deal_results = []
    stage_pass_rates: dict[str, dict] = {}

    for deal in deals:
        deal_stage = deal.get("stage", "")
        stage_label = stage_labels.get(deal_stage, deal_stage)

        # Find criteria for this deal's stage
        stage_criteria = [
            c for c in exit_criteria
            if c.get("stage") == deal_stage or c.get("stage") == stage_label
        ]

        if not stage_criteria:
            continue

        tests = []
        for criterion in stage_criteria:
            field = criterion.get("required_field", "")
            test_name = criterion.get("test_name", "")

            # Evaluate pass/fail based on field presence
            value = deal.get(field)
            passed = value is not None and value != "" and value != 0

            tests.append({
                "test_name": test_name,
                "status": "pass" if passed else "fail",
                "required_field": field,
                "current_value": value,
                "is_blocking": criterion.get("is_blocking", True),
            })

        passing = sum(1 for t in tests if t["status"] == "pass")
        total_tests = len(tests)
        blocking_failures = [t for t in tests if t["status"] == "fail" and t["is_blocking"]]

        deal_results.append({
            "deal_id": deal.get("id"),
            "deal_name": deal.get("name"),
            "stage": stage_label,
            "tests": tests,
            "passing": passing,
            "total": total_tests,
            "pass_rate": round(passing / total_tests * 100, 1) if total_tests > 0 else 0,
            "blocked": len(blocking_failures) > 0,
            "blocking_failures": [t["test_name"] for t in blocking_failures],
        })

        # Aggregate by stage
        if stage_label not in stage_pass_rates:
            stage_pass_rates[stage_label] = {"total_tests": 0, "passed": 0, "deals": 0}
        stage_pass_rates[stage_label]["total_tests"] += total_tests
        stage_pass_rates[stage_label]["passed"] += passing
        stage_pass_rates[stage_label]["deals"] += 1

    # Calculate aggregate pass rates
    for stage in stage_pass_rates:
        total = stage_pass_rates[stage]["total_tests"]
        passed = stage_pass_rates[stage]["passed"]
        stage_pass_rates[stage]["pass_rate"] = round(passed / total * 100, 1) if total > 0 else 0

    return {
        "deal_results": deal_results,
        "stage_pass_rates": stage_pass_rates,
    }


def _detect_pipeline_signals(
    deals: list[dict],
    velocity: dict,
    at_risk: list[dict],
    stage_labels: dict[str, str],
) -> list[dict]:
    """Detect key signals from pipeline data for signal-framed output."""
    signals = []

    # Velocity anomaly signal
    bottleneck = velocity.get("bottleneck_stage")
    avg_days = velocity.get("avg_days_per_stage", {})
    if bottleneck and avg_days.get(bottleneck, 0) > 60:
        signals.append({
            "signal_type": "velocity_anomaly",
            "signal_name": f"Bottleneck detected: {bottleneck}",
            "evidence": f"Average {avg_days[bottleneck]:.0f} days in stage (2x+ benchmark)",
            "recommended_action": f"Review exit criteria and process for {bottleneck}",
        })

    # Conversion drop-off signal
    rates = velocity.get("conversion_rates", {})
    for transition, rate in rates.items():
        if rate < 25:
            signals.append({
                "signal_type": "conversion_drop_off",
                "signal_name": f"Severe drop-off: {transition}",
                "evidence": f"Only {rate}% conversion (benchmark: 50%)",
                "recommended_action": "Investigate qualification criteria at this transition",
            })

    # Win/loss pattern signal
    total = len(deals)
    if total > 0 and len(at_risk) / total > 0.3:
        signals.append({
            "signal_type": "win_loss_pattern",
            "signal_name": "High at-risk deal proportion",
            "evidence": f"{len(at_risk)}/{total} deals ({len(at_risk)/total*100:.0f}%) flagged at-risk",
            "recommended_action": "Review pipeline qualification — deals may be advancing prematurely",
        })

    return signals


def score_pipeline(
    pipeline_id: Optional[str] = None,
    source: str = "hubspot",
    hubspot_client: Optional[HubSpotClient] = None,
    exit_criteria: Optional[list[dict]] = None,
) -> dict:
    """Score pipeline health with velocity metrics, at-risk detection, and signal intelligence.

    Args:
        pipeline_id: Optional pipeline ID filter.
        source: "hubspot" or "sample".
        hubspot_client: Pre-configured HubSpotClient (required for source="hubspot").
        exit_criteria: Optional list of exit criterion dicts for structured testing.
            Each criterion: {stage, test_name, required_field, pass_condition, is_blocking}.

    Returns:
        Pipeline health analysis with signal framing and optional exit criteria results.
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

    # Auto-detect pipeline stages from HubSpot when using live data
    stage_order = None
    stage_labels = None

    if source == "hubspot" and hubspot_client:
        try:
            hs_stages = hubspot_client.fetch_pipeline_stages(pipeline_id or "default")
            if hs_stages:
                stage_order = [s["id"] for s in hs_stages]
                stage_labels = {s["id"]: s["label"] for s in hs_stages}
        except (ValueError, Exception):
            pass  # Fall back to defaults if pipeline fetch fails

    if not deals:
        return {
            "health_score": 0,
            "health_label": "Critical",
            "total_deals": 0,
            "total_value": 0,
            "velocity": {},
            "conversion_rates": {},
            "at_risk_deals": [],
            "stage_distribution": {},
            "signals": [],
        }

    _labels = stage_labels or STAGE_LABELS
    total_value = sum(d.get("amount", 0) for d in deals)

    # Velocity metrics
    velocity = _calculate_velocity(deals, now, stage_order, stage_labels)

    # At-risk deals
    at_risk = _find_at_risk_deals(deals, now, stage_labels)

    # Health score
    health_score, health_label = _calculate_health_score(deals, velocity, at_risk)

    # Stage distribution
    stage_dist: dict = {}
    for deal in deals:
        stage = _labels.get(deal.get("stage", ""), deal.get("stage", ""))
        if stage not in stage_dist:
            stage_dist[stage] = {"count": 0, "value": 0}
        stage_dist[stage]["count"] += 1
        stage_dist[stage]["value"] += deal.get("amount", 0)

    # Signal detection
    pipeline_signals = _detect_pipeline_signals(deals, velocity, at_risk, _labels)

    result = {
        "health_score": health_score,
        "health_label": health_label,
        "total_deals": len(deals),
        "total_value": round(total_value, 2),
        "velocity": {
            "avg_days_per_stage": velocity["avg_days_per_stage"],
            "bottleneck_stage": velocity["bottleneck_stage"],
            "overall_cycle_days": velocity["overall_cycle_days"],
        },
        "conversion_rates": velocity["conversion_rates"],
        "at_risk_deals": at_risk,
        "stage_distribution": stage_dist,
        "signals": pipeline_signals,
    }

    # Exit criteria evaluation (if provided)
    if exit_criteria:
        criteria_results = _evaluate_exit_criteria(deals, exit_criteria, _labels)
        result["exit_criteria_results"] = criteria_results

    return result

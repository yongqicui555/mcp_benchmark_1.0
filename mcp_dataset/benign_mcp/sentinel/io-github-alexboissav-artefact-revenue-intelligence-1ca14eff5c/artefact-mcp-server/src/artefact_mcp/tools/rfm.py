"""
run_rfm_analysis tool

Runs RFM (Recency, Frequency, Monetary) analysis on client data from HubSpot
or sample data. Scores clients, segments them, and extracts ICP patterns.
"""

from datetime import datetime
from typing import Optional

from artefact_mcp.core.rfm_scorer import (
    RFMScorer,
    B2BServiceScorer,
    B2BSaaSScorer,
    B2BManufacturingScorer,
)
from artefact_mcp.core.segmenter import Segmenter, ICPAnalyzer
from artefact_mcp.core.hubspot_client import HubSpotClient


def _sample_date(days_ago: int) -> str:
    """Generate a date string relative to today."""
    from datetime import timedelta
    return (datetime.now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def _get_sample_clients() -> list[dict]:
    """Generate realistic sample client data with relative dates."""
    return [
        {"client_id": "S001", "client_name": "Nextera Systems", "total_revenue": 185000, "transaction_count": 8, "last_purchase_date": _sample_date(25), "industry": "SaaS", "employee_count": "51-200", "company_revenue": "$5M-$20M", "state_region": "Ontario"},
        {"client_id": "S002", "client_name": "Precision Components Group", "total_revenue": 340000, "transaction_count": 12, "last_purchase_date": _sample_date(8), "industry": "Manufacturing", "employee_count": "201-500", "company_revenue": "$20M-$70M", "state_region": "Quebec"},
        {"client_id": "S003", "client_name": "Covalent Labs", "total_revenue": 92000, "transaction_count": 4, "last_purchase_date": _sample_date(80), "industry": "Technology", "employee_count": "11-50", "company_revenue": "$1M-$5M", "state_region": "BC"},
        {"client_id": "S004", "client_name": "Bridgeport Advisory", "total_revenue": 67000, "transaction_count": 3, "last_purchase_date": _sample_date(180), "industry": "Professional Services", "employee_count": "11-50", "company_revenue": "$1M-$5M", "state_region": "Nova Scotia"},
        {"client_id": "S005", "client_name": "Clearpath Distribution", "total_revenue": 210000, "transaction_count": 6, "last_purchase_date": _sample_date(12), "industry": "Logistics", "employee_count": "51-200", "company_revenue": "$5M-$20M", "state_region": "Alberta"},
        {"client_id": "S006", "client_name": "Spark & Co Creative", "total_revenue": 28000, "transaction_count": 1, "last_purchase_date": _sample_date(330), "industry": "Agency", "employee_count": "1-10", "company_revenue": "<$1M", "state_region": "Quebec"},
        {"client_id": "S007", "client_name": "MedBridge Health", "total_revenue": 155000, "transaction_count": 5, "last_purchase_date": _sample_date(70), "industry": "Healthcare", "employee_count": "51-200", "company_revenue": "$5M-$20M", "state_region": "Ontario"},
        {"client_id": "S008", "client_name": "Vaulted Financial Technologies", "total_revenue": 420000, "transaction_count": 15, "last_purchase_date": _sample_date(4), "industry": "FinTech", "employee_count": "51-200", "company_revenue": "$20M-$70M", "state_region": "BC"},
        {"client_id": "S009", "client_name": "Ironworks Building Corp", "total_revenue": 45000, "transaction_count": 2, "last_purchase_date": _sample_date(590), "industry": "Construction", "employee_count": "201-500", "company_revenue": "$20M-$70M", "state_region": "Alberta"},
        {"client_id": "S010", "client_name": "Learnwell Platform", "total_revenue": 73000, "transaction_count": 3, "last_purchase_date": _sample_date(115), "industry": "EdTech", "employee_count": "11-50", "company_revenue": "$1M-$5M", "state_region": "Quebec"},
        {"client_id": "S011", "client_name": "Signal Nine Media", "total_revenue": 18000, "transaction_count": 1, "last_purchase_date": _sample_date(750), "industry": "Media", "employee_count": "1-10", "company_revenue": "<$1M", "state_region": "Ontario"},
        {"client_id": "S012", "client_name": "Harborstone Consulting", "total_revenue": 125000, "transaction_count": 7, "last_purchase_date": _sample_date(150), "industry": "Professional Services", "employee_count": "11-50", "company_revenue": "$1M-$5M", "state_region": "Nova Scotia"},
    ]


def _get_scorer(industry_preset: str) -> RFMScorer:
    scorers = {
        "b2b_service": B2BServiceScorer,
        "saas": B2BSaaSScorer,
        "manufacturing": B2BManufacturingScorer,
    }
    cls = scorers.get(industry_preset)
    if cls:
        return cls()
    return RFMScorer()


def _score_client(
    client: dict,
    scorer: RFMScorer,
    segmenter: Segmenter,
    all_revenues: list[float],
    analysis_date: datetime,
) -> dict:
    last_purchase = client.get("last_purchase_date")
    if isinstance(last_purchase, str):
        try:
            last_purchase = datetime.strptime(last_purchase, "%Y-%m-%d")
        except ValueError:
            last_purchase = None

    # Strip timezone info for safe comparison (HubSpot returns tz-aware dates)
    if last_purchase and hasattr(last_purchase, "tzinfo") and last_purchase.tzinfo is not None:
        last_purchase = last_purchase.replace(tzinfo=None)

    days_since = (analysis_date - last_purchase).days if last_purchase else 999

    r = scorer.score_recency(days_since)
    f = scorer.score_frequency(client.get("transaction_count", 0))
    m = scorer.score_monetary(client.get("total_revenue", 0), all_revenues)

    rfm_total = r + f + m
    segment = segmenter.classify(r, f, m)

    return {
        **client,
        "days_since_last": days_since,
        "r_score": r,
        "f_score": f,
        "m_score": m,
        "rfm_total": rfm_total,
        "rfm_code": f"{r}{f}{m}",
        "segment": segment,
    }


def run_rfm_analysis(
    source: str = "hubspot",
    industry_preset: str = "default",
    hubspot_client: Optional[HubSpotClient] = None,
) -> dict:
    """Run RFM analysis on client data.

    Args:
        source: "hubspot" to pull live data, "sample" for built-in sample data.
        industry_preset: "b2b_service", "saas", "manufacturing", or "default".
        hubspot_client: Pre-configured HubSpotClient (used when source="hubspot").

    Returns:
        Full analysis results dict.
    """
    if source == "sample":
        clients = _get_sample_clients()
    elif source == "hubspot":
        if not hubspot_client:
            raise ValueError(
                "HubSpot client required for source='hubspot'. "
                "Set HUBSPOT_API_KEY environment variable."
            )
        clients = hubspot_client.fetch_client_data()
    else:
        raise ValueError(f"Invalid source: {source}. Use 'hubspot' or 'sample'.")

    if not clients:
        return {
            "error": "No client data found",
            "analysis_date": datetime.now().strftime("%Y-%m-%d"),
            "total_clients": 0,
        }

    scorer = _get_scorer(industry_preset)
    segmenter = Segmenter()
    analyzer = ICPAnalyzer(segmenter)
    analysis_date = datetime.now()

    all_revenues = [c.get("total_revenue", 0) for c in clients]

    scored = [
        _score_client(c, scorer, segmenter, all_revenues, analysis_date)
        for c in clients
    ]
    scored.sort(key=lambda x: x["rfm_total"], reverse=True)

    # Segment distribution
    total_revenue = sum(c.get("total_revenue", 0) for c in scored)
    segment_dist: dict = {}
    for c in scored:
        seg = c["segment"]
        if seg not in segment_dist:
            segment_dist[seg] = {"count": 0, "revenue": 0}
        segment_dist[seg]["count"] += 1
        segment_dist[seg]["revenue"] += c.get("total_revenue", 0)

    for seg in segment_dist:
        segment_dist[seg]["pct"] = round(
            segment_dist[seg]["count"] / len(scored) * 100, 1
        )
        segment_dist[seg]["pct_revenue"] = round(
            segment_dist[seg]["revenue"] / total_revenue * 100, 1
        ) if total_revenue else 0

    # ICP patterns
    top_performers = analyzer.filter_top_performers(scored)
    icp_patterns = analyzer.extract_patterns(top_performers, scored)
    tier_recs = analyzer.generate_tier_recommendations(icp_patterns)

    # Top performers list (limited for output)
    top_list = [
        {
            "name": c["client_name"],
            "rfm_total": c["rfm_total"],
            "rfm_code": c["rfm_code"],
            "segment": c["segment"],
            "revenue": c.get("total_revenue", 0),
        }
        for c in scored[:10]
    ]

    champion_count = sum(1 for c in scored if c["segment"] == "Champions")
    at_risk_count = sum(
        1 for c in scored if c["segment"] in ("At Risk", "Can't Lose Them")
    )

    # Signal intelligence from RFM data
    signals = _extract_rfm_signals(scored, icp_patterns, segment_dist)

    return {
        "analysis_date": analysis_date.strftime("%Y-%m-%d"),
        "total_clients": len(scored),
        "industry_preset": industry_preset,
        "top_performers": top_list,
        "segment_distribution": segment_dist,
        "icp_patterns": icp_patterns,
        "tier_recommendations": tier_recs,
        "summary": {
            "total_revenue": round(total_revenue, 2),
            "avg_rfm_score": round(
                sum(c["rfm_total"] for c in scored) / len(scored), 1
            ),
            "champion_count": champion_count,
            "at_risk_count": at_risk_count,
        },
        "signals": signals,
    }


def _extract_rfm_signals(
    scored: list[dict],
    icp_patterns: dict,
    segment_dist: dict,
) -> list[dict]:
    """Extract signal intelligence from RFM analysis results."""
    signals = []
    total = len(scored)
    if total == 0:
        return signals

    # Win/loss pattern: Champion concentration by industry
    industry_patterns = icp_patterns.get("industry", {})
    primary_industries = industry_patterns.get("primary", [])
    for pattern in primary_industries[:2]:
        signals.append({
            "signal_type": "win_loss_pattern",
            "signal_name": f"Champions concentrated in {pattern['value']}",
            "evidence": (
                f"{pattern['value']} represents {pattern['pct_top']}% of top performers "
                f"vs. {pattern['pct_all']}% of all clients ({pattern['lift']}x lift)"
            ),
            "recommended_action": (
                f"Strong ICP signal — {pattern['value']} clients outperform at "
                f"{pattern['lift']}x. Weight this industry higher in ICP scoring."
            ),
        })

    # Win/loss pattern: At-risk segment concentration
    at_risk_count = sum(
        1 for c in scored if c["segment"] in ("At Risk", "Can't Lose Them")
    )
    at_risk_pct = at_risk_count / total * 100
    if at_risk_pct > 20:
        signals.append({
            "signal_type": "win_loss_pattern",
            "signal_name": "High at-risk client concentration",
            "evidence": (
                f"{at_risk_count}/{total} clients ({at_risk_pct:.0f}%) are At Risk or Can't Lose. "
                "This suggests retention issues."
            ),
            "recommended_action": (
                "Prioritize retention outreach. Investigate common traits of at-risk clients "
                "to build early warning triggers."
            ),
        })

    # Revenue concentration signal
    champion_revenue = segment_dist.get("Champions", {}).get("pct_revenue", 0)
    if champion_revenue > 60:
        signals.append({
            "signal_type": "win_loss_pattern",
            "signal_name": "Revenue over-concentrated in Champions",
            "evidence": (
                f"Champions generate {champion_revenue}% of total revenue. "
                "High dependency on a small segment."
            ),
            "recommended_action": (
                "Revenue concentration risk — diversify by nurturing Potential Loyalists "
                "and Loyal Customers into Champions."
            ),
        })

    return signals

"""
Artefact Revenue Intelligence MCP Server

The AI-native interface to your Revenue Operating System.
Version-controlled GTM intelligence — signals, commits, and closed-loop
measurement — accessible to any AI agent.

Tools:
  - run_rfm: RFM analysis with ICP pattern signals
  - qualify: 14.5-point ICP scoring with constraint context
  - score_pipeline_health: Pipeline health with signal detection and exit criteria
  - detect_signals: Scan for all 6 signal types
  - identify_constraint: Find the dominant scaling constraint
  - analyze_engine: Value Engine health analysis (Growth/Fulfillment/Innovation)
  - propose_gtm_change: Draft structured GTM commits

Resources:
  - methodology://scoring-model, tier-definitions, rfm-segments, spiced-framework
  - methodology://value-engines, exit-criteria, constraints
  - methodology://signal-taxonomy, revenue-formula, gtm-commit-anatomy
"""

import json
import os
import sys
from typing import Optional

from fastmcp import FastMCP

from artefact_mcp import __version__
from artefact_mcp.core.hubspot_client import HubSpotClient
from artefact_mcp.core.license import validate_license, require_license, LicenseInfo
from artefact_mcp.tools.rfm import run_rfm_analysis
from artefact_mcp.tools.icp import qualify_prospect
from artefact_mcp.tools.pipeline import score_pipeline
from artefact_mcp.tools.signals import detect_signals as _detect_signals
from artefact_mcp.tools.constraints import identify_dominant_constraint as _identify_constraint
from artefact_mcp.tools.engines import analyze_engine as _analyze_engine
from artefact_mcp.tools.gtm_commits import propose_gtm_change as _propose_gtm_change
from artefact_mcp.resources.methodology import get_resource, list_resources

# --- License validation at startup ---
_license: LicenseInfo = validate_license()

if not _license.valid:
    print(f"[Artefact MCP] License error: {_license.error}", file=sys.stderr)
    print("[Artefact MCP] Running in free mode (sample data only).", file=sys.stderr)
    _license.tier = "free"
elif _license.tier == "free":
    print("[Artefact MCP] No license key found. Running in free mode (sample data only).", file=sys.stderr)
    print("[Artefact MCP] Purchase a license at https://artefactventures.lemonsqueezy.com", file=sys.stderr)
else:
    print(f"[Artefact MCP] License valid — tier: {_license.tier}", file=sys.stderr)
    if _license.customer_name:
        print(f"[Artefact MCP] Licensed to: {_license.customer_name}", file=sys.stderr)

# --- Server ---

mcp = FastMCP(
    "Artefact Revenue Intelligence",
    instructions=(
        "The AI-native interface to your Revenue Operating System. "
        "Version-controlled GTM intelligence with signal detection, constraint analysis, "
        "value engine health scoring, and structured commit proposals. "
        "Tools: RFM analysis, ICP scoring (14.5-point model), pipeline health, "
        "signal detection (6 types), constraint identification (4 scaling constraints), "
        "value engine analysis (Growth/Fulfillment/Innovation), and GTM commit drafting. "
        + (
            "Connect to HubSpot for live data or use built-in sample data."
            if _license.tier != "free"
            else "Running in free mode — tools auto-detect the best data source. "
            "Purchase a Pro license for live HubSpot integration."
        )
    ),
)


def _get_hubspot_client() -> Optional[HubSpotClient]:
    """Create a HubSpot client if API key is available."""
    api_key = os.getenv("HUBSPOT_API_KEY")
    if api_key:
        return HubSpotClient(api_key)
    return None


# --- Tools ---


@mcp.tool(
    annotations={
        "title": "RFM Analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def run_rfm(
    source: str = "auto",
    industry_preset: str = "default",
) -> str:
    """Run RFM (Recency, Frequency, Monetary) analysis on client data.

    Scores clients based on purchase behavior, segments them into 11 categories,
    extracts ICP patterns from top performers, and detects win/loss pattern signals.

    Args:
        source: Data source — "auto" (uses HubSpot if API key is set, otherwise sample data),
            "hubspot" for live HubSpot data, "sample" for built-in demo data.
        industry_preset: Scoring preset — "b2b_service", "saas", "manufacturing", or "default".

    Returns:
        JSON with scored clients, segment distribution, ICP patterns, signals, and tier recommendations.
    """
    if source == "auto":
        source = "hubspot" if os.getenv("HUBSPOT_API_KEY") else "sample"

    try:
        require_license(source, _license)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    client = _get_hubspot_client() if source == "hubspot" else None
    try:
        result = run_rfm_analysis(
            source=source,
            industry_preset=industry_preset,
            hubspot_client=client,
        )
        if source == "sample":
            result["_note"] = (
                "Results based on built-in sample data. "
                "Connect your HubSpot (set HUBSPOT_API_KEY) for live analysis."
            )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if client:
            client.close()


@mcp.tool(
    annotations={
        "title": "ICP Qualification",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def qualify(
    company_id: Optional[str] = None,
    company_data: Optional[str] = None,
    scoring_config: Optional[str] = None,
) -> str:
    """Score a prospect against the Artefact 14.5-point ICP model with constraint context.

    Evaluates Firmographic Fit (5 pts), Behavioral Fit (5 pts), and Strategic Fit (4.5 pts).
    Returns tier classification, score breakdown, recommended engagement strategy,
    and how this prospect relates to your scaling constraints.

    Provide EITHER company_id (HubSpot ID, requires HUBSPOT_API_KEY) OR company_data (JSON string).

    Args:
        company_id: HubSpot company ID to fetch and score.
        company_data: JSON string with company attributes. Example keys:
            industry, annual_revenue, employee_count, geography, tech_stack (list),
            growth_signals (list), content_engagement ("active"|"occasional"|"none"),
            purchase_history ("regular"|"occasional"|"never"),
            decision_maker_access ("c_suite"|"director"|"manager"|"indirect"|"none"),
            budget_authority ("dedicated"|"shared"|"possible"|"none"),
            strategic_alignment ("strong"|"partial"|"misaligned").
        scoring_config: Optional JSON string to override default scoring parameters.

    Returns:
        JSON with total score, tier, breakdown, constraint context, and recommended action.
    """
    if company_id:
        try:
            require_license("hubspot", _license)
        except ValueError as e:
            return json.dumps({"error": str(e)})

    parsed_data = None
    if company_data:
        try:
            parsed_data = json.loads(company_data) if isinstance(company_data, str) else company_data
        except (json.JSONDecodeError, TypeError) as e:
            return json.dumps({"error": f"Invalid company_data JSON: {e}"})

    parsed_config = None
    if scoring_config:
        try:
            parsed_config = json.loads(scoring_config) if isinstance(scoring_config, str) else scoring_config
        except (json.JSONDecodeError, TypeError) as e:
            return json.dumps({"error": f"Invalid scoring_config JSON: {e}"})

    client = _get_hubspot_client() if company_id else None
    try:
        result = qualify_prospect(
            company_id=company_id,
            company_data=parsed_data,
            hubspot_client=client,
            scoring_config=parsed_config,
        )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if client:
            client.close()


@mcp.tool(
    annotations={
        "title": "Pipeline Health Score",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def score_pipeline_health(
    pipeline_id: Optional[str] = None,
    source: str = "auto",
    exit_criteria: Optional[str] = None,
) -> str:
    """Analyze pipeline health with velocity metrics, signal detection, and exit criteria testing.

    Calculates overall health score (0-100), identifies bottleneck stages,
    measures stage-to-stage conversion rates, flags stalled deals,
    detects pipeline signals, and optionally tests deals against exit criteria.

    Args:
        pipeline_id: Optional HubSpot pipeline ID to filter. Default: all pipelines.
        source: "auto" (uses HubSpot if API key is set, otherwise sample data),
            "hubspot" for live data, "sample" for built-in demo data.
        exit_criteria: Optional JSON string with exit criteria to test against.
            List of objects: [{stage, test_name, required_field, is_blocking}].

    Returns:
        JSON with health score, velocity, conversion rates, at-risk deals, signals,
        and optional exit criteria test results.
    """
    if source == "auto":
        source = "hubspot" if os.getenv("HUBSPOT_API_KEY") else "sample"

    try:
        require_license(source, _license)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    parsed_criteria = None
    if exit_criteria:
        try:
            parsed_criteria = json.loads(exit_criteria) if isinstance(exit_criteria, str) else exit_criteria
        except (json.JSONDecodeError, TypeError) as e:
            return json.dumps({"error": f"Invalid exit_criteria JSON: {e}"})

    client = _get_hubspot_client() if source == "hubspot" else None
    try:
        result = score_pipeline(
            pipeline_id=pipeline_id,
            source=source,
            hubspot_client=client,
            exit_criteria=parsed_criteria,
        )
        if source == "sample":
            result["_note"] = (
                "Results based on built-in sample data. "
                "Connect your HubSpot (set HUBSPOT_API_KEY) for live analysis."
            )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if client:
            client.close()


@mcp.tool(
    annotations={
        "title": "Signal Detection",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def detect_signals(
    source: str = "auto",
    pipeline_id: Optional[str] = None,
) -> str:
    """Scan pipeline data for all 6 signal types and return structured findings.

    Detects: win_loss_pattern, conversion_drop_off, velocity_anomaly,
    attribution_shift, data_quality, and pipeline concentration signals.

    Each signal includes signal_type, signal_strength (0-1), evidence,
    and recommended_action — enabling evidence-backed GTM decisions.

    Args:
        source: "auto" (uses HubSpot if API key is set, otherwise sample data),
            "hubspot" for live data, "sample" for built-in demo data.
        pipeline_id: Optional HubSpot pipeline ID to filter.

    Returns:
        JSON with detected signals, summary, critical signals, and signal taxonomy.
    """
    if source == "auto":
        source = "hubspot" if os.getenv("HUBSPOT_API_KEY") else "sample"

    try:
        require_license(source, _license)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    client = _get_hubspot_client() if source == "hubspot" else None
    try:
        result = _detect_signals(
            source=source,
            hubspot_client=client,
            pipeline_id=pipeline_id,
        )
        if source == "sample":
            result["_note"] = (
                "Signals detected from built-in sample data. "
                "Connect your HubSpot (set HUBSPOT_API_KEY) for live signal detection."
            )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if client:
            client.close()


@mcp.tool(
    annotations={
        "title": "Dominant Constraint Identification",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def identify_constraint(
    source: str = "auto",
    pipeline_id: Optional[str] = None,
    quota: Optional[float] = None,
) -> str:
    """Identify the dominant scaling constraint bottlenecking revenue.

    Analyzes pipeline coverage, conversion rates, velocity, and deal characteristics
    to determine which of 4 constraints is dominant: Lead Generation, Conversion,
    Delivery, or Profitability.

    Returns the Revenue Formula breakdown (Traffic × CR1 × CR2 × ... × ACV × 1/Churn)
    with gap-to-benchmark for each lever and the weakest link.

    Args:
        source: "auto" (uses HubSpot if API key is set, otherwise sample data),
            "hubspot" for live data, "sample" for built-in demo data.
        pipeline_id: Optional HubSpot pipeline ID to filter.
        quota: Optional quarterly revenue quota for pipeline coverage calculation.

    Returns:
        JSON with dominant constraint, severity scores, revenue formula, and recommended focus.
    """
    if source == "auto":
        source = "hubspot" if os.getenv("HUBSPOT_API_KEY") else "sample"

    try:
        require_license(source, _license)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    client = _get_hubspot_client() if source == "hubspot" else None
    try:
        result = _identify_constraint(
            source=source,
            hubspot_client=client,
            pipeline_id=pipeline_id,
            quota=quota,
        )
        if source == "sample":
            result["_note"] = (
                "Constraint analysis based on built-in sample data. "
                "Connect your HubSpot (set HUBSPOT_API_KEY) for live analysis."
            )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if client:
            client.close()


@mcp.tool(
    annotations={
        "title": "Value Engine Analysis",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True,
    }
)
def analyze_engine(
    engine_type: str,
    source: str = "auto",
    pipeline_id: Optional[str] = None,
) -> str:
    """Analyze a Value Engine: Growth, Fulfillment, or Innovation.

    Each engine has its own stages, metrics, and health scoring:
    - **Growth:** Create Demand → Capture Demand → Convert. Pipeline-based metrics.
    - **Fulfillment:** Onboard → Deliver → Activate → Review → Renew → Expand.
    - **Innovation:** Gather → Prioritize → Build/Test → Launch.

    Args:
        engine_type: Which engine — "growth", "fulfillment", or "innovation".
        source: "auto" (uses HubSpot if API key is set, otherwise sample data),
            "hubspot" for live data, "sample" for built-in demo data.
        pipeline_id: Optional HubSpot pipeline ID to filter.

    Returns:
        JSON with engine definition, health score, metrics, signals, and recommendations.
    """
    if source == "auto":
        source = "hubspot" if os.getenv("HUBSPOT_API_KEY") else "sample"

    try:
        require_license(source, _license)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    client = _get_hubspot_client() if source == "hubspot" else None
    try:
        result = _analyze_engine(
            engine_type=engine_type,
            source=source,
            hubspot_client=client,
            pipeline_id=pipeline_id,
        )
        if source == "sample":
            result["_note"] = (
                "Engine analysis based on built-in sample data. "
                "Connect your HubSpot (set HUBSPOT_API_KEY) for live analysis."
            )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if client:
            client.close()


@mcp.tool(
    annotations={
        "title": "GTM Change Proposal",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False,
    }
)
def propose_gtm_change(
    entity_type: str,
    change_description: str,
    current_state: Optional[str] = None,
    proposed_state: Optional[str] = None,
    signal_type: Optional[str] = None,
    signal_data: Optional[str] = None,
) -> str:
    """Draft a structured GTM commit proposal following the GTM OS anatomy.

    Creates a version-controlled change proposal with: Intent, Diff, Impact Surface,
    Risk Level, Evidence, and Measurement Plan. Does NOT apply the change —
    outputs a proposal for human review.

    Args:
        entity_type: What's being changed — "icp", "persona", "positioning",
            "pipeline_stage", "exit_criteria", "gtm_motion", "scoring_model", "playbook".
        change_description: Human-readable description of the proposed change.
        current_state: Optional description of current state (before).
        proposed_state: Optional description of proposed state (after).
        signal_type: Optional signal type that triggered this change
            (win_loss_pattern, conversion_drop_off, velocity_anomaly,
            spiced_frequency, attribution_shift, data_quality).
        signal_data: Optional JSON string with structured evidence from signal detection.

    Returns:
        JSON with structured commit proposal and next steps.
    """
    parsed_signal_data = None
    if signal_data:
        try:
            parsed_signal_data = json.loads(signal_data) if isinstance(signal_data, str) else signal_data
        except (json.JSONDecodeError, TypeError) as e:
            return json.dumps({"error": f"Invalid signal_data JSON: {e}"})

    try:
        result = _propose_gtm_change(
            entity_type=entity_type,
            change_description=change_description,
            current_state=current_state,
            proposed_state=proposed_state,
            signal_type=signal_type,
            signal_data=parsed_signal_data,
        )
        return json.dumps(result, indent=2, default=str)
    except Exception as e:
        return json.dumps({"error": str(e)})


# --- Resources ---


@mcp.resource("methodology://scoring-model")
def scoring_model() -> str:
    """ICP 14.5-point scoring model reference."""
    return get_resource("scoring-model")


@mcp.resource("methodology://tier-definitions")
def tier_definitions() -> str:
    """4-tier classification system (Ideal / Strong / Moderate / Poor)."""
    return get_resource("tier-definitions")


@mcp.resource("methodology://rfm-segments")
def rfm_segments() -> str:
    """11 RFM segment definitions with scoring scales."""
    return get_resource("rfm-segments")


@mcp.resource("methodology://spiced-framework")
def spiced_framework() -> str:
    """SPICED discovery framework reference."""
    return get_resource("spiced-framework")


@mcp.resource("methodology://value-engines")
def value_engines() -> str:
    """3 Value Engines: Growth, Fulfillment, Innovation — stages, metrics, and mapping."""
    return get_resource("value-engines")


@mcp.resource("methodology://exit-criteria")
def exit_criteria() -> str:
    """Pipeline stage exit criteria framework with standard test library."""
    return get_resource("exit-criteria")


@mcp.resource("methodology://constraints")
def constraints() -> str:
    """4 scaling constraints (Lead Gen, Conversion, Delivery, Profitability) with diagnostics."""
    return get_resource("constraints")


@mcp.resource("methodology://signal-taxonomy")
def signal_taxonomy() -> str:
    """6 signal types for evidence-backed GTM intelligence."""
    return get_resource("signal-taxonomy")


@mcp.resource("methodology://revenue-formula")
def revenue_formula() -> str:
    """WbD multiplicative pipeline model + NRR compounding formula."""
    return get_resource("revenue-formula")


@mcp.resource("methodology://gtm-commit-anatomy")
def gtm_commit_anatomy() -> str:
    """5-component structure for version-controlled GTM changes."""
    return get_resource("gtm-commit-anatomy")


@mcp.resource("server://version")
def server_version() -> str:
    """Server version and status information."""
    return json.dumps({
        "name": "Artefact Revenue Intelligence",
        "version": __version__,
        "tier": _license.tier,
        "hubspot_connected": bool(os.getenv("HUBSPOT_API_KEY")),
        "tools": [
            "run_rfm",
            "qualify",
            "score_pipeline_health",
            "detect_signals",
            "identify_constraint",
            "analyze_engine",
            "propose_gtm_change",
        ],
        "resources": [
            "methodology://scoring-model",
            "methodology://tier-definitions",
            "methodology://rfm-segments",
            "methodology://spiced-framework",
            "methodology://value-engines",
            "methodology://exit-criteria",
            "methodology://constraints",
            "methodology://signal-taxonomy",
            "methodology://revenue-formula",
            "methodology://gtm-commit-anatomy",
        ],
    }, indent=2)


def main():
    """Entry point for the MCP server."""
    transport = os.getenv("MCP_TRANSPORT", "stdio")
    if transport == "streamable-http":
        host = os.getenv("MCP_HOST", "0.0.0.0")
        port = int(os.getenv("MCP_PORT", os.getenv("PORT", "8000")))
        mcp.run(transport="streamable-http", host=host, port=port)
    else:
        mcp.run()


if __name__ == "__main__":
    main()

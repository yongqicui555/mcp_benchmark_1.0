"""
QAE Safety Certification MCP Server

This server exposes the QAE safety certification kernel as Claude MCP tools.
It enables Claude to evaluate the safety of autonomous actions before execution.

The server maintains a stateful SafetyCertifier with an AgenticAdapter that
enforces safety budgets and rate limits. All certifications are logged and
retrievable via the certification history tool.

Author: Northbeam Solutions LLC
License: Apache-2.0
"""

import logging
import threading
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from collections import deque

from mcp.server.fastmcp import FastMCP

try:
    from qae_safety import (
        AgenticAdapter,
        SafetyCertifier,
        SimpleAction,
        StateDelta,
        CertifierConfig,
    )
except ImportError as e:
    raise ImportError(
        "qae-safety package not found. Install with: pip install qae-safety"
    ) from e


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# Initialize MCP server
server = FastMCP("qae-safety", "0.1.0")

# Global state: certifier and certification history
_certifier: Optional[SafetyCertifier] = None
_adapter: Optional[AgenticAdapter] = None
_certification_history: deque = deque(maxlen=50)  # Keep last 50 certifications
_initialized = False
_init_lock = threading.Lock()
_BUDGET_LIMIT = 100.0
_RATE_LIMIT = 50.0
_total_certifications = 0  # Unbounded count (not capped by deque maxlen)


def _sanitize_for_log(value: str) -> str:
    """Sanitize a string for safe inclusion in log messages."""
    return value.replace("\n", "\\n").replace("\r", "\\r")


def _initialize_certifier() -> None:
    """Initialize the SafetyCertifier on first use (thread-safe)."""
    global _certifier, _adapter, _initialized

    if _initialized:
        return

    with _init_lock:
        # Double-checked locking: re-check after acquiring lock
        if _initialized:
            return

        try:
            # Create AgenticAdapter with sensible defaults
            adapter = AgenticAdapter(
                budget_limit=_BUDGET_LIMIT,
                rate_limit=_RATE_LIMIT,
            )

            # Create SafetyCertifier with configuration
            config = CertifierConfig(
                safe_threshold=0.6,      # margin > 0.6 => Certified
                caution_threshold=0.3,   # margin in (0.3, 0.6] => CertifiedWithWarning
                block_threshold=0.1,     # margin <= 0.1 => Blocked
            )

            _adapter = adapter  # Keep reference for budget queries
            _certifier = SafetyCertifier(adapter, config=config)
            _initialized = True
            logger.info("SafetyCertifier initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize SafetyCertifier: {e}")
            raise


def _get_certifier() -> SafetyCertifier:
    """Get or initialize the global SafetyCertifier."""
    if not _initialized:
        _initialize_certifier()
    return _certifier


@server.tool()
def certify_action(
    action_id: str,
    agent_id: str,
    scope: float,
    reversibility: float,
    sensitivity: float,
    description: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Evaluate the safety of an action across multiple constraint dimensions.

    This tool uses the QAE safety kernel to assess whether a proposed action
    is safe to execute. It returns a certificate with a decision (Certified,
    CertifiedWithWarning, EscalateToHuman, or Blocked) and detailed margins
    for each constraint dimension.

    Args:
        action_id: Unique identifier for the action (e.g., "act_123")
        agent_id: Identifier of the agent proposing the action (e.g., "claude_v3")
        scope: Scope dimension [0, 1], where 0=narrow, 1=global
        reversibility: Reversibility dimension [0, 1], where 0=permanent, 1=easily reversible
        sensitivity: Sensitivity dimension [0, 1], where 0=low-impact, 1=high-impact
        description: Optional human-readable description of the action

    Returns:
        Dictionary with keys:
        - decision: "Certified", "CertifiedWithWarning", "EscalateToHuman", or "Blocked"
        - zone: "Safe", "Caution", or "Danger"
        - margins: Dict of dimension -> margin value [0, 1]
        - binding_constraint: Name of most restrictive constraint (if any)
        - drift_budget: Remaining budget after this certification
        - certificate_id: Unique certificate identifier
        - deterministic_hash: SHA256 hash of the certificate
        - timestamp: ISO 8601 timestamp
        - description: Echo of input description (if provided)

    Example:
        >>> certify_action(
        ...     action_id="act_deploy_algo",
        ...     agent_id="claude_sales",
        ...     scope=0.7,
        ...     reversibility=0.4,
        ...     sensitivity=0.8,
        ...     description="Deploy new recommendation algorithm to 10% of users"
        ... )
    """
    try:
        certifier = _get_certifier()

        # Validate input ranges
        for dim, val in [("scope", scope), ("reversibility", reversibility), ("sensitivity", sensitivity)]:
            if not (0.0 <= val <= 1.0):
                raise ValueError(f"{dim} must be in [0, 1], got {val}")

        # Create state deltas from dimension scores
        # These represent changes to the agent's state in each dimension
        state_deltas = [
            StateDelta(dimension="scope_score", from_value=0.0, to_value=scope),
            StateDelta(dimension="reversibility_score", from_value=1.0, to_value=reversibility),
            StateDelta(dimension="sensitivity_score", from_value=0.0, to_value=sensitivity),
        ]

        # Create and certify the action
        action = SimpleAction(
            action_id=action_id,
            agent_id=agent_id,
            state_deltas=state_deltas,
        )

        certificate = certifier.certify(action)

        # Build response
        response = {
            "decision": certificate.decision,
            "zone": certificate.zone,
            "margins": certificate.margins,
            "binding_constraint": certificate.binding_constraint,
            "drift_budget": certificate.drift_budget,
            "certificate_id": certificate.certificate_id,
            "deterministic_hash": certificate.deterministic_hash,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        if description:
            response["description"] = description

        # Log to certification history
        history_entry = {
            "certificate_id": certificate.certificate_id,
            "action_id": action_id,
            "agent_id": agent_id,
            "decision": certificate.decision,
            "zone": certificate.zone,
            "timestamp": response["timestamp"],
            "description": description,
        }
        _certification_history.append(history_entry)
        global _total_certifications
        _total_certifications += 1

        logger.info(
            f"Certified action {_sanitize_for_log(action_id)}: {certificate.decision} "
            f"(zone={certificate.zone}, cert_id={certificate.certificate_id})"
        )

        return response

    except ValueError as e:
        logger.error(f"Validation error in certify_action: {e}")
        return {
            "error": str(e),
            "action_id": action_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }
    except Exception as e:
        logger.error(f"Error in certify_action: {e}")
        return {
            "error": f"Certification failed: {str(e)}",
            "action_id": action_id,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }


@server.tool()
def check_budget() -> Dict[str, Any]:
    """
    Check the current safety budget utilization.

    This tool returns the current state of the safety budget, including:
    - Total budget limit (resets on schedule)
    - Amount used in current period
    - Number of certifications performed
    - Rate limit enforcement status

    Returns:
        Dictionary with keys:
        - budget_limit: Total safety budget [tokens/actions]
        - budget_used: Amount consumed in current period
        - budget_remaining: budget_limit - budget_used (clamped to >= 0)
        - rate_limit: Maximum certifications per period
        - total_certifications: Total number of certifications performed
        - utilization_percent: (budget_used / budget_limit) * 100
        - timestamp: Current time (ISO 8601)
    """
    try:
        _get_certifier()  # Ensure initialized

        utilization = _adapter.budget_utilization()
        budget_used = utilization * _BUDGET_LIMIT
        budget_remaining = max(0.0, _BUDGET_LIMIT - budget_used)

        response = {
            "budget_limit": _BUDGET_LIMIT,
            "budget_used": round(budget_used, 2),
            "budget_remaining": round(budget_remaining, 2),
            "budget_utilization": round(utilization, 4),
            "rate_limit": _RATE_LIMIT,
            "total_certifications": _total_certifications,
            "utilization_percent": round(utilization * 100, 2),
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        logger.info(
            f"Budget check: {response['budget_remaining']:.1f}/"
            f"{response['budget_limit']:.1f} remaining"
        )

        return response

    except Exception as e:
        logger.error(f"Error in check_budget: {e}")
        return {
            "error": f"Failed to check budget: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }


@server.tool()
def get_certification_history(limit: int = 10) -> Dict[str, Any]:
    """
    Retrieve the recent certification history.

    This tool returns a list of recent certifications, most recent first.
    The history includes decision, zone, timestamp, and other metadata.
    Up to 50 certifications are stored; older ones are discarded.

    Args:
        limit: Maximum number of certifications to return (default 10, max 50)

    Returns:
        Dictionary with keys:
        - certifications: List of recent certification summaries
        - total_count: Total certifications in history
        - timestamp: Current time (ISO 8601)

    Each certification entry contains:
        - certificate_id: Unique certificate identifier
        - action_id: Action that was certified
        - agent_id: Agent that proposed the action
        - decision: Final decision ("Certified", "CertifiedWithWarning", etc.)
        - zone: Risk zone ("Safe", "Caution", "Danger")
        - timestamp: When the certification occurred
        - description: Optional action description
    """
    try:
        limit = min(max(limit, 1), 50)  # Clamp to [1, 50]

        # Reverse to get most recent first
        recent = list(reversed(list(_certification_history)))[:limit]

        response = {
            "certifications": recent,
            "total_count": len(_certification_history),
            "limit": limit,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }

        logger.info(f"Retrieved {len(recent)} certifications from history")

        return response

    except Exception as e:
        logger.error(f"Error in get_certification_history: {e}")
        return {
            "error": f"Failed to retrieve history: {str(e)}",
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        }


def main() -> None:
    """
    Entry point for the MCP server.

    This function starts the FastMCP server and handles incoming tool calls
    from Claude.
    """
    logger.info("Starting QAE Safety Certification MCP Server")
    logger.info("Available tools: certify_action, check_budget, get_certification_history")

    try:
        _initialize_certifier()
        server.run()
    except KeyboardInterrupt:
        logger.info("Server shutdown requested")
    except Exception as e:
        logger.error(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()

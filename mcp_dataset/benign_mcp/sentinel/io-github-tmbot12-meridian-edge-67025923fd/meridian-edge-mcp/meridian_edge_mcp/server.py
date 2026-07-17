#!/usr/bin/env python3
"""
Meridian Edge MCP Server

Exposes prediction market consensus data as Claude tools via the
Model Context Protocol. AI assistants can query real-time consensus
probabilities, divergence opportunities, and market signals.

For informational purposes only. Not investment advice.
"""
import os
import httpx
from typing import Optional
from mcp.server.fastmcp import FastMCP

# ─── Config ──────────────────────────────────────────────────────────────────

BASE_URL = "https://meridianedge.io/api/v1"
DISCLAIMER = "For informational purposes only. Not investment advice."

# API key: set MERIDIAN_EDGE_API_KEY env var, or use the free demo key.
# Free key (100 calls/day): sign up at meridianedge.io
# Demo key works for testing but has limited data.
_ENV_KEY = os.environ.get("MERIDIAN_EDGE_API_KEY", "me_free_demo000000000000")


# ─── MCP server ──────────────────────────────────────────────────────────────

mcp = FastMCP(
    name="meridian-edge",
    instructions=(
        "You have access to real-time prediction market data from Meridian Edge. "
        "Use get_consensus to check what prediction markets collectively say about "
        "sports events and other outcomes. Use get_opportunities when asked about "
        "markets where predictions diverge. Use get_signals for recent market moves. "
        "Always note that data is for informational purposes only, not investment advice."
    ),
)


# ─── HTTP helper ─────────────────────────────────────────────────────────────

def _get(endpoint: str, params: dict | None = None) -> dict:
    """Make authenticated GET request to Meridian Edge API."""
    headers = {"X-API-Key": _ENV_KEY}
    url = f"{BASE_URL}/{endpoint.lstrip('/')}"
    with httpx.Client(timeout=10.0) as client:
        r = client.get(url, params=params, headers=headers)
        r.raise_for_status()
        return r.json()


def _movement_arrow(movement: str, pct: float) -> str:
    """Format movement as arrow + pct."""
    if movement == "up":
        return f"↑ +{abs(pct):.1f}%"
    elif movement == "down":
        return f"↓ -{abs(pct):.1f}%"
    return "→ stable"


def _sparkline(values: list) -> str:
    """Convert 6-point sparkline to Unicode bar chart."""
    if not values or len(values) < 2:
        return ""
    bars = "▁▂▃▄▅▆▇█"
    lo, hi = min(values), max(values)
    rng = hi - lo or 0.001
    chars = [bars[min(7, int((v - lo) / rng * 7))] for v in values]
    return "".join(chars)


# ─── Tools ───────────────────────────────────────────────────────────────────

@mcp.tool()
def get_consensus(
    sport: Optional[str] = None,
    limit: int = 10,
) -> str:
    """Get real-time prediction market consensus probabilities.

    Returns aggregated consensus from multiple regulated prediction markets.
    Each event shows the collective probability, trend direction, and how
    much markets agree (spread).

    Args:
        sport: Filter by sport — NBA, NFL, MLB, NHL, MLS, POLITICS, or omit
               for all active events.
        limit: Number of events to return (1–20, default 10).

    Returns:
        Formatted consensus data with probabilities, trends, and confidence.
    """
    try:
        params: dict = {"limit": min(max(1, limit), 20)}
        if sport:
            params["sport"] = sport.upper()

        data = _get("consensus", params)
        events = data.get("data", [])

        if not events:
            label = f" for {sport.upper()}" if sport else ""
            return f"No active prediction market events{label} right now.\n\n{DISCLAIMER}"

        label = f" — {sport.upper()}" if sport else ""
        lines = [f"PREDICTION MARKET CONSENSUS{label} ({len(events)} events)\n"]

        for i, e in enumerate(events, 1):
            name      = e.get("event_name") or e.get("event_key", "Unknown")
            prob      = e.get("consensus_prob", 0)
            conf      = e.get("confidence", "—")
            spread    = e.get("spread", 0)
            movement  = e.get("movement", "stable")
            mvt_pct   = e.get("movement_pct", 0)
            n_plat    = e.get("n_platforms", 1)
            sparkline = e.get("sparkline", [])
            ts        = (e.get("ts") or "")[:16].replace("T", " ")

            trend_str = _movement_arrow(movement, abs(mvt_pct))
            spark_str = _sparkline(sparkline)

            lines.append(
                f"{i}. {name}\n"
                f"   Consensus: {prob:.1%} YES  |  Spread: {spread:.1%}  |  Confidence: {conf}\n"
                f"   Trend (30min): {trend_str}  |  Platforms: {n_plat}"
                + (f"  |  {spark_str}" if spark_str else "")
                + (f"\n   Updated: {ts} UTC" if ts else "")
                + "\n"
            )

        lines.append(f"\n{DISCLAIMER}")
        lines.append("Source: Meridian Edge — meridianedge.io")
        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return "Rate limit reached. Free tier: 100 calls/day. Upgrade at meridianedge.io/#pricing"
        if e.response.status_code == 401:
            return "Invalid API key. Set MERIDIAN_EDGE_API_KEY or get a free key at meridianedge.io"
        return f"API error {e.response.status_code}. Check meridianedge.io/api/v1/status"
    except Exception as e:
        return f"Could not fetch consensus data: {e}\nCheck status: meridianedge.io/api/v1/status"


@mcp.tool()
def get_opportunities(
    min_score: float = 5.0,
    sport: Optional[str] = None,
    limit: int = 10,
) -> str:
    """Get events where prediction markets show notable divergence.

    Divergence opportunities are events where regulated prediction markets
    disagree significantly. Higher scores indicate greater disagreement.
    This may surface events where information is still being incorporated.

    Args:
        min_score: Minimum opportunity score to include (default 5.0).
        sport: Filter by sport — NBA, NFL, MLB, NHL, MLS, POLITICS, or omit.
        limit: Number of opportunities to return (1–20, default 10).

    Returns:
        Formatted list of divergence opportunities ranked by score.
    """
    try:
        params: dict = {"limit": min(max(1, limit), 20), "min_score": min_score}
        if sport:
            params["sport"] = sport.upper()

        data = _get("opportunities", params)
        events = data.get("data", [])
        total  = data.get("total_available", len(events))
        teaser = data.get("teaser", False)

        if not events:
            return (
                f"No divergence opportunities found (min_score={min_score}).\n"
                "Try a lower min_score or check back when markets are active.\n\n"
                f"{DISCLAIMER}"
            )

        label = f" — {sport.upper()}" if sport else ""
        shown = len(events)
        lines = [f"DIVERGENCE OPPORTUNITIES{label} (showing {shown} of {total})\n"]

        for i, e in enumerate(events, 1):
            name      = e.get("event_name") or e.get("event_key", "Unknown")
            score     = e.get("opportunity_score", 0)
            conf      = e.get("confidence", "—")
            sp_sport  = e.get("sport", "").upper()
            detected  = (e.get("detected_at") or "")[:16].replace("T", " ")

            lines.append(
                f"{i}. {name}"
                + (f" ({sp_sport})" if sp_sport and not sport else "")
                + f"\n   Score: {score:.1f}  |  Confidence: {conf}"
                + (f"\n   Detected: {detected} UTC" if detected else "")
                + "\n"
            )

        if teaser and total > shown:
            lines.append(
                f"\n{total - shown} more opportunities available on Starter+ tier.\n"
                "Upgrade: meridianedge.io/#pricing"
            )

        lines.append(f"\n{DISCLAIMER}")
        lines.append("Source: Meridian Edge — meridianedge.io")
        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            return (
                "Opportunities endpoint requires Starter tier or above.\n"
                "Upgrade at meridianedge.io/#pricing"
            )
        if e.response.status_code == 429:
            return "Rate limit reached. Free tier: 100 calls/day."
        return f"API error {e.response.status_code}."
    except Exception as e:
        return f"Could not fetch opportunities: {e}"


@mcp.tool()
def get_signals(
    limit: int = 5,
) -> str:
    """Get recent market signals showing direction of price moves.

    Signals indicate notable directional moves in prediction market consensus.
    Each signal shows whether the market shifted toward YES or NO, and the
    current status of the market.

    Args:
        limit: Number of signals to return (1–10, default 5).

    Returns:
        Formatted recent signals with direction and event details.
    """
    try:
        params = {"limit": min(max(1, limit), 10)}
        data   = _get("signals/recent", params)
        signals = data.get("data", [])
        meta    = data.get("meta", {})

        if not signals:
            return f"No recent market signals available.\n\n{DISCLAIMER}"

        delay = meta.get("delay_seconds", 0)
        lines = ["RECENT MARKET SIGNALS\n"]
        if delay:
            lines.append(f"(Signals delayed {delay // 60} minutes on free tier)\n")

        for i, s in enumerate(signals, 1):
            event     = s.get("event") or s.get("event_key", "Unknown")
            direction = s.get("direction", "—").upper()
            sp_sport  = s.get("sport", "").upper()
            status    = s.get("status", "—")
            ts        = (s.get("timestamp") or "")[:16].replace("T", " ")

            dir_arrow = "↑ YES" if direction == "YES" else "↓ NO" if direction == "NO" else direction
            lines.append(
                f"{i}. {event}\n"
                f"   Direction: {dir_arrow}  |  Status: {status}"
                + (f"  |  Sport: {sp_sport}" if sp_sport else "")
                + (f"\n   Time: {ts} UTC" if ts else "")
                + "\n"
            )

        lines.append(f"\n{DISCLAIMER}")
        lines.append("Source: Meridian Edge — meridianedge.io")
        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 403:
            return "Signals endpoint requires a free API key. Get one at meridianedge.io"
        if e.response.status_code == 429:
            return "Rate limit reached. Free tier: 100 calls/day."
        return f"API error {e.response.status_code}."
    except Exception as e:
        return f"Could not fetch signals: {e}"


@mcp.tool()
def get_markets(
    sport: Optional[str] = None,
    limit: int = 10,
) -> str:
    """Get active prediction markets currently being tracked.

    Shows markets that are open and being monitored for consensus. Use this
    to see what events are currently available before querying consensus.

    Args:
        sport: Filter by sport — NBA, NFL, MLB, NHL, MLS, POLITICS, or omit.
        limit: Number of markets to return (1–20, default 10).

    Returns:
        Formatted list of active markets with status and sport.
    """
    try:
        params: dict = {"limit": min(max(1, limit), 20)}
        if sport:
            params["sport"] = sport.upper()

        data    = _get("markets", params)
        markets = data.get("data", [])

        if not markets:
            label = f" for {sport.upper()}" if sport else ""
            return f"No active markets{label} right now.\n\n{DISCLAIMER}"

        label = f" — {sport.upper()}" if sport else ""
        lines = [f"ACTIVE MARKETS{label} ({len(markets)} markets)\n"]

        for i, m in enumerate(markets, 1):
            key       = m.get("event_key") or m.get("event_id", "Unknown")
            league    = (m.get("league") or m.get("sport") or "").upper()
            status    = m.get("status", "open")
            prob      = m.get("consensus_probability")
            score     = m.get("opportunity_score")
            ttl       = m.get("time_to_event_hours")

            line = f"{i}. {key}"
            if league:
                line += f"  [{league}]"
            details = [f"Status: {status}"]
            if prob is not None:
                details.append(f"Consensus: {prob:.1%}")
            if score is not None:
                details.append(f"Opp. score: {score:.1f}")
            if ttl is not None:
                details.append(f"Starts in: {ttl:.1f}h")
            lines.append(line + "\n   " + "  |  ".join(details) + "\n")

        lines.append(f"\n{DISCLAIMER}")
        lines.append("Source: Meridian Edge — meridianedge.io")
        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return "Rate limit reached. Free tier: 100 calls/day."
        return f"API error {e.response.status_code}."
    except Exception as e:
        return f"Could not fetch markets: {e}"


@mcp.tool()
def get_settlements(
    limit: int = 5,
) -> str:
    """Get recently settled prediction market events with verified outcomes.

    Shows events that have concluded, with verified outcome data. Useful for
    checking how recent consensus predictions compared to actual results.

    Args:
        limit: Number of settled events to return (1–10, default 5).

    Returns:
        Formatted settlement history with outcomes and verification status.
    """
    try:
        params  = {"limit": min(max(1, limit), 10)}
        data    = _get("settlements/recent", params)
        settled = data.get("data", [])

        if not settled:
            return f"No recent settled events available.\n\n{DISCLAIMER}"

        lines = [f"RECENTLY SETTLED MARKETS ({len(settled)} events)\n"]

        for i, s in enumerate(settled, 1):
            key      = s.get("event_key") or s.get("event_id", "Unknown")
            outcome  = s.get("outcome", "—").upper()
            verify   = s.get("verification", "—")
            sport    = s.get("sport", "").upper()
            settled_at = (s.get("settled_at") or "")[:16].replace("T", " ")

            outcome_icon = "✓" if outcome == "CORRECT" else "✗" if outcome == "INCORRECT" else "?"
            lines.append(
                f"{i}. {key}"
                + (f"  [{sport}]" if sport else "")
                + f"\n   Outcome: {outcome_icon} {outcome}  |  Verified: {verify}"
                + (f"\n   Settled: {settled_at} UTC" if settled_at else "")
                + "\n"
            )

        lines.append(f"\n{DISCLAIMER}")
        lines.append("Source: Meridian Edge — meridianedge.io")
        return "\n".join(lines)

    except httpx.HTTPStatusError as e:
        if e.response.status_code == 429:
            return "Rate limit reached. Free tier: 100 calls/day."
        return f"API error {e.response.status_code}."
    except Exception as e:
        return f"Could not fetch settlements: {e}"


# ─── Entry point ─────────────────────────────────────────────────────────────

def main():
    mcp.run()


if __name__ == "__main__":
    main()

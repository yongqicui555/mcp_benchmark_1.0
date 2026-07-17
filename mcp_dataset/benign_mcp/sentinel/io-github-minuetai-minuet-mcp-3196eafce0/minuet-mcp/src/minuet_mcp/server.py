"""MCP server exposing Minuet's relationship data as read-only tools.

Backing API: the Flask app at https://minuet.ai. All tools are read-only
wrappers; write routes (claim/propose/confirm) are wallet-gated and
intentionally excluded.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .client import MinuetClient

mcp = FastMCP("minuet-mcp")


def _agent_id(item: dict[str, Any]) -> str:
    """Derive the canonical `chainId:agentId` string the API expects."""
    if item.get("id"):
        return str(item["id"])
    chain = item.get("chainId", "")
    agent = item.get("agentId", "")
    return f"{chain}:{agent}"


# ----- Tools -----


@mcp.tool()
async def search_agents(query: str | None = None, limit: int = 25) -> dict[str, Any]:
    """Search indexed ERC-8004 agents.

    Args:
        query: Optional substring to match against agent name.
        limit: Maximum number of agents to return (default 25).
    """
    async with MinuetClient() as client:
        data = await client.list_agents(name=query, limit=limit)
    agents = data.get("agents", [])[:limit]
    return {"count": len(agents), "agents": agents}


@mcp.tool()
async def get_agent(agent_id: str) -> dict[str, Any]:
    """Fetch full details for a specific agent, including its Minuet relationships.

    Args:
        agent_id: Canonical identifier in the form `chainId:agentId`
            (e.g. `1:6817` for Ethereum mainnet agent 6817).
    """
    async with MinuetClient() as client:
        return await client.get_agent(agent_id)


@mcp.tool()
async def get_agent_relationships(
    agent_id: str, direction: str = "both"
) -> dict[str, Any]:
    """List relationships for a specific agent.

    Args:
        agent_id: Canonical `chainId:agentId` identifier.
        direction: One of `incoming`, `outgoing`, or `both` (default).
    """
    async with MinuetClient() as client:
        return await client.get_agent_relationships(agent_id, direction=direction)


@mcp.tool()
async def get_hub_agents(limit: int = 10) -> dict[str, Any]:
    """Return the most-connected agents in the Minuet relationship graph.

    Useful for discovering which agents other agents actually work with.

    Args:
        limit: Maximum number of hubs to return (default 10).
    """
    async with MinuetClient() as client:
        data = await client.get_clusters()
    hubs = data.get("hubs", [])[:limit]
    return {"count": len(hubs), "hubs": hubs}


@mcp.tool()
async def get_owner_ecosystems(limit: int = 10) -> dict[str, Any]:
    """Return owners who operate multiple connected agents.

    An "ecosystem" is a single wallet address with 2+ named agents that
    have at least one relationship. Useful for finding multi-agent teams.

    Args:
        limit: Maximum number of ecosystems to return (default 10).
    """
    async with MinuetClient() as client:
        data = await client.get_clusters()
    ecosystems = data.get("ecosystems", [])[:limit]
    return {"count": len(ecosystems), "ecosystems": ecosystems}


@mcp.tool()
async def get_relationship_graph(min_connections: int = 0) -> dict[str, Any]:
    """Return the full set of relationships as a graph.

    Args:
        min_connections: Filter out agents with fewer than this many
            relationships from the returned edge list (default 0 = no filter).
    """
    async with MinuetClient() as client:
        data = await client.list_relationships()
    relationships = data.get("relationships", [])

    if min_connections > 0:
        from collections import Counter

        counts: Counter[str] = Counter()
        for r in relationships:
            counts[r.get("from_agent", "")] += 1
            counts[r.get("to_agent", "")] += 1
        relationships = [
            r
            for r in relationships
            if counts[r.get("from_agent", "")] >= min_connections
            and counts[r.get("to_agent", "")] >= min_connections
        ]

    return {"count": len(relationships), "relationships": relationships}


@mcp.tool()
async def get_network_stats() -> dict[str, Any]:
    """Return aggregate statistics about the Minuet relationship graph.

    Returns totals for relationships, agents, named agents, verified vs
    inferred status, and the top relationship types.
    """
    from collections import Counter

    async with MinuetClient() as client:
        clusters = await client.get_clusters()
        rels = await client.list_relationships()

    relationships = rels.get("relationships", [])
    status_counts: Counter[str] = Counter(r.get("status", "") for r in relationships)
    type_counts: Counter[str] = Counter(
        r.get("relationship_type", "") for r in relationships
    )

    stats = dict(clusters.get("stats", {}))
    stats["by_status"] = dict(status_counts)
    stats["by_relationship_type"] = dict(type_counts)
    return stats


@mcp.tool()
async def get_recent_relationships(limit: int = 20) -> dict[str, Any]:
    """Return the most recently created relationships.

    Args:
        limit: Maximum number of relationships to return (default 20).
    """
    async with MinuetClient() as client:
        data = await client.list_relationships()
    relationships = data.get("relationships", [])
    relationships.sort(key=lambda r: r.get("created_at") or "", reverse=True)
    return {"count": min(limit, len(relationships)), "relationships": relationships[:limit]}


# ----- Entrypoint -----


def main() -> None:
    """Entrypoint for the `minuet-mcp` console script."""
    mcp.run()


if __name__ == "__main__":
    main()

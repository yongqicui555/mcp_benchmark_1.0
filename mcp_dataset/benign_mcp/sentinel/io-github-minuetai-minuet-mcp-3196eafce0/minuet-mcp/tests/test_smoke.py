"""Smoke tests: package and server import cleanly, all tools register."""

from __future__ import annotations


def test_package_imports() -> None:
    import minuet_mcp  # noqa: F401


def test_server_imports() -> None:
    from minuet_mcp import server  # noqa: F401


async def test_expected_tools_registered() -> None:
    from minuet_mcp.server import mcp

    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    expected = {
        "search_agents",
        "get_agent",
        "get_agent_relationships",
        "get_hub_agents",
        "get_owner_ecosystems",
        "get_relationship_graph",
        "get_network_stats",
        "get_recent_relationships",
    }
    assert expected <= names, f"missing tools: {expected - names}"

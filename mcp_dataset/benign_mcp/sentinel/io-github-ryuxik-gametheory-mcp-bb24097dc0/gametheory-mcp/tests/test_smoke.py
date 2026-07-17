"""
Smoke tests — verify the package imports and each tier's headline tool
returns sensible output. Detailed math tests live in the upstream private
repo's tournament harness.
"""
import pytest


def test_package_imports():
    import gametheory_mcp
    assert gametheory_mcp.__version__


def test_tier1_sell_next_offer_returns_in_unit_interval():
    from gametheory_mcp.negotiation import sell_next_offer
    rec = sell_next_offer(
        my_reservation=0.4,
        opponent_offer_history=[0.6, 0.55],
        my_offer_history=[0.85],
        deadline_rounds=8,
        pareto_knob=0.5,
    )
    assert 0.0 <= rec["recommended_offer"] <= 1.0
    assert rec["recommended_offer"] >= 0.4   # never below reservation


def test_tier1_buy_next_offer_runs_with_anchor_defense():
    from gametheory_mcp.negotiation import buy_next_offer
    rec = buy_next_offer(
        my_reservation=0.5,
        seller_offer_history=[0.20],
        my_offer_history=[],
        deadline_rounds=8,
        defenses=["anchor_attack_detection"],
        market_prior={"mu": 0.55, "sigma": 0.10},
    )
    assert "recommended_offer" in rec
    assert any(w["code"] == "anchor_attack_detected" for w in rec["warnings"])


def test_tier1_detect_anchor_attack_flags_extreme_opening():
    from gametheory_mcp.negotiation import detect_anchor_attack
    res = detect_anchor_attack(
        opponent_offer_history=[0.20],
        market_prior={"mu": 0.55, "sigma": 0.10},
    )
    assert res["is_anchor_attack"] is True


def test_tier2_vickrey_is_truthful():
    from gametheory_mcp.auctions import optimal_bid
    res = optimal_bid(
        auction_format="second_price_vickrey",
        my_valuation=0.7,
        n_competing_bidders=2,
        competitor_value_prior={"family": "uniform",
                                 "params": {"low": 0.0, "high": 1.0}},
    )
    assert res["optimal_bid"] == 0.7
    assert res["dominant_strategy"] is True


def test_tier2_optimal_reserve_uniform():
    from gametheory_mcp.auctions import optimal_reserve
    res = optimal_reserve(
        bidder_value_prior={"family": "uniform",
                             "params": {"low": 0.0, "high": 1.0}},
        n_bidders=3,
        seller_valuation=0.0,
    )
    assert res["reserve_price"] == pytest.approx(0.5, abs=0.01)


def test_tier3_gale_shapley_textbook():
    from gametheory_mcp.mechanism import gale_shapley
    res = gale_shapley(
        proposers=[
            {"id": "a", "preferences": ["X", "Y"]},
            {"id": "b", "preferences": ["Y", "X"]},
        ],
        receivers=[
            {"id": "X", "preferences": ["a", "b"]},
            {"id": "Y", "preferences": ["b", "a"]},
        ],
    )
    assert res["matching"] == {"a": "X", "b": "Y"}
    assert res["blocking_pairs"] == []


def test_mcp_server_lists_all_tools():
    """Importing the server module registers all @mcp.tool decorators."""
    from gametheory_mcp.server import mcp
    tools = list(mcp._tool_manager._tools.keys())  # FastMCP internal API
    expected_prefixes = ("gt_negotiation_", "gt_auction_", "gt_mechanism_")
    assert any(t.startswith(p) for t in tools for p in expected_prefixes)
    assert len(tools) >= 10  # 3 negotiation + 4 auction + 3 mechanism = 10

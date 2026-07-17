"""
MCP server binding for the gametheory toolkit.

Run as a stdio MCP server (for local agents):
    gametheory-mcp serve         # console script
    python -m gametheory_mcp     # equivalent

Tools are namespaced by tier:
  - gt_negotiation_*   (Tier 1: multi-round bargaining)
  - gt_auction_*       (Tier 2: single-unit auctions)
  - gt_mechanism_*     (Tier 3: marketplace operator primitives)

First-strike commit-reveal (the cryptographic buy-side defense) lives on
the hosted API at https://api.snhp.dev — it requires a server-side EdDSA
key and a global commitment ledger, which can't run cleanly in a stdio
MCP process. Call /v1/negotiation/declare_first_strike + reveal_first_strike
directly via HTTP for that workflow.
"""
from __future__ import annotations

from typing import Literal, Optional

from mcp.server.fastmcp import FastMCP

from gametheory_mcp.negotiation import (
    sell_next_offer, buy_next_offer, detect_anchor_attack,
)
from gametheory_mcp.auctions import (
    optimal_bid, optimal_reserve, format_recommendation, simulate,
)
from gametheory_mcp.mechanism import (
    gale_shapley, optimal_auction_design, posted_price_optimal,
)


mcp = FastMCP(
    "gametheory",
    instructions=(
        "Equilibrium-aware primitives for AI agents. Tier 1 (negotiation), "
        "Tier 2 (auctions), Tier 3 (mechanism design). All math runs locally. "
        "First-strike commit-reveal (buy-side cryptographic defense) is on "
        "the hosted API at api.snhp.dev — it needs server-side keys.\n\n"
        "Honest limitation: returned strategies are *vanilla* — for the "
        "tournament-tuned (NSGA-II Pareto-validated) parameters, point your "
        "calls at api.snhp.dev (free tier, 600 req/min)."
    ),
)


# ─── Tier 1: Negotiation ─────────────────────────────────────────────────────


@mcp.tool()
def gt_negotiation_sell_next_offer(
    my_reservation: float,
    opponent_offer_history: list[float],
    my_offer_history: list[float],
    deadline_rounds: int,
    pareto_knob: float = 0.5,
    buyer_wtp_prior: Optional[dict] = None,
) -> dict:
    """
    Sell-side next-offer recommendation. pareto_knob ∈ [0, 1] interpolates
    between deal-rate-max (0) and H2H-margin-max (1). Returns the
    recommended offer (in our utility space), acceptance probability,
    expected payoff, and the inferred posterior over the buyer's WTP.
    """
    return sell_next_offer(
        my_reservation=my_reservation,
        opponent_offer_history=opponent_offer_history,
        my_offer_history=my_offer_history,
        deadline_rounds=deadline_rounds,
        pareto_knob=pareto_knob,
        buyer_wtp_prior=buyer_wtp_prior,
    )


@mcp.tool()
def gt_negotiation_buy_next_offer(
    my_reservation: float,
    seller_offer_history: list[float],
    my_offer_history: list[float],
    deadline_rounds: int,
    pareto_knob: float = 0.5,
    defenses: Optional[list[str]] = None,
    market_prior: Optional[dict] = None,
) -> dict:
    """
    Buy-side next-offer recommendation with a defense bundle. If
    `anchor_attack_detection` is in defenses, supply `market_prior`
    {mu, sigma}. Returns recommended offer + warnings + defense actions.
    """
    return buy_next_offer(
        my_reservation=my_reservation,
        seller_offer_history=seller_offer_history,
        my_offer_history=my_offer_history,
        deadline_rounds=deadline_rounds,
        pareto_knob=pareto_knob,
        defenses=defenses,
        market_prior=market_prior,
    )


@mcp.tool()
def gt_negotiation_detect_anchor_attack(
    opponent_offer_history: list[float],
    market_prior: dict,
) -> dict:
    """
    Z-score the opponent's opening offer against a market prior {mu, sigma}.
    Recommends ignore / counter_with_market / walk_away.
    """
    return detect_anchor_attack(
        opponent_offer_history=opponent_offer_history,
        market_prior=market_prior,
    )


# ─── Tier 2: Auctions ────────────────────────────────────────────────────────


@mcp.tool()
def gt_auction_optimal_bid(
    auction_format: Literal["first_price", "second_price_vickrey", "english_ascending"],
    my_valuation: float,
    n_competing_bidders: int,
    competitor_value_prior: dict,
    reserve_price: Optional[float] = None,
    risk_aversion: float = 1.0,
) -> dict:
    """
    Optimal bid for {first_price | second_price_vickrey | english_ascending}.
    Vickrey is truthful. First-price uses the BNE for symmetric IPV.
    """
    return optimal_bid(
        auction_format=auction_format,
        my_valuation=my_valuation,
        n_competing_bidders=n_competing_bidders,
        competitor_value_prior=competitor_value_prior,
        reserve_price=reserve_price,
        risk_aversion=risk_aversion,
    )


@mcp.tool()
def gt_auction_optimal_reserve(
    bidder_value_prior: dict, n_bidders: int, seller_valuation: float,
) -> dict:
    """Myerson optimal reserve from virtual-value-equal-seller-valuation."""
    return optimal_reserve(
        bidder_value_prior=bidder_value_prior,
        n_bidders=n_bidders,
        seller_valuation=seller_valuation,
    )


@mcp.tool()
def gt_auction_format_recommendation(
    bidder_value_prior: dict, n_bidders: int, seller_valuation: float,
    weights: Optional[dict] = None,
) -> dict:
    """Recommend format from {first_price, vickrey, english} given weights."""
    return format_recommendation(
        bidder_value_prior=bidder_value_prior, n_bidders=n_bidders,
        seller_valuation=seller_valuation, weights=weights,
    )


@mcp.tool()
def gt_auction_simulate(
    auction_format: Literal["first_price", "second_price_vickrey", "english_ascending"],
    bidder_priors: list[dict], reserve_price: float,
    n_simulations: int = 10_000, seed: Optional[int] = None,
) -> dict:
    """Monte Carlo auction revenue + efficiency."""
    return simulate(
        auction_format=auction_format, bidder_priors=bidder_priors,
        reserve_price=reserve_price, n_simulations=n_simulations, seed=seed,
    )


# ─── Tier 3: Mechanism Design ───────────────────────────────────────────────


@mcp.tool()
def gt_mechanism_gale_shapley(
    proposers: list[dict], receivers: list[dict],
) -> dict:
    """
    Stable matching via deferred acceptance. Proposers/receivers each have
    {id, preferences} (and optional capacity for receivers). Returns a
    proposer-optimal stable matching plus a blocking-pair sanity check.
    """
    return gale_shapley(proposers=proposers, receivers=receivers)


@mcp.tool()
def gt_mechanism_optimal_auction_design(
    bidder_priors: list[dict],
    seller_valuation: float,
    objective: Literal["revenue", "welfare"] = "revenue",
    n_simulations: int = 5_000,
    seed: int = 42,
) -> dict:
    """
    Myerson revenue-optimal mechanism for asymmetric IPV. Per-bidder
    reserves; collapses to second-price-with-reserve under symmetric IPV.
    """
    return optimal_auction_design(
        bidder_priors=bidder_priors, seller_valuation=seller_valuation,
        objective=objective, n_simulations=n_simulations, seed=seed,
    )


@mcp.tool()
def gt_mechanism_posted_price_optimal(
    buyer_arrival_prior: dict,
    arrival_rate_per_second: float,
    inventory: int,
    horizon_seconds: float,
    n_simulations: int = 2_000,
    seed: int = 42,
) -> dict:
    """
    Gallego-van Ryzin posted-price (static p* + dynamic backward-DP schedule).
    """
    return posted_price_optimal(
        buyer_arrival_prior=buyer_arrival_prior,
        arrival_rate_per_second=arrival_rate_per_second,
        inventory=inventory, horizon_seconds=horizon_seconds,
        n_simulations=n_simulations, seed=seed,
    )


def main() -> None:
    """Entry point for the `gametheory-mcp` console script (stdio MCP)."""
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()

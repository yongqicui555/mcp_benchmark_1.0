# gametheory-mcp

mcp-name: io.github.ryuxik/gametheory-mcp

**Equilibrium-aware primitives for AI agents** — negotiation, auctions, mechanism design — exposed over MCP and importable as a Python library.

LLMs are structurally bad at multi-round, opponent-modeling problems with closed-form solutions. This package gives them the math.

[![PyPI](https://img.shields.io/pypi/v/gametheory-mcp.svg)](https://pypi.org/project/gametheory-mcp/)
[![License: Apache 2.0](https://img.shields.io/badge/License-Apache_2.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

## Install

```sh
pip install gametheory-mcp
```

## Use it as an MCP server

Add to your MCP-aware client config (Claude Desktop, etc.):

```json
{
  "mcpServers": {
    "gametheory": {
      "command": "gametheory-mcp"
    }
  }
}
```

The server is stdio-only. 13 tools across three tiers:

- **Tier 1 — Negotiation**: `gt_negotiation_sell_next_offer`, `gt_negotiation_buy_next_offer`, `gt_negotiation_detect_anchor_attack`
- **Tier 2 — Auctions**: `gt_auction_optimal_bid`, `gt_auction_optimal_reserve`, `gt_auction_format_recommendation`, `gt_auction_simulate`
- **Tier 3 — Mechanism Design**: `gt_mechanism_gale_shapley`, `gt_mechanism_optimal_auction_design`, `gt_mechanism_posted_price_optimal`

## Use it as a library

```python
from gametheory_mcp.negotiation import sell_next_offer
from gametheory_mcp.auctions import optimal_bid
from gametheory_mcp.mechanism import gale_shapley

# Sell-side next-offer recommendation
rec = sell_next_offer(
    my_reservation=0.4,
    opponent_offer_history=[0.6, 0.55],
    my_offer_history=[0.85],
    deadline_rounds=8,
    pareto_knob=0.5,  # 0=max deal rate, 1=max margin
)
# → {recommended_offer, acceptance_probability, expected_payoff, ...}

# Vickrey is dominant-strategy truthful
bid = optimal_bid(
    auction_format="second_price_vickrey",
    my_valuation=0.7,
    n_competing_bidders=3,
    competitor_value_prior={"family": "uniform",
                             "params": {"low": 0, "high": 1}},
)
# → {optimal_bid: 0.7, dominant_strategy: True, ...}
```

## What's in the package

The math primitives — Rubinstein 1982 SPE, Myerson 1981 optimal auction,
Gale-Shapley deferred acceptance, Bayesian particle filter for opponent
WTP inference. Empirical Pareto frontier data and tournament-tuned
parameters are bundled in `gametheory_mcp/_data/`.

## What's NOT in the package

The hosted API at https://api.snhp.dev adds:

- **Cryptographic first-strike commit-reveal** for buy-side defense
  (requires server-side EdDSA keys + global commitment ledger; can't
  run cleanly in a stdio MCP process)
- **Vertical-specific Bayesian priors** that warm-start new agents from
  the opt-in telemetry corpus
- **GDPR-compliant data export and deletion** for the corpus

The hosted API is free for math endpoints (600 requests/min per key).
Self-serve key issuance at `POST https://api.snhp.dev/v1/keys`.

## Empirical anchor

SNHP — the negotiation strategy this package wraps — was rank #1 of 21
in a NegMAS round-robin tournament against well-known programmatic
opponents (Aspiration, Anchorer, BATNA Bluffer, etc.). Statistically beats
Aspiration (p=0.011), Split-the-Diff (p=0.014), Fair Demand (p<0.001).

Live leaderboard with LLM baselines: https://snhp.dev

## License

Apache 2.0. See `LICENSE`.

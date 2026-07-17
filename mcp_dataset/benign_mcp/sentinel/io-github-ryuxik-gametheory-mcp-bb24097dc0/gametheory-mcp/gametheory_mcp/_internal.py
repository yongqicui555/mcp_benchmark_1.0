"""
Shared internals: prior validation, auction-format and prior-family Literal
types, Myerson reserve solver. Used by Tier 2 (auctions) and Tier 3
(mechanism design) handlers.
"""
from __future__ import annotations

from typing import Literal, get_args

import numpy as np
from scipy import stats
from scipy.optimize import brentq


AuctionFormat = Literal["first_price", "second_price_vickrey", "english_ascending"]
PriorFamily = Literal["lognorm", "uniform"]

VALID_AUCTION_FORMATS: tuple[str, ...] = get_args(AuctionFormat)
VALID_PRIOR_FAMILIES: tuple[str, ...] = get_args(PriorFamily)


def validate_prior(prior: dict) -> None:
    family = prior.get("family")
    if family not in VALID_PRIOR_FAMILIES:
        raise ValueError(
            f"prior.family must be one of {VALID_PRIOR_FAMILIES}, got {family!r}"
        )
    params = prior.get("params") or {}
    if family == "lognorm":
        if "mu" not in params or "sigma" not in params:
            raise ValueError("lognorm prior requires params.mu and params.sigma")
    elif family == "uniform":
        if "low" not in params or "high" not in params:
            raise ValueError("uniform prior requires params.low and params.high")
        if params["high"] <= params["low"]:
            raise ValueError("uniform high must exceed low")


def prior_to_scipy_dist(prior: dict):
    family = prior["family"]
    params = prior["params"]
    if family == "uniform":
        return stats.uniform(loc=params["low"], scale=params["high"] - params["low"])
    return stats.lognorm(s=params["sigma"], scale=np.exp(params["mu"]))


def sample_prior(prior: dict, n: int, rng) -> np.ndarray:
    family = prior["family"]
    params = prior["params"]
    if family == "uniform":
        return rng.uniform(params["low"], params["high"], size=n)
    return rng.lognormal(mean=params["mu"], sigma=params["sigma"], size=n)


def myerson_reserve(prior: dict, seller_valuation: float) -> float:
    """Closed form for uniform; brentq for lognormal. Falls back to the
    lognormal median if no sign change is found in the search interval."""
    family = prior["family"]
    params = prior["params"]
    if family == "uniform":
        a, b = params["low"], params["high"]
        return max((b + seller_valuation) / 2.0, seller_valuation, a)
    mu, sigma = params["mu"], params["sigma"]
    dist = stats.lognorm(s=sigma, scale=np.exp(mu))

    def virtual_value_minus_seller(v: float) -> float:
        F = float(dist.cdf(v))
        f = float(dist.pdf(v))
        if f < 1e-12:
            return float("inf")
        return v - (1.0 - F) / f - seller_valuation

    try:
        r = float(brentq(
            virtual_value_minus_seller,
            np.exp(mu) * 0.01, np.exp(mu) * 100.0,
        ))
    except ValueError:
        r = float(np.exp(mu))
    return max(r, seller_valuation)

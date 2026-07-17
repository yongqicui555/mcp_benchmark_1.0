"""
RFM Score Calculator

Calculates Recency, Frequency, and Monetary scores based on configurable thresholds.
Pure Python — no numpy dependency.
"""

from typing import Optional


def _percentile(data: list[float], p: float) -> float:
    """Calculate the p-th percentile of a list of numbers (pure Python).

    Uses linear interpolation, matching numpy's default method.
    """
    if not data:
        return 0.0
    sorted_data = sorted(data)
    n = len(sorted_data)
    if n == 1:
        return sorted_data[0]
    k = (p / 100.0) * (n - 1)
    f = int(k)
    c = f + 1
    if c >= n:
        return sorted_data[-1]
    d = k - f
    return sorted_data[f] + d * (sorted_data[c] - sorted_data[f])


class RFMScorer:
    """Calculate R, F, M scores for customer segmentation."""

    def __init__(self, thresholds: Optional[dict] = None):
        self.thresholds = thresholds or {}
        self._cached_percentiles: dict[tuple, list[float]] = {}

    def score_recency(self, days_since: int) -> int:
        """Score based on days since last purchase (lower = better).

        Default thresholds:
            0-30 days: 5 | 31-90: 4 | 91-180: 3 | 181-365: 2 | 366+: 1
        """
        config = self.thresholds.get("recency", {})
        thresholds = config.get("days", [30, 90, 180, 365])
        scores = config.get("scores", [5, 4, 3, 2, 1])

        for i, threshold in enumerate(thresholds):
            if days_since <= threshold:
                return scores[i]
        return scores[-1]

    def score_frequency(self, transaction_count: int) -> int:
        """Score based on number of transactions (higher = better).

        Default thresholds:
            10+: 5 | 5-9: 4 | 3-4: 3 | 2: 2 | 1: 1
        """
        config = self.thresholds.get("frequency", {})
        thresholds = config.get("counts", [10, 5, 3, 2])
        scores = config.get("scores", [5, 4, 3, 2, 1])

        for i, threshold in enumerate(thresholds):
            if transaction_count >= threshold:
                return scores[i]
        return scores[-1]

    def score_monetary(self, revenue: float, all_revenues: list[float]) -> int:
        """Score based on total revenue using percentile method.

        Default: Top 20% = 5, 60-80% = 4, 40-60% = 3, 20-40% = 2, Bottom 20% = 1
        """
        config = self.thresholds.get("monetary", {})
        method = config.get("method", "percentile")

        if method == "fixed":
            return self._score_monetary_fixed(revenue, config)
        return self._score_monetary_percentile(revenue, all_revenues, config)

    def _score_monetary_percentile(
        self, revenue: float, all_revenues: list[float], config: dict
    ) -> int:
        percentiles = config.get("percentiles", [80, 60, 40, 20])

        cache_key = tuple(sorted(all_revenues))
        if cache_key not in self._cached_percentiles:
            self._cached_percentiles[cache_key] = [
                _percentile(all_revenues, p) for p in percentiles
            ]

        thresholds = self._cached_percentiles[cache_key]

        if revenue >= thresholds[0]:
            return 5
        elif revenue >= thresholds[1]:
            return 4
        elif revenue >= thresholds[2]:
            return 3
        elif revenue >= thresholds[3]:
            return 2
        else:
            return 1

    def _score_monetary_fixed(self, revenue: float, config: dict) -> int:
        thresholds = config.get("thresholds", [100000, 50000, 25000, 10000])
        scores = config.get("scores", [5, 4, 3, 2, 1])

        for i, threshold in enumerate(thresholds):
            if revenue >= threshold:
                return scores[i]
        return scores[-1]


class B2BServiceScorer(RFMScorer):
    """RFM Scorer with B2B service thresholds (longer buying cycles)."""

    def __init__(self):
        super().__init__(
            {
                "recency": {"days": [60, 180, 365, 730], "scores": [5, 4, 3, 2, 1]},
                "frequency": {"counts": [5, 3, 2, 1], "scores": [5, 4, 3, 2, 1]},
                "monetary": {"method": "percentile", "percentiles": [80, 60, 40, 20]},
            }
        )


class B2BSaaSScorer(RFMScorer):
    """RFM Scorer for B2B SaaS (subscription businesses)."""

    def __init__(self):
        super().__init__(
            {
                "recency": {"days": [30, 60, 90, 180], "scores": [5, 4, 3, 2, 1]},
                "frequency": {
                    "counts": [5, 3, 2, 1, 0],
                    "scores": [5, 4, 3, 2, 1],
                },
                "monetary": {"method": "percentile", "percentiles": [80, 60, 40, 20]},
            }
        )


class B2BManufacturingScorer(RFMScorer):
    """RFM Scorer for B2B manufacturing (long cycles, large transactions)."""

    def __init__(self):
        super().__init__(
            {
                "recency": {
                    "days": [90, 365, 730, 1095],
                    "scores": [5, 4, 3, 2, 1],
                },
                "frequency": {"counts": [8, 4, 2, 1], "scores": [5, 4, 3, 2, 1]},
                "monetary": {"method": "percentile", "percentiles": [80, 60, 40, 20]},
            }
        )

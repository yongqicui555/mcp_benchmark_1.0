"""
RFM Segment Classifier

Assigns customers to segments based on their R, F, M scores.
Implements 11 standard RFM segments.
"""

from typing import Optional


class Segmenter:
    """Classify customers into RFM segments based on scores."""

    SEGMENTS = {
        "Champions": {
            "description": "Best customers, highest value",
            "r_min": 4,
            "f_min": 4,
            "total_min": 13,
            "action": "Reward loyalty, ask for referrals",
        },
        "Loyal Customers": {
            "description": "Consistent, engaged customers",
            "r_min": 3,
            "f_min": 3,
            "total_min": 11,
            "action": "Cross-sell, maintain relationship",
        },
        "Potential Loyalists": {
            "description": "Recent buyers who could grow",
            "r_min": 4,
            "f_range": (2, 3),
            "total_min": 9,
            "action": "Nurture with targeted content",
        },
        "New Customers": {
            "description": "Just acquired, high potential",
            "r_exact": 5,
            "f_exact": 1,
            "total_min": 8,
            "action": "Exceptional onboarding",
        },
        "Promising": {
            "description": "Recent single purchase, promising",
            "r_exact": 4,
            "f_exact": 1,
            "total_min": 7,
            "action": "Second purchase incentive",
        },
        "Need Attention": {
            "description": "Average customers, slipping",
            "r_exact": 3,
            "f_range": (2, 3),
            "total_range": (7, 10),
            "action": "Re-engagement campaigns",
        },
        "About to Sleep": {
            "description": "Haven't purchased recently",
            "r_range": (2, 3),
            "f_range": (1, 2),
            "total_range": (5, 8),
            "action": "Win-back campaigns",
        },
        "At Risk": {
            "description": "Were good, slipping away",
            "r_max": 2,
            "f_min": 3,
            "total_min": 8,
            "action": "Urgent outreach, investigate",
        },
        "Can't Lose Them": {
            "description": "High value but dormant",
            "r_range": (1, 2),
            "f_min": 4,
            "total_min": 10,
            "action": "Executive outreach, service recovery",
        },
        "Hibernating": {
            "description": "Long time since purchase",
            "r_max": 2,
            "f_max": 2,
            "total_max": 6,
            "action": "Low-cost re-engagement",
        },
        "Lost": {
            "description": "Gone, unlikely to return",
            "r_exact": 1,
            "f_exact": 1,
            "total_max": 4,
            "action": "Remove from active campaigns",
        },
    }

    def classify(self, r: int, f: int, m: int) -> str:
        """Classify customer into segment based on R, F, M scores (each 1-5)."""
        total = r + f + m

        if r >= 4 and f >= 4 and total >= 13:
            return "Champions"
        if r in [1, 2] and f >= 4 and total >= 10:
            return "Can't Lose Them"
        if r <= 2 and f >= 3 and total >= 8:
            return "At Risk"
        if r >= 3 and f >= 3 and total >= 11:
            return "Loyal Customers"
        if r == 5 and f == 1 and total >= 8:
            return "New Customers"
        if r == 4 and f == 1 and total >= 7:
            return "Promising"
        if r >= 4 and f in [2, 3] and total >= 9:
            return "Potential Loyalists"
        if r == 3 and f in [2, 3] and 7 <= total <= 10:
            return "Need Attention"
        if r in [2, 3] and f in [1, 2] and 5 <= total <= 8:
            return "About to Sleep"
        if r == 1 and f == 1 and total <= 4:
            return "Lost"
        if r <= 2 and f <= 2 and total <= 6:
            return "Hibernating"

        # Edge cases
        if r >= 4:
            return "Potential Loyalists"
        if f >= 3:
            return "At Risk"
        return "Need Attention"

    def get_segment_info(self, segment: str) -> Optional[dict]:
        return self.SEGMENTS.get(segment)

    def get_action(self, segment: str) -> str:
        info = self.SEGMENTS.get(segment, {})
        return info.get("action", "Review manually")

    def get_all_segments(self) -> list[str]:
        return [
            "Champions",
            "Loyal Customers",
            "Potential Loyalists",
            "New Customers",
            "Promising",
            "Need Attention",
            "About to Sleep",
            "At Risk",
            "Can't Lose Them",
            "Hibernating",
            "Lost",
        ]

    def is_top_performer(self, segment: str) -> bool:
        return segment in ["Champions", "Loyal Customers"]

    def is_at_risk(self, segment: str) -> bool:
        return segment in ["At Risk", "Can't Lose Them"]

    def is_low_value(self, segment: str) -> bool:
        return segment in ["Hibernating", "Lost"]


class ICPAnalyzer:
    """Analyze top performers for ICP patterns."""

    def __init__(self, segmenter: Optional[Segmenter] = None):
        self.segmenter = segmenter or Segmenter()

    def filter_top_performers(
        self, clients: list[dict], min_total: int = 11
    ) -> list[dict]:
        top = []
        for client in clients:
            segment = client.get("segment", "")
            rfm_total = client.get("rfm_total", 0)
            if self.segmenter.is_top_performer(segment) or rfm_total >= min_total:
                top.append(client)
        return top

    def extract_patterns(
        self, top_performers: list[dict], all_clients: list[dict]
    ) -> dict:
        return {
            "industry": self._analyze_dimension(
                top_performers, all_clients, "industry"
            ),
            "employee_count": self._analyze_dimension(
                top_performers, all_clients, "employee_count"
            ),
            "company_revenue": self._analyze_dimension(
                top_performers, all_clients, "company_revenue"
            ),
            "region": self._analyze_dimension(
                top_performers, all_clients, "state_region"
            ),
        }

    def _analyze_dimension(
        self, top: list[dict], all_clients: list[dict], field: str
    ) -> dict:
        top_counts: dict[str, int] = {}
        for client in top:
            value = client.get(field, "Unknown")
            top_counts[value] = top_counts.get(value, 0) + 1

        all_counts: dict[str, int] = {}
        for client in all_clients:
            value = client.get(field, "Unknown")
            all_counts[value] = all_counts.get(value, 0) + 1

        results = []
        for value, count in top_counts.items():
            pct_top = count / len(top) * 100 if top else 0
            pct_all = (
                all_counts.get(value, 0) / len(all_clients) * 100
                if all_clients
                else 0
            )
            lift = pct_top / pct_all if pct_all > 0 else 0

            results.append(
                {
                    "value": value,
                    "count": count,
                    "pct_top": round(pct_top, 1),
                    "pct_all": round(pct_all, 1),
                    "lift": round(lift, 2),
                }
            )

        results.sort(key=lambda x: x["pct_top"], reverse=True)

        return {
            "distribution": results,
            "primary": [r for r in results if r["lift"] >= 2.0],
            "secondary": [r for r in results if 1.5 <= r["lift"] < 2.0],
            "negative": [r for r in results if r["lift"] < 0.5],
        }

    def generate_tier_recommendations(self, patterns: dict) -> dict:
        primary_industry = self._get_primary_values(patterns.get("industry", {}))
        primary_size = self._get_primary_values(patterns.get("employee_count", {}))
        primary_revenue = self._get_primary_values(patterns.get("company_revenue", {}))

        return {
            "tier_1": {
                "criteria": {
                    "industry": primary_industry,
                    "size": primary_size,
                    "revenue": primary_revenue,
                },
                "match_required": "all",
                "priority": "HIGHEST",
            },
            "tier_2": {
                "criteria": "Match 2/3 Tier 1 criteria",
                "match_required": "2 of 3",
                "priority": "HIGH",
            },
            "tier_3": {
                "criteria": "Match 1/3 Tier 1 criteria",
                "match_required": "1 of 3",
                "priority": "SELECTIVE",
            },
            "tier_4": {
                "criteria": "Does not match criteria",
                "anti_patterns": {
                    "industry": patterns.get("industry", {}).get("negative", []),
                    "size": patterns.get("employee_count", {}).get("negative", []),
                    "revenue": patterns.get("company_revenue", {}).get("negative", []),
                },
                "priority": "AVOID",
            },
        }

    def _get_primary_values(self, pattern_data: dict) -> list[str]:
        primary = pattern_data.get("primary", [])
        return [p["value"] for p in primary[:3]]

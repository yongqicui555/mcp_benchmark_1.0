"""
ICP Scorer — 14.5-Point Ideal Customer Profile Scoring Model

Codified from:
- scoring-model.md (exact point values)
- tier-definitions.md (tier thresholds)
- icp-qualification SKILL.md (5 discriminators, exclusions)
"""

from dataclasses import dataclass
from typing import Optional


EXCLUDED_INDUSTRIES = [
    "agencies",
    "agency",
    "consulting",
    "consulting firm",
    "b2c",
    "retail",
    "non-profit",
    "nonprofit",
    "staffing",
    "events",
    "events services",
    "vc",
    "pe",
    "venture capital",
    "private equity",
]


@dataclass
class TierInfo:
    number: int
    label: str
    color: str
    hubspot_value: str
    min_score: float
    max_score: float
    engagement_strategy: str


TIERS = [
    TierInfo(
        number=1,
        label="Ideal",
        color="green",
        hubspot_value="tier_1_ideal",
        min_score=12.0,
        max_score=14.5,
        engagement_strategy=(
            "Highest priority — pursue aggressively. Same-day response SLA. "
            "Senior team, custom proposals, full value pricing. "
            "Dedicated account plan with expansion roadmap."
        ),
    ),
    TierInfo(
        number=2,
        label="Strong",
        color="blue",
        hubspot_value="tier_2_strong",
        min_score=9.0,
        max_score=11.9,
        engagement_strategy=(
            "High priority — active pursuit. 24h response SLA. "
            "Standard team, templated proposals with customization. "
            "Standard pricing, selective discounting for strategic wins."
        ),
    ),
    TierInfo(
        number=3,
        label="Moderate",
        color="yellow",
        hubspot_value="tier_3_moderate",
        min_score=6.0,
        max_score=8.9,
        engagement_strategy=(
            "Selective — pursue only if inbound or strategic reason. "
            "48h response SLA, no proactive outreach. "
            "Junior team or automated workflows. Standard pricing only."
        ),
    ),
    TierInfo(
        number=4,
        label="Poor",
        color="red",
        hubspot_value="tier_4_poor",
        min_score=0.0,
        max_score=5.9,
        engagement_strategy=(
            "Deprioritize — nurture only. No SLA. Fully automated. "
            "General newsletter only. Consider partner referral."
        ),
    ),
]


@dataclass
class ICPResult:
    total_score: float
    tier: dict
    breakdown: dict
    exclusion_check: dict
    recommended_action: str
    engagement_strategy: str


class ICPScorer:
    """14.5-point ICP scoring model across Firmographic, Behavioral, and Strategic dimensions.

    Accepts optional scoring_config to override default parameters:
        - primary_industries: list of high-score industries (2 pts)
        - adjacent_industries: list of medium-score industries (1 pt)
        - excluded_industries: list of auto-excluded industries
        - revenue_range: [min, max] for sweet spot (1.5 pts)
        - employee_range: [min, max] for ideal range (1 pt)
        - primary_geography: list of primary market strings (0.5 pts)
        - secondary_geography: list of secondary market strings (0.25 pts)
        - required_tech: list of must-have tech stack items
    """

    def __init__(self, scoring_config: dict | None = None):
        self._config = scoring_config or {}

    def score_company(self, company_data: dict) -> ICPResult:
        """Score a company against the ICP model.

        Args:
            company_data: Dict with keys like industry, annual_revenue, employee_count,
                         geography, tech_stack, growth_signals, content_engagement,
                         purchase_history, decision_maker_access, budget_authority,
                         strategic_alignment.

        Returns:
            ICPResult with full score breakdown.
        """
        # Check exclusions first
        exclusion = self._check_exclusions(company_data)

        # Score each dimension
        firmographic = self._score_firmographic(company_data)
        behavioral = self._score_behavioral(company_data)
        strategic = self._score_strategic(company_data)

        total = round(firmographic["score"] + behavioral["score"] + strategic["score"], 1)

        tier = self.classify_tier(total)

        if exclusion["excluded"]:
            recommended_action = f"EXCLUDED: {exclusion['reason']}. Do not pursue."
            engagement_strategy = "None — excluded from ICP."
        else:
            recommended_action = self._get_recommended_action(tier, total)
            engagement_strategy = tier.engagement_strategy

        return ICPResult(
            total_score=total,
            tier={
                "number": tier.number,
                "label": tier.label,
                "color": tier.color,
                "hubspot_value": tier.hubspot_value,
            },
            breakdown={
                "firmographic": {
                    "score": firmographic["score"],
                    "max": 5.0,
                    "details": firmographic["details"],
                },
                "behavioral": {
                    "score": behavioral["score"],
                    "max": 5.0,
                    "details": behavioral["details"],
                },
                "strategic": {
                    "score": strategic["score"],
                    "max": 4.5,
                    "details": strategic["details"],
                },
            },
            exclusion_check=exclusion,
            recommended_action=recommended_action,
            engagement_strategy=engagement_strategy,
        )

    def classify_tier(self, score: float) -> TierInfo:
        """Classify a score into one of 4 tiers."""
        for tier in TIERS:
            if tier.min_score <= score <= tier.max_score:
                return tier
        return TIERS[-1]  # Default to Tier 4

    # --- Firmographic (5 points max) ---

    def _score_firmographic(self, data: dict) -> dict:
        industry = self._score_industry(data.get("industry", ""))
        revenue = self._score_revenue_range(data.get("annual_revenue"))
        employees = self._score_employee_count(data.get("employee_count"))
        geography = self._score_geography(data.get("geography", ""))

        total = round(industry["score"] + revenue["score"] + employees["score"] + geography["score"], 1)

        return {
            "score": total,
            "details": {
                "industry": industry,
                "revenue_range": revenue,
                "employee_count": employees,
                "geography": geography,
            },
        }

    def _score_industry(self, industry: str) -> dict:
        """Industry scoring (2 pts max)."""
        if not industry:
            return {"score": 0, "max": 2.0, "rationale": "No industry provided"}

        industry_lower = industry.lower().strip()

        # Use config overrides if provided, otherwise defaults
        primary = self._config.get("primary_industries", [
            "technology", "saas", "software", "b2b technology",
            "manufacturing", "industrial",
            "professional services",
        ])
        adjacent = self._config.get("adjacent_industries", [
            "healthcare", "health tech", "fintech", "financial services",
            "construction", "engineering", "logistics", "distribution",
            "education", "edtech",
        ])
        tangential = self._config.get("tangential_industries", [
            "real estate", "media", "telecommunications", "energy",
            "agriculture", "food", "hospitality",
        ])

        for p in primary:
            if p.lower() in industry_lower or industry_lower in p.lower():
                return {"score": 2.0, "max": 2.0, "rationale": f"Primary target industry: {industry}"}

        for a in adjacent:
            if a.lower() in industry_lower or industry_lower in a.lower():
                return {"score": 1.0, "max": 2.0, "rationale": f"Adjacent industry: {industry}"}

        for t in tangential:
            if t.lower() in industry_lower or industry_lower in t.lower():
                return {"score": 0.5, "max": 2.0, "rationale": f"Tangential industry: {industry}"}

        return {"score": 0, "max": 2.0, "rationale": f"Outside target industries: {industry}"}

    def _score_revenue_range(self, annual_revenue: Optional[float]) -> dict:
        """Revenue range scoring (1.5 pts max)."""
        if annual_revenue is None:
            return {"score": 0, "max": 1.5, "rationale": "No revenue data"}

        # Config override: [min, max] for sweet spot
        rev_range = self._config.get("revenue_range")
        if rev_range and len(rev_range) == 2:
            r_min, r_max = rev_range[0], rev_range[1]
            margin = (r_max - r_min) * 0.25  # 25% margin for acceptable/stretch
            if r_min <= annual_revenue <= r_max:
                return {"score": 1.5, "max": 1.5, "rationale": f"Sweet spot: ${annual_revenue:,.0f}"}
            elif (r_min - margin) <= annual_revenue < r_min or r_max < annual_revenue <= (r_max + margin):
                return {"score": 1.0, "max": 1.5, "rationale": f"Acceptable range: ${annual_revenue:,.0f}"}
            elif (r_min - margin * 2) <= annual_revenue < (r_min - margin) or (r_max + margin) < annual_revenue <= (r_max + margin * 2):
                return {"score": 0.5, "max": 1.5, "rationale": f"Stretch range: ${annual_revenue:,.0f}"}
            else:
                return {"score": 0, "max": 1.5, "rationale": f"Outside viable range: ${annual_revenue:,.0f}"}

        # Default Artefact ranges
        if 1_600_000 <= annual_revenue <= 70_000_000:
            return {"score": 1.5, "max": 1.5, "rationale": f"Sweet spot: ${annual_revenue:,.0f}"}
        elif 1_000_000 <= annual_revenue < 1_600_000 or 70_000_000 < annual_revenue <= 100_000_000:
            return {"score": 1.0, "max": 1.5, "rationale": f"Acceptable range: ${annual_revenue:,.0f}"}
        elif 500_000 <= annual_revenue < 1_000_000 or 100_000_000 < annual_revenue <= 200_000_000:
            return {"score": 0.5, "max": 1.5, "rationale": f"Stretch range: ${annual_revenue:,.0f}"}
        else:
            return {"score": 0, "max": 1.5, "rationale": f"Outside viable range: ${annual_revenue:,.0f}"}

    def _score_employee_count(self, employee_count: Optional[int]) -> dict:
        """Employee count scoring (1 pt max)."""
        if employee_count is None:
            return {"score": 0, "max": 1.0, "rationale": "No employee data"}

        # Config override: [min, max] for ideal range
        emp_range = self._config.get("employee_range")
        if emp_range and len(emp_range) == 2:
            e_min, e_max = emp_range[0], emp_range[1]
            margin_low = max(e_min // 2, 1)
            margin_high = e_max + (e_max - e_min) // 2
            if e_min <= employee_count <= e_max:
                return {"score": 1.0, "max": 1.0, "rationale": f"Ideal range: {employee_count}"}
            elif margin_low <= employee_count < e_min or e_max < employee_count <= margin_high:
                return {"score": 0.5, "max": 1.0, "rationale": f"Borderline: {employee_count}"}
            else:
                return {"score": 0, "max": 1.0, "rationale": f"Outside range: {employee_count}"}

        # Default Artefact ranges
        if 10 <= employee_count <= 200:
            return {"score": 1.0, "max": 1.0, "rationale": f"Ideal range: {employee_count}"}
        elif 5 <= employee_count < 10 or 200 < employee_count <= 500:
            return {"score": 0.5, "max": 1.0, "rationale": f"Borderline: {employee_count}"}
        else:
            return {"score": 0, "max": 1.0, "rationale": f"Outside range: {employee_count}"}

    def _score_geography(self, geography: str) -> dict:
        """Geography scoring (0.5 pts max)."""
        if not geography:
            return {"score": 0, "max": 0.5, "rationale": "No geography provided"}

        geo_lower = geography.lower().strip()

        primary = self._config.get("primary_geography", [
            "quebec", "ontario", "bc", "british columbia", "alberta",
            "nova scotia", "canada", "montreal", "toronto", "vancouver",
        ])
        secondary = self._config.get("secondary_geography", [
            "us", "usa", "united states", "new york", "boston", "california",
        ])

        for p in primary:
            if p.lower() in geo_lower or geo_lower in p.lower():
                return {"score": 0.5, "max": 0.5, "rationale": f"Primary market: {geography}"}

        for s in secondary:
            if s.lower() in geo_lower or geo_lower in s.lower():
                return {"score": 0.25, "max": 0.5, "rationale": f"Secondary market: {geography}"}

        return {"score": 0, "max": 0.5, "rationale": f"Outside market: {geography}"}

    # --- Behavioral (5 points max) ---

    def _score_behavioral(self, data: dict) -> dict:
        tech = self._score_tech_stack(data.get("tech_stack", []))
        growth = self._score_growth_signals(data.get("growth_signals", []))
        content = self._score_content_engagement(data.get("content_engagement", "none"))
        purchase = self._score_purchase_history(data.get("purchase_history", "never"))

        total = round(tech["score"] + growth["score"] + content["score"] + purchase["score"], 1)

        return {
            "score": total,
            "details": {
                "tech_stack": tech,
                "growth_signals": growth,
                "content_engagement": content,
                "purchase_frequency": purchase,
            },
        }

    def _score_tech_stack(self, tech_stack: list[str]) -> dict:
        """Tech stack match scoring (2 pts max)."""
        if not tech_stack:
            return {"score": 0, "max": 2.0, "rationale": "No tech stack data"}

        stack_lower = [t.lower().strip() for t in tech_stack]

        has_hubspot = any("hubspot" in t for t in stack_lower)
        has_crm = has_hubspot or any(t in stack_lower for t in ["salesforce", "crm", "pipedrive"])
        has_marketing_automation = any(
            t in stack_lower
            for t in ["marketing automation", "mailchimp", "marketo", "pardot", "activecampaign", "hubspot"]
        )
        has_analytics = any(
            t in stack_lower
            for t in ["google analytics", "ga4", "analytics", "mixpanel", "amplitude"]
        )

        score_count = sum([has_hubspot, has_crm, has_marketing_automation, has_analytics])

        if has_hubspot and score_count >= 3:
            return {"score": 2.0, "max": 2.0, "rationale": f"Full core stack: {', '.join(tech_stack)}"}
        elif has_hubspot and score_count >= 2:
            return {"score": 1.5, "max": 2.0, "rationale": f"Most of required stack: {', '.join(tech_stack)}"}
        elif has_crm:
            return {"score": 1.0, "max": 2.0, "rationale": f"Partial stack (CRM present): {', '.join(tech_stack)}"}
        elif score_count >= 1:
            return {"score": 0.5, "max": 2.0, "rationale": f"Minimal stack: {', '.join(tech_stack)}"}
        else:
            return {"score": 0, "max": 2.0, "rationale": "No relevant tech stack"}

    def _score_growth_signals(self, growth_signals: list[str]) -> dict:
        """Growth signals scoring (1.5 pts max)."""
        if not growth_signals:
            return {"score": 0, "max": 1.5, "rationale": "No growth signals"}

        count = len(growth_signals)
        if count >= 3:
            return {"score": 1.5, "max": 1.5, "rationale": f"Multiple strong signals: {', '.join(growth_signals)}"}
        elif count == 2:
            return {"score": 1.0, "max": 1.5, "rationale": f"Some signals: {', '.join(growth_signals)}"}
        elif count == 1:
            return {"score": 0.5, "max": 1.5, "rationale": f"Weak signal: {growth_signals[0]}"}
        return {"score": 0, "max": 1.5, "rationale": "No growth signals"}

    def _score_content_engagement(self, engagement: str) -> dict:
        """Content engagement scoring (1 pt max)."""
        mapping = {
            "active": (1.0, "Active engager"),
            "occasional": (0.5, "Occasional interaction"),
            "none": (0, "No engagement"),
        }
        score, rationale = mapping.get(engagement.lower(), (0, f"Unknown: {engagement}"))
        return {"score": score, "max": 1.0, "rationale": rationale}

    def _score_purchase_history(self, history: str) -> dict:
        """Purchase frequency scoring (0.5 pts max)."""
        mapping = {
            "regular": (0.5, "Regular buyer of services"),
            "occasional": (0.25, "Occasional service buyer"),
            "never": (0, "No purchase history"),
        }
        score, rationale = mapping.get(history.lower(), (0, f"Unknown: {history}"))
        return {"score": score, "max": 0.5, "rationale": rationale}

    # --- Strategic (4.5 points max) ---

    def _score_strategic(self, data: dict) -> dict:
        decision_maker = self._score_decision_maker_access(
            data.get("decision_maker_access", "none")
        )
        budget = self._score_budget_authority(data.get("budget_authority", "none"))
        alignment = self._score_strategic_alignment(
            data.get("strategic_alignment", "misaligned")
        )

        total = round(decision_maker["score"] + budget["score"] + alignment["score"], 1)

        return {
            "score": total,
            "details": {
                "decision_maker_access": decision_maker,
                "budget_authority": budget,
                "strategic_alignment": alignment,
            },
        }

    def _score_decision_maker_access(self, access: str) -> dict:
        """Decision-maker access scoring (2 pts max)."""
        mapping = {
            "c_suite": (2.0, "Direct C-suite/VP access"),
            "director": (1.5, "Senior director with budget influence"),
            "manager": (1.0, "Manager-level with path to decision maker"),
            "indirect": (0.5, "Indirect access — champion only"),
            "none": (0, "No decision-maker access"),
        }
        score, rationale = mapping.get(access.lower(), (0, f"Unknown: {access}"))
        return {"score": score, "max": 2.0, "rationale": rationale}

    def _score_budget_authority(self, authority: str) -> dict:
        """Budget authority scoring (1.5 pts max)."""
        mapping = {
            "dedicated": (1.5, "Dedicated budget for consulting/optimization"),
            "shared": (1.0, "Shared budget available"),
            "possible": (0.5, "Budget possible but needs approval"),
            "none": (0, "No budget"),
        }
        score, rationale = mapping.get(authority.lower(), (0, f"Unknown: {authority}"))
        return {"score": score, "max": 1.5, "rationale": rationale}

    def _score_strategic_alignment(self, alignment: str) -> dict:
        """Strategic alignment scoring (1 pt max)."""
        mapping = {
            "strong": (1.0, "Strong — growth conviction, data-driven, values methodology"),
            "partial": (0.5, "Partial — interested but skeptical"),
            "misaligned": (0, "Misaligned — looking for quick fixes"),
        }
        score, rationale = mapping.get(alignment.lower(), (0, f"Unknown: {alignment}"))
        return {"score": score, "max": 1.0, "rationale": rationale}

    # --- Exclusions ---

    def _check_exclusions(self, data: dict) -> dict:
        industry = (data.get("industry") or "").lower().strip()

        exclusions = self._config.get("excluded_industries", EXCLUDED_INDUSTRIES)

        for excluded in exclusions:
            exc = excluded.lower() if isinstance(excluded, str) else excluded
            if exc in industry or industry in exc:
                return {
                    "excluded": True,
                    "reason": f"Industry '{data.get('industry')}' is in exclusion list",
                }

        return {"excluded": False, "reason": None}

    # --- Actions ---

    def _get_recommended_action(self, tier: TierInfo, score: float) -> str:
        actions = {
            1: "Pursue aggressively — assign senior team, create custom proposal.",
            2: "Active pursuit — standard proposal with customization. Worth investing.",
            3: "Selective engagement — pursue only if inbound or strategic reason.",
            4: "Deprioritize — automated nurture only. Consider partner referral.",
        }
        return actions.get(tier.number, "Review manually.")

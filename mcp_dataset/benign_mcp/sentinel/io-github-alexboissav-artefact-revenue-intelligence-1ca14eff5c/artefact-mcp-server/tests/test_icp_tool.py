"""Tests for qualify_prospect tool and ICP scoring."""

import pytest

from artefact_mcp.core.icp_scorer import ICPScorer, TIERS
from artefact_mcp.tools.icp import qualify_prospect


class TestICPScorer:
    def setup_method(self):
        self.scorer = ICPScorer()

    def test_perfect_score(self):
        data = {
            "industry": "SaaS",
            "annual_revenue": 10_000_000,
            "employee_count": 80,
            "geography": "Quebec",
            "tech_stack": ["HubSpot", "Google Analytics", "Marketing Automation"],
            "growth_signals": ["hiring", "funding", "new product"],
            "content_engagement": "active",
            "purchase_history": "regular",
            "decision_maker_access": "c_suite",
            "budget_authority": "dedicated",
            "strategic_alignment": "strong",
        }
        result = self.scorer.score_company(data)
        assert result.total_score == 14.5
        assert result.tier["number"] == 1
        assert result.tier["label"] == "Ideal"

    def test_zero_score(self):
        data = {
            "industry": "Unknown",
            "annual_revenue": 100,
            "employee_count": 2,
            "geography": "Mars",
            "tech_stack": [],
            "growth_signals": [],
            "content_engagement": "none",
            "purchase_history": "never",
            "decision_maker_access": "none",
            "budget_authority": "none",
            "strategic_alignment": "misaligned",
        }
        result = self.scorer.score_company(data)
        assert result.total_score == 0
        assert result.tier["number"] == 4

    def test_tier_boundaries(self):
        # Tier 1 starts at 12.0
        tier = self.scorer.classify_tier(12.0)
        assert tier.number == 1

        # Tier 2: 9.0 - 11.9
        tier = self.scorer.classify_tier(9.0)
        assert tier.number == 2

        tier = self.scorer.classify_tier(11.9)
        assert tier.number == 2

        # Tier 3: 6.0 - 8.9
        tier = self.scorer.classify_tier(6.0)
        assert tier.number == 3

        # Tier 4: 0 - 5.9
        tier = self.scorer.classify_tier(5.9)
        assert tier.number == 4

    def test_exclusion_agency(self):
        data = {"industry": "Agency", "annual_revenue": 5_000_000}
        result = self.scorer.score_company(data)
        assert result.exclusion_check["excluded"] is True
        assert "EXCLUDED" in result.recommended_action.upper()

    def test_exclusion_consulting(self):
        data = {"industry": "Consulting firm"}
        result = self.scorer.score_company(data)
        assert result.exclusion_check["excluded"] is True

    def test_non_excluded_passes(self):
        data = {"industry": "SaaS", "annual_revenue": 10_000_000}
        result = self.scorer.score_company(data)
        assert result.exclusion_check["excluded"] is False

    def test_firmographic_breakdown(self):
        data = {
            "industry": "Technology",
            "annual_revenue": 5_000_000,
            "employee_count": 50,
            "geography": "Ontario",
        }
        result = self.scorer.score_company(data)
        firm = result.breakdown["firmographic"]
        assert firm["max"] == 5.0
        assert firm["details"]["industry"]["score"] == 2.0
        assert firm["details"]["revenue_range"]["score"] == 1.5
        assert firm["details"]["employee_count"]["score"] == 1.0
        assert firm["details"]["geography"]["score"] == 0.5

    def test_behavioral_with_hubspot(self):
        data = {
            "tech_stack": ["HubSpot", "Google Analytics", "Marketo"],
            "growth_signals": ["hiring", "funding"],
            "content_engagement": "active",
            "purchase_history": "regular",
        }
        result = self.scorer.score_company(data)
        beh = result.breakdown["behavioral"]
        assert beh["details"]["tech_stack"]["score"] == 2.0
        assert beh["details"]["growth_signals"]["score"] == 1.0
        assert beh["details"]["content_engagement"]["score"] == 1.0
        assert beh["details"]["purchase_frequency"]["score"] == 0.5

    def test_strategic_full(self):
        data = {
            "decision_maker_access": "c_suite",
            "budget_authority": "dedicated",
            "strategic_alignment": "strong",
        }
        result = self.scorer.score_company(data)
        strat = result.breakdown["strategic"]
        assert strat["score"] == 4.5
        assert strat["max"] == 4.5

    def test_geography_secondary_market(self):
        data = {"geography": "New York"}
        result = self.scorer.score_company(data)
        geo = result.breakdown["firmographic"]["details"]["geography"]
        assert geo["score"] == 0.25


class TestQualifyProspectTool:
    def test_manual_company_data(self):
        data = {
            "company_name": "Test Corp",
            "industry": "SaaS",
            "annual_revenue": 10_000_000,
            "employee_count": 80,
            "geography": "Quebec",
            "tech_stack": ["HubSpot"],
            "growth_signals": ["hiring"],
            "content_engagement": "occasional",
            "purchase_history": "occasional",
            "decision_maker_access": "director",
            "budget_authority": "shared",
            "strategic_alignment": "partial",
        }
        result = qualify_prospect(company_data=data)
        assert "total_score" in result
        assert "tier" in result
        assert "breakdown" in result
        assert result["company"]["name"] == "Test Corp"
        assert result["total_score"] > 0

    def test_no_input_raises(self):
        with pytest.raises(ValueError, match="Either company_id or company_data"):
            qualify_prospect()

    def test_company_id_without_client_raises(self):
        with pytest.raises(ValueError, match="HubSpot client required"):
            qualify_prospect(company_id="12345")

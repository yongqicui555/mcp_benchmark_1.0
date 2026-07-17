"""Tests for run_rfm_analysis tool."""

import pytest

from artefact_mcp.tools.rfm import run_rfm_analysis
from artefact_mcp.core.rfm_scorer import RFMScorer, B2BServiceScorer, _percentile
from artefact_mcp.core.segmenter import Segmenter, ICPAnalyzer


class TestPercentile:
    def test_basic(self):
        data = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        assert _percentile(data, 50) == pytest.approx(5.5, abs=0.1)
        assert _percentile(data, 0) == 1.0
        assert _percentile(data, 100) == 10.0

    def test_single_value(self):
        assert _percentile([42], 50) == 42.0

    def test_empty(self):
        assert _percentile([], 50) == 0.0

    def test_80th(self):
        data = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        result = _percentile(data, 80)
        assert 72 < result <= 82


class TestRFMScorer:
    def test_recency_very_recent(self):
        scorer = RFMScorer()
        assert scorer.score_recency(10) == 5

    def test_recency_dormant(self):
        scorer = RFMScorer()
        assert scorer.score_recency(400) == 1

    def test_frequency_high(self):
        scorer = RFMScorer()
        assert scorer.score_frequency(12) == 5

    def test_frequency_one(self):
        scorer = RFMScorer()
        assert scorer.score_frequency(1) == 1

    def test_monetary_percentile(self):
        scorer = RFMScorer()
        revenues = [10, 20, 30, 40, 50, 60, 70, 80, 90, 100]
        assert scorer.score_monetary(100, revenues) == 5
        assert scorer.score_monetary(10, revenues) == 1

    def test_b2b_service_longer_windows(self):
        scorer = B2BServiceScorer()
        # 45 days should be score 5 for B2B service (window is 60)
        assert scorer.score_recency(45) == 5
        # But only 4 for default scorer
        default = RFMScorer()
        assert default.score_recency(45) == 4


class TestSegmenter:
    def test_champion(self):
        s = Segmenter()
        assert s.classify(5, 5, 5) == "Champions"

    def test_lost(self):
        s = Segmenter()
        assert s.classify(1, 1, 1) == "Lost"

    def test_at_risk(self):
        s = Segmenter()
        assert s.classify(2, 3, 4) == "At Risk"

    def test_cant_lose(self):
        s = Segmenter()
        assert s.classify(1, 5, 5) == "Can't Lose Them"

    def test_new_customer(self):
        s = Segmenter()
        assert s.classify(5, 1, 3) == "New Customers"

    def test_all_segments_exist(self):
        s = Segmenter()
        assert len(s.get_all_segments()) == 11


class TestICPAnalyzer:
    def test_filter_top_performers(self):
        analyzer = ICPAnalyzer()
        clients = [
            {"segment": "Champions", "rfm_total": 15},
            {"segment": "Lost", "rfm_total": 3},
            {"segment": "Loyal Customers", "rfm_total": 12},
        ]
        top = analyzer.filter_top_performers(clients)
        assert len(top) == 2
        assert top[0]["segment"] == "Champions"

    def test_extract_patterns(self):
        analyzer = ICPAnalyzer()
        top = [
            {"industry": "SaaS", "employee_count": "51-200", "company_revenue": "$5M-$20M", "state_region": "Ontario"},
            {"industry": "SaaS", "employee_count": "51-200", "company_revenue": "$5M-$20M", "state_region": "Quebec"},
        ]
        all_clients = top + [
            {"industry": "Retail", "employee_count": "1-10", "company_revenue": "<$1M", "state_region": "Ontario"},
        ]
        patterns = analyzer.extract_patterns(top, all_clients)
        assert "industry" in patterns
        assert len(patterns["industry"]["distribution"]) > 0


class TestRFMTool:
    def test_sample_analysis(self):
        result = run_rfm_analysis(source="sample")
        assert result["total_clients"] == 12
        assert "segment_distribution" in result
        assert "icp_patterns" in result
        assert "summary" in result
        assert result["summary"]["total_revenue"] > 0

    def test_sample_with_preset(self):
        result = run_rfm_analysis(source="sample", industry_preset="saas")
        assert result["total_clients"] == 12
        assert result["industry_preset"] == "saas"

    def test_invalid_source(self):
        with pytest.raises(ValueError, match="Invalid source"):
            run_rfm_analysis(source="invalid")

    def test_hubspot_without_client(self):
        with pytest.raises(ValueError, match="HubSpot client required"):
            run_rfm_analysis(source="hubspot")

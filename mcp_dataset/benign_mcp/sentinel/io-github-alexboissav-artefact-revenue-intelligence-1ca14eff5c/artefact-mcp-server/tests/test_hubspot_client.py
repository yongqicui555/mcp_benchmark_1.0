"""Tests for HubSpot client with mocked HTTP responses."""

import pytest
import json

from artefact_mcp.core.hubspot_client import HubSpotClient


class TestHubSpotClientInit:
    def test_requires_api_key(self):
        with pytest.raises(ValueError, match="API key required"):
            HubSpotClient(api_key=None)

    def test_accepts_api_key(self):
        client = HubSpotClient(api_key="test-key-123")
        # api_key property returns masked value for safety
        assert client.api_key == "test...-123"
        client.close()

    def test_context_manager(self):
        with HubSpotClient(api_key="test-key-abc") as client:
            assert client.api_key == "test...-abc"


class TestHubSpotClientHelpers:
    def setup_method(self):
        self.client = HubSpotClient(api_key="test-key")

    def teardown_method(self):
        self.client.close()

    def test_safe_float(self):
        assert self.client._safe_float("123.45") == 123.45
        assert self.client._safe_float(None) == 0.0
        assert self.client._safe_float("not-a-number") == 0.0

    def test_safe_int(self):
        assert self.client._safe_int("42") == 42
        assert self.client._safe_int(None) is None
        assert self.client._safe_int("not-a-number") is None

    def test_parse_employee_band(self):
        assert self.client._parse_employee_band("5") == "1-10"
        assert self.client._parse_employee_band("25") == "11-50"
        assert self.client._parse_employee_band("100") == "51-200"
        assert self.client._parse_employee_band("300") == "201-500"
        assert self.client._parse_employee_band("800") == "501-1000"
        assert self.client._parse_employee_band("5000") == "1000+"
        assert self.client._parse_employee_band(None) is None

    def test_parse_revenue_band(self):
        assert self.client._parse_revenue_band("500000") == "<$1M"
        assert self.client._parse_revenue_band("3000000") == "$1M-$5M"
        assert self.client._parse_revenue_band("10000000") == "$5M-$20M"
        assert self.client._parse_revenue_band("50000000") == "$20M-$70M"
        assert self.client._parse_revenue_band("100000000") == "$70M+"
        assert self.client._parse_revenue_band(None) is None

    def test_parse_date(self):
        dt = self.client._parse_date("2026-01-15T10:00:00Z")
        assert dt is not None
        assert dt.year == 2026
        assert dt.month == 1

        assert self.client._parse_date(None) is None
        assert self.client._parse_date("invalid") is None

    def test_aggregate_by_company(self):
        deals = [
            {
                "id": "1",
                "name": "Deal 1",
                "amount": 10000,
                "close_date": None,
                "stage": "closedwon",
                "associations": {
                    "companies": {"results": [{"id": "C1"}]}
                },
            },
            {
                "id": "2",
                "name": "Deal 2",
                "amount": 20000,
                "close_date": None,
                "stage": "closedwon",
                "associations": {
                    "companies": {"results": [{"id": "C1"}]}
                },
            },
        ]
        companies = {
            "C1": {
                "id": "C1",
                "name": "Test Corp",
                "domain": "test.com",
                "industry": "SaaS",
                "employee_count": "51-200",
                "company_revenue": "$5M-$20M",
                "state_region": "Quebec",
            }
        }

        result = self.client._aggregate_by_company(deals, companies)
        assert len(result) == 1
        assert result[0]["client_name"] == "Test Corp"
        assert result[0]["total_revenue"] == 30000
        assert result[0]["transaction_count"] == 2

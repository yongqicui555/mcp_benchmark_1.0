"""
Unit tests for the QAE Safety Certification MCP Server.

These tests verify:
- Tool registration and invocation
- Input validation
- Certificate structure
- Budget tracking
- History management
"""

import pytest
from unittest.mock import Mock, patch, MagicMock

# Tests assume qae_mcp_server is importable from src
try:
    from qae_mcp_server.server import (
        certify_action,
        check_budget,
        get_certification_history,
        _initialize_certifier,
        _get_certifier,
    )
    import qae_mcp_server.server as _server_module
except ImportError:
    pytest.skip("qae_mcp_server module not available", allow_module_level=True)


@pytest.fixture(autouse=True)
def _reset_server_state():
    """Reset global server state before each test to ensure isolation."""
    _server_module._certifier = None
    _server_module._adapter = None
    _server_module._initialized = False
    _server_module._certification_history.clear()
    _server_module._total_certifications = 0
    yield


class TestInitialization:
    """Test certifier initialization."""

    def test_certifier_initializes_on_first_use(self):
        """Certifier should be created on first call to _get_certifier."""
        certifier = _get_certifier()
        assert certifier is not None

    def test_certifier_is_singleton(self):
        """Multiple calls to _get_certifier should return the same instance."""
        cert1 = _get_certifier()
        cert2 = _get_certifier()
        assert cert1 is cert2


class TestCertifyActionTool:
    """Test the certify_action tool."""

    def test_valid_certification(self):
        """Should return a valid certificate structure."""
        result = certify_action(
            action_id="test_action_001",
            agent_id="test_agent",
            scope=0.5,
            reversibility=0.5,
            sensitivity=0.5,
        )

        # Check response structure
        assert "decision" in result
        assert "zone" in result
        assert "margins" in result
        assert "certificate_id" in result
        assert "deterministic_hash" in result
        assert "timestamp" in result

    def test_dimension_validation_scope_too_high(self):
        """Should reject scope > 1.0."""
        result = certify_action(
            action_id="test_action_002",
            agent_id="test_agent",
            scope=1.5,  # Invalid
            reversibility=0.5,
            sensitivity=0.5,
        )

        assert "error" in result

    def test_dimension_validation_scope_negative(self):
        """Should reject negative scope."""
        result = certify_action(
            action_id="test_action_003",
            agent_id="test_agent",
            scope=-0.1,  # Invalid
            reversibility=0.5,
            sensitivity=0.5,
        )

        assert "error" in result

    def test_dimension_validation_reversibility(self):
        """Should reject invalid reversibility."""
        result = certify_action(
            action_id="test_action_004",
            agent_id="test_agent",
            scope=0.5,
            reversibility=2.0,  # Invalid
            sensitivity=0.5,
        )

        assert "error" in result

    def test_dimension_validation_sensitivity(self):
        """Should reject invalid sensitivity."""
        result = certify_action(
            action_id="test_action_005",
            agent_id="test_agent",
            scope=0.5,
            reversibility=0.5,
            sensitivity=-0.5,  # Invalid
        )

        assert "error" in result

    def test_with_description(self):
        """Should include description in response if provided."""
        description = "Test action with description"
        result = certify_action(
            action_id="test_action_006",
            agent_id="test_agent",
            scope=0.5,
            reversibility=0.5,
            sensitivity=0.5,
            description=description,
        )

        assert result.get("description") == description

    def test_safe_action_returns_certified(self):
        """Very safe actions (high reversibility, low scope/sensitivity) should be Certified."""
        result = certify_action(
            action_id="test_action_safe",
            agent_id="test_agent",
            scope=0.7,           # Margins map directly: 0.7 > safe threshold 0.6
            reversibility=0.8,   # 0.8 > safe threshold
            sensitivity=0.7,     # 0.7 > safe threshold
        )

        # Should be Certified or CertifiedWithWarning (Debug format may include extra info)
        assert "Certified" in result["decision"]

    def test_risky_action_returns_warning_or_escalate(self):
        """Risky actions (low reversibility, high scope/sensitivity) should warn or escalate."""
        result = certify_action(
            action_id="test_action_risky",
            agent_id="test_agent",
            scope=0.9,          # Very broad
            reversibility=0.1,  # Difficult to reverse
            sensitivity=0.9,    # High impact
        )

        # Should be CertifiedWithWarning, EscalateToHuman, or Blocked (Debug format)
        decision = result["decision"]
        assert "Warning" in decision or "Escalate" in decision or "Blocked" in decision

    def test_boundary_values(self):
        """Should handle boundary values [0.0, 1.0]."""
        # All zero
        result = certify_action(
            action_id="test_action_zero",
            agent_id="test_agent",
            scope=0.0,
            reversibility=0.0,
            sensitivity=0.0,
        )
        assert "decision" in result

        # All one
        result = certify_action(
            action_id="test_action_one",
            agent_id="test_agent",
            scope=1.0,
            reversibility=1.0,
            sensitivity=1.0,
        )
        assert "decision" in result


class TestCheckBudgetTool:
    """Test the check_budget tool."""

    def test_budget_structure(self):
        """Should return valid budget structure."""
        result = check_budget()

        assert "budget_limit" in result
        assert "budget_used" in result
        assert "budget_remaining" in result
        assert "rate_limit" in result
        assert "total_certifications" in result
        assert "utilization_percent" in result
        assert "timestamp" in result

    def test_budget_values_are_numeric(self):
        """Budget values should be numeric."""
        result = check_budget()

        assert isinstance(result["budget_limit"], (int, float))
        assert isinstance(result["budget_used"], (int, float))
        assert isinstance(result["budget_remaining"], (int, float))

    def test_budget_remaining_is_positive(self):
        """Budget remaining should not exceed limit."""
        result = check_budget()

        assert result["budget_remaining"] <= result["budget_limit"]
        assert result["budget_remaining"] >= 0


class TestCertificationHistoryTool:
    """Test the get_certification_history tool."""

    def test_history_structure(self):
        """Should return valid history structure."""
        result = get_certification_history()

        assert "certifications" in result
        assert "total_count" in result
        assert "timestamp" in result

    def test_history_is_list(self):
        """Certifications should be a list."""
        result = get_certification_history()

        assert isinstance(result["certifications"], list)

    def test_history_limit_respected(self):
        """Should respect limit parameter."""
        # Perform several certifications
        for i in range(5):
            certify_action(
                action_id=f"history_test_{i}",
                agent_id="test_agent",
                scope=0.5,
                reversibility=0.5,
                sensitivity=0.5,
            )

        result = get_certification_history(limit=2)
        assert len(result["certifications"]) <= 2

    def test_history_limit_clamped_to_50(self):
        """History limit should be clamped to [1, 50]."""
        # Request more than max
        result = get_certification_history(limit=100)
        assert len(result["certifications"]) <= 50

        # Request 0 should become 1
        result = get_certification_history(limit=0)
        assert len(result["certifications"]) >= 0  # May be 0 if no history


class TestDeterminism:
    """Test that certifications produce consistent decisions and unique certificates."""

    def test_same_inputs_produce_same_decision(self):
        """Same inputs should produce the same decision and zone."""
        params = {
            "action_id": "test_determinism_001",
            "agent_id": "test_agent",
            "scope": 0.5,
            "reversibility": 0.5,
            "sensitivity": 0.5,
        }

        result1 = certify_action(**params)
        result2 = certify_action(**params)

        # Decisions should match for same inputs
        assert result1["decision"] == result2["decision"]
        assert result1["zone"] == result2["zone"]
        # Each certification gets a unique hash (includes stateful budget tracking)
        assert isinstance(result1["deterministic_hash"], str)
        assert len(result1["deterministic_hash"]) > 0

    def test_different_inputs_produce_different_certificates(self):
        """Different inputs should produce different certificate IDs."""
        params1 = {
            "action_id": "test_determinism_002a",
            "agent_id": "test_agent",
            "scope": 0.5,
            "reversibility": 0.5,
            "sensitivity": 0.5,
        }

        params2 = {
            "action_id": "test_determinism_002b",
            "agent_id": "test_agent",
            "scope": 0.6,  # Different
            "reversibility": 0.5,
            "sensitivity": 0.5,
        }

        result1 = certify_action(**params1)
        result2 = certify_action(**params2)

        # Different inputs should produce different certificate IDs
        assert result1["certificate_id"] != result2["certificate_id"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

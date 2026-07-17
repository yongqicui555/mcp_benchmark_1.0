"""Tests for signal detection tool."""

import pytest

from artefact_mcp.tools.signals import detect_signals, SIGNAL_TYPES


class TestDetectSignals:
    def test_sample_signals(self):
        result = detect_signals(source="sample")
        assert "signals" in result
        assert "summary" in result
        assert result["deals_scanned"] == 8
        assert result["summary"]["total_signals"] >= 0

    def test_signal_structure(self):
        result = detect_signals(source="sample")
        for signal in result["signals"]:
            assert "signal_type" in signal
            assert "signal_name" in signal
            assert "signal_strength" in signal
            assert "evidence" in signal
            assert "recommended_action" in signal
            assert 0 <= signal["signal_strength"] <= 1.0
            assert signal["signal_type"] in SIGNAL_TYPES

    def test_signal_types_in_taxonomy(self):
        result = detect_signals(source="sample")
        assert "signal_taxonomy" in result
        assert len(result["signal_taxonomy"]) == 6
        for signal_type in SIGNAL_TYPES:
            assert signal_type in result["signal_taxonomy"]

    def test_signals_sorted_by_strength(self):
        result = detect_signals(source="sample")
        signals = result["signals"]
        if len(signals) > 1:
            for i in range(len(signals) - 1):
                assert signals[i]["signal_strength"] >= signals[i + 1]["signal_strength"]

    def test_summary_critical_signals(self):
        result = detect_signals(source="sample")
        summary = result["summary"]
        critical = summary.get("critical_signals", [])
        for sig in critical:
            assert sig["signal_strength"] >= 0.7

    def test_detects_velocity_anomaly(self):
        """Sample data includes stalled deals that should trigger velocity signals."""
        result = detect_signals(source="sample")
        velocity_signals = [
            s for s in result["signals"] if s["signal_type"] == "velocity_anomaly"
        ]
        # Sample data has deals open 100+ days — should detect anomalies
        assert len(velocity_signals) > 0

    def test_detects_pipeline_signals(self):
        """Sample data should trigger at least some pipeline signals."""
        result = detect_signals(source="sample")
        # Sample data should produce multiple signal types
        assert result["summary"]["total_signals"] >= 2
        detected_types = result["summary"]["signal_types_detected"]
        assert len(detected_types) >= 1

    def test_invalid_source(self):
        with pytest.raises(ValueError, match="Invalid source"):
            detect_signals(source="invalid")

    def test_hubspot_without_client(self):
        with pytest.raises(ValueError, match="HubSpot client required"):
            detect_signals(source="hubspot")

    def test_scan_date_present(self):
        result = detect_signals(source="sample")
        assert "scan_date" in result
        assert len(result["scan_date"]) == 10  # YYYY-MM-DD

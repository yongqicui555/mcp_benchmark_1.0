"""Tests for technical indicators."""

import pytest

from stocksense.data.technicals import _ema, _rsi, _sma, compute_technicals


class TestSMA:
    def test_basic(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0]
        result = _sma(values, 3)
        assert result[0] is None
        assert result[1] is None
        assert result[2] == 2.0
        assert result[3] == 3.0
        assert result[4] == 4.0

    def test_window_equals_length(self):
        values = [10.0, 20.0, 30.0]
        result = _sma(values, 3)
        assert result[-1] == 20.0


class TestEMA:
    def test_basic(self):
        values = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0]
        result = _ema(values, 3)
        assert result[0] is None
        assert result[1] is None
        assert result[2] is not None
        assert all(r is not None for r in result[2:])

    def test_too_few_values(self):
        values = [1.0, 2.0]
        result = _ema(values, 5)
        assert all(r is None for r in result)


class TestRSI:
    def test_basic(self):
        # Create a simple uptrend
        values = [float(i) for i in range(30)]
        result = _rsi(values, 14)
        assert result[-1] is not None
        # Pure uptrend should have high RSI
        assert result[-1] > 90

    def test_bounds(self):
        values = list(range(50))
        result = _rsi([float(v) for v in values], 14)
        for r in result:
            if r is not None:
                assert 0 <= r <= 100


class TestComputeTechnicals:
    def test_returns_valid_data(self):
        result = compute_technicals("AAPL")
        assert result["ticker"] == "AAPL"
        assert "indicators" in result
        assert "signals" in result
        assert "performance" in result

    def test_indicators_structure(self):
        result = compute_technicals("MSFT")
        ind = result["indicators"]
        assert "sma_20" in ind
        assert "sma_50" in ind
        assert "rsi_14" in ind
        assert "macd" in ind

    def test_signals_structure(self):
        result = compute_technicals("AAPL")
        sig = result["signals"]
        assert sig["rsi_signal"] in ("overbought", "oversold", "neutral")

    def test_performance_structure(self):
        result = compute_technicals("AAPL")
        perf = result["performance"]
        assert "1_week" in perf
        assert "1_month" in perf
        assert "ytd" in perf

    def test_invalid_ticker(self):
        with pytest.raises((ValueError, RuntimeError)):
            compute_technicals("INVALIDTICKER999XYZ")

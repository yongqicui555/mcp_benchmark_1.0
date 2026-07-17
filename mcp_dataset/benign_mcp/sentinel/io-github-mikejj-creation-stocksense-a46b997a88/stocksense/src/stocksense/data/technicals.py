"""Technical indicator calculations from price data."""

from stocksense.data.market import fetch_price_history


def _get_closes(ticker: str, period: str = "1y") -> list[float]:
    """Get closing prices for a ticker."""
    records = fetch_price_history(ticker, period=period, interval="1d")
    return [r["close"] for r in records]


def _sma(values: list[float], window: int) -> list[float | None]:
    """Simple Moving Average."""
    result = []
    for i in range(len(values)):
        if i < window - 1:
            result.append(None)
        else:
            result.append(round(sum(values[i - window + 1 : i + 1]) / window, 2))
    return result


def _ema(values: list[float], window: int) -> list[float | None]:
    """Exponential Moving Average."""
    if len(values) < window:
        return [None] * len(values)

    multiplier = 2 / (window + 1)
    result: list[float | None] = [None] * (window - 1)
    # Start with SMA for first EMA value
    ema_val = sum(values[:window]) / window
    result.append(round(ema_val, 2))

    for i in range(window, len(values)):
        ema_val = (values[i] - ema_val) * multiplier + ema_val
        result.append(round(ema_val, 2))
    return result


def _rsi(values: list[float], window: int = 14) -> list[float | None]:
    """Relative Strength Index."""
    if len(values) < window + 1:
        return [None] * len(values)

    result: list[float | None] = [None] * window
    gains = []
    losses = []

    for i in range(1, window + 1):
        change = values[i] - values[i - 1]
        gains.append(max(change, 0))
        losses.append(max(-change, 0))

    avg_gain = sum(gains) / window
    avg_loss = sum(losses) / window

    if avg_loss == 0:
        result.append(100.0)
    else:
        rs = avg_gain / avg_loss
        result.append(round(100 - (100 / (1 + rs)), 1))

    for i in range(window + 1, len(values)):
        change = values[i] - values[i - 1]
        gain = max(change, 0)
        loss = max(-change, 0)
        avg_gain = (avg_gain * (window - 1) + gain) / window
        avg_loss = (avg_loss * (window - 1) + loss) / window

        if avg_loss == 0:
            result.append(100.0)
        else:
            rs = avg_gain / avg_loss
            result.append(round(100 - (100 / (1 + rs)), 1))

    return result


def compute_technicals(ticker: str) -> dict:
    """Compute key technical indicators for a ticker.

    Returns current values of SMA(20), SMA(50), SMA(200), EMA(12), EMA(26),
    RSI(14), and MACD.
    """
    closes = _get_closes(ticker, period="1y")
    if len(closes) < 26:
        raise ValueError(f"Not enough price data for {ticker} to compute indicators")

    current_price = closes[-1]

    # Moving averages
    sma_20 = _sma(closes, 20)
    sma_50 = _sma(closes, 50)
    sma_200 = _sma(closes, 200)
    ema_12 = _ema(closes, 12)
    ema_26 = _ema(closes, 26)

    # RSI
    rsi_values = _rsi(closes, 14)

    # MACD
    macd_line = None
    signal_line = None
    if ema_12[-1] is not None and ema_26[-1] is not None:
        macd_values = []
        for e12, e26 in zip(ema_12, ema_26):
            if e12 is not None and e26 is not None:
                macd_values.append(e12 - e26)
        if macd_values:
            macd_line = round(macd_values[-1], 2)
            # Signal line = 9-period EMA of MACD
            if len(macd_values) >= 9:
                signal = _ema(macd_values, 9)
                signal_line = signal[-1]

    # Performance stats
    if len(closes) >= 5:
        pct_1w = round((current_price / closes[-5] - 1) * 100, 2)
    else:
        pct_1w = None

    if len(closes) >= 21:
        pct_1m = round((current_price / closes[-21] - 1) * 100, 2)
    else:
        pct_1m = None

    if len(closes) >= 63:
        pct_3m = round((current_price / closes[-63] - 1) * 100, 2)
    else:
        pct_3m = None

    if len(closes) >= 126:
        pct_6m = round((current_price / closes[-126] - 1) * 100, 2)
    else:
        pct_6m = None

    pct_ytd = round((current_price / closes[0] - 1) * 100, 2) if closes else None

    return {
        "ticker": ticker.upper(),
        "price": current_price,
        "indicators": {
            "sma_20": sma_20[-1],
            "sma_50": sma_50[-1],
            "sma_200": sma_200[-1] if len(closes) >= 200 else None,
            "ema_12": ema_12[-1],
            "ema_26": ema_26[-1],
            "rsi_14": rsi_values[-1],
            "macd": macd_line,
            "macd_signal": signal_line,
            "macd_histogram": round(macd_line - signal_line, 2)
            if macd_line is not None and signal_line is not None
            else None,
        },
        "signals": {
            "above_sma_20": current_price > sma_20[-1] if sma_20[-1] else None,
            "above_sma_50": current_price > sma_50[-1] if sma_50[-1] else None,
            "above_sma_200": current_price > sma_200[-1]
            if sma_200[-1] is not None
            else None,
            "rsi_signal": "overbought"
            if rsi_values[-1] and rsi_values[-1] > 70
            else "oversold"
            if rsi_values[-1] and rsi_values[-1] < 30
            else "neutral",
            "macd_signal_crossover": "bullish"
            if macd_line is not None
            and signal_line is not None
            and macd_line > signal_line
            else "bearish"
            if macd_line is not None and signal_line is not None
            else None,
        },
        "performance": {
            "1_week": pct_1w,
            "1_month": pct_1m,
            "3_months": pct_3m,
            "6_months": pct_6m,
            "ytd": pct_ytd,
        },
    }

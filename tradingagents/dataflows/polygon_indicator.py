# TradingAgents/dataflows/polygon_indicator.py
"""
Polygon.io Technical Indicators Module

Supports: SMA, EMA, RSI, MACD (natively via Polygon API).
Unsupported indicators (Bollinger, ATR, VWMA, MFI) raise ValueError
to trigger automatic fallback to yfinance/stockstats.
"""

from datetime import datetime
from dateutil.relativedelta import relativedelta

from .polygon_common import (
    get_client,
    enforce_rate_limit,
    read_cache,
    write_cache,
    _get_cache_key,
)


# Indicator descriptions (shared with alpha_vantage_indicator.py)
INDICATOR_DESCRIPTIONS = {
    "close_50_sma": "50 SMA: A medium-term trend indicator. Usage: Identify trend direction and serve as dynamic support/resistance. Tips: It lags price; combine with faster indicators for timely signals.",
    "close_200_sma": "200 SMA: A long-term trend benchmark. Usage: Confirm overall market trend and identify golden/death cross setups. Tips: It reacts slowly; best for strategic trend confirmation rather than frequent trading entries.",
    "close_10_ema": "10 EMA: A responsive short-term average. Usage: Capture quick shifts in momentum and potential entry points. Tips: Prone to noise in choppy markets; use alongside longer averages for filtering false signals.",
    "macd": "MACD: Computes momentum via differences of EMAs. Usage: Look for crossovers and divergence as signals of trend changes. Tips: Confirm with other indicators in low-volatility or sideways markets.",
    "macds": "MACD Signal: An EMA smoothing of the MACD line. Usage: Use crossovers with the MACD line to trigger trades. Tips: Should be part of a broader strategy to avoid false positives.",
    "macdh": "MACD Histogram: Shows the gap between the MACD line and its signal. Usage: Visualize momentum strength and spot divergence early. Tips: Can be volatile; complement with additional filters in fast-moving markets.",
    "rsi": "RSI: Measures momentum to flag overbought/oversold conditions. Usage: Apply 70/30 thresholds and watch for divergence to signal reversals. Tips: In strong trends, RSI may remain extreme; always cross-check with trend analysis.",
}

# Indicators supported by Polygon (maps internal name -> API params)
SUPPORTED_INDICATORS = {
    "close_50_sma", "close_200_sma", "close_10_ema",
    "macd", "macds", "macdh", "rsi",
}

# Indicators NOT supported by Polygon (fallback to yfinance/stockstats)
UNSUPPORTED_INDICATORS = {"boll", "boll_ub", "boll_lb", "atr", "vwma", "mfi"}


def get_indicator(
    symbol: str,
    indicator: str,
    curr_date: str,
    look_back_days: int,
    interval: str = "daily",
    time_period: int = 14,
    series_type: str = "close",
) -> str:
    """Returns technical indicator values from Polygon.io.

    Matches the return format of alpha_vantage_indicator.get_indicator.

    Args:
        symbol: Ticker symbol
        indicator: Internal indicator name (e.g., "close_50_sma", "rsi")
        curr_date: Current trading date in YYYY-mm-dd format
        look_back_days: Number of days to look back
        interval: Not used by Polygon (kept for signature compatibility)
        time_period: Not used by Polygon (kept for signature compatibility)
        series_type: Not used by Polygon (kept for signature compatibility)

    Returns:
        Formatted markdown string with indicator values and description.

    Raises:
        ValueError: For unsupported indicators (triggers vendor fallback).
    """
    if indicator in UNSUPPORTED_INDICATORS:
        raise ValueError(
            f"Indicator '{indicator}' is not available from Polygon.io. "
            f"Supported: {sorted(SUPPORTED_INDICATORS)}"
        )

    if indicator not in SUPPORTED_INDICATORS:
        raise ValueError(
            f"Unknown indicator '{indicator}'. "
            f"Supported: {sorted(SUPPORTED_INDICATORS)}"
        )

    cache_key = _get_cache_key(
        "indicator", f"{symbol}_{indicator}_{curr_date}_{look_back_days}"
    )
    cached = read_cache(cache_key)
    if cached:
        print(f"CACHE HIT: Polygon {indicator} for {symbol}")
        return cached

    curr_date_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    before = curr_date_dt - relativedelta(days=look_back_days)
    before_str = before.strftime("%Y-%m-%d")

    enforce_rate_limit()
    client = get_client()

    try:
        if indicator in ("macd", "macds", "macdh"):
            result_str = _fetch_macd(client, symbol, indicator, before_str, curr_date)
        elif indicator in ("close_50_sma", "close_200_sma"):
            window = 50 if indicator == "close_50_sma" else 200
            result_str = _fetch_sma(client, symbol, window, before_str, curr_date)
        elif indicator == "close_10_ema":
            result_str = _fetch_ema(client, symbol, 10, before_str, curr_date)
        elif indicator == "rsi":
            result_str = _fetch_rsi(client, symbol, before_str, curr_date)
        else:
            return f"Error: Indicator {indicator} not implemented for Polygon."
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate" in error_msg.lower():
            from .polygon_common import PolygonRateLimitError
            raise PolygonRateLimitError(f"Polygon rate limit exceeded: {e}")
        raise

    # Format output matching Alpha Vantage indicator style
    description = INDICATOR_DESCRIPTIONS.get(indicator, "No description available.")
    output = (
        f"## {indicator.upper()} values from {before_str} to {curr_date}:\n\n"
        + result_str
        + "\n\n"
        + description
    )

    write_cache(cache_key, output)
    return output


def _fetch_sma(client, symbol: str, window: int, from_date: str, to_date: str) -> str:
    """Fetch SMA values from Polygon."""
    results = client.get_sma(
        ticker=symbol.upper(),
        timestamp_gte=from_date,
        timestamp_lte=to_date,
        timespan="day",
        window=window,
        series_type="close",
        adjusted=True,
        order="asc",
        limit=5000,
    )

    if not results or not results.values:
        return "No data available for the specified date range.\n"

    lines = []
    for val in results.values:
        ts = datetime.fromtimestamp(val.timestamp / 1000).strftime("%Y-%m-%d")
        lines.append(f"{ts}: {val.value:.4f}")

    print(f"FETCHED: Polygon SMA({window}) for {symbol} ({len(lines)} values)")
    return "\n".join(lines) + "\n"


def _fetch_ema(client, symbol: str, window: int, from_date: str, to_date: str) -> str:
    """Fetch EMA values from Polygon."""
    results = client.get_ema(
        ticker=symbol.upper(),
        timestamp_gte=from_date,
        timestamp_lte=to_date,
        timespan="day",
        window=window,
        series_type="close",
        adjusted=True,
        order="asc",
        limit=5000,
    )

    if not results or not results.values:
        return "No data available for the specified date range.\n"

    lines = []
    for val in results.values:
        ts = datetime.fromtimestamp(val.timestamp / 1000).strftime("%Y-%m-%d")
        lines.append(f"{ts}: {val.value:.4f}")

    print(f"FETCHED: Polygon EMA({window}) for {symbol} ({len(lines)} values)")
    return "\n".join(lines) + "\n"


def _fetch_rsi(client, symbol: str, from_date: str, to_date: str) -> str:
    """Fetch RSI values from Polygon."""
    results = client.get_rsi(
        ticker=symbol.upper(),
        timestamp_gte=from_date,
        timestamp_lte=to_date,
        timespan="day",
        window=14,
        series_type="close",
        adjusted=True,
        order="asc",
        limit=5000,
    )

    if not results or not results.values:
        return "No data available for the specified date range.\n"

    lines = []
    for val in results.values:
        ts = datetime.fromtimestamp(val.timestamp / 1000).strftime("%Y-%m-%d")
        lines.append(f"{ts}: {val.value:.4f}")

    print(f"FETCHED: Polygon RSI for {symbol} ({len(lines)} values)")
    return "\n".join(lines) + "\n"


def _fetch_macd(
    client, symbol: str, indicator: str, from_date: str, to_date: str
) -> str:
    """Fetch MACD values from Polygon.

    Args:
        indicator: One of "macd" (MACD line), "macds" (signal), "macdh" (histogram)
    """
    results = client.get_macd(
        ticker=symbol.upper(),
        timestamp_gte=from_date,
        timestamp_lte=to_date,
        timespan="day",
        short_window=12,
        long_window=26,
        signal_window=9,
        series_type="close",
        adjusted=True,
        order="asc",
        limit=5000,
    )

    if not results or not results.values:
        return "No data available for the specified date range.\n"

    lines = []
    for val in results.values:
        ts = datetime.fromtimestamp(val.timestamp / 1000).strftime("%Y-%m-%d")
        # MACDIndicatorValue has: value (MACD line), signal, histogram
        if indicator == "macd":
            lines.append(f"{ts}: {val.value:.4f}")
        elif indicator == "macds":
            lines.append(f"{ts}: {val.signal:.4f}")
        elif indicator == "macdh":
            lines.append(f"{ts}: {val.histogram:.4f}")

    label = {"macd": "MACD", "macds": "MACD Signal", "macdh": "MACD Histogram"}
    print(f"FETCHED: Polygon {label.get(indicator, indicator)} for {symbol} ({len(lines)} values)")
    return "\n".join(lines) + "\n"

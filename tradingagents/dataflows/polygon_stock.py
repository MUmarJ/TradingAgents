# TradingAgents/dataflows/polygon_stock.py
"""
Polygon.io Stock Data Module

Fetches daily OHLCV aggregate bars from Polygon.io.
Returns CSV format matching Alpha Vantage output for compatibility.
"""

import io
import csv
from datetime import datetime

from .polygon_common import (
    get_client,
    enforce_rate_limit,
    read_cache,
    write_cache,
    _get_cache_key,
)


def get_stock(symbol: str, start_date: str, end_date: str) -> str:
    """Returns daily OHLCV data from Polygon.io as CSV string.

    Matches the return format of alpha_vantage_stock.get_stock.

    Args:
        symbol: Ticker symbol (e.g., AAPL, MSFT)
        start_date: Start date in yyyy-mm-dd format
        end_date: End date in yyyy-mm-dd format

    Returns:
        CSV string with columns: timestamp, open, high, low, close,
        adjusted_close, volume, dividend_amount, split_coefficient
    """
    cache_key = _get_cache_key("stock", f"{symbol}_{start_date}_{end_date}")
    cached = read_cache(cache_key)
    if cached:
        print(f"CACHE HIT: Polygon stock data for {symbol}")
        return cached

    enforce_rate_limit()
    client = get_client()

    try:
        aggs = list(client.list_aggs(
            ticker=symbol.upper(),
            multiplier=1,
            timespan="day",
            from_=start_date,
            to=end_date,
            adjusted=True,
            sort="asc",
            limit=50000,
        ))
    except Exception as e:
        error_msg = str(e)
        if "403" in error_msg or "forbidden" in error_msg.lower():
            raise PermissionError(f"Polygon API access denied for {symbol}: {e}")
        if "429" in error_msg or "rate" in error_msg.lower():
            from .polygon_common import PolygonRateLimitError
            raise PolygonRateLimitError(f"Polygon rate limit exceeded: {e}")
        raise

    if not aggs:
        return f"No data found for symbol '{symbol}' between {start_date} and {end_date}"

    # Build CSV matching Alpha Vantage format
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "timestamp", "open", "high", "low", "close",
        "adjusted_close", "volume", "dividend_amount", "split_coefficient",
    ])

    for agg in aggs:
        ts = datetime.fromtimestamp(agg.timestamp / 1000).strftime("%Y-%m-%d")
        # Polygon returns adjusted data when adjusted=True,
        # so close IS the adjusted close
        writer.writerow([
            ts, agg.open, agg.high, agg.low, agg.close,
            agg.close, agg.volume, 0, 1,
        ])

    result = output.getvalue()
    print(f"FETCHED: Polygon OHLCV for {symbol} ({len(aggs)} bars)")
    write_cache(cache_key, result)
    return result

"""
StockGeist Sentiment Data Module

Fetches social media sentiment data from StockGeist's REST API.
StockGeist uses NLP/deep learning to analyze sentiment across social media
and news for 2,200+ US stocks.

API docs: https://api.stockgeist.ai/v2/docs
Python client: https://github.com/stockgeist/stockgeist-client-python

Free tier: 10,000 credits/month.
"""

import os
import json
import hashlib
import requests
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from .config import get_config

# Cache settings
CACHE_EXPIRY_HOURS = 24

STOCKGEIST_BASE_URL = "https://api.stockgeist.ai/"

# Metrics to fetch from message-metrics endpoint
MESSAGE_METRICS_FILTER = [
    "total_count",
    "pos_index",
    "inf_positive_count",
    "inf_negative_count",
    "inf_neutral_count",
    "em_positive_count",
    "em_negative_count",
    "em_neutral_count",
]


def _get_cache_dir() -> str:
    config = get_config()
    cache_dir = os.path.join(config.get("data_cache_dir", "./data_cache"), "stockgeist")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _get_cache_key(endpoint: str, ticker: str, date: str, extra: str = "") -> str:
    key_str = f"stockgeist_{endpoint}_{ticker}_{date}_{extra}"
    return hashlib.md5(key_str.encode()).hexdigest()


def _read_cache(cache_key: str) -> Optional[Dict]:
    cache_dir = _get_cache_dir()
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, "r") as f:
            cached = json.load(f)

        cached_time = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_time > timedelta(hours=CACHE_EXPIRY_HOURS):
            return None

        return cached.get("data")
    except (json.JSONDecodeError, KeyError):
        return None


def _write_cache(cache_key: str, data: Dict) -> None:
    cache_dir = _get_cache_dir()
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    cached = {
        "cached_at": datetime.now().isoformat(),
        "data": data
    }

    with open(cache_file, "w") as f:
        json.dump(cached, f, indent=2, default=str)


def _make_request(endpoint: str, params: Dict) -> Dict:
    """Make authenticated request to StockGeist API."""
    token = os.getenv("STOCKGEIST_API_KEY")
    if not token:
        raise RuntimeError("STOCKGEIST_API_KEY not set")

    params["token"] = token
    url = f"{STOCKGEIST_BASE_URL}{endpoint}"

    response = requests.get(url, params=params, timeout=15)

    if response.status_code == 401:
        raise RuntimeError("StockGeist API: Invalid or expired token")
    if response.status_code == 402:
        raise RuntimeError("StockGeist API: Insufficient credits")
    if response.status_code == 429:
        raise RuntimeError("StockGeist API: Rate limit exceeded")

    response.raise_for_status()
    return response.json()


def get_message_metrics(
    ticker: str,
    start_date: str,
    end_date: str,
    timeframe: str = "1d",
) -> Dict[str, Any]:
    """
    Get social media message metrics from StockGeist.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        timeframe: Data resolution - "5m", "1h", or "1d"

    Returns:
        Dict with message metrics data
    """
    cache_key = _get_cache_key("message_metrics", ticker, f"{start_date}_{end_date}", timeframe)
    cached = _read_cache(cache_key)
    if cached:
        print(f"CACHE HIT: StockGeist message metrics for {ticker}")
        return cached

    print(f"FETCHING: StockGeist message metrics for {ticker} ({start_date} to {end_date})")

    try:
        params = {
            "symbol": ticker,
            "timeframe": timeframe,
            "start": f"{start_date}T00:00:00",
            "end": f"{end_date}T23:59:59",
            "filter": ",".join(MESSAGE_METRICS_FILTER),
        }

        data = _make_request("time-series/message-metrics", params)

        body = data.get("body", {})
        metadata = data.get("metadata", {})

        result = {
            "source": "stockgeist",
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "timeframe": timeframe,
            "credits_used": metadata.get("credits", 0),
            "data": body,
            "fetched_at": datetime.now().isoformat(),
        }

        _write_cache(cache_key, result)
        return result

    except Exception as e:
        print(f"ERROR: StockGeist message metrics failed: {e}")
        return {
            "source": "stockgeist",
            "ticker": ticker,
            "error": str(e),
            "data": None,
        }


def get_article_metrics(
    ticker: str,
    start_date: str,
    end_date: str,
    timeframe: str = "1d",
) -> Dict[str, Any]:
    """
    Get news article sentiment metrics from StockGeist.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        timeframe: Data resolution - "5m", "1h", or "1d"

    Returns:
        Dict with article metrics data (titles, sentiments, mentions)
    """
    cache_key = _get_cache_key("article_metrics", ticker, f"{start_date}_{end_date}", timeframe)
    cached = _read_cache(cache_key)
    if cached:
        print(f"CACHE HIT: StockGeist article metrics for {ticker}")
        return cached

    print(f"FETCHING: StockGeist article metrics for {ticker} ({start_date} to {end_date})")

    try:
        params = {
            "symbol": ticker,
            "timeframe": timeframe,
            "start": f"{start_date}T00:00:00",
            "end": f"{end_date}T23:59:59",
            "filter": "titles,title_sentiments,mentions",
        }

        data = _make_request("time-series/article-metrics", params)

        body = data.get("body", {})
        metadata = data.get("metadata", {})

        result = {
            "source": "stockgeist",
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "timeframe": timeframe,
            "credits_used": metadata.get("credits", 0),
            "data": body,
            "fetched_at": datetime.now().isoformat(),
        }

        _write_cache(cache_key, result)
        return result

    except Exception as e:
        print(f"ERROR: StockGeist article metrics failed: {e}")
        return {
            "source": "stockgeist",
            "ticker": ticker,
            "error": str(e),
            "data": None,
        }


def _format_report(ticker: str, msg_data: Dict, article_data: Dict = None) -> str:
    """Format StockGeist data as a report string."""
    report = f"# StockGeist Sentiment Report for {ticker}\n\n"

    if msg_data.get("error"):
        report += f"*Error: {msg_data['error']}*\n"
        return report

    body = msg_data.get("data", {})
    timestamps = body.get("timestamp", [])
    total_counts = body.get("total_count", [])
    pos_index = body.get("pos_index", [])
    inf_pos = body.get("inf_positive_count", [])
    inf_neg = body.get("inf_negative_count", [])
    inf_neu = body.get("inf_neutral_count", [])

    if not timestamps:
        report += "*No message data available for the specified period*\n"
        return report

    report += f"**Period:** {msg_data.get('start_date')} to {msg_data.get('end_date')}\n"
    report += f"**Data points:** {len(timestamps)} ({msg_data.get('timeframe', '1d')} resolution)\n\n"

    # Aggregate stats
    total_messages = sum(c for c in total_counts if c is not None)
    total_positive = sum(c for c in inf_pos if c is not None)
    total_negative = sum(c for c in inf_neg if c is not None)
    total_neutral = sum(c for c in inf_neu if c is not None)
    valid_pos_index = [p for p in pos_index if p is not None]
    avg_pos_index = sum(valid_pos_index) / len(valid_pos_index) if valid_pos_index else 0

    report += "## Sentiment Summary\n"
    report += f"- **Total social media messages:** {int(total_messages)}\n"
    report += f"- **Positive:** {int(total_positive)}"
    if total_messages > 0:
        report += f" ({total_positive / total_messages:.1%})"
    report += "\n"
    report += f"- **Negative:** {int(total_negative)}"
    if total_messages > 0:
        report += f" ({total_negative / total_messages:.1%})"
    report += "\n"
    report += f"- **Neutral:** {int(total_neutral)}"
    if total_messages > 0:
        report += f" ({total_neutral / total_messages:.1%})"
    report += "\n"
    report += f"- **Average Positivity Index:** {avg_pos_index:.2f}\n\n"

    # Determine overall sentiment
    if total_positive > total_negative:
        ratio = total_positive / (total_positive + total_negative) if (total_positive + total_negative) > 0 else 0.5
        if ratio > 0.7:
            overall = "Strongly Bullish"
        elif ratio > 0.55:
            overall = "Bullish"
        else:
            overall = "Slightly Bullish"
    elif total_negative > total_positive:
        ratio = total_negative / (total_positive + total_negative) if (total_positive + total_negative) > 0 else 0.5
        if ratio > 0.7:
            overall = "Strongly Bearish"
        elif ratio > 0.55:
            overall = "Bearish"
        else:
            overall = "Slightly Bearish"
    else:
        overall = "Neutral"

    report += f"**Overall Sentiment:** {overall}\n\n"

    # Daily breakdown (last 7 data points max)
    report += "## Daily Breakdown\n\n"
    report += "| Date | Messages | Positive | Negative | Pos Index |\n"
    report += "|------|----------|----------|----------|----------|\n"

    show_points = min(len(timestamps), 7)
    for i in range(-show_points, 0):
        ts = timestamps[i][:10] if isinstance(timestamps[i], str) else str(timestamps[i])[:10]
        tc = int(total_counts[i]) if total_counts[i] is not None else 0
        ip = int(inf_pos[i]) if i < len(inf_pos) and inf_pos[i] is not None else 0
        in_ = int(inf_neg[i]) if i < len(inf_neg) and inf_neg[i] is not None else 0
        pi = f"{pos_index[i]:.2f}" if i < len(pos_index) and pos_index[i] is not None else "N/A"
        report += f"| {ts} | {tc} | {ip} | {in_} | {pi} |\n"

    report += "\n"

    # Article metrics if available
    if article_data and not article_data.get("error") and article_data.get("data"):
        art_body = article_data["data"]
        art_timestamps = art_body.get("timestamp", [])
        art_titles = art_body.get("titles", [])
        art_sentiments = art_body.get("title_sentiments", [])

        if art_timestamps and art_titles:
            report += "## Recent News Articles (via StockGeist)\n\n"
            # Show most recent articles
            for i in range(-min(len(art_timestamps), 5), 0):
                if i < len(art_titles) and art_titles[i]:
                    titles_list = art_titles[i] if isinstance(art_titles[i], list) else [art_titles[i]]
                    sentiments_list = art_sentiments[i] if i < len(art_sentiments) and art_sentiments[i] else {}

                    for title in titles_list[:3]:
                        report += f"- {title}\n"

                    if sentiments_list and isinstance(sentiments_list, dict):
                        pos_arts = sentiments_list.get("positive", 0)
                        neg_arts = sentiments_list.get("negative", 0)
                        neu_arts = sentiments_list.get("neutral", 0)
                        report += f"  Sentiment: +{pos_arts} / -{neg_arts} / ~{neu_arts}\n"

            report += "\n"

    return report


def get_social_sentiment_stockgeist(
    ticker: str,
    start_date: str,
    end_date: str,
    limit: int = 50,
) -> str:
    """
    Get social sentiment from StockGeist.

    This is the vendor wrapper called by route_to_vendor.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Not used (kept for API compatibility)

    Returns:
        Formatted string with StockGeist sentiment analysis

    Raises:
        RuntimeError: If StockGeist API fails (triggers fallback to other vendors)
    """
    msg_data = get_message_metrics(ticker, start_date, end_date)

    if msg_data.get("error"):
        raise RuntimeError(f"StockGeist error: {msg_data['error']}")

    # Also try article metrics (non-fatal if fails)
    article_data = None
    try:
        article_data = get_article_metrics(ticker, start_date, end_date)
    except Exception:
        pass

    return _format_report(ticker, msg_data, article_data)

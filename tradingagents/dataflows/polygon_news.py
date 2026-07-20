# TradingAgents/dataflows/polygon_news.py
"""
Polygon.io News Data Module

Fetches ticker news and global news from Polygon.io.
Returns dict format matching Alpha Vantage news output for compatibility.
"""

from datetime import datetime, timedelta

from .polygon_common import (
    get_client,
    enforce_rate_limit,
    read_cache,
    write_cache,
    _get_cache_key,
)


def _extract_sentiment(news_item) -> str:
    """Extract sentiment label from Polygon TickerNews insights.

    Polygon insights contain per-ticker sentiment analysis.
    We aggregate to a single label.
    """
    insights = getattr(news_item, "insights", None)
    if not insights:
        return "Neutral"

    positive = 0
    negative = 0

    for insight in insights:
        sentiment = getattr(insight, "sentiment", "")
        sentiment_str = str(sentiment).lower()
        if "positive" in sentiment_str or "bullish" in sentiment_str:
            positive += 1
        elif "negative" in sentiment_str or "bearish" in sentiment_str:
            negative += 1

    if positive > negative:
        return "Bullish"
    elif negative > positive:
        return "Bearish"
    return "Neutral"


def get_news(ticker: str, start_date: str, end_date: str, limit: int = 50) -> dict:
    """Returns ticker news from Polygon.io.

    Matches the return format of alpha_vantage_news.get_news.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date in yyyy-mm-dd format (or datetime)
        end_date: End date in yyyy-mm-dd format (or datetime)
        limit: Maximum number of articles to return (default 50)

    Returns:
        Dictionary with "feed" key containing list of article dicts.
    """
    # Normalize date inputs
    if isinstance(start_date, datetime):
        start_date = start_date.strftime("%Y-%m-%d")
    if isinstance(end_date, datetime):
        end_date = end_date.strftime("%Y-%m-%d")

    cache_key = _get_cache_key("news", f"{ticker}_{start_date}_{end_date}_{limit}")
    cached = read_cache(cache_key)
    if cached:
        print(f"CACHE HIT: Polygon news for {ticker}")
        return cached

    enforce_rate_limit()
    client = get_client()

    articles = []
    try:
        for n in client.list_ticker_news(
            ticker=ticker.upper(),
            published_utc_gte=start_date,
            published_utc_lte=end_date + "T14:30:00Z",  # 9:30 AM ET = 2:30 PM UTC (market open)
            order="desc",
            sort="published_utc",
            limit=limit,
        ):
            publisher = getattr(n, "publisher", None)
            source_name = getattr(publisher, "name", "Unknown") if publisher else "Unknown"

            articles.append({
                "title": n.title or "",
                "url": n.article_url or "",
                "time_published": n.published_utc or "",
                "summary": getattr(n, "description", "") or "",
                "source": source_name,
                "tickers": n.tickers or [],
                "overall_sentiment_label": _extract_sentiment(n),
            })

            if len(articles) >= limit:
                break
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate" in error_msg.lower():
            from .polygon_common import PolygonRateLimitError
            raise PolygonRateLimitError(f"Polygon rate limit exceeded: {e}")
        raise

    result = {
        "feed": articles,
        "items": str(len(articles)),
        "source": "polygon",
    }

    print(f"FETCHED: Polygon news for {ticker} ({len(articles)} articles)")
    write_cache(cache_key, result)
    return result


def get_global_news(
    curr_date: str, look_back_days: int = 7, limit: int = 50
) -> dict:
    """Returns global market news from Polygon.io (no ticker filter).

    Matches the return format of alpha_vantage_news.get_global_news.

    Args:
        curr_date: Current date in YYYY-MM-DD format
        look_back_days: Number of days to look back for news (default 7)
        limit: Maximum number of articles to return (default 50)

    Returns:
        Dictionary with "feed" key containing list of article dicts.
    """
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=look_back_days)
    start_date = start_dt.strftime("%Y-%m-%d")
    end_date = end_dt.strftime("%Y-%m-%d")

    cache_key = _get_cache_key("global_news", f"{start_date}_{end_date}_{limit}")
    cached = read_cache(cache_key)
    if cached:
        print(f"CACHE HIT: Polygon global news")
        return cached

    enforce_rate_limit()
    client = get_client()

    articles = []
    try:
        # list_ticker_news without a ticker returns all news
        for n in client.list_ticker_news(
            published_utc_gte=start_date,
            published_utc_lte=end_date + "T14:30:00Z",  # 9:30 AM ET = 2:30 PM UTC (market open)
            order="desc",
            sort="published_utc",
            limit=limit,
        ):
            publisher = getattr(n, "publisher", None)
            source_name = getattr(publisher, "name", "Unknown") if publisher else "Unknown"

            articles.append({
                "title": n.title or "",
                "url": n.article_url or "",
                "time_published": n.published_utc or "",
                "summary": getattr(n, "description", "") or "",
                "source": source_name,
                "tickers": n.tickers or [],
                "overall_sentiment_label": _extract_sentiment(n),
            })

            if len(articles) >= limit:
                break
    except Exception as e:
        error_msg = str(e)
        if "429" in error_msg or "rate" in error_msg.lower():
            from .polygon_common import PolygonRateLimitError
            raise PolygonRateLimitError(f"Polygon rate limit exceeded: {e}")
        raise

    result = {
        "feed": articles,
        "items": str(len(articles)),
        "source": "polygon",
    }

    print(f"FETCHED: Polygon global news ({len(articles)} articles)")
    write_cache(cache_key, result)
    return result

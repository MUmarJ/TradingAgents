from .alpha_vantage_common import _make_api_request, format_datetime_for_api
from .config import get_config
from datetime import datetime, timedelta
import time
import json


def _fetch_articles_by_month(
    ticker: str | None,
    start_date: datetime,
    end_date: datetime,
    total_limit: int,
    delay_between_calls: float = 2.0
) -> list:
    """Fetch articles from each month separately to ensure temporal diversity.

    For long recall periods, this ensures articles are fetched from each month
    rather than just the most recent articles (which is what happens with a
    single API call sorted by LATEST).

    Args:
        ticker: Stock symbol (None for global news).
        start_date: Start of recall period.
        end_date: End of recall period.
        total_limit: Total articles to return (distributed across months).
        delay_between_calls: Seconds to wait between API calls (rate limiting).

    Returns:
        List of articles from all months combined.
    """
    # Generate monthly date ranges
    months = []
    current = start_date.replace(day=1)
    while current <= end_date:
        # Calculate month end (last day of current month or end_date, whichever is earlier)
        next_month = (current + timedelta(days=32)).replace(day=1)
        month_end = next_month - timedelta(days=1)
        month_end = min(month_end, end_date)

        # Only add if the range is valid (start <= end)
        month_start = max(current, start_date)
        if month_start <= month_end:
            months.append((month_start, month_end))

        current = next_month

    if not months:
        return []

    # Calculate base articles per month
    base_per_month = max(10, total_limit // len(months))

    all_articles = []
    remaining_quota = total_limit  # Track remaining articles to fetch

    for i, (month_start, month_end) in enumerate(months):
        if i > 0:
            time.sleep(delay_between_calls)  # Rate limiting

        # Calculate how many to fetch this month
        # Redistribute quota from previous months that had fewer articles
        months_left = len(months) - i
        articles_this_month = max(10, remaining_quota // months_left)

        params = {
            "time_from": format_datetime_for_api(month_start),
            "time_to": format_datetime_for_api(month_end),
            "sort": "LATEST",
            "limit": str(articles_this_month),
        }
        if ticker:
            params["tickers"] = ticker

        try:
            result = _make_api_request("NEWS_SENTIMENT", params)
            if isinstance(result, dict) and "feed" in result:
                fetched = result["feed"]
                all_articles.extend(fetched)
                remaining_quota -= len(fetched)
                print(f"  Monthly bucket {month_start.strftime('%Y-%m')}: fetched {len(fetched)}/{articles_this_month} articles")
            else:
                print(f"  Monthly bucket {month_start.strftime('%Y-%m')}: no articles found")
        except Exception as e:
            print(f"  Warning: Failed to fetch articles for {month_start.strftime('%Y-%m')}: {e}")
            continue

    return all_articles


def _sample_articles_by_time(articles: list, limit: int) -> list:
    """Sample articles evenly across time periods to ensure temporal diversity.

    For longer recall periods, this ensures we get articles from throughout
    the time range rather than just the most recent ones.
    """
    if not articles or len(articles) <= limit:
        return articles

    # Sort by time (newest first)
    sorted_articles = sorted(
        articles,
        key=lambda x: x.get("time_published", ""),
        reverse=True
    )

    # Sample evenly across the list
    step = len(sorted_articles) / limit
    sampled = []
    for i in range(limit):
        idx = int(i * step)
        if idx < len(sorted_articles):
            sampled.append(sorted_articles[idx])

    return sampled


def get_news(ticker, start_date, end_date, limit=50) -> dict[str, str] | str:
    """Returns live and historical market news & sentiment data from premier news outlets worldwide.

    Covers stocks, cryptocurrencies, forex, and topics like fiscal policy, mergers & acquisitions, IPOs.
    For long time ranges, samples articles evenly across the period for temporal diversity.

    Args:
        ticker: Stock symbol for news articles.
        start_date: Start date for news search.
        end_date: End date for news search.
        limit: Maximum number of articles to return (default 50).

    Returns:
        Dictionary containing news sentiment data or JSON string.
    """
    # Parse dates to calculate time range
    try:
        if isinstance(start_date, str):
            start_dt = datetime.strptime(start_date[:10], "%Y-%m-%d")
        else:
            start_dt = start_date
        if isinstance(end_date, str):
            end_dt = datetime.strptime(end_date[:10], "%Y-%m-%d")
        else:
            end_dt = end_date
        days_range = (end_dt - start_dt).days
    except (ValueError, TypeError):
        days_range = 7  # Default assumption

    # Check if monthly bucketing is enabled via config
    config = get_config()
    monthly_bucketing = config.get("news_monthly_bucketing", False)

    # Use monthly bucketing for long periods when enabled
    # This fetches from each month separately for true temporal diversity
    if monthly_bucketing and days_range > 30:
        print(f"Using monthly bucketing for {ticker} ({days_range} days)")
        articles = _fetch_articles_by_month(ticker, start_dt, end_dt, limit)

        # Sample if we got more than requested
        if len(articles) > limit:
            articles = _sample_articles_by_time(articles, limit)

        num_months = (days_range // 30) + 1
        return {
            "feed": articles,
            "items": str(len(articles)),
            "fetch_note": f"Fetched {len(articles)} articles from {num_months} monthly buckets across {days_range} days"
        }

    # Standard single-request approach
    params = {
        "tickers": ticker,
        "time_from": format_datetime_for_api(start_date),
        "time_to": format_datetime_for_api(end_date),
        "sort": "LATEST",
        "limit": str(limit),
    }

    result = _make_api_request("NEWS_SENTIMENT", params)

    # Check if we got meaningful results
    articles = []
    if isinstance(result, str):
        try:
            result = json.loads(result)
        except json.JSONDecodeError:
            return result
    if isinstance(result, dict):
        articles = result.get("feed", [])

    # Fallback: If few/no articles, try searching by company name
    config = get_config()
    company_fallback_enabled = config.get("news_company_fallback", True)

    if company_fallback_enabled and len(articles) < 5:
        from .alpha_vantage_common import get_company_name
        company_name = get_company_name(ticker)

        if company_name:
            print(f"  Fallback: Searching by company name '{company_name}'")
            # Use first word of company name as topic keyword
            fallback_params = {
                "time_from": format_datetime_for_api(start_date),
                "time_to": format_datetime_for_api(end_date),
                "sort": "LATEST",
                "limit": str(limit),
                "topics": company_name.split()[0],
            }

            try:
                fallback_result = _make_api_request("NEWS_SENTIMENT", fallback_params)
                if isinstance(fallback_result, str):
                    fallback_result = json.loads(fallback_result)
                if isinstance(fallback_result, dict) and "feed" in fallback_result:
                    fallback_articles = fallback_result["feed"]
                    if len(fallback_articles) > len(articles):
                        print(f"  Fallback found {len(fallback_articles)} articles (vs {len(articles)} by ticker)")
                        return fallback_result
            except Exception as e:
                print(f"  Fallback search failed: {e}")

    return result

def get_global_news(curr_date: str, look_back_days: int = 7, limit: int = 50) -> dict[str, str] | str:
    """Returns global market news & sentiment data without ticker filter.

    Retrieves general market news from premier news outlets worldwide,
    covering topics like fiscal policy, mergers & acquisitions, IPOs, etc.
    For long time ranges, samples articles evenly across the period for temporal diversity.

    Args:
        curr_date: Current date in YYYY-MM-DD format.
        look_back_days: Number of days to look back for news.
        limit: Maximum number of news items to return.

    Returns:
        Dictionary containing news sentiment data or JSON string.
    """
    # Calculate date range
    end_dt = datetime.strptime(curr_date, "%Y-%m-%d")
    start_dt = end_dt - timedelta(days=look_back_days)

    # Check if monthly bucketing is enabled via config
    config = get_config()
    monthly_bucketing = config.get("news_monthly_bucketing", False)

    # Use monthly bucketing for long periods when enabled
    # This fetches from each month separately for true temporal diversity
    if monthly_bucketing and look_back_days > 30:
        print(f"Using monthly bucketing for global news ({look_back_days} days)")
        articles = _fetch_articles_by_month(None, start_dt, end_dt, limit)

        # Sample if we got more than requested
        if len(articles) > limit:
            articles = _sample_articles_by_time(articles, limit)

        num_months = (look_back_days // 30) + 1
        return {
            "feed": articles,
            "items": str(len(articles)),
            "fetch_note": f"Fetched {len(articles)} articles from {num_months} monthly buckets across {look_back_days} days"
        }

    # Standard single-request approach
    params = {
        "time_from": format_datetime_for_api(start_dt),
        "time_to": format_datetime_for_api(end_dt),
        "sort": "LATEST",
        "limit": str(limit),
    }

    return _make_api_request("NEWS_SENTIMENT", params)


def get_insider_transactions(symbol: str) -> dict[str, str] | str:
    """Returns latest and historical insider transactions by key stakeholders.

    Covers transactions by founders, executives, board members, etc.

    Args:
        symbol: Ticker symbol. Example: "IBM".

    Returns:
        Dictionary containing insider transaction data or JSON string.
    """

    params = {
        "symbol": symbol,
    }

    return _make_api_request("INSIDER_TRANSACTIONS", params)
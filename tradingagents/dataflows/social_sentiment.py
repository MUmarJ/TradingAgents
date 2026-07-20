# TradingAgents/dataflows/social_sentiment.py
"""
Social Sentiment Data Module

Fetches social media sentiment data from multiple sources:
- Finnhub: Social sentiment from Reddit and Twitter
- Stocktwits: Dedicated stock social platform
- Reddit PRAW: Direct Reddit access for custom analysis

Note: ApeWisdom was removed as a source — unreliable data quality.

All data is cached to disk to avoid redundant API calls.
"""

import os
import json
import hashlib
import requests
import time
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from .config import get_config

# Cache settings
CACHE_EXPIRY_HOURS = 24  # How long before cache is considered stale


def _get_cache_dir() -> str:
    """Get the cache directory for social sentiment data."""
    config = get_config()
    cache_dir = os.path.join(config.get("data_cache_dir", "./data_cache"), "social_sentiment")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _get_cache_key(source: str, ticker: str, date: str, extra: str = "") -> str:
    """Generate a unique cache key for a request."""
    key_str = f"{source}_{ticker}_{date}_{extra}"
    return hashlib.md5(key_str.encode()).hexdigest()


def _read_cache(cache_key: str) -> Optional[Dict]:
    """Read data from cache if it exists and is not expired."""
    cache_dir = _get_cache_dir()
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    if not os.path.exists(cache_file):
        return None

    try:
        with open(cache_file, "r") as f:
            cached = json.load(f)

        # Check if cache is expired
        cached_time = datetime.fromisoformat(cached.get("cached_at", "2000-01-01"))
        if datetime.now() - cached_time > timedelta(hours=CACHE_EXPIRY_HOURS):
            return None

        return cached.get("data")
    except (json.JSONDecodeError, KeyError):
        return None


def _write_cache(cache_key: str, data: Dict) -> None:
    """Write data to cache."""
    cache_dir = _get_cache_dir()
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    cached = {
        "cached_at": datetime.now().isoformat(),
        "data": data
    }

    with open(cache_file, "w") as f:
        json.dump(cached, f, indent=2, default=str)


# =============================================================================
# ApeWisdom API - Aggregated Reddit Sentiment
# =============================================================================

def get_apewisdom_trending(
    ticker: str,
    filter_type: str = "all-stocks",
) -> Dict[str, Any]:
    """
    Get trending stocks and mentions from ApeWisdom.

    ApeWisdom aggregates mentions from WSB, r/stocks, r/investing, and more.

    Args:
        ticker: Stock ticker to look for
        filter_type: One of 'all', 'all-stocks', 'all-crypto', 'wallstreetbets',
                    'stocks', 'investing', 'options', etc.

    Returns:
        Dict with ticker mention data including rank, mentions, upvotes
    """
    cache_key = _get_cache_key("apewisdom", ticker, datetime.now().strftime("%Y-%m-%d"), filter_type)
    cached = _read_cache(cache_key)
    if cached:
        print(f"CACHE HIT: ApeWisdom data for {ticker}")
        return cached

    print(f"FETCHING: ApeWisdom trending for {ticker} (filter: {filter_type})")

    try:
        # ApeWisdom returns paginated results, we'll check first few pages
        all_results = []
        for page in range(1, 4):  # Check first 3 pages (300 tickers)
            url = f"https://apewisdom.io/api/v1.0/filter/{filter_type}/page/{page}"
            response = requests.get(url, timeout=10)

            if response.status_code != 200:
                break

            data = response.json()
            results = data.get("results", [])
            if not results:
                break

            all_results.extend(results)
            time.sleep(0.5)  # Rate limiting

        # Find our ticker in the results
        ticker_data = None
        for item in all_results:
            if item.get("ticker", "").upper() == ticker.upper():
                ticker_data = item
                break

        result = {
            "source": "apewisdom",
            "ticker": ticker,
            "filter": filter_type,
            "found": ticker_data is not None,
            "data": ticker_data,
            "top_trending": all_results[:10] if all_results else [],  # Include top 10 for context
            "fetched_at": datetime.now().isoformat()
        }

        _write_cache(cache_key, result)
        return result

    except Exception as e:
        print(f"ERROR: ApeWisdom API failed: {e}")
        return {
            "source": "apewisdom",
            "ticker": ticker,
            "error": str(e),
            "found": False,
            "data": None
        }


# =============================================================================
# Finnhub Social Sentiment API
# =============================================================================

def get_finnhub_social_sentiment(
    ticker: str,
    start_date: str,
    end_date: str,
) -> Dict[str, Any]:
    """
    Get social sentiment data from Finnhub (Reddit + Twitter).

    Requires FINNHUB_API_KEY environment variable.

    Args:
        ticker: Stock ticker
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)

    Returns:
        Dict with social sentiment data
    """
    cache_key = _get_cache_key("finnhub_social", ticker, f"{start_date}_{end_date}")
    cached = _read_cache(cache_key)
    if cached:
        print(f"CACHE HIT: Finnhub social sentiment for {ticker}")
        return cached

    api_key = os.getenv("FINNHUB_API_KEY")
    if not api_key:
        return {
            "source": "finnhub",
            "ticker": ticker,
            "error": "FINNHUB_API_KEY not set",
            "data": None
        }

    print(f"FETCHING: Finnhub social sentiment for {ticker} ({start_date} to {end_date})")

    try:
        url = "https://finnhub.io/api/v1/stock/social-sentiment"
        params = {
            "symbol": ticker,
            "from": start_date,
            "to": end_date,
            "token": api_key
        }

        response = requests.get(url, params=params, timeout=10)

        if response.status_code == 403:
            return {
                "source": "finnhub",
                "ticker": ticker,
                "error": "Finnhub social sentiment requires premium subscription",
                "data": None
            }

        response.raise_for_status()
        data = response.json()

        result = {
            "source": "finnhub",
            "ticker": ticker,
            "start_date": start_date,
            "end_date": end_date,
            "data": data,
            "fetched_at": datetime.now().isoformat()
        }

        _write_cache(cache_key, result)
        return result

    except Exception as e:
        print(f"ERROR: Finnhub social sentiment failed: {e}")
        return {
            "source": "finnhub",
            "ticker": ticker,
            "error": str(e),
            "data": None
        }


# =============================================================================
# Stocktwits API
# =============================================================================

# Stocktwits rate limits: 200 requests/hour unauthenticated, 30 messages per request
# Max pagination: ~20 pages before rate limiting becomes a concern
STOCKTWITS_MAX_PAGES = 20  # 20 pages * 30 messages = 600 messages max

def get_stocktwits_sentiment(
    ticker: str,
    limit: int = 50,
    start_date: str = None,
    end_date: str = None,
) -> Dict[str, Any]:
    """
    Get sentiment data from Stocktwits with pagination and date filtering.

    Stocktwits is a social platform specifically for stock discussions.
    Messages include sentiment labels (Bullish/Bearish) from users.

    Rate limits: 200 requests/hour, 30 messages per request.
    With pagination, can fetch up to 600 messages (20 pages) per ticker.

    Args:
        ticker: Stock ticker
        limit: Target number of messages to fetch (will paginate to reach this)
               Recommended: 50 (default), 200 (3mo), 500 (6mo+)
        start_date: Filter messages after this date (YYYY-MM-DD), optional
        end_date: Filter messages before this date (YYYY-MM-DD), optional

    Returns:
        Dict with Stocktwits messages and sentiment analysis
    """
    # Include limit and dates in cache key
    date_suffix = f"limit_{limit}"
    if start_date:
        date_suffix += f"_from_{start_date}"
    if end_date:
        date_suffix += f"_to_{end_date}"
    cache_key = _get_cache_key("stocktwits", ticker, datetime.now().strftime("%Y-%m-%d"), date_suffix)
    cached = _read_cache(cache_key)
    if cached:
        print(f"CACHE HIT: Stocktwits data for {ticker} (limit={limit})")
        return cached

    # Parse date filters
    start_dt = None
    end_dt = None
    if start_date:
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        except ValueError:
            pass
    if end_date:
        try:
            end_dt = datetime.strptime(end_date, "%Y-%m-%d").replace(hour=23, minute=59, second=59)
        except ValueError:
            pass

    date_filter_str = ""
    if start_dt or end_dt:
        date_filter_str = f" [filtering: {start_date or 'any'} to {end_date or 'any'}]"
    print(f"FETCHING: Stocktwits sentiment for {ticker} (target: {limit} messages){date_filter_str}")

    try:
        url = f"https://api.stocktwits.com/api/2/streams/symbol/{ticker}.json"
        headers = {
            "User-Agent": "TradingAgents/1.0 (stock research tool)",
            "Accept": "application/json"
        }

        all_messages = []
        max_cursor = None
        pages_fetched = 0
        symbol_info = None

        # Paginate until we have enough messages or no more available
        while len(all_messages) < limit and pages_fetched < STOCKTWITS_MAX_PAGES:
            params = {"limit": 30}
            if max_cursor:
                params["max"] = max_cursor

            response = requests.get(url, params=params, headers=headers, timeout=10)

            # Handle specific error codes before raise_for_status
            if response.status_code == 404:
                return {
                    "source": "stocktwits",
                    "ticker": ticker,
                    "error": f"Ticker {ticker} not found on Stocktwits",
                    "message_count": 0,
                    "sentiment_summary": None
                }
            elif response.status_code == 403:
                # Cloudflare blocking or rate limiting
                print(f"WARNING: Stocktwits blocked (403 Forbidden) - likely Cloudflare protection or rate limit")
                return {
                    "source": "stocktwits",
                    "ticker": ticker,
                    "error": "Stocktwits API blocked (403) - rate limited or Cloudflare protection. Try again later.",
                    "message_count": 0,
                    "sentiment_summary": None
                }

            response.raise_for_status()
            data = response.json()

            messages = data.get("messages", [])
            if not messages:
                break

            all_messages.extend(messages)
            pages_fetched += 1

            # Save symbol info from first request
            if symbol_info is None:
                symbol_info = data.get("symbol", {})

            # Check if more pages available
            cursor = data.get("cursor", {})
            if cursor.get("more") and cursor.get("max"):
                max_cursor = cursor["max"]
                time.sleep(0.3)  # Rate limiting - be nice to the API
            else:
                break

        print(f"FETCHED: {len(all_messages)} Stocktwits messages for {ticker} ({pages_fetched} pages)")

        # Filter messages by date if specified
        filtered_messages = []
        for msg in all_messages:
            created_at_str = msg.get("created_at")
            if created_at_str:
                try:
                    # Parse ISO format: 2026-01-21T21:54:00Z
                    msg_dt = datetime.fromisoformat(created_at_str.replace("Z", "+00:00")).replace(tzinfo=None)

                    # Apply date filters
                    if start_dt and msg_dt < start_dt:
                        continue
                    if end_dt and msg_dt > end_dt:
                        continue
                except (ValueError, AttributeError):
                    pass  # Keep message if date parsing fails

            filtered_messages.append(msg)

        # Report filtering stats
        if start_dt or end_dt:
            filtered_out = len(all_messages) - len(filtered_messages)
            if filtered_out > 0:
                print(f"FILTERED: {filtered_out} messages outside date range, {len(filtered_messages)} remaining")

        # Analyze sentiment from filtered messages
        bullish_count = 0
        bearish_count = 0
        neutral_count = 0

        processed_messages = []
        for msg in filtered_messages:
            sentiment = msg.get("entities", {}).get("sentiment", {})
            sentiment_label = sentiment.get("basic") if sentiment else None

            if sentiment_label == "Bullish":
                bullish_count += 1
            elif sentiment_label == "Bearish":
                bearish_count += 1
            else:
                neutral_count += 1

            processed_messages.append({
                "id": msg.get("id"),
                "body": msg.get("body"),
                "sentiment": sentiment_label,
                "created_at": msg.get("created_at"),
                "user": msg.get("user", {}).get("username"),
                "likes": msg.get("likes", {}).get("total", 0)
            })

        total = bullish_count + bearish_count + neutral_count

        # Calculate date range of messages
        date_range = {}
        if processed_messages:
            dates = [m.get("created_at") for m in processed_messages if m.get("created_at")]
            if dates:
                date_range = {
                    "oldest": min(dates),
                    "newest": max(dates),
                }

        result = {
            "source": "stocktwits",
            "ticker": ticker,
            "symbol_info": symbol_info or {},
            "message_count": len(filtered_messages),
            "messages_before_filter": len(all_messages),
            "pages_fetched": pages_fetched,
            "date_range": date_range,
            "date_filter": {
                "start": start_date,
                "end": end_date,
            } if start_dt or end_dt else None,
            "sentiment_summary": {
                "bullish": bullish_count,
                "bearish": bearish_count,
                "neutral": neutral_count,
                "bullish_ratio": bullish_count / total if total > 0 else 0,
                "bearish_ratio": bearish_count / total if total > 0 else 0,
            },
            "messages": processed_messages[:50],  # Keep top 50 for LLM context
            "fetched_at": datetime.now().isoformat()
        }

        _write_cache(cache_key, result)
        return result

    except Exception as e:
        print(f"ERROR: Stocktwits API failed: {e}")
        return {
            "source": "stocktwits",
            "ticker": ticker,
            "error": str(e),
            "message_count": 0,
            "sentiment_summary": None
        }


# =============================================================================
# Reddit PRAW Integration
# =============================================================================

def get_reddit_sentiment(
    ticker: str,
    company_name: str,
    start_date: str,
    end_date: str,
    subreddits: List[str] = None,
    limit_per_subreddit: int = 25,
) -> Dict[str, Any]:
    """
    Get sentiment data directly from Reddit using PRAW.

    Requires REDDIT_CLIENT_ID, REDDIT_CLIENT_SECRET environment variables.

    Args:
        ticker: Stock ticker
        company_name: Company name for searching
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        subreddits: List of subreddits to search (default: WSB, stocks, investing)
        limit_per_subreddit: Max posts per subreddit

    Returns:
        Dict with Reddit posts and basic sentiment analysis
    """
    if subreddits is None:
        subreddits = ["wallstreetbets", "stocks", "investing", "stockmarket"]

    cache_key = _get_cache_key(
        "reddit_praw",
        ticker,
        f"{start_date}_{end_date}",
        "_".join(subreddits)
    )
    cached = _read_cache(cache_key)
    if cached:
        print(f"CACHE HIT: Reddit PRAW data for {ticker}")
        return cached

    # Check for PRAW credentials
    client_id = os.getenv("REDDIT_CLIENT_ID")
    client_secret = os.getenv("REDDIT_CLIENT_SECRET")

    if not client_id or not client_secret:
        return {
            "source": "reddit_praw",
            "ticker": ticker,
            "error": "REDDIT_CLIENT_ID and REDDIT_CLIENT_SECRET not set. See https://www.reddit.com/prefs/apps",
            "data": None
        }

    print(f"FETCHING: Reddit posts for {ticker}/{company_name} from {subreddits}")

    try:
        import praw
    except ImportError:
        return {
            "source": "reddit_praw",
            "ticker": ticker,
            "error": "praw package not installed. Run: pip install praw",
            "data": None
        }

    try:
        reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            user_agent="TradingAgents/1.0"
        )

        start_dt = datetime.strptime(start_date, "%Y-%m-%d")
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")

        all_posts = []
        search_terms = [ticker, company_name] if company_name else [ticker]

        for subreddit_name in subreddits:
            try:
                subreddit = reddit.subreddit(subreddit_name)

                for term in search_terms:
                    # Search for posts
                    for post in subreddit.search(term, limit=limit_per_subreddit, sort="relevance"):
                        post_date = datetime.utcfromtimestamp(post.created_utc)

                        # Filter by date range
                        if start_dt <= post_date <= end_dt:
                            all_posts.append({
                                "subreddit": subreddit_name,
                                "title": post.title,
                                "selftext": post.selftext[:500] if post.selftext else "",
                                "score": post.score,
                                "upvote_ratio": post.upvote_ratio,
                                "num_comments": post.num_comments,
                                "created_utc": post.created_utc,
                                "created_date": post_date.strftime("%Y-%m-%d"),
                                "url": f"https://reddit.com{post.permalink}",
                                "search_term": term
                            })

                time.sleep(1)  # Rate limiting between subreddits

            except Exception as e:
                print(f"WARNING: Failed to fetch from r/{subreddit_name}: {e}")
                continue

        # Remove duplicates (same post found with different search terms)
        seen_urls = set()
        unique_posts = []
        for post in all_posts:
            if post["url"] not in seen_urls:
                seen_urls.add(post["url"])
                unique_posts.append(post)

        # Sort by score
        unique_posts.sort(key=lambda x: x["score"], reverse=True)

        # Basic sentiment analysis using keywords
        positive_keywords = ["bullish", "buy", "moon", "rocket", "gain", "up", "profit", "long"]
        negative_keywords = ["bearish", "sell", "crash", "loss", "down", "short", "dump", "puts"]

        positive_count = 0
        negative_count = 0

        for post in unique_posts:
            text = (post["title"] + " " + post["selftext"]).lower()
            pos_matches = sum(1 for kw in positive_keywords if kw in text)
            neg_matches = sum(1 for kw in negative_keywords if kw in text)

            if pos_matches > neg_matches:
                positive_count += 1
                post["keyword_sentiment"] = "positive"
            elif neg_matches > pos_matches:
                negative_count += 1
                post["keyword_sentiment"] = "negative"
            else:
                post["keyword_sentiment"] = "neutral"

        total = len(unique_posts)

        result = {
            "source": "reddit_praw",
            "ticker": ticker,
            "company_name": company_name,
            "start_date": start_date,
            "end_date": end_date,
            "subreddits_searched": subreddits,
            "post_count": len(unique_posts),
            "sentiment_summary": {
                "positive": positive_count,
                "negative": negative_count,
                "neutral": total - positive_count - negative_count,
                "positive_ratio": positive_count / total if total > 0 else 0,
                "negative_ratio": negative_count / total if total > 0 else 0,
            },
            "posts": unique_posts[:30],  # Limit to top 30 posts
            "fetched_at": datetime.now().isoformat()
        }

        _write_cache(cache_key, result)
        return result

    except Exception as e:
        print(f"ERROR: Reddit PRAW failed: {e}")
        return {
            "source": "reddit_praw",
            "ticker": ticker,
            "error": str(e),
            "data": None
        }


# =============================================================================
# Aggregated Social Sentiment (combines all sources)
# =============================================================================

def get_aggregated_social_sentiment(
    ticker: str,
    company_name: str = None,
    start_date: str = None,
    end_date: str = None,
    lookback_days: int = 7,
) -> str:
    """
    Get aggregated social sentiment from all available sources.

    This is the main entry point for the Social Media Analyst.
    Combines data from Finnhub, Stocktwits, and Reddit.

    Args:
        ticker: Stock ticker
        company_name: Company name (optional, improves Reddit search)
        start_date: Start date (YYYY-MM-DD), defaults to lookback_days ago
        end_date: End date (YYYY-MM-DD), defaults to today
        lookback_days: Days to look back if dates not specified

    Returns:
        Formatted string with social sentiment analysis from all sources
    """
    # Set default dates
    if not end_date:
        end_date = datetime.now().strftime("%Y-%m-%d")
    if not start_date:
        start_date = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    if not company_name:
        # Use ticker-to-company mapping if available
        from .reddit_utils import ticker_to_company
        company_name = ticker_to_company.get(ticker, ticker)

    report = f"# Social Media Sentiment Report for {ticker}\n"
    report += f"**Period:** {start_date} to {end_date}\n\n"

    # 1. Stocktwits
    report += "## 1. Stocktwits Sentiment\n\n"
    stocktwits_data = get_stocktwits_sentiment(ticker)

    if stocktwits_data.get("error"):
        report += f"*Error: {stocktwits_data['error']}*\n\n"
    elif stocktwits_data.get("sentiment_summary"):
        summary = stocktwits_data["sentiment_summary"]
        report += f"- **Messages analyzed:** {stocktwits_data.get('message_count', 0)}\n"
        report += f"- **Bullish:** {summary['bullish']} ({summary['bullish_ratio']:.1%})\n"
        report += f"- **Bearish:** {summary['bearish']} ({summary['bearish_ratio']:.1%})\n"
        report += f"- **Neutral:** {summary['neutral']}\n\n"

        # Sample messages
        if stocktwits_data.get("messages"):
            report += "**Recent Stocktwits Messages:**\n"
            for msg in stocktwits_data["messages"][:5]:
                sentiment_emoji = "🐂" if msg.get("sentiment") == "Bullish" else "🐻" if msg.get("sentiment") == "Bearish" else "➖"
                report += f"- {sentiment_emoji} @{msg.get('user', 'anon')}: {msg.get('body', '')[:100]}...\n"
            report += "\n"

    # 2. Finnhub Social Sentiment
    report += "## 2. Finnhub Social Sentiment (Reddit + Twitter)\n\n"
    finnhub_data = get_finnhub_social_sentiment(ticker, start_date, end_date)

    if finnhub_data.get("error"):
        report += f"*{finnhub_data['error']}*\n\n"
    elif finnhub_data.get("data"):
        data = finnhub_data["data"]
        if data.get("reddit"):
            report += "**Reddit (via Finnhub):**\n"
            for item in data["reddit"][:5]:
                report += f"- {item.get('atTime', 'N/A')}: Score {item.get('score', 0)}, Mentions: {item.get('mention', 0)}\n"
            report += "\n"
        if data.get("twitter"):
            report += "**Twitter (via Finnhub):**\n"
            for item in data["twitter"][:5]:
                report += f"- {item.get('atTime', 'N/A')}: Score {item.get('score', 0)}, Mentions: {item.get('mention', 0)}\n"
            report += "\n"

    # 3. Reddit PRAW (direct)
    report += "## 3. Reddit Direct Analysis (PRAW)\n\n"
    reddit_data = get_reddit_sentiment(ticker, company_name, start_date, end_date)

    if reddit_data.get("error"):
        report += f"*{reddit_data['error']}*\n\n"
    elif reddit_data.get("post_count", 0) > 0:
        summary = reddit_data["sentiment_summary"]
        report += f"- **Posts found:** {reddit_data['post_count']}\n"
        report += f"- **Subreddits searched:** {', '.join(reddit_data.get('subreddits_searched', []))}\n"
        report += f"- **Positive sentiment:** {summary['positive']} ({summary['positive_ratio']:.1%})\n"
        report += f"- **Negative sentiment:** {summary['negative']} ({summary['negative_ratio']:.1%})\n\n"

        if reddit_data.get("posts"):
            report += "**Top Reddit Posts (by upvotes):**\n\n"
            for post in reddit_data["posts"][:5]:
                sentiment_emoji = "🟢" if post.get("keyword_sentiment") == "positive" else "🔴" if post.get("keyword_sentiment") == "negative" else "⚪"
                report += f"### {sentiment_emoji} r/{post['subreddit']}: {post['title'][:80]}...\n"
                report += f"- Score: {post['score']} | Comments: {post['num_comments']} | Date: {post['created_date']}\n"
                if post.get("selftext"):
                    report += f"- Preview: {post['selftext'][:200]}...\n"
                report += "\n"
    else:
        report += "*No Reddit posts found for the specified period*\n\n"

    # Summary
    report += "## Summary\n\n"
    report += "| Source | Status | Key Finding |\n"
    report += "|--------|--------|-------------|\n"

    # Stocktwits summary
    if stocktwits_data.get("sentiment_summary"):
        summary = stocktwits_data["sentiment_summary"]
        dominant = "Bullish" if summary["bullish"] > summary["bearish"] else "Bearish" if summary["bearish"] > summary["bullish"] else "Neutral"
        report += f"| Stocktwits | ✅ | {dominant} ({max(summary['bullish_ratio'], summary['bearish_ratio']):.0%}) |\n"
    else:
        report += f"| Stocktwits | ❌ | {stocktwits_data.get('error', 'No data')} |\n"

    # Finnhub summary
    if finnhub_data.get("data"):
        report += "| Finnhub | ✅ | Data available |\n"
    else:
        report += f"| Finnhub | ❌ | {finnhub_data.get('error', 'No data')[:30]} |\n"

    # Reddit summary
    if reddit_data.get("post_count", 0) > 0:
        summary = reddit_data["sentiment_summary"]
        dominant = "Positive" if summary["positive"] > summary["negative"] else "Negative" if summary["negative"] > summary["positive"] else "Mixed"
        report += f"| Reddit | ✅ | {reddit_data['post_count']} posts, {dominant} sentiment |\n"
    else:
        report += f"| Reddit | ❌ | {reddit_data.get('error', 'No posts found')[:30]} |\n"

    report += "\n"

    return report


# =============================================================================
# Individual Vendor Wrappers (for vendor-specific configuration)
# =============================================================================

def _format_stocktwits_report(ticker: str, data: Dict, max_messages_in_report: int = 25) -> str:
    """Format Stocktwits data as a report string.

    Args:
        ticker: Stock ticker
        data: Stocktwits data dict
        max_messages_in_report: Max messages to include in report (default: 25)
    """
    report = f"# Stocktwits Sentiment Report for {ticker}\n\n"

    if data.get("error"):
        report += f"*Error: {data['error']}*\n"
        return report

    if data.get("sentiment_summary"):
        summary = data["sentiment_summary"]
        msg_count = data.get('message_count', 0)
        pages = data.get('pages_fetched', 1)
        before_filter = data.get('messages_before_filter', msg_count)

        report += f"## Sentiment Summary\n"
        report += f"- **Messages analyzed:** {msg_count}"
        if before_filter > msg_count:
            report += f" (filtered from {before_filter})"
        report += f" ({pages} pages fetched)\n"

        # Show date range of messages
        date_range = data.get('date_range', {})
        if date_range:
            report += f"- **Date range:** {date_range.get('oldest', 'N/A')} to {date_range.get('newest', 'N/A')}\n"

        report += f"- **Bullish:** {summary['bullish']} ({summary['bullish_ratio']:.1%})\n"
        report += f"- **Bearish:** {summary['bearish']} ({summary['bearish_ratio']:.1%})\n"
        report += f"- **Neutral:** {summary['neutral']}\n"

        # Calculate sentiment score (-1 to +1)
        total_sentiment = summary['bullish'] + summary['bearish']
        if total_sentiment > 0:
            sentiment_score = (summary['bullish'] - summary['bearish']) / total_sentiment
            sentiment_label = "Strongly Bullish" if sentiment_score > 0.5 else \
                             "Bullish" if sentiment_score > 0.2 else \
                             "Neutral" if sentiment_score > -0.2 else \
                             "Bearish" if sentiment_score > -0.5 else "Strongly Bearish"
            report += f"- **Overall sentiment score:** {sentiment_score:.2f} ({sentiment_label})\n"

        report += "\n"

        if data.get("messages"):
            # Show sample of messages, mix of bullish and bearish
            messages = data["messages"]
            bullish_msgs = [m for m in messages if m.get("sentiment") == "Bullish"]
            bearish_msgs = [m for m in messages if m.get("sentiment") == "Bearish"]
            neutral_msgs = [m for m in messages if m.get("sentiment") not in ["Bullish", "Bearish"]]

            report += f"## Sample Messages ({min(len(messages), max_messages_in_report)} of {msg_count})\n\n"

            # Include balanced sample
            sample = []
            sample.extend(bullish_msgs[:max_messages_in_report // 3])
            sample.extend(bearish_msgs[:max_messages_in_report // 3])
            sample.extend(neutral_msgs[:max_messages_in_report // 3])
            # Sort by most recent (id is typically chronological)
            sample.sort(key=lambda x: x.get("id", 0), reverse=True)

            for msg in sample[:max_messages_in_report]:
                sentiment_emoji = "🐂" if msg.get("sentiment") == "Bullish" else "🐻" if msg.get("sentiment") == "Bearish" else "➖"
                body = msg.get('body', '')[:200].replace('\n', ' ')
                report += f"- {sentiment_emoji} @{msg.get('user', 'anon')}: {body}\n"

    return report


def _format_apewisdom_report(ticker: str, data: Dict) -> str:
    """Format ApeWisdom data as a report string."""
    report = f"# Reddit Trending Report for {ticker} (via ApeWisdom)\n\n"

    if data.get("error"):
        report += f"*Error: {data['error']}*\n"
        return report

    if data.get("found") and data.get("data"):
        d = data["data"]
        report += f"- **Rank:** #{d.get('rank', 'N/A')} on Reddit stock discussions\n"
        report += f"- **Mentions (24h):** {d.get('mentions', 'N/A')}\n"
        report += f"- **Rank 24h ago:** #{d.get('rank_24h_ago', 'N/A')}\n"
        report += f"- **Upvotes:** {d.get('upvotes', 'N/A')}\n\n"

        if data.get("top_trending"):
            report += "**Current Top 10 Trending on Reddit:**\n"
            for i, item in enumerate(data["top_trending"][:10], 1):
                marker = " 👈" if item.get("ticker", "").upper() == ticker.upper() else ""
                report += f"{i}. {item.get('ticker')} - {item.get('mentions')} mentions{marker}\n"
    else:
        report += f"*{ticker} not found in top Reddit trending stocks*\n\n"
        if data.get("top_trending"):
            report += "**Current Top 10 Trending (for context):**\n"
            for i, item in enumerate(data["top_trending"][:10], 1):
                report += f"{i}. {item.get('ticker')} - {item.get('mentions')} mentions\n"

    return report


def _format_finnhub_report(ticker: str, start_date: str, end_date: str, data: Dict) -> str:
    """Format Finnhub social sentiment data as a report string."""
    report = f"# Finnhub Social Sentiment Report for {ticker}\n"
    report += f"**Period:** {start_date} to {end_date}\n\n"

    if data.get("error"):
        report += f"*Error: {data['error']}*\n"
        return report

    if data.get("data"):
        d = data["data"]
        if d.get("reddit"):
            report += "**Reddit Sentiment (via Finnhub):**\n"
            for item in d["reddit"][:10]:
                report += f"- {item.get('atTime', 'N/A')}: Score {item.get('score', 0)}, Mentions: {item.get('mention', 0)}\n"
            report += "\n"
        if d.get("twitter"):
            report += "**Twitter Sentiment (via Finnhub):**\n"
            for item in d["twitter"][:10]:
                report += f"- {item.get('atTime', 'N/A')}: Score {item.get('score', 0)}, Mentions: {item.get('mention', 0)}\n"
    else:
        report += "*No data available*\n"

    return report


def _format_reddit_praw_report(ticker: str, data: Dict) -> str:
    """Format Reddit PRAW data as a report string."""
    report = f"# Reddit Direct Analysis for {ticker}\n\n"

    if data.get("error"):
        report += f"*Error: {data['error']}*\n"
        return report

    if data.get("post_count", 0) > 0:
        summary = data["sentiment_summary"]
        report += f"- **Posts found:** {data['post_count']}\n"
        report += f"- **Subreddits:** {', '.join(data.get('subreddits_searched', []))}\n"
        report += f"- **Positive:** {summary['positive']} ({summary['positive_ratio']:.1%})\n"
        report += f"- **Negative:** {summary['negative']} ({summary['negative_ratio']:.1%})\n\n"

        if data.get("posts"):
            report += "**Top Posts (by upvotes):**\n\n"
            for post in data["posts"][:10]:
                emoji = "🟢" if post.get("keyword_sentiment") == "positive" else "🔴" if post.get("keyword_sentiment") == "negative" else "⚪"
                report += f"### {emoji} r/{post['subreddit']}: {post['title'][:100]}\n"
                report += f"- Score: {post['score']} | Comments: {post['num_comments']} | {post['created_date']}\n"
                if post.get("selftext"):
                    report += f"- {post['selftext'][:300]}...\n"
                report += "\n"
    else:
        report += "*No posts found*\n"

    return report


def get_social_sentiment_stocktwits(
    ticker: str,
    start_date: str,
    end_date: str,
    limit: int = 50,
) -> str:
    """Get social sentiment from Stocktwits only with date filtering.

    Args:
        ticker: Stock ticker
        start_date: Filter messages after this date (YYYY-MM-DD)
        end_date: Filter messages before this date (YYYY-MM-DD)
        limit: Target number of messages to fetch (default: 50, max: 600)

    Raises:
        RuntimeError: If Stocktwits API fails (triggers fallback to other vendors)
    """
    # Pass dates for filtering - Stocktwits API doesn't support date params,
    # so we fetch more and filter client-side
    data = get_stocktwits_sentiment(ticker, limit=limit, start_date=start_date, end_date=end_date)

    # If error occurred, raise exception to trigger vendor fallback
    if data.get("error"):
        raise RuntimeError(f"Stocktwits error: {data['error']}")

    return _format_stocktwits_report(ticker, data)


def get_social_sentiment_apewisdom(
    ticker: str,
    start_date: str,
    end_date: str,
    limit: int = 50,
) -> str:
    """Get social sentiment from ApeWisdom (Reddit aggregated) only.

    Note: ApeWisdom only shows trending stocks, so a stock not being found
    is not an error - it just means the stock isn't trending on Reddit.
    """
    data = get_apewisdom_trending(ticker)

    # Only raise on actual API errors, not "not found"
    if data.get("error") and not data.get("found") is False:
        raise RuntimeError(f"ApeWisdom error: {data['error']}")

    return _format_apewisdom_report(ticker, data)


def get_social_sentiment_finnhub(
    ticker: str,
    start_date: str,
    end_date: str,
    limit: int = 50,
) -> str:
    """Get social sentiment from Finnhub only.

    Raises:
        RuntimeError: If Finnhub API fails (triggers fallback to other vendors)
    """
    data = get_finnhub_social_sentiment(ticker, start_date, end_date)

    # If error occurred, raise exception to trigger vendor fallback
    if data.get("error"):
        raise RuntimeError(f"Finnhub error: {data['error']}")

    return _format_finnhub_report(ticker, start_date, end_date, data)


def get_social_sentiment_reddit(
    ticker: str,
    start_date: str,
    end_date: str,
    limit: int = 50,
) -> str:
    """Get social sentiment from Reddit PRAW only.

    Raises:
        RuntimeError: If Reddit API fails (triggers fallback to other vendors)
    """
    from .reddit_utils import ticker_to_company
    company_name = ticker_to_company.get(ticker, ticker)
    data = get_reddit_sentiment(ticker, company_name, start_date, end_date)

    # If error occurred, raise exception to trigger vendor fallback
    if data.get("error"):
        raise RuntimeError(f"Reddit PRAW error: {data['error']}")

    return _format_reddit_praw_report(ticker, data)


# =============================================================================
# Tool wrapper for LangChain (aggregated - default)
# =============================================================================

def get_social_sentiment(
    ticker: str,
    start_date: str,
    end_date: str,
    limit: int = 50,
) -> str:
    """
    Get social media sentiment data for a stock (aggregated from all sources).

    This is the main tool function exposed to the Social Media Analyst.

    Args:
        ticker: Stock ticker symbol
        start_date: Start date (YYYY-MM-DD)
        end_date: End date (YYYY-MM-DD)
        limit: Maximum items to return (not used, kept for API compatibility)

    Returns:
        Formatted string with social sentiment analysis
    """
    return get_aggregated_social_sentiment(
        ticker=ticker,
        start_date=start_date,
        end_date=end_date,
    )

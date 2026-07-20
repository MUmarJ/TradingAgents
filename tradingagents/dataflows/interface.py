from typing import Annotated
import json
import time

# Import from vendor-specific modules
from .local import get_YFin_data, get_finnhub_news, get_finnhub_company_insider_sentiment, get_finnhub_company_insider_transactions, get_simfin_balance_sheet, get_simfin_cashflow, get_simfin_income_statements, get_reddit_global_news, get_reddit_company_news
from .y_finance import get_YFin_data_online, get_stock_stats_indicators_window, get_balance_sheet as get_yfinance_balance_sheet, get_cashflow as get_yfinance_cashflow, get_income_statement as get_yfinance_income_statement, get_insider_transactions as get_yfinance_insider_transactions
from .google import get_google_news
from .openai import get_stock_news_openai, get_global_news_openai, get_fundamentals_openai
from .alpha_vantage import (
    get_stock as get_alpha_vantage_stock,
    get_indicator as get_alpha_vantage_indicator,
    get_fundamentals as get_alpha_vantage_fundamentals,
    get_balance_sheet as get_alpha_vantage_balance_sheet,
    get_cashflow as get_alpha_vantage_cashflow,
    get_income_statement as get_alpha_vantage_income_statement,
    get_insider_transactions as get_alpha_vantage_insider_transactions,
    get_news as get_alpha_vantage_news,
    get_global_news as get_alpha_vantage_global_news
)
from .social_sentiment import (
    get_social_sentiment as get_social_sentiment_aggregated,
    get_social_sentiment_stocktwits,
    get_social_sentiment_finnhub,
    get_social_sentiment_reddit,
)
from .stockgeist_sentiment import get_social_sentiment_stockgeist
from .alpha_vantage_common import AlphaVantageRateLimitError
from .polygon_common import PolygonRateLimitError
from .polygon import (
    get_stock as get_polygon_stock,
    get_indicator as get_polygon_indicator,
    get_news as get_polygon_news,
    get_global_news as get_polygon_global_news,
)
from openai import APIConnectionError, APITimeoutError, RateLimitError

# Configuration and routing logic
from .config import get_config

# Tools organized by category
TOOLS_CATEGORIES = {
    "core_stock_apis": {
        "description": "OHLCV stock price data",
        "tools": [
            "get_stock_data"
        ]
    },
    "technical_indicators": {
        "description": "Technical analysis indicators",
        "tools": [
            "get_indicators"
        ]
    },
    "fundamental_data": {
        "description": "Company fundamentals",
        "tools": [
            "get_fundamentals",
            "get_balance_sheet",
            "get_cashflow",
            "get_income_statement"
        ]
    },
    "news_data": {
        "description": "News (public/insiders, original/processed)",
        "tools": [
            "get_news",
            "get_global_news",
            "get_insider_sentiment",
            "get_insider_transactions",
        ]
    },
    "social_sentiment": {
        "description": "Social media sentiment (Reddit, Stocktwits, Twitter)",
        "tools": [
            "get_social_sentiment"
        ]
    }
}

VENDOR_LIST = [
    "polygon",
    "alpha_vantage",
    "local",
    "yfinance",
    "openai",
    "google",
    "stockgeist",   # StockGeist NLP sentiment (free tier: 10k credits/mo)
    "aggregated",   # For social sentiment (combines multiple sources)
]

# Mapping of methods to their vendor-specific implementations
VENDOR_METHODS = {
    # core_stock_apis
    "get_stock_data": {
        "polygon": get_polygon_stock,
        "alpha_vantage": get_alpha_vantage_stock,
        "yfinance": get_YFin_data_online,
        "local": get_YFin_data,
    },
    # technical_indicators
    "get_indicators": {
        "polygon": get_polygon_indicator,
        "alpha_vantage": get_alpha_vantage_indicator,
        "yfinance": get_stock_stats_indicators_window,
        "local": get_stock_stats_indicators_window,
    },
    # fundamental_data
    "get_fundamentals": {
        "alpha_vantage": get_alpha_vantage_fundamentals,
        "openai": get_fundamentals_openai,
    },
    "get_balance_sheet": {
        "alpha_vantage": get_alpha_vantage_balance_sheet,
        "yfinance": get_yfinance_balance_sheet,
        "local": get_simfin_balance_sheet,
    },
    "get_cashflow": {
        "alpha_vantage": get_alpha_vantage_cashflow,
        "yfinance": get_yfinance_cashflow,
        "local": get_simfin_cashflow,
    },
    "get_income_statement": {
        "alpha_vantage": get_alpha_vantage_income_statement,
        "yfinance": get_yfinance_income_statement,
        "local": get_simfin_income_statements,
    },
    # news_data
    "get_news": {
        "polygon": get_polygon_news,
        "alpha_vantage": get_alpha_vantage_news,
        "openai": get_stock_news_openai,
        "google": get_google_news,
        "local": [get_finnhub_news, get_reddit_company_news, get_google_news],
    },
    "get_global_news": {
        "polygon": get_polygon_global_news,
        "alpha_vantage": get_alpha_vantage_global_news,
        "openai": get_global_news_openai,
        "local": get_reddit_global_news,
    },
    "get_insider_sentiment": {
        "local": get_finnhub_company_insider_sentiment
    },
    "get_insider_transactions": {
        "alpha_vantage": get_alpha_vantage_insider_transactions,
        "yfinance": get_yfinance_insider_transactions,
        "local": get_finnhub_company_insider_transactions,
    },
    # social_sentiment
    "get_social_sentiment": {
        "stocktwits": get_social_sentiment_stocktwits,      # Free, no API key needed
        "stockgeist": get_social_sentiment_stockgeist,      # Free tier (10k credits/mo), requires STOCKGEIST_API_KEY
        # "apewisdom" disabled — unreliable data source, not used in backtests
        "finnhub": get_social_sentiment_finnhub,            # Requires FINNHUB_API_KEY (premium)
        "reddit": get_social_sentiment_reddit,              # Requires REDDIT_CLIENT_ID + REDDIT_CLIENT_SECRET
        "aggregated": get_social_sentiment_aggregated,      # Combines all sources (excluding ApeWisdom)
    },
}

def _deduplicate_articles(articles: list, threshold: float = 0.7) -> list:
    """Remove near-duplicate news articles using title similarity.

    Uses Jaccard similarity on title words to detect duplicates.
    When duplicates are found, keeps the article with the longest summary.

    Args:
        articles: List of article dicts (must have 'title' key).
        threshold: Jaccard similarity threshold (0-1). Articles above
                   this are considered duplicates. Default 0.7.

    Returns:
        Deduplicated list of articles.
    """
    if not articles or len(articles) <= 1:
        return articles

    def _title_words(title: str) -> set:
        """Extract lowercase word set from title, ignoring short words."""
        return {w.lower().strip(".,!?;:'\"()[]") for w in title.split() if len(w) > 2}

    def _jaccard(set_a: set, set_b: set) -> float:
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a & set_b)
        union = len(set_a | set_b)
        return intersection / union if union > 0 else 0.0

    # Build word sets for all titles
    title_sets = []
    for article in articles:
        title = article.get("title", "")
        title_sets.append(_title_words(title))

    # Track which articles are kept (not marked as duplicates)
    kept = [True] * len(articles)

    for i in range(len(articles)):
        if not kept[i]:
            continue
        for j in range(i + 1, len(articles)):
            if not kept[j]:
                continue
            sim = _jaccard(title_sets[i], title_sets[j])
            if sim >= threshold:
                # Keep the article with the longer summary
                summary_i = len(article.get("summary", "") if (article := articles[i]) else "")
                summary_j = len(article.get("summary", "") if (article := articles[j]) else "")
                if summary_j > summary_i:
                    kept[i] = False
                    break  # i is removed, no need to compare further
                else:
                    kept[j] = False

    result = [a for a, k in zip(articles, kept) if k]
    removed = len(articles) - len(result)
    if removed > 0:
        print(f"DEDUP: Removed {removed} duplicate article(s) ({len(articles)} -> {len(result)})")
    return result


def _deduplicate_news_result(result):
    """Apply deduplication to a news result (dict with 'feed' key or string).

    Handles both single-vendor results (dict) and multi-vendor concatenated results (string).
    """
    if isinstance(result, dict) and "feed" in result:
        result["feed"] = _deduplicate_articles(result["feed"])
        result["items"] = str(len(result["feed"]))
        return result
    elif isinstance(result, str):
        # Try to parse as JSON (multi-vendor results may be JSON strings)
        try:
            parsed = json.loads(result)
            if isinstance(parsed, dict) and "feed" in parsed:
                parsed["feed"] = _deduplicate_articles(parsed["feed"])
                parsed["items"] = str(len(parsed["feed"]))
                return parsed
        except (json.JSONDecodeError, ValueError):
            pass
    return result


def get_category_for_method(method: str) -> str:
    """Get the category that contains the specified method."""
    for category, info in TOOLS_CATEGORIES.items():
        if method in info["tools"]:
            return category
    raise ValueError(f"Method '{method}' not found in any category")

def get_vendor(category: str, method: str = None) -> str:
    """Get the configured vendor for a data category or specific tool method.
    Tool-level configuration takes precedence over category-level.
    """
    config = get_config()

    # Check tool-level configuration first (if method provided)
    if method:
        tool_vendors = config.get("tool_vendors", {})
        if method in tool_vendors:
            return tool_vendors[method]

    # Fall back to category-level configuration
    return config.get("data_vendors", {}).get(category, "default")

def route_to_vendor(method: str, *args, **kwargs):
    """Route method calls to appropriate vendor implementation with fallback support."""
    category = get_category_for_method(method)
    vendor_config = get_vendor(category, method)

    # Handle comma-separated vendors
    primary_vendors = [v.strip() for v in vendor_config.split(',')]

    if method not in VENDOR_METHODS:
        raise ValueError(f"Method '{method}' not supported")

    # Get all available vendors for this method for fallback
    all_available_vendors = list(VENDOR_METHODS[method].keys())
    
    # Create fallback vendor list: primary vendors first, then remaining vendors as fallbacks
    fallback_vendors = primary_vendors.copy()
    for vendor in all_available_vendors:
        if vendor not in fallback_vendors:
            fallback_vendors.append(vendor)

    # Debug: Print fallback ordering
    primary_str = " → ".join(primary_vendors)
    fallback_str = " → ".join(fallback_vendors)
    print(f"DEBUG: {method} - Primary: [{primary_str}] | Full fallback order: [{fallback_str}]")

    # Track results and execution state
    results = []
    vendor_attempt_count = 0
    any_primary_vendor_attempted = False
    successful_vendor = None

    for vendor in fallback_vendors:
        if vendor not in VENDOR_METHODS[method]:
            if vendor in primary_vendors:
                print(f"INFO: Vendor '{vendor}' not supported for method '{method}', falling back to next vendor")
            continue

        vendor_impl = VENDOR_METHODS[method][vendor]
        is_primary_vendor = vendor in primary_vendors
        vendor_attempt_count += 1

        # Track if we attempted any primary vendor
        if is_primary_vendor:
            any_primary_vendor_attempted = True

        # Multi-vendor: skip fallback vendors if primaries already produced results
        if not is_primary_vendor and results and len(primary_vendors) > 1:
            print(f"DEBUG: Skipping fallback vendor '{vendor}' - already have {len(results)} result(s) from primaries")
            vendor_attempt_count -= 1
            break

        # Debug: Print current attempt
        vendor_type = "PRIMARY" if is_primary_vendor else "FALLBACK"
        print(f"DEBUG: Attempting {vendor_type} vendor '{vendor}' for {method} (attempt #{vendor_attempt_count})")

        # Handle list of methods for a vendor
        if isinstance(vendor_impl, list):
            vendor_methods = [(impl, vendor) for impl in vendor_impl]
            print(f"DEBUG: Vendor '{vendor}' has multiple implementations: {len(vendor_methods)} functions")
        else:
            vendor_methods = [(vendor_impl, vendor)]

        # Run methods for this vendor with retry logic
        vendor_results = []
        for impl_func, vendor_name in vendor_methods:
            max_retries = 3
            base_delay = 1.0
            last_error = None

            for retry_attempt in range(max_retries):
                try:
                    if retry_attempt > 0:
                        print(f"RETRY: Attempt {retry_attempt + 1}/{max_retries} "
                              f"for {impl_func.__name__}")
                    else:
                        print(f"DEBUG: Calling {impl_func.__name__} "
                              f"from vendor '{vendor_name}'...")

                    result = impl_func(*args, **kwargs)
                    vendor_results.append(result)
                    print(f"SUCCESS: {impl_func.__name__} from vendor "
                          f"'{vendor_name}' completed successfully")
                    last_error = None
                    break  # Success, exit retry loop

                except (AlphaVantageRateLimitError, RateLimitError, PolygonRateLimitError) as e:
                    print(f"RATE_LIMIT: {type(e).__name__} exceeded, falling back to next vendor.")
                    print(f"DEBUG: Rate limit details: {e}")
                    last_error = e
                    break  # Don't retry rate limits, move to next vendor

                except (ConnectionError, TimeoutError, OSError,
                        APIConnectionError, APITimeoutError) as e:
                    # Transient errors - retry with backoff
                    last_error = e
                    if retry_attempt < max_retries - 1:
                        delay = base_delay * (2 ** retry_attempt)
                        print(f"TRANSIENT_ERROR: {type(e).__name__} - {e}")
                        print(f"RETRY: Waiting {delay}s before retry...")
                        time.sleep(delay)
                    else:
                        print(f"FAILED: {impl_func.__name__} from vendor "
                              f"'{vendor_name}' failed after {max_retries} "
                              f"attempts: {e}")

                except Exception as e:
                    # Non-transient errors - don't retry
                    last_error = e
                    print(f"FAILED: {impl_func.__name__} from vendor "
                          f"'{vendor_name}' failed: {type(e).__name__}: {e}")
                    break

            if last_error is not None:
                continue  # Move to next implementation

        # Add this vendor's results
        if vendor_results:
            results.extend(vendor_results)
            successful_vendor = vendor
            result_summary = f"Got {len(vendor_results)} result(s)"
            print(f"SUCCESS: Vendor '{vendor}' succeeded - {result_summary}")

            # Stopping logic:
            # - Single-vendor config: stop after first success
            # - Multi-vendor config: stop once a fallback (non-primary) vendor succeeds
            if len(primary_vendors) == 1:
                print(f"DEBUG: Stopping after successful vendor '{vendor}' (single-vendor config)")
                break
            elif not is_primary_vendor:
                print(f"DEBUG: Stopping after fallback vendor '{vendor}' succeeded")
                break
        else:
            print(f"FAILED: Vendor '{vendor}' produced no results")

    # Final result summary
    if not results:
        print(f"FAILURE: All {vendor_attempt_count} vendor attempts failed for method '{method}'")
        raise RuntimeError(f"All vendor implementations failed for method '{method}'")
    else:
        print(f"FINAL: Method '{method}' completed with {len(results)} result(s) from {vendor_attempt_count} vendor attempt(s)")

    # Apply deduplication for news methods
    if method in ("get_news", "get_global_news"):
        results = [_deduplicate_news_result(r) for r in results]

    # Return single result if only one, otherwise concatenate as string
    if len(results) == 1:
        return results[0]
    else:
        # Convert all results to strings and concatenate
        return '\n'.join(str(result) for result in results)
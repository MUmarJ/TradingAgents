# TradingAgents/dataflows/polygon_common.py
"""
Polygon.io (Massive) Common Utilities

Shared infrastructure for the Polygon vendor module:
- API key retrieval and client factory
- Rate limiting (5 req/min free tier)
- Disk caching (24h TTL)
"""

import os
import time
import json
import hashlib
import threading
from datetime import datetime, timedelta
from typing import Optional, Any

from .config import get_config

# Try polygon (pre-rebrand) then massive (post-rebrand)
try:
    from polygon import RESTClient
except ImportError:
    try:
        from massive import RESTClient
    except ImportError:
        RESTClient = None

# Rate limiting for free tier: 5 requests per minute
_rate_lock = threading.Lock()
_request_timestamps = []
RATE_LIMIT_PER_MINUTE = 5

# Cache settings
CACHE_EXPIRY_HOURS = 24


class PolygonRateLimitError(Exception):
    """Exception raised when Polygon.io API rate limit is exceeded."""
    pass


def get_api_key() -> str:
    """Retrieve the API key for Polygon.io from environment variables."""
    api_key = os.getenv("POLYGON_API_KEY")
    if not api_key:
        raise ValueError(
            "POLYGON_API_KEY environment variable is not set. "
            "Get a free API key at https://polygon.io/"
        )
    return api_key


def get_client() -> "RESTClient":
    """Get a configured Polygon RESTClient instance.

    Returns:
        RESTClient configured with the user's API key.

    Raises:
        ImportError: If neither polygon-api-client nor massive package is installed.
        ValueError: If POLYGON_API_KEY is not set.
    """
    if RESTClient is None:
        raise ImportError(
            "Polygon.io client not installed. Run: pip install polygon-api-client"
        )
    return RESTClient(api_key=get_api_key())


def enforce_rate_limit():
    """Enforce 5-requests-per-minute rate limit for free tier.

    Blocks the current thread if the rate limit would be exceeded.
    Thread-safe via lock.
    """
    with _rate_lock:
        now = time.time()
        # Remove timestamps older than 60 seconds
        _request_timestamps[:] = [t for t in _request_timestamps if now - t < 60]

        if len(_request_timestamps) >= RATE_LIMIT_PER_MINUTE:
            # Sleep until oldest request expires
            sleep_time = 60 - (now - _request_timestamps[0]) + 0.1
            if sleep_time > 0:
                print(f"POLYGON: Rate limit reached, sleeping {sleep_time:.1f}s")
                time.sleep(sleep_time)

        _request_timestamps.append(time.time())


# =============================================================================
# Disk cache helpers
# =============================================================================

def _get_cache_dir() -> str:
    """Get the cache directory for Polygon data."""
    config = get_config()
    cache_dir = os.path.join(config.get("data_cache_dir", "./data_cache"), "polygon")
    os.makedirs(cache_dir, exist_ok=True)
    return cache_dir


def _get_cache_key(endpoint: str, params_str: str) -> str:
    """Generate a unique cache key."""
    key_str = f"polygon_{endpoint}_{params_str}"
    return hashlib.md5(key_str.encode()).hexdigest()


def read_cache(cache_key: str) -> Optional[Any]:
    """Read data from cache if it exists and is not expired."""
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


def write_cache(cache_key: str, data: Any) -> None:
    """Write data to cache."""
    cache_dir = _get_cache_dir()
    cache_file = os.path.join(cache_dir, f"{cache_key}.json")

    cached = {
        "cached_at": datetime.now().isoformat(),
        "data": data,
    }

    with open(cache_file, "w") as f:
        json.dump(cached, f, indent=2, default=str)

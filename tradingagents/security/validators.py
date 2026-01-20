"""
Input validation and sanitization functions for security.
"""

import re
from datetime import datetime
from typing import Optional
from urllib.parse import urlparse


def validate_ticker(ticker: str, max_length: int = 10) -> str:
    """
    Validate and sanitize stock ticker symbol.

    Args:
        ticker: Raw ticker symbol input
        max_length: Maximum allowed length (default: 10)

    Returns:
        Sanitized ticker symbol in uppercase

    Raises:
        ValueError: If ticker is invalid or contains dangerous characters
    """
    if not ticker or not isinstance(ticker, str):
        raise ValueError("Ticker symbol is required")

    # Convert to uppercase and strip whitespace
    ticker = ticker.strip().upper()

    # Check length
    if len(ticker) > max_length:
        raise ValueError(f"Ticker symbol too long (max {max_length} characters)")

    # Block path traversal attempts
    if ".." in ticker or "/" in ticker or "\\" in ticker:
        raise ValueError("Invalid ticker symbol: contains path traversal characters")

    # Allow only alphanumeric, dots (for ETFs like BRK.B), and hyphens
    if not re.match(r"^[A-Z0-9.\-]+$", ticker):
        raise ValueError("Invalid ticker symbol: contains invalid characters")

    return ticker


def validate_date(
    date_str: str,
    allow_future: bool = False,
    min_year: int = 1900,
) -> datetime:
    """
    Validate and parse date string.

    Args:
        date_str: Date string in YYYY-MM-DD format
        allow_future: Whether to allow future dates
        min_year: Minimum allowed year

    Returns:
        Parsed datetime object

    Raises:
        ValueError: If date is invalid or out of range
    """
    if not date_str or not isinstance(date_str, str):
        raise ValueError("Date is required")

    date_str = date_str.strip()

    # Block path traversal
    if ".." in date_str or "/" in date_str or "\\" in date_str:
        raise ValueError("Invalid date: contains path traversal characters")

    # Parse date
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Invalid date format. Expected YYYY-MM-DD")

    # Check year range
    if parsed.year < min_year:
        raise ValueError(f"Date too old (minimum year: {min_year})")

    # Check future date
    if not allow_future and parsed > datetime.now():
        raise ValueError("Future dates are not allowed")

    return parsed


def sanitize_path_component(value: str, max_length: int = 50) -> str:
    """
    Sanitize a value for use in file paths.

    Removes dangerous characters and path traversal sequences.

    Args:
        value: Raw string to sanitize
        max_length: Maximum allowed length

    Returns:
        Sanitized string safe for path construction

    Raises:
        ValueError: If value is empty or invalid
    """
    if not value or not isinstance(value, str):
        raise ValueError("Path component is required")

    value = value.strip()

    # Remove path traversal sequences
    value = value.replace("..", "")
    value = value.replace("/", "")
    value = value.replace("\\", "")

    # Remove null bytes
    value = value.replace("\x00", "")

    # Keep only alphanumeric, dashes, underscores, and dots
    value = re.sub(r"[^a-zA-Z0-9._-]", "", value)

    # Enforce length limit
    if len(value) > max_length:
        value = value[:max_length]

    if not value:
        raise ValueError("Path component is empty after sanitization")

    return value


def validate_api_key(
    key: Optional[str],
    key_name: str = "API key",
    min_length: int = 10,
) -> str:
    """
    Validate API key format.

    Args:
        key: API key to validate
        key_name: Name of the key for error messages
        min_length: Minimum expected key length

    Returns:
        Validated API key

    Raises:
        ValueError: If key is missing or invalid
    """
    if not key:
        raise ValueError(f"{key_name} is required")

    key = key.strip()

    if " " in key:
        raise ValueError(f"{key_name} contains spaces")

    if len(key) < min_length:
        import warnings

        warnings.warn(
            f"{key_name} appears suspiciously short (length: {len(key)})",
            UserWarning,
        )

    return key


def validate_url(
    url: str,
    allowed_schemes: tuple = ("http", "https"),
    block_private: bool = True,
) -> str:
    """
    Validate URL for SSRF protection.

    Args:
        url: URL to validate
        allowed_schemes: Tuple of allowed URL schemes
        block_private: Block private/internal IP addresses

    Returns:
        Validated URL

    Raises:
        ValueError: If URL is invalid or potentially dangerous
    """
    if not url or not isinstance(url, str):
        raise ValueError("URL is required")

    url = url.strip()

    try:
        parsed = urlparse(url)
    except Exception:
        raise ValueError("Invalid URL format")

    # Check scheme
    if parsed.scheme not in allowed_schemes:
        raise ValueError(f"URL scheme must be one of: {allowed_schemes}")

    # Check for hostname
    if not parsed.netloc:
        raise ValueError("URL must have a hostname")

    # Block private IPs if requested
    if block_private:
        hostname = parsed.hostname or ""
        hostname_lower = hostname.lower()

        # Block localhost
        if hostname_lower in ("localhost", "127.0.0.1", "::1"):
            raise ValueError("localhost URLs are not allowed")

        # Block private IP ranges (simplified check)
        if hostname.startswith(("10.", "192.168.", "172.16.", "172.17.")):
            raise ValueError("Private IP addresses are not allowed")

    return url

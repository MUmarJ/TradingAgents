"""
Confidence-scaled position sizing.

Scales position size by decision confidence so that high-confidence
decisions get larger allocations and low-confidence decisions get smaller ones.
"""

from typing import Optional


def confidence_scaled_position(
    portfolio_value: float,
    confidence: Optional[float],
    max_fraction: float = 0.05,
) -> float:
    """Scale position size by confidence.

    confidence=1.0 -> max_fraction of portfolio
    confidence=0.25 -> 25% of max_fraction of portfolio

    Args:
        portfolio_value: Total portfolio value
        confidence: Confidence score (0.0-1.0), defaults to 0.5 if None
        max_fraction: Maximum fraction of portfolio per trade (default 5%)

    Returns:
        Position size in dollars
    """
    if confidence is None:
        confidence = 0.5  # default to medium confidence

    # Clamp to valid range
    confidence = max(0.0, min(1.0, confidence))

    return portfolio_value * max_fraction * confidence


def fixed_position(amount: float = 10000.0) -> float:
    """Return a fixed position size (baseline comparison).

    Args:
        amount: Fixed dollar amount per trade

    Returns:
        Position size in dollars
    """
    return amount

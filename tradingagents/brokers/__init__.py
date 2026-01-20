"""
Broker integrations for TradingAgents.

This module provides broker interfaces for paper and live trading.
"""

from .base import (
    BaseBroker,
    BrokerOrder,
    BrokerPosition,
    BrokerAccount,
    OrderSide,
    OrderType,
    OrderStatus,
    BrokerError,
    BrokerConnectionError,
    OrderError,
    InsufficientFundsError,
)

__all__ = [
    "BaseBroker",
    "BrokerOrder",
    "BrokerPosition",
    "BrokerAccount",
    "OrderSide",
    "OrderType",
    "OrderStatus",
    "BrokerError",
    "BrokerConnectionError",
    "OrderError",
    "InsufficientFundsError",
]

# Conditionally import Alpaca broker if available
ALPACA_AVAILABLE = False
try:
    from .alpaca_broker import AlpacaBroker

    ALPACA_AVAILABLE = True
    __all__.append("AlpacaBroker")
except ImportError:
    pass

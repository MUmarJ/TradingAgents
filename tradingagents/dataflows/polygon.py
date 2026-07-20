# TradingAgents/dataflows/polygon.py
"""
Polygon.io Data Vendor Module

Re-exports all Polygon vendor functions from specialized sub-modules.
Follows the same pattern as alpha_vantage.py.

Available on free tier:
- Stock OHLCV data (aggregate bars)
- News (ticker + global)
- Technical indicators (SMA, EMA, RSI, MACD)

NOT available on free tier:
- Fundamentals (balance sheet, income statement, cash flow) - requires $199/mo
- Insider transactions
"""

from .polygon_stock import get_stock
from .polygon_news import get_news, get_global_news
from .polygon_indicator import get_indicator

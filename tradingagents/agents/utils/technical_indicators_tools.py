from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor

# Normalize common indicator name variants to internal names.
# Handles case mismatches and alternative names from LLM tool calls.
INDICATOR_ALIASES = {
    "RSI": "rsi",
    "MACD": "macd",
    "SMA": "close_50_sma",
    "SMA_50": "close_50_sma",
    "SMA_200": "close_200_sma",
    "sma_50": "close_50_sma",
    "sma_200": "close_200_sma",
    "bollinger": "boll",
    "bollinger_bands": "boll",
    "Bollinger": "boll",
    "ATR": "atr",
    "VWMA": "vwma",
    "MFI": "mfi",
}


def _normalize_indicator(name: str) -> str:
    """Normalize indicator name to internal format."""
    return INDICATOR_ALIASES.get(name, INDICATOR_ALIASES.get(name.upper(), name.lower()))


@tool
def get_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 30,
) -> str:
    """
    Retrieve technical indicators for a given ticker symbol.
    Uses the configured technical_indicators vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        indicator (str): Technical indicator to get the analysis and report of
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 30
    Returns:
        str: A formatted dataframe containing the technical indicators for the specified ticker symbol and indicator.
    """
    indicator = _normalize_indicator(indicator)
    return route_to_vendor("get_indicators", symbol, indicator, curr_date, look_back_days)
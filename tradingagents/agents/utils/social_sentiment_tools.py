from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor


@tool
def get_social_sentiment(
    ticker: Annotated[str, "Ticker symbol"],
    start_date: Annotated[str, "Start date in yyyy-mm-dd format"],
    end_date: Annotated[str, "End date in yyyy-mm-dd format"],
    limit: Annotated[int, "Maximum number of items to return"] = 50,
) -> str:
    """
    Retrieve social media sentiment data for a given ticker symbol.

    Aggregates sentiment from multiple sources:
    - Stocktwits: Dedicated stock social platform with sentiment labels
    - Finnhub: Social sentiment from Reddit and Twitter (requires API key)
    - Reddit PRAW: Direct Reddit access (requires API credentials)

    Args:
        ticker (str): Ticker symbol (e.g., AAPL, TSLA)
        start_date (str): Start date in yyyy-mm-dd format
        end_date (str): End date in yyyy-mm-dd format
        limit (int): Maximum number of items to return (default 50)

    Returns:
        str: A comprehensive social sentiment report with data from all available sources
    """
    return route_to_vendor("get_social_sentiment", ticker, start_date, end_date, limit)

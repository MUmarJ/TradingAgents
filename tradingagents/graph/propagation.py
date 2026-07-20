# TradingAgents/graph/propagation.py

from typing import Dict, Any
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)


class Propagator:
    """Handles state initialization and propagation through the graph."""

    def __init__(self, max_recur_limit=100):
        """Initialize with configuration parameters."""
        self.max_recur_limit = max_recur_limit

    def create_initial_state(
        self,
        company_name: str,
        trade_date: str,
        news_lookback_days: int = 7,
        news_article_limit: int = 50,
    ) -> Dict[str, Any]:
        """Create the initial state for the agent graph.

        Args:
            company_name: Ticker symbol of the company to analyze.
            trade_date: Date of analysis in YYYY-MM-DD format.
            news_lookback_days: Number of days to look back for news analysis (default 7).
            news_article_limit: Maximum number of news articles to fetch (default 50).
        """
        return {
            "messages": [("human", company_name)],
            "company_of_interest": company_name,
            "trade_date": str(trade_date),
            "news_lookback_days": news_lookback_days,
            "news_article_limit": news_article_limit,
            "investment_debate_state": InvestDebateState(
                {
                    "history": "",
                    "bull_history": "",
                    "bear_history": "",
                    "current_response": "",
                    "judge_decision": "",
                    "count": 0,
                }
            ),
            "risk_debate_state": RiskDebateState(
                {
                    "history": "",
                    "risky_history": "",
                    "safe_history": "",
                    "neutral_history": "",
                    "latest_speaker": "",
                    "current_risky_response": "",
                    "current_safe_response": "",
                    "current_neutral_response": "",
                    "judge_decision": "",
                    "count": 0,
                }
            ),
            "market_report": "",
            "fundamentals_report": "",
            "sentiment_report": "",
            "news_report": "",
        }

    def get_graph_args(self) -> Dict[str, Any]:
        """Get arguments for the graph invocation."""
        return {
            "stream_mode": "values",
            "config": {"recursion_limit": self.max_recur_limit},
        }

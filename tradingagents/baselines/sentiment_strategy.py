"""Sentiment-only trading strategy using FinBERT/DeBERTa.

Makes BUY/SELL/HOLD decisions based purely on aggregated news sentiment
from a specialized HuggingFace model. Zero API cost, deterministic output.

Uses the same cached datasets as SingleAgentBaseline for fair comparison.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, Optional

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.models.sentiment import (
    FinancialSentimentModel,
    AggregatedSentiment,
    SENTIMENT_MODELS,
)
from tradingagents.models.data_parsers import parse_news_articles


class SentimentStrategy:
    """Trading strategy based on FinBERT/DeBERTa news sentiment analysis.

    Deterministic: same input always produces the same output.
    Free: runs locally on CPU, no API calls.
    """

    # Decision thresholds
    BUY_THRESHOLD = 0.15
    SELL_THRESHOLD = -0.15

    def __init__(self, model_name: str = "deberta-finance", config: Dict = None):
        if model_name not in SENTIMENT_MODELS:
            raise ValueError(
                f"Unknown sentiment model: {model_name}. "
                f"Supported: {list(SENTIMENT_MODELS.keys())}"
            )
        self.config = config or DEFAULT_CONFIG
        self.model_name = model_name
        self.sentiment_model = FinancialSentimentModel(model_name)

    def _dataset_cache_path(self, ticker: str, trade_date: str) -> Path:
        """Return path for cached dataset (same as SingleAgentBaseline)."""
        results_dir = self.config.get("results_dir", "./results")
        return (
            Path(results_dir) / "datasets" / ticker / trade_date
            / f"{ticker}_{trade_date}_raw_dataset.json"
        )

    def _load_cached_dataset(self, ticker: str, trade_date: str) -> Optional[Dict[str, str]]:
        """Load cached raw data. Returns None if not cached."""
        path = self._dataset_cache_path(ticker, trade_date)
        legacy_path = path.parent / "dataset.json"

        for candidate in [path, legacy_path]:
            if candidate.exists():
                try:
                    with open(candidate) as f:
                        data = json.load(f)
                    if "news_data" in data:
                        return data
                except (json.JSONDecodeError, KeyError):
                    pass
        return None

    def _make_decision(
        self,
        ticker_sentiment: AggregatedSentiment,
        global_sentiment: AggregatedSentiment,
    ) -> tuple:
        """Rule-based decision from sentiment scores.

        Uses ticker-specific sentiment as primary signal with global sentiment
        as a confirming/opposing filter.

        Returns (decision, confidence) tuple.
        """
        score = ticker_sentiment.weighted_score
        global_score = global_sentiment.avg_score if global_sentiment.num_articles > 0 else 0.0

        if score > self.BUY_THRESHOLD and global_score >= -0.1:
            decision = "BUY"
            confidence = min(0.5 + abs(score), 0.95)
        elif score < self.SELL_THRESHOLD and global_score <= 0.1:
            decision = "SELL"
            confidence = min(0.5 + abs(score), 0.95)
        else:
            decision = "HOLD"
            confidence = 0.3 + abs(score) * 0.3

        return decision, round(confidence, 2)

    def analyze(self, ticker: str, trade_date: str, **kwargs) -> Dict[str, Any]:
        """Run sentiment analysis on cached news data.

        Args:
            ticker: Stock ticker symbol.
            trade_date: Analysis date (YYYY-MM-DD).

        Returns:
            Dict compatible with evaluate_v2.py TradeOutcome contract:
            {decision, confidence, strategy, raw_response, input_tokens,
             output_tokens, llm_calls}
        """
        cached = self._load_cached_dataset(ticker, trade_date)
        if not cached:
            raise FileNotFoundError(
                f"No cached dataset for {ticker} {trade_date}. "
                f"Run a single-agent analysis first to populate the cache."
            )

        print(f"DATASET CACHE HIT: {ticker} {trade_date}", end=" | ")

        # Parse news articles from cached strings
        ticker_articles = parse_news_articles(cached.get("news_data", ""))
        global_articles = parse_news_articles(cached.get("global_news_data", ""))

        # Score articles with the sentiment model
        ticker_sentiments = self.sentiment_model.score_articles(ticker_articles)
        global_sentiments = self.sentiment_model.score_articles(global_articles)

        # Aggregate scores
        ticker_agg = self.sentiment_model.aggregate(ticker, trade_date, ticker_sentiments)
        global_agg = self.sentiment_model.aggregate("GLOBAL", trade_date, global_sentiments)

        # Make decision
        decision, confidence = self._make_decision(ticker_agg, global_agg)

        # Build raw response summary
        raw_response = (
            f"Sentiment Model: {self.model_name}\n"
            f"Ticker articles: {ticker_agg.num_articles} | "
            f"Avg score: {ticker_agg.avg_score:+.3f} | "
            f"Weighted: {ticker_agg.weighted_score:+.3f} | "
            f"Pos/Neg/Neu: {ticker_agg.positive_pct:.0%}/{ticker_agg.negative_pct:.0%}/{ticker_agg.neutral_pct:.0%}\n"
            f"Global articles: {global_agg.num_articles} | "
            f"Avg score: {global_agg.avg_score:+.3f} | "
            f"Weighted: {global_agg.weighted_score:+.3f}\n"
            f"Decision: {decision} | Confidence: {confidence}"
        )

        return {
            "decision": decision,
            "confidence": confidence,
            "strategy": f"sentiment_{self.model_name}",
            "raw_response": raw_response,
            "input_tokens": 0,
            "output_tokens": 0,
            "llm_calls": 0,
        }

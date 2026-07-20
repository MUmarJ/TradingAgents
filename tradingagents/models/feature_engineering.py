"""Feature extraction from cached datasets for ML models.

Converts cached string data (OHLCV CSV, indicator text, sentiment scores)
into a flat numeric feature vector suitable for XGBoost/LightGBM.
"""

import re
from io import StringIO
from typing import Dict, List, Optional, Any

import pandas as pd
import numpy as np

from tradingagents.models.data_parsers import (
    parse_news_articles,
    extract_av_ticker_sentiment,
)
from tradingagents.models.sentiment import FinancialSentimentModel, AggregatedSentiment


def parse_ohlcv_csv(csv_str: str) -> pd.DataFrame:
    """Parse OHLCV from cached CSV string into DataFrame."""
    df = pd.read_csv(StringIO(csv_str))
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    df = df.set_index('timestamp').sort_index()
    # Ensure numeric
    for col in ['open', 'high', 'low', 'close', 'volume']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    return df


def parse_indicators(indicators_str: str) -> Dict[str, pd.Series]:
    """Parse indicator sections from cached text format.

    Format:
        === RSI ===
        ## RSI values from 2025-01-30 to 2025-03-31:

        2025-01-30: 55.2265
        2025-01-31: 52.3409
        ...
    """
    indicators = {}
    sections = re.split(r'=== (.+?) ===', indicators_str)
    # sections[0] is before first header (empty), then alternating name/content
    for i in range(1, len(sections), 2):
        name = sections[i].strip()
        content = sections[i + 1] if i + 1 < len(sections) else ""
        dates = []
        values = []
        for line in content.strip().split('\n'):
            match = re.match(r'(\d{4}-\d{2}-\d{2}):\s*([-\d.]+)', line.strip())
            if match:
                dates.append(pd.Timestamp(match.group(1)))
                values.append(float(match.group(2)))
        if dates:
            indicators[name] = pd.Series(values, index=dates).sort_index()
    return indicators


class FeatureExtractor:
    """Extract a flat feature vector from a cached dataset snapshot."""

    def __init__(
        self,
        sentiment_model: Optional[FinancialSentimentModel] = None,
        selected_features: Optional[List[str]] = None,
    ):
        self._sentiment_model = sentiment_model
        self._selected_features = set(selected_features) if selected_features else None

    def extract(
        self,
        cached_dataset: Dict[str, str],
        sentiment: Optional[AggregatedSentiment] = None,
    ) -> Dict[str, float]:
        """Extract all features from a single cached dataset.

        Returns a dict of feature_name -> float value.
        """
        features = {}

        # 1. OHLCV features from ticker
        try:
            ohlcv = parse_ohlcv_csv(cached_dataset["market_data"])
            features.update(self._ohlcv_features(ohlcv, prefix=""))
        except Exception:
            pass

        # 2. Technical indicators
        try:
            indicators = parse_indicators(cached_dataset.get("indicators_data", ""))
            features.update(self._indicator_features(indicators, prefix=""))
        except Exception:
            pass

        # 3. SPY features (market context)
        try:
            spy = parse_ohlcv_csv(cached_dataset["spy_market_data"])
            features.update(self._ohlcv_features(spy, prefix="spy_"))
        except Exception:
            pass

        # 4. SPY indicators
        try:
            spy_ind = parse_indicators(cached_dataset.get("spy_indicators", ""))
            features.update(self._indicator_features(spy_ind, prefix="spy_"))
        except Exception:
            pass

        # 5. Sector ETF features
        try:
            sector = parse_ohlcv_csv(cached_dataset["sector_market_data"])
            features.update(self._ohlcv_features(sector, prefix="sector_"))
        except Exception:
            pass

        # 6. Relative features (ticker vs SPY, ticker vs sector)
        try:
            ohlcv = parse_ohlcv_csv(cached_dataset["market_data"])
            spy = parse_ohlcv_csv(cached_dataset["spy_market_data"])
            features.update(self._relative_features(ohlcv, spy, prefix="vs_spy"))
        except Exception:
            pass

        try:
            ohlcv = parse_ohlcv_csv(cached_dataset["market_data"])
            sector = parse_ohlcv_csv(cached_dataset["sector_market_data"])
            features.update(self._relative_features(ohlcv, sector, prefix="vs_sector"))
        except Exception:
            pass

        # 7. Sentiment features (from Phase 1 model or pre-computed)
        if sentiment:
            features.update(self._sentiment_features(sentiment))
        elif self._sentiment_model:
            try:
                articles = parse_news_articles(cached_dataset.get("news_data", ""))
                sentiments = self._sentiment_model.score_articles(articles)
                ticker = cached_dataset.get("ticker", "UNK")
                date = cached_dataset.get("trade_date", "")
                agg = self._sentiment_model.aggregate(ticker, date, sentiments)
                features.update(self._sentiment_features(agg))
            except Exception:
                pass

        # 8. Alpha Vantage pre-computed ticker-specific sentiment
        ticker = cached_dataset.get("ticker", "")
        news_str = cached_dataset.get("news_data", "")
        if ticker and news_str:
            try:
                av_sent = extract_av_ticker_sentiment(news_str, ticker)
                features.update(self._av_sentiment_features(av_sent))
            except Exception:
                pass

        # Also extract from global_news_data if available
        global_news_str = cached_dataset.get("global_news_data", "")
        if ticker and global_news_str:
            try:
                av_global = extract_av_ticker_sentiment(global_news_str, ticker)
                features.update(self._av_sentiment_features(av_global, prefix="global_"))
            except Exception:
                pass

        # Apply feature selection if configured
        if self._selected_features is not None:
            features = {k: v for k, v in features.items() if k in self._selected_features}

        return features

    def _ohlcv_features(self, df: pd.DataFrame, prefix: str = "") -> Dict[str, float]:
        """Derive price, volume, and volatility features from OHLCV."""
        features = {}
        if len(df) < 2:
            return features

        close = df["close"]
        volume = df.get("volume", pd.Series(dtype=float))

        # Returns at multiple lookback windows
        for n in [1, 3, 5, 10, 20]:
            if len(close) > n:
                ret = (close.iloc[-1] / close.iloc[-n] - 1) * 100
                features[f"{prefix}return_{n}d"] = ret

        # Realized volatility
        pct = close.pct_change().dropna()
        if len(pct) >= 5:
            features[f"{prefix}vol_5d"] = pct.tail(5).std() * 100
        if len(pct) >= 20:
            features[f"{prefix}vol_20d"] = pct.tail(20).std() * 100

        # Volume features
        if len(volume) >= 20 and volume.tail(20).mean() > 0:
            features[f"{prefix}vol_ratio_5d"] = (
                volume.tail(5).mean() / volume.tail(20).mean()
            )

        # Overnight gap (last day)
        if len(df) >= 2 and "open" in df.columns:
            features[f"{prefix}gap"] = (
                (df["open"].iloc[-1] / close.iloc[-2] - 1) * 100
            )

        # High-low range
        if len(df) >= 5:
            features[f"{prefix}range_5d"] = (
                (df["high"].tail(5).max() - df["low"].tail(5).min())
                / close.iloc[-1] * 100
            )

        # Price relative to recent range
        if len(df) >= 20:
            h20 = df["high"].tail(20).max()
            l20 = df["low"].tail(20).min()
            if h20 > l20:
                features[f"{prefix}pct_range_20d"] = (
                    (close.iloc[-1] - l20) / (h20 - l20)
                )

        return features

    def _indicator_features(
        self, indicators: Dict[str, pd.Series], prefix: str = ""
    ) -> Dict[str, float]:
        """Extract latest value and recent delta for each indicator."""
        features = {}
        for name, series in indicators.items():
            safe_name = name.lower().replace(" ", "_")
            if len(series) > 0:
                features[f"{prefix}ind_{safe_name}"] = series.iloc[-1]
                if len(series) >= 5:
                    features[f"{prefix}ind_{safe_name}_delta5"] = (
                        series.iloc[-1] - series.iloc[-5]
                    )

        return features

    def _relative_features(
        self, ticker_df: pd.DataFrame, benchmark_df: pd.DataFrame, prefix: str
    ) -> Dict[str, float]:
        """Compute ticker-relative-to-benchmark features."""
        features = {}
        tc = ticker_df["close"]
        bc = benchmark_df["close"]

        # Align on common dates
        common = tc.index.intersection(bc.index)
        if len(common) < 5:
            return features

        tc = tc.loc[common]
        bc = bc.loc[common]

        for n in [5, 10, 20]:
            if len(tc) > n:
                t_ret = (tc.iloc[-1] / tc.iloc[-n] - 1) * 100
                b_ret = (bc.iloc[-1] / bc.iloc[-n] - 1) * 100
                features[f"{prefix}_excess_{n}d"] = t_ret - b_ret

        # Correlation (20-day rolling)
        if len(tc) >= 20:
            t_pct = tc.pct_change().dropna()
            b_pct = bc.pct_change().dropna()
            common_pct = t_pct.index.intersection(b_pct.index)
            if len(common_pct) >= 10:
                features[f"{prefix}_corr_20d"] = (
                    t_pct.loc[common_pct].tail(20).corr(b_pct.loc[common_pct].tail(20))
                )

        return features

    def _sentiment_features(self, agg: AggregatedSentiment) -> Dict[str, float]:
        """Convert aggregated sentiment to numeric features."""
        return {
            "sent_avg": agg.avg_score,
            "sent_weighted": agg.weighted_score,
            "sent_pos_pct": agg.positive_pct,
            "sent_neg_pct": agg.negative_pct,
            "sent_neutral_pct": agg.neutral_pct,
            "sent_n_articles": float(agg.num_articles),
        }

    def _av_sentiment_features(
        self, av_sent: Dict[str, Any], prefix: str = "av_"
    ) -> Dict[str, float]:
        """Convert AV pre-computed ticker sentiment to numeric features."""
        features = {
            f"{prefix}n_ticker_articles": float(av_sent.get("n_ticker_articles", 0)),
            f"{prefix}avg_ticker_sentiment": float(av_sent.get("avg_ticker_sentiment", 0.0)),
            f"{prefix}max_ticker_sentiment": float(av_sent.get("max_ticker_sentiment", 0.0)),
            f"{prefix}min_ticker_sentiment": float(av_sent.get("min_ticker_sentiment", 0.0)),
            f"{prefix}avg_relevance": float(av_sent.get("avg_relevance", 0.0)),
            f"{prefix}n_bearish": float(av_sent.get("n_bearish", 0)),
            f"{prefix}n_bullish": float(av_sent.get("n_bullish", 0)),
            f"{prefix}n_neutral": float(av_sent.get("n_neutral", 0)),
            f"{prefix}n_tech_articles": float(av_sent.get("n_tech_articles", 0)),
        }

        # Add topic-level sentiments (technology, earnings, financial_markets, etc.)
        for key, val in av_sent.items():
            if key.startswith("topic_") and isinstance(val, (int, float)):
                features[f"{prefix}{key}"] = float(val)

        return features

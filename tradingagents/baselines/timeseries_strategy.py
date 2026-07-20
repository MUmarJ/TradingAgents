"""Kronos time-series trading strategy using OHLCV price prediction.

Makes BUY/SELL/HOLD decisions based on Kronos foundation model predictions
of future price candles. Zero-shot (no training needed), zero API cost,
runs locally on CPU/MPS/CUDA.

Uses the same cached datasets as other strategies for fair comparison.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.models.timeseries import predict_direction


class TimeSeriesStrategy:
    """Trading strategy using Kronos time-series foundation model."""

    def __init__(
        self,
        model_size: str = "mini",
        pred_days: int = 3,
        sample_count: int = 20,
        temperature: float = 0.8,
        config: Dict = None,
    ):
        """Initialize Kronos strategy.

        Args:
            model_size: Kronos model size ('mini'=4M, 'small'=25M, 'base'=102M).
            pred_days: Number of days ahead to predict for decision.
            sample_count: Monte Carlo samples for stable predictions.
            temperature: Sampling temperature (lower = less random).
            config: Config dict with results_dir.
        """
        self.config = config or DEFAULT_CONFIG
        self.model_size = model_size
        self.pred_days = pred_days
        self.sample_count = sample_count
        self.temperature = temperature

    def _dataset_cache_path(self, ticker: str, trade_date: str) -> Path:
        results_dir = self.config.get("results_dir", "./results")
        return (
            Path(results_dir) / "datasets" / ticker / trade_date
            / f"{ticker}_{trade_date}_raw_dataset.json"
        )

    def _load_cached_dataset(self, ticker: str, trade_date: str) -> Optional[Dict]:
        path = self._dataset_cache_path(ticker, trade_date)
        legacy_path = path.parent / "dataset.json"
        for candidate in [path, legacy_path]:
            if candidate.exists():
                try:
                    with open(candidate) as f:
                        return json.load(f)
                except (json.JSONDecodeError, KeyError):
                    pass
        return None

    def analyze(self, ticker: str, trade_date: str, **kwargs) -> Dict[str, Any]:
        """Run Kronos time-series prediction on cached OHLCV data.

        Args:
            ticker: Stock ticker symbol.
            trade_date: Analysis date (YYYY-MM-DD).

        Returns:
            Dict compatible with evaluate_v2.py TradeOutcome contract.
        """
        cached = self._load_cached_dataset(ticker, trade_date)
        if not cached:
            raise FileNotFoundError(
                f"No cached dataset for {ticker} {trade_date}"
            )

        print(f"DATASET CACHE HIT: {ticker} {trade_date}", end=" | ")

        ohlcv_csv = cached.get("market_data", "")
        if not ohlcv_csv:
            return {
                "decision": "HOLD",
                "confidence": 0.3,
                "strategy": f"ts_kronos_{self.model_size}",
                "raw_response": "No OHLCV data in cached dataset",
                "input_tokens": 0,
                "output_tokens": 0,
                "llm_calls": 0,
            }

        prediction = predict_direction(
            ohlcv_csv=ohlcv_csv,
            trade_date=trade_date,
            model_size=self.model_size,
            pred_days=self.pred_days,
            sample_count=self.sample_count,
            temperature=self.temperature,
        )

        # Build summary
        days_str = " | ".join(
            f"d{d['day']}: {d['pct_from_current']:+.1f}%"
            for d in prediction["pred_days_detail"]
        )
        raw_response = (
            f"Kronos Model: {self.model_size} (pred_days={self.pred_days}, samples={self.sample_count})\n"
            f"Current close: ${prediction['current_close']:.2f}\n"
            f"Predicted 1d close: ${prediction['predicted_close_1d']:.2f} ({prediction['predicted_pct_1d']:+.2f}%)\n"
            f"Avg predicted move: {prediction['avg_predicted_pct']:+.2f}%\n"
            f"Up probability: {prediction['up_probability']:.4f}\n"
            f"Per-day: {days_str}\n"
            f"Decision: {prediction['decision']} | Confidence: {prediction['confidence']}"
        )

        if "fallback_reason" in prediction:
            raw_response += f"\nFallback: {prediction['fallback_reason']}"

        return {
            "decision": prediction["decision"],
            "confidence": prediction["confidence"],
            "strategy": f"ts_kronos_{self.model_size}",
            "raw_response": raw_response,
            "input_tokens": 0,
            "output_tokens": 0,
            "llm_calls": 0,
        }

"""XGBoost/LightGBM trading strategy using cached dataset features.

Trains a gradient boosting model on OHLCV + indicators + sentiment features
and uses it for BUY/SELL/HOLD predictions. Deterministic, zero API cost.

Walk-forward training: for each prediction date, trains only on data
from earlier dates to prevent look-ahead bias.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.models.feature_engineering import FeatureExtractor
from tradingagents.models.ml_trainer import MLTrainer
from tradingagents.models.sentiment import FinancialSentimentModel


class MLStrategy:
    """Trading strategy using XGBoost/LightGBM on structured features."""

    def __init__(
        self,
        model_type: str = "xgboost",
        include_sentiment: bool = True,
        config: Dict = None,
        selected_features: Optional[List[str]] = None,
    ):
        self.config = config or DEFAULT_CONFIG
        self.model_type = model_type
        self.include_sentiment = include_sentiment

        # Lazy-init sentiment model
        self._sentiment_model = None
        if include_sentiment:
            self._sentiment_model = FinancialSentimentModel("deberta-finance")

        self.feature_extractor = FeatureExtractor(
            sentiment_model=self._sentiment_model,
            selected_features=selected_features,
        )

        # Cache trained models by cutoff date
        self._model_cache: Dict[str, MLTrainer] = {}

    def _get_results_dir(self) -> str:
        return self.config.get("results_dir", "./results")

    def _get_available_tickers(self) -> List[str]:
        """Find all tickers with cached datasets."""
        datasets_dir = Path(self._get_results_dir()) / "datasets"
        if not datasets_dir.exists():
            return []
        return [
            d.name for d in datasets_dir.iterdir()
            if d.is_dir() and not d.name.startswith(".")
        ]

    def _dataset_cache_path(self, ticker: str, trade_date: str) -> Path:
        return (
            Path(self._get_results_dir()) / "datasets" / ticker / trade_date
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

    def _ensure_trained(self, trade_date: str) -> MLTrainer:
        """Train model on all available data before trade_date."""
        if trade_date in self._model_cache:
            return self._model_cache[trade_date]

        trainer = MLTrainer(self.model_type)
        tickers = self._get_available_tickers()

        df = trainer.build_training_set(
            results_dir=self._get_results_dir(),
            tickers=tickers,
            feature_extractor=self.feature_extractor,
            cutoff_date=trade_date,
        )

        if df.empty or len(df) < 5:
            # Not enough training data — fall back to simple momentum
            self._model_cache[trade_date] = None
            return None

        metrics = trainer.train(df)
        self._model_cache[trade_date] = trainer
        return trainer

    def analyze(self, ticker: str, trade_date: str, **kwargs) -> Dict[str, Any]:
        """Run ML prediction on cached data.

        Walk-forward: trains on all data before trade_date, then predicts.
        """
        cached = self._load_cached_dataset(ticker, trade_date)
        if not cached:
            raise FileNotFoundError(
                f"No cached dataset for {ticker} {trade_date}"
            )

        print(f"DATASET CACHE HIT: {ticker} {trade_date}", end=" | ")

        # Extract features for the prediction date
        features = self.feature_extractor.extract(cached)

        # Train model (walk-forward)
        trainer = self._ensure_trained(trade_date)

        if trainer is None:
            # Not enough training data — return HOLD
            return {
                "decision": "HOLD",
                "confidence": 0.3,
                "strategy": f"ml_{self.model_type}",
                "raw_response": "Insufficient training data (< 5 samples before this date)",
                "input_tokens": 0,
                "output_tokens": 0,
                "llm_calls": 0,
            }

        prediction = trainer.predict(features)

        # Feature importance summary (top 5)
        top_features = trainer.feature_importance(top_n=5)
        feat_str = ", ".join(f"{n}={v:.3f}" for n, v in top_features)

        raw_response = (
            f"ML Model: {self.model_type}\n"
            f"Up probability: {prediction['up_probability']:.4f}\n"
            f"Decision: {prediction['decision']} | Confidence: {prediction['confidence']}\n"
            f"Top features: {feat_str}"
        )

        return {
            "decision": prediction["decision"],
            "confidence": prediction["confidence"],
            "strategy": f"ml_{self.model_type}",
            "raw_response": raw_response,
            "input_tokens": 0,
            "output_tokens": 0,
            "llm_calls": 0,
        }

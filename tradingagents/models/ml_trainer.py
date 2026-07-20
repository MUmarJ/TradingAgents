"""XGBoost/LightGBM training pipeline for trading signal generation.

Supports walk-forward (expanding window) training to prevent look-ahead bias.
Models are trained on features extracted from cached datasets.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd


class MLTrainer:
    """Train and evaluate gradient boosting models for directional prediction."""

    def __init__(self, model_type: str = "xgboost"):
        if model_type not in ("xgboost", "lightgbm"):
            raise ValueError(f"model_type must be 'xgboost' or 'lightgbm', got '{model_type}'")
        self.model_type = model_type
        self.model = None
        self.feature_names: Optional[List[str]] = None
        self._train_X: Optional[pd.DataFrame] = None

    def build_training_set(
        self,
        results_dir: str,
        tickers: List[str],
        feature_extractor: Any,
        cutoff_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Build feature matrix with labels from cached datasets.

        Walks all cached datasets for the given tickers and extracts features.
        Label: next-day price direction (1 = up, 0 = down).
        Excludes days where the move is ambiguous (< 0.15% either way).

        Args:
            results_dir: Path to results directory containing datasets/.
            tickers: List of tickers to include.
            feature_extractor: FeatureExtractor instance.
            cutoff_date: Only include dates before this (YYYY-MM-DD) to
                        prevent look-ahead. None means use all available.
        """
        rows = []

        for ticker in tickers:
            datasets_dir = Path(results_dir) / "datasets" / ticker
            if not datasets_dir.exists():
                continue

            # Get all cached dates sorted
            dates = sorted([
                d.name for d in datasets_dir.iterdir()
                if d.is_dir() and len(d.name) == 10  # YYYY-MM-DD format
            ])

            # Pre-load all OHLCV data to compute cross-dataset labels.
            # Each dataset's OHLCV ends at its trade date, so we need the
            # NEXT dataset's OHLCV to get the next-day close for labeling.
            from tradingagents.models.feature_engineering import parse_ohlcv_csv

            for i, date in enumerate(dates):
                if cutoff_date and date >= cutoff_date:
                    continue

                # Load dataset
                dataset_path = datasets_dir / date / f"{ticker}_{date}_raw_dataset.json"
                legacy_path = datasets_dir / date / "dataset.json"

                ds_path = dataset_path if dataset_path.exists() else legacy_path
                if not ds_path.exists():
                    continue

                try:
                    with open(ds_path) as f:
                        cached = json.load(f)
                except (json.JSONDecodeError, KeyError):
                    continue

                # Extract features
                features = feature_extractor.extract(cached)
                if not features:
                    continue

                # Compute label: next-day direction.
                # The current dataset's OHLCV ends at trade_date, so use the
                # next cached dataset's OHLCV to find next-day close.
                try:
                    ohlcv = parse_ohlcv_csv(cached["market_data"])
                    trade_ts = pd.Timestamp(date)
                    valid_dates = ohlcv.index[ohlcv.index <= trade_ts]
                    if len(valid_dates) == 0:
                        continue
                    close_today = ohlcv.loc[valid_dates[-1], "close"]

                    # Try to find next-day close from a later dataset
                    close_next = None

                    # First check current dataset (in case it has future data)
                    future_dates = ohlcv.index[ohlcv.index > trade_ts]
                    if len(future_dates) > 0:
                        close_next = ohlcv.loc[future_dates[0], "close"]
                    else:
                        # Look in the next cached dataset
                        for j in range(i + 1, min(i + 3, len(dates))):
                            next_path = datasets_dir / dates[j] / f"{ticker}_{dates[j]}_raw_dataset.json"
                            next_legacy = datasets_dir / dates[j] / "dataset.json"
                            np_path = next_path if next_path.exists() else next_legacy
                            if not np_path.exists():
                                continue
                            try:
                                with open(np_path) as nf:
                                    next_cached = json.load(nf)
                                next_ohlcv = parse_ohlcv_csv(next_cached["market_data"])
                                # Find first date after trade_ts
                                next_future = next_ohlcv.index[next_ohlcv.index > trade_ts]
                                if len(next_future) > 0:
                                    close_next = next_ohlcv.loc[next_future[0], "close"]
                                    break
                            except Exception:
                                continue

                    if close_next is None:
                        continue

                    pct_change = (close_next / close_today - 1) * 100

                    # Skip ambiguous moves
                    if abs(pct_change) < 0.15:
                        continue

                    label = 1 if pct_change > 0 else 0
                except Exception:
                    continue

                features["_ticker"] = ticker
                features["_date"] = date
                features["_label"] = label
                features["_pct_change"] = pct_change
                rows.append(features)

        if not rows:
            return pd.DataFrame()

        df = pd.DataFrame(rows)
        # Separate metadata from features
        meta_cols = [c for c in df.columns if c.startswith("_")]
        feat_cols = [c for c in df.columns if not c.startswith("_")]
        self.feature_names = sorted(feat_cols)

        return df

    def train(self, df: pd.DataFrame) -> Dict[str, float]:
        """Train model on the full dataset. Returns cross-val metrics.

        Uses TimeSeriesSplit for temporal cross-validation.
        """
        if df.empty or "_label" not in df.columns:
            raise ValueError("Empty or unlabeled training data")

        X = df[self.feature_names].fillna(0)
        self._train_X = X
        y = df["_label"]

        if self.model_type == "xgboost":
            import xgboost as xgb
            self.model = xgb.XGBClassifier(
                n_estimators=150,
                max_depth=3,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                eval_metric="logloss",
                random_state=42,
            )
        else:
            import lightgbm as lgb
            self.model = lgb.LGBMClassifier(
                n_estimators=150,
                max_depth=3,
                learning_rate=0.05,
                subsample=0.8,
                colsample_bytree=0.8,
                random_state=42,
                verbose=-1,
            )

        # Time-series cross-validation
        from sklearn.model_selection import TimeSeriesSplit

        tscv = TimeSeriesSplit(n_splits=min(3, len(df) // 5))
        cv_accuracies = []

        for train_idx, val_idx in tscv.split(X):
            X_train, X_val = X.iloc[train_idx], X.iloc[val_idx]
            y_train, y_val = y.iloc[train_idx], y.iloc[val_idx]

            if len(y_train.unique()) < 2:
                continue

            self.model.fit(X_train, y_train)
            preds = self.model.predict(X_val)
            acc = (preds == y_val).mean()
            cv_accuracies.append(acc)

        # Final fit on all data
        self.model.fit(X, y)

        return {
            "cv_accuracy": np.mean(cv_accuracies) if cv_accuracies else 0.0,
            "cv_std": np.std(cv_accuracies) if cv_accuracies else 0.0,
            "n_samples": len(df),
            "n_features": len(self.feature_names),
            "n_positive": int(y.sum()),
            "n_negative": int(len(y) - y.sum()),
        }

    def predict(self, features: Dict[str, float]) -> Dict[str, Any]:
        """Predict direction and return probability."""
        if self.model is None:
            raise RuntimeError("Model not trained yet")

        # Build feature vector in the same column order
        X = pd.DataFrame([{f: features.get(f, 0) for f in self.feature_names}])
        prob = self.model.predict_proba(X)[0]

        # prob[0] = P(down), prob[1] = P(up)
        up_prob = float(prob[1]) if len(prob) > 1 else 0.5

        if up_prob > 0.55:
            decision = "BUY"
        elif up_prob < 0.45:
            decision = "SELL"
        else:
            decision = "HOLD"

        return {
            "decision": decision,
            "confidence": round(max(up_prob, 1 - up_prob), 2),
            "up_probability": round(up_prob, 4),
        }

    def feature_importance(self, top_n: int = 15) -> List[Tuple[str, float]]:
        """Return top feature importances."""
        if self.model is None or self.feature_names is None:
            return []

        importances = self.model.feature_importances_
        pairs = sorted(
            zip(self.feature_names, importances),
            key=lambda x: x[1],
            reverse=True,
        )
        return pairs[:top_n]

    def shap_importance(self, X: pd.DataFrame = None, top_n: int = 20) -> List[Tuple[str, float]]:
        """Return top features ranked by mean |SHAP value|.

        Uses TreeExplainer for exact Shapley values on tree-based models.
        """
        if self.model is None or self.feature_names is None:
            return []

        import shap

        explainer = shap.TreeExplainer(self.model)

        if X is None:
            if self._train_X is None:
                raise RuntimeError("No training data stored. Pass X or call train() first.")
            X = self._train_X

        shap_values = explainer.shap_values(X)

        # Binary classification: shap_values may be list [class_0, class_1]
        if isinstance(shap_values, list):
            sv = shap_values[1]
        else:
            sv = shap_values

        mean_abs = np.abs(sv).mean(axis=0)
        pairs = sorted(
            zip(self.feature_names, mean_abs),
            key=lambda x: x[1],
            reverse=True,
        )
        return pairs[:top_n]

    def shap_values_raw(self, X: pd.DataFrame = None):
        """Return raw SHAP values array and explainer for visualization.

        Returns:
            Tuple of (shap_values ndarray, TreeExplainer, X DataFrame).
        """
        if self.model is None:
            raise RuntimeError("Model not trained yet")

        import shap

        explainer = shap.TreeExplainer(self.model)

        if X is None:
            if self._train_X is None:
                raise RuntimeError("No training data stored.")
            X = self._train_X

        shap_values = explainer.shap_values(X)
        if isinstance(shap_values, list):
            sv = shap_values[1]
        else:
            sv = shap_values

        return sv, explainer, X

    def save(self, path: str):
        """Save trained model and feature names to disk."""
        import pickle
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'wb') as f:
            pickle.dump({
                "model": self.model,
                "feature_names": self.feature_names,
                "model_type": self.model_type,
            }, f)

    def load(self, path: str):
        """Load a previously saved model."""
        import pickle
        with open(path, 'rb') as f:
            data = pickle.load(f)
        self.model = data["model"]
        self.feature_names = data["feature_names"]
        self.model_type = data["model_type"]


def load_selected_features(path: str = None) -> Optional[List[str]]:
    """Load a SHAP-selected feature list from JSON.

    Args:
        path: Path to selected_features.json. Defaults to the
              bundled file in the models package.

    Returns:
        List of feature names, or None if file not found.
    """
    if path is None:
        path = str(Path(__file__).parent / "selected_features.json")

    if not Path(path).exists():
        return None

    with open(path) as f:
        data = json.load(f)

    return data.get("features", None)

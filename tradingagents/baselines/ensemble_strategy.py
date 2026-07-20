"""Ensemble meta-learner combining multiple trading strategy signals.

Combines signals from sentiment, ML (XGBoost), and time-series (Kronos)
strategies using voting and confidence-weighted approaches.

Zero API cost when all sub-strategies are local models.
"""

import json
from collections import Counter
from pathlib import Path
from typing import Dict, Any, Optional, List

from tradingagents.default_config import DEFAULT_CONFIG


class EnsembleStrategy:
    """Meta-learner that combines multiple sub-strategy signals.

    Supports three combination methods:
    - majority_vote: Simple majority wins.
    - weighted_vote: Signals weighted by confidence.
    - adaptive: Dynamically adjusts weights based on recent accuracy.
    """

    VALID_METHODS = ("majority_vote", "weighted_vote", "adaptive")

    def __init__(
        self,
        method: str = "weighted_vote",
        sub_strategies: Optional[List[str]] = None,
        config: Dict = None,
    ):
        if method not in self.VALID_METHODS:
            raise ValueError(
                f"Unknown method: {method}. Supported: {self.VALID_METHODS}"
            )
        self.method = method
        self.config = config or DEFAULT_CONFIG
        self.sub_strategies = sub_strategies or [
            "ml_xgboost",
            "ts_kronos_mini",
            "sentiment_deberta",
        ]

        # Lazy-loaded sub-strategy instances
        self._instances: Dict[str, Any] = {}

    def _get_strategy(self, name: str):
        """Lazy-load a sub-strategy instance."""
        if name in self._instances:
            return self._instances[name]

        if name.startswith("ml_") and name.endswith("_pruned"):
            from tradingagents.baselines.ml_strategy_pruned import MLStrategyPruned
            model_type = name[len("ml_"):-len("_pruned")]
            inst = MLStrategyPruned(model_type=model_type, config=self.config)
        elif name.startswith("ml_"):
            from tradingagents.baselines.ml_strategy import MLStrategy
            model_type = name[len("ml_"):]
            inst = MLStrategy(model_type=model_type, config=self.config)
        elif name.startswith("ts_kronos"):
            from tradingagents.baselines.timeseries_strategy import TimeSeriesStrategy
            parts = name.split("_")
            model_size = parts[2] if len(parts) > 2 else "mini"
            inst = TimeSeriesStrategy(model_size=model_size, config=self.config)
        elif name.startswith("sentiment_"):
            from tradingagents.baselines.sentiment_strategy import SentimentStrategy
            model_name = name[len("sentiment_"):]
            # Map short names to full model names
            name_map = {
                "deberta": "deberta-finance",
                "deberta-finance": "deberta-finance",
                "finbert": "finbert",
                "modern-finbert": "modern-finbert",
            }
            inst = SentimentStrategy(
                model_name=name_map.get(model_name, model_name),
                config=self.config,
            )
        else:
            raise ValueError(f"Unknown sub-strategy: {name}")

        self._instances[name] = inst
        return inst

    def _collect_signals(
        self, ticker: str, trade_date: str
    ) -> List[Dict[str, Any]]:
        """Run all sub-strategies and collect their signals."""
        signals = []
        for name in self.sub_strategies:
            try:
                strategy = self._get_strategy(name)
                result = strategy.analyze(ticker, trade_date)
                signals.append({
                    "strategy": name,
                    "decision": result["decision"],
                    "confidence": result["confidence"],
                    "raw_response": result.get("raw_response", ""),
                })
            except Exception as e:
                print(f"  Sub-strategy {name} failed: {e}")
                signals.append({
                    "strategy": name,
                    "decision": "HOLD",
                    "confidence": 0.3,
                    "raw_response": f"Error: {e}",
                    "error": True,
                })
        return signals

    def _majority_vote(self, signals: List[Dict]) -> tuple:
        """Simple majority vote."""
        decisions = [s["decision"] for s in signals]
        counter = Counter(decisions)
        winner, count = counter.most_common(1)[0]

        # Confidence = proportion of agreeing strategies
        agreement = count / len(signals)
        avg_conf = sum(
            s["confidence"] for s in signals if s["decision"] == winner
        ) / max(count, 1)

        confidence = round(agreement * avg_conf, 2)
        return winner, confidence

    def _weighted_vote(self, signals: List[Dict]) -> tuple:
        """Confidence-weighted vote."""
        # Score each direction: BUY=+1, SELL=-1, HOLD=0
        score = 0.0
        total_weight = 0.0

        for s in signals:
            weight = s["confidence"]
            if s["decision"] == "BUY":
                score += weight
            elif s["decision"] == "SELL":
                score -= weight
            # HOLD contributes 0
            total_weight += weight

        if total_weight == 0:
            return "HOLD", 0.3

        # Normalize score to [-1, 1]
        normalized = score / total_weight

        if normalized > 0.15:
            decision = "BUY"
        elif normalized < -0.15:
            decision = "SELL"
        else:
            decision = "HOLD"

        confidence = round(min(0.5 + abs(normalized) * 0.5, 0.95), 2)
        return decision, confidence

    def _adaptive_vote(self, signals: List[Dict]) -> tuple:
        """Adaptive weighted vote — increases weight for strategies that
        have shown historical accuracy. Falls back to weighted_vote
        since we don't have live accuracy tracking yet."""
        # Strategy-level bias weights (informed by Phase 1-2 benchmarks)
        bias = {
            "ml_xgboost": 1.3,       # Best overall accuracy
            "ml_lightgbm": 1.3,
            "ts_kronos_mini": 1.1,    # New, give moderate weight
            "ts_kronos_small": 1.1,
            "ts_kronos_base": 1.1,
            "sentiment_deberta": 0.8, # Lower accuracy, mostly BUYs
            "sentiment_finbert": 0.7,
            "sentiment_modern-finbert": 0.7,
        }

        score = 0.0
        total_weight = 0.0

        for s in signals:
            w = s["confidence"] * bias.get(s["strategy"], 1.0)
            if s["decision"] == "BUY":
                score += w
            elif s["decision"] == "SELL":
                score -= w
            total_weight += w

        if total_weight == 0:
            return "HOLD", 0.3

        normalized = score / total_weight

        if normalized > 0.12:
            decision = "BUY"
        elif normalized < -0.12:
            decision = "SELL"
        else:
            decision = "HOLD"

        confidence = round(min(0.5 + abs(normalized) * 0.5, 0.95), 2)
        return decision, confidence

    def analyze(self, ticker: str, trade_date: str, **kwargs) -> Dict[str, Any]:
        """Run ensemble prediction combining multiple sub-strategies."""
        signals = self._collect_signals(ticker, trade_date)

        if self.method == "majority_vote":
            decision, confidence = self._majority_vote(signals)
        elif self.method == "weighted_vote":
            decision, confidence = self._weighted_vote(signals)
        elif self.method == "adaptive":
            decision, confidence = self._adaptive_vote(signals)
        else:
            decision, confidence = self._weighted_vote(signals)

        # Build summary
        signal_lines = []
        for s in signals:
            err = " [ERROR]" if s.get("error") else ""
            signal_lines.append(
                f"  {s['strategy']}: {s['decision']} (conf={s['confidence']:.2f}){err}"
            )

        raw_response = (
            f"Ensemble Method: {self.method}\n"
            f"Sub-strategies ({len(signals)}):\n"
            + "\n".join(signal_lines)
            + f"\nFinal Decision: {decision} | Confidence: {confidence}"
        )

        return {
            "decision": decision,
            "confidence": confidence,
            "strategy": f"ensemble_{self.method}",
            "raw_response": raw_response,
            "input_tokens": 0,
            "output_tokens": 0,
            "llm_calls": 0,
        }

"""Kronos time-series foundation model wrapper for price prediction.

Kronos (AAAI 2026) is a financial time-series foundation model pre-trained on
12 billion candlestick records from 45 exchanges. It predicts future OHLCV bars
in zero-shot mode (no fine-tuning needed).

Uses the cached OHLCV data from market_data to predict next-day price direction.
Deterministic when sample_count is high enough, zero API cost.
"""

from io import StringIO
from typing import Dict, Any, Optional, Tuple

import numpy as np
import pandas as pd


# Lazy-loaded globals to avoid slow imports at module level
_tokenizer = None
_model = None
_predictor = None
_model_size = None


def _ensure_kronos(model_size: str = "mini"):
    """Lazy-load Kronos model and tokenizer on first use."""
    global _tokenizer, _model, _predictor, _model_size

    if _predictor is not None and _model_size == model_size:
        return _predictor

    from tradingagents.models.kronos import KronosTokenizer, Kronos, KronosPredictor

    print(f"Loading Kronos-{model_size} model...")
    _tokenizer = KronosTokenizer.from_pretrained("NeoQuasar/Kronos-Tokenizer-base")
    _model = Kronos.from_pretrained(f"NeoQuasar/Kronos-{model_size}")
    _predictor = KronosPredictor(_model, _tokenizer, max_context=512)
    _model_size = model_size
    print(f"Kronos-{model_size} loaded on {_predictor.device}")
    return _predictor


def predict_direction(
    ohlcv_csv: str,
    trade_date: str,
    model_size: str = "mini",
    pred_days: int = 3,
    sample_count: int = 20,
    temperature: float = 0.8,
) -> Dict[str, Any]:
    """Predict price direction from cached OHLCV CSV string.

    Args:
        ohlcv_csv: CSV string with columns: timestamp, open, high, low, close, volume
        trade_date: The trade date (YYYY-MM-DD). Only data up to this date is used.
        model_size: Kronos model size ('mini', 'small', 'base').
        pred_days: Number of days ahead to predict.
        sample_count: Number of Monte Carlo samples to average (more = stable).
        temperature: Sampling temperature (lower = less random).

    Returns:
        Dict with keys: decision, confidence, up_probability,
        predicted_close, current_close, predicted_pct_change,
        pred_days_detail (list of per-day predictions).
    """
    predictor = _ensure_kronos(model_size)

    # Parse OHLCV CSV
    df = pd.read_csv(StringIO(ohlcv_csv))
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values("timestamp")

    # Filter to data up to trade_date (prevent look-ahead)
    trade_ts = pd.Timestamp(trade_date)
    df = df[df["timestamp"] <= trade_ts].copy()

    if len(df) < 5:
        return _fallback_result("Insufficient OHLCV data (< 5 bars)")

    # Prepare data for Kronos
    current_close = float(df["close"].iloc[-1])

    ohlcv_df = df[["open", "high", "low", "close", "volume"]].copy()
    for col in ["open", "high", "low", "close", "volume"]:
        ohlcv_df[col] = pd.to_numeric(ohlcv_df[col], errors="coerce")
    ohlcv_df = ohlcv_df.dropna()

    if len(ohlcv_df) < 5:
        return _fallback_result("Insufficient valid OHLCV data after cleaning")

    # Create timestamps as Series (Kronos requires .dt accessor)
    x_timestamps = pd.Series(df["timestamp"].values[-len(ohlcv_df):]).reset_index(drop=True)

    # Generate future business day timestamps
    last_date = x_timestamps.iloc[-1]
    future_dates = pd.bdate_range(
        start=last_date + pd.Timedelta(days=1),
        periods=pred_days,
    )
    y_timestamps = pd.Series(future_dates)

    # Run Kronos prediction
    pred_df = predictor.predict(
        df=ohlcv_df.reset_index(drop=True),
        x_timestamp=x_timestamps,
        y_timestamp=y_timestamps,
        pred_len=pred_days,
        T=temperature,
        top_p=0.9,
        sample_count=sample_count,
        verbose=False,
    )

    # Extract predictions
    predicted_closes = pred_df["close"].values
    pred_1d = float(predicted_closes[0])
    pct_change_1d = (pred_1d / current_close - 1) * 100

    # Multi-day analysis
    days_detail = []
    up_count = 0
    total_pct = 0
    for i, pc in enumerate(predicted_closes):
        pct = (float(pc) / current_close - 1) * 100
        days_detail.append({
            "day": i + 1,
            "predicted_close": round(float(pc), 2),
            "pct_from_current": round(pct, 2),
        })
        if pct > 0:
            up_count += 1
        total_pct += pct

    # Decision based on average predicted direction and consistency
    avg_pct = total_pct / pred_days
    up_ratio = up_count / pred_days

    # Combine 1-day and multi-day signals
    # up_probability: weighted average of 1-day direction and multi-day consistency
    if pct_change_1d > 0:
        up_prob_1d = 0.5 + min(abs(pct_change_1d) / 5, 0.45)
    else:
        up_prob_1d = 0.5 - min(abs(pct_change_1d) / 5, 0.45)

    up_probability = 0.6 * up_prob_1d + 0.4 * up_ratio

    if up_probability > 0.55:
        decision = "BUY"
    elif up_probability < 0.45:
        decision = "SELL"
    else:
        decision = "HOLD"

    confidence = round(min(0.5 + abs(up_probability - 0.5) * 2, 0.95), 2)

    return {
        "decision": decision,
        "confidence": confidence,
        "up_probability": round(up_probability, 4),
        "predicted_close_1d": round(pred_1d, 2),
        "current_close": round(current_close, 2),
        "predicted_pct_1d": round(pct_change_1d, 2),
        "avg_predicted_pct": round(avg_pct, 2),
        "pred_days_detail": days_detail,
    }


def _fallback_result(reason: str) -> Dict[str, Any]:
    """Return a HOLD result when prediction is not possible."""
    return {
        "decision": "HOLD",
        "confidence": 0.3,
        "up_probability": 0.5,
        "predicted_close_1d": 0.0,
        "current_close": 0.0,
        "predicted_pct_1d": 0.0,
        "avg_predicted_pct": 0.0,
        "pred_days_detail": [],
        "fallback_reason": reason,
    }

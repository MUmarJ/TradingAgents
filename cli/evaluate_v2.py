#!/usr/bin/env python3
"""
V2 backtest: Fixes look-ahead bias, removes HOLD fallback.
Compares best single-agent vs best multi-agent from v1 results.

Changes from v1 (evaluate.py):
- No reuse of v1 cached datasets (they have broken fields + look-ahead quotes)
- Decision extraction failures are task failures (no silent HOLD)
- Fresh dataset caching to results/datasets_v2/
- 5-day validation as secondary metric
- Explicit --provider / --deep-model / --quick-model flags for Claude support
- Failure analysis in reports

Usage:
    # Default (OpenAI, v1-best models)
    python -m cli.evaluate_v2 --tickers AMBA,RAPT,ET,ZTS

    # Claude models
    python -m cli.evaluate_v2 --tickers AMBA,RAPT,ET,ZTS \
        --provider anthropic \
        --deep-model claude-sonnet-4-20250514 \
        --quick-model claude-haiku-4-20250514

    # Resume after interruption
    python -m cli.evaluate_v2 --resume

    # Retry failed tasks
    python -m cli.evaluate_v2 --resume --retry-failed

    # Generate report from completed run
    python -m cli.evaluate_v2 --report <run_id>
"""

import argparse
import json
import os
import re
import sys
import time
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import numpy as np

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.backtest.outcome_tracker import (
    TradeOutcome,
    validate_outcome_against_market,
    validate_multi_horizon_outcome,
    HORIZONS,
)
from tradingagents.graph.signal_processing import (
    extract_decision_from_text,
    extract_confidence_from_text,
)

# Reuse helpers from evaluate.py
from cli.evaluate import (
    get_monthly_dates,
    save_checkpoint,
    load_checkpoint,
    find_latest_checkpoint,
    count_by_status,
    _load_cached_reports,
    _save_reports,
    _calc_stats,
    _strategy_outcomes,
    _build_run_config,
)

# ───────────────────────────────────────────────────────
# V2 dataset caching (separate from v1)
# ───────────────────────────────────────────────────────

V2_DATASET_DIR = "datasets_v2"

# Approximate cost per task (USD) by strategy type and model family.
# Used by --dry-run for budget estimation. Based on typical token usage.
COST_PER_TASK = {
    "single": {
        "gpt-5.1-codex-mini": 0.08,
        "gpt-4o": 0.15,
        "gpt-4o-mini": 0.03,
        "claude-opus-4-5": 0.45,
        "claude-opus-4-6": 0.45,
        "claude-sonnet-4": 0.10,
        "claude-sonnet-4-5": 0.10,
        "claude-haiku": 0.02,
    },
    "multi_agent": {
        "gpt-5.1-codex-mini": 0.50,
        "gpt-4o": 1.00,
        "gpt-4o-mini": 0.20,
        "claude-opus-4-5": 2.60,
        "claude-opus-4-6": 2.60,
        "claude-sonnet-4": 0.60,
        "claude-sonnet-4-5": 0.60,
        "claude-haiku": 0.15,
    },
    "sentiment": {
        "deberta-finance": 0.00,
        "finbert": 0.00,
        "modern-finbert": 0.00,
    },
    "ml": {
        "xgboost": 0.00,
        "lightgbm": 0.00,
    },
    "timeseries": {
        "kronos_mini": 0.00,
        "kronos_small": 0.00,
        "kronos_base": 0.00,
    },
    "ensemble": {
        "majority_vote": 0.00,
        "weighted_vote": 0.00,
        "adaptive": 0.00,
    },
}


def _normalize_sub_strategy(short_name: str) -> str:
    """Map short ensemble sub-strategy names to full strategy names."""
    mapping = {
        "kronos_mini": "ts_kronos_mini",
        "kronos_small": "ts_kronos_small",
        "kronos_base": "ts_kronos_base",
        "xgboost": "ml_xgboost",
        "lightgbm": "ml_lightgbm",
        "deberta": "sentiment_deberta",
        "finbert": "sentiment_finbert",
        "modern_finbert": "sentiment_modern-finbert",
    }
    return mapping.get(short_name, short_name)


def _estimate_cost(model: str, strategy_type: str) -> float:
    """Estimate cost per task for a given model and strategy type.

    Matches against the COST_PER_TASK table using longest-match-first.
    Returns 0.10 as fallback if model is unknown.
    """
    table = COST_PER_TASK.get(strategy_type, COST_PER_TASK["single"])
    model_lower = model.lower()
    # Sort by key length descending so "gpt-4o-mini" matches before "gpt-4o"
    for key in sorted(table.keys(), key=len, reverse=True):
        if key in model_lower:
            return table[key]
    return 0.10  # Unknown model fallback


def get_tri_monthly_dates(start: str, end: str) -> List[str]:
    """Generate 10th, 20th, and end-of-month dates between start and end.

    Produces three analysis dates per month for higher-frequency evaluation.
    """
    from calendar import monthrange

    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    dates = []

    current = start_dt.replace(day=1)
    while current <= end_dt:
        year, month = current.year, current.month
        _, last_day = monthrange(year, month)

        for day in [10, 20, last_day]:
            candidate = current.replace(day=day)
            if start_dt <= candidate <= end_dt:
                dates.append(candidate.strftime("%Y-%m-%d"))

        current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)

    return sorted(set(dates))


# Strategy name -> full model ID mapping for --strategies arg
STRATEGY_MODEL_MAP = {
    # Anthropic
    "sonnet-4-5": "claude-sonnet-4-5-20250929",
    "haiku-4-5": "claude-haiku-4-5-20251001",
    "opus-4-5": "claude-opus-4-5-20251101",
    "opus-4-6": "claude-opus-4-6",
    # OpenAI
    "gpt-4o-mini": "gpt-4o-mini",
    "gpt-5.1-codex-mini": "gpt-5.1-codex-mini",
    "gpt-4o": "gpt-4o",
}


def _parse_retry_after(error_str: str) -> Optional[float]:
    """Parse retry-after seconds from a rate limit error message.

    Looks for patterns like 'Please try again in 6.045s' or
    'retry after 30 seconds'.
    """
    # "Please try again in 6.045s"
    match = re.search(r"try again in ([\d.]+)s", error_str)
    if match:
        return float(match.group(1))
    # "retry after 30 seconds"
    match = re.search(r"retry after (\d+)", error_str, re.IGNORECASE)
    if match:
        return float(match.group(1))
    return None


def _v2_dataset_path(results_dir: Path, ticker: str, date: str) -> Path:
    """Return path for v2 cached dataset."""
    return results_dir / V2_DATASET_DIR / ticker / date / f"{ticker}_{date}_raw_dataset.json"


def _load_v2_dataset(results_dir: Path, ticker: str, date: str) -> Optional[Dict[str, str]]:
    """Load cached v2 dataset if available."""
    path = _v2_dataset_path(results_dir, ticker, date)
    if path.exists():
        try:
            with open(path) as f:
                data = json.load(f)
            if all(k in data for k in ["market_data", "fundamentals_data", "news_data"]):
                print(f"  V2 DATASET CACHE HIT: {ticker} {date}")
                return data
        except (json.JSONDecodeError, KeyError):
            pass
    return None


def _save_v2_dataset(results_dir: Path, ticker: str, date: str, data: Dict[str, str]):
    """Save raw data to v2 cache."""
    path = _v2_dataset_path(results_dir, ticker, date)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(data, f, indent=2)


def _fetch_v2_dataset(ticker: str, date: str, results_dir: Path) -> Dict[str, str]:
    """Fetch all raw data for a ticker/date, using v2 cache if available.

    Uses the fixed data tools with proper parameter names and date bounding.
    """
    cached = _load_v2_dataset(results_dir, ticker, date)
    if cached:
        return cached

    from tradingagents.agents.utils.agent_utils import (
        get_stock_data, get_current_quote, get_indicators,
        get_fundamentals, get_balance_sheet, get_cashflow,
        get_income_statement, get_news, get_global_news,
    )
    from tradingagents.baselines.single_agent import (
        _fetch_data_safe, _fetch_all_indicators, _get_sector_etf,
    )

    end_date = date
    start_dt = datetime.strptime(date, "%Y-%m-%d") - timedelta(days=90)
    start_date = start_dt.strftime("%Y-%m-%d")

    sector_etf = _get_sector_etf(ticker)

    data = {
        "market_data": _fetch_data_safe(get_stock_data, ticker, start_date, end_date),
        "quote_data": _fetch_data_safe(get_current_quote, ticker, date),
        "indicators_data": _fetch_all_indicators(ticker, end_date, look_back_days=60),
        "fundamentals_data": _fetch_data_safe(get_fundamentals, ticker, date),
        "balance_sheet_data": _fetch_data_safe(get_balance_sheet, ticker),
        "cashflow_data": _fetch_data_safe(get_cashflow, ticker),
        "income_data": _fetch_data_safe(get_income_statement, ticker),
        "news_data": _fetch_data_safe(get_news, ticker, start_date, end_date),
        "global_news_data": _fetch_data_safe(get_global_news, date),
        "spy_market_data": _fetch_data_safe(get_stock_data, "SPY", start_date, end_date),
        "spy_indicators": _fetch_all_indicators("SPY", end_date, look_back_days=60),
        "sector_market_data": _fetch_data_safe(get_stock_data, sector_etf, start_date, end_date),
        "sector_indicators": _fetch_all_indicators(sector_etf, end_date, look_back_days=60),
        "sector_etf": sector_etf,
        "sentiment_data": "",
        "cached_at": datetime.now().isoformat(),
        "ticker": ticker,
        "trade_date": date,
    }

    _save_v2_dataset(results_dir, ticker, date, data)
    print(f"  V2 DATASET SAVED: {ticker} {date}")
    return data


# ───────────────────────────────────────────────────────
# Strategy runners (v2)
# ───────────────────────────────────────────────────────


def _detect_provider(model: str) -> str:
    """Auto-detect LLM provider from model name."""
    if model.startswith("claude-"):
        return "anthropic"
    if model.startswith(("gpt-", "o1-", "o3-")):
        return "openai"
    return "openai"


def run_single_agent_v2(ticker: str, date: str, model: str,
                        config: Dict, articles: int = 50) -> Dict[str, Any]:
    """Run single-agent baseline with v2 dataset caching."""
    from tradingagents.baselines.single_agent import SingleAgentBaseline

    # Override results_dir and auto-detect provider from model name
    sa_config = config.copy()
    sa_config["llm_provider"] = _detect_provider(model)
    baseline = SingleAgentBaseline(model=model, config=sa_config)
    result = baseline.analyze(ticker, date, news_article_limit=articles)

    return {
        "decision": result["decision"],
        "confidence": result["confidence"],
        "strategy": f"single_{_short_model(model)}",
        "raw_response": result.get("raw_response", ""),
        "input_tokens": result.get("input_tokens", 0),
        "output_tokens": result.get("output_tokens", 0),
        "llm_calls": result.get("llm_calls", 1),
    }


def run_sentiment_strategy_v2(ticker: str, date: str, model_name: str,
                              config: Dict) -> Dict[str, Any]:
    """Run sentiment-only strategy (FinBERT/DeBERTa) on cached data."""
    from tradingagents.baselines.sentiment_strategy import SentimentStrategy

    strategy = SentimentStrategy(model_name=model_name, config=config)
    result = strategy.analyze(ticker, date)
    return result


# Singleton ML strategy instances (reuse across tasks to avoid retraining)
_ml_strategy_cache: Dict[str, Any] = {}


def run_ml_strategy_v2(ticker: str, date: str, model_type: str,
                       config: Dict) -> Dict[str, Any]:
    """Run ML strategy (XGBoost/LightGBM) on cached data."""
    from tradingagents.baselines.ml_strategy import MLStrategy

    cache_key = f"ml_{model_type}"
    if cache_key not in _ml_strategy_cache:
        _ml_strategy_cache[cache_key] = MLStrategy(
            model_type=model_type, config=config
        )
    strategy = _ml_strategy_cache[cache_key]
    result = strategy.analyze(ticker, date)
    return result


# Singleton pruned ML strategy instances
_ml_pruned_strategy_cache: Dict[str, Any] = {}


def run_ml_pruned_strategy_v2(ticker: str, date: str, model_type: str,
                               config: Dict) -> Dict[str, Any]:
    """Run pruned ML strategy (SHAP-selected features) on cached data."""
    from tradingagents.baselines.ml_strategy_pruned import MLStrategyPruned

    cache_key = f"ml_{model_type}_pruned"
    if cache_key not in _ml_pruned_strategy_cache:
        _ml_pruned_strategy_cache[cache_key] = MLStrategyPruned(
            model_type=model_type, config=config
        )
    strategy = _ml_pruned_strategy_cache[cache_key]
    result = strategy.analyze(ticker, date)
    return result


# Singleton time-series strategy instances (reuse to keep model loaded)
_ts_strategy_cache: Dict[str, Any] = {}


def run_ts_strategy_v2(ticker: str, date: str, model_size: str,
                       config: Dict) -> Dict[str, Any]:
    """Run Kronos time-series strategy on cached OHLCV data."""
    from tradingagents.baselines.timeseries_strategy import TimeSeriesStrategy

    cache_key = f"ts_kronos_{model_size}"
    if cache_key not in _ts_strategy_cache:
        _ts_strategy_cache[cache_key] = TimeSeriesStrategy(
            model_size=model_size, config=config
        )
    strategy = _ts_strategy_cache[cache_key]
    result = strategy.analyze(ticker, date)
    return result


# Singleton ensemble strategy instances
_ensemble_strategy_cache: Dict[str, Any] = {}


def run_ensemble_strategy_v2(ticker: str, date: str, method: str,
                             config: Dict,
                             sub_strategies=None) -> Dict[str, Any]:
    """Run ensemble meta-learner combining multiple sub-strategies."""
    from tradingagents.baselines.ensemble_strategy import EnsembleStrategy

    cache_key = f"ensemble_{method}_{'_'.join(sub_strategies or ['default'])}"
    if cache_key not in _ensemble_strategy_cache:
        _ensemble_strategy_cache[cache_key] = EnsembleStrategy(
            method=method, sub_strategies=sub_strategies, config=config
        )
    strategy = _ensemble_strategy_cache[cache_key]
    result = strategy.analyze(ticker, date)
    return result


def run_multi_agent_v2(ticker: str, date: str, config: Dict,
                       articles: int = 50) -> Dict[str, Any]:
    """Run the full multi-agent analysis (v2 — no v1 report cache reuse)."""
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    graph = TradingAgentsGraph(
        ["market", "social", "news", "fundamentals"],
        config=config,
        debug=False,
    )

    # Only use v2 cached reports (not v1)
    results_dir = Path(config.get("results_dir", "./results"))
    v2_report_dir = results_dir / "reports_v2"
    cached_reports = _load_v2_reports(v2_report_dir, ticker, date)

    final_state, decision = graph.propagate(
        ticker, date, cached_reports=cached_reports if cached_reports else None
    )

    # Save reports to v2 cache
    _save_v2_reports(v2_report_dir, ticker, date, final_state)

    confidence = extract_confidence_from_text(
        final_state.get("final_trade_decision", "")
    )

    return {
        "decision": decision,
        "confidence": confidence,
        "strategy": "multi_agent",
        "raw_response": final_state.get("final_trade_decision", ""),
    }


def _load_v2_reports(v2_report_dir: Path, ticker: str, date: str) -> Dict:
    """Load cached v2 analyst reports if available."""
    report_dir = v2_report_dir / ticker / date
    cached = {}
    report_files = {
        "market_report": "market_report.md",
        "sentiment_report": "sentiment_report.md",
        "news_report": "news_report.md",
        "fundamentals_report": "fundamentals_report.md",
    }
    for key, filename in report_files.items():
        path = report_dir / filename
        if path.exists():
            try:
                content = path.read_text()
                if content.strip():
                    cached[key] = content
            except Exception:
                pass
    return cached


def _save_v2_reports(v2_report_dir: Path, ticker: str, date: str,
                     final_state: Dict):
    """Save analyst reports to v2 cache."""
    report_dir = v2_report_dir / ticker / date
    report_dir.mkdir(parents=True, exist_ok=True)

    report_map = {
        "market_report": "market_report.md",
        "sentiment_report": "sentiment_report.md",
        "news_report": "news_report.md",
        "fundamentals_report": "fundamentals_report.md",
        "final_trade_decision": "final_trade_decision.md",
    }
    for key, filename in report_map.items():
        content = final_state.get(key, "")
        if content:
            try:
                (report_dir / filename).write_text(content)
            except Exception:
                pass


# ───────────────────────────────────────────────────────
# Model name shortening
# ───────────────────────────────────────────────────────

def _short_model(model: str) -> str:
    """Shorten model name for strategy labels.

    Examples:
        gpt-5.1-codex-mini -> 5.1-codex-mini
        claude-opus-4-5-20251101 -> opus-4-5
        claude-sonnet-4-5-20250929 -> sonnet-4-5
        gpt-4o-2025-12-11 -> 4o
    """
    name = model.replace("gpt-", "").replace("claude-", "")
    name = re.sub(r"-20\d{6}", "", name)          # Strip -YYYYMMDD (e.g., -20251101)
    name = re.sub(r"-\d{4}-\d{2}-\d{2}", "", name)  # Strip -YYYY-MM-DD (e.g., -2025-12-11)
    return name


# ───────────────────────────────────────────────────────
# Checkpoint creation (v2)
# ───────────────────────────────────────────────────────

def create_v2_checkpoint(tickers: List[str], dates: List[str],
                         strategies: List[str], config: Dict,
                         args) -> Dict[str, Any]:
    """Create a new v2 checkpoint structure."""
    run_id = f"v2_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    tasks = {}
    for ticker in tickers:
        for date in dates:
            for strategy in strategies:
                key = f"{ticker}|{date}|{strategy}"
                tasks[key] = {"status": "pending"}

    checkpoint = {
        "run_id": run_id,
        "version": 2,
        "config": {
            "tickers": tickers,
            "start_date": args.start,
            "end_date": args.end,
            "interval": getattr(args, 'date_mode', 'monthly'),
            "articles_per_month": args.articles_per_month,
            "strategies": strategies,
            "memory_enabled": not args.no_memory,
            "date_mode": getattr(args, 'date_mode', 'monthly'),
            "multi_horizon": getattr(args, 'multi_horizon', False),
            "selected_horizons": getattr(args, 'selected_horizons', None),
        },
        "analysis_dates": dates,
        "tasks": tasks,
        "outcomes": [],
        "last_updated": datetime.now().isoformat(),
        "run_config": _build_run_config(config),
    }

    # Store model tiers
    if config.get("_model_tiers"):
        checkpoint["config"]["model_tiers"] = config["_model_tiers"]

    return checkpoint


# ───────────────────────────────────────────────────────
# Main backtest loop (v2)
# ───────────────────────────────────────────────────────

def _is_rate_limit_error(e: Exception) -> bool:
    """Check if an exception is a rate limit / quota error."""
    err_name = type(e).__name__.lower()
    err_str = str(e)
    return (
        "rate" in err_name or "quota" in err_name
        or "429" in err_str or "rate_limit" in err_str.lower()
        or "rate limit" in err_str.lower()
    )


def run_v2_backtest(checkpoint: Dict, checkpoint_path: Path, config: Dict,
                    wait_on_rate_limit: bool = False):
    """Execute the v2 backtest, processing all pending/failed tasks.

    Args:
        wait_on_rate_limit: If True, sleep and retry on rate limits instead of stopping.
    """
    total = len(checkpoint["tasks"])
    completed = count_by_status(checkpoint, "completed")
    failed = count_by_status(checkpoint, "failed")

    print(f"\n{'=' * 70}")
    print(f"  V2 Backtest (look-ahead free, no HOLD fallback)")
    print(f"  Tickers: {', '.join(checkpoint['config']['tickers'])}")
    print(f"  Period: {checkpoint['config']['start_date']} to {checkpoint['config']['end_date']}")
    print(f"  Strategies: {', '.join(checkpoint['config']['strategies'])}")
    print(f"  Provider: {config.get('llm_provider', 'openai')}")
    print(f"  Deep model: {config.get('deep_think_llm', 'N/A')}")
    print(f"  Quick model: {config.get('quick_think_llm', 'N/A')}")
    print(f"  Progress: {completed}/{total} completed, {failed} failed")
    if wait_on_rate_limit:
        print(f"  Rate limit handling: auto-retry (max 3 consecutive)")
    print(f"{'=' * 70}\n")

    articles = checkpoint["config"].get("articles_per_month", 50)
    model_tiers = config.get("_model_tiers", {})

    # Build ordered list of pending task keys for iteration
    # (allows retry-in-place without restarting the loop)
    pending_keys = [k for k, t in checkpoint["tasks"].items()
                    if t["status"] not in ("completed", "skipped")]

    i = 0
    consecutive_rl_failures = 0

    while i < len(pending_keys):
        task_key = pending_keys[i]
        task = checkpoint["tasks"][task_key]

        # Skip if completed during this run (e.g., after retry)
        if task["status"] in ("completed", "skipped"):
            i += 1
            continue

        ticker, date, strategy = task_key.split("|")
        completed = count_by_status(checkpoint, "completed")
        idx = completed + 1

        print(f"[{idx:>3}/{total}] {ticker:<6} | {date} | {strategy:<25} | ", end="", flush=True)

        try:
            checkpoint["tasks"][task_key]["status"] = "running"
            save_checkpoint(checkpoint, checkpoint_path)

            if strategy in model_tiers:
                tier = model_tiers[strategy]
                if tier["type"] == "multi_agent":
                    tier_config = config.copy()
                    tier_config["deep_think_llm"] = tier["deep"]
                    tier_config["quick_think_llm"] = tier["quick"]
                    tier_config["llm_provider"] = _detect_provider(tier["deep"])
                    result = run_multi_agent_v2(ticker, date, tier_config, articles)
                    result["strategy"] = strategy
                elif tier["type"] == "sentiment":
                    result = run_sentiment_strategy_v2(
                        ticker, date, tier["model"], config
                    )
                    result["strategy"] = strategy
                elif tier["type"] == "ml":
                    result = run_ml_strategy_v2(
                        ticker, date, tier["model"], config
                    )
                    result["strategy"] = strategy
                elif tier["type"] == "ml_pruned":
                    result = run_ml_pruned_strategy_v2(
                        ticker, date, tier["model"], config
                    )
                    result["strategy"] = strategy
                elif tier["type"] == "timeseries":
                    result = run_ts_strategy_v2(
                        ticker, date, tier["model"], config
                    )
                    result["strategy"] = strategy
                elif tier["type"] == "ensemble":
                    result = run_ensemble_strategy_v2(
                        ticker, date, tier["model"], config,
                        sub_strategies=tier.get("sub_strategies"),
                    )
                    result["strategy"] = strategy
                else:
                    result = run_single_agent_v2(ticker, date, tier["model"], config, articles)
                    result["strategy"] = strategy
            elif strategy.startswith("ma_"):
                result = run_multi_agent_v2(ticker, date, config, articles)
                result["strategy"] = strategy
            elif strategy.startswith("single_"):
                print(f"SKIP (no model tier mapping)")
                checkpoint["tasks"][task_key]["status"] = "skipped"
                save_checkpoint(checkpoint, checkpoint_path)
                i += 1
                continue
            else:
                print(f"Unknown strategy: {strategy}")
                checkpoint["tasks"][task_key]["status"] = "skipped"
                save_checkpoint(checkpoint, checkpoint_path)
                i += 1
                continue

            # Create and validate outcome
            outcome = TradeOutcome(
                ticker=ticker,
                trade_date=date,
                decision=result["decision"],
                confidence=result.get("confidence"),
                strategy_name=result.get("strategy", strategy),
                llm_calls=result.get("llm_calls", 0),
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
            )
            outcome = validate_outcome_against_market(outcome)

            # Multi-horizon validation (if enabled)
            if checkpoint["config"].get("multi_horizon", False):
                sel_h = checkpoint["config"].get("selected_horizons")
                outcome = validate_multi_horizon_outcome(
                    outcome, horizons=sel_h,
                )

            # Update checkpoint
            checkpoint["tasks"][task_key] = {
                "status": "completed",
                "decision": outcome.decision,
                "confidence": outcome.confidence,
                "pnl": outcome.pnl,
                "decision_correct": outcome.decision_correct,
                "day5_correct": outcome.day5_correct,
                "day5_change_pct": outcome.day5_change_pct,
                "horizon_outcomes": outcome.horizon_outcomes,
                "completed_at": datetime.now().isoformat(),
            }
            checkpoint["outcomes"].append(outcome.to_dict())

            # Print result
            pnl_str = f"${outcome.pnl:>+8.2f}" if outcome.validated else "    N/A "
            correct_str = "Y" if outcome.decision_correct else "N" if outcome.decision_correct is not None else "?"
            d5_str = ""
            if outcome.day5_correct is not None:
                d5_str = f" 5d:{'Y' if outcome.day5_correct else 'N'}"
            h_str = ""
            if outcome.horizon_outcomes:
                h_correct = sum(1 for h in outcome.horizon_outcomes.values() if h.get("correct"))
                h_total = len(outcome.horizon_outcomes)
                h_str = f" H:{h_correct}/{h_total}"
            conf_str = f"{outcome.confidence:.2f}" if outcome.confidence else " N/A"
            print(f"{outcome.decision:<4} {conf_str} | {pnl_str} {correct_str}{d5_str}{h_str}")

            # Reset rate limit counter on success
            consecutive_rl_failures = 0

        except ValueError as e:
            checkpoint["tasks"][task_key] = {
                "status": "failed",
                "error": "DecisionExtractionError",
                "message": str(e)[:300],
                "failed_at": datetime.now().isoformat(),
            }
            print(f"PARSE FAIL: {str(e)[:80]}")
            consecutive_rl_failures = 0

        except Exception as e:
            if _is_rate_limit_error(e):
                if wait_on_rate_limit and consecutive_rl_failures < 3:
                    consecutive_rl_failures += 1
                    wait_time = _parse_retry_after(str(e)) or 60
                    print(f"RATE LIMITED — waiting {wait_time:.0f}s "
                          f"(attempt {consecutive_rl_failures}/3)")
                    # Reset task to pending for retry
                    checkpoint["tasks"][task_key]["status"] = "pending"
                    save_checkpoint(checkpoint, checkpoint_path)
                    time.sleep(wait_time)
                    continue  # Retry same task (don't increment i)
                else:
                    checkpoint["tasks"][task_key] = {
                        "status": "failed",
                        "error": type(e).__name__,
                        "message": str(e)[:300],
                        "failed_at": datetime.now().isoformat(),
                    }
                    print(f"RATE LIMITED (max retries exhausted)")
                    print(f"\nProgress saved. Resume with: "
                          f"python -m cli.evaluate_v2 --resume {checkpoint['run_id']}")
                    save_checkpoint(checkpoint, checkpoint_path)
                    return
            else:
                err_name = type(e).__name__
                checkpoint["tasks"][task_key] = {
                    "status": "failed",
                    "error": err_name,
                    "message": str(e)[:300],
                    "failed_at": datetime.now().isoformat(),
                }
                print(f"FAILED ({err_name}: {str(e)[:60]})")
                traceback.print_exc()
                consecutive_rl_failures = 0

        save_checkpoint(checkpoint, checkpoint_path)
        i += 1

    # All tasks processed
    completed = count_by_status(checkpoint, "completed")
    failed = count_by_status(checkpoint, "failed")
    print(f"\nV2 Backtest complete: {completed}/{total} completed, {failed} failed")

    # Generate report
    run_dir = checkpoint_path.parent
    generate_v2_report(checkpoint, run_dir)


# ───────────────────────────────────────────────────────
# V2 Report generation
# ───────────────────────────────────────────────────────

def generate_v2_report(checkpoint: Dict, run_dir: Path):
    """Generate v2 backtest report with failure analysis and 5-day metrics."""
    outcomes = [TradeOutcome.from_dict(o) for o in checkpoint.get("outcomes", [])]
    config = checkpoint["config"]
    tickers = config["tickers"]
    strategies = config["strategies"]
    dates = checkpoint.get("analysis_dates", [])
    total_tasks = len(checkpoint.get("tasks", {}))
    failed_tasks = count_by_status(checkpoint, "failed")

    lines = []
    lines.append("# TradingAgents V2 Benchmark Report")
    lines.append(f"**Run ID:** {checkpoint['run_id']}")
    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**Period:** {config['start_date']} to {config['end_date']}")
    lines.append(f"**Tickers:** {', '.join(tickers)} ({len(tickers)} tickers)")
    date_mode = config.get("date_mode", "monthly")
    multi_horizon = config.get("multi_horizon", False)
    lines.append(f"**Dates:** {len(dates)} {date_mode} snapshots")
    lines.append(f"**Version:** 2 (look-ahead free, no HOLD fallback)")
    if date_mode == "tri-monthly":
        lines.append(f"**Date Mode:** tri-monthly (10th, 20th, end-of-month)")
    if multi_horizon:
        sel_h = config.get("selected_horizons")
        if sel_h:
            h_str = ", ".join(sel_h)
            lines.append(f"**Horizons:** {h_str} ({len(sel_h)} projection horizons)")
        else:
            lines.append(f"**Horizons:** {', '.join(HORIZONS.keys())} "
                         f"({len(HORIZONS)} projection horizons)")
    lines.append(f"**Total tasks:** {total_tasks}")
    lines.append(f"**Completed:** {len(outcomes)}")
    lines.append(f"**Failed:** {failed_tasks}")
    if total_tasks > 0:
        lines.append(f"**Failure rate:** {failed_tasks / total_tasks * 100:.1f}%\n")

    # Runtime configuration
    run_config = checkpoint.get("run_config", {})
    if run_config:
        lines.append("## Configuration\n")
        lines.append("| Setting | Value |")
        lines.append("|---------|-------|")
        lines.append(f"| LLM Provider | {run_config.get('llm_provider', 'N/A')} |")
        lines.append(f"| Deep Think LLM | {run_config.get('deep_think_llm', 'N/A')} |")
        lines.append(f"| Quick Think LLM | {run_config.get('quick_think_llm', 'N/A')} |")
        lines.append(f"| Memory Enabled | {run_config.get('memory_enabled', 'N/A')} |")
        lines.append(f"| ACE Enabled | {run_config.get('ace_enabled', 'N/A')} |")
        model_tiers = config.get("model_tiers", {})
        if model_tiers:
            lines.append(f"| Model Tiers | {len(model_tiers)} configurations |")
            for name, tier in model_tiers.items():
                if tier.get("type") == "multi_agent":
                    lines.append(f"| &nbsp;&nbsp;{name} | deep={tier['deep']}, quick={tier['quick']} |")
                else:
                    lines.append(f"| &nbsp;&nbsp;{name} | model={tier['model']} |")
        lines.append("")

    # Failure analysis
    if failed_tasks > 0:
        lines.append("## Failure Analysis\n")
        error_counts = {}
        for task_key, task in checkpoint.get("tasks", {}).items():
            if task.get("status") == "failed":
                err = task.get("error", "Unknown")
                error_counts[err] = error_counts.get(err, 0) + 1

        lines.append("| Error Type | Count | % of Total |")
        lines.append("|------------|-------|------------|")
        for err, count in sorted(error_counts.items(), key=lambda x: -x[1]):
            lines.append(f"| {err} | {count} | {count / total_tasks * 100:.1f}% |")
        lines.append("")

        # Show sample failure messages
        lines.append("**Sample failure messages:**\n")
        shown = set()
        for task_key, task in checkpoint.get("tasks", {}).items():
            if task.get("status") == "failed" and task.get("error") not in shown:
                shown.add(task.get("error"))
                lines.append(f"- `{task.get('error')}`: {task.get('message', 'N/A')[:150]}")
                if len(shown) >= 5:
                    break
        lines.append("")

    if not outcomes:
        lines.append("\nNo completed outcomes to report on.")
        report_text = "\n".join(lines)
        _save_v2_report(report_text, checkpoint, run_dir)
        return

    # Executive summary (next-day accuracy)
    lines.append("## Executive Summary (Next-Day Accuracy)\n")
    lines.append(_build_v2_summary_table(outcomes, strategies))

    # 5-day accuracy
    lines.append("\n## 5-Day Forward Accuracy\n")
    lines.append(_build_5day_table(outcomes, strategies))

    # Multi-horizon analysis (if horizon data available)
    has_horizon_data = any(o.horizon_outcomes for o in outcomes)
    if has_horizon_data:
        lines.append("\n---\n")
        lines.append("## Multi-Horizon Analysis\n")

        # Executive summary comparison
        lines.append("### Horizon Comparison (All Models)\n")
        lines.append(_build_horizon_comparison_table(outcomes, strategies))

        # Per-strategy detailed tables
        for s in strategies:
            lines.append(f"\n### {s} — Per-Horizon Accuracy\n")
            lines.append(_build_horizon_accuracy_table(outcomes, s))

        # Consistency analysis
        lines.append("\n## Cross-Horizon Consistency\n")
        lines.append(_build_consistency_table(outcomes, strategies))
        lines.append("\n---\n")

    # Conclusion
    lines.append("\n## Conclusion\n")
    lines.append(_build_v2_conclusion(outcomes, strategies))

    # Results by month
    lines.append("\n## Results by Month\n")
    lines.append(_build_v2_monthly_table(outcomes, strategies, dates))

    # By ticker
    lines.append("\n## Results by Ticker\n")
    lines.append(_build_v2_ticker_table(outcomes, strategies, tickers))

    # Decision distribution
    lines.append("\n## Decision Distribution\n")
    for s in strategies:
        s_outcomes = _strategy_outcomes(outcomes, s)
        stats = _calc_stats(s_outcomes)
        lines.append(f"**{s}:** BUY {stats['buy_pct']:.0f}% | SELL {stats['sell_pct']:.0f}% | HOLD {stats['hold_pct']:.0f}% (n={stats['count']})")
    lines.append("")

    # V3 Analysis sections (baselines, walk-forward, statistics)
    has_horizon_data = any(o.horizon_outcomes for o in outcomes)
    if has_horizon_data:
        try:
            sel_h = config.get("selected_horizons")
            baselines = compute_free_baselines(outcomes, horizons=sel_h)
            lines.append("\n" + _build_baselines_table(baselines, outcomes, strategies))
            lines.append("")
        except Exception as e:
            lines.append(f"\n*Baselines computation failed: {e}*\n")
            baselines = {}

        try:
            lines.append("\n" + compute_walk_forward_split(
                outcomes, strategies, split_date="2025-09-01"))
            lines.append("")
        except Exception as e:
            lines.append(f"\n*Walk-forward analysis failed: {e}*\n")

        if baselines:
            try:
                lines.append("\n" + compute_statistical_tests(
                    outcomes, strategies, baselines))
                lines.append("")
            except Exception as e:
                lines.append(f"\n*Statistical tests failed: {e}*\n")

    lines.append("\n---\n")

    # Confidence analysis
    lines.append("\n## Confidence Analysis\n")
    for s in strategies:
        s_outcomes = _strategy_outcomes(outcomes, s)
        with_conf = [o for o in s_outcomes if o.confidence is not None]
        if not with_conf:
            lines.append(f"**{s}:** No confidence scores extracted")
            continue

        validated = [o for o in with_conf if o.validated and o.decision_correct is not None]
        if not validated:
            lines.append(f"**{s}:** {len(with_conf)} confidence scores but no validated outcomes")
            continue

        high_conf = [o for o in validated if o.confidence >= 0.6]
        low_conf = [o for o in validated if o.confidence < 0.6]

        high_correct = sum(1 for o in high_conf if o.decision_correct) if high_conf else 0
        low_correct = sum(1 for o in low_conf if o.decision_correct) if low_conf else 0

        high_acc = (high_correct / len(high_conf) * 100) if high_conf else 0
        low_acc = (low_correct / len(low_conf) * 100) if low_conf else 0

        avg_conf = sum(o.confidence for o in with_conf) / len(with_conf)

        lines.append(f"**{s}:** Avg confidence: {avg_conf:.2f} | "
                     f"High-confidence accuracy: {high_acc:.0f}% ({len(high_conf)} trades) | "
                     f"Low-confidence accuracy: {low_acc:.0f}% ({len(low_conf)} trades)")
    lines.append("")

    report_text = "\n".join(lines)
    _save_v2_report(report_text, checkpoint, run_dir)


def _save_v2_report(report_text: str, checkpoint: Dict, run_dir: Path):
    """Save report files."""
    outcomes = [TradeOutcome.from_dict(o) for o in checkpoint.get("outcomes", [])]
    config = checkpoint["config"]
    tickers = config["tickers"]

    report_path = run_dir / "report.md"
    report_path.write_text(report_text)
    print(f"Report saved to: {report_path}")

    benchmarks_dir = Path("reports/benchmarks")
    benchmarks_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    symbols_str = "_".join(tickers[:4])
    benchmark_path = benchmarks_dir / f"V2_BENCHMARK_{date_str}_{symbols_str}.md"
    benchmark_path.write_text(report_text)
    print(f"Benchmark report saved to: {benchmark_path}")

    # Save outcomes JSON
    outcomes_data = {
        "run_id": checkpoint["run_id"],
        "version": 2,
        "generated_at": datetime.now().isoformat(),
        "run_config": checkpoint.get("run_config", {}),
        "model_tiers": config.get("model_tiers", {}),
        "backtest_config": {
            "tickers": tickers,
            "start_date": config["start_date"],
            "end_date": config["end_date"],
            "strategies": config["strategies"],
            "analysis_dates": checkpoint.get("analysis_dates", []),
        },
        "failure_count": count_by_status(checkpoint, "failed"),
        "outcomes": [o.to_dict() for o in outcomes],
    }
    outcomes_path = run_dir / "outcomes.json"
    with open(outcomes_path, "w") as f:
        json.dump(outcomes_data, f, indent=2)
    print(f"Outcomes saved to: {outcomes_path}")


def _build_v2_summary_table(outcomes: List[TradeOutcome],
                            strategies: List[str]) -> str:
    """Build the executive summary table with next-day metrics."""
    lines = []
    header = "| Metric |"
    sep = "|--------|"
    for s in strategies:
        header += f" {s} |"
        sep += "--------|"

    lines.append(header)
    lines.append(sep)

    stats = {s: _calc_stats(_strategy_outcomes(outcomes, s)) for s in strategies}

    def winner_col(metric, higher_better=True):
        vals = {s: stats[s][metric] for s in strategies if stats[s]["count"] > 0}
        if not vals:
            return None
        return max(vals, key=vals.get) if higher_better else min(vals, key=vals.get)

    rows = [
        ("Next-day accuracy", "accuracy", "{:.1f}%", True),
        ("Total P&L (post-cost)", "total_pnl", "${:,.2f}", True),
        ("Max drawdown", "max_drawdown", "${:,.2f}", False),
        ("Avg confidence", "avg_conf", "{:.2f}", None),
        ("BUY %", "buy_pct", "{:.0f}%", None),
        ("SELL %", "sell_pct", "{:.0f}%", None),
        ("HOLD %", "hold_pct", "{:.0f}%", None),
        ("Analyses", "count", "{:d}", None),
    ]

    for label, metric, fmt, higher_better in rows:
        row = f"| {label} |"
        best = winner_col(metric, higher_better) if higher_better is not None else None
        for s in strategies:
            val = stats[s][metric]
            formatted = fmt.format(val)
            if best and s == best:
                formatted = f"**{formatted}**"
            row += f" {formatted} |"
        lines.append(row)

    return "\n".join(lines)


def _build_5day_table(outcomes: List[TradeOutcome],
                      strategies: List[str]) -> str:
    """Build 5-day forward accuracy table."""
    lines = []
    header = "| Metric |"
    sep = "|--------|"
    for s in strategies:
        header += f" {s} |"
        sep += "--------|"
    lines.append(header)
    lines.append(sep)

    for s in strategies:
        s_outcomes = _strategy_outcomes(outcomes, s)
        with_5d = [o for o in s_outcomes if o.day5_correct is not None]
        if with_5d:
            correct_5d = sum(1 for o in with_5d if o.day5_correct)
            acc_5d = correct_5d / len(with_5d) * 100
        else:
            acc_5d = 0

    # Build rows
    for s in strategies:
        s_outcomes = _strategy_outcomes(outcomes, s)
        with_5d = [o for o in s_outcomes if o.day5_correct is not None]
        correct_5d = sum(1 for o in with_5d if o.day5_correct) if with_5d else 0
        total_5d = len(with_5d)

        row_data = {
            "5-day accuracy": f"{correct_5d}/{total_5d} ({correct_5d / total_5d * 100:.1f}%)" if total_5d > 0 else "N/A",
        }

        # Calculate 5-day P&L (BUY: gain if up, SELL: gain if down)
        pnl_5d = 0.0
        for o in with_5d:
            if o.day5_change_pct is not None and o.decision_date_close > 0:
                position_value = 10000.0
                shares = position_value / o.decision_date_close
                if o.decision == "BUY":
                    pnl_5d += o.decision_date_close * shares * (o.day5_change_pct / 100)
                elif o.decision == "SELL":
                    pnl_5d -= o.decision_date_close * shares * (o.day5_change_pct / 100)

        row_data["5-day P&L"] = f"${pnl_5d:,.2f}"

    # Rebuild as proper table
    lines = []
    lines.append(header)
    lines.append(sep)

    # 5-day accuracy row
    row = "| 5-day accuracy |"
    for s in strategies:
        s_outcomes = _strategy_outcomes(outcomes, s)
        with_5d = [o for o in s_outcomes if o.day5_correct is not None]
        if with_5d:
            correct_5d = sum(1 for o in with_5d if o.day5_correct)
            row += f" {correct_5d}/{len(with_5d)} ({correct_5d / len(with_5d) * 100:.1f}%) |"
        else:
            row += " N/A |"
    lines.append(row)

    # 5-day P&L row
    row = "| 5-day P&L |"
    for s in strategies:
        s_outcomes = _strategy_outcomes(outcomes, s)
        with_5d = [o for o in s_outcomes if o.day5_correct is not None and o.day5_change_pct is not None]
        pnl_5d = 0.0
        for o in with_5d:
            if o.decision_date_close > 0:
                position_value = 10000.0
                shares = position_value / o.decision_date_close
                if o.decision == "BUY":
                    pnl_5d += o.decision_date_close * shares * (o.day5_change_pct / 100)
                elif o.decision == "SELL":
                    pnl_5d -= o.decision_date_close * shares * (o.day5_change_pct / 100)
        row += f" ${pnl_5d:,.2f} |"
    lines.append(row)

    return "\n".join(lines)


def _build_v2_conclusion(outcomes: List[TradeOutcome],
                         strategies: List[str]) -> str:
    """Build conclusion paragraph."""
    stats = {s: _calc_stats(_strategy_outcomes(outcomes, s)) for s in strategies}

    active = [s for s in strategies if stats[s]["count"] > 0]
    if not active:
        return "No completed outcomes to draw conclusions from."

    best_accuracy = max(active, key=lambda s: stats[s]["accuracy"])
    best_pnl = max(active, key=lambda s: stats[s]["total_pnl"])

    lines = []
    lines.append(f"- **Most accurate strategy:** {best_accuracy} ({stats[best_accuracy]['accuracy']:.1f}%)")
    lines.append(f"- **Highest P&L strategy:** {best_pnl} (${stats[best_pnl]['total_pnl']:,.2f})")

    # Compare single vs multi
    single_strats = [s for s in active if s.startswith("single_")]
    multi_strats = [s for s in active if s.startswith("ma_") or s == "multi_agent"]

    if single_strats and multi_strats:
        best_single_acc = max(single_strats, key=lambda s: stats[s]["accuracy"])
        best_multi_acc = max(multi_strats, key=lambda s: stats[s]["accuracy"])

        if stats[best_single_acc]["accuracy"] >= stats[best_multi_acc]["accuracy"]:
            lines.append(f"- Single-agent ({best_single_acc}: {stats[best_single_acc]['accuracy']:.1f}%) "
                         f"matched or exceeded multi-agent ({best_multi_acc}: {stats[best_multi_acc]['accuracy']:.1f}%) accuracy.")
        else:
            diff = stats[best_multi_acc]["accuracy"] - stats[best_single_acc]["accuracy"]
            lines.append(f"- Multi-agent ({best_multi_acc}: {stats[best_multi_acc]['accuracy']:.1f}%) "
                         f"outperformed single-agent ({best_single_acc}: {stats[best_single_acc]['accuracy']:.1f}%) "
                         f"by {diff:.1f} percentage points.")

    return "\n".join(lines)


def _build_v2_monthly_table(outcomes: List[TradeOutcome],
                            strategies: List[str],
                            dates: List[str]) -> str:
    """Build monthly breakdown table."""
    lines = []
    header = "| Month |"
    sep = "|-------|"
    for s in strategies:
        header += f" {s} |"
        sep += "--------|"
    lines.append(header)
    lines.append(sep)

    for date in dates:
        month_label = date[:7]
        row = f"| {month_label} |"
        for s in strategies:
            month_outcomes = [
                o for o in outcomes
                if o.strategy_name == s and o.trade_date[:7] == month_label
            ]
            validated = [o for o in month_outcomes if o.validated]
            correct = sum(1 for o in validated if o.decision_correct)
            total = len(validated)
            if total > 0:
                row += f" {correct}/{total} ({correct / total * 100:.0f}%) |"
            else:
                row += " N/A |"
        lines.append(row)

    return "\n".join(lines)


def _build_v2_ticker_table(outcomes: List[TradeOutcome],
                           strategies: List[str],
                           tickers: List[str]) -> str:
    """Build per-ticker breakdown table."""
    lines = []
    header = "| Ticker |"
    sep = "|--------|"
    for s in strategies:
        header += f" {s} Acc | {s} P&L |"
        sep += "--------|---------|"
    lines.append(header)
    lines.append(sep)

    for ticker in tickers:
        row = f"| {ticker} |"
        for s in strategies:
            ticker_outcomes = [
                o for o in outcomes
                if o.strategy_name == s and o.ticker == ticker
            ]
            stats = _calc_stats(ticker_outcomes)
            row += f" {stats['accuracy']:.0f}% | ${stats['total_pnl']:,.0f} |"
        lines.append(row)

    return "\n".join(lines)


# ───────────────────────────────────────────────────────
# Multi-horizon report helpers
# ───────────────────────────────────────────────────────


def _get_horizon_labels(outcomes: List[TradeOutcome]) -> List[str]:
    """Extract sorted horizon labels present in outcome data."""
    labels = set()
    for o in outcomes:
        if o.horizon_outcomes:
            labels.update(o.horizon_outcomes.keys())
    order = list(HORIZONS.keys())
    return [l for l in order if l in labels]


def _build_horizon_accuracy_table(outcomes: List[TradeOutcome],
                                   strategy: str) -> str:
    """Build per-horizon accuracy table for a single strategy."""
    s_outcomes = [o for o in _strategy_outcomes(outcomes, strategy)
                  if o.horizon_outcomes]

    if not s_outcomes:
        return f"No multi-horizon data available for {strategy}."

    lines = []
    lines.append("| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |")
    lines.append("|---------|---------|-------|----------|---------------------|------------------|")

    for label in _get_horizon_labels(outcomes):
        correct_returns = []
        wrong_returns = []
        total = 0

        for o in s_outcomes:
            h = o.horizon_outcomes.get(label)
            if h is None:
                continue
            total += 1
            if h["correct"]:
                correct_returns.append(h["change_pct"])
            else:
                wrong_returns.append(h["change_pct"])

        correct_count = len(correct_returns)
        accuracy = (correct_count / total * 100) if total > 0 else 0
        avg_correct = (sum(correct_returns) / len(correct_returns)) if correct_returns else 0
        avg_wrong = (sum(wrong_returns) / len(wrong_returns)) if wrong_returns else 0

        lines.append(
            f"| {label:<7} | {correct_count:<7} | {total:<5} | "
            f"{accuracy:>5.1f}% | {avg_correct:>+19.2f}% | {avg_wrong:>+16.2f}% |"
        )

    return "\n".join(lines)


def _build_horizon_comparison_table(outcomes: List[TradeOutcome],
                                     strategies: List[str]) -> str:
    """Build cross-model comparison table by horizon."""
    lines = []
    header = "| Horizon |"
    sep = "|---------|"
    for s in strategies:
        header += f" {s} |"
        sep += "---------|"
    header += " Winner |"
    sep += "--------|"

    lines.append(header)
    lines.append(sep)

    for label in _get_horizon_labels(outcomes):
        row = f"| {label:<7} |"
        best_acc = -1
        best_strategy = ""
        accuracies = {}

        for s in strategies:
            s_outcomes = [o for o in _strategy_outcomes(outcomes, s)
                          if o.horizon_outcomes and label in o.horizon_outcomes]
            if s_outcomes:
                correct = sum(1 for o in s_outcomes
                              if o.horizon_outcomes[label].get("correct"))
                total = len(s_outcomes)
                acc = correct / total * 100
                accuracies[s] = acc
                if acc > best_acc:
                    best_acc = acc
                    best_strategy = s
            else:
                accuracies[s] = 0

        for s in strategies:
            acc = accuracies[s]
            formatted = f"{acc:.1f}%"
            if s == best_strategy and len(strategies) > 1:
                formatted = f"**{formatted}**"
            row += f" {formatted:>8} |"

        row += f" {best_strategy} |" if best_strategy else " N/A |"
        lines.append(row)

    # Overall row
    row = "| **Overall** |"
    overall_best_acc = -1
    overall_best = ""
    for s in strategies:
        s_outcomes = [o for o in _strategy_outcomes(outcomes, s)
                      if o.horizon_outcomes]
        total_correct = 0
        total_count = 0
        for o in s_outcomes:
            for h_label in _get_horizon_labels(outcomes):
                h = o.horizon_outcomes.get(h_label)
                if h:
                    total_count += 1
                    if h["correct"]:
                        total_correct += 1
        acc = (total_correct / total_count * 100) if total_count > 0 else 0
        formatted = f"{acc:.1f}%"
        if acc > overall_best_acc:
            overall_best_acc = acc
            overall_best = s
        row += f" {formatted:>8} |"
    row += f" {overall_best} |"
    lines.append(row)

    return "\n".join(lines)


def _build_consistency_table(outcomes: List[TradeOutcome],
                              strategies: List[str]) -> str:
    """Build cross-horizon consistency analysis."""
    lines = []

    # Part 1: Consistency scores
    lines.append("### Cross-Horizon Consistency\n")
    lines.append("| Metric | " + " | ".join(strategies) + " |")
    lines.append("|--------|" + "|".join(["---------|"] * len(strategies)))

    consistency_data = {}
    for s in strategies:
        s_outcomes = [o for o in _strategy_outcomes(outcomes, s)
                      if o.horizon_outcomes and len(o.horizon_outcomes) >= 3]
        all_correct = sum(1 for o in s_outcomes
                          if all(h["correct"] for h in o.horizon_outcomes.values()))
        all_wrong = sum(1 for o in s_outcomes
                        if not any(h["correct"] for h in o.horizon_outcomes.values()))
        mixed = len(s_outcomes) - all_correct - all_wrong
        total = len(s_outcomes)
        consistency_data[s] = {
            "all_correct": all_correct, "all_wrong": all_wrong,
            "mixed": mixed, "total": total,
        }

    for metric_label, metric_key in [
        ("All horizons correct", "all_correct"),
        ("All horizons wrong", "all_wrong"),
        ("Mixed results", "mixed"),
    ]:
        row = f"| {metric_label} |"
        for s in strategies:
            d = consistency_data[s]
            total = d["total"]
            val = d[metric_key]
            pct = (val / total * 100) if total > 0 else 0
            row += f" {val}/{total} ({pct:.0f}%) |"
        lines.append(row)

    lines.append("")

    # Part 2: Short vs Long term
    # Dynamically pick shortest 2 and longest 2 horizon labels
    h_labels = _get_horizon_labels(outcomes)
    short_labels = h_labels[:2] if len(h_labels) >= 2 else h_labels
    long_labels = h_labels[-2:] if len(h_labels) >= 2 else h_labels
    short_str = "+".join(short_labels)
    long_str = "+".join(long_labels)

    lines.append("### Short-Term vs Long-Term Accuracy\n")
    lines.append(f"| Model | Short ({short_str} avg) | Long ({long_str} avg) | Delta |")
    lines.append("|-------|-------------------|-------------------|-------|")

    for s in strategies:
        s_outcomes = [o for o in _strategy_outcomes(outcomes, s)
                      if o.horizon_outcomes]

        short_correct = 0
        short_total = 0
        long_correct = 0
        long_total = 0

        for o in s_outcomes:
            for h_label in short_labels:
                h = o.horizon_outcomes.get(h_label)
                if h:
                    short_total += 1
                    if h["correct"]:
                        short_correct += 1
            for h_label in long_labels:
                h = o.horizon_outcomes.get(h_label)
                if h:
                    long_total += 1
                    if h["correct"]:
                        long_correct += 1

        short_acc = (short_correct / short_total * 100) if short_total > 0 else 0
        long_acc = (long_correct / long_total * 100) if long_total > 0 else 0
        delta = long_acc - short_acc

        lines.append(f"| {s} | {short_acc:.1f}% | {long_acc:.1f}% | {delta:+.1f}% |")

    # Part 3: Decision-type by horizon
    lines.append("")
    lines.append("### BUY Decision Accuracy by Horizon\n")
    header = "| Horizon |"
    sep = "|---------|"
    for s in strategies:
        header += f" {s} |"
        sep += "---------|"
    lines.append(header)
    lines.append(sep)

    for h_label in _get_horizon_labels(outcomes):
        row = f"| {h_label:<7} |"
        for s in strategies:
            buys = [o for o in _strategy_outcomes(outcomes, s)
                    if o.decision == "BUY" and o.horizon_outcomes
                    and h_label in o.horizon_outcomes]
            if buys:
                correct = sum(1 for o in buys if o.horizon_outcomes[h_label]["correct"])
                acc = correct / len(buys) * 100
                row += f" {acc:>5.1f}% |"
            else:
                row += "   N/A |"
        lines.append(row)

    lines.append("")
    lines.append("### SELL Decision Accuracy by Horizon\n")
    lines.append(header)
    lines.append(sep)

    for h_label in _get_horizon_labels(outcomes):
        row = f"| {h_label:<7} |"
        for s in strategies:
            sells = [o for o in _strategy_outcomes(outcomes, s)
                     if o.decision == "SELL" and o.horizon_outcomes
                     and h_label in o.horizon_outcomes]
            if sells:
                correct = sum(1 for o in sells if o.horizon_outcomes[h_label]["correct"])
                acc = correct / len(sells) * 100
                row += f" {acc:>5.1f}% |"
            else:
                row += "   N/A |"
        lines.append(row)

    return "\n".join(lines)


# ───────────────────────────────────────────────────────
# V3 Analysis: Baselines, Walk-Forward, Statistics
# ───────────────────────────────────────────────────────


def compute_free_baselines(
    outcomes: List[TradeOutcome],
    horizons: Optional[List[str]] = None,
) -> Dict[str, Dict[str, Dict[str, Any]]]:
    """Compute Always-BUY, Always-SELL, Momentum-5d baselines from market data.

    Returns: {baseline_name: {horizon: {correct, total, accuracy}}}
    Uses horizon_outcomes already computed in each TradeOutcome.
    """
    import yfinance as yf

    h_labels = horizons or _get_horizon_labels(outcomes)
    baselines = {
        "Always-BUY": {},
        "Always-SELL": {},
        "Momentum-5d": {},
        "Random (expected)": {},
    }

    # Collect unique (ticker, date) pairs from outcomes
    seen = set()
    unique_outcomes = []
    for o in outcomes:
        key = (o.ticker, o.trade_date)
        if key not in seen and o.horizon_outcomes:
            seen.add(key)
            unique_outcomes.append(o)

    for h_label in h_labels:
        buy_correct = 0
        sell_correct = 0
        momentum_correct = 0
        total = 0

        for o in unique_outcomes:
            h = o.horizon_outcomes.get(h_label)
            if h is None:
                continue
            total += 1
            change_pct = h["change_pct"]

            # Always-BUY: correct if price rose > transaction cost
            if change_pct > 0.15:
                buy_correct += 1
            # Always-SELL: correct if price fell > transaction cost
            if change_pct < -0.15:
                sell_correct += 1

            # Momentum-5d: check 5-day trend before decision date
            try:
                decision_date = datetime.strptime(o.trade_date, "%Y-%m-%d")
                start = decision_date - timedelta(days=14)
                ticker_data = yf.Ticker(o.ticker)
                hist = ticker_data.history(start=start, end=decision_date)
                if len(hist) >= 5:
                    momentum = hist["Close"].iloc[-1] - hist["Close"].iloc[-5]
                    if momentum > 0 and change_pct > 0.15:
                        momentum_correct += 1
                    elif momentum < 0 and change_pct < -0.15:
                        momentum_correct += 1
                    elif abs(momentum) < 0.001:
                        from tradingagents.backtest.outcome_tracker import HOLD_THRESHOLDS
                        threshold = HOLD_THRESHOLDS.get(h_label, 0.5)
                        if abs(change_pct) < threshold:
                            momentum_correct += 1
            except Exception:
                pass

        baselines["Always-BUY"][h_label] = {
            "correct": buy_correct, "total": total,
            "accuracy": (buy_correct / total * 100) if total > 0 else 0,
        }
        baselines["Always-SELL"][h_label] = {
            "correct": sell_correct, "total": total,
            "accuracy": (sell_correct / total * 100) if total > 0 else 0,
        }
        baselines["Momentum-5d"][h_label] = {
            "correct": momentum_correct, "total": total,
            "accuracy": (momentum_correct / total * 100) if total > 0 else 0,
        }
        baselines["Random (expected)"][h_label] = {
            "correct": round(total / 3), "total": total,
            "accuracy": 33.3,
        }

    return baselines


def _build_baselines_table(
    baselines: Dict,
    outcomes: List[TradeOutcome],
    strategies: List[str],
) -> str:
    """Build combined baselines + model comparison table."""
    h_labels = _get_horizon_labels(outcomes)
    lines = []
    lines.append("## Free Baselines Comparison\n")

    header = "| Strategy |"
    sep = "|----------|"
    for h in h_labels:
        header += f" {h} |"
        sep += "------|"
    lines.append(header)
    lines.append(sep)

    # Model accuracies
    for s in strategies:
        row = f"| **{s}** |"
        s_outcomes = [o for o in _strategy_outcomes(outcomes, s)
                      if o.horizon_outcomes]
        for h in h_labels:
            total = sum(1 for o in s_outcomes if h in o.horizon_outcomes)
            correct = sum(1 for o in s_outcomes
                         if h in o.horizon_outcomes
                         and o.horizon_outcomes[h]["correct"])
            acc = (correct / total * 100) if total > 0 else 0
            row += f" {acc:.1f}% |"
        lines.append(row)

    # Baseline rows
    for b_name in ["Always-BUY", "Always-SELL", "Momentum-5d", "Random (expected)"]:
        row = f"| {b_name} |"
        for h in h_labels:
            data = baselines.get(b_name, {}).get(h, {})
            acc = data.get("accuracy", 0)
            row += f" {acc:.1f}% |"
        lines.append(row)

    return "\n".join(lines)


def compute_walk_forward_split(
    outcomes: List[TradeOutcome],
    strategies: List[str],
    split_date: str = "2025-09-01",
) -> str:
    """Build walk-forward (in-sample vs out-of-sample) analysis table."""
    lines = []
    lines.append("## Walk-Forward Validation\n")
    lines.append(f"**Split date:** {split_date} "
                 f"(Period 1: before, Period 2: after)\n")

    header = "| Strategy | Period 1 (in-sample) | Period 2 (out-of-sample) | Delta |"
    sep = "|----------|---------------------|-------------------------|-------|"
    lines.append(header)
    lines.append(sep)

    for s in strategies:
        s_outcomes = [o for o in _strategy_outcomes(outcomes, s)]
        p1 = [o for o in s_outcomes if o.trade_date < split_date]
        p2 = [o for o in s_outcomes if o.trade_date >= split_date]

        p1_correct = sum(1 for o in p1 if o.decision_correct)
        p1_acc = (p1_correct / len(p1) * 100) if p1 else 0
        p2_correct = sum(1 for o in p2 if o.decision_correct)
        p2_acc = (p2_correct / len(p2) * 100) if p2 else 0
        delta = p2_acc - p1_acc

        lines.append(
            f"| {s} | {p1_correct}/{len(p1)} ({p1_acc:.1f}%) "
            f"| {p2_correct}/{len(p2)} ({p2_acc:.1f}%) "
            f"| {delta:+.1f}% |"
        )

    # Per-horizon walk-forward (next-day is just one view; also show horizon split)
    h_labels = _get_horizon_labels(outcomes)
    if h_labels:
        lines.append("")
        lines.append("### Walk-Forward by Horizon\n")

        header2 = "| Strategy | Horizon | P1 Acc | P2 Acc | Delta |"
        sep2 = "|----------|---------|--------|--------|-------|"
        lines.append(header2)
        lines.append(sep2)

        for s in strategies:
            s_outcomes = [o for o in _strategy_outcomes(outcomes, s)
                          if o.horizon_outcomes]
            for h in h_labels:
                p1 = [o for o in s_outcomes
                      if o.trade_date < split_date and h in o.horizon_outcomes]
                p2 = [o for o in s_outcomes
                      if o.trade_date >= split_date and h in o.horizon_outcomes]

                p1c = sum(1 for o in p1 if o.horizon_outcomes[h]["correct"])
                p1a = (p1c / len(p1) * 100) if p1 else 0
                p2c = sum(1 for o in p2 if o.horizon_outcomes[h]["correct"])
                p2a = (p2c / len(p2) * 100) if p2 else 0
                d = p2a - p1a

                lines.append(
                    f"| {s} | {h} | {p1a:.1f}% | {p2a:.1f}% | {d:+.1f}% |"
                )

    return "\n".join(lines)


def compute_statistical_tests(
    outcomes: List[TradeOutcome],
    strategies: List[str],
    baselines: Dict,
) -> str:
    """Compute binomial test vs Always-BUY and bootstrap CIs."""
    from scipy import stats

    lines = []
    lines.append("## Statistical Significance\n")

    h_labels = _get_horizon_labels(outcomes)

    # Binomial test: is model accuracy significantly different from Always-BUY?
    lines.append("### Binomial Test vs Always-BUY Baseline\n")
    header = "| Strategy | Horizon | Model Acc | Baseline Acc | p-value | Significant? |"
    sep = "|----------|---------|-----------|-------------|---------|-------------|"
    lines.append(header)
    lines.append(sep)

    for s in strategies:
        s_outcomes = [o for o in _strategy_outcomes(outcomes, s)
                      if o.horizon_outcomes]
        for h in h_labels:
            h_outcomes = [o for o in s_outcomes if h in o.horizon_outcomes]
            n = len(h_outcomes)
            if n == 0:
                continue
            k = sum(1 for o in h_outcomes if o.horizon_outcomes[h]["correct"])
            model_acc = k / n * 100

            baseline_data = baselines.get("Always-BUY", {}).get(h, {})
            baseline_acc = baseline_data.get("accuracy", 33.3)
            p0 = baseline_acc / 100

            # Two-sided binomial test
            p_value = stats.binomtest(k, n, p0).pvalue
            sig = "Yes" if p_value < 0.05 else "No"

            lines.append(
                f"| {s} | {h} | {model_acc:.1f}% | {baseline_acc:.1f}% "
                f"| {p_value:.4f} | {sig} |"
            )

    # Bootstrap CI for overall accuracy
    lines.append("")
    lines.append("### Bootstrap 95% CI (Next-Day Accuracy)\n")
    lines.append("| Strategy | Accuracy | 95% CI | n |")
    lines.append("|----------|----------|--------|---|")

    for s in strategies:
        s_outcomes = list(_strategy_outcomes(outcomes, s))
        n = len(s_outcomes)
        if n == 0:
            continue
        correct = [1 if o.decision_correct else 0 for o in s_outcomes]
        observed = sum(correct) / n * 100

        # Bootstrap
        rng = np.random.default_rng(42)
        boot_accs = []
        for _ in range(10000):
            sample = rng.choice(correct, size=n, replace=True)
            boot_accs.append(np.mean(sample) * 100)
        ci_low = np.percentile(boot_accs, 2.5)
        ci_high = np.percentile(boot_accs, 97.5)

        lines.append(
            f"| {s} | {observed:.1f}% | [{ci_low:.1f}%, {ci_high:.1f}%] | {n} |"
        )

    return "\n".join(lines)


# ───────────────────────────────────────────────────────
# Cross-run comparison
# ───────────────────────────────────────────────────────

def compare_runs(run_id_a: str, run_id_b: str):
    """Generate a head-to-head comparison of two V2 backtest runs.

    Finds overlapping ticker/date pairs and compares decisions, accuracy, P&L.
    """
    eval_dir = Path("results/evaluations")

    def _load_run(run_id: str) -> Dict:
        cp_path = eval_dir / f"backtest_{run_id}" / "checkpoint.json"
        if not cp_path.exists():
            # Try without backtest_ prefix
            cp_path = eval_dir / run_id / "checkpoint.json"
        if not cp_path.exists():
            print(f"Checkpoint not found for run: {run_id}")
            sys.exit(1)
        return load_checkpoint(cp_path)

    cp_a = _load_run(run_id_a)
    cp_b = _load_run(run_id_b)

    # Extract run metadata
    config_a = cp_a.get("run_config", {})
    config_b = cp_b.get("run_config", {})
    label_a = f"{config_a.get('llm_provider', '?')}/{config_a.get('deep_think_llm', '?')}"
    label_b = f"{config_b.get('llm_provider', '?')}/{config_b.get('deep_think_llm', '?')}"

    # Index completed outcomes by (ticker, date) for each run
    outcomes_a = {}
    for task_key, task in cp_a.get("tasks", {}).items():
        if task.get("status") == "completed":
            parts = task_key.split("|")
            if len(parts) >= 2:
                ticker, date = parts[0], parts[1]
                outcomes_a[(ticker, date)] = task

    outcomes_b = {}
    for task_key, task in cp_b.get("tasks", {}).items():
        if task.get("status") == "completed":
            parts = task_key.split("|")
            if len(parts) >= 2:
                ticker, date = parts[0], parts[1]
                outcomes_b[(ticker, date)] = task

    # Find overlapping pairs
    overlap = sorted(set(outcomes_a.keys()) & set(outcomes_b.keys()))

    lines = []
    lines.append(f"# Head-to-Head Comparison")
    lines.append(f"")
    lines.append(f"**Run A:** {cp_a.get('run_id', run_id_a)} — {label_a}")
    lines.append(f"**Run B:** {cp_b.get('run_id', run_id_b)} — {label_b}")
    lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
    lines.append(f"**Overlapping pairs:** {len(overlap)} (same ticker + date)")
    lines.append("")

    if not overlap:
        lines.append("No overlapping ticker/date pairs found between the two runs.")
        report = "\n".join(lines)
        print(report)
        return

    # Detail table
    lines.append("## Decision-by-Decision Comparison\n")
    lines.append("| Ticker | Date | Run A Decision | Run B Decision | "
                 "Market Move | A Correct | B Correct |")
    lines.append("|--------|------|---------------|---------------|"
                 "------------|-----------|-----------|")

    a_correct_count = 0
    b_correct_count = 0
    a_total = 0
    b_total = 0
    a_pnl = 0.0
    b_pnl = 0.0

    for ticker, date in overlap:
        ta = outcomes_a[(ticker, date)]
        tb = outcomes_b[(ticker, date)]

        dec_a = ta.get("decision", "?")
        dec_b = tb.get("decision", "?")
        pnl_a = ta.get("pnl", 0) or 0
        pnl_b = tb.get("pnl", 0) or 0
        correct_a = ta.get("decision_correct")
        correct_b = tb.get("decision_correct")

        a_pnl += pnl_a
        b_pnl += pnl_b

        if correct_a is not None:
            a_total += 1
            if correct_a:
                a_correct_count += 1
        if correct_b is not None:
            b_total += 1
            if correct_b:
                b_correct_count += 1

        # Approximate market move from P&L direction
        move_str = "N/A"
        d5_a = ta.get("day5_change_pct")
        d5_b = tb.get("day5_change_pct")
        if d5_a is not None:
            move_str = f"{d5_a:+.1f}% (5d)"

        ca_str = "Y" if correct_a else "N" if correct_a is not None else "?"
        cb_str = "Y" if correct_b else "N" if correct_b is not None else "?"

        lines.append(f"| {ticker} | {date} | {dec_a} | {dec_b} | "
                     f"{move_str} | {ca_str} | {cb_str} |")

    lines.append("")

    # Aggregate comparison
    lines.append("## Aggregate Comparison\n")
    lines.append("| Metric | Run A | Run B |")
    lines.append("|--------|-------|-------|")

    a_acc = (a_correct_count / a_total * 100) if a_total > 0 else 0
    b_acc = (b_correct_count / b_total * 100) if b_total > 0 else 0
    lines.append(f"| Accuracy (next-day) | {a_acc:.1f}% ({a_correct_count}/{a_total}) "
                 f"| {b_acc:.1f}% ({b_correct_count}/{b_total}) |")
    lines.append(f"| Total P&L | ${a_pnl:,.2f} | ${b_pnl:,.2f} |")

    # Decision distribution
    for label, outcomes_dict in [("Run A", outcomes_a), ("Run B", outcomes_b)]:
        decisions = [t.get("decision", "?") for (tk, dt), t in outcomes_dict.items()
                     if (tk, dt) in overlap]
        buy_pct = decisions.count("BUY") / len(decisions) * 100 if decisions else 0
        sell_pct = decisions.count("SELL") / len(decisions) * 100 if decisions else 0
        hold_pct = decisions.count("HOLD") / len(decisions) * 100 if decisions else 0
        lines.append(f"| {label} decisions | BUY {buy_pct:.0f}% / SELL {sell_pct:.0f}% / "
                     f"HOLD {hold_pct:.0f}% | |")

    # Failure comparison
    failed_a = count_by_status(cp_a, "failed")
    failed_b = count_by_status(cp_b, "failed")
    total_a = len(cp_a.get("tasks", {}))
    total_b = len(cp_b.get("tasks", {}))
    lines.append(f"| Failure rate | {failed_a}/{total_a} "
                 f"({failed_a/total_a*100:.0f}%) | {failed_b}/{total_b} "
                 f"({failed_b/total_b*100:.0f}%) |")
    lines.append("")

    # Winner
    if a_acc > b_acc:
        lines.append(f"**Winner (accuracy):** Run A ({label_a}) by {a_acc - b_acc:.1f} pp")
    elif b_acc > a_acc:
        lines.append(f"**Winner (accuracy):** Run B ({label_b}) by {b_acc - a_acc:.1f} pp")
    else:
        lines.append("**Accuracy tied.**")

    if a_pnl > b_pnl:
        lines.append(f"**Winner (P&L):** Run A ({label_a}) by ${a_pnl - b_pnl:,.2f}")
    elif b_pnl > a_pnl:
        lines.append(f"**Winner (P&L):** Run B ({label_b}) by ${b_pnl - a_pnl:,.2f}")

    report = "\n".join(lines)

    # Save report
    benchmarks_dir = Path("reports/benchmarks")
    benchmarks_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    report_path = benchmarks_dir / f"V2_COMPARE_{date_str}_{run_id_a}_vs_{run_id_b}.md"
    report_path.write_text(report)
    print(report)
    print(f"\nComparison saved to: {report_path}")


# ───────────────────────────────────────────────────────
# CLI entry point
# ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="V2 backtest harness (look-ahead free, no HOLD fallback)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--tickers", type=str,
                        default="AMBA,RAPT,ET,ZTS",
                        help="Comma-separated tickers (default: AMBA,RAPT,ET,ZTS)")
    parser.add_argument("--start", type=str, default="2025-01-28",
                        help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default="2026-01-28",
                        help="End date (YYYY-MM-DD)")
    parser.add_argument("--articles-per-month", type=int, default=50,
                        help="News articles per analysis")

    # Model configuration
    parser.add_argument("--provider", type=str,
                        default=os.getenv("LLM_PROVIDER", "openai"),
                        help="LLM provider: openai, anthropic, google (default: from .env or openai)")
    parser.add_argument("--deep-model", type=str,
                        default=os.getenv("DEEP_THINK_LLM", "gpt-5.1-codex-mini"),
                        help="Deep thinking model (default: from .env or gpt-5.1-codex-mini)")
    parser.add_argument("--quick-model", type=str,
                        default=os.getenv("QUICK_THINK_LLM", "gpt-5.1-codex-mini"),
                        help="Quick thinking model (default: from .env or gpt-5.1-codex-mini)")
    parser.add_argument("--backend-url", type=str,
                        default=os.getenv("LLM_BACKEND_URL", ""),
                        help="LLM backend URL override")

    # Run modes
    parser.add_argument("--resume", nargs="?", const="latest",
                        help="Resume a backtest (optionally specify run_id)")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Retry failed tasks when resuming")
    parser.add_argument("--report", type=str,
                        help="Generate report from run_id")
    parser.add_argument("--list-runs", action="store_true",
                        help="List all v2 backtest runs")

    # Comparison mode
    parser.add_argument("--compare", nargs=2, metavar=("RUN_A", "RUN_B"),
                        help="Compare two runs head-to-head (provide two run IDs)")

    # Operational flags
    parser.add_argument("--dry-run", action="store_true",
                        help="Show task count and estimated cost, then exit without running")
    parser.add_argument("--wait-on-rate-limit", action="store_true",
                        help="Auto-retry on rate limits (sleep + retry up to 3 times per task)")

    # Ablation flags
    parser.add_argument("--no-memory", action="store_true",
                        help="Disable ChromaDB memory")
    parser.add_argument("--ace", action="store_true",
                        help="Enable ACE framework")
    parser.add_argument("--single-only", action="store_true",
                        help="Only run single-agent strategy (skip multi-agent)")
    parser.add_argument("--multi-only", action="store_true",
                        help="Only run multi-agent strategy (skip single-agent)")

    # Multi-horizon benchmark flags
    parser.add_argument("--strategies", type=str, default=None,
                        help="Comma-separated strategy names (e.g., "
                             "single_sonnet-4-5,single_opus-4-6). "
                             "Overrides auto-generated strategies.")
    parser.add_argument("--date-mode", type=str, choices=["monthly", "tri-monthly"],
                        default="monthly",
                        help="Date generation: monthly (end-of-month) or "
                             "tri-monthly (10th, 20th, end-of-month)")
    parser.add_argument("--multi-horizon", action="store_true",
                        help="Enable multi-horizon validation (1w, 2w, 4w, 8w, 13w)")
    parser.add_argument("--horizons", type=str, default=None,
                        help="Comma-separated horizons to validate "
                             "(e.g. 1d,3d,1w,2w,4w). Default: all in HORIZONS")

    args = parser.parse_args()

    # Parse --horizons into a list
    if args.horizons:
        args.selected_horizons = [h.strip() for h in args.horizons.split(",")]
        if not args.multi_horizon:
            args.multi_horizon = True  # --horizons implies --multi-horizon
    else:
        args.selected_horizons = None  # use all HORIZONS

    # ── Compare mode (no config needed) ──
    if args.compare:
        compare_runs(args.compare[0], args.compare[1])
        return

    # Build config from args
    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = args.provider
    config["deep_think_llm"] = args.deep_model
    config["quick_think_llm"] = args.quick_model
    if args.backend_url:
        config["backend_url"] = args.backend_url
    elif args.provider == "anthropic" and config.get("backend_url", "").startswith("https://api.openai.com"):
        config["backend_url"] = "https://api.anthropic.com"
    if args.no_memory:
        config["memory_enabled"] = False
    if args.ace:
        config["ace_enabled"] = True

    # ── List runs mode ──
    if args.list_runs:
        eval_dir = Path("results/evaluations")
        if not eval_dir.exists():
            print("No evaluations directory found.")
            sys.exit(0)
        v2_runs = list(eval_dir.glob("backtest_v2_*/checkpoint.json"))
        if not v2_runs:
            print("No v2 runs found.")
            sys.exit(0)
        for cp_file in sorted(v2_runs):
            cp = load_checkpoint(cp_file)
            total = len(cp["tasks"])
            done = count_by_status(cp, "completed")
            failed = count_by_status(cp, "failed")
            strats = ", ".join(cp["config"].get("strategies", []))
            print(f"  {cp['run_id']}  {done}/{total} done, {failed} failed  |  {strats}")
        return

    # ── Report only mode ──
    if args.report:
        run_dir = Path(f"results/evaluations/backtest_{args.report}")
        cp_path = run_dir / "checkpoint.json"
        if not cp_path.exists():
            print(f"Checkpoint not found: {cp_path}")
            sys.exit(1)
        checkpoint = load_checkpoint(cp_path)
        generate_v2_report(checkpoint, run_dir)
        return

    # ── Resume mode ──
    if args.resume:
        if args.resume == "latest":
            eval_dir = Path("results/evaluations")
            v2_checkpoints = list(eval_dir.glob("backtest_v2_*/checkpoint.json"))
            if not v2_checkpoints:
                print("No v2 checkpoints found.")
                sys.exit(1)
            cp_path = max(v2_checkpoints, key=lambda p: p.stat().st_mtime)
        else:
            cp_path = Path(f"results/evaluations/backtest_{args.resume}/checkpoint.json")

        if not cp_path.exists():
            print(f"Checkpoint not found: {cp_path}")
            sys.exit(1)

        checkpoint = load_checkpoint(cp_path)
        print(f"Resuming run {checkpoint['run_id']}")

        # Restore model tiers
        saved_tiers = checkpoint.get("config", {}).get("model_tiers")
        if saved_tiers:
            config["_model_tiers"] = saved_tiers

        # Restore provider/model from checkpoint run_config
        saved_config = checkpoint.get("run_config", {})
        if saved_config:
            config["llm_provider"] = saved_config.get("llm_provider", config["llm_provider"])
            config["deep_think_llm"] = saved_config.get("deep_think_llm", config["deep_think_llm"])
            config["quick_think_llm"] = saved_config.get("quick_think_llm", config["quick_think_llm"])

        if args.retry_failed:
            reset_count = 0
            for key, task in checkpoint["tasks"].items():
                if task["status"] == "failed":
                    checkpoint["tasks"][key] = {"status": "pending"}
                    reset_count += 1
            if reset_count:
                print(f"Reset {reset_count} failed tasks to pending")

        run_v2_backtest(checkpoint, cp_path, config,
                        wait_on_rate_limit=args.wait_on_rate_limit)
        return

    # ── New backtest mode ──
    tickers = [t.strip().upper() for t in args.tickers.split(",")]

    if args.date_mode == "tri-monthly":
        dates = get_tri_monthly_dates(args.start, args.end)
    else:
        dates = get_monthly_dates(args.start, args.end)

    if not dates:
        print(f"No {args.date_mode} dates between {args.start} and {args.end}")
        sys.exit(1)

    # Build strategies from model names
    if args.strategies:
        # Explicit strategy list: parse names and map to full model IDs
        strategies = [s.strip() for s in args.strategies.split(",")]
        model_tiers = {}

        for strategy in strategies:
            if strategy.startswith("single_"):
                short_name = strategy[len("single_"):]
                model_id = STRATEGY_MODEL_MAP.get(short_name, f"claude-{short_name}")
                model_tiers[strategy] = {"type": "single", "model": model_id}
            elif strategy.startswith("sentiment_"):
                sentiment_model = strategy[len("sentiment_"):]
                from tradingagents.models.sentiment import SENTIMENT_MODELS
                if sentiment_model not in SENTIMENT_MODELS:
                    print(f"Warning: Unknown sentiment model: {sentiment_model}. "
                          f"Available: {list(SENTIMENT_MODELS.keys())}")
                else:
                    model_tiers[strategy] = {"type": "sentiment", "model": sentiment_model}
            elif strategy.startswith("ml_") and strategy.endswith("_pruned"):
                ml_model = strategy[len("ml_"):-len("_pruned")]
                if ml_model not in ("xgboost", "lightgbm"):
                    print(f"Warning: Unknown ML model: {ml_model}. "
                          f"Available: xgboost, lightgbm")
                else:
                    model_tiers[strategy] = {"type": "ml_pruned", "model": ml_model}
            elif strategy.startswith("ml_"):
                ml_model = strategy[len("ml_"):]
                if ml_model not in ("xgboost", "lightgbm"):
                    print(f"Warning: Unknown ML model: {ml_model}. "
                          f"Available: xgboost, lightgbm")
                else:
                    model_tiers[strategy] = {"type": "ml", "model": ml_model}
            elif strategy.startswith("ts_kronos"):
                # Parse: ts_kronos, ts_kronos_mini, ts_kronos_small, ts_kronos_base
                parts = strategy.split("_")
                model_size = parts[2] if len(parts) > 2 else "mini"
                if model_size not in ("mini", "small", "base"):
                    print(f"Warning: Unknown Kronos size: {model_size}. "
                          f"Available: mini, small, base")
                else:
                    model_tiers[strategy] = {"type": "timeseries", "model": model_size}
            elif strategy.startswith("ensemble_"):
                # Parse: ensemble_METHOD or ensemble_METHOD+sub1+sub2+...
                remainder = strategy[len("ensemble_"):]
                valid_methods = ("majority_vote", "weighted_vote", "adaptive")
                if "+" in remainder:
                    parts = remainder.split("+")
                    method = parts[0]
                    sub_strats = [_normalize_sub_strategy(s) for s in parts[1:]]
                else:
                    method = remainder
                    sub_strats = None  # use default
                if method not in valid_methods:
                    print(f"Warning: Unknown ensemble method: {method}. "
                          f"Available: {valid_methods}")
                else:
                    model_tiers[strategy] = {
                        "type": "ensemble", "model": method,
                        "sub_strategies": sub_strats,
                    }
            elif strategy.startswith("ma_"):
                parts_str = strategy[len("ma_"):]
                if "+" in parts_str:
                    deep_short, quick_short = parts_str.split("+", 1)
                else:
                    deep_short = quick_short = parts_str
                deep_model = STRATEGY_MODEL_MAP.get(deep_short, f"claude-{deep_short}")
                quick_model = STRATEGY_MODEL_MAP.get(quick_short, f"claude-{quick_short}")
                model_tiers[strategy] = {
                    "type": "multi_agent",
                    "deep": deep_model,
                    "quick": quick_model,
                }
            else:
                print(f"Warning: Unknown strategy format: {strategy}")
    else:
        deep_short = _short_model(args.deep_model)
        quick_short = _short_model(args.quick_model)

        strategies = []
        model_tiers = {}

        if not args.single_only:
            if args.deep_model == args.quick_model:
                ma_name = f"ma_{deep_short}"
            else:
                ma_name = f"ma_{deep_short}+{quick_short}"
            strategies.append(ma_name)
            model_tiers[ma_name] = {
                "type": "multi_agent",
                "deep": args.deep_model,
                "quick": args.quick_model,
            }

        if not args.multi_only:
            s_deep = f"single_{deep_short}"
            if s_deep not in model_tiers:
                strategies.append(s_deep)
                model_tiers[s_deep] = {"type": "single", "model": args.deep_model}

            if args.deep_model != args.quick_model:
                s_quick = f"single_{quick_short}"
                if s_quick not in model_tiers:
                    strategies.append(s_quick)
                    model_tiers[s_quick] = {"type": "single", "model": args.quick_model}

    config["_model_tiers"] = model_tiers

    total_tasks = len(tickers) * len(dates) * len(strategies)

    date_label = "tri-monthly" if args.date_mode == "tri-monthly" else "monthly"

    print(f"V2 Backtest Configuration:")
    print(f"  Provider: {args.provider}")
    print(f"  Deep model: {args.deep_model}")
    print(f"  Quick model: {args.quick_model}")
    print(f"  Tickers: {', '.join(tickers)}")
    print(f"  Dates: {len(dates)} {date_label} snapshots ({dates[0]} to {dates[-1]})")
    print(f"  Strategies: {', '.join(strategies)}")
    print(f"  Total tasks: {total_tasks}")
    if args.multi_horizon:
        n_horizons = len(args.selected_horizons) if args.selected_horizons else len(HORIZONS)
        h_list = ", ".join(args.selected_horizons) if args.selected_horizons else ", ".join(HORIZONS.keys())
        print(f"  Multi-horizon: {n_horizons} horizons ({h_list})")
        print(f"  Total validation outcomes: {total_tasks * n_horizons}")

    # ── Dry run: show cost estimate and exit ──
    if args.dry_run:
        print(f"\n{'─' * 50}")
        print(f"DRY RUN — Cost Estimate")
        print(f"{'─' * 50}")
        total_cost = 0.0
        for s_name, tier in model_tiers.items():
            s_type = "multi_agent" if tier.get("type") == "multi_agent" else "single"
            model = tier.get("model") or tier.get("deep", "unknown")
            cost_per = _estimate_cost(model, s_type)
            s_tasks = len(tickers) * len(dates)
            s_cost = cost_per * s_tasks
            total_cost += s_cost
            print(f"  {s_name:<30} {s_tasks:>3} tasks × ${cost_per:.2f} = ${s_cost:.2f}")
        print(f"{'─' * 50}")
        print(f"  TOTAL ESTIMATED COST: ${total_cost:.2f}")
        print(f"{'─' * 50}")
        if args.multi_horizon:
            print(f"  Multi-horizon: {n_horizons} horizons × {total_tasks} tasks = "
                  f"{total_tasks * n_horizons} validation outcomes")
        if args.date_mode == "tri-monthly":
            print(f"  Date mode: tri-monthly (10th, 20th, end-of-month)")
        print(f"\nRemove --dry-run to start the backtest.")
        return

    checkpoint = create_v2_checkpoint(tickers, dates, strategies, config, args)

    run_dir = Path(f"results/evaluations/backtest_{checkpoint['run_id']}")
    cp_path = run_dir / "checkpoint.json"

    save_checkpoint(checkpoint, cp_path)
    print(f"Checkpoint created: {cp_path}")

    run_v2_backtest(checkpoint, cp_path, config,
                    wait_on_rate_limit=args.wait_on_rate_limit)


if __name__ == "__main__":
    main()

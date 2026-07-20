#!/usr/bin/env python3
"""
Resumable backtest harness with checkpoint system.

Runs multi-agent and single-agent baselines across tickers and dates,
with full checkpoint/resume support for surviving API rate limits.

Usage:
    # Start new backtest
    python -m cli.evaluate --tickers RAPT,SUPN,ZTS,SNOW,AMBA,ET \
      --backtest --start 2025-01-28 --end 2026-01-28 \
      --interval monthly --articles-per-month 50

    # Resume after interruption
    python -m cli.evaluate --resume

    # Resume specific run
    python -m cli.evaluate --resume bt_20260128_143022

    # Generate report from completed run
    python -m cli.evaluate --report bt_20260128_143022
"""

import argparse
import json
import os
import sys
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.backtest.outcome_tracker import (
    TradeOutcome,
    validate_outcome_against_market,
)
from tradingagents.graph.signal_processing import (
    extract_decision_from_text,
    extract_confidence_from_text,
    extract_technical_signals,
    format_technical_opinion,
    apply_hard_override,
)


# ───────────────────────────────────────────────────────
# Date generation
# ───────────────────────────────────────────────────────

def get_monthly_dates(start: str, end: str) -> List[str]:
    """Generate last-trading-day-of-month dates between start and end.

    Uses last calendar day as approximation; yfinance handles
    non-trading-day adjustment during validation.
    """
    from calendar import monthrange

    start_dt = datetime.strptime(start, "%Y-%m-%d")
    end_dt = datetime.strptime(end, "%Y-%m-%d")
    dates = []

    current = start_dt.replace(day=1)
    while current <= end_dt:
        _, last_day = monthrange(current.year, current.month)
        month_end = current.replace(day=last_day)
        if month_end <= end_dt:
            dates.append(month_end.strftime("%Y-%m-%d"))
        current = (current.replace(day=28) + timedelta(days=4)).replace(day=1)

    return dates


# ───────────────────────────────────────────────────────
# Checkpoint management
# ───────────────────────────────────────────────────────

def _build_run_config(config: Dict) -> Dict[str, Any]:
    """Build a serializable snapshot of the runtime config for logging.

    Captures all settings that affect backtest results so each run is
    fully reproducible from its checkpoint alone.
    """
    return {
        "llm_provider": config.get("llm_provider", "openai"),
        "deep_think_llm": config.get("deep_think_llm", "gpt-4o"),
        "quick_think_llm": config.get("quick_think_llm", "gpt-4o-mini"),
        "backend_url": config.get("backend_url", ""),
        "memory_enabled": config.get("memory_enabled", True),
        "ace_enabled": config.get("ace_enabled", False),
        "data_vendors": config.get("data_vendors", {}),
        "tool_vendors": config.get("tool_vendors", {}),
        "news_limits": config.get("news_limits", {}),
        "sentiment_limits": config.get("sentiment_limits", {}),
        "news_monthly_bucketing": config.get("news_monthly_bucketing", False),
        "news_company_fallback": config.get("news_company_fallback", True),
        "max_debate_rounds": config.get("max_debate_rounds", 1),
        "max_risk_discuss_rounds": config.get("max_risk_discuss_rounds", 1),
    }


def create_checkpoint(args, tickers: List[str], dates: List[str],
                      strategies: List[str], config: Dict = None) -> Dict[str, Any]:
    """Create a new checkpoint structure."""
    run_id = f"bt_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    tasks = {}
    for ticker in tickers:
        for date in dates:
            for strategy in strategies:
                key = f"{ticker}|{date}|{strategy}"
                tasks[key] = {"status": "pending"}

    checkpoint = {
        "run_id": run_id,
        "config": {
            "tickers": tickers,
            "start_date": args.start,
            "end_date": args.end,
            "interval": args.interval,
            "articles_per_month": args.articles_per_month,
            "strategies": strategies,
            "memory_enabled": not args.no_memory,
        },
        "analysis_dates": dates,
        "tasks": tasks,
        "outcomes": [],
        "last_updated": datetime.now().isoformat(),
    }

    # Store full runtime config for reproducibility
    if config:
        checkpoint["run_config"] = _build_run_config(config)

    # Store model tiers if using --models flag
    model_tiers = getattr(args, '_model_tiers', None)
    if model_tiers is None and hasattr(args, 'models') and args.models:
        # model_tiers are built in main() and stored in config
        pass  # Will be added from config before saving
    return checkpoint


def save_checkpoint(checkpoint: Dict, path: Path):
    """Save checkpoint to disk."""
    checkpoint["last_updated"] = datetime.now().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w") as f:
        json.dump(checkpoint, f, indent=2)


def load_checkpoint(path: Path) -> Dict[str, Any]:
    """Load checkpoint from disk."""
    with open(path) as f:
        return json.load(f)


def find_latest_checkpoint() -> Optional[Path]:
    """Find the most recent checkpoint file."""
    eval_dir = Path("results/evaluations")
    if not eval_dir.exists():
        return None

    checkpoints = list(eval_dir.glob("backtest_*/checkpoint.json"))
    if not checkpoints:
        return None

    return max(checkpoints, key=lambda p: p.stat().st_mtime)


def count_by_status(checkpoint: Dict, status: str) -> int:
    """Count tasks with a given status."""
    return sum(1 for t in checkpoint["tasks"].values() if t["status"] == status)


# ───────────────────────────────────────────────────────
# Strategy runners
# ───────────────────────────────────────────────────────

def _save_raw_dataset(results_dir: Path, ticker: str, date: str):
    """Fetch and save raw data for single-agent replay.

    Saves the same raw data the multi-agent system uses so single-agent
    baselines can replay with different models without re-fetching.
    """
    import json
    from datetime import datetime as dt, timedelta
    from tradingagents.agents.utils.agent_utils import (
        get_stock_data, get_current_quote, get_indicators,
        get_fundamentals, get_balance_sheet, get_cashflow,
        get_income_statement, get_news, get_global_news,
        get_social_sentiment,
    )

    dataset_path = results_dir / "datasets" / ticker / date / f"{ticker}_{date}_raw_dataset.json"
    if dataset_path.exists():
        return  # Already cached

    end_date = date
    start_dt = dt.strptime(date, "%Y-%m-%d") - timedelta(days=90)
    start_date = start_dt.strftime("%Y-%m-%d")

    from tradingagents.baselines.single_agent import _fetch_data_safe

    data = {
        "market_data": _fetch_data_safe(get_stock_data, ticker, start_date, end_date),
        "quote_data": _fetch_data_safe(get_current_quote, ticker, date),
        "indicators_data": _fetch_data_safe(get_indicators, ticker, start_date, end_date),
        "fundamentals_data": _fetch_data_safe(get_fundamentals, ticker, date),
        "balance_sheet_data": _fetch_data_safe(get_balance_sheet, ticker),
        "cashflow_data": _fetch_data_safe(get_cashflow, ticker),
        "income_data": _fetch_data_safe(get_income_statement, ticker),
        "news_data": _fetch_data_safe(get_news, ticker, start_date, end_date),
        "global_news_data": _fetch_data_safe(get_global_news, ticker, date),
        "sentiment_data": _fetch_data_safe(get_social_sentiment, ticker, start_date, end_date),
        "cached_at": dt.now().isoformat(),
        "ticker": ticker,
        "trade_date": date,
    }

    dataset_path.parent.mkdir(parents=True, exist_ok=True)
    with open(dataset_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"DATASET SAVED: {ticker} {date} -> {dataset_path}")


def run_multi_agent(ticker: str, date: str, config: Dict,
                    articles: int = 50) -> Dict[str, Any]:
    """Run the full multi-agent analysis."""
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    graph = TradingAgentsGraph(
        ["market", "social", "news", "fundamentals"],
        config=config,
        debug=False,
    )

    # Check for cached reports
    results_dir = Path(config.get("results_dir", "./results"))
    cached_reports = _load_cached_reports(results_dir, ticker, date)

    final_state, decision = graph.propagate(
        ticker, date, cached_reports=cached_reports if cached_reports else None
    )

    # Save analyst reports (LLM-generated) for future cache use
    _save_reports(results_dir, ticker, date, final_state)

    # Save raw data for single-agent replay (separate from reports)
    try:
        _save_raw_dataset(results_dir, ticker, date)
    except Exception as e:
        print(f"Warning: Failed to save raw dataset for {ticker} {date}: {e}")

    confidence = extract_confidence_from_text(
        final_state.get("final_trade_decision", "")
    )

    return {
        "decision": decision,
        "confidence": confidence,
        "strategy": "multi_agent",
        "raw_response": final_state.get("final_trade_decision", ""),
    }


def run_single_agent(ticker: str, date: str, model: str,
                     config: Dict, articles: int = 50) -> Dict[str, Any]:
    """Run single-agent baseline analysis."""
    from tradingagents.baselines.single_agent import SingleAgentBaseline

    baseline = SingleAgentBaseline(model=model, config=config)
    result = baseline.analyze(ticker, date, news_article_limit=articles)

    return {
        "decision": result["decision"],
        "confidence": result["confidence"],
        "strategy": f"single_{model}",
        "raw_response": result.get("raw_response", ""),
        "input_tokens": result.get("input_tokens", 0),
        "output_tokens": result.get("output_tokens", 0),
        "llm_calls": result.get("llm_calls", 1),
    }


def _load_cached_reports(results_dir: Path, ticker: str, date: str) -> Dict:
    """Load cached analyst reports if available."""
    report_dir = results_dir / ticker / date / "reports"
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


def _save_reports(results_dir: Path, ticker: str, date: str,
                  final_state: Dict):
    """Save analyst reports for cache reuse."""
    report_dir = results_dir / ticker / date / "reports"
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
# Main backtest loop
# ───────────────────────────────────────────────────────

def run_backtest(checkpoint: Dict, checkpoint_path: Path, config: Dict):
    """Execute the backtest, processing all pending/failed tasks."""
    total = len(checkpoint["tasks"])
    completed = count_by_status(checkpoint, "completed")
    failed = count_by_status(checkpoint, "failed")

    print(f"\n{'=' * 70}")
    print(f"  Backtest: {', '.join(checkpoint['config']['tickers'])}")
    print(f"  Period: {checkpoint['config']['start_date']} to {checkpoint['config']['end_date']}")
    print(f"  Strategies: {', '.join(checkpoint['config']['strategies'])}")
    print(f"  Progress: {completed}/{total} completed, {failed} failed")
    print(f"{'=' * 70}\n")

    articles = checkpoint["config"].get("articles_per_month", 50)
    deep_model = config.get("deep_think_llm", "gpt-4o")
    quick_model = config.get("quick_think_llm", "gpt-4o-mini")

    # Model tier lookup for parameterized strategies
    model_tiers = config.get("_model_tiers", {})

    for task_key, task in checkpoint["tasks"].items():
        if task["status"] in ("completed", "skipped"):
            continue

        ticker, date, strategy = task_key.split("|")
        completed = count_by_status(checkpoint, "completed")
        idx = completed + 1

        print(f"[{idx:>3}/{total}] {ticker:<6} | {date} | {strategy:<20} | ", end="", flush=True)

        try:
            checkpoint["tasks"][task_key]["status"] = "running"
            save_checkpoint(checkpoint, checkpoint_path)

            if model_tiers and strategy in model_tiers:
                # Model-parameterized strategy
                tier = model_tiers[strategy]
                if tier["type"] == "multi_agent":
                    # Override config with the specified models for this tier
                    tier_config = config.copy()
                    tier_config["deep_think_llm"] = tier["deep"]
                    tier_config["quick_think_llm"] = tier["quick"]
                    result = run_multi_agent(ticker, date, tier_config, articles)
                    result["strategy"] = strategy
                else:
                    result = run_single_agent(ticker, date, tier["model"], config, articles)
                    result["strategy"] = strategy
            elif strategy == "multi_agent":
                result = run_multi_agent(ticker, date, config, articles)
            elif strategy == "single_deep":
                result = run_single_agent(ticker, date, deep_model, config, articles)
            elif strategy == "single_quick":
                result = run_single_agent(ticker, date, quick_model, config, articles)
            else:
                print(f"Unknown strategy: {strategy}")
                checkpoint["tasks"][task_key]["status"] = "skipped"
                save_checkpoint(checkpoint, checkpoint_path)
                continue

            # Create and validate outcome
            strategy_label = result.get("strategy", strategy)
            outcome = TradeOutcome(
                ticker=ticker,
                trade_date=date,
                decision=result["decision"],
                confidence=result.get("confidence"),
                strategy_name=strategy_label,
                llm_calls=result.get("llm_calls", 0),
                input_tokens=result.get("input_tokens", 0),
                output_tokens=result.get("output_tokens", 0),
            )
            outcome = validate_outcome_against_market(outcome)

            # Update checkpoint
            checkpoint["tasks"][task_key] = {
                "status": "completed",
                "decision": outcome.decision,
                "confidence": outcome.confidence,
                "pnl": outcome.pnl,
                "decision_correct": outcome.decision_correct,
                "completed_at": datetime.now().isoformat(),
            }
            checkpoint["outcomes"].append(outcome.to_dict())

            # Print result
            pnl_str = f"${outcome.pnl:>+8.2f}" if outcome.validated else "    N/A "
            correct_str = "Y" if outcome.decision_correct else "N" if outcome.decision_correct is not None else "?"
            conf_str = f"{outcome.confidence:.2f}" if outcome.confidence else " N/A"
            print(f"{outcome.decision:<4} {conf_str} | {pnl_str} {correct_str}")

        except Exception as e:
            err_name = type(e).__name__
            checkpoint["tasks"][task_key] = {
                "status": "failed",
                "error": err_name,
                "message": str(e)[:200],
                "failed_at": datetime.now().isoformat(),
            }

            # Check for rate limit / quota errors
            if "rate" in err_name.lower() or "quota" in err_name.lower() or "429" in str(e):
                print(f"RATE LIMITED")
                print(f"\nProgress saved. Resume with: python -m cli.evaluate --resume {checkpoint['run_id']}")
                save_checkpoint(checkpoint, checkpoint_path)
                return
            else:
                print(f"FAILED ({err_name})")
                # Log full traceback for debugging
                traceback.print_exc()

        save_checkpoint(checkpoint, checkpoint_path)

    # All tasks processed
    completed = count_by_status(checkpoint, "completed")
    failed = count_by_status(checkpoint, "failed")
    print(f"\nBacktest complete: {completed}/{total} completed, {failed} failed")

    # Generate report
    run_dir = checkpoint_path.parent
    generate_report(checkpoint, run_dir)


# ───────────────────────────────────────────────────────
# Report generation
# ───────────────────────────────────────────────────────

def generate_report(checkpoint: Dict, run_dir: Path):
    """Generate backtest report from checkpoint data."""
    outcomes = [TradeOutcome.from_dict(o) for o in checkpoint.get("outcomes", [])]
    if not outcomes:
        print("No outcomes to report on.")
        return

    config = checkpoint["config"]
    tickers = config["tickers"]
    strategies = config["strategies"]
    dates = checkpoint.get("analysis_dates", [])

    report_lines = []
    report_lines.append(f"# TradingAgents Benchmark Report")
    report_lines.append(f"**Run ID:** {checkpoint['run_id']}")
    report_lines.append(f"**Date:** {datetime.now().strftime('%Y-%m-%d')}")
    report_lines.append(f"**Period:** {config['start_date']} to {config['end_date']}")
    report_lines.append(f"**Tickers:** {', '.join(tickers)} ({len(tickers)} tickers)")
    report_lines.append(f"**Dates:** {len(dates)} monthly snapshots")
    report_lines.append(f"**Analyses:** {len(outcomes)} completed\n")

    # Runtime configuration used
    run_config = checkpoint.get("run_config", {})
    if run_config:
        report_lines.append("## Configuration\n")
        report_lines.append(f"| Setting | Value |")
        report_lines.append(f"|---------|-------|")
        report_lines.append(f"| LLM Provider | {run_config.get('llm_provider', 'N/A')} |")
        report_lines.append(f"| Deep Think LLM | {run_config.get('deep_think_llm', 'N/A')} |")
        report_lines.append(f"| Quick Think LLM | {run_config.get('quick_think_llm', 'N/A')} |")
        report_lines.append(f"| Memory Enabled | {run_config.get('memory_enabled', 'N/A')} |")
        report_lines.append(f"| ACE Enabled | {run_config.get('ace_enabled', 'N/A')} |")
        vendors = run_config.get("data_vendors", {})
        for category, vendor in vendors.items():
            report_lines.append(f"| Vendor: {category} | {vendor} |")
        model_tiers = checkpoint.get("config", {}).get("model_tiers", {})
        if model_tiers:
            report_lines.append(f"| Model Tiers | {len(model_tiers)} configurations |")
            for name, tier in model_tiers.items():
                if tier.get("type") == "multi_agent":
                    report_lines.append(f"| &nbsp;&nbsp;{name} | deep={tier['deep']}, quick={tier['quick']} |")
                else:
                    report_lines.append(f"| &nbsp;&nbsp;{name} | model={tier['model']} |")
        report_lines.append("")

    # Executive summary table
    report_lines.append("## Executive Summary\n")
    report_lines.append(_build_summary_table(outcomes, strategies))

    # Conclusion
    report_lines.append("\n## Conclusion\n")
    report_lines.append(_build_conclusion(outcomes, strategies))

    # Detailed results by month
    report_lines.append("\n## Results by Month\n")
    report_lines.append(_build_monthly_table(outcomes, strategies, dates))

    # By ticker
    report_lines.append("\n## Results by Ticker\n")
    report_lines.append(_build_ticker_table(outcomes, strategies, tickers))

    # Decision distribution
    report_lines.append("\n## Decision Distribution\n")
    report_lines.append(_build_decision_distribution(outcomes, strategies))

    # Confidence calibration
    report_lines.append("\n## Confidence Analysis\n")
    report_lines.append(_build_confidence_analysis(outcomes, strategies))

    report_text = "\n".join(report_lines)

    # Save to run directory
    report_path = run_dir / "report.md"
    report_path.write_text(report_text)
    print(f"Report saved to: {report_path}")

    # Also save to reports/benchmarks/
    benchmarks_dir = Path("reports/benchmarks")
    benchmarks_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now().strftime("%Y-%m-%d")
    symbols_str = "_".join(tickers[:3])
    benchmark_path = benchmarks_dir / f"BENCHMARK_REPORT_{date_str}_{symbols_str}.md"
    benchmark_path.write_text(report_text)
    print(f"Benchmark report saved to: {benchmark_path}")

    # Save outcomes JSON (includes run config for traceability)
    outcomes_data = {
        "run_id": checkpoint["run_id"],
        "generated_at": datetime.now().isoformat(),
        "run_config": checkpoint.get("run_config", {}),
        "model_tiers": checkpoint.get("config", {}).get("model_tiers", {}),
        "backtest_config": {
            "tickers": tickers,
            "start_date": config["start_date"],
            "end_date": config["end_date"],
            "strategies": strategies,
            "analysis_dates": dates,
        },
        "outcomes": [o.to_dict() for o in outcomes],
    }
    outcomes_path = run_dir / "outcomes.json"
    with open(outcomes_path, "w") as f:
        json.dump(outcomes_data, f, indent=2)
    print(f"Outcomes saved to: {outcomes_path}")


def _strategy_outcomes(outcomes: List[TradeOutcome], strategy: str) -> List[TradeOutcome]:
    """Filter outcomes by strategy name."""
    return [o for o in outcomes if o.strategy_name == strategy]


def _calc_stats(outcomes: List[TradeOutcome]) -> Dict[str, Any]:
    """Calculate summary statistics for a set of outcomes."""
    if not outcomes:
        return {"accuracy": 0, "total_pnl": 0, "avg_conf": 0,
                "buy_pct": 0, "sell_pct": 0, "hold_pct": 0, "count": 0}

    validated = [o for o in outcomes if o.validated]
    correct = sum(1 for o in validated if o.decision_correct)
    total = len(validated)

    buy_count = sum(1 for o in outcomes if o.decision == "BUY")
    sell_count = sum(1 for o in outcomes if o.decision == "SELL")
    hold_count = sum(1 for o in outcomes if o.decision == "HOLD")
    n = len(outcomes)

    confidences = [o.confidence for o in outcomes if o.confidence is not None]
    avg_conf = sum(confidences) / len(confidences) if confidences else 0

    total_pnl = sum(o.pnl for o in validated)

    # Max drawdown approximation (cumulative PnL)
    cum_pnl = 0
    peak = 0
    max_dd = 0
    for o in sorted(validated, key=lambda x: x.trade_date):
        cum_pnl += o.pnl
        if cum_pnl > peak:
            peak = cum_pnl
        dd = peak - cum_pnl
        if dd > max_dd:
            max_dd = dd

    return {
        "accuracy": (correct / total * 100) if total > 0 else 0,
        "correct": correct,
        "total": total,
        "total_pnl": total_pnl,
        "avg_conf": avg_conf,
        "buy_pct": (buy_count / n * 100) if n > 0 else 0,
        "sell_pct": (sell_count / n * 100) if n > 0 else 0,
        "hold_pct": (hold_count / n * 100) if n > 0 else 0,
        "count": n,
        "max_drawdown": max_dd,
    }


def _build_summary_table(outcomes: List[TradeOutcome],
                         strategies: List[str]) -> str:
    """Build the executive summary table."""
    lines = []
    header = "| Metric |"
    sep = "|--------|"
    for s in strategies:
        header += f" {s} |"
        sep += "--------|"

    lines.append(header)
    lines.append(sep)

    stats = {s: _calc_stats(_strategy_outcomes(outcomes, s)) for s in strategies}

    # Find winner for each metric
    def winner_col(metric, higher_better=True):
        vals = {s: stats[s][metric] for s in strategies}
        if higher_better:
            best = max(vals, key=vals.get)
        else:
            best = min(vals, key=vals.get)
        return best

    rows = [
        ("Overall accuracy", "accuracy", "{:.1f}%", True),
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


def _build_conclusion(outcomes: List[TradeOutcome],
                      strategies: List[str]) -> str:
    """Build conclusion paragraph."""
    stats = {s: _calc_stats(_strategy_outcomes(outcomes, s)) for s in strategies}

    best_accuracy = max(strategies, key=lambda s: stats[s]["accuracy"])
    best_pnl = max(strategies, key=lambda s: stats[s]["total_pnl"])

    lines = []
    lines.append(f"- **Most accurate strategy:** {best_accuracy} ({stats[best_accuracy]['accuracy']:.1f}%)")
    lines.append(f"- **Highest P&L strategy:** {best_pnl} (${stats[best_pnl]['total_pnl']:,.2f})")

    ma_stats = stats.get("multi_agent", {})
    for s in strategies:
        if s != "multi_agent" and stats[s].get("accuracy", 0) >= ma_stats.get("accuracy", 0):
            lines.append(f"- {s} matched or exceeded multi-agent accuracy, suggesting the multi-agent architecture may not justify its additional cost.")
            break
    else:
        if ma_stats.get("accuracy", 0) > 0:
            lines.append(f"- Multi-agent outperformed baselines on accuracy, suggesting the architecture adds value.")

    return "\n".join(lines)


def _build_monthly_table(outcomes: List[TradeOutcome],
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
        month_label = date[:7]  # YYYY-MM
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
                row += f" {correct}/{total} ({correct/total*100:.0f}%) |"
            else:
                row += " N/A |"
        lines.append(row)

    return "\n".join(lines)


def _build_ticker_table(outcomes: List[TradeOutcome],
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


def _build_decision_distribution(outcomes: List[TradeOutcome],
                                 strategies: List[str]) -> str:
    """Build decision distribution analysis."""
    lines = []
    for s in strategies:
        s_outcomes = _strategy_outcomes(outcomes, s)
        stats = _calc_stats(s_outcomes)
        lines.append(f"**{s}:** BUY {stats['buy_pct']:.0f}% | SELL {stats['sell_pct']:.0f}% | HOLD {stats['hold_pct']:.0f}% (n={stats['count']})")
    return "\n\n".join(lines)


def _build_confidence_analysis(outcomes: List[TradeOutcome],
                               strategies: List[str]) -> str:
    """Build confidence calibration analysis."""
    lines = []
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

        # Split into high/low confidence buckets
        high_conf = [o for o in validated if o.confidence >= 0.6]
        low_conf = [o for o in validated if o.confidence < 0.6]

        high_correct = sum(1 for o in high_conf if o.decision_correct) if high_conf else 0
        low_correct = sum(1 for o in low_conf if o.decision_correct) if low_conf else 0

        high_acc = (high_correct / len(high_conf) * 100) if high_conf else 0
        low_acc = (low_correct / len(low_conf) * 100) if low_conf else 0

        avg_conf = sum(o.confidence for o in with_conf) / len(with_conf)

        lines.append(f"**{s}:** Avg confidence: {avg_conf:.2f} | "
                     f"High-confidence accuracy: {high_acc:.0f}% ({len(high_conf)} trades) | "
                     f"Low-confidence accuracy: {low_acc:.0f}% ({len(low_conf)} trades) | "
                     f"Parseable: {len(with_conf)}/{len(s_outcomes)} ({len(with_conf)/len(s_outcomes)*100:.0f}%)")

    return "\n\n".join(lines)


# ───────────────────────────────────────────────────────
# CLI entry point
# ───────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Resumable backtest harness for TradingAgents",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    parser.add_argument("--tickers", type=str,
                        default="RAPT,SUPN,ZTS,SNOW,AMBA,ET",
                        help="Comma-separated tickers")
    parser.add_argument("--backtest", action="store_true",
                        help="Start a new backtest")
    parser.add_argument("--start", type=str, default="2025-01-28",
                        help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end", type=str, default="2026-01-28",
                        help="End date (YYYY-MM-DD)")
    parser.add_argument("--interval", type=str, default="monthly",
                        choices=["monthly"], help="Analysis interval")
    parser.add_argument("--articles-per-month", type=int, default=50,
                        help="News articles per analysis")

    parser.add_argument("--resume", nargs="?", const="latest",
                        help="Resume a backtest (optionally specify run_id)")
    parser.add_argument("--retry-failed", action="store_true",
                        help="Retry failed tasks when resuming")
    parser.add_argument("--fresh", action="store_true",
                        help="Force fresh start, ignore existing checkpoints")

    parser.add_argument("--report", type=str,
                        help="Generate report from run_id without running new analyses")
    parser.add_argument("--compare", type=str,
                        help="Compare multiple runs (comma-separated run_ids)")
    parser.add_argument("--list-runs", action="store_true",
                        help="List all backtest runs and their status")

    parser.add_argument("--no-memory", action="store_true",
                        help="Disable ChromaDB memory (ablation)")
    parser.add_argument("--ace", action="store_true",
                        help="Enable ACE framework (ablation)")

    parser.add_argument("--baseline-model", type=str,
                        help="Override model for single-agent baselines")

    parser.add_argument("--models", type=str, action="append", default=[],
                        help="Model tier as 'deep:quick' pair. Can be specified multiple times. "
                             "Each pair adds multi_agent_<deep>, single_<deep>, single_<quick> strategies. "
                             "Example: --models gpt-4o:gpt-4o-mini --models gpt-5.2:gpt-5.1-codex-mini")

    parser.add_argument("--single-only", action="store_true",
                        help="Only run single-agent baselines (skip multi_agent)")
    parser.add_argument("--replay", type=str, action="append", default=[],
                        help="Replay cached datasets with new models (no data fetching). "
                             "Specify model names, e.g. --replay gpt-4o --replay gpt-4o-mini. "
                             "Only runs single-agent strategies using saved datasets from results/datasets/")

    args = parser.parse_args()

    # Build config
    config = DEFAULT_CONFIG.copy()
    if args.no_memory:
        config["memory_enabled"] = False
    if args.ace:
        config["ace_enabled"] = True

    # Determine strategies based on --models flag
    if args.models:
        strategies = []
        model_tiers = {}  # strategy_name -> model config

        def _short(model: str) -> str:
            """Shorten model name for strategy labels."""
            return (model.replace("gpt-", "")
                    .replace("-2025-12-11", "")
                    .replace("-2025", ""))

        seen_single = set()  # track single-agent models already added

        for model_pair in args.models:
            parts = model_pair.split(":")
            if len(parts) == 2:
                deep, quick = parts[0].strip(), parts[1].strip()
            elif len(parts) == 1:
                deep = quick = parts[0].strip()
            else:
                print(f"Invalid model pair: {model_pair}. Use 'deep:quick' format.")
                sys.exit(1)

            deep_short = _short(deep)
            quick_short = _short(quick)

            # Multi-agent strategy: name reflects both models when different
            if not args.single_only:
                if deep == quick:
                    ma_name = f"ma_{deep_short}"
                else:
                    ma_name = f"ma_{deep_short}+{quick_short}"
                if ma_name not in model_tiers:
                    strategies.append(ma_name)
                    model_tiers[ma_name] = {"type": "multi_agent", "deep": deep, "quick": quick}

            # Single-agent strategies: deduplicate across model pairs
            for model in [deep, quick]:
                s_name = f"single_{_short(model)}"
                if model not in seen_single:
                    seen_single.add(model)
                    strategies.append(s_name)
                    model_tiers[s_name] = {"type": "single", "model": model}

        # Store model tiers in config for run_backtest to use
        config["_model_tiers"] = model_tiers
    else:
        strategies = ["multi_agent", "single_deep", "single_quick"]

    # ── List runs mode ──
    if args.list_runs:
        eval_dir = Path("results/evaluations")
        if not eval_dir.exists():
            print("No evaluations directory found.")
            sys.exit(0)
        for cp_file in sorted(eval_dir.glob("backtest_*/checkpoint.json")):
            cp = load_checkpoint(cp_file)
            total = len(cp["tasks"])
            done = count_by_status(cp, "completed")
            failed = count_by_status(cp, "failed")
            strats = ", ".join(cp["config"].get("strategies", []))
            print(f"  {cp['run_id']}  {done}/{total} done, {failed} failed  |  {strats}")
        return

    # ── Compare runs mode ──
    if args.compare:
        run_ids = [r.strip() for r in args.compare.split(",")]
        all_outcomes = []
        all_strategies = []
        for rid in run_ids:
            cp_path = Path(f"results/evaluations/backtest_{rid}/checkpoint.json")
            if not cp_path.exists():
                print(f"Run not found: {rid}")
                continue
            cp = load_checkpoint(cp_path)
            outcomes = [TradeOutcome.from_dict(o) for o in cp.get("outcomes", [])]
            all_outcomes.extend(outcomes)
            all_strategies.extend(cp["config"].get("strategies", []))

        all_strategies = list(dict.fromkeys(all_strategies))  # deduplicate, preserve order
        if not all_outcomes:
            print("No outcomes found across specified runs.")
            sys.exit(1)

        # Generate combined report
        run_dir = Path("results/evaluations")
        print(f"\n{'=' * 70}")
        print(f"  Cross-Run Comparison: {', '.join(run_ids)}")
        print(f"  Strategies: {', '.join(all_strategies)}")
        print(f"  Total outcomes: {len(all_outcomes)}")
        print(f"{'=' * 70}\n")
        print(_build_summary_table(all_outcomes, all_strategies))
        print()
        print(_build_decision_distribution(all_outcomes, all_strategies))
        print()
        print(_build_confidence_analysis(all_outcomes, all_strategies))
        return

    # ── Replay mode (cached datasets, new models, single-agent only) ──
    if args.replay:
        tickers = [t.strip().upper() for t in args.tickers.split(",")]
        dates = get_monthly_dates(args.start, args.end)
        results_dir = Path(config.get("results_dir", "./results"))

        # Check which ticker/dates have cached datasets
        available = []
        for ticker in tickers:
            for date in dates:
                # Check both new and legacy filenames for backward compatibility
                new_path = results_dir / "datasets" / ticker / date / f"{ticker}_{date}_raw_dataset.json"
                legacy_path = results_dir / "datasets" / ticker / date / "dataset.json"
                if new_path.exists() or legacy_path.exists():
                    available.append((ticker, date))

        if not available:
            print("No cached datasets found. Run a backtest first to populate datasets.")
            print(f"Checked: {results_dir / 'datasets'}")
            sys.exit(1)

        replay_strategies = []
        model_tiers = {}
        for model in args.replay:
            def _short(m):
                return m.replace("gpt-", "").replace("-2025-12-11", "").replace("-2025", "")
            s_name = f"single_{_short(model)}"
            replay_strategies.append(s_name)
            model_tiers[s_name] = {"type": "single", "model": model}

        config["_model_tiers"] = model_tiers

        print(f"\n{'=' * 70}")
        print(f"  REPLAY MODE: Using cached datasets (no data API calls)")
        print(f"  Tickers: {', '.join(tickers)}")
        print(f"  Cached dates available: {len(available)} ticker/date pairs")
        print(f"  Models: {', '.join(args.replay)}")
        print(f"  Total tasks: {len(available) * len(replay_strategies)}")
        print(f"{'=' * 70}\n")

        # Create checkpoint for replay run
        replay_args = argparse.Namespace(
            start=args.start, end=args.end, interval=args.interval,
            articles_per_month=args.articles_per_month, no_memory=args.no_memory,
        )
        # Only create tasks for available ticker/dates
        run_id = f"replay_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        tasks = {}
        replay_dates = sorted(set(d for _, d in available))
        for ticker, date in available:
            for strategy in replay_strategies:
                key = f"{ticker}|{date}|{strategy}"
                tasks[key] = {"status": "pending"}

        checkpoint = {
            "run_id": run_id,
            "config": {
                "tickers": tickers,
                "start_date": args.start,
                "end_date": args.end,
                "interval": args.interval,
                "articles_per_month": args.articles_per_month,
                "strategies": replay_strategies,
                "memory_enabled": not args.no_memory,
                "model_tiers": model_tiers,
                "replay": True,
            },
            "run_config": _build_run_config(config),
            "analysis_dates": replay_dates,
            "tasks": tasks,
            "outcomes": [],
            "last_updated": datetime.now().isoformat(),
        }

        run_dir = Path(f"results/evaluations/backtest_{run_id}")
        cp_path = run_dir / "checkpoint.json"
        save_checkpoint(checkpoint, cp_path)

        run_backtest(checkpoint, cp_path, config)
        return

    # ── Report only mode ──
    if args.report:
        run_dir = Path(f"results/evaluations/backtest_{args.report}")
        cp_path = run_dir / "checkpoint.json"
        if not cp_path.exists():
            print(f"Checkpoint not found: {cp_path}")
            sys.exit(1)
        checkpoint = load_checkpoint(cp_path)
        generate_report(checkpoint, run_dir)
        return

    # ── Resume mode ──
    if args.resume:
        if args.resume == "latest":
            cp_path = find_latest_checkpoint()
            if not cp_path:
                print("No checkpoints found. Start a new backtest with --backtest")
                sys.exit(1)
        else:
            cp_path = Path(f"results/evaluations/backtest_{args.resume}/checkpoint.json")

        if not cp_path.exists():
            print(f"Checkpoint not found: {cp_path}")
            sys.exit(1)

        checkpoint = load_checkpoint(cp_path)
        print(f"Resuming run {checkpoint['run_id']}")

        # Restore model tiers from checkpoint if present
        saved_tiers = checkpoint.get("config", {}).get("model_tiers")
        if saved_tiers:
            config["_model_tiers"] = saved_tiers

        # Reset failed tasks if --retry-failed
        if args.retry_failed:
            reset_count = 0
            for key, task in checkpoint["tasks"].items():
                if task["status"] == "failed":
                    checkpoint["tasks"][key] = {"status": "pending"}
                    reset_count += 1
            if reset_count:
                print(f"Reset {reset_count} failed tasks to pending")

        run_backtest(checkpoint, cp_path, config)
        return

    # ── New backtest mode ──
    if not args.backtest:
        parser.print_help()
        print("\nUse --backtest to start a new backtest, or --resume to continue one.")
        sys.exit(1)

    tickers = [t.strip().upper() for t in args.tickers.split(",")]
    dates = get_monthly_dates(args.start, args.end)

    if not dates:
        print(f"No monthly dates between {args.start} and {args.end}")
        sys.exit(1)

    print(f"Tickers: {', '.join(tickers)}")
    print(f"Dates: {len(dates)} monthly snapshots ({dates[0]} to {dates[-1]})")
    print(f"Strategies: {', '.join(strategies)}")
    print(f"Total tasks: {len(tickers) * len(dates) * len(strategies)}")

    checkpoint = create_checkpoint(args, tickers, dates, strategies, config)

    # Store model tiers in checkpoint for resume support
    if config.get("_model_tiers"):
        checkpoint["config"]["model_tiers"] = config["_model_tiers"]

    run_dir = Path(f"results/evaluations/backtest_{checkpoint['run_id']}")
    cp_path = run_dir / "checkpoint.json"

    save_checkpoint(checkpoint, cp_path)
    print(f"Checkpoint created: {cp_path}")

    run_backtest(checkpoint, cp_path, config)


if __name__ == "__main__":
    main()

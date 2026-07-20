#!/usr/bin/env python3
"""
Trade Outcome Analysis Dashboard.

Analyzes trade outcomes logged by the OutcomeTracker to identify patterns
without automatic prompt injection (per FINSABER research recommendations).

Usage:
    python -m cli.analyze_outcomes [options]

    # Show summary statistics
    python -m cli.analyze_outcomes --summary

    # Analyze specific ticker
    python -m cli.analyze_outcomes --ticker NVDA

    # Filter by date range
    python -m cli.analyze_outcomes --start 2024-01-01 --end 2024-06-30

    # Export to CSV
    python -m cli.analyze_outcomes --export outcomes_analysis.csv

    # Process historical results from ./results/{date} directories
    python -m cli.analyze_outcomes --process-historical
"""

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import os

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingagents.backtest.outcome_tracker import (
    OutcomeTracker,
    TradeOutcome,
    OutcomeStats,
    validate_all_outcomes,
)


def load_outcomes_from_file(path: Path) -> List[TradeOutcome]:
    """Load outcomes from a JSON file."""
    with open(path) as f:
        data = json.load(f)
    return [TradeOutcome.from_dict(o) for o in data.get("outcomes", [])]


def load_all_outcomes(outcomes_dir: str = "./results/outcomes") -> List[TradeOutcome]:
    """Load all outcomes from the outcomes directory.

    Automatically validates any unvalidated outcomes against market prices.
    """
    from tradingagents.backtest.outcome_tracker import validate_outcome_against_market

    outcomes_path = Path(outcomes_dir)
    if not outcomes_path.exists():
        return []

    all_outcomes = []
    for file in outcomes_path.glob("outcomes_*.json"):
        try:
            outcomes = load_outcomes_from_file(file)
            all_outcomes.extend(outcomes)
        except Exception as e:
            print(f"Warning: Could not load {file}: {e}")

    # Validate any unvalidated outcomes
    newly_validated = 0
    for i, outcome in enumerate(all_outcomes):
        if not outcome.validated:
            all_outcomes[i] = validate_outcome_against_market(outcome)
            if all_outcomes[i].validated:
                newly_validated += 1

    if newly_validated > 0:
        print(f"Auto-validated {newly_validated} previously unvalidated outcomes")

    return all_outcomes


def process_historical_results(results_dir: str = "./results") -> List[TradeOutcome]:
    """
    Process historical results from ./results/{TICKER}/{DATE}/ directories.

    Scans for TradingAgents report files and extracts decision outcomes.
    Structure expected: ./results/{TICKER}/{DATE}/reports/
    """
    results_path = Path(results_dir)
    if not results_path.exists():
        print(f"Results directory not found: {results_dir}")
        return []

    outcomes = []
    processed_count = 0

    # Look for ticker directories
    for ticker_dir in sorted(results_path.iterdir()):
        if not ticker_dir.is_dir():
            continue

        # Skip non-ticker directories
        dir_name = ticker_dir.name
        if dir_name in ["outcomes", ".DS_Store"] or dir_name.startswith("."):
            continue

        ticker = dir_name

        # Look for date directories under ticker
        for date_dir in sorted(ticker_dir.iterdir()):
            if not date_dir.is_dir():
                continue

            date_name = date_dir.name
            # Skip if not a date-like name
            if not (len(date_name) >= 8 and "-" in date_name):
                continue

            # Try to read reports from this date directory
            reports_dir = date_dir / "reports"
            reports_summary = {}

            if reports_dir.exists():
                # Read individual report files
                for report_type in ["market", "sentiment", "news", "fundamentals"]:
                    report_file = reports_dir / f"{report_type}_report.md"
                    if report_file.exists():
                        try:
                            content = report_file.read_text()
                            reports_summary[report_type] = _truncate_report(content)
                        except Exception:
                            pass

            # Also check for JSON log files (eval_results format)
            log_files = list(date_dir.glob("*.json")) + list(date_dir.glob("**/full_states_log_*.json"))

            decision_found = False
            for log_file in log_files:
                try:
                    with open(log_file) as f:
                        data = json.load(f)

                    # Extract decision info from log
                    for date_key, state in data.items():
                        if not isinstance(state, dict):
                            continue

                        trade_date = state.get("trade_date", date_name)
                        decision = state.get("final_trade_decision", "")

                        # Update reports summary from JSON if not already loaded
                        if not reports_summary.get("market"):
                            reports_summary["market"] = _truncate_report(state.get("market_report", ""))
                        if not reports_summary.get("sentiment"):
                            reports_summary["sentiment"] = _truncate_report(state.get("sentiment_report", ""))
                        if not reports_summary.get("news"):
                            reports_summary["news"] = _truncate_report(state.get("news_report", ""))
                        if not reports_summary.get("fundamentals"):
                            reports_summary["fundamentals"] = _truncate_report(state.get("fundamentals_report", ""))

                        # Parse decision to get action
                        action = _parse_decision_action(decision)

                        # Create outcome record
                        outcome = TradeOutcome(
                            ticker=ticker,
                            trade_date=str(trade_date),
                            decision=action,
                            reports_summary=reports_summary,
                            entry_price=0.0,  # Unknown without backtest
                            exit_price=0.0,
                            pnl=0.0,
                            return_pct=0.0,
                            holding_period_days=0,
                            market_regime="unknown",
                            strategy_name="TradingAgents",
                        )
                        outcomes.append(outcome)
                        processed_count += 1
                        decision_found = True

                except Exception as e:
                    print(f"Warning: Could not process {log_file}: {e}")

            # If no JSON log found but reports exist, create outcome from reports
            if not decision_found and reports_summary:
                outcome = TradeOutcome(
                    ticker=ticker,
                    trade_date=date_name,
                    decision="UNKNOWN",  # No decision file found
                    reports_summary=reports_summary,
                    entry_price=0.0,
                    exit_price=0.0,
                    pnl=0.0,
                    return_pct=0.0,
                    holding_period_days=0,
                    market_regime="unknown",
                    strategy_name="TradingAgents",
                )
                outcomes.append(outcome)
                processed_count += 1

    print(f"Processed {processed_count} historical decisions from {results_dir}")
    return outcomes


def _truncate_report(report: str, max_length: int = 200) -> str:
    """Truncate a report to a reasonable summary length."""
    if not report:
        return ""
    if len(report) <= max_length:
        return report
    return report[:max_length] + "..."


def _parse_decision_action(decision: str) -> str:
    """Parse the final decision to extract the action (BUY/SELL/HOLD).

    Uses the canonical signal_processing extractor first, then falls back
    to keyword search.  Returns "UNKNOWN" instead of silently defaulting
    to HOLD when no decision can be determined.
    """
    # Try structured extraction first
    try:
        from tradingagents.graph.signal_processing import extract_decision_from_text
        return extract_decision_from_text(decision)
    except (ValueError, ImportError):
        pass

    # Keyword fallback
    decision_lower = decision.lower()
    if "buy" in decision_lower or "long" in decision_lower:
        return "BUY"
    elif "sell" in decision_lower or "short" in decision_lower:
        return "SELL"
    elif "hold" in decision_lower:
        return "HOLD"
    else:
        return "UNKNOWN"


def print_summary(outcomes: List[TradeOutcome]) -> None:
    """Print summary statistics."""
    if not outcomes:
        print("No outcomes to analyze.")
        return

    # Check validation status
    validated_count = sum(1 for o in outcomes if o.validated)
    unvalidated_count = len(outcomes) - validated_count

    print("\n" + "=" * 70)
    print("TRADE OUTCOME ANALYSIS SUMMARY")
    print("=" * 70)

    if unvalidated_count > 0:
        print(f"\n⚠️  {unvalidated_count} outcomes not validated against market prices.")
        print("   Run with --validate to fetch actual price data.")

    # Calculate stats based on validated outcomes for accuracy
    validated_outcomes = [o for o in outcomes if o.validated]

    if validated_outcomes:
        # Stats from validated data
        correct_decisions = sum(1 for o in validated_outcomes if o.decision_correct)
        total_validated = len(validated_outcomes)
        accuracy = (correct_decisions / total_validated * 100) if total_validated > 0 else 0

        total_pnl = sum(o.pnl for o in validated_outcomes)
        avg_return = sum(o.next_day_change_pct for o in validated_outcomes) / total_validated

        print(f"\n📊 Validated Statistics ({total_validated} trades):")
        print(f"   Decision Accuracy: {accuracy:.1f}% ({correct_decisions}/{total_validated} correct)")
        print(f"   Total P&L (hypothetical $10K/trade): ${total_pnl:,.2f}")
        print(f"   Average Next-Day Return: {avg_return:+.2f}%")

        # Wins/losses based on actual price movement
        wins = [o for o in validated_outcomes if o.decision_correct]
        losses = [o for o in validated_outcomes if not o.decision_correct and o.decision_correct is not None]
        print(f"   Winning Decisions: {len(wins)}")
        print(f"   Losing Decisions: {len(losses)}")

    print(f"\n📋 Decision Details:")
    print(f"   {'Ticker':<8} {'Date':<12} {'Decision':<6} {'Close':<10} {'Next Close':<12} {'Change':<10} {'Result'}")
    print(f"   {'-'*8} {'-'*12} {'-'*6} {'-'*10} {'-'*12} {'-'*10} {'-'*8}")

    for outcome in sorted(outcomes, key=lambda x: (x.ticker, x.trade_date)):
        if outcome.validated:
            status = "✅" if outcome.decision_correct else "❌"
            change_str = f"{outcome.next_day_change_pct:+.2f}%"
            close_str = f"${outcome.decision_date_close:.2f}"
            next_close_str = f"${outcome.next_day_close:.2f}"
        else:
            status = "❓"
            change_str = "N/A"
            close_str = "N/A"
            next_close_str = "N/A"

        print(f"   {outcome.ticker:<8} {outcome.trade_date:<12} {outcome.decision:<6} "
              f"{close_str:<10} {next_close_str:<12} {change_str:<10} {status}")

    # Summary by decision type
    print(f"\n🎯 By Decision Type:")
    for decision_type in ["BUY", "SELL", "HOLD"]:
        type_outcomes = [o for o in outcomes if o.decision == decision_type and o.validated]
        if type_outcomes:
            correct = sum(1 for o in type_outcomes if o.decision_correct)
            total = len(type_outcomes)
            avg_change = sum(o.next_day_change_pct for o in type_outcomes) / total
            print(f"   {decision_type}: {total} trades, {correct/total*100:.1f}% accuracy, "
                  f"avg next-day change: {avg_change:+.2f}%")

    print("\n" + "=" * 70)


def print_ticker_analysis(outcomes: List[TradeOutcome], ticker: str) -> None:
    """Print detailed analysis for a specific ticker."""
    ticker_outcomes = [o for o in outcomes if o.ticker.upper() == ticker.upper()]

    if not ticker_outcomes:
        print(f"No outcomes found for ticker: {ticker}")
        return

    print(f"\n{'=' * 60}")
    print(f"DETAILED ANALYSIS: {ticker.upper()}")
    print("=" * 60)

    wins = [o for o in ticker_outcomes if o.pnl > 0]
    losses = [o for o in ticker_outcomes if o.pnl <= 0]

    print(f"\n📊 Summary:")
    print(f"   Total Trades: {len(ticker_outcomes)}")
    print(f"   Wins: {len(wins)} | Losses: {len(losses)}")
    print(f"   Win Rate: {len(wins) / len(ticker_outcomes) * 100:.1f}%")
    print(f"   Total P&L: ${sum(o.pnl for o in ticker_outcomes):,.2f}")

    print(f"\n📈 Trade History:")
    for i, outcome in enumerate(sorted(ticker_outcomes, key=lambda x: x.trade_date), 1):
        status = "✅" if outcome.pnl > 0 else "❌" if outcome.pnl < 0 else "➖"
        print(f"   {i}. {outcome.trade_date} | {outcome.decision:4} | "
              f"${outcome.pnl:+,.2f} ({outcome.return_pct:+.2f}%) | "
              f"{outcome.market_regime} {status}")

    # Show report patterns for winning vs losing trades
    if wins and losses:
        print(f"\n🔍 Pattern Analysis:")
        print(f"   Average holding period (wins): {sum(o.holding_period_days for o in wins) / len(wins):.1f} days")
        print(f"   Average holding period (losses): {sum(o.holding_period_days for o in losses) / len(losses):.1f} days")

    print("\n" + "=" * 60)


def filter_by_date_range(
    outcomes: List[TradeOutcome],
    start_date: Optional[str],
    end_date: Optional[str],
) -> List[TradeOutcome]:
    """Filter outcomes by date range."""
    filtered = outcomes

    if start_date:
        filtered = [o for o in filtered if o.trade_date >= start_date]

    if end_date:
        filtered = [o for o in filtered if o.trade_date <= end_date]

    return filtered


def export_to_csv(outcomes: List[TradeOutcome], output_path: str) -> None:
    """Export outcomes to CSV."""
    tracker = OutcomeTracker(auto_save=False)
    tracker.outcomes = outcomes
    path = tracker.export_csv(output_path)
    print(f"Exported {len(outcomes)} outcomes to {path}")


def main():
    parser = argparse.ArgumentParser(
        description="Trade Outcome Analysis Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "--outcomes-dir",
        default="./results/outcomes",
        help="Directory containing outcome JSON files",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Show summary statistics",
    )
    parser.add_argument(
        "--ticker",
        type=str,
        help="Analyze specific ticker",
    )
    parser.add_argument(
        "--start",
        type=str,
        help="Start date filter (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--end",
        type=str,
        help="End date filter (YYYY-MM-DD)",
    )
    parser.add_argument(
        "--export",
        type=str,
        help="Export outcomes to CSV file",
    )
    parser.add_argument(
        "--process-historical",
        action="store_true",
        help="Process historical results from ./results/{date} directories",
    )
    parser.add_argument(
        "--results-dir",
        default="./results",
        help="Directory containing historical results (for --process-historical)",
    )
    parser.add_argument(
        "--save-historical",
        action="store_true",
        help="Save processed historical outcomes to outcomes directory",
    )
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Validate outcomes against actual market prices using yfinance",
    )

    args = parser.parse_args()

    # Load outcomes
    outcomes = []

    if args.process_historical:
        outcomes = process_historical_results(args.results_dir)
        if args.save_historical and outcomes:
            tracker = OutcomeTracker(output_dir=args.outcomes_dir)
            tracker.outcomes = outcomes
            path = tracker.save()
            print(f"Saved historical outcomes to {path}")
    else:
        outcomes = load_all_outcomes(args.outcomes_dir)

    if not outcomes:
        print("No outcomes found. Run backtests with outcome tracking enabled,")
        print("or use --process-historical to analyze existing results.")
        return

    # Apply date filters
    outcomes = filter_by_date_range(outcomes, args.start, args.end)

    if not outcomes:
        print("No outcomes match the specified filters.")
        return

    # Validate against market if requested
    if args.validate:
        print("Validating outcomes against market prices...")
        unvalidated = [o for o in outcomes if not o.validated]
        if unvalidated:
            def progress(current, total):
                print(f"  Validating {current}/{total}...", end="\r")
            outcomes = validate_all_outcomes(outcomes, progress_callback=progress)
            print(f"  Validated {len(unvalidated)} outcomes.              ")

            # Save validated outcomes
            tracker = OutcomeTracker(output_dir=args.outcomes_dir)
            tracker.outcomes = outcomes
            path = tracker.save()
            print(f"Saved validated outcomes to {path}")
        else:
            print("All outcomes already validated.")

    # Show analysis
    if args.ticker:
        print_ticker_analysis(outcomes, args.ticker)
    elif args.summary or not args.export:
        print_summary(outcomes)

    # Export if requested
    if args.export:
        export_to_csv(outcomes, args.export)


if __name__ == "__main__":
    main()

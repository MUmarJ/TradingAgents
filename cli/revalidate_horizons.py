"""Re-validate all outcomes with all horizons (including 8w, 13w).

Usage:
    python -m cli.revalidate_horizons <run_id>
    python -m cli.revalidate_horizons latest

This does NOT require new LLM calls — it only re-fetches yfinance data
and validates existing decisions against all horizon windows.
"""

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tradingagents.backtest.outcome_tracker import (
    TradeOutcome,
    validate_multi_horizon_outcome,
    HORIZONS,
)


def revalidate(run_id: str):
    eval_dir = Path("results/evaluations")

    if run_id == "latest":
        runs = sorted(eval_dir.glob("backtest_v2_*"), key=lambda p: p.name)
        if not runs:
            print("No V2 runs found.")
            sys.exit(1)
        run_dir = runs[-1]
        run_id = run_dir.name.replace("backtest_", "")
    else:
        run_dir = eval_dir / f"backtest_{run_id}"

    cp_path = run_dir / "checkpoint.json"
    if not cp_path.exists():
        print(f"Checkpoint not found: {cp_path}")
        sys.exit(1)

    with open(cp_path) as f:
        checkpoint = json.load(f)

    outcomes = checkpoint.get("outcomes", [])
    print(f"Run: {run_id}")
    print(f"Outcomes: {len(outcomes)}")
    print(f"Horizons: {', '.join(HORIZONS.keys())} ({len(HORIZONS)} total)")
    print()

    updated = 0
    for i, outcome_dict in enumerate(outcomes):
        outcome = TradeOutcome.from_dict(outcome_dict)

        old_horizons = set(outcome.horizon_outcomes.keys()) if outcome.horizon_outcomes else set()

        # Re-validate with ALL horizons (no filter)
        outcome = validate_multi_horizon_outcome(outcome, horizons=None)

        new_horizons = set(outcome.horizon_outcomes.keys()) if outcome.horizon_outcomes else set()
        added = new_horizons - old_horizons

        # Update checkpoint
        outcomes[i] = outcome.to_dict()

        if added:
            updated += 1
            h_correct = sum(1 for h in outcome.horizon_outcomes.values() if h.get("correct"))
            h_total = len(outcome.horizon_outcomes)
            print(f"[{i+1:>3}/{len(outcomes)}] {outcome.ticker:<6} {outcome.trade_date} "
                  f"| +{', '.join(sorted(added))} | H:{h_correct}/{h_total}")
        else:
            print(f"[{i+1:>3}/{len(outcomes)}] {outcome.ticker:<6} {outcome.trade_date} "
                  f"| no new horizons (already {len(new_horizons)})")

        # Also update task entry if it has horizon_outcomes
        task_key = f"{outcome.ticker}|{outcome.trade_date}|{outcome.strategy_name}"
        if task_key in checkpoint.get("tasks", {}):
            task = checkpoint["tasks"][task_key]
            if outcome.horizon_outcomes:
                task["horizon_outcomes"] = outcome.horizon_outcomes

    # Update config to reflect all horizons
    checkpoint["config"]["selected_horizons"] = None
    checkpoint["outcomes"] = outcomes

    # Save
    with open(cp_path, "w") as f:
        json.dump(checkpoint, f, indent=2)
    print(f"\nSaved {updated} updated outcomes to {cp_path}")
    print(f"Now run: python -m cli.evaluate_v2 --report {run_id}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m cli.revalidate_horizons <run_id|latest>")
        sys.exit(1)
    revalidate(sys.argv[1])

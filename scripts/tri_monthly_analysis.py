#!/usr/bin/env python3
"""Deep analysis of tri-monthly V5 benchmark results.

Reads outcomes.json and produces comprehensive analysis of whether
alpha is consistent across different entry dates (10th, 20th, EoM)
for each horizon.
"""
import json
import sys
from collections import defaultdict
from datetime import datetime

OUTCOMES_FILE = "results/evaluations/backtest_v2_20260214_193006/outcomes.json"
PREV_OUTCOMES_FILE = "results/evaluations/backtest_v2_20260214_132347/outcomes.json"
HORIZONS = ["1d", "3d", "1w", "2w", "4w", "8w", "13w"]

def classify_date_group(date_str: str) -> str:
    """Classify a date as '10th', '20th', or 'EoM'."""
    day = int(date_str.split("-")[2])
    if day == 10:
        return "10th"
    elif day == 20:
        return "20th"
    else:
        return "EoM"

def load_outcomes(path: str) -> list:
    with open(path) as f:
        data = json.load(f)
    return data["outcomes"]

def main():
    outcomes = load_outcomes(OUTCOMES_FILE)

    # Load previous EoM-only run for consistency check
    try:
        prev_outcomes = load_outcomes(PREV_OUTCOMES_FILE)
    except FileNotFoundError:
        prev_outcomes = []

    # Separate by model
    models = sorted(set(o["strategy_name"] for o in outcomes))

    print("=" * 80)
    print("TRI-MONTHLY DEEP ANALYSIS — AMBA, Mar-Dec 2025")
    print(f"Total outcomes: {len(outcomes)} ({len(outcomes)//len(models)} per model)")
    print(f"Models: {', '.join(models)}")
    print("=" * 80)

    # ═══════════════════════════════════════════════════════════════════
    # 1. DATE-GROUP ACCURACY BY HORIZON
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n### 1. Date-Group Accuracy by Horizon\n")

    for model in models:
        model_outcomes = [o for o in outcomes if o["strategy_name"] == model]
        short_name = model.replace("single_", "")

        print(f"\n**{short_name}:**\n")
        print(f"| Horizon | 10th (n=10) | 20th (n=10) | EoM (n=10) | All (n=30) | Spread |")
        print(f"|---------|:-----------:|:-----------:|:----------:|:----------:|:------:|")

        for h in HORIZONS:
            group_acc = {}
            for group_name in ["10th", "20th", "EoM"]:
                group_outcomes = [o for o in model_outcomes if classify_date_group(o["trade_date"]) == group_name]
                valid = [o for o in group_outcomes if h in o.get("horizon_outcomes", {})]
                correct = sum(1 for o in valid if o["horizon_outcomes"][h]["correct"])
                total = len(valid)
                group_acc[group_name] = (correct, total)

            all_valid = [o for o in model_outcomes if h in o.get("horizon_outcomes", {})]
            all_correct = sum(1 for o in all_valid if o["horizon_outcomes"][h]["correct"])
            all_total = len(all_valid)

            accs = []
            parts = []
            for g in ["10th", "20th", "EoM"]:
                c, t = group_acc[g]
                pct = (c/t*100) if t > 0 else 0
                accs.append(pct)
                parts.append(f"{c}/{t} ({pct:.0f}%)")

            all_pct = (all_correct/all_total*100) if all_total > 0 else 0
            spread = max(accs) - min(accs)

            print(f"| {h:<7} | {parts[0]:>11} | {parts[1]:>11} | {parts[2]:>10} | {all_correct}/{all_total} ({all_pct:.0f}%) | {spread:.0f}pp |")

    # ═══════════════════════════════════════════════════════════════════
    # 2. DECISION DISTRIBUTION BY DATE GROUP
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n### 2. Decision Distribution by Date Group\n")

    for model in models:
        model_outcomes = [o for o in outcomes if o["strategy_name"] == model]
        short_name = model.replace("single_", "")

        print(f"\n**{short_name}:**\n")
        print(f"| Date Group | BUY | SELL | HOLD | n |")
        print(f"|------------|:---:|:----:|:----:|:-:|")

        for group_name in ["10th", "20th", "EoM", "ALL"]:
            if group_name == "ALL":
                group = model_outcomes
            else:
                group = [o for o in model_outcomes if classify_date_group(o["trade_date"]) == group_name]

            buys = sum(1 for o in group if o["decision"] == "BUY")
            sells = sum(1 for o in group if o["decision"] == "SELL")
            holds = sum(1 for o in group if o["decision"] == "HOLD")
            n = len(group)

            print(f"| {group_name:<10} | {buys}/{n} ({buys/n*100:.0f}%) | {sells}/{n} ({sells/n*100:.0f}%) | {holds}/{n} ({holds/n*100:.0f}%) | {n} |")

    # ═══════════════════════════════════════════════════════════════════
    # 3. P&L BY DATE GROUP
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n### 3. P&L by Date Group\n")

    for model in models:
        model_outcomes = [o for o in outcomes if o["strategy_name"] == model]
        short_name = model.replace("single_", "")

        print(f"\n**{short_name}:**\n")
        print(f"| Date Group | P&L | Trades | Avg P&L/Trade | Win Rate (1d) |")
        print(f"|------------|:---:|:------:|:-------------:|:-------------:|")

        for group_name in ["10th", "20th", "EoM", "ALL"]:
            if group_name == "ALL":
                group = model_outcomes
            else:
                group = [o for o in model_outcomes if classify_date_group(o["trade_date"]) == group_name]

            total_pnl = sum(o["pnl"] for o in group)
            trades = sum(1 for o in group if o["decision"] != "HOLD")
            correct_1d = sum(1 for o in group if o.get("decision_correct", False))
            n = len(group)
            avg_pnl = total_pnl / n if n > 0 else 0

            print(f"| {group_name:<10} | ${total_pnl:>+,.0f} | {trades}/{n} | ${avg_pnl:>+,.0f} | {correct_1d}/{n} ({correct_1d/n*100:.0f}%) |")

    # ═══════════════════════════════════════════════════════════════════
    # 4. HOLDING POWER ANALYSIS
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n### 4. Holding Power Analysis\n")
    print("For each correct call at a given horizon, how often does the call remain correct at longer horizons?\n")

    for model in models:
        model_outcomes = [o for o in outcomes if o["strategy_name"] == model]
        short_name = model.replace("single_", "")

        print(f"\n**{short_name} — Holding Power Matrix:**\n")
        print(f"| If correct at → | Still correct at 3d | 1w | 2w | 4w | 8w | 13w |")
        print(f"|-----------------|:-------------------:|:--:|:--:|:--:|:--:|:---:|")

        for start_h in ["1d", "3d", "1w"]:
            # Find outcomes correct at start_h
            correct_at_start = [o for o in model_outcomes
                              if start_h in o.get("horizon_outcomes", {})
                              and o["horizon_outcomes"][start_h]["correct"]]

            if not correct_at_start:
                continue

            parts = []
            for target_h in ["3d", "1w", "2w", "4w", "8w", "13w"]:
                if HORIZONS.index(target_h) <= HORIZONS.index(start_h):
                    parts.append("—")
                    continue

                still_correct = sum(1 for o in correct_at_start
                                  if target_h in o.get("horizon_outcomes", {})
                                  and o["horizon_outcomes"][target_h]["correct"])
                total_valid = sum(1 for o in correct_at_start
                                if target_h in o.get("horizon_outcomes", {}))

                if total_valid > 0:
                    pct = still_correct / total_valid * 100
                    parts.append(f"{still_correct}/{total_valid} ({pct:.0f}%)")
                else:
                    parts.append("N/A")

            n = len(correct_at_start)
            print(f"| {start_h} (n={n}) | {' | '.join(parts)} |")

    # Reverse holding power: if wrong at 1d, how often correct at longer horizons?
    print("\n**Reverse: If WRONG at 1d, how often correct at longer horizons?**\n")

    for model in models:
        model_outcomes = [o for o in outcomes if o["strategy_name"] == model]
        short_name = model.replace("single_", "")

        wrong_1d = [o for o in model_outcomes
                   if "1d" in o.get("horizon_outcomes", {})
                   and not o["horizon_outcomes"]["1d"]["correct"]]

        if not wrong_1d:
            continue

        parts = []
        for target_h in ["3d", "1w", "2w", "4w", "8w", "13w"]:
            correct_later = sum(1 for o in wrong_1d
                              if target_h in o.get("horizon_outcomes", {})
                              and o["horizon_outcomes"][target_h]["correct"])
            total_valid = sum(1 for o in wrong_1d
                            if target_h in o.get("horizon_outcomes", {}))
            if total_valid > 0:
                pct = correct_later / total_valid * 100
                parts.append(f"{correct_later}/{total_valid} ({pct:.0f}%)")
            else:
                parts.append("N/A")

        print(f"**{short_name}** wrong at 1d (n={len(wrong_1d)}): " + " → ".join(f"{h}: {p}" for h, p in zip(["3d", "1w", "2w", "4w", "8w", "13w"], parts)))

    # ═══════════════════════════════════════════════════════════════════
    # 5. ALWAYS-BUY COMPARISON BY DATE GROUP
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n### 5. Always-BUY Baseline by Date Group\n")

    # For Always-BUY, we need to compute what BUY would have gotten on each date
    # We can derive this from horizon_outcomes: BUY is correct if change_pct > threshold
    print("| Date Group | Horizon | Always-BUY | Sonnet | GPT | Sonnet vs BUY | GPT vs BUY |")
    print("|------------|---------|:----------:|:------:|:---:|:-------------:|:----------:|")

    for group_name in ["10th", "20th", "EoM"]:
        for h in ["1d", "1w", "4w", "13w"]:  # Key horizons only
            # Always-BUY: correct if change_pct > hold_threshold
            # Use any model's outcomes since horizon data is the same
            any_model_outcomes = [o for o in outcomes
                                if o["strategy_name"] == models[0]
                                and classify_date_group(o["trade_date"]) == group_name
                                and h in o.get("horizon_outcomes", {})]

            buy_correct = sum(1 for o in any_model_outcomes
                            if o["horizon_outcomes"][h]["change_pct"] > o["horizon_outcomes"][h]["hold_threshold"])
            buy_total = len(any_model_outcomes)
            buy_pct = (buy_correct / buy_total * 100) if buy_total > 0 else 0

            model_accs = {}
            for model in models:
                m_outcomes = [o for o in outcomes
                            if o["strategy_name"] == model
                            and classify_date_group(o["trade_date"]) == group_name
                            and h in o.get("horizon_outcomes", {})]
                correct = sum(1 for o in m_outcomes if o["horizon_outcomes"][h]["correct"])
                total = len(m_outcomes)
                model_accs[model] = (correct / total * 100) if total > 0 else 0

            s_acc = model_accs.get("single_sonnet-4-5", 0)
            g_acc = model_accs.get("single_gpt-5.1-codex-mini", 0)

            s_delta = s_acc - buy_pct
            g_delta = g_acc - buy_pct

            print(f"| {group_name:<10} | {h:<7} | {buy_correct}/{buy_total} ({buy_pct:.0f}%) | {s_acc:.0f}% | {g_acc:.0f}% | {s_delta:+.0f}pp | {g_delta:+.0f}pp |")

    # ═══════════════════════════════════════════════════════════════════
    # 6. CONFIDENCE CALIBRATION (n=30)
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n### 6. Confidence Calibration (n=30)\n")

    for model in models:
        model_outcomes = [o for o in outcomes if o["strategy_name"] == model]
        short_name = model.replace("single_", "")

        # Bucket by confidence ranges
        buckets = [
            ("Low (< 0.4)", lambda c: c is not None and c < 0.4),
            ("Medium (0.4-0.6)", lambda c: c is not None and 0.4 <= c < 0.6),
            ("High (0.6-0.75)", lambda c: c is not None and 0.6 <= c < 0.75),
            ("Very High (≥ 0.75)", lambda c: c is not None and c >= 0.75),
        ]

        print(f"\n**{short_name}:**\n")
        print(f"| Confidence | n | 1d Acc | Avg P&L | Decisions |")
        print(f"|------------|:-:|:------:|:-------:|:---------:|")

        for label, fn in buckets:
            bucket = [o for o in model_outcomes if fn(o["confidence"])]
            if not bucket:
                print(f"| {label} | 0 | — | — | — |")
                continue

            correct_1d = sum(1 for o in bucket
                           if "1d" in o.get("horizon_outcomes", {})
                           and o["horizon_outcomes"]["1d"]["correct"])
            valid_1d = sum(1 for o in bucket if "1d" in o.get("horizon_outcomes", {}))
            acc = (correct_1d / valid_1d * 100) if valid_1d > 0 else 0
            avg_pnl = sum(o["pnl"] for o in bucket) / len(bucket)

            decisions = defaultdict(int)
            for o in bucket:
                decisions[o["decision"]] += 1
            dec_str = " ".join(f"{d[0]}:{decisions[d]}" for d in ["BUY", "SELL", "HOLD"] if decisions[d] > 0)

            print(f"| {label} | {len(bucket)} | {correct_1d}/{valid_1d} ({acc:.0f}%) | ${avg_pnl:+,.0f} | {dec_str} |")

    # ═══════════════════════════════════════════════════════════════════
    # 7. EOM CONSISTENCY CHECK
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n### 7. End-of-Month Consistency (This Run vs Previous Run)\n")

    if prev_outcomes:
        print("Do the same model on the same EoM dates produce the same decisions?\n")
        print(f"| Date | Model | Prev Decision | Prev Conf | This Decision | This Conf | Same? |")
        print(f"|------|-------|:-------------:|:---------:|:-------------:|:---------:|:-----:|")

        match_count = 0
        total_comparisons = 0

        for model in models:
            prev_model = [o for o in prev_outcomes if o["strategy_name"] == model]
            curr_eom = [o for o in outcomes
                       if o["strategy_name"] == model
                       and classify_date_group(o["trade_date"]) == "EoM"]

            for prev_o in prev_model:
                date = prev_o["trade_date"]
                curr_o = next((o for o in curr_eom if o["trade_date"] == date), None)
                if curr_o:
                    same = "Yes" if prev_o["decision"] == curr_o["decision"] else "**No**"
                    if prev_o["decision"] == curr_o["decision"]:
                        match_count += 1
                    total_comparisons += 1

                    short_model = model.replace("single_", "")
                    prev_conf = prev_o['confidence'] or 0
                    curr_conf = curr_o['confidence'] or 0
                    print(f"| {date} | {short_model} | {prev_o['decision']} | {prev_conf:.2f} | {curr_o['decision']} | {curr_conf:.2f} | {same} |")

        if total_comparisons > 0:
            print(f"\n**Consistency rate:** {match_count}/{total_comparisons} ({match_count/total_comparisons*100:.0f}%) same decisions")
    else:
        print("Previous run outcomes not available for comparison.")

    # ═══════════════════════════════════════════════════════════════════
    # 8. DETAILED DECISION-BY-DECISION TABLE
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n### 8. Full Decision-by-Decision Table (All 30 Dates)\n")

    # Get unique dates
    dates = sorted(set(o["trade_date"] for o in outcomes))

    print(f"| Date | Group | Sonnet Decision | Conf | 1d | P&L | GPT Decision | Conf | 1d | P&L | Price |")
    print(f"|------|:-----:|:---------------:|:----:|:--:|:---:|:------------:|:----:|:--:|:---:|:-----:|")

    for date in dates:
        group = classify_date_group(date)
        sonnet = next((o for o in outcomes if o["trade_date"] == date and o["strategy_name"] == "single_sonnet-4-5"), None)
        gpt = next((o for o in outcomes if o["trade_date"] == date and o["strategy_name"] == "single_gpt-5.1-codex-mini"), None)

        if sonnet:
            s_1d = "Y" if sonnet.get("horizon_outcomes", {}).get("1d", {}).get("correct", False) else "N"
            s_dec = sonnet["decision"]
            s_conf = sonnet["confidence"] or 0
            s_pnl = sonnet["pnl"] or 0
            price = sonnet["decision_date_close"] or 0
        else:
            s_dec = s_1d = "—"
            s_conf = s_pnl = price = 0

        if gpt:
            g_1d = "Y" if gpt.get("horizon_outcomes", {}).get("1d", {}).get("correct", False) else "N"
            g_dec = gpt["decision"]
            g_conf = gpt["confidence"] or 0
            g_pnl = gpt["pnl"] or 0
        else:
            g_dec = g_1d = "—"
            g_conf = g_pnl = 0

        print(f"| {date} | {group:>3} | {s_dec:>4} | {s_conf:.2f} | {s_1d} | ${s_pnl:>+7,.0f} | {g_dec:>4} | {g_conf:.2f} | {g_1d} | ${g_pnl:>+7,.0f} | ${price:.2f} |")

    # ═══════════════════════════════════════════════════════════════════
    # 9. HORIZON PERSISTENCE — "DECAY CURVES"
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n### 9. Accuracy Decay Across Horizons\n")
    print("How does accuracy change as the horizon extends?\n")

    for model in models:
        model_outcomes = [o for o in outcomes if o["strategy_name"] == model]
        short_name = model.replace("single_", "")

        directional = [o for o in model_outcomes if o["decision"] != "HOLD"]
        holds = [o for o in model_outcomes if o["decision"] == "HOLD"]

        print(f"\n**{short_name} — Directional trades only (n={len(directional)}):**\n")
        print(f"| Horizon | Correct | Total | Accuracy |")
        print(f"|---------|:-------:|:-----:|:--------:|")

        for h in HORIZONS:
            valid = [o for o in directional if h in o.get("horizon_outcomes", {})]
            correct = sum(1 for o in valid if o["horizon_outcomes"][h]["correct"])
            total = len(valid)
            acc = (correct / total * 100) if total > 0 else 0
            print(f"| {h:<7} | {correct:>7} | {total:>5} | {acc:>6.1f}% |")

        if holds:
            print(f"\n**{short_name} — HOLD trades (n={len(holds)}) — what would have been right?**\n")
            print(f"| Horizon | BUY would win | SELL would win | HOLD correct | HOLD wrong |")
            print(f"|---------|:-------------:|:--------------:|:------------:|:----------:|")

            for h in HORIZONS:
                valid = [o for o in holds if h in o.get("horizon_outcomes", {})]
                buy_wins = sum(1 for o in valid
                             if o["horizon_outcomes"][h]["change_pct"] > o["horizon_outcomes"][h]["hold_threshold"])
                sell_wins = sum(1 for o in valid
                              if o["horizon_outcomes"][h]["change_pct"] < -o["horizon_outcomes"][h]["hold_threshold"])
                hold_correct = sum(1 for o in valid if o["horizon_outcomes"][h]["correct"])
                hold_wrong = len(valid) - hold_correct

                total = len(valid)
                if total > 0:
                    print(f"| {h:<7} | {buy_wins}/{total} ({buy_wins/total*100:.0f}%) | {sell_wins}/{total} ({sell_wins/total*100:.0f}%) | {hold_correct}/{total} ({hold_correct/total*100:.0f}%) | {hold_wrong}/{total} ({hold_wrong/total*100:.0f}%) |")

    # ═══════════════════════════════════════════════════════════════════
    # 10. THE KEY QUESTION: IS ALPHA DATE-DEPENDENT?
    # ═══════════════════════════════════════════════════════════════════
    print("\n\n### 10. Summary: Is Alpha Date-Dependent?\n")

    for model in models:
        model_outcomes = [o for o in outcomes if o["strategy_name"] == model]
        short_name = model.replace("single_", "")

        # Compute 1d accuracy per date group
        group_accs = {}
        for group_name in ["10th", "20th", "EoM"]:
            group = [o for o in model_outcomes if classify_date_group(o["trade_date"]) == group_name]
            valid = [o for o in group if "1d" in o.get("horizon_outcomes", {})]
            correct = sum(1 for o in valid if o["horizon_outcomes"]["1d"]["correct"])
            group_accs[group_name] = correct / len(valid) * 100 if valid else 0

        spread = max(group_accs.values()) - min(group_accs.values())
        all_valid = [o for o in model_outcomes if "1d" in o.get("horizon_outcomes", {})]
        all_correct = sum(1 for o in all_valid if o["horizon_outcomes"]["1d"]["correct"])
        overall = all_correct / len(all_valid) * 100 if all_valid else 0

        # Always-BUY for comparison
        any_outcomes = [o for o in outcomes if o["strategy_name"] == models[0]]
        buy_correct = sum(1 for o in any_outcomes
                        if "1d" in o.get("horizon_outcomes", {})
                        and o["horizon_outcomes"]["1d"]["change_pct"] > o["horizon_outcomes"]["1d"]["hold_threshold"])
        buy_total = sum(1 for o in any_outcomes if "1d" in o.get("horizon_outcomes", {}))
        buy_pct = (buy_correct / buy_total * 100) if buy_total > 0 else 0

        print(f"**{short_name}:**")
        print(f"  Overall 1d accuracy: {overall:.1f}% (n=30)")
        print(f"  10th: {group_accs['10th']:.0f}% | 20th: {group_accs['20th']:.0f}% | EoM: {group_accs['EoM']:.0f}%")
        print(f"  Spread: {spread:.0f}pp")
        print(f"  vs Always-BUY ({buy_pct:.0f}%): {overall - buy_pct:+.1f}pp")
        print()

    print("\n### VERDICT\n")

    # Compute key numbers for verdict
    sonnet_outcomes = [o for o in outcomes if o["strategy_name"] == "single_sonnet-4-5"]
    gpt_outcomes = [o for o in outcomes if o["strategy_name"] == "single_gpt-5.1-codex-mini"]

    # Sonnet EoM accuracy in THIS run
    sonnet_eom = [o for o in sonnet_outcomes if classify_date_group(o["trade_date"]) == "EoM"]
    sonnet_eom_1d = sum(1 for o in sonnet_eom
                       if "1d" in o.get("horizon_outcomes", {})
                       and o["horizon_outcomes"]["1d"]["correct"])
    sonnet_eom_total = sum(1 for o in sonnet_eom if "1d" in o.get("horizon_outcomes", {}))

    sonnet_mid = [o for o in sonnet_outcomes if classify_date_group(o["trade_date"]) != "EoM"]
    sonnet_mid_1d = sum(1 for o in sonnet_mid
                       if "1d" in o.get("horizon_outcomes", {})
                       and o["horizon_outcomes"]["1d"]["correct"])
    sonnet_mid_total = sum(1 for o in sonnet_mid if "1d" in o.get("horizon_outcomes", {}))

    print(f"Sonnet EoM in this run: {sonnet_eom_1d}/{sonnet_eom_total} ({sonnet_eom_1d/sonnet_eom_total*100:.0f}%)")
    print(f"Sonnet mid-month (10th+20th): {sonnet_mid_1d}/{sonnet_mid_total} ({sonnet_mid_1d/sonnet_mid_total*100:.0f}%)")
    print(f"Sonnet EoM in previous run: 6/10 (60%)")
    print()

    # Check if EoM decisions even match
    if prev_outcomes:
        sonnet_prev = [o for o in prev_outcomes if o["strategy_name"] == "single_sonnet-4-5"]
        matches = 0
        for prev_o in sonnet_prev:
            curr_o = next((o for o in sonnet_eom if o["trade_date"] == prev_o["trade_date"]), None)
            if curr_o and curr_o["decision"] == prev_o["decision"]:
                matches += 1
        print(f"Sonnet EoM decision consistency: {matches}/{len(sonnet_prev)} same decisions across runs")


if __name__ == "__main__":
    main()

# Test V2.1: Multi-Horizon Benchmark Plan

## Look-Ahead Bias Verification (Code-Verified)

| Component | Status | Evidence |
|-----------|--------|----------|
| **News Cutoff** | ✅ FIXED | `polygon_news.py:82` - `published_utc_lte=end_date + "T14:30:00Z"` (9:30 AM ET) |
| **Quote Data** | ✅ FIXED | `core_stock_tools.py:63-64` - `hist[hist.index.date <= curr_dt.date()]` filters future data |
| **Single-Agent Prompt** | ✅ FIXED | `single_agent.py:47-50` - "Only consider information that would have been available BEFORE 9:30 AM ET on {date}" |
| **BUY Threshold** | ✅ FIXED | `outcome_tracker.py:533` - `> TRANSACTION_COST_PCT` (0.15%) |
| **SELL Threshold** | ✅ FIXED | `outcome_tracker.py:536` - `< -TRANSACTION_COST_PCT` (-0.15%) |
| **HOLD Threshold** | ✅ FIXED | `outcome_tracker.py:539` - `< 0.5%` (tightened from 1%) |

**All 5 critical look-ahead bias fixes are in place.**

---

## Objective

Run comprehensive benchmark comparing **Sonnet 4.5** vs **claude-opus-4-6** single-agent on AMBA with:
- 3 analysis dates per month (10th, 20th, end-of-month)
- 5 projection horizons per decision (1w, 2w, 4w, 8w, 13w)
- Date range: March 1, 2025 to February 7, 2026

---

## Test Configuration

| Parameter | Value |
|-----------|-------|
| **Ticker** | AMBA |
| **Models** | claude-sonnet-4-5-20250929, claude-opus-4-6-20250501 |
| **Architecture** | Single-agent only |
| **Analysis Dates** | 33 (10th, 20th, end-of-month × 11 months) |
| **Horizons** | 1w (5 trading days), 2w (10), 4w (20), 8w (40), 13w (65) |
| **LLM Calls** | 66 total (33 per model) |
| **Validation Outcomes** | 330 (66 × 5 horizons) |
| **Estimated Cost** | ~$18 (33 × $0.10 Sonnet + 33 × $0.45 Opus) |

---

## Multi-Horizon Validation Logic

### How It Works

Each LLM call produces ONE decision (BUY/SELL/HOLD). That single decision is then validated against 5 different time horizons using historical market data:

```
Decision Date: 2025-03-10
Decision: SELL (confidence 0.75)

Validation:
├── 1 week (5 trading days):   Close on ~2025-03-17 vs 2025-03-10
├── 2 weeks (10 trading days): Close on ~2025-03-24 vs 2025-03-10
├── 4 weeks (20 trading days): Close on ~2025-04-07 vs 2025-03-10
├── 8 weeks (40 trading days): Close on ~2025-05-05 vs 2025-03-10
└── 13 weeks (65 trading days): Close on ~2025-06-09 vs 2025-03-10
```

### Correctness Rules

| Decision | Correctness Condition |
|----------|----------------------|
| **BUY** | Price increased > 0.15% (covers transaction costs) |
| **SELL** | Price decreased > 0.15% |
| **HOLD** | Price change within threshold (scales with horizon) |

**HOLD Thresholds by Horizon:**

| Horizon | Trading Days | HOLD Threshold | Rationale |
|---------|-------------|----------------|-----------|
| 1 week  | 5           | ±0.5%          | Short-term noise |
| 2 weeks | 10          | ±0.8%          | Moderate noise |
| 4 weeks | 20          | ±1.2%          | Monthly volatility |
| 8 weeks | 40          | ±1.8%          | Quarterly movement |
| 13 weeks| 65          | ±2.5%          | Significant drift acceptable |

---

## Metrics Structure

### Per-Outcome Record

```json
{
  "ticker": "AMBA",
  "trade_date": "2025-03-10",
  "model": "claude-opus-4-6",
  "decision": "SELL",
  "confidence": 0.75,
  "decision_close": 52.34,

  "horizon_outcomes": {
    "1w": {
      "target_date": "2025-03-17",
      "target_close": 50.12,
      "change_pct": -4.24,
      "correct": true
    },
    "2w": {
      "target_date": "2025-03-24",
      "target_close": 48.90,
      "change_pct": -6.57,
      "correct": true
    },
    "4w": {
      "target_date": "2025-04-07",
      "target_close": 53.10,
      "change_pct": +1.45,
      "correct": false
    },
    "8w": {
      "target_date": "2025-05-05",
      "target_close": 49.50,
      "change_pct": -5.43,
      "correct": true
    },
    "13w": {
      "target_date": "2025-06-09",
      "target_close": 47.20,
      "change_pct": -9.82,
      "correct": true
    }
  }
}
```

### Separate Accuracy Metrics (Per Horizon)

Each horizon is evaluated independently:

```markdown
## Sonnet 4.5 - Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return When Correct | Avg Loss When Wrong |
|---------|---------|-------|----------|------------------------|---------------------|
| 1 week  | 18      | 33    | 54.5%    | +3.2%                  | -2.1%               |
| 2 weeks | 17      | 33    | 51.5%    | +5.1%                  | -3.4%               |
| 4 weeks | 15      | 33    | 45.5%    | +8.2%                  | -5.7%               |
| 8 weeks | 16      | 33    | 48.5%    | +12.3%                 | -8.9%               |
| 13 weeks| 14      | 33    | 42.4%    | +18.5%                 | -11.2%              |
```

### Aggregated Metrics

**1. Cross-Horizon Consistency:**
How often is a decision correct across ALL horizons?

```markdown
## Consistency Score (All 5 Horizons Agree)

| Model | All Correct | All Wrong | Mixed | Consistency Rate |
|-------|-------------|-----------|-------|------------------|
| Sonnet 4.5 | 8/33 | 5/33 | 20/33 | 39.4% |
| Opus 4.6 | 10/33 | 3/33 | 20/33 | 39.4% |
```

**2. Short vs Long Horizon Performance:**

```markdown
## Short-Term vs Long-Term Accuracy

| Model | Short (1w+2w avg) | Long (8w+13w avg) | Delta |
|-------|-------------------|-------------------|-------|
| Sonnet 4.5 | 53.0% | 45.5% | -7.5% |
| Opus 4.6 | 48.5% | 51.5% | +3.0% |
```

**3. Decision-Type by Horizon:**

```markdown
## BUY Decision Accuracy by Horizon

| Horizon | Sonnet 4.5 | Opus 4.6 |
|---------|------------|----------|
| 1 week  | 60.0%      | 55.0%    |
| 2 weeks | 55.0%      | 52.0%    |
| 4 weeks | 45.0%      | 50.0%    |
| 8 weeks | 40.0%      | 55.0%    |
| 13 weeks| 35.0%      | 58.0%    |
```

**4. Overall Aggregated Accuracy:**

```markdown
## Overall Metrics (Aggregated)

| Model | Total Outcomes | Total Correct | Overall Accuracy |
|-------|----------------|---------------|------------------|
| Sonnet 4.5 | 165 | 80 | 48.5% |
| Opus 4.6 | 165 | 82 | 49.7% |
```

---

## Analysis Dates (33 Total)

```
March 2025:    10, 20, 31
April 2025:    10, 20, 30
May 2025:      10, 20, 31
June 2025:     10, 20, 30
July 2025:     10, 20, 31
August 2025:   10, 20, 31
September 2025: 10, 20, 30
October 2025:  10, 20, 31
November 2025: 10, 20, 30
December 2025: 10, 20, 31
January 2026:  10, 20, 31

Total: 33 dates
```

Note: February 2026 excluded (end date is Feb 7, before any tri-monthly date)

---

## Implementation Changes

### Files to Modify

| File | Changes |
|------|---------|
| [cli/evaluate_v2.py](cli/evaluate_v2.py) | Add `get_tri_monthly_dates()`, `--date-mode`, `--multi-horizon` args, multi-model support |
| [tradingagents/backtest/outcome_tracker.py](tradingagents/backtest/outcome_tracker.py) | Add `horizon_outcomes` field, extend data fetch to 130 days, add `validate_multi_horizon_outcome()` |

### 1. outcome_tracker.py Changes

**Extend TradeOutcome dataclass:**
```python
@dataclass
class TradeOutcome:
    # ... existing fields ...
    horizon_outcomes: Optional[Dict[str, Dict[str, Any]]] = None
```

**Extend data fetch window:**
```python
# Line ~483, change from:
end_date = decision_date + timedelta(days=10)
# To:
end_date = decision_date + timedelta(days=130)  # Cover 13 weeks + buffer
```

**Add multi-horizon validation function:**
```python
HORIZONS = {
    "1w": 5,    # 5 trading days
    "2w": 10,
    "4w": 20,
    "8w": 40,
    "13w": 65,
}

HOLD_THRESHOLDS = {
    "1w": 0.5,
    "2w": 0.8,
    "4w": 1.2,
    "8w": 1.8,
    "13w": 2.5,
}

def validate_multi_horizon_outcome(outcome: TradeOutcome) -> TradeOutcome:
    """Validate outcome against all projection horizons."""
    # ... implementation ...
```

### 2. evaluate_v2.py Changes

**Add tri-monthly date generation:**
```python
def get_tri_monthly_dates(start: str, end: str) -> List[str]:
    """Generate 10th, 20th, and end-of-month dates."""
    # ... implementation ...
```

**Add CLI arguments:**
```python
parser.add_argument("--date-mode", choices=["monthly", "tri-monthly"], default="monthly")
parser.add_argument("--multi-horizon", action="store_true")
```

**Add multi-horizon report generation:**
```python
def _build_horizon_accuracy_table(outcomes, model) -> str:
    """Build per-horizon accuracy table for a model."""

def _build_horizon_comparison_table(outcomes) -> str:
    """Build cross-model comparison by horizon."""

def _build_consistency_table(outcomes) -> str:
    """Build cross-horizon consistency analysis."""
```

---

## Report Format

### Expected Output Structure

```markdown
# Multi-Horizon Benchmark Report: AMBA

**Run ID:** v2_20260209_...
**Date:** 2026-02-09
**Models:** claude-sonnet-4-5-20250929, claude-opus-4-6
**Period:** 2025-03-01 to 2026-02-07
**Dates:** 33 tri-monthly (10th, 20th, end-of-month)
**Horizons:** 1w, 2w, 4w, 8w, 13w

---

## Executive Summary

| Model | 1w Acc | 2w Acc | 4w Acc | 8w Acc | 13w Acc | Overall |
|-------|--------|--------|--------|--------|---------|---------|
| Sonnet 4.5 | XX% | XX% | XX% | XX% | XX% | XX% |
| Opus 4.6 | XX% | XX% | XX% | XX% | XX% | XX% |

---

## Sonnet 4.5 Detailed Results

### Per-Horizon Accuracy
[Table]

### Decision Distribution
BUY: XX% | SELL: XX% | HOLD: XX%

### By Decision Type
[Table showing BUY/SELL/HOLD accuracy at each horizon]

---

## Opus 4.6 Detailed Results

### Per-Horizon Accuracy
[Table]

### Decision Distribution
BUY: XX% | SELL: XX% | HOLD: XX%

### By Decision Type
[Table showing BUY/SELL/HOLD accuracy at each horizon]

---

## Cross-Model Comparison

### Horizon-by-Horizon
[Which model wins at each horizon]

### Consistency Analysis
[How often each model is right across all horizons]

### Short vs Long Term
[Performance delta between 1w/2w vs 8w/13w]

---

## Monthly Breakdown

| Month | Sonnet (5 horizons) | Opus (5 horizons) |
|-------|---------------------|-------------------|
| 2025-03 | X/15 | X/15 |
| ... | ... | ... |

---

## Key Findings

1. [Which model is better for short-term?]
2. [Which model is better for long-term?]
3. [Are decisions consistent across horizons?]
4. [How does confidence correlate with accuracy?]

---

## Raw Data

[Link to outcomes.json]
```

---

## Execution Commands

```bash
# Dry run (cost estimate)
python -m cli.evaluate_v2 \
    --tickers AMBA \
    --start 2025-03-01 --end 2026-02-07 \
    --date-mode tri-monthly --multi-horizon \
    --provider anthropic \
    --strategies single_sonnet-4-5,single_opus-4-6 \
    --dry-run

# Full run
python -m cli.evaluate_v2 \
    --tickers AMBA \
    --start 2025-03-01 --end 2026-02-07 \
    --date-mode tri-monthly --multi-horizon \
    --provider anthropic \
    --strategies single_sonnet-4-5,single_opus-4-6 \
    --wait-on-rate-limit

# Resume if interrupted
python -m cli.evaluate_v2 --resume --wait-on-rate-limit

# Generate report
python -m cli.evaluate_v2 --report <run_id>
```

---

## Note on Multi-Horizon Data Window

**Current Issue:** `outcome_tracker.py:483` only fetches 10 days forward:
```python
end_date = decision_date + timedelta(days=10)
```

**Required Change:** Must extend to 130 days to cover 13-week (65 trading days) horizon:
```python
end_date = decision_date + timedelta(days=130)
```

This is a required implementation change before running the benchmark.

---

## Verification Steps

1. **Pre-Implementation:**
   - Verify both model IDs work with Anthropic API
   - Verify yfinance has AMBA data through June 2026 (for 13w horizon from Jan 2026)

2. **Post-Implementation:**
   - Run single date to verify horizon validation
   - Check checkpoint structure has `horizon_outcomes`
   - Verify report renders all tables correctly

3. **Data Validation:**
   - Cross-check a few horizon calculations manually
   - Ensure trading days (not calendar days) are used

---

## Implementation Checklist

### Phase 1: outcome_tracker.py
- [ ] Add `horizon_outcomes: Optional[Dict[str, Dict[str, Any]]] = None` to TradeOutcome dataclass (line ~85)
- [ ] Change line 483 from `timedelta(days=10)` to `timedelta(days=130)`
- [ ] Add `HORIZONS` and `HOLD_THRESHOLDS` constants
- [ ] Add `validate_multi_horizon_outcome()` function

### Phase 2: evaluate_v2.py
- [ ] Add `get_tri_monthly_dates(start, end)` function
- [ ] Add `--date-mode` CLI argument (choices: monthly, tri-monthly)
- [ ] Add `--multi-horizon` CLI flag
- [ ] Update date generation logic to use tri-monthly when specified
- [ ] Call `validate_multi_horizon_outcome()` when `--multi-horizon` is set
- [ ] Update checkpoint to store `horizon_outcomes`
- [ ] Add `_build_horizon_accuracy_table()` report function
- [ ] Add `_build_horizon_comparison_table()` report function
- [ ] Add `_build_consistency_table()` report function

### Phase 3: Testing
- [ ] Verify claude-opus-4-6 model ID works
- [ ] Dry run with cost estimate
- [ ] Single date test to verify horizon validation
- [ ] Full benchmark run
- [ ] Verify report output

---

*Plan compiled: 2026-02-09*

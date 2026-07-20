# TradingAgents V2 Benchmark Report
**Run ID:** v2_20260218_192919
**Date:** 2026-02-18
**Period:** 2025-03-01 to 2025-12-31
**Tickers:** AMBA (1 tickers)
**Dates:** 30 tri-monthly snapshots
**Version:** 2 (look-ahead free, no HOLD fallback)
**Date Mode:** tri-monthly (10th, 20th, end-of-month)
**Horizons:** 1d, 3d, 1w, 2w, 4w, 8w, 13w (7 projection horizons)
**Total tasks:** 30
**Completed:** 30
**Failed:** 0
**Failure rate:** 0.0%

## Configuration

| Setting | Value |
|---------|-------|
| LLM Provider | openai |
| Deep Think LLM | gpt-5.1-codex-mini |
| Quick Think LLM | gpt-5.2-2025-12-11 |
| Memory Enabled | False |
| ACE Enabled | False |
| Model Tiers | 1 configurations |
| &nbsp;&nbsp;ensemble_weighted_vote+kronos_mini+xgboost | model=weighted_vote |

## Executive Summary (Next-Day Accuracy)

| Metric | ensemble_weighted_vote+kronos_mini+xgboost |
|--------|--------|
| Next-day accuracy | **63.3%** |
| Total P&L (post-cost) | **$482.16** |
| Max drawdown | **$1,368.61** |
| Avg confidence | 0.83 |
| BUY % | 47% |
| SELL % | 43% |
| HOLD % | 10% |
| Analyses | 30 |

## 5-Day Forward Accuracy

| Metric | ensemble_weighted_vote+kronos_mini+xgboost |
|--------|--------|
| 5-day accuracy | 11/30 (36.7%) |
| 5-day P&L | $298.90 |

---

## Multi-Horizon Analysis

### Horizon Comparison (All Models)

| Horizon | ensemble_weighted_vote+kronos_mini+xgboost | Winner |
|---------|---------|--------|
| 1d      |    63.3% | ensemble_weighted_vote+kronos_mini+xgboost |
| 3d      |    53.3% | ensemble_weighted_vote+kronos_mini+xgboost |
| 1w      |    36.7% | ensemble_weighted_vote+kronos_mini+xgboost |
| 2w      |    40.0% | ensemble_weighted_vote+kronos_mini+xgboost |
| 4w      |    36.7% | ensemble_weighted_vote+kronos_mini+xgboost |
| 8w      |    35.7% | ensemble_weighted_vote+kronos_mini+xgboost |
| 13w     |    52.0% | ensemble_weighted_vote+kronos_mini+xgboost |
| **Overall** |    45.3% | ensemble_weighted_vote+kronos_mini+xgboost |

### ensemble_weighted_vote+kronos_mini+xgboost — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1d      | 19      | 30    |  63.3% |               +0.63% |            +0.78% |
| 3d      | 16      | 30    |  53.3% |               +4.02% |            -0.06% |
| 1w      | 11      | 30    |  36.7% |               +5.44% |            -0.87% |
| 2w      | 12      | 30    |  40.0% |               +7.97% |            +0.82% |
| 4w      | 11      | 30    |  36.7% |              +14.07% |            -1.29% |
| 8w      | 10      | 28    |  35.7% |              +18.22% |            +6.53% |
| 13w     | 13      | 25    |  52.0% |              +20.23% |           +14.71% |

## Cross-Horizon Consistency

### Cross-Horizon Consistency

| Metric | ensemble_weighted_vote+kronos_mini+xgboost |
|--------|---------|
| All horizons correct | 1/30 (3%) |
| All horizons wrong | 4/30 (13%) |
| Mixed results | 25/30 (83%) |

### Short-Term vs Long-Term Accuracy

| Model | Short (1d+3d avg) | Long (8w+13w avg) | Delta |
|-------|-------------------|-------------------|-------|
| ensemble_weighted_vote+kronos_mini+xgboost | 58.3% | 43.4% | -14.9% |

### BUY Decision Accuracy by Horizon

| Horizon | ensemble_weighted_vote+kronos_mini+xgboost |
|---------|---------|
| 1d      |  71.4% |
| 3d      |  64.3% |
| 1w      |  42.9% |
| 2w      |  57.1% |
| 4w      |  42.9% |
| 8w      |  75.0% |
| 13w     |  88.9% |

### SELL Decision Accuracy by Horizon

| Horizon | ensemble_weighted_vote+kronos_mini+xgboost |
|---------|---------|
| 1d      |  61.5% |
| 3d      |  53.8% |
| 1w      |  38.5% |
| 2w      |  30.8% |
| 4w      |  38.5% |
| 8w      |   7.7% |
| 13w     |  38.5% |

---


## Conclusion

- **Most accurate strategy:** ensemble_weighted_vote+kronos_mini+xgboost (63.3%)
- **Highest P&L strategy:** ensemble_weighted_vote+kronos_mini+xgboost ($482.16)

## Results by Month

| Month | ensemble_weighted_vote+kronos_mini+xgboost |
|-------|--------|
| 2025-03 | 2/3 (67%) |
| 2025-03 | 2/3 (67%) |
| 2025-03 | 2/3 (67%) |
| 2025-04 | 2/3 (67%) |
| 2025-04 | 2/3 (67%) |
| 2025-04 | 2/3 (67%) |
| 2025-05 | 2/3 (67%) |
| 2025-05 | 2/3 (67%) |
| 2025-05 | 2/3 (67%) |
| 2025-06 | 1/3 (33%) |
| 2025-06 | 1/3 (33%) |
| 2025-06 | 1/3 (33%) |
| 2025-07 | 2/3 (67%) |
| 2025-07 | 2/3 (67%) |
| 2025-07 | 2/3 (67%) |
| 2025-08 | 2/3 (67%) |
| 2025-08 | 2/3 (67%) |
| 2025-08 | 2/3 (67%) |
| 2025-09 | 1/3 (33%) |
| 2025-09 | 1/3 (33%) |
| 2025-09 | 1/3 (33%) |
| 2025-10 | 3/3 (100%) |
| 2025-10 | 3/3 (100%) |
| 2025-10 | 3/3 (100%) |
| 2025-11 | 1/3 (33%) |
| 2025-11 | 1/3 (33%) |
| 2025-11 | 1/3 (33%) |
| 2025-12 | 3/3 (100%) |
| 2025-12 | 3/3 (100%) |
| 2025-12 | 3/3 (100%) |

## Results by Ticker

| Ticker | ensemble_weighted_vote+kronos_mini+xgboost Acc | ensemble_weighted_vote+kronos_mini+xgboost P&L |
|--------|--------|---------|
| AMBA | 63% | $482 |

## Decision Distribution

**ensemble_weighted_vote+kronos_mini+xgboost:** BUY 47% | SELL 43% | HOLD 10% (n=30)


## Free Baselines Comparison

| Strategy | 1d | 3d | 1w | 2w | 4w | 8w | 13w |
|----------|------|------|------|------|------|------|------|
| **ensemble_weighted_vote+kronos_mini+xgboost** | 63.3% | 53.3% | 36.7% | 40.0% | 36.7% | 35.7% | 52.0% |
| Always-BUY | 50.0% | 53.3% | 50.0% | 63.3% | 50.0% | 78.6% | 68.0% |
| Always-SELL | 46.7% | 46.7% | 43.3% | 36.7% | 50.0% | 21.4% | 32.0% |
| Momentum-5d | 36.7% | 43.3% | 46.7% | 53.3% | 53.3% | 60.7% | 48.0% |
| Random (expected) | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% |


## Walk-Forward Validation

**Split date:** 2025-09-01 (Period 1: before, Period 2: after)

| Strategy | Period 1 (in-sample) | Period 2 (out-of-sample) | Delta |
|----------|---------------------|-------------------------|-------|
| ensemble_weighted_vote+kronos_mini+xgboost | 11/18 (61.1%) | 8/12 (66.7%) | +5.6% |

### Walk-Forward by Horizon

| Strategy | Horizon | P1 Acc | P2 Acc | Delta |
|----------|---------|--------|--------|-------|
| ensemble_weighted_vote+kronos_mini+xgboost | 1d | 61.1% | 66.7% | +5.6% |
| ensemble_weighted_vote+kronos_mini+xgboost | 3d | 61.1% | 41.7% | -19.4% |
| ensemble_weighted_vote+kronos_mini+xgboost | 1w | 44.4% | 25.0% | -19.4% |
| ensemble_weighted_vote+kronos_mini+xgboost | 2w | 44.4% | 33.3% | -11.1% |
| ensemble_weighted_vote+kronos_mini+xgboost | 4w | 44.4% | 25.0% | -19.4% |
| ensemble_weighted_vote+kronos_mini+xgboost | 8w | 44.4% | 20.0% | -24.4% |
| ensemble_weighted_vote+kronos_mini+xgboost | 13w | 50.0% | 57.1% | +7.1% |


## Statistical Significance

### Binomial Test vs Always-BUY Baseline

| Strategy | Horizon | Model Acc | Baseline Acc | p-value | Significant? |
|----------|---------|-----------|-------------|---------|-------------|
| ensemble_weighted_vote+kronos_mini+xgboost | 1d | 63.3% | 50.0% | 0.2005 | No |
| ensemble_weighted_vote+kronos_mini+xgboost | 3d | 53.3% | 53.3% | 1.0000 | No |
| ensemble_weighted_vote+kronos_mini+xgboost | 1w | 36.7% | 50.0% | 0.2005 | No |
| ensemble_weighted_vote+kronos_mini+xgboost | 2w | 40.0% | 63.3% | 0.0124 | Yes |
| ensemble_weighted_vote+kronos_mini+xgboost | 4w | 36.7% | 50.0% | 0.2005 | No |
| ensemble_weighted_vote+kronos_mini+xgboost | 8w | 35.7% | 78.6% | 0.0000 | Yes |
| ensemble_weighted_vote+kronos_mini+xgboost | 13w | 52.0% | 68.0% | 0.0905 | No |

### Bootstrap 95% CI (Next-Day Accuracy)

| Strategy | Accuracy | 95% CI | n |
|----------|----------|--------|---|
| ensemble_weighted_vote+kronos_mini+xgboost | 63.3% | [46.7%, 80.0%] | 30 |


---


## Confidence Analysis

**ensemble_weighted_vote+kronos_mini+xgboost:** Avg confidence: 0.83 | High-confidence accuracy: 65% (26 trades) | Low-confidence accuracy: 50% (4 trades)

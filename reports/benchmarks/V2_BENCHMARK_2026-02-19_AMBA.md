# TradingAgents V2 Benchmark Report
**Run ID:** v2_20260219_034243
**Date:** 2026-02-19
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
| &nbsp;&nbsp;ensemble_weighted_vote+lightgbm+xgboost | model=weighted_vote |

## Executive Summary (Next-Day Accuracy)

| Metric | ensemble_weighted_vote+lightgbm+xgboost |
|--------|--------|
| Next-day accuracy | **40.0%** |
| Total P&L (post-cost) | **$-326.51** |
| Max drawdown | **$1,564.59** |
| Avg confidence | 0.82 |
| BUY % | 47% |
| SELL % | 27% |
| HOLD % | 27% |
| Analyses | 30 |

## 5-Day Forward Accuracy

| Metric | ensemble_weighted_vote+lightgbm+xgboost |
|--------|--------|
| 5-day accuracy | 10/30 (33.3%) |
| 5-day P&L | $3,039.12 |

---

## Multi-Horizon Analysis

### Horizon Comparison (All Models)

| Horizon | ensemble_weighted_vote+lightgbm+xgboost | Winner |
|---------|---------|--------|
| 1d      |    36.7% | ensemble_weighted_vote+lightgbm+xgboost |
| 3d      |    33.3% | ensemble_weighted_vote+lightgbm+xgboost |
| 1w      |    33.3% | ensemble_weighted_vote+lightgbm+xgboost |
| 2w      |    40.0% | ensemble_weighted_vote+lightgbm+xgboost |
| 4w      |    33.3% | ensemble_weighted_vote+lightgbm+xgboost |
| 8w      |    41.4% | ensemble_weighted_vote+lightgbm+xgboost |
| 13w     |    56.0% | ensemble_weighted_vote+lightgbm+xgboost |
| **Overall** |    38.7% | ensemble_weighted_vote+lightgbm+xgboost |

### ensemble_weighted_vote+lightgbm+xgboost — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1d      | 11      | 30    |  36.7% |               +1.60% |            +0.16% |
| 3d      | 10      | 30    |  33.3% |               +6.60% |            -0.12% |
| 1w      | 10      | 30    |  33.3% |               +6.41% |            -1.04% |
| 2w      | 12      | 30    |  40.0% |               +9.49% |            -0.19% |
| 4w      | 10      | 30    |  33.3% |              +16.18% |            -1.58% |
| 8w      | 12      | 29    |  41.4% |              +16.83% |            +5.07% |
| 13w     | 14      | 25    |  56.0% |              +21.42% |           +12.70% |

## Cross-Horizon Consistency

### Cross-Horizon Consistency

| Metric | ensemble_weighted_vote+lightgbm+xgboost |
|--------|---------|
| All horizons correct | 2/30 (7%) |
| All horizons wrong | 7/30 (23%) |
| Mixed results | 21/30 (70%) |

### Short-Term vs Long-Term Accuracy

| Model | Short (1d+3d avg) | Long (8w+13w avg) | Delta |
|-------|-------------------|-------------------|-------|
| ensemble_weighted_vote+lightgbm+xgboost | 35.0% | 48.1% | +13.1% |

### BUY Decision Accuracy by Horizon

| Horizon | ensemble_weighted_vote+lightgbm+xgboost |
|---------|---------|
| 1d      |  50.0% |
| 3d      |  50.0% |
| 1w      |  50.0% |
| 2w      |  64.3% |
| 4w      |  50.0% |
| 8w      |  69.2% |
| 13w     |  81.8% |

### SELL Decision Accuracy by Horizon

| Horizon | ensemble_weighted_vote+lightgbm+xgboost |
|---------|---------|
| 1d      |  37.5% |
| 3d      |  37.5% |
| 1w      |  37.5% |
| 2w      |  25.0% |
| 4w      |  37.5% |
| 8w      |  25.0% |
| 13w     |  71.4% |

---


## Conclusion

- **Most accurate strategy:** ensemble_weighted_vote+lightgbm+xgboost (40.0%)
- **Highest P&L strategy:** ensemble_weighted_vote+lightgbm+xgboost ($-326.51)

## Results by Month

| Month | ensemble_weighted_vote+lightgbm+xgboost |
|-------|--------|
| 2025-03 | 1/3 (33%) |
| 2025-03 | 1/3 (33%) |
| 2025-03 | 1/3 (33%) |
| 2025-04 | 2/3 (67%) |
| 2025-04 | 2/3 (67%) |
| 2025-04 | 2/3 (67%) |
| 2025-05 | 2/3 (67%) |
| 2025-05 | 2/3 (67%) |
| 2025-05 | 2/3 (67%) |
| 2025-06 | 0/3 (0%) |
| 2025-06 | 0/3 (0%) |
| 2025-06 | 0/3 (0%) |
| 2025-07 | 1/3 (33%) |
| 2025-07 | 1/3 (33%) |
| 2025-07 | 1/3 (33%) |
| 2025-08 | 2/3 (67%) |
| 2025-08 | 2/3 (67%) |
| 2025-08 | 2/3 (67%) |
| 2025-09 | 1/3 (33%) |
| 2025-09 | 1/3 (33%) |
| 2025-09 | 1/3 (33%) |
| 2025-10 | 0/3 (0%) |
| 2025-10 | 0/3 (0%) |
| 2025-10 | 0/3 (0%) |
| 2025-11 | 1/3 (33%) |
| 2025-11 | 1/3 (33%) |
| 2025-11 | 1/3 (33%) |
| 2025-12 | 2/3 (67%) |
| 2025-12 | 2/3 (67%) |
| 2025-12 | 2/3 (67%) |

## Results by Ticker

| Ticker | ensemble_weighted_vote+lightgbm+xgboost Acc | ensemble_weighted_vote+lightgbm+xgboost P&L |
|--------|--------|---------|
| AMBA | 40% | $-327 |

## Decision Distribution

**ensemble_weighted_vote+lightgbm+xgboost:** BUY 47% | SELL 27% | HOLD 27% (n=30)


## Free Baselines Comparison

| Strategy | 1d | 3d | 1w | 2w | 4w | 8w | 13w |
|----------|------|------|------|------|------|------|------|
| **ensemble_weighted_vote+lightgbm+xgboost** | 36.7% | 33.3% | 33.3% | 40.0% | 33.3% | 41.4% | 56.0% |
| Always-BUY | 50.0% | 53.3% | 50.0% | 63.3% | 50.0% | 75.9% | 68.0% |
| Always-SELL | 46.7% | 46.7% | 43.3% | 36.7% | 50.0% | 24.1% | 32.0% |
| Momentum-5d | 36.7% | 43.3% | 46.7% | 53.3% | 53.3% | 62.1% | 48.0% |
| Random (expected) | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% |


## Walk-Forward Validation

**Split date:** 2025-09-01 (Period 1: before, Period 2: after)

| Strategy | Period 1 (in-sample) | Period 2 (out-of-sample) | Delta |
|----------|---------------------|-------------------------|-------|
| ensemble_weighted_vote+lightgbm+xgboost | 8/18 (44.4%) | 4/12 (33.3%) | -11.1% |

### Walk-Forward by Horizon

| Strategy | Horizon | P1 Acc | P2 Acc | Delta |
|----------|---------|--------|--------|-------|
| ensemble_weighted_vote+lightgbm+xgboost | 1d | 38.9% | 33.3% | -5.6% |
| ensemble_weighted_vote+lightgbm+xgboost | 3d | 33.3% | 33.3% | +0.0% |
| ensemble_weighted_vote+lightgbm+xgboost | 1w | 33.3% | 33.3% | +0.0% |
| ensemble_weighted_vote+lightgbm+xgboost | 2w | 50.0% | 25.0% | -25.0% |
| ensemble_weighted_vote+lightgbm+xgboost | 4w | 38.9% | 25.0% | -13.9% |
| ensemble_weighted_vote+lightgbm+xgboost | 8w | 55.6% | 18.2% | -37.4% |
| ensemble_weighted_vote+lightgbm+xgboost | 13w | 55.6% | 57.1% | +1.6% |


## Statistical Significance

### Binomial Test vs Always-BUY Baseline

| Strategy | Horizon | Model Acc | Baseline Acc | p-value | Significant? |
|----------|---------|-----------|-------------|---------|-------------|
| ensemble_weighted_vote+lightgbm+xgboost | 1d | 36.7% | 50.0% | 0.2005 | No |
| ensemble_weighted_vote+lightgbm+xgboost | 3d | 33.3% | 53.3% | 0.0423 | Yes |
| ensemble_weighted_vote+lightgbm+xgboost | 1w | 33.3% | 50.0% | 0.0987 | No |
| ensemble_weighted_vote+lightgbm+xgboost | 2w | 40.0% | 63.3% | 0.0124 | Yes |
| ensemble_weighted_vote+lightgbm+xgboost | 4w | 33.3% | 50.0% | 0.0987 | No |
| ensemble_weighted_vote+lightgbm+xgboost | 8w | 41.4% | 75.9% | 0.0001 | Yes |
| ensemble_weighted_vote+lightgbm+xgboost | 13w | 56.0% | 68.0% | 0.2034 | No |

### Bootstrap 95% CI (Next-Day Accuracy)

| Strategy | Accuracy | 95% CI | n |
|----------|----------|--------|---|
| ensemble_weighted_vote+lightgbm+xgboost | 40.0% | [23.3%, 56.7%] | 30 |


---


## Confidence Analysis

**ensemble_weighted_vote+lightgbm+xgboost:** Avg confidence: 0.82 | High-confidence accuracy: 45% (22 trades) | Low-confidence accuracy: 25% (8 trades)

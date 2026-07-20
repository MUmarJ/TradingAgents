# TradingAgents V2 Benchmark Report
**Run ID:** v2_20260217_190514
**Date:** 2026-02-17
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
| &nbsp;&nbsp;ts_kronos_small | model=small |

## Executive Summary (Next-Day Accuracy)

| Metric | ts_kronos_small |
|--------|--------|
| Next-day accuracy | **43.3%** |
| Total P&L (post-cost) | **$-692.08** |
| Max drawdown | **$2,361.03** |
| Avg confidence | 0.90 |
| BUY % | 50% |
| SELL % | 47% |
| HOLD % | 3% |
| Analyses | 30 |

## 5-Day Forward Accuracy

| Metric | ts_kronos_small |
|--------|--------|
| 5-day accuracy | 15/30 (50.0%) |
| 5-day P&L | $2,943.32 |

---

## Multi-Horizon Analysis

### Horizon Comparison (All Models)

| Horizon | ts_kronos_small | Winner |
|---------|---------|--------|
| 1d      |    40.0% | ts_kronos_small |
| 3d      |    60.0% | ts_kronos_small |
| 1w      |    50.0% | ts_kronos_small |
| 2w      |    50.0% | ts_kronos_small |
| 4w      |    43.3% | ts_kronos_small |
| 8w      |    42.9% | ts_kronos_small |
| 13w     |    56.0% | ts_kronos_small |
| **Overall** |    48.8% | ts_kronos_small |

### ts_kronos_small — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1d      | 12      | 30    |  40.0% |               +1.12% |            +0.40% |
| 3d      | 18      | 30    |  60.0% |               +3.36% |            +0.25% |
| 1w      | 15      | 30    |  50.0% |               +2.43% |            +0.45% |
| 2w      | 15      | 30    |  50.0% |               +4.19% |            +3.17% |
| 4w      | 13      | 30    |  43.3% |               +6.73% |            +2.51% |
| 8w      | 12      | 28    |  42.9% |              +11.71% |            +9.95% |
| 13w     | 14      | 25    |  56.0% |              +17.54% |           +17.63% |

## Cross-Horizon Consistency

### Cross-Horizon Consistency

| Metric | ts_kronos_small |
|--------|---------|
| All horizons correct | 1/30 (3%) |
| All horizons wrong | 4/30 (13%) |
| Mixed results | 25/30 (83%) |

### Short-Term vs Long-Term Accuracy

| Model | Short (1d+3d avg) | Long (8w+13w avg) | Delta |
|-------|-------------------|-------------------|-------|
| ts_kronos_small | 50.0% | 49.1% | -0.9% |

### BUY Decision Accuracy by Horizon

| Horizon | ts_kronos_small |
|---------|---------|
| 1d      |  40.0% |
| 3d      |  66.7% |
| 1w      |  53.3% |
| 2w      |  66.7% |
| 4w      |  46.7% |
| 8w      |  71.4% |
| 13w     |  75.0% |

### SELL Decision Accuracy by Horizon

| Horizon | ts_kronos_small |
|---------|---------|
| 1d      |  42.9% |
| 3d      |  57.1% |
| 1w      |  50.0% |
| 2w      |  35.7% |
| 4w      |  42.9% |
| 8w      |  15.4% |
| 13w     |  41.7% |

---


## Conclusion

- **Most accurate strategy:** ts_kronos_small (43.3%)
- **Highest P&L strategy:** ts_kronos_small ($-692.08)

## Results by Month

| Month | ts_kronos_small |
|-------|--------|
| 2025-03 | 2/3 (67%) |
| 2025-03 | 2/3 (67%) |
| 2025-03 | 2/3 (67%) |
| 2025-04 | 1/3 (33%) |
| 2025-04 | 1/3 (33%) |
| 2025-04 | 1/3 (33%) |
| 2025-05 | 2/3 (67%) |
| 2025-05 | 2/3 (67%) |
| 2025-05 | 2/3 (67%) |
| 2025-06 | 0/3 (0%) |
| 2025-06 | 0/3 (0%) |
| 2025-06 | 0/3 (0%) |
| 2025-07 | 2/3 (67%) |
| 2025-07 | 2/3 (67%) |
| 2025-07 | 2/3 (67%) |
| 2025-08 | 1/3 (33%) |
| 2025-08 | 1/3 (33%) |
| 2025-08 | 1/3 (33%) |
| 2025-09 | 1/3 (33%) |
| 2025-09 | 1/3 (33%) |
| 2025-09 | 1/3 (33%) |
| 2025-10 | 1/3 (33%) |
| 2025-10 | 1/3 (33%) |
| 2025-10 | 1/3 (33%) |
| 2025-11 | 2/3 (67%) |
| 2025-11 | 2/3 (67%) |
| 2025-11 | 2/3 (67%) |
| 2025-12 | 1/3 (33%) |
| 2025-12 | 1/3 (33%) |
| 2025-12 | 1/3 (33%) |

## Results by Ticker

| Ticker | ts_kronos_small Acc | ts_kronos_small P&L |
|--------|--------|---------|
| AMBA | 43% | $-692 |

## Decision Distribution

**ts_kronos_small:** BUY 50% | SELL 47% | HOLD 3% (n=30)


## Free Baselines Comparison

| Strategy | 1d | 3d | 1w | 2w | 4w | 8w | 13w |
|----------|------|------|------|------|------|------|------|
| **ts_kronos_small** | 40.0% | 60.0% | 50.0% | 50.0% | 43.3% | 42.9% | 56.0% |
| Always-BUY | 50.0% | 53.3% | 50.0% | 63.3% | 50.0% | 78.6% | 68.0% |
| Always-SELL | 46.7% | 46.7% | 43.3% | 36.7% | 50.0% | 21.4% | 32.0% |
| Momentum-5d | 36.7% | 43.3% | 46.7% | 53.3% | 53.3% | 60.7% | 48.0% |
| Random (expected) | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% |


## Walk-Forward Validation

**Split date:** 2025-09-01 (Period 1: before, Period 2: after)

| Strategy | Period 1 (in-sample) | Period 2 (out-of-sample) | Delta |
|----------|---------------------|-------------------------|-------|
| ts_kronos_small | 8/18 (44.4%) | 5/12 (41.7%) | -2.8% |

### Walk-Forward by Horizon

| Strategy | Horizon | P1 Acc | P2 Acc | Delta |
|----------|---------|--------|--------|-------|
| ts_kronos_small | 1d | 38.9% | 41.7% | +2.8% |
| ts_kronos_small | 3d | 55.6% | 66.7% | +11.1% |
| ts_kronos_small | 1w | 38.9% | 66.7% | +27.8% |
| ts_kronos_small | 2w | 44.4% | 58.3% | +13.9% |
| ts_kronos_small | 4w | 44.4% | 41.7% | -2.8% |
| ts_kronos_small | 8w | 50.0% | 30.0% | -20.0% |
| ts_kronos_small | 13w | 55.6% | 57.1% | +1.6% |


## Statistical Significance

### Binomial Test vs Always-BUY Baseline

| Strategy | Horizon | Model Acc | Baseline Acc | p-value | Significant? |
|----------|---------|-----------|-------------|---------|-------------|
| ts_kronos_small | 1d | 40.0% | 50.0% | 0.3616 | No |
| ts_kronos_small | 3d | 60.0% | 53.3% | 0.5838 | No |
| ts_kronos_small | 1w | 50.0% | 50.0% | 1.0000 | No |
| ts_kronos_small | 2w | 50.0% | 63.3% | 0.1339 | No |
| ts_kronos_small | 4w | 43.3% | 50.0% | 0.5847 | No |
| ts_kronos_small | 8w | 42.9% | 78.6% | 0.0000 | Yes |
| ts_kronos_small | 13w | 56.0% | 68.0% | 0.2034 | No |

### Bootstrap 95% CI (Next-Day Accuracy)

| Strategy | Accuracy | 95% CI | n |
|----------|----------|--------|---|
| ts_kronos_small | 43.3% | [26.7%, 60.0%] | 30 |


---


## Confidence Analysis

**ts_kronos_small:** Avg confidence: 0.90 | High-confidence accuracy: 41% (29 trades) | Low-confidence accuracy: 100% (1 trades)

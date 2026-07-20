# TradingAgents V2 Benchmark Report
**Run ID:** v2_20260214_193006
**Date:** 2026-02-14
**Period:** 2025-03-01 to 2025-12-31
**Tickers:** AMBA (1 tickers)
**Dates:** 30 tri-monthly snapshots
**Version:** 2 (look-ahead free, no HOLD fallback)
**Date Mode:** tri-monthly (10th, 20th, end-of-month)
**Horizons:** 1d, 3d, 1w, 2w, 4w, 8w, 13w (7 projection horizons)
**Total tasks:** 60
**Completed:** 60
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
| Model Tiers | 2 configurations |
| &nbsp;&nbsp;single_sonnet-4-5 | model=claude-sonnet-4-5-20250929 |
| &nbsp;&nbsp;single_gpt-5.1-codex-mini | model=gpt-5.1-codex-mini |

## Executive Summary (Next-Day Accuracy)

| Metric | single_sonnet-4-5 | single_gpt-5.1-codex-mini |
|--------|--------|--------|
| Next-day accuracy | **36.7%** | 36.7% |
| Total P&L (post-cost) | $-875.22 | **$467.62** |
| Max drawdown | $1,532.12 | **$915.80** |
| Avg confidence | 0.66 | 0.45 |
| BUY % | 10% | 47% |
| SELL % | 40% | 20% |
| HOLD % | 50% | 33% |
| Analyses | 30 | 30 |

## 5-Day Forward Accuracy

| Metric | single_sonnet-4-5 | single_gpt-5.1-codex-mini |
|--------|--------|--------|
| 5-day accuracy | 10/30 (33.3%) | 13/30 (43.3%) |
| 5-day P&L | $-4,131.01 | $1,656.94 |

---

## Multi-Horizon Analysis

### Horizon Comparison (All Models)

| Horizon | single_sonnet-4-5 | single_gpt-5.1-codex-mini | Winner |
|---------|---------|---------|--------|
| 1d      | **30.0%** |    26.7% | single_sonnet-4-5 |
| 3d      |    23.3% | **26.7%** | single_gpt-5.1-codex-mini |
| 1w      |    33.3% | **43.3%** | single_gpt-5.1-codex-mini |
| 2w      |    16.7% | **40.0%** | single_gpt-5.1-codex-mini |
| 4w      |    23.3% | **36.7%** | single_gpt-5.1-codex-mini |
| 8w      |    17.9% | **42.9%** | single_gpt-5.1-codex-mini |
| 13w     |    20.0% | **28.0%** | single_gpt-5.1-codex-mini |
| **Overall** |    23.6% |    35.0% | single_gpt-5.1-codex-mini |

### single_sonnet-4-5 — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1d      | 9       | 30    |  30.0% |               -0.88% |            +1.36% |
| 3d      | 7       | 30    |  23.3% |               -0.89% |            +3.04% |
| 1w      | 10      | 30    |  33.3% |               -1.91% |            +3.12% |
| 2w      | 5       | 30    |  16.7% |               -3.11% |            +5.04% |
| 4w      | 7       | 30    |  23.3% |               -1.39% |            +6.09% |
| 8w      | 5       | 28    |  17.9% |               +4.77% |           +11.99% |
| 13w     | 5       | 25    |  20.0% |               +1.34% |           +21.64% |

### single_gpt-5.1-codex-mini — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1d      | 8       | 30    |  26.7% |               +1.97% |            +0.22% |
| 3d      | 8       | 30    |  26.7% |               +2.33% |            +2.04% |
| 1w      | 13      | 30    |  43.3% |               +0.86% |            +1.89% |
| 2w      | 12      | 30    |  40.0% |               +2.19% |            +4.67% |
| 4w      | 11      | 30    |  36.7% |               +0.49% |            +6.57% |
| 8w      | 12      | 28    |  42.9% |              +10.84% |           +10.60% |
| 13w     | 7       | 25    |  28.0% |              +24.65% |           +14.83% |

## Cross-Horizon Consistency

### Cross-Horizon Consistency

| Metric | single_sonnet-4-5 | single_gpt-5.1-codex-mini |
|--------|---------||---------|
| All horizons correct | 0/30 (0%) | 2/30 (7%) |
| All horizons wrong | 8/30 (27%) | 9/30 (30%) |
| Mixed results | 22/30 (73%) | 19/30 (63%) |

### Short-Term vs Long-Term Accuracy

| Model | Short (1d+3d avg) | Long (8w+13w avg) | Delta |
|-------|-------------------|-------------------|-------|
| single_sonnet-4-5 | 26.7% | 18.9% | -7.8% |
| single_gpt-5.1-codex-mini | 26.7% | 35.8% | +9.2% |

### BUY Decision Accuracy by Horizon

| Horizon | single_sonnet-4-5 | single_gpt-5.1-codex-mini |
|---------|---------|---------|
| 1d      |  33.3% |  35.7% |
| 3d      |  66.7% |  42.9% |
| 1w      |  66.7% |  57.1% |
| 2w      |  66.7% |  64.3% |
| 4w      |  66.7% |  50.0% |
| 8w      | 100.0% |  78.6% |
| 13w     |  66.7% |  50.0% |

### SELL Decision Accuracy by Horizon

| Horizon | single_sonnet-4-5 | single_gpt-5.1-codex-mini |
|---------|---------|---------|
| 1d      |  50.0% |  33.3% |
| 3d      |  41.7% |  33.3% |
| 1w      |  41.7% |  50.0% |
| 2w      |  25.0% |  50.0% |
| 4w      |  16.7% |  66.7% |
| 8w      |   9.1% |  16.7% |
| 13w     |  30.0% |   0.0% |

---


## Conclusion

- **Most accurate strategy:** single_sonnet-4-5 (36.7%)
- **Highest P&L strategy:** single_gpt-5.1-codex-mini ($467.62)

## Results by Month

| Month | single_sonnet-4-5 | single_gpt-5.1-codex-mini |
|-------|--------|--------|
| 2025-03 | 1/3 (33%) | 1/3 (33%) |
| 2025-03 | 1/3 (33%) | 1/3 (33%) |
| 2025-03 | 1/3 (33%) | 1/3 (33%) |
| 2025-04 | 2/3 (67%) | 1/3 (33%) |
| 2025-04 | 2/3 (67%) | 1/3 (33%) |
| 2025-04 | 2/3 (67%) | 1/3 (33%) |
| 2025-05 | 0/3 (0%) | 1/3 (33%) |
| 2025-05 | 0/3 (0%) | 1/3 (33%) |
| 2025-05 | 0/3 (0%) | 1/3 (33%) |
| 2025-06 | 1/3 (33%) | 1/3 (33%) |
| 2025-06 | 1/3 (33%) | 1/3 (33%) |
| 2025-06 | 1/3 (33%) | 1/3 (33%) |
| 2025-07 | 1/3 (33%) | 1/3 (33%) |
| 2025-07 | 1/3 (33%) | 1/3 (33%) |
| 2025-07 | 1/3 (33%) | 1/3 (33%) |
| 2025-08 | 2/3 (67%) | 2/3 (67%) |
| 2025-08 | 2/3 (67%) | 2/3 (67%) |
| 2025-08 | 2/3 (67%) | 2/3 (67%) |
| 2025-09 | 2/3 (67%) | 2/3 (67%) |
| 2025-09 | 2/3 (67%) | 2/3 (67%) |
| 2025-09 | 2/3 (67%) | 2/3 (67%) |
| 2025-10 | 1/3 (33%) | 0/3 (0%) |
| 2025-10 | 1/3 (33%) | 0/3 (0%) |
| 2025-10 | 1/3 (33%) | 0/3 (0%) |
| 2025-11 | 0/3 (0%) | 0/3 (0%) |
| 2025-11 | 0/3 (0%) | 0/3 (0%) |
| 2025-11 | 0/3 (0%) | 0/3 (0%) |
| 2025-12 | 1/3 (33%) | 2/3 (67%) |
| 2025-12 | 1/3 (33%) | 2/3 (67%) |
| 2025-12 | 1/3 (33%) | 2/3 (67%) |

## Results by Ticker

| Ticker | single_sonnet-4-5 Acc | single_sonnet-4-5 P&L | single_gpt-5.1-codex-mini Acc | single_gpt-5.1-codex-mini P&L |
|--------|--------|---------|--------|---------|
| AMBA | 37% | $-875 | 37% | $468 |

## Decision Distribution

**single_sonnet-4-5:** BUY 10% | SELL 40% | HOLD 50% (n=30)
**single_gpt-5.1-codex-mini:** BUY 47% | SELL 20% | HOLD 33% (n=30)


## Free Baselines Comparison

| Strategy | 1d | 3d | 1w | 2w | 4w | 8w | 13w |
|----------|------|------|------|------|------|------|------|
| **single_sonnet-4-5** | 30.0% | 23.3% | 33.3% | 16.7% | 23.3% | 17.9% | 20.0% |
| **single_gpt-5.1-codex-mini** | 26.7% | 26.7% | 43.3% | 40.0% | 36.7% | 42.9% | 28.0% |
| Always-BUY | 50.0% | 53.3% | 50.0% | 63.3% | 50.0% | 78.6% | 68.0% |
| Always-SELL | 46.7% | 46.7% | 43.3% | 36.7% | 50.0% | 21.4% | 32.0% |
| Momentum-5d | 36.7% | 43.3% | 46.7% | 53.3% | 53.3% | 60.7% | 48.0% |
| Random (expected) | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% |


## Walk-Forward Validation

**Split date:** 2025-09-01 (Period 1: before, Period 2: after)

| Strategy | Period 1 (in-sample) | Period 2 (out-of-sample) | Delta |
|----------|---------------------|-------------------------|-------|
| single_sonnet-4-5 | 7/18 (38.9%) | 4/12 (33.3%) | -5.6% |
| single_gpt-5.1-codex-mini | 7/18 (38.9%) | 4/12 (33.3%) | -5.6% |

### Walk-Forward by Horizon

| Strategy | Horizon | P1 Acc | P2 Acc | Delta |
|----------|---------|--------|--------|-------|
| single_sonnet-4-5 | 1d | 27.8% | 33.3% | +5.6% |
| single_sonnet-4-5 | 3d | 22.2% | 25.0% | +2.8% |
| single_sonnet-4-5 | 1w | 22.2% | 50.0% | +27.8% |
| single_sonnet-4-5 | 2w | 22.2% | 8.3% | -13.9% |
| single_sonnet-4-5 | 4w | 11.1% | 41.7% | +30.6% |
| single_sonnet-4-5 | 8w | 16.7% | 20.0% | +3.3% |
| single_sonnet-4-5 | 13w | 16.7% | 28.6% | +11.9% |
| single_gpt-5.1-codex-mini | 1d | 27.8% | 25.0% | -2.8% |
| single_gpt-5.1-codex-mini | 3d | 27.8% | 25.0% | -2.8% |
| single_gpt-5.1-codex-mini | 1w | 38.9% | 50.0% | +11.1% |
| single_gpt-5.1-codex-mini | 2w | 38.9% | 41.7% | +2.8% |
| single_gpt-5.1-codex-mini | 4w | 44.4% | 25.0% | -19.4% |
| single_gpt-5.1-codex-mini | 8w | 44.4% | 40.0% | -4.4% |
| single_gpt-5.1-codex-mini | 13w | 38.9% | 0.0% | -38.9% |


## Statistical Significance

### Binomial Test vs Always-BUY Baseline

| Strategy | Horizon | Model Acc | Baseline Acc | p-value | Significant? |
|----------|---------|-----------|-------------|---------|-------------|
| single_sonnet-4-5 | 1d | 30.0% | 50.0% | 0.0428 | Yes |
| single_sonnet-4-5 | 3d | 23.3% | 53.3% | 0.0014 | Yes |
| single_sonnet-4-5 | 1w | 33.3% | 50.0% | 0.0987 | No |
| single_sonnet-4-5 | 2w | 16.7% | 63.3% | 0.0000 | Yes |
| single_sonnet-4-5 | 4w | 23.3% | 50.0% | 0.0052 | Yes |
| single_sonnet-4-5 | 8w | 17.9% | 78.6% | 0.0000 | Yes |
| single_sonnet-4-5 | 13w | 20.0% | 68.0% | 0.0000 | Yes |
| single_gpt-5.1-codex-mini | 1d | 26.7% | 50.0% | 0.0161 | Yes |
| single_gpt-5.1-codex-mini | 3d | 26.7% | 53.3% | 0.0051 | Yes |
| single_gpt-5.1-codex-mini | 1w | 43.3% | 50.0% | 0.5847 | No |
| single_gpt-5.1-codex-mini | 2w | 40.0% | 63.3% | 0.0124 | Yes |
| single_gpt-5.1-codex-mini | 4w | 36.7% | 50.0% | 0.2005 | No |
| single_gpt-5.1-codex-mini | 8w | 42.9% | 78.6% | 0.0000 | Yes |
| single_gpt-5.1-codex-mini | 13w | 28.0% | 68.0% | 0.0000 | Yes |

### Bootstrap 95% CI (Next-Day Accuracy)

| Strategy | Accuracy | 95% CI | n |
|----------|----------|--------|---|
| single_sonnet-4-5 | 36.7% | [20.0%, 53.3%] | 30 |
| single_gpt-5.1-codex-mini | 36.7% | [20.0%, 53.3%] | 30 |


---


## Confidence Analysis

**single_sonnet-4-5:** Avg confidence: 0.66 | High-confidence accuracy: 37% (27 trades) | Low-confidence accuracy: 33% (3 trades)
**single_gpt-5.1-codex-mini:** Avg confidence: 0.45 | High-confidence accuracy: 33% (3 trades) | Low-confidence accuracy: 40% (25 trades)

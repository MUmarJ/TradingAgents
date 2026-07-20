# TradingAgents V2 Benchmark Report
**Run ID:** v2_20260215_175115
**Date:** 2026-02-15
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
| &nbsp;&nbsp;sentiment_deberta-finance | model=deberta-finance |

## Executive Summary (Next-Day Accuracy)

| Metric | sentiment_deberta-finance |
|--------|--------|
| Next-day accuracy | **46.7%** |
| Total P&L (post-cost) | **$944.85** |
| Max drawdown | **$1,722.45** |
| Avg confidence | 0.71 |
| BUY % | 73% |
| SELL % | 0% |
| HOLD % | 27% |
| Analyses | 30 |

## 5-Day Forward Accuracy

| Metric | sentiment_deberta-finance |
|--------|--------|
| 5-day accuracy | 9/30 (30.0%) |
| 5-day P&L | $-1,227.33 |

---

## Multi-Horizon Analysis

### Horizon Comparison (All Models)

| Horizon | sentiment_deberta-finance | Winner |
|---------|---------|--------|
| 1d      |    36.7% | sentiment_deberta-finance |
| 3d      |    33.3% | sentiment_deberta-finance |
| 1w      |    30.0% | sentiment_deberta-finance |
| 2w      |    46.7% | sentiment_deberta-finance |
| 4w      |    40.0% | sentiment_deberta-finance |
| 8w      |    53.6% | sentiment_deberta-finance |
| 13w     |    40.0% | sentiment_deberta-finance |
| **Overall** |    39.9% | sentiment_deberta-finance |

### sentiment_deberta-finance — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1d      | 11      | 30    |  36.7% |               +3.14% |            -0.74% |
| 3d      | 10      | 30    |  33.3% |               +6.26% |            +0.05% |
| 1w      | 9       | 30    |  30.0% |               +6.78% |            -0.85% |
| 2w      | 14      | 30    |  46.7% |               +8.77% |            -0.77% |
| 4w      | 12      | 30    |  40.0% |              +13.40% |            -1.70% |
| 8w      | 15      | 28    |  53.6% |              +13.88% |            +7.04% |
| 13w     | 10      | 25    |  40.0% |              +30.84% |            +8.74% |

## Cross-Horizon Consistency

### Cross-Horizon Consistency

| Metric | sentiment_deberta-finance |
|--------|---------|
| All horizons correct | 1/30 (3%) |
| All horizons wrong | 7/30 (23%) |
| Mixed results | 22/30 (73%) |

### Short-Term vs Long-Term Accuracy

| Model | Short (1d+3d avg) | Long (8w+13w avg) | Delta |
|-------|-------------------|-------------------|-------|
| sentiment_deberta-finance | 35.0% | 47.2% | +12.2% |

### BUY Decision Accuracy by Horizon

| Horizon | sentiment_deberta-finance |
|---------|---------|
| 1d      |  50.0% |
| 3d      |  45.5% |
| 1w      |  40.9% |
| 2w      |  63.6% |
| 4w      |  45.5% |
| 8w      |  75.0% |
| 13w     |  58.8% |

### SELL Decision Accuracy by Horizon

| Horizon | sentiment_deberta-finance |
|---------|---------|
| 1d      |   N/A |
| 3d      |   N/A |
| 1w      |   N/A |
| 2w      |   N/A |
| 4w      |   N/A |
| 8w      |   N/A |
| 13w     |   N/A |

---


## Conclusion

- **Most accurate strategy:** sentiment_deberta-finance (46.7%)
- **Highest P&L strategy:** sentiment_deberta-finance ($944.85)

## Results by Month

| Month | sentiment_deberta-finance |
|-------|--------|
| 2025-03 | 2/3 (67%) |
| 2025-03 | 2/3 (67%) |
| 2025-03 | 2/3 (67%) |
| 2025-04 | 2/3 (67%) |
| 2025-04 | 2/3 (67%) |
| 2025-04 | 2/3 (67%) |
| 2025-05 | 0/3 (0%) |
| 2025-05 | 0/3 (0%) |
| 2025-05 | 0/3 (0%) |
| 2025-06 | 1/3 (33%) |
| 2025-06 | 1/3 (33%) |
| 2025-06 | 1/3 (33%) |
| 2025-07 | 0/3 (0%) |
| 2025-07 | 0/3 (0%) |
| 2025-07 | 0/3 (0%) |
| 2025-08 | 2/3 (67%) |
| 2025-08 | 2/3 (67%) |
| 2025-08 | 2/3 (67%) |
| 2025-09 | 2/3 (67%) |
| 2025-09 | 2/3 (67%) |
| 2025-09 | 2/3 (67%) |
| 2025-10 | 1/3 (33%) |
| 2025-10 | 1/3 (33%) |
| 2025-10 | 1/3 (33%) |
| 2025-11 | 1/3 (33%) |
| 2025-11 | 1/3 (33%) |
| 2025-11 | 1/3 (33%) |
| 2025-12 | 3/3 (100%) |
| 2025-12 | 3/3 (100%) |
| 2025-12 | 3/3 (100%) |

## Results by Ticker

| Ticker | sentiment_deberta-finance Acc | sentiment_deberta-finance P&L |
|--------|--------|---------|
| AMBA | 47% | $945 |

## Decision Distribution

**sentiment_deberta-finance:** BUY 73% | SELL 0% | HOLD 27% (n=30)


## Free Baselines Comparison

| Strategy | 1d | 3d | 1w | 2w | 4w | 8w | 13w |
|----------|------|------|------|------|------|------|------|
| **sentiment_deberta-finance** | 36.7% | 33.3% | 30.0% | 46.7% | 40.0% | 53.6% | 40.0% |
| Always-BUY | 50.0% | 53.3% | 50.0% | 63.3% | 50.0% | 78.6% | 68.0% |
| Always-SELL | 46.7% | 46.7% | 43.3% | 36.7% | 50.0% | 21.4% | 32.0% |
| Momentum-5d | 36.7% | 43.3% | 46.7% | 53.3% | 53.3% | 60.7% | 48.0% |
| Random (expected) | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% |


## Walk-Forward Validation

**Split date:** 2025-09-01 (Period 1: before, Period 2: after)

| Strategy | Period 1 (in-sample) | Period 2 (out-of-sample) | Delta |
|----------|---------------------|-------------------------|-------|
| sentiment_deberta-finance | 7/18 (38.9%) | 7/12 (58.3%) | +19.4% |

### Walk-Forward by Horizon

| Strategy | Horizon | P1 Acc | P2 Acc | Delta |
|----------|---------|--------|--------|-------|
| sentiment_deberta-finance | 1d | 22.2% | 58.3% | +36.1% |
| sentiment_deberta-finance | 3d | 22.2% | 50.0% | +27.8% |
| sentiment_deberta-finance | 1w | 33.3% | 25.0% | -8.3% |
| sentiment_deberta-finance | 2w | 44.4% | 50.0% | +5.6% |
| sentiment_deberta-finance | 4w | 44.4% | 33.3% | -11.1% |
| sentiment_deberta-finance | 8w | 61.1% | 40.0% | -21.1% |
| sentiment_deberta-finance | 13w | 55.6% | 0.0% | -55.6% |


## Statistical Significance

### Binomial Test vs Always-BUY Baseline

| Strategy | Horizon | Model Acc | Baseline Acc | p-value | Significant? |
|----------|---------|-----------|-------------|---------|-------------|
| sentiment_deberta-finance | 1d | 36.7% | 50.0% | 0.2005 | No |
| sentiment_deberta-finance | 3d | 33.3% | 53.3% | 0.0423 | Yes |
| sentiment_deberta-finance | 1w | 30.0% | 50.0% | 0.0428 | Yes |
| sentiment_deberta-finance | 2w | 46.7% | 63.3% | 0.0861 | No |
| sentiment_deberta-finance | 4w | 40.0% | 50.0% | 0.3616 | No |
| sentiment_deberta-finance | 8w | 53.6% | 78.6% | 0.0040 | Yes |
| sentiment_deberta-finance | 13w | 40.0% | 68.0% | 0.0044 | Yes |

### Bootstrap 95% CI (Next-Day Accuracy)

| Strategy | Accuracy | 95% CI | n |
|----------|----------|--------|---|
| sentiment_deberta-finance | 46.7% | [30.0%, 63.3%] | 30 |


---


## Confidence Analysis

**sentiment_deberta-finance:** Avg confidence: 0.71 | High-confidence accuracy: 50% (22 trades) | Low-confidence accuracy: 38% (8 trades)

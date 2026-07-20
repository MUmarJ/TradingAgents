# TradingAgents V2 Benchmark Report
**Run ID:** v2_20260214_001747
**Date:** 2026-02-14
**Period:** 2025-06-01 to 2025-07-01
**Tickers:** AAPL, MSFT, NVDA, AMBA, JNJ, XOM, JPM, COST, TSLA, NEE (10 tickers)
**Dates:** 1 monthly snapshots
**Version:** 2 (look-ahead free, no HOLD fallback)
**Horizons:** 1d, 3d, 1w, 2w, 4w, 8w, 13w (7 projection horizons)
**Total tasks:** 10
**Completed:** 10
**Failed:** 0
**Failure rate:** 0.0%

## Configuration

| Setting | Value |
|---------|-------|
| LLM Provider | anthropic |
| Deep Think LLM | gpt-5.1-codex-mini |
| Quick Think LLM | gpt-5.2-2025-12-11 |
| Memory Enabled | False |
| ACE Enabled | False |
| Model Tiers | 1 configurations |
| &nbsp;&nbsp;single_haiku-4-5 | model=claude-haiku-4-5-20251001 |

## Executive Summary (Next-Day Accuracy)

| Metric | single_haiku-4-5 |
|--------|--------|
| Next-day accuracy | **50.0%** |
| Total P&L (post-cost) | **$883.57** |
| Max drawdown | **$148.58** |
| Avg confidence | 0.71 |
| BUY % | 0% |
| SELL % | 40% |
| HOLD % | 60% |
| Analyses | 10 |

## 5-Day Forward Accuracy

| Metric | single_haiku-4-5 |
|--------|--------|
| 5-day accuracy | 3/10 (30.0%) |
| 5-day P&L | $-207.11 |

---

## Multi-Horizon Analysis

### Horizon Comparison (All Models)

| Horizon | single_haiku-4-5 | Winner |
|---------|---------|--------|
| 1d      |    40.0% | single_haiku-4-5 |
| 3d      |    30.0% | single_haiku-4-5 |
| 1w      |    30.0% | single_haiku-4-5 |
| 2w      |    20.0% | single_haiku-4-5 |
| 4w      |     0.0% | single_haiku-4-5 |
| 8w      |    10.0% | single_haiku-4-5 |
| 13w     |     0.0% | single_haiku-4-5 |
| **Overall** |    18.6% | single_haiku-4-5 |

### single_haiku-4-5 — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1d      | 4       | 10    |  40.0% |               -2.65% |            +1.41% |
| 3d      | 3       | 10    |  30.0% |               -0.24% |            +3.15% |
| 1w      | 3       | 10    |  30.0% |               -2.27% |            +2.15% |
| 2w      | 2       | 10    |  20.0% |               -1.42% |            +3.01% |
| 4w      | 0       | 10    |   0.0% |               +0.00% |            +3.79% |
| 8w      | 1       | 10    |  10.0% |               +1.10% |            +7.97% |
| 13w     | 0       | 10    |   0.0% |               +0.00% |           +16.35% |

## Cross-Horizon Consistency

### Cross-Horizon Consistency

| Metric | single_haiku-4-5 |
|--------|---------|
| All horizons correct | 0/10 (0%) |
| All horizons wrong | 4/10 (40%) |
| Mixed results | 6/10 (60%) |

### Short-Term vs Long-Term Accuracy

| Model | Short (1d+3d avg) | Long (8w+13w avg) | Delta |
|-------|-------------------|-------------------|-------|
| single_haiku-4-5 | 35.0% | 5.0% | -30.0% |

### BUY Decision Accuracy by Horizon

| Horizon | single_haiku-4-5 |
|---------|---------|
| 1d      |   N/A |
| 3d      |   N/A |
| 1w      |   N/A |
| 2w      |   N/A |
| 4w      |   N/A |
| 8w      |   N/A |
| 13w     |   N/A |

### SELL Decision Accuracy by Horizon

| Horizon | single_haiku-4-5 |
|---------|---------|
| 1d      |  75.0% |
| 3d      |  25.0% |
| 1w      |  25.0% |
| 2w      |  25.0% |
| 4w      |   0.0% |
| 8w      |   0.0% |
| 13w     |   0.0% |

---


## Conclusion

- **Most accurate strategy:** single_haiku-4-5 (50.0%)
- **Highest P&L strategy:** single_haiku-4-5 ($883.57)

## Results by Month

| Month | single_haiku-4-5 |
|-------|--------|
| 2025-06 | 5/10 (50%) |

## Results by Ticker

| Ticker | single_haiku-4-5 Acc | single_haiku-4-5 P&L |
|--------|--------|---------|
| AAPL | 0% | $0 |
| MSFT | 0% | $0 |
| NVDA | 100% | $282 |
| AMBA | 100% | $232 |
| JNJ | 0% | $0 |
| XOM | 0% | $-149 |
| JPM | 100% | $0 |
| COST | 100% | $0 |
| TSLA | 100% | $519 |
| NEE | 0% | $0 |

## Decision Distribution

**single_haiku-4-5:** BUY 0% | SELL 40% | HOLD 60% (n=10)


## Free Baselines Comparison

| Strategy | 1d | 3d | 1w | 2w | 4w | 8w | 13w |
|----------|------|------|------|------|------|------|------|
| **single_haiku-4-5** | 40.0% | 30.0% | 30.0% | 20.0% | 0.0% | 10.0% | 0.0% |
| Always-BUY | 50.0% | 80.0% | 60.0% | 70.0% | 90.0% | 90.0% | 90.0% |
| Always-SELL | 50.0% | 20.0% | 40.0% | 30.0% | 10.0% | 10.0% | 10.0% |
| Momentum-5d | 50.0% | 80.0% | 60.0% | 70.0% | 70.0% | 70.0% | 70.0% |
| Random (expected) | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% |


## Walk-Forward Validation

**Split date:** 2025-09-01 (Period 1: before, Period 2: after)

| Strategy | Period 1 (in-sample) | Period 2 (out-of-sample) | Delta |
|----------|---------------------|-------------------------|-------|
| single_haiku-4-5 | 5/10 (50.0%) | 0/0 (0.0%) | -50.0% |

### Walk-Forward by Horizon

| Strategy | Horizon | P1 Acc | P2 Acc | Delta |
|----------|---------|--------|--------|-------|
| single_haiku-4-5 | 1d | 40.0% | 0.0% | -40.0% |
| single_haiku-4-5 | 3d | 30.0% | 0.0% | -30.0% |
| single_haiku-4-5 | 1w | 30.0% | 0.0% | -30.0% |
| single_haiku-4-5 | 2w | 20.0% | 0.0% | -20.0% |
| single_haiku-4-5 | 4w | 0.0% | 0.0% | +0.0% |
| single_haiku-4-5 | 8w | 10.0% | 0.0% | -10.0% |
| single_haiku-4-5 | 13w | 0.0% | 0.0% | +0.0% |


## Statistical Significance

### Binomial Test vs Always-BUY Baseline

| Strategy | Horizon | Model Acc | Baseline Acc | p-value | Significant? |
|----------|---------|-----------|-------------|---------|-------------|
| single_haiku-4-5 | 1d | 40.0% | 50.0% | 0.7539 | No |
| single_haiku-4-5 | 3d | 30.0% | 80.0% | 0.0009 | Yes |
| single_haiku-4-5 | 1w | 30.0% | 60.0% | 0.1011 | No |
| single_haiku-4-5 | 2w | 20.0% | 70.0% | 0.0016 | Yes |
| single_haiku-4-5 | 4w | 0.0% | 90.0% | 0.0000 | Yes |
| single_haiku-4-5 | 8w | 10.0% | 90.0% | 0.0000 | Yes |
| single_haiku-4-5 | 13w | 0.0% | 90.0% | 0.0000 | Yes |

### Bootstrap 95% CI (Next-Day Accuracy)

| Strategy | Accuracy | 95% CI | n |
|----------|----------|--------|---|
| single_haiku-4-5 | 50.0% | [20.0%, 80.0%] | 10 |


---


## Confidence Analysis

**single_haiku-4-5:** Avg confidence: 0.71 | High-confidence accuracy: 50% (10 trades) | Low-confidence accuracy: 0% (0 trades)

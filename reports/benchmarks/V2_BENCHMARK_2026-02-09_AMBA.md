# TradingAgents V2 Benchmark Report
**Run ID:** v2_20260209_125812
**Date:** 2026-02-09
**Period:** 2025-03-01 to 2026-02-07
**Tickers:** AMBA (1 tickers)
**Dates:** 33 tri-monthly snapshots
**Version:** 2 (look-ahead free, no HOLD fallback)
**Date Mode:** tri-monthly (10th, 20th, end-of-month)
**Horizons:** 1w, 2w, 4w, 8w, 13w (5 projection horizons)
**Total tasks:** 66
**Completed:** 66
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
| Model Tiers | 2 configurations |
| &nbsp;&nbsp;single_sonnet-4-5 | model=claude-sonnet-4-5-20250929 |
| &nbsp;&nbsp;single_opus-4-6 | model=claude-opus-4-6 |

## Executive Summary (Next-Day Accuracy)

| Metric | single_sonnet-4-5 | single_opus-4-6 |
|--------|--------|--------|
| Next-day accuracy | 27.3% | **39.4%** |
| Total P&L (post-cost) | **$-384.40** | $-1,941.23 |
| Max drawdown | **$387.40** | $2,636.12 |
| Avg confidence | 0.71 | 0.69 |
| BUY % | 0% | 3% |
| SELL % | 21% | 48% |
| HOLD % | 79% | 48% |
| Analyses | 33 | 33 |

## 5-Day Forward Accuracy

| Metric | single_sonnet-4-5 | single_opus-4-6 |
|--------|--------|--------|
| 5-day accuracy | 10/33 (30.3%) | 10/33 (30.3%) |
| 5-day P&L | $1,427.98 | $-3,255.40 |

---

## Multi-Horizon Analysis

### Horizon Comparison (All Models)

| Horizon | single_sonnet-4-5 | single_opus-4-6 | Winner |
|---------|---------|---------|--------|
| 1w      |    21.2% | **30.3%** | single_opus-4-6 |
| 2w      |    18.8% | **28.1%** | single_opus-4-6 |
| 4w      |    22.6% | **29.0%** | single_opus-4-6 |
| 8w      | **7.1%** |     7.1% | single_sonnet-4-5 |
| 13w     | **4.2%** |     4.2% | single_sonnet-4-5 |
| **Overall** |    15.5% |    20.9% | single_opus-4-6 |

### single_sonnet-4-5 — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1w      | 7       | 33    |  21.2% |               -5.73% |            +3.19% |
| 2w      | 6       | 32    |  18.8% |               -4.68% |            +4.88% |
| 4w      | 7       | 31    |  22.6% |               -7.30% |            +7.32% |
| 8w      | 2       | 28    |   7.1% |              -21.37% |           +13.17% |
| 13w     | 1       | 24    |   4.2% |              -13.81% |           +21.01% |

### single_opus-4-6 — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1w      | 10      | 33    |  30.3% |               -4.38% |            +3.77% |
| 2w      | 9       | 32    |  28.1% |               -5.54% |            +6.47% |
| 4w      | 9       | 31    |  29.0% |               -7.29% |            +8.64% |
| 8w      | 2       | 28    |   7.1% |              -21.37% |           +13.17% |
| 13w     | 1       | 24    |   4.2% |              -11.09% |           +20.89% |

## Cross-Horizon Consistency

### Cross-Horizon Consistency

| Metric | single_sonnet-4-5 | single_opus-4-6 |
|--------|---------||---------|
| All horizons correct | 2/31 (6%) | 3/31 (10%) |
| All horizons wrong | 18/31 (58%) | 15/31 (48%) |
| Mixed results | 11/31 (35%) | 13/31 (42%) |

### Short-Term vs Long-Term Accuracy

| Model | Short (1w+2w avg) | Long (8w+13w avg) | Delta |
|-------|-------------------|-------------------|-------|
| single_sonnet-4-5 | 20.0% | 5.8% | -14.2% |
| single_opus-4-6 | 29.2% | 5.8% | -23.5% |

### BUY Decision Accuracy by Horizon

| Horizon | single_sonnet-4-5 | single_opus-4-6 |
|---------|---------|---------|
| 1w      |   N/A | 100.0% |
| 2w      |   N/A | 100.0% |
| 4w      |   N/A |   0.0% |
| 8w      |   N/A |   0.0% |
| 13w     |   N/A |   0.0% |

### SELL Decision Accuracy by Horizon

| Horizon | single_sonnet-4-5 | single_opus-4-6 |
|---------|---------|---------|
| 1w      |  57.1% |  43.8% |
| 2w      |  57.1% |  46.7% |
| 4w      |  57.1% |  42.9% |
| 8w      |  28.6% |  16.7% |
| 13w     |  20.0% |  10.0% |

---


## Conclusion

- **Most accurate strategy:** single_opus-4-6 (39.4%)
- **Highest P&L strategy:** single_sonnet-4-5 ($-384.40)

## Results by Month

| Month | single_sonnet-4-5 | single_opus-4-6 |
|-------|--------|--------|
| 2025-03 | 0/3 (0%) | 0/3 (0%) |
| 2025-03 | 0/3 (0%) | 0/3 (0%) |
| 2025-03 | 0/3 (0%) | 0/3 (0%) |
| 2025-04 | 1/3 (33%) | 2/3 (67%) |
| 2025-04 | 1/3 (33%) | 2/3 (67%) |
| 2025-04 | 1/3 (33%) | 2/3 (67%) |
| 2025-05 | 0/3 (0%) | 0/3 (0%) |
| 2025-05 | 0/3 (0%) | 0/3 (0%) |
| 2025-05 | 0/3 (0%) | 0/3 (0%) |
| 2025-06 | 1/3 (33%) | 2/3 (67%) |
| 2025-06 | 1/3 (33%) | 2/3 (67%) |
| 2025-06 | 1/3 (33%) | 2/3 (67%) |
| 2025-07 | 0/3 (0%) | 1/3 (33%) |
| 2025-07 | 0/3 (0%) | 1/3 (33%) |
| 2025-07 | 0/3 (0%) | 1/3 (33%) |
| 2025-08 | 2/3 (67%) | 1/3 (33%) |
| 2025-08 | 2/3 (67%) | 1/3 (33%) |
| 2025-08 | 2/3 (67%) | 1/3 (33%) |
| 2025-09 | 1/3 (33%) | 1/3 (33%) |
| 2025-09 | 1/3 (33%) | 1/3 (33%) |
| 2025-09 | 1/3 (33%) | 1/3 (33%) |
| 2025-10 | 1/3 (33%) | 1/3 (33%) |
| 2025-10 | 1/3 (33%) | 1/3 (33%) |
| 2025-10 | 1/3 (33%) | 1/3 (33%) |
| 2025-11 | 1/3 (33%) | 1/3 (33%) |
| 2025-11 | 1/3 (33%) | 1/3 (33%) |
| 2025-11 | 1/3 (33%) | 1/3 (33%) |
| 2025-12 | 2/3 (67%) | 2/3 (67%) |
| 2025-12 | 2/3 (67%) | 2/3 (67%) |
| 2025-12 | 2/3 (67%) | 2/3 (67%) |
| 2026-01 | 0/3 (0%) | 2/3 (67%) |
| 2026-01 | 0/3 (0%) | 2/3 (67%) |
| 2026-01 | 0/3 (0%) | 2/3 (67%) |

## Results by Ticker

| Ticker | single_sonnet-4-5 Acc | single_sonnet-4-5 P&L | single_opus-4-6 Acc | single_opus-4-6 P&L |
|--------|--------|---------|--------|---------|
| AMBA | 27% | $-384 | 39% | $-1,941 |

## Decision Distribution

**single_sonnet-4-5:** BUY 0% | SELL 21% | HOLD 79% (n=33)
**single_opus-4-6:** BUY 3% | SELL 48% | HOLD 48% (n=33)


## Confidence Analysis

**single_sonnet-4-5:** Avg confidence: 0.71 | High-confidence accuracy: 28% (32 trades) | Low-confidence accuracy: 0% (0 trades)
**single_opus-4-6:** Avg confidence: 0.69 | High-confidence accuracy: 39% (31 trades) | Low-confidence accuracy: 50% (2 trades)

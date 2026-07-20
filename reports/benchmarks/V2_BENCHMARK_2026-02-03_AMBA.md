# TradingAgents V2 Benchmark Report
**Run ID:** v2_20260203_183027
**Date:** 2026-02-03
**Period:** 2025-01-01 to 2025-05-15
**Tickers:** AMBA (1 tickers)
**Dates:** 4 monthly snapshots
**Version:** 2 (look-ahead free, no HOLD fallback)
**Total tasks:** 12
**Completed:** 12
**Failed:** 0
**Failure rate:** 0.0%

## Configuration

| Setting | Value |
|---------|-------|
| LLM Provider | anthropic |
| Deep Think LLM | claude-opus-4-5-20251101 |
| Quick Think LLM | claude-sonnet-4-5-20250929 |
| Memory Enabled | False |
| ACE Enabled | False |
| Model Tiers | 3 configurations |
| &nbsp;&nbsp;ma_opus-4-5+sonnet-4-5 | deep=claude-opus-4-5-20251101, quick=claude-sonnet-4-5-20250929 |
| &nbsp;&nbsp;single_opus-4-5 | model=claude-opus-4-5-20251101 |
| &nbsp;&nbsp;single_sonnet-4-5 | model=claude-sonnet-4-5-20250929 |

## Executive Summary (Next-Day Accuracy)

| Metric | ma_opus-4-5+sonnet-4-5 | single_opus-4-5 | single_sonnet-4-5 |
|--------|--------|--------|--------|
| Next-day accuracy | 25.0% | 50.0% | **75.0%** |
| Total P&L (post-cost) | $645.82 | $0.00 | **$737.08** |
| Max drawdown | $91.25 | **$0.00** | $0.00 |
| Avg confidence | 0.61 | 0.76 | 0.69 |
| BUY % | 0% | 0% | 0% |
| SELL % | 75% | 0% | 25% |
| HOLD % | 25% | 100% | 75% |
| Analyses | 4 | 4 | 4 |

## 5-Day Forward Accuracy

| Metric | ma_opus-4-5+sonnet-4-5 | single_opus-4-5 | single_sonnet-4-5 |
|--------|--------|--------|--------|
| 5-day accuracy | 2/4 (50.0%) | 0/4 (0.0%) | 1/4 (25.0%) |
| 5-day P&L | $2,445.99 | $0.00 | $1,360.90 |

## Conclusion

- **Most accurate strategy:** single_sonnet-4-5 (75.0%)
- **Highest P&L strategy:** single_sonnet-4-5 ($737.08)
- Single-agent (single_sonnet-4-5: 75.0%) matched or exceeded multi-agent (ma_opus-4-5+sonnet-4-5: 25.0%) accuracy.

## Results by Month

| Month | ma_opus-4-5+sonnet-4-5 | single_opus-4-5 | single_sonnet-4-5 |
|-------|--------|--------|--------|
| 2025-01 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |
| 2025-02 | 1/1 (100%) | 0/1 (0%) | 1/1 (100%) |
| 2025-03 | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) |
| 2025-04 | 0/1 (0%) | 1/1 (100%) | 1/1 (100%) |

## Results by Ticker

| Ticker | ma_opus-4-5+sonnet-4-5 Acc | ma_opus-4-5+sonnet-4-5 P&L | single_opus-4-5 Acc | single_opus-4-5 P&L | single_sonnet-4-5 Acc | single_sonnet-4-5 P&L |
|--------|--------|---------|--------|---------|--------|---------|
| AMBA | 25% | $646 | 50% | $0 | 75% | $737 |

## Decision Distribution

**ma_opus-4-5+sonnet-4-5:** BUY 0% | SELL 75% | HOLD 25% (n=4)
**single_opus-4-5:** BUY 0% | SELL 0% | HOLD 100% (n=4)
**single_sonnet-4-5:** BUY 0% | SELL 25% | HOLD 75% (n=4)


## Confidence Analysis

**ma_opus-4-5+sonnet-4-5:** Avg confidence: 0.61 | High-confidence accuracy: 33% (3 trades) | Low-confidence accuracy: 0% (1 trades)
**single_opus-4-5:** Avg confidence: 0.76 | High-confidence accuracy: 50% (4 trades) | Low-confidence accuracy: 0% (0 trades)
**single_sonnet-4-5:** Avg confidence: 0.69 | High-confidence accuracy: 75% (4 trades) | Low-confidence accuracy: 0% (0 trades)

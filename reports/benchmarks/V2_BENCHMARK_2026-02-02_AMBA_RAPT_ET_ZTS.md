# TradingAgents V2 Benchmark Report
**Run ID:** v2_20260202_153754
**Date:** 2026-02-02
**Period:** 2025-01-28 to 2026-01-28
**Tickers:** AMBA, RAPT, ET, ZTS (4 tickers)
**Dates:** 12 monthly snapshots
**Version:** 2 (look-ahead free, no HOLD fallback)
**Total tasks:** 96
**Completed:** 8
**Failed:** 0
**Failure rate:** 0.0%

## Configuration

| Setting | Value |
|---------|-------|
| LLM Provider | openai |
| Deep Think LLM | gpt-5.1-codex-mini |
| Quick Think LLM | gpt-5.1-codex-mini |
| Memory Enabled | False |
| ACE Enabled | False |
| Model Tiers | 2 configurations |
| &nbsp;&nbsp;ma_5.1-codex-mini | deep=gpt-5.1-codex-mini, quick=gpt-5.1-codex-mini |
| &nbsp;&nbsp;single_5.1-codex-mini | model=gpt-5.1-codex-mini |

## Executive Summary (Next-Day Accuracy)

| Metric | ma_5.1-codex-mini | single_5.1-codex-mini |
|--------|--------|--------|
| Next-day accuracy | **50.0%** | 25.0% |
| Total P&L (post-cost) | $0.00 | **$645.82** |
| Max drawdown | **$0.00** | $91.25 |
| Avg confidence | 0.50 | 0.33 |
| BUY % | 0% | 0% |
| SELL % | 0% | 75% |
| HOLD % | 100% | 25% |
| Analyses | 4 | 4 |

## 5-Day Forward Accuracy

| Metric | ma_5.1-codex-mini | single_5.1-codex-mini |
|--------|--------|--------|
| 5-day accuracy | 1/4 (25.0%) | 3/4 (75.0%) |
| 5-day P&L | $0.00 | $2,445.99 |

## Conclusion

- **Most accurate strategy:** ma_5.1-codex-mini (50.0%)
- **Highest P&L strategy:** single_5.1-codex-mini ($645.82)
- Multi-agent (ma_5.1-codex-mini: 50.0%) outperformed single-agent (single_5.1-codex-mini: 25.0%) by 25.0 percentage points.

## Results by Month

| Month | ma_5.1-codex-mini | single_5.1-codex-mini |
|-------|--------|--------|
| 2025-01 | 0/1 (0%) | 0/1 (0%) |
| 2025-02 | 0/1 (0%) | 1/1 (100%) |
| 2025-03 | 1/1 (100%) | 0/1 (0%) |
| 2025-04 | 1/1 (100%) | 0/1 (0%) |
| 2025-05 | N/A | N/A |
| 2025-06 | N/A | N/A |
| 2025-07 | N/A | N/A |
| 2025-08 | N/A | N/A |
| 2025-09 | N/A | N/A |
| 2025-10 | N/A | N/A |
| 2025-11 | N/A | N/A |
| 2025-12 | N/A | N/A |

## Results by Ticker

| Ticker | ma_5.1-codex-mini Acc | ma_5.1-codex-mini P&L | single_5.1-codex-mini Acc | single_5.1-codex-mini P&L |
|--------|--------|---------|--------|---------|
| AMBA | 50% | $0 | 25% | $646 |
| RAPT | 0% | $0 | 0% | $0 |
| ET | 0% | $0 | 0% | $0 |
| ZTS | 0% | $0 | 0% | $0 |

## Decision Distribution

**ma_5.1-codex-mini:** BUY 0% | SELL 0% | HOLD 100% (n=4)
**single_5.1-codex-mini:** BUY 0% | SELL 75% | HOLD 25% (n=4)


## Confidence Analysis

**ma_5.1-codex-mini:** Avg confidence: 0.50 | High-confidence accuracy: 0% (0 trades) | Low-confidence accuracy: 50% (4 trades)
**single_5.1-codex-mini:** Avg confidence: 0.33 | High-confidence accuracy: 0% (0 trades) | Low-confidence accuracy: 25% (4 trades)

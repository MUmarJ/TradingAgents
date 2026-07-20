# TradingAgents V2 Benchmark Report
**Run ID:** v2_20260202_184554
**Date:** 2026-02-02
**Period:** 2025-01-28 to 2025-05-28
**Tickers:** AMBA (1 tickers)
**Dates:** 4 monthly snapshots
**Version:** 2 (look-ahead free, no HOLD fallback)
**Total tasks:** 4
**Completed:** 3
**Failed:** 1
**Failure rate:** 25.0%

## Configuration

| Setting | Value |
|---------|-------|
| LLM Provider | anthropic |
| Deep Think LLM | claude-opus-4-5-20251101 |
| Quick Think LLM | claude-sonnet-4-5-20250929 |
| Memory Enabled | False |
| ACE Enabled | False |
| Model Tiers | 1 configurations |
| &nbsp;&nbsp;ma_opus-4-5+sonnet-4-5 | deep=claude-opus-4-5-20251101, quick=claude-sonnet-4-5-20250929 |

## Failure Analysis

| Error Type | Count | % of Total |
|------------|-------|------------|
| BadRequestError | 1 | 25.0% |

**Sample failure messages:**

- `BadRequestError`: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Your credit balance is too low to access the Anthropic API.

## Executive Summary (Next-Day Accuracy)

| Metric | ma_opus-4-5+sonnet-4-5 |
|--------|--------|
| Next-day accuracy | **0.0%** |
| Total P&L (post-cost) | **$-40.83** |
| Max drawdown | **$40.83** |
| Avg confidence | 0.48 |
| BUY % | 0% |
| SELL % | 33% |
| HOLD % | 67% |
| Analyses | 3 |

## 5-Day Forward Accuracy

| Metric | ma_opus-4-5+sonnet-4-5 |
|--------|--------|
| 5-day accuracy | 2/3 (66.7%) |
| 5-day P&L | $1,720.64 |

## Conclusion

- **Most accurate strategy:** ma_opus-4-5+sonnet-4-5 (0.0%)
- **Highest P&L strategy:** ma_opus-4-5+sonnet-4-5 ($-40.83)

## Results by Month

| Month | ma_opus-4-5+sonnet-4-5 |
|-------|--------|
| 2025-01 | 0/1 (0%) |
| 2025-02 | 0/1 (0%) |
| 2025-03 | 0/1 (0%) |
| 2025-04 | N/A |

## Results by Ticker

| Ticker | ma_opus-4-5+sonnet-4-5 Acc | ma_opus-4-5+sonnet-4-5 P&L |
|--------|--------|---------|
| AMBA | 0% | $-41 |

## Decision Distribution

**ma_opus-4-5+sonnet-4-5:** BUY 0% | SELL 33% | HOLD 67% (n=3)


## Confidence Analysis

**ma_opus-4-5+sonnet-4-5:** Avg confidence: 0.48 | High-confidence accuracy: 0% (0 trades) | Low-confidence accuracy: 0% (3 trades)

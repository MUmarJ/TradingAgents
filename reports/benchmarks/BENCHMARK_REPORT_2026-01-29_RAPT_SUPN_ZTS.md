# TradingAgents Benchmark Report (Interim)
**Run ID:** bt_20260129_133950
**Date:** 2026-01-29
**Period:** 2025-01-28 to 2026-01-28
**Tickers:** RAPT, SUPN, ZTS, SNOW, AMBA, ET (6 tickers)
**Dates:** 12 monthly snapshots
**Analyses:** 42/216 completed (19.4% -- paused due to API quota)
**Models:** Deep: gpt-5.2-2025-12-11, Quick: gpt-5.1-codex-mini

> **Note:** This is an interim report. Backtest was paused at task 42/216 due to OpenAI API quota exhaustion.
> Resume with: `python -m cli.evaluate --resume bt_20260129_133950`
> A second run with GPT-4o models is also checkpointed (0/216): `python -m cli.evaluate --resume bt_20260129_163016`

## Executive Summary

| Metric | multi_agent | single_deep | single_quick |
|--------|--------|--------|--------|
| Overall accuracy | 21.4% | **35.7%** | 7.1% |
| Total P&L (post-cost) | $774.47 | **$2,176.07** | $69.81 |
| Max drawdown | **$0.00** | $15.00 | $15.00 |
| Avg confidence | 0.51 | 0.39 | 0.63 |
| BUY % | 0% | 0% | 0% |
| SELL % | 7% | 43% | 14% |
| HOLD % | 93% | 57% | 86% |
| Analyses | 14 | 14 | 14 |

## Conclusion

- **Most accurate strategy:** single_deep (35.7%)
- **Highest P&L strategy:** single_deep ($2,176.07)
- single_deep matched or exceeded multi-agent accuracy, suggesting the multi-agent architecture may not justify its additional cost.

## Results by Month

| Month | multi_agent | single_deep | single_quick |
|-------|--------|--------|--------|
| 2025-01 | 1/2 (50%) | 0/2 (0%) | 0/2 (0%) |
| 2025-02 | 2/2 (100%) | 2/2 (100%) | 1/2 (50%) |
| 2025-03 | 0/1 (0%) | 1/1 (100%) | 0/1 (0%) |
| 2025-04 | 0/1 (0%) | 1/1 (100%) | 0/1 (0%) |
| 2025-05 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |
| 2025-06 | 0/1 (0%) | 1/1 (100%) | 0/1 (0%) |
| 2025-07 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |
| 2025-08 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |
| 2025-09 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |
| 2025-10 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |
| 2025-11 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |
| 2025-12 | 0/1 (0%) | 0/1 (0%) | 0/1 (0%) |

## Results by Ticker

| Ticker | multi_agent Acc | multi_agent P&L | single_deep Acc | single_deep P&L | single_quick Acc | single_quick P&L |
|--------|--------|---------|--------|---------|--------|---------|
| RAPT | 17% | $774 | 33% | $2,091 | 0% | $-15 |
| SUPN | 50% | $0 | 50% | $85 | 50% | $85 |
| ZTS | 0% | $0 | 0% | $0 | 0% | $0 |
| SNOW | 0% | $0 | 0% | $0 | 0% | $0 |
| AMBA | 0% | $0 | 0% | $0 | 0% | $0 |
| ET | 0% | $0 | 0% | $0 | 0% | $0 |

## Decision Distribution

**multi_agent:** BUY 0% | SELL 7% | HOLD 93% (n=14)

**single_deep:** BUY 0% | SELL 43% | HOLD 57% (n=14)

**single_quick:** BUY 0% | SELL 14% | HOLD 86% (n=14)

## Confidence Analysis

**multi_agent:** Avg confidence: 0.51 | High-confidence accuracy: 0% (0 trades) | Low-confidence accuracy: 21% (14 trades) | Parseable: 14/14 (100%)

**single_deep:** Avg confidence: 0.39 | High-confidence accuracy: 0% (0 trades) | Low-confidence accuracy: 36% (14 trades) | Parseable: 14/14 (100%)

**single_quick:** Avg confidence: 0.63 | High-confidence accuracy: 7% (14 trades) | Low-confidence accuracy: 0% (0 trades) | Parseable: 14/14 (100%)
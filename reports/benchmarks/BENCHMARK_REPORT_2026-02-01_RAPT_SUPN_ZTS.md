# TradingAgents Benchmark Report
**Run ID:** bt_20260129_173611
**Date:** 2026-02-01
**Period:** 2025-01-28 to 2026-01-28
**Tickers:** RAPT, SUPN, ZTS, SNOW, AMBA, ET (6 tickers)
**Dates:** 12 monthly snapshots
**Analyses:** 503 completed

## Executive Summary

| Metric | ma_5.2+5.1-codex-mini | single_5.2 | single_5.1-codex-mini | ma_5.1-codex-mini | ma_5.2 | ma_4o | single_4o |
|--------|--------|--------|--------|--------|--------|--------|--------|
| Overall accuracy | 38.0% | 40.3% | **45.8%** | 33.3% | 40.3% | 43.1% | 40.3% |
| Total P&L (post-cost) | $26.32 | $519.09 | **$1,173.32** | $-389.58 | $0.00 | $-408.82 | $-759.35 |
| Max drawdown | $142.47 | $624.83 | $629.64 | $389.58 | **$0.00** | $939.10 | $1,367.10 |
| Avg confidence | 0.60 | 0.64 | 0.37 | 0.52 | 0.59 | 0.52 | 0.53 |
| BUY % | 0% | 0% | 3% | 3% | 0% | 0% | 1% |
| SELL % | 4% | 12% | 26% | 10% | 0% | 6% | 8% |
| HOLD % | 96% | 88% | 71% | 88% | 100% | 94% | 90% |
| Analyses | 71 | 72 | 72 | 72 | 72 | 72 | 72 |

## Conclusion

- **Most accurate strategy:** single_5.1-codex-mini (45.8%)
- **Highest P&L strategy:** single_5.1-codex-mini ($1,173.32)
- ma_5.2+5.1-codex-mini matched or exceeded multi-agent accuracy, suggesting the multi-agent architecture may not justify its additional cost.

## Results by Month

| Month | ma_5.2+5.1-codex-mini | single_5.2 | single_5.1-codex-mini | ma_5.1-codex-mini | ma_5.2 | ma_4o | single_4o |
|-------|--------|--------|--------|--------|--------|--------|--------|
| 2025-01 | 4/6 (67%) | 2/6 (33%) | 2/6 (33%) | 2/6 (33%) | 3/6 (50%) | 3/6 (50%) | 3/6 (50%) |
| 2025-02 | 1/6 (17%) | 1/6 (17%) | 3/6 (50%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) |
| 2025-03 | 2/6 (33%) | 1/6 (17%) | 2/6 (33%) | 2/6 (33%) | 2/6 (33%) | 2/6 (33%) | 1/6 (17%) |
| 2025-04 | 4/6 (67%) | 4/6 (67%) | 4/6 (67%) | 3/6 (50%) | 4/6 (67%) | 4/6 (67%) | 4/6 (67%) |
| 2025-05 | 4/6 (67%) | 3/6 (50%) | 4/6 (67%) | 3/6 (50%) | 4/6 (67%) | 4/6 (67%) | 3/6 (50%) |
| 2025-06 | 1/6 (17%) | 2/6 (33%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) |
| 2025-07 | 0/6 (0%) | 0/6 (0%) | 1/6 (17%) | 1/6 (17%) | 0/6 (0%) | 0/6 (0%) | 1/6 (17%) |
| 2025-08 | 0/5 (0%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) |
| 2025-09 | 3/6 (50%) | 3/6 (50%) | 2/6 (33%) | 3/6 (50%) | 3/6 (50%) | 3/6 (50%) | 3/6 (50%) |
| 2025-10 | 3/6 (50%) | 4/6 (67%) | 4/6 (67%) | 1/6 (17%) | 4/6 (67%) | 4/6 (67%) | 4/6 (67%) |
| 2025-11 | 2/6 (33%) | 4/6 (67%) | 5/6 (83%) | 3/6 (50%) | 3/6 (50%) | 4/6 (67%) | 3/6 (50%) |
| 2025-12 | 3/6 (50%) | 4/6 (67%) | 4/6 (67%) | 3/6 (50%) | 3/6 (50%) | 4/6 (67%) | 4/6 (67%) |

## Results by Ticker

| Ticker | ma_5.2+5.1-codex-mini Acc | ma_5.2+5.1-codex-mini P&L | single_5.2 Acc | single_5.2 P&L | single_5.1-codex-mini Acc | single_5.1-codex-mini P&L | ma_5.1-codex-mini Acc | ma_5.1-codex-mini P&L | ma_5.2 Acc | ma_5.2 P&L | ma_4o Acc | ma_4o P&L | single_4o Acc | single_4o P&L |
|--------|--------|---------|--------|---------|--------|---------|--------|---------|--------|---------|--------|---------|--------|---------|
| RAPT | 8% | $0 | 8% | $808 | 17% | $494 | 8% | $257 | 8% | $0 | 8% | $-614 | 8% | $-611 |
| SUPN | 50% | $0 | 50% | $85 | 75% | $679 | 50% | $0 | 50% | $0 | 50% | $0 | 50% | $0 |
| ZTS | 58% | $0 | 58% | $-124 | 50% | $-182 | 50% | $-256 | 58% | $0 | 58% | $0 | 58% | $0 |
| SNOW | 8% | $-142 | 33% | $106 | 33% | $-367 | 17% | $-334 | 25% | $0 | 33% | $106 | 42% | $681 |
| AMBA | 42% | $169 | 25% | $-355 | 33% | $445 | 25% | $-21 | 33% | $0 | 42% | $99 | 25% | $-739 |
| ET | 64% | $0 | 67% | $0 | 67% | $105 | 50% | $-36 | 67% | $0 | 67% | $0 | 58% | $-90 |

## Decision Distribution

**ma_5.2+5.1-codex-mini:** BUY 0% | SELL 4% | HOLD 96% (n=71)

**single_5.2:** BUY 0% | SELL 12% | HOLD 88% (n=72)

**single_5.1-codex-mini:** BUY 3% | SELL 26% | HOLD 71% (n=72)

**ma_5.1-codex-mini:** BUY 3% | SELL 10% | HOLD 88% (n=72)

**ma_5.2:** BUY 0% | SELL 0% | HOLD 100% (n=72)

**ma_4o:** BUY 0% | SELL 6% | HOLD 94% (n=72)

**single_4o:** BUY 1% | SELL 8% | HOLD 90% (n=72)

## Confidence Analysis

**ma_5.2+5.1-codex-mini:** Avg confidence: 0.60 | High-confidence accuracy: 30% (43 trades) | Low-confidence accuracy: 50% (28 trades) | Parseable: 71/71 (100%)

**single_5.2:** Avg confidence: 0.64 | High-confidence accuracy: 41% (70 trades) | Low-confidence accuracy: 0% (2 trades) | Parseable: 72/72 (100%)

**single_5.1-codex-mini:** Avg confidence: 0.37 | High-confidence accuracy: 100% (1 trades) | Low-confidence accuracy: 45% (69 trades) | Parseable: 70/72 (97%)

**ma_5.1-codex-mini:** Avg confidence: 0.52 | High-confidence accuracy: 0% (4 trades) | Low-confidence accuracy: 35% (68 trades) | Parseable: 72/72 (100%)

**ma_5.2:** Avg confidence: 0.59 | High-confidence accuracy: 50% (36 trades) | Low-confidence accuracy: 31% (36 trades) | Parseable: 72/72 (100%)

**ma_4o:** Avg confidence: 0.52 | High-confidence accuracy: 33% (9 trades) | Low-confidence accuracy: 44% (63 trades) | Parseable: 72/72 (100%)

**single_4o:** Avg confidence: 0.53 | High-confidence accuracy: 33% (33 trades) | Low-confidence accuracy: 46% (39 trades) | Parseable: 72/72 (100%)
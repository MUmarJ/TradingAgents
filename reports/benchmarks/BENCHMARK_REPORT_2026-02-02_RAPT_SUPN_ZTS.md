# TradingAgents Benchmark Report

**Run ID:** bt_20260129_173611
**Date:** 2026-02-02
**Period:** 2025-01-28 to 2026-01-28 (12 months)
**Tickers:** RAPT, SUPN, ZTS, SNOW, AMBA, ET (6 tickers)
**Monthly Snapshots:** 12 (last trading day of each month)
**Strategies Tested:** 7 (4 multi-agent, 3 single-agent)
**Total Analyses:** 504 completed, 0 failed

---

## Configuration

| Setting | Value |
|---------|-------|
| LLM Provider | OpenAI |
| Memory (ChromaDB) | Enabled |
| ACE Framework | Disabled |
| Max Debate Rounds | 1 |
| Max Risk Discussion Rounds | 1 |
| News Lookback | 90 days per analysis window |
| Articles per Month | 50 |

### Data Sources

| Category | Primary Vendor | Fallback |
|----------|---------------|----------|
| Stock Prices (OHLCV) | Polygon.io | Alpha Vantage, yfinance |
| Technical Indicators | Polygon.io (SMA/EMA/RSI/MACD) | yfinance for unsupported |
| Fundamentals | Alpha Vantage | yfinance |
| Balance Sheet | Alpha Vantage | yfinance |
| Cash Flow | Alpha Vantage | yfinance |
| Income Statement | Alpha Vantage | yfinance |
| News | Polygon.io + Alpha Vantage (dual-source, deduplicated) | Google, local |
| Social Sentiment | Stocktwits (primary) | Finnhub, Reddit PRAW |

- **Polygon.io cache:** 571 cached data files (stock prices, indicators, news)
- **Social sentiment cache:** 30 cached files (Stocktwits messages)
- **Analyst reports generated:** 77 per report type (market, sentiment, news, fundamentals) across 6 tickers x ~13 months
- **Report caching:** Multi-agent analyst reports (market, sentiment, news, fundamentals) are generated once per ticker/date, then shared across all multi-agent strategy variants

### Model Configurations Tested

| Strategy | Type | Deep Think Model | Quick Think Model |
|----------|------|-----------------|-------------------|
| ma_5.2+5.1-codex-mini | Multi-agent (12 agents) | gpt-5.2-2025-12-11 | gpt-5.1-codex-mini |
| ma_5.1-codex-mini | Multi-agent (12 agents) | gpt-5.1-codex-mini | gpt-5.1-codex-mini |
| ma_5.2 | Multi-agent (12 agents) | gpt-5.2-2025-12-11 | gpt-5.2-2025-12-11 |
| ma_4o | Multi-agent (12 agents) | gpt-4o | gpt-4o |
| single_5.1-codex-mini | Single-agent (1 LLM call) | gpt-5.1-codex-mini | — |
| single_5.2 | Single-agent (1 LLM call) | gpt-5.2-2025-12-11 | — |
| single_4o | Single-agent (1 LLM call) | gpt-4o | — |

**Multi-agent pipeline:** 4 Analysts (Market, Social, News, Fundamentals) → 2 Researchers (Bull, Bear) → 1 Trader → 2 Risk Managers, with bull/bear debate and risk discussion rounds.

**Single-agent baseline:** One LLM call with all raw data (market, indicators, fundamentals, balance sheet, cash flow, income, news, global news, sentiment) passed directly in context.

---

## Executive Summary

| Metric | single_5.1-codex-mini | single_5.2 | ma_5.2+5.1-codex-mini | ma_5.2 | ma_5.1-codex-mini | ma_4o | single_4o |
|--------|--------|--------|--------|--------|--------|--------|--------|
| **Overall accuracy** | **45.8%** | 40.3% | 38.9% | 40.3% | 33.3% | 43.1% | 40.3% |
| **Total P&L (post-cost)** | **+$1,173.32** | +$519.09 | +$26.32 | $0.00 | -$389.58 | -$408.82 | -$759.35 |
| Max drawdown | $629.64 | $624.83 | $142.47 | **$0.00** | $389.58 | $939.10 | $1,367.10 |
| Avg confidence | 0.37 | 0.64 | 0.60 | 0.59 | 0.52 | 0.52 | 0.53 |
| Active trades | **21 (29%)** | 9 (12%) | 3 (4%) | 0 (0%) | 9 (12%) | 4 (6%) | 7 (10%) |
| Win rate (on trades) | **57%** | 44% | 33% | N/A | 11% | 50% | 29% |
| Avg win | +$220.84 | +$359.40 | +$168.79 | — | +$272.04 | +$265.14 | +$458.83 |
| Avg loss | -$164.09 | -$183.70 | -$71.23 | — | -$82.70 | -$469.55 | -$335.40 |
| BUY % | 3% | 0% | 0% | 0% | 3% | 0% | 1% |
| SELL % | 26% | 12% | 4% | 0% | 10% | 6% | 8% |
| HOLD % | 71% | 88% | 96% | 100% | 88% | 94% | 90% |
| Analyses | 72 | 72 | 72 | 72 | 72 | 72 | 72 |

### Single-Agent vs Multi-Agent (Aggregated)

| Category | Accuracy | P&L | Active Trade Rate |
|----------|----------|-----|-------------------|
| **Single-agent (3 strategies, 216 tasks)** | **42% (91/216)** | **+$933.06** | 17% (37 trades) |
| Multi-agent (4 strategies, 288 tasks) | 39% (112/288) | -$772.08 | 6% (16 trades) |

---

## Ticker Difficulty Analysis

Tickers ranked from hardest to easiest based on average accuracy across all 7 strategies:

| Rank | Ticker | Avg Accuracy | Aggregate P&L | Best Strategy | Worst Strategy | Notes |
|------|--------|-------------|---------------|---------------|----------------|-------|
| 1 (hardest) | **RAPT** | **10%** | +$334 | single_5.2 (+$808, 8%) | ma_4o (-$614, 8%) | Micro-cap biotech ($9-$12 range). Extreme volatility, very low news coverage. Most strategies scored only 1/12 correct. Only profits came from rare correct SELL calls. |
| 2 | **SNOW** | **27%** | +$49 | single_4o (+$681, 42%) | single_5.1-codex-mini (-$367, 33%) | High-growth tech. Inconsistent performance — the best overall strategy (single_5.1-codex-mini) actually lost money here. Market dynamics too unpredictable for any consistent edge. |
| 3 | **AMBA** | **32%** | -$401 | single_5.1-codex-mini (+$445, 33%) | single_4o (-$739, 25%) | Semiconductor. Wide dispersion between strategies — winner made +$445, loser lost -$739. GPT-4o particularly poor on this ticker. |
| 4 | **SUPN** | **54%** | +$763 | single_5.1-codex-mini (+$679, 75%) | ma_5.2+5.1-codex-mini ($0, 50%) | Specialty pharma with clearer directional signals. Best ticker for the winning strategy (75% accuracy). Multi-agent strategies defaulted to HOLD, missing profitable opportunities. |
| 5 | **ZTS** | **56%** | -$562 | ma_5.2+5.1-codex-mini ($0, 58%) | ma_5.1-codex-mini (-$256, 50%) | Large-cap animal health. High accuracy but negative P&L — strategies predicted direction correctly but lost on the trades they did make. Safe for HOLD strategies. |
| 6 (easiest) | **ET** | **63%** | -$22 | single_5.1-codex-mini (+$105, 67%) | single_4o (-$90, 58%) | Energy midstream/MLP. Most predictable — stable price action, high dividend yield making HOLD often correct. Near break-even aggregate P&L despite high accuracy because few trades were made. |

### Key Observations on Ticker Behavior

- **Accuracy does not equal profitability:** ZTS had 56% average accuracy but -$562 aggregate P&L. ET had 63% accuracy but -$22 P&L. High accuracy on HOLD-dominated strategies doesn't generate returns.
- **RAPT's 10% accuracy** across 84 tasks means the market moved against virtually every prediction. This is a biotech micro-cap with binary event risk (clinical trials, FDA decisions) that no amount of financial data can predict.
- **SUPN was the profit engine** — +$763 aggregate P&L, driven primarily by single_5.1-codex-mini's 75% accuracy and profitable SELL calls.

---

## Active Trading Analysis

### Win Rate When Actually Trading (non-HOLD Only)

| Strategy | Total Trades | Wins | Losses | Win Rate | Avg Win P&L | Avg Loss P&L | Win/Loss Ratio |
|----------|-------------|------|--------|----------|-------------|--------------|----------------|
| **single_5.1-codex-mini** | **21** | **12** | **9** | **57%** | +$220.84 | -$164.09 | **1.35:1** |
| single_5.2 | 9 | 4 | 5 | 44% | +$359.40 | -$183.70 | 1.96:1 |
| ma_4o | 4 | 2 | 2 | 50% | +$265.14 | -$469.55 | 0.56:1 |
| ma_5.2+5.1-codex-mini | 3 | 1 | 2 | 33% | +$168.79 | -$71.23 | 2.37:1 |
| ma_5.1-codex-mini | 9 | 1 | 8 | **11%** | +$272.04 | -$82.70 | 3.29:1 |
| single_4o | 7 | 2 | 5 | 29% | +$458.83 | -$335.40 | 1.37:1 |
| ma_5.2 | **0** | — | — | N/A | — | — | — |

### HOLD-Only Accuracy (Was Doing Nothing Correct?)

| Strategy | Correct HOLDs | HOLD Accuracy |
|----------|--------------|---------------|
| ma_4o | 29/68 | 43% |
| single_4o | 27/65 | 42% |
| single_5.1-codex-mini | 21/51 | 41% |
| ma_5.2 | 29/72 | 40% |
| single_5.2 | 25/63 | 40% |
| ma_5.2+5.1-codex-mini | 27/69 | 39% |
| ma_5.1-codex-mini | 23/63 | 37% |

HOLD accuracy is ~40% across all strategies, meaning the market moved meaningfully ~60% of the time. Strategies with very high HOLD rates (ma_5.2 at 100%, ma_5.2+5.1-codex-mini at 96%) are systematically leaving money on the table.

---

## Results by Month

| Month | single_5.1-codex-mini | single_5.2 | ma_5.2+5.1-codex-mini | ma_5.2 | ma_5.1-codex-mini | ma_4o | single_4o |
|-------|--------|--------|--------|--------|--------|--------|--------|
| 2025-01 | 2/6 (33%) | 2/6 (33%) | 4/6 (67%) | 3/6 (50%) | 2/6 (33%) | 3/6 (50%) | 3/6 (50%) |
| 2025-02 | 3/6 (50%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) |
| 2025-03 | 2/6 (33%) | 1/6 (17%) | 2/6 (33%) | 2/6 (33%) | 2/6 (33%) | 2/6 (33%) | 1/6 (17%) |
| 2025-04 | 4/6 (67%) | 4/6 (67%) | 4/6 (67%) | 4/6 (67%) | 3/6 (50%) | 4/6 (67%) | 4/6 (67%) |
| 2025-05 | 4/6 (67%) | 3/6 (50%) | 4/6 (67%) | 4/6 (67%) | 3/6 (50%) | 4/6 (67%) | 3/6 (50%) |
| 2025-06 | 1/6 (17%) | 2/6 (33%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) |
| 2025-07 | 1/6 (17%) | 0/6 (0%) | 0/6 (0%) | 0/6 (0%) | 1/6 (17%) | 0/6 (0%) | 1/6 (17%) |
| 2025-08 | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) | 1/6 (17%) |
| 2025-09 | 2/6 (33%) | 3/6 (50%) | 3/6 (50%) | 3/6 (50%) | 3/6 (50%) | 3/6 (50%) | 3/6 (50%) |
| 2025-10 | 4/6 (67%) | 4/6 (67%) | 3/6 (50%) | 4/6 (67%) | 1/6 (17%) | 4/6 (67%) | 4/6 (67%) |
| 2025-11 | 5/6 (83%) | 4/6 (67%) | 2/6 (33%) | 3/6 (50%) | 3/6 (50%) | 4/6 (67%) | 3/6 (50%) |
| 2025-12 | 4/6 (67%) | 4/6 (67%) | 3/6 (50%) | 3/6 (50%) | 3/6 (50%) | 4/6 (67%) | 4/6 (67%) |

### Cumulative P&L: single_5.1-codex-mini (Best Strategy)

| Month | Monthly P&L | Cumulative P&L | Accuracy |
|-------|------------|----------------|----------|
| 2025-01 | -$15.00 | -$15.00 | 2/6 (33%) |
| 2025-02 | +$941.67 | +$926.67 | 3/6 (50%) |
| 2025-03 | +$329.16 | +$1,255.84 | 2/6 (33%) |
| 2025-04 | +$55.07 | +$1,310.91 | 4/6 (67%) |
| 2025-05 | $0.00 | +$1,310.91 | 4/6 (67%) |
| 2025-06 | $0.00 | +$1,310.91 | 1/6 (17%) |
| 2025-07 | -$22.25 | +$1,288.66 | 1/6 (17%) |
| 2025-08 | -$227.02 | +$1,061.64 | 1/6 (17%) |
| 2025-09 | +$26.01 | +$1,087.65 | 2/6 (33%) |
| 2025-10 | $0.00 | +$1,087.65 | 4/6 (67%) |
| 2025-11 | +$604.69 | +$1,692.34 | 5/6 (83%) |
| 2025-12 | -$519.02 | +$1,173.32 | 4/6 (67%) |

Most profits came from Q1 2025 (+$1,256 in first 3 months) with a second surge in Nov 2025 (+$605). Mid-year (Jun-Aug) was a drawdown period across all strategies.

---

## Results by Ticker

| Ticker | single_5.1-codex-mini | single_5.2 | ma_5.2+5.1-codex-mini | ma_5.2 | ma_5.1-codex-mini | ma_4o | single_4o |
|--------|--------|--------|--------|--------|--------|--------|--------|
| RAPT | 17% / +$494 | 8% / +$808 | 8% / $0 | 8% / $0 | 8% / +$257 | 8% / -$614 | 8% / -$611 |
| SUPN | **75% / +$679** | 50% / +$85 | 50% / $0 | 50% / $0 | 50% / $0 | 50% / $0 | 50% / $0 |
| ZTS | 50% / -$182 | 58% / -$124 | 58% / $0 | 58% / $0 | 50% / -$256 | 58% / $0 | 58% / $0 |
| SNOW | 33% / -$367 | 33% / +$106 | 8% / -$142 | 25% / $0 | 17% / -$334 | 33% / +$106 | **42% / +$681** |
| AMBA | 33% / +$445 | 25% / -$355 | **42% / +$169** | 33% / $0 | 25% / -$21 | 42% / +$99 | 25% / -$739 |
| ET | **67% / +$105** | 67% / $0 | 67% / $0 | 67% / $0 | 50% / -$36 | 67% / $0 | 58% / -$90 |

---

## Decision Distribution

| Strategy | BUY | SELL | HOLD | Active Rate |
|----------|-----|------|------|-------------|
| **single_5.1-codex-mini** | 3% (2) | **26% (19)** | 71% (51) | **29%** |
| single_5.2 | 0% (0) | 12% (9) | 88% (63) | 12% |
| ma_5.1-codex-mini | 3% (2) | 10% (7) | 88% (63) | 12% |
| single_4o | 1% (1) | 8% (6) | 90% (65) | 10% |
| ma_4o | 0% (0) | 6% (4) | 94% (68) | 6% |
| ma_5.2+5.1-codex-mini | 0% (0) | 4% (3) | 96% (69) | 4% |
| ma_5.2 | 0% (0) | **0% (0)** | **100% (72)** | **0%** |

---

## Confidence Analysis

| Strategy | Avg Confidence | High-Conf (>=0.6) Accuracy | Low-Conf (<0.6) Accuracy | Parseable |
|----------|---------------|---------------------------|--------------------------|-----------|
| single_5.2 | 0.64 | 41% (70 trades) | 0% (2 trades) | 72/72 (100%) |
| ma_5.2+5.1-codex-mini | 0.60 | 32% (44 trades) | 50% (28 trades) | 72/72 (100%) |
| ma_5.2 | 0.59 | 50% (36 trades) | 31% (36 trades) | 72/72 (100%) |
| single_4o | 0.53 | 33% (33 trades) | 46% (39 trades) | 72/72 (100%) |
| ma_4o | 0.52 | 33% (9 trades) | 44% (63 trades) | 72/72 (100%) |
| ma_5.1-codex-mini | 0.52 | 0% (4 trades) | 35% (68 trades) | 72/72 (100%) |
| **single_5.1-codex-mini** | **0.37** | 100% (1 trade) | **45% (69 trades)** | 70/72 (97%) |

**Confidence calibration paradox:** `single_5.1-codex-mini` has the *lowest* average confidence (0.37) but the *highest* accuracy (46%). It is under-confident but correct more often. Conversely, `single_5.2` has the highest confidence (0.64) with lower accuracy (40%). This suggests `gpt-5.1-codex-mini` is better calibrated — it knows what it doesn't know — while `gpt-5.2` is overconfident.

---

## Data Sources Detail

### Stock Price Data (Polygon.io)
- **Data type:** Daily OHLCV (Open, High, Low, Close, Volume)
- **History window:** 90 days prior to each analysis date
- **Indicators computed:** SMA (20/50/200-day), EMA (12/26-day), RSI (14-day), MACD (12/26/9)
- **Coverage:** All 6 tickers fully covered for the full 12-month test period
- **Cache:** 571 Polygon data files cached locally to avoid redundant API calls

### Fundamental Data (Alpha Vantage)
- **Data types:** Company overview, balance sheet, cash flow statement, income statement
- **Coverage:** Quarterly financials for all 6 tickers
- **Report size:** Avg 7.8 KB per fundamentals report (detailed financial metrics)

### News Data (Polygon.io + Alpha Vantage, dual-source)
- **Sources:** Polygon.io news API + Alpha Vantage news API with cross-source deduplication
- **Lookback:** 90 days of news per analysis window
- **Article limit:** 50 articles per analysis
- **Deduplication:** Jaccard similarity (0.7 threshold) on article titles to remove cross-source duplicates
- **Company name fallback:** Enabled — retries with company name if ticker search yields few results (useful for small-cap tickers like RAPT)
- **Report size:** Avg 6.8 KB per news report, avg 6.5 KB per market report

### Social Sentiment Data (Stocktwits)
- **Primary source:** Stocktwits (free, no API key required)
- **Data type:** User messages with bullish/bearish/neutral sentiment labels
- **Cache:** 30 sentiment cache files across all ticker/date combinations
- **Report size:** Avg 2.0 KB per sentiment report
- **Note:** ApeWisdom was disabled for this run (unreliable data quality). Finnhub and Reddit PRAW available as optional fallback sources.

### Analyst Reports (LLM-generated, cached per ticker/date)
- **Market report:** Technical analysis, price levels, trend assessment (avg 6.5 KB)
- **Sentiment report:** Social media sentiment summary (avg 2.0 KB)
- **News report:** News digest with macro/micro analysis (avg 6.8 KB)
- **Fundamentals report:** Valuation, earnings quality, balance sheet health (avg 7.8 KB)
- **Final trade decision:** Multi-agent consensus decision (avg 3.1 KB)
- **Total:** 77 reports per type, 385+ reports total across all categories
- **Caching:** Reports generated by the first multi-agent strategy per ticker/date, then reused by all subsequent multi-agent variants (only debate/trader/risk layers re-run with different models)

---

## Conclusions

### 1. Single-Agent Decisively Outperforms Multi-Agent

Across 504 analyses, single-agent strategies generated **+$933 aggregate P&L at 42% accuracy**, while multi-agent strategies lost **-$772 at 39% accuracy**. This is not marginal — it's a reversal. The 12-agent pipeline (4 analysts, 2 researchers, 1 trader, 2 risk managers) actively destroys the alpha that individual models can generate.

### 2. The Multi-Agent Debate Process Kills Conviction

The core problem is systematic: the bull/bear debate followed by risk manager review collapses almost every actionable signal into HOLD. Evidence:
- `ma_5.2` made **zero trades** across 72 tasks (100% HOLD)
- `ma_5.2+5.1-codex-mini` made only 3 trades (96% HOLD)
- Multi-agent active trade rate: **6%** vs single-agent **17%**
- When multi-agent strategies *did* trade, they performed poorly (ma_5.1-codex-mini: 11% win rate)

The consensus mechanism is a bug, not a feature. It doesn't filter bad trades — it filters *all* trades.

### 3. GPT-5.1-codex-mini Is the Best Model for Trading Decisions

`gpt-5.1-codex-mini` as a single agent achieved:
- **Highest accuracy:** 45.8% (33/72 correct)
- **Highest P&L:** +$1,173.32
- **Most active trading:** 21 trades (29% active rate)
- **Best win rate:** 57% on active trades
- **Favorable risk/reward:** 1.35:1 win/loss ratio ($221 avg win vs $164 avg loss)
- **Best calibration:** Lowest confidence (0.37) but highest accuracy — knows what it doesn't know

### 4. GPT-4o Is the Weakest Model

GPT-4o produced negative P&L in both configurations:
- `single_4o`: -$759, 40% accuracy, 29% win rate on trades
- `ma_4o`: -$409, 43% accuracy, 50% win rate but massive avg losses ($470)

GPT-4o's problem is not accuracy (40-43% is competitive) but *trade quality* — when it acts, its losses are disproportionately large compared to wins.

### 5. Model Pairing Doesn't Help Multi-Agent

The mixed-model strategy (`ma_5.2+5.1-codex-mini` with different deep/quick models) performed no better than same-model variants. Its +$26 P&L is essentially flat. The multi-agent architecture bottleneck is structural, not model-dependent.

### 6. Ticker Type Matters More Than Strategy Choice

- **Predictable tickers** (ET at 63%, ZTS at 56%, SUPN at 54%): Stable businesses where HOLD is often correct. Most strategies perform similarly.
- **Unpredictable tickers** (RAPT at 10%, SNOW at 27%): High-volatility names where models consistently fail. RAPT (biotech micro-cap) is essentially random — 10% accuracy is worse than chance.
- **The winning strategy's edge comes from mid-difficulty tickers** (AMBA, SUPN) where active trading can exploit directional signals that exist but aren't obvious.

### 7. Actionable Recommendations

1. **Use single-agent with gpt-5.1-codex-mini** as the production strategy — it's simpler, cheaper (1 LLM call vs ~8-12), and more profitable.
2. **If using multi-agent, reduce the debate/risk layers** — the current consensus mechanism needs fundamental redesign. Consider: removing the risk manager veto, or requiring explicit BUY/SELL signals rather than defaulting to HOLD.
3. **Filter out micro-cap biotech tickers** (like RAPT) from automated trading — the data available to LLMs cannot predict binary event outcomes.
4. **Focus on mid-cap stocks with clear fundamental stories** (like SUPN) where the model's analytical capabilities provide genuine edge.
5. **Don't trust confidence scores for position sizing** — the most confident model (gpt-5.2, 0.64) underperforms the least confident (gpt-5.1-codex-mini, 0.37).

---

## Methodology Notes

- **Outcome validation:** Each BUY/SELL decision is validated against actual market movement over the following 30-day window. A BUY is correct if price rose; a SELL is correct if price fell. HOLD is correct if price moved less than 1%.
- **P&L calculation:** Based on $10,000 position size per trade, with 0.1% spread + 0.05% slippage transaction costs applied to all non-HOLD trades.
- **Signal extraction:** Decisions extracted from LLM text using regex pattern matching on "FINAL TRANSACTION PROPOSAL" lines, with fallback LLM extraction for ambiguous outputs.
- **Hard overrides:** Quantitative guardrails (RSI, SMA crossovers) can override LLM decisions when technical signals are extreme, though this was rarely triggered in practice.
- **Reproducibility:** All raw data cached in `results/datasets/`, analyst reports in `results/{TICKER}/{DATE}/reports/`, checkpoint with full task-level results in `results/evaluations/backtest_bt_20260129_173611/checkpoint.json`.

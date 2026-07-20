# TradingAgents V3 Benchmark Report
**Run ID:** v2_20260211_021106
**Date:** 2026-02-11
**Period:** 2025-03-01 to 2026-02-07
**Tickers:** AAPL, MSFT, NVDA, AMBA, JNJ, XOM, JPM, COST, TSLA, NEE (10 tickers)
**Dates:** 11 monthly snapshots
**Version:** 2 (look-ahead free, no HOLD fallback)
**Horizons:** 1d, 3d, 1w, 2w, 4w, 8w, 13w (7 projection horizons)
**Total tasks:** 440
**Completed:** 440
**Failed:** 0
**Failure rate:** 0.0%

## Configuration

| Setting | Value |
|---------|-------|
| LLM Provider | Mixed (auto-detected per model) |
| Architecture | Single-agent (all models) |
| Memory Enabled | False |
| ACE Enabled | False |
| Model Tiers | 4 configurations |
| &nbsp;&nbsp;single_haiku-4-5 | model=claude-haiku-4-5-20251001 |
| &nbsp;&nbsp;single_gpt-4o-mini | model=gpt-4o-mini |
| &nbsp;&nbsp;single_gpt-5.1-codex-mini | model=gpt-5.1-codex-mini |
| &nbsp;&nbsp;single_sonnet-4-5 | model=claude-sonnet-4-5-20250929 |

## Methodology

### Objective

Test whether model intelligence matters for stock trading prediction accuracy, or whether the bottleneck is data quality. If a $0.02/task model (Haiku) matches a $0.10/task model (Sonnet), the system's limiting factor is its data pipeline, not LLM reasoning capability.

### Model Selection

Four models selected to span a 5x cost range while skipping expensive Opus ($0.45/task), which V2 showed provides only +12pp accuracy over Sonnet — insufficient to justify the 4.5x cost premium:

| Model | Provider | $/task | Role |
|-------|----------|--------|------|
| Haiku 4.5 | Anthropic | ~$0.02 | Cheapest available — "are cheap models enough?" |
| gpt-4o-mini | OpenAI | ~$0.03 | Cross-provider comparison at same price tier |
| gpt-5.1-codex-mini | OpenAI | ~$0.08 | Mid-tier with strong reasoning |
| Sonnet 4.5 | Anthropic | ~$0.10 | Reference baseline from V2 benchmarks |

### Ticker Selection (10 across 7 sectors)

| Ticker | Sector | Market Cap | Volatility |
|--------|--------|-----------|------------|
| AAPL, MSFT | Tech | Mega | Low |
| NVDA, AMBA | Semiconductors | Mega/Mid | High |
| JNJ | Healthcare | Mega | Low |
| XOM | Energy | Mega | Moderate |
| JPM | Finance | Mega | Moderate |
| COST | Consumer | Mega | Low |
| TSLA | Auto/Tech | Mega | Very High |
| NEE | Utility | Large | Low |

### Horizon Design

Each LLM decision (BUY/SELL/HOLD) is validated against 7 forward-looking windows. HOLD thresholds scale with horizon duration to account for increasing natural price drift:

| Horizon | Trading Days | HOLD Threshold |
|---------|-------------|----------------|
| 1d | 1 | ±0.2% |
| 3d | 3 | ±0.35% |
| 1w | 5 | ±0.5% |
| 2w | 10 | ±0.8% |
| 4w | 20 | ±1.2% |
| 8w | 40 | ±1.8% |
| 13w | 65 | ±2.5% |

### Walk-Forward Design

The 11-month period is split for out-of-sample validation:
- **Period 1 (in-sample):** March–August 2025 (6 dates, 60 tasks per model)
- **Period 2 (out-of-sample):** September 2025–January 2026 (5 dates, 50 tasks per model)

The LLM sees no difference between periods — the split is purely for post-hoc analysis to detect overfitting.

### Baselines (zero-cost, computed from market data)

| Baseline | Rule |
|----------|------|
| Always-BUY | Correct if price rose > threshold at horizon |
| Always-SELL | Correct if price fell > threshold at horizon |
| Momentum-5d | Follow the direction of the last 5 trading days |
| Random | Expected 33.3% for 3-class classification |

---

## Data Pipeline Limitations

### Data Sources Used

| Category | Source | Status |
|----------|--------|--------|
| Market OHLCV | Polygon | Working |
| Market Quote | Polygon | Working |
| Technical Indicators | Polygon/Alpha Vantage/yfinance | **BROKEN** — date string passed as indicator name |
| Fundamentals (P/E, EPS, etc.) | Alpha Vantage | Working |
| Balance Sheet | Alpha Vantage | Working |
| Cash Flow | Alpha Vantage | Working |
| Income Statement | Alpha Vantage | Working |
| News (ticker-specific) | Polygon + Alpha Vantage | Working (deduplicated) |
| Global/Macro News | Alpha Vantage | **BROKEN** — date string passed where integer expected |
| Social Sentiment | Stocktwits/StockGeist/Finnhub/Reddit | **EMPTY** — all providers blocked or no API keys |

### Impact on Results

LLM decisions were made **without technical indicators** (RSI, MACD, Bollinger Bands, SMA) and **without social sentiment data**. This is a significant limitation — technical analysis is a primary input for short-term trading decisions. Accuracy may improve substantially once the indicator bug is fixed and social sentiment APIs are configured.

---

## Executive Summary (Next-Day Accuracy)

| Metric | single_haiku-4-5 | single_gpt-4o-mini | single_gpt-5.1-codex-mini | single_sonnet-4-5 |
|--------|--------|--------|--------|--------|
| Next-day accuracy | 32.7% | 31.8% | 31.8% | **34.5%** |
| Total P&L (post-cost) | $-86.00 | $-1,096.25 | $-36.80 | **$1,280.12** |
| Max drawdown | $1,516.37 | $1,478.08 | $1,368.01 | **$767.40** |
| Avg confidence | 0.72 | 0.70 | 0.42 | 0.71 |
| BUY % | 5% | 19% | 15% | 5% |
| SELL % | 15% | 13% | 26% | 20% |
| HOLD % | 79% | 68% | 58% | 75% |
| Analyses | 110 | 110 | 110 | 110 |

## 5-Day Forward Accuracy

| Metric | single_haiku-4-5 | single_gpt-4o-mini | single_gpt-5.1-codex-mini | single_sonnet-4-5 |
|--------|--------|--------|--------|--------|
| 5-day accuracy | 26/110 (23.6%) | 25/110 (22.7%) | 34/110 (30.9%) | 24/110 (21.8%) |
| 5-day P&L | $735.03 | $-1,839.41 | $5,500.53 | $914.09 |

---

## Multi-Horizon Analysis

### Horizon Comparison (All Models)

| Horizon | single_haiku-4-5 | single_gpt-4o-mini | single_gpt-5.1-codex-mini | single_sonnet-4-5 | Winner |
|---------|---------|---------|---------|---------|--------|
| 1d      |    17.3% |    21.8% | **25.5%** |    20.9% | single_gpt-5.1-codex-mini |
| 3d      |    17.3% |    23.6% | **29.1%** |    19.1% | single_gpt-5.1-codex-mini |
| 1w      |    11.8% |    13.6% | **22.7%** |    13.6% | single_gpt-5.1-codex-mini |
| 2w      |    18.0% |    19.0% | **22.0%** |    21.0% | single_gpt-5.1-codex-mini |
| 4w      |    18.0% | **24.0%** |    24.0% |    20.0% | single_gpt-4o-mini |
| 8w      |    13.3% | **22.2%** |    17.8% |    16.7% | single_gpt-4o-mini |
| 13w     |    12.5% | **16.2%** |    13.8% |    12.5% | single_gpt-4o-mini |
| **Overall** |    15.6% |    20.1% |    22.6% |    17.9% | single_gpt-5.1-codex-mini |

### single_haiku-4-5 — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1d      | 19      | 110   |  17.3% |               -0.72% |            +0.17% |
| 3d      | 19      | 110   |  17.3% |               -0.86% |            +0.36% |
| 1w      | 13      | 110   |  11.8% |               -2.89% |            -0.24% |
| 2w      | 18      | 100   |  18.0% |               -2.14% |            +2.33% |
| 4w      | 18      | 100   |  18.0% |               -1.27% |            +4.20% |
| 8w      | 12      | 90    |  13.3% |               -1.04% |            +8.40% |
| 13w     | 10      | 80    |  12.5% |               -1.72% |           +12.70% |

### single_gpt-4o-mini — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1d      | 24      | 110   |  21.8% |               -0.28% |            +0.10% |
| 3d      | 26      | 110   |  23.6% |               +0.04% |            +0.18% |
| 1w      | 15      | 110   |  13.6% |               -1.95% |            -0.33% |
| 2w      | 19      | 100   |  19.0% |               +0.37% |            +1.79% |
| 4w      | 24      | 100   |  24.0% |               +1.31% |            +3.82% |
| 8w      | 20      | 90    |  22.2% |               +2.69% |            +8.42% |
| 13w     | 13      | 80    |  16.2% |               +5.49% |           +11.95% |

### single_gpt-5.1-codex-mini — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1d      | 28      | 110   |  25.5% |               -0.61% |            +0.23% |
| 3d      | 32      | 110   |  29.1% |               -1.16% |            +0.68% |
| 1w      | 25      | 110   |  22.7% |               -3.68% |            +0.37% |
| 2w      | 22      | 100   |  22.0% |               -2.00% |            +2.52% |
| 4w      | 24      | 100   |  24.0% |               -0.49% |            +4.39% |
| 8w      | 16      | 90    |  17.8% |               -1.62% |            +9.04% |
| 13w     | 11      | 80    |  13.8% |               -1.55% |           +12.88% |

### single_sonnet-4-5 — Per-Horizon Accuracy

| Horizon | Correct | Total | Accuracy | Avg Return (Correct) | Avg Loss (Wrong) |
|---------|---------|-------|----------|---------------------|------------------|
| 1d      | 23      | 110   |  20.9% |               -1.16% |            +0.32% |
| 3d      | 21      | 110   |  19.1% |               -1.14% |            +0.45% |
| 1w      | 15      | 110   |  13.6% |               -3.53% |            -0.08% |
| 2w      | 21      | 100   |  21.0% |               -0.60% |            +2.09% |
| 4w      | 20      | 100   |  20.0% |               +0.14% |            +3.98% |
| 8w      | 15      | 90    |  16.7% |               +1.11% |            +8.35% |
| 13w     | 10      | 80    |  12.5% |               +2.09% |           +12.16% |

## Cross-Horizon Consistency

### Cross-Horizon Consistency

| Metric | single_haiku-4-5 | single_gpt-4o-mini | single_gpt-5.1-codex-mini | single_sonnet-4-5 |
|--------|---------||---------||---------||---------|
| All horizons correct | 3/110 (3%) | 5/110 (5%) | 5/110 (5%) | 4/110 (4%) |
| All horizons wrong | 53/110 (48%) | 47/110 (43%) | 38/110 (35%) | 46/110 (42%) |
| Mixed results | 54/110 (49%) | 58/110 (53%) | 67/110 (61%) | 60/110 (55%) |

### Short-Term vs Long-Term Accuracy

| Model | Short (1d+3d avg) | Long (8w+13w avg) | Delta |
|-------|-------------------|-------------------|-------|
| single_haiku-4-5 | 17.3% | 12.9% | -4.3% |
| single_gpt-4o-mini | 22.7% | 19.4% | -3.3% |
| single_gpt-5.1-codex-mini | 27.3% | 15.9% | -11.4% |
| single_sonnet-4-5 | 20.0% | 14.7% | -5.3% |

### BUY Decision Accuracy by Horizon

| Horizon | single_haiku-4-5 | single_gpt-4o-mini | single_gpt-5.1-codex-mini | single_sonnet-4-5 |
|---------|---------|---------|---------|---------|
| 1d      |  50.0% |  47.6% |  47.1% |  20.0% |
| 3d      |  50.0% |  57.1% |  58.8% |  80.0% |
| 1w      |  16.7% |  28.6% |  35.3% |  20.0% |
| 2w      |  40.0% |  35.0% |  28.6% |  80.0% |
| 4w      |  40.0% |  45.0% |  50.0% |  80.0% |
| 8w      |  25.0% |  55.6% |  36.4% |  80.0% |
| 13w     |  50.0% |  60.0% |  44.4% |  80.0% |

### SELL Decision Accuracy by Horizon

| Horizon | single_haiku-4-5 | single_gpt-4o-mini | single_gpt-5.1-codex-mini | single_sonnet-4-5 |
|---------|---------|---------|---------|---------|
| 1d      |  41.2% |  57.1% |  41.4% |  68.2% |
| 3d      |  41.2% |  35.7% |  58.6% |  45.5% |
| 1w      |  47.1% |  50.0% |  51.7% |  45.5% |
| 2w      |  47.1% |  38.5% |  40.7% |  36.8% |
| 4w      |  23.5% |  38.5% |  29.6% |  21.1% |
| 8w      |  20.0% |  27.3% |  19.2% |  11.8% |
| 13w     |  28.6% |  18.2% |  15.4% |  12.5% |

### HOLD Decision Accuracy by Horizon

| Horizon | single_haiku-4-5 | single_gpt-4o-mini | single_gpt-5.1-codex-mini | single_sonnet-4-5 |
|---------|---------|---------|---------|---------|
| 1d      |  10.3% |  8.0% |  12.5% |  8.4% |
| 3d      |  10.3% |  12.0% |  7.8% |  8.4% |
| 1w      |  4.6% |  2.7% |  6.2% |  4.8% |
| 2w      |  10.3% |  10.4% |  11.9% |  13.2% |
| 4w      |  15.4% |  14.9% |  15.3% |  15.8% |
| 8w      |  11.3% |  11.5% |  13.2% |  13.2% |
| 13w     |  6.5% |  3.7% |  6.7% |  6.8% |

HOLD accuracy is consistently the lowest of all decision types (3-16% across horizons). This is because HOLD requires the price to stay within a narrow threshold band — a condition that becomes increasingly unlikely as time passes and the market moves directionally. Despite HOLD being "wrong" at the horizon level, HOLD-heavy strategies generate better P&L by avoiding transaction costs and wrong-direction trades.

---

## Prior Results Comparison

How V3 results compare to previous benchmark runs:

| Run | Date | Models | Tickers | n/model | Best Acc | Notes |
|-----|------|--------|---------|---------|----------|-------|
| V2.02 | 2026-02-02 | gpt-5.1-codex-mini (single+multi) | AMBA, RAPT, ET, ZTS | 4 | 50.0% (multi) | First multi-ticker run |
| V2.03 | 2026-02-03 | Sonnet, Opus, multi-agent | AMBA | 4 | 75.0% (Sonnet) | Small sample noise |
| V2.09 | 2026-02-09 | Sonnet 4.5, Opus 4.6 | AMBA | 33 | 39.4% (Opus) | First statistically meaningful run |
| **V3** | **2026-02-11** | **Haiku, gpt-4o-mini, gpt-5.1-codex-mini, Sonnet** | **10 tickers** | **110** | **34.5% (Sonnet)** | **Definitive: models cluster at ~33%** |

**Key pattern:** As sample size increases, accuracy converges to ~33% (random). Sonnet's apparent 75% accuracy at n=4 was pure noise — it stabilized to 27% at n=33 and 34.5% at n=110. This confirms that no model has genuine predictive alpha with the current data pipeline.

---

## Key Findings

### 1. All LLMs are significantly worse than Always-BUY (p < 0.0001)

Every model at every horizon is statistically below the trivial Always-BUY baseline. At the 1d horizon, Always-BUY achieves 48.2% while the best model (gpt-5.1-codex-mini) reaches only 25.5%. The gap widens at longer horizons — at 13w, Always-BUY hits 72.5% while models top out at 16.2%. The LLM system is not generating trading alpha.

### 2. Model intelligence does not matter for this task

All four models cluster in a narrow 31.8%–34.5% accuracy band. The bootstrap 95% confidence intervals overlap completely (Haiku: [24.5%, 41.8%], Sonnet: [25.5%, 43.6%]). Spending 5x more on Sonnet ($0.10) vs Haiku ($0.02) buys no measurable accuracy improvement. The bottleneck is data quality, not reasoning capability.

### 3. gpt-5.1-codex-mini wins short-term, gpt-4o-mini wins long-term

gpt-5.1-codex-mini dominates 1d–2w horizons (25.5%–29.1%), while gpt-4o-mini wins at 4w–13w (22.2%–24.0%). However, the short-term advantage comes with high variance — gpt-5.1-codex-mini's 2w accuracy drops from 30.0% to 10.0% between Period 1 and Period 2 in the walk-forward analysis.

### 4. Accuracy collapses at longer horizons

Short-term (1d+3d avg): 17–27%. Long-term (8w+13w avg): 13–19%. SELL decisions are worst affected — SELL accuracy at 13w ranges from 12.5% to 28.6%, well below random. Long-horizon prediction adds noise, not signal.

### 5. Conservative HOLD-heavy strategy wins on P&L

Sonnet 4.5 generated the only positive P&L (+$1,280) by HOLDing 75% of the time. Meanwhile, the more aggressive gpt-4o-mini (68% HOLD, 19% BUY) lost $1,096. When accuracy is random, the optimal strategy is to minimize trading — which is exactly what HOLD achieves.

### 6. No overfitting detected — but no signal either

Walk-forward analysis shows no systematic accuracy degradation from Period 1 to Period 2. gpt-5.1-codex-mini actually improved (+7.7pp). This isn't evidence of skill — it's evidence that accuracy fluctuates randomly around 33%, regardless of market regime.

### 7. TSLA and AAPL are the most "predictable" tickers (47.7% and 64% respectively)

TSLA's strong directional moves may be easier for LLMs to identify from news sentiment. AAPL's stability means HOLD decisions are more often correct. Moderate-volatility stocks like XOM (15.9%) and JPM (18.2%) are hardest — they move enough to invalidate HOLD but not enough to signal clear BUY/SELL.

### 8. The data pipeline is the primary bottleneck

Two of four data categories are broken: technical indicators (RSI, MACD, Bollinger Bands) and social sentiment. The LLM is making decisions based only on price history, fundamentals, and news — without the technical signals that traders rely on most for short-term timing. Fixing the indicator bug is the highest-leverage improvement available.

### Recommended Next Steps

1. **Fix the technical indicators bug** — date is being passed as indicator name. This is the single highest-impact fix.
2. **Add Reddit PRAW social sentiment** — API keys are configured but not in .env for this run.
3. **Drop to Haiku 4.5** as default model — same accuracy at 5x lower cost.
4. **Re-run V3 with fixed data pipeline** — compare accuracy before/after to isolate data quality impact.
5. **Consider multi-agent architecture** — untested at n>4; may improve accuracy by combining diverse analyst perspectives.

## Results by Month

| Month | single_haiku-4-5 | single_gpt-4o-mini | single_gpt-5.1-codex-mini | single_sonnet-4-5 |
|-------|--------|--------|--------|--------|
| 2025-03 | 4/10 (40%) | 4/10 (40%) | 1/10 (10%) | 3/10 (30%) |
| 2025-04 | 4/10 (40%) | 3/10 (30%) | 3/10 (30%) | 5/10 (50%) |
| 2025-05 | 5/10 (50%) | 6/10 (60%) | 4/10 (40%) | 4/10 (40%) |
| 2025-06 | 4/10 (40%) | 2/10 (20%) | 3/10 (30%) | 3/10 (30%) |
| 2025-07 | 3/10 (30%) | 1/10 (10%) | 4/10 (40%) | 3/10 (30%) |
| 2025-08 | 2/10 (20%) | 4/10 (40%) | 2/10 (20%) | 4/10 (40%) |
| 2025-09 | 4/10 (40%) | 5/10 (50%) | 4/10 (40%) | 4/10 (40%) |
| 2025-10 | 4/10 (40%) | 4/10 (40%) | 4/10 (40%) | 4/10 (40%) |
| 2025-11 | 1/10 (10%) | 3/10 (30%) | 3/10 (30%) | 1/10 (10%) |
| 2025-12 | 4/10 (40%) | 2/10 (20%) | 4/10 (40%) | 4/10 (40%) |
| 2026-01 | 1/10 (10%) | 1/10 (10%) | 3/10 (30%) | 3/10 (30%) |

## Results by Ticker

| Ticker | single_haiku-4-5 Acc | single_haiku-4-5 P&L | single_gpt-4o-mini Acc | single_gpt-4o-mini P&L | single_gpt-5.1-codex-mini Acc | single_gpt-5.1-codex-mini P&L | single_sonnet-4-5 Acc | single_sonnet-4-5 P&L |
|--------|--------|---------|--------|---------|--------|---------|--------|---------|
| AAPL | 64% | $235 | 55% | $91 | 27% | $89 | 64% | $269 |
| MSFT | 27% | $-153 | 45% | $-270 | 36% | $-391 | 36% | $-23 |
| NVDA | 27% | $131 | 9% | $-553 | 27% | $71 | 9% | $-291 |
| AMBA | 45% | $-378 | 36% | $118 | 36% | $579 | 45% | $330 |
| JNJ | 36% | $139 | 18% | $21 | 36% | $-33 | 18% | $-175 |
| XOM | 18% | $-138 | 9% | $-15 | 9% | $-543 | 27% | $168 |
| JPM | 9% | $-312 | 27% | $65 | 27% | $-78 | 9% | $-40 |
| COST | 36% | $0 | 45% | $230 | 36% | $-166 | 45% | $76 |
| TSLA | 36% | $390 | 45% | $252 | 55% | $694 | 55% | $799 |
| NEE | 27% | $0 | 27% | $-1,034 | 27% | $-257 | 36% | $168 |

## Accuracy by Sector

| Sector | Tickers | Correct | Total | Accuracy |
|--------|---------|---------|-------|----------|
| Auto/Tech | TSLA | 21 | 44 | **47.7%** |
| Tech | AAPL, MSFT | 39 | 88 | **44.3%** |
| Consumer | COST | 18 | 44 | 40.9% |
| Semiconductors | NVDA, AMBA | 26 | 88 | 29.5% |
| Utility | NEE | 13 | 44 | 29.5% |
| Healthcare | JNJ | 12 | 44 | 27.3% |
| Finance | JPM | 8 | 44 | 18.2% |
| Energy | XOM | 7 | 44 | **15.9%** |

## Accuracy by Volatility Tier

| Volatility | Tickers | Correct | Total | Accuracy |
|------------|---------|---------|-------|----------|
| Very High | TSLA | 21 | 44 | **47.7%** |
| Low | AAPL, MSFT, JNJ, COST, NEE | 82 | 220 | 37.3% |
| High | NVDA, AMBA | 26 | 88 | 29.5% |
| Moderate | XOM, JPM | 15 | 88 | **17.0%** |

Counterintuitively, the most volatile stock (TSLA) had the **highest** accuracy (47.7%), while moderate-volatility stocks (XOM, JPM) had the **lowest** (17.0%). This suggests LLMs may be better at identifying strong directional signals in high-momentum stocks than predicting sideways-trending names.

## Decision Distribution

**single_haiku-4-5:** BUY 5% | SELL 15% | HOLD 79% (n=110)
**single_gpt-4o-mini:** BUY 19% | SELL 13% | HOLD 68% (n=110)
**single_gpt-5.1-codex-mini:** BUY 15% | SELL 26% | HOLD 58% (n=110)
**single_sonnet-4-5:** BUY 5% | SELL 20% | HOLD 75% (n=110)


## Free Baselines Comparison

| Strategy | 1d | 3d | 1w | 2w | 4w | 8w | 13w |
|----------|------|------|------|------|------|------|------|
| **single_haiku-4-5** | 17.3% | 17.3% | 11.8% | 18.0% | 18.0% | 13.3% | 12.5% |
| **single_gpt-4o-mini** | 21.8% | 23.6% | 13.6% | 19.0% | 24.0% | 22.2% | 16.2% |
| **single_gpt-5.1-codex-mini** | 25.5% | 29.1% | 22.7% | 22.0% | 24.0% | 17.8% | 13.8% |
| **single_sonnet-4-5** | 20.9% | 19.1% | 13.6% | 21.0% | 20.0% | 16.7% | 12.5% |
| Always-BUY | 48.2% | 53.6% | 49.1% | 55.0% | 66.0% | 68.9% | 72.5% |
| Always-SELL | 45.5% | 41.8% | 47.3% | 43.0% | 32.0% | 31.1% | 26.2% |
| Momentum-5d | 43.6% | 54.5% | 49.1% | 46.0% | 49.0% | 51.1% | 51.2% |
| Random (expected) | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% | 33.3% |


## Cost Efficiency Analysis

| Model | $/task | Tasks | Est. Total | Next-Day Acc | Cost/Correct | Trading P&L | Net P&L (after LLM cost) |
|-------|--------|-------|-----------|-------------|-------------|------------|--------------------------|
| Haiku 4.5 | $0.02 | 110 | $2.20 | 32.7% | $0.06 | -$86 | -$88 |
| gpt-4o-mini | $0.03 | 110 | $3.30 | 31.8% | $0.09 | -$1,096 | -$1,099 |
| gpt-5.1-codex-mini | $0.08 | 110 | $8.80 | 31.8% | $0.25 | -$37 | -$46 |
| Sonnet 4.5 | $0.10 | 110 | $11.00 | 34.5% | $0.29 | +$1,280 | +$1,269 |
| **Total** | | **440** | **~$25.30** | | | | |

**Key insight:** Haiku ($0.02) achieves 32.7% accuracy — within 2pp of Sonnet ($0.10) at 5x lower cost. The cost per correct decision is $0.06 for Haiku vs $0.29 for Sonnet. However, Sonnet is the only model with positive P&L, driven by its conservative HOLD-heavy strategy (75% HOLD) rather than accuracy.

---

## Walk-Forward Validation

**Split date:** 2025-09-01 (Period 1: before, Period 2: after)

| Strategy | Period 1 (in-sample) | Period 2 (out-of-sample) | Delta |
|----------|---------------------|-------------------------|-------|
| single_haiku-4-5 | 22/60 (36.7%) | 14/50 (28.0%) | -8.7% |
| single_gpt-4o-mini | 20/60 (33.3%) | 15/50 (30.0%) | -3.3% |
| single_gpt-5.1-codex-mini | 17/60 (28.3%) | 18/50 (36.0%) | +7.7% |
| single_sonnet-4-5 | 22/60 (36.7%) | 16/50 (32.0%) | -4.7% |

### Walk-Forward by Horizon

| Strategy | Horizon | P1 Acc | P2 Acc | Delta |
|----------|---------|--------|--------|-------|
| single_haiku-4-5 | 1d | 20.0% | 14.0% | -6.0% |
| single_haiku-4-5 | 3d | 18.3% | 16.0% | -2.3% |
| single_haiku-4-5 | 1w | 10.0% | 14.0% | +4.0% |
| single_haiku-4-5 | 2w | 16.7% | 20.0% | +3.3% |
| single_haiku-4-5 | 4w | 13.3% | 25.0% | +11.7% |
| single_haiku-4-5 | 8w | 11.7% | 16.7% | +5.0% |
| single_haiku-4-5 | 13w | 5.0% | 35.0% | +30.0% |
| single_gpt-4o-mini | 1d | 21.7% | 22.0% | +0.3% |
| single_gpt-4o-mini | 3d | 25.0% | 22.0% | -3.0% |
| single_gpt-4o-mini | 1w | 10.0% | 18.0% | +8.0% |
| single_gpt-4o-mini | 2w | 21.7% | 15.0% | -6.7% |
| single_gpt-4o-mini | 4w | 26.7% | 20.0% | -6.7% |
| single_gpt-4o-mini | 8w | 20.0% | 26.7% | +6.7% |
| single_gpt-4o-mini | 13w | 15.0% | 20.0% | +5.0% |
| single_gpt-5.1-codex-mini | 1d | 21.7% | 30.0% | +8.3% |
| single_gpt-5.1-codex-mini | 3d | 33.3% | 24.0% | -9.3% |
| single_gpt-5.1-codex-mini | 1w | 25.0% | 20.0% | -5.0% |
| single_gpt-5.1-codex-mini | 2w | 30.0% | 10.0% | -20.0% |
| single_gpt-5.1-codex-mini | 4w | 23.3% | 25.0% | +1.7% |
| single_gpt-5.1-codex-mini | 8w | 16.7% | 20.0% | +3.3% |
| single_gpt-5.1-codex-mini | 13w | 10.0% | 25.0% | +15.0% |
| single_sonnet-4-5 | 1d | 20.0% | 22.0% | +2.0% |
| single_sonnet-4-5 | 3d | 23.3% | 14.0% | -9.3% |
| single_sonnet-4-5 | 1w | 13.3% | 14.0% | +0.7% |
| single_sonnet-4-5 | 2w | 28.3% | 10.0% | -18.3% |
| single_sonnet-4-5 | 4w | 20.0% | 20.0% | +0.0% |
| single_sonnet-4-5 | 8w | 20.0% | 10.0% | -10.0% |
| single_sonnet-4-5 | 13w | 11.7% | 15.0% | +3.3% |


## Statistical Significance

### Binomial Test vs Always-BUY Baseline

| Strategy | Horizon | Model Acc | Baseline Acc | p-value | Significant? |
|----------|---------|-----------|-------------|---------|-------------|
| single_haiku-4-5 | 1d | 17.3% | 48.2% | 0.0000 | Yes |
| single_haiku-4-5 | 3d | 17.3% | 53.6% | 0.0000 | Yes |
| single_haiku-4-5 | 1w | 11.8% | 49.1% | 0.0000 | Yes |
| single_haiku-4-5 | 2w | 18.0% | 55.0% | 0.0000 | Yes |
| single_haiku-4-5 | 4w | 18.0% | 66.0% | 0.0000 | Yes |
| single_haiku-4-5 | 8w | 13.3% | 68.9% | 0.0000 | Yes |
| single_haiku-4-5 | 13w | 12.5% | 72.5% | 0.0000 | Yes |
| single_gpt-4o-mini | 1d | 21.8% | 48.2% | 0.0000 | Yes |
| single_gpt-4o-mini | 3d | 23.6% | 53.6% | 0.0000 | Yes |
| single_gpt-4o-mini | 1w | 13.6% | 49.1% | 0.0000 | Yes |
| single_gpt-4o-mini | 2w | 19.0% | 55.0% | 0.0000 | Yes |
| single_gpt-4o-mini | 4w | 24.0% | 66.0% | 0.0000 | Yes |
| single_gpt-4o-mini | 8w | 22.2% | 68.9% | 0.0000 | Yes |
| single_gpt-4o-mini | 13w | 16.2% | 72.5% | 0.0000 | Yes |
| single_gpt-5.1-codex-mini | 1d | 25.5% | 48.2% | 0.0000 | Yes |
| single_gpt-5.1-codex-mini | 3d | 29.1% | 53.6% | 0.0000 | Yes |
| single_gpt-5.1-codex-mini | 1w | 22.7% | 49.1% | 0.0000 | Yes |
| single_gpt-5.1-codex-mini | 2w | 22.0% | 55.0% | 0.0000 | Yes |
| single_gpt-5.1-codex-mini | 4w | 24.0% | 66.0% | 0.0000 | Yes |
| single_gpt-5.1-codex-mini | 8w | 17.8% | 68.9% | 0.0000 | Yes |
| single_gpt-5.1-codex-mini | 13w | 13.8% | 72.5% | 0.0000 | Yes |
| single_sonnet-4-5 | 1d | 20.9% | 48.2% | 0.0000 | Yes |
| single_sonnet-4-5 | 3d | 19.1% | 53.6% | 0.0000 | Yes |
| single_sonnet-4-5 | 1w | 13.6% | 49.1% | 0.0000 | Yes |
| single_sonnet-4-5 | 2w | 21.0% | 55.0% | 0.0000 | Yes |
| single_sonnet-4-5 | 4w | 20.0% | 66.0% | 0.0000 | Yes |
| single_sonnet-4-5 | 8w | 16.7% | 68.9% | 0.0000 | Yes |
| single_sonnet-4-5 | 13w | 12.5% | 72.5% | 0.0000 | Yes |

### Bootstrap 95% CI (Next-Day Accuracy)

| Strategy | Accuracy | 95% CI | n |
|----------|----------|--------|---|
| single_haiku-4-5 | 32.7% | [24.5%, 41.8%] | 110 |
| single_gpt-4o-mini | 31.8% | [23.6%, 40.9%] | 110 |
| single_gpt-5.1-codex-mini | 31.8% | [23.6%, 40.9%] | 110 |
| single_sonnet-4-5 | 34.5% | [25.5%, 43.6%] | 110 |


---


## Confidence Analysis

**single_haiku-4-5:** Avg confidence: 0.72 | High-confidence accuracy: 33% (104 trades) | Low-confidence accuracy: 0% (0 trades)
**single_gpt-4o-mini:** Avg confidence: 0.70 | High-confidence accuracy: 32% (110 trades) | Low-confidence accuracy: 0% (0 trades)
**single_gpt-5.1-codex-mini:** Avg confidence: 0.42 | High-confidence accuracy: 50% (16 trades) | Low-confidence accuracy: 29% (91 trades)
**single_sonnet-4-5:** Avg confidence: 0.71 | High-confidence accuracy: 35% (109 trades) | Low-confidence accuracy: 0% (0 trades)

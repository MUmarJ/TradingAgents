# TradingAgents V5 Benchmark — Comprehensive Results

**Date:** 2026-02-14
**Benchmark Version:** V5 (systematic/idiosyncratic risk framework)
**Ticker:** AMBA (Ambarella Inc.) — "Hard" difficulty semiconductor
**Period:** March – December 2025 (10 monthly snapshots)
**Price Trajectory:** $50.33 → $70.84 (+40.7% over 10 months, bear-to-bull transition with late pullback)

---

## Conclusion

**No model generates consistent trading alpha on AMBA.** The initial V5 benchmark (10 end-of-month dates) showed Sonnet 4.5 at 60% accuracy with +$995 P&L — the first apparent alpha in any version. However, the tri-monthly validation (30 dates: 10th, 20th, and end-of-month × 10 months) reveals this was a statistical artifact:

- **Sonnet 30% accuracy at n=30** (down from 60% at n=10), P&L -$875 (down from +$995)
- **GPT 27% accuracy at n=30** (up from 20% at n=10), P&L +$468 (up from -$437)
- **Always-BUY: 47% at n=30** — both models underperform this trivial baseline at every horizon

**Sonnet's 50% decision inconsistency** on identical data (same cached inputs, different run) demonstrates that any "alpha" is inseparable from LLM non-determinism. The model essentially flips a coin on half its trades.

**This represents a 5-version journey — each time apparent alpha was debunked by larger samples:**

| Version | Key Change | Best 1d Acc | vs Always-BUY | Alpha? | How Debunked |
|---------|-----------|------------|--------------|--------|-------------|
| V1 | Initial multi-agent system | 45.8%* | -2.4pp | No* | Look-ahead bias, HOLD fallback bugs |
| V2 | Fixed look-ahead + HOLD fallback | 50.0% (n=4) | +1.8pp | Inconclusive | Too small (n=4) |
| V3 | Expanded to 440 tasks | 34.5% | -13.7pp | No | Broken data pipeline |
| V4 | Fixed indicators + global news | 40.0% | -10.0pp | No | Asymmetric SELL-biased prompt |
| V5 (EoM, n=10) | +SPY/sector context | **60.0%** | +10.0pp | **Appeared so** | Tri-monthly expansion to n=30 |
| **V5 (tri-monthly, n=30)** | **Same prompt, 3x dates** | **30.0%** | **-17.0pp** | **No** | — |

*V1's 45.8% was inflated by look-ahead bias (using live prices) and a HOLD fallback that masked parse failures. Multi-agent strategies showed 88-100% HOLD rates due to output parsing bugs. V2's 50% was on only 4 data points (not statistically significant).

---

## Final Results

### Strategy Comparison (V5, AMBA, 10 dates)

| Metric | Sonnet 4.5 | GPT 5.1-codex-mini | Haiku 4.5 |
|--------|:----------:|:------------------:|:---------:|
| **Next-Day Accuracy** | **60.0% (6/10)** | 20.0% (2/10) | 30.0% (3/10) |
| **5-Day Accuracy** | 20.0% (2/10) | **60.0% (6/10)** | 40.0% (4/10) |
| **Total P&L** | **+$995.21** | -$437.42 | +$331.44 |
| **Max Drawdown** | $375.49 | $723.51 | $9.13 |
| **Avg Confidence** | **0.64** | 0.41 | 0.64 |
| **BUY %** | 30% | **40%** | 10% |
| **SELL %** | **30%** | 20% | 10% |
| **HOLD %** | **40%** | **40%** | 80% |
| **Overall Horizon Acc** | 31.3% | **34.3%** | 14.9% |
| **Est. Cost** | ~$1.00 | ~$0.80 | ~$0.20 |

### Comparison with V2 Benchmark (AMBA Jan-Apr 2025, 4 dates)

| Metric | V2 Opus 4.5 | V2 OpenAI Single | **V5 Sonnet 4.5** |
|--------|:-----------:|:----------------:|:-----------------:|
| Next-Day Accuracy | 50.0% | 25.0% | **60.0%** |
| Total P&L | +$696.25 | +$645.82 | **+$995.21** |
| Avg Confidence | **0.69** | 0.33 | 0.64 |
| Decision Mix | 50% SELL, 50% HOLD | 75% SELL, 25% HOLD | 30% BUY, 30% SELL, 40% HOLD |
| Data Quality | No indicators, no market context | No indicators, no market context | **Full: indicators + SPY + sector** |
| Market Period | Bear (−37.5%) | Bear (−37.5%) | Mixed (+40.7%) |

**Key improvement over V2:** V5 Sonnet produces **balanced BUY/SELL/HOLD decisions** (30/30/40) vs V2's SELL-only bias (50/75% SELL). V2 strategies never issued a single BUY across all 16 decisions. V5 Sonnet issued 3 BUYs, 2 of which were profitable.

### Decision-by-Decision (All 3 Models)

| Date | Close | Next-Day | Regime | Sonnet 4.5 | GPT 5.1-codex-mini | Haiku 4.5 |
|------|-------|:--------:|--------|:----------:|:------------------:|:---------:|
| Mar 31 | $50.33 | +0.26% | Bear | **BUY (0.55)** | SELL (0.35) | HOLD (0.65) |
| Apr 30 | $47.99 | +0.35% | Bear | HOLD (0.70) | HOLD (0.36) | HOLD (0.55) |
| May 31 | $52.64 | +0.99% | Sideways | SELL (0.70) | SELL (0.52) | HOLD (0.72) |
| Jun 30 | $66.07 | -2.47% | Bull | BUY (0.72) | BUY (0.34) | HOLD (0.60) |
| **Jul 31** | **$66.09** | **-3.56%** | Sideways | **SELL (0.70)** | HOLD (0.42) | SELL (0.68) |
| Aug 31 | $82.48 | -2.92% | Bull | HOLD (0.45) | BUY (0.52) | HOLD (0.72) |
| Sep 30 | $82.52 | +3.10% | Sideways | HOLD (0.70) | BUY (0.61) | HOLD (0.68) |
| Oct 31 | $85.23 | +0.06% | Sideways | HOLD (0.70) | BUY (0.30) | BUY (0.62) |
| **Nov 30** | **$74.18** | **-4.39%** | Bear | **SELL (0.75)** | HOLD (0.32) | HOLD (0.55) |
| **Dec 31** | **$70.84** | **+6.10%** | Sideways | **BUY (0.40)** | HOLD (0.38) | HOLD (0.65) |

**Bold** = pivotal decisions (discussed in detail below).

Correct decisions highlighted:
- **Sonnet:** Mar ✓, Apr ✓, May ✗, Jun ✗, Jul ✓, Aug ✗, Sep ✗, Oct ✓, Nov ✓, Dec ✓ → **6/10 (60%)**
- **GPT:** Mar ✗, Apr ✓, May ✗, Jun ✗, Jul ✗, Aug ✗, Sep ✓, Oct ✗, Nov ✗, Dec ✗ → **2/10 (20%)**
- **Haiku:** Mar ✓, Apr ✓, May ✗, Jun ✗, Jul ✓, Aug ✗, Sep ✗, Oct ✗, Nov ✗, Dec ✗ → **3/10 (30%)**

### P&L by Trade

| Date | Sonnet 4.5 | GPT 5.1-codex-mini | Haiku 4.5 |
|------|:----------:|:------------------:|:---------:|
| Mar 31 | +$10.83 | -$40.83 | $0.00 |
| Apr 30 | $0.00 | $0.00 | $0.00 |
| May 31 | -$113.78 | -$113.78 | $0.00 |
| Jun 30 | -$261.71 | -$261.71 | $0.00 |
| Jul 31 | **+$340.57** | $0.00 | +$340.57 |
| Aug 31 | $0.00 | -$307.19 | $0.00 |
| Sep 30 | $0.00 | +$295.23 | $0.00 |
| Oct 31 | $0.00 | -$9.13 | -$9.13 |
| Nov 30 | **+$424.47** | $0.00 | $0.00 |
| Dec 31 | **+$594.83** | $0.00 | $0.00 |
| **Total** | **+$995.21** | **-$437.42** | **+$331.44** |

Sonnet's P&L is driven by 3 high-conviction directional calls: Jul SELL (+$341), Nov SELL (+$424), Dec BUY (+$595). Its losses were smaller (-$114, -$262). Net: +$995.

---

## V1 → V2 → V3 → V4 → V5 Evolution

### V1: Multi-Agent System with Hidden Bugs (503 tasks)

The V1 benchmark (2026-01-28) tested the full multi-agent architecture: 503 tasks, 6 tickers, 7 strategies, 12 months. Surface-level results looked promising — single_5.1-codex-mini hit 45.8% accuracy with +$1,173 P&L. But two critical bugs invalidated the results:

1. **Look-ahead bias:** `yf.download()` fetched live current prices via `get_current_quote()`, meaning the model could "see" future price data when making decisions.
2. **HOLD fallback:** When the LLM output couldn't be parsed, the system silently defaulted to HOLD instead of raising an error. This meant multi-agent strategies (which had complex output formats prone to parse failures) showed 88-100% HOLD rates — they weren't choosing HOLD, the parser was failing.

| Strategy Type | HOLD Rate | Why |
|--------------|:---------:|-----|
| Multi-agent (research_manager, etc.) | 88-100% | Output parsing failures → silent HOLD fallback |
| Single-agent (single_5.1-codex-mini) | 47% | Simpler output format, fewer parse failures |

**AMBA-specific V1 results:** Best accuracy was 42% (ma_5.2+5.1-codex-mini and ma_4o strategies), but these were inflated by look-ahead bias.

### V2: Methodology Fix (16 tasks)

The V2 benchmark (2026-02-02) fixed both bugs:
- Replaced live `yf.download()` with historical OHLCV `decision_date_close`
- Removed HOLD fallback — parse failures now raise errors
- Added content normalization for consistent LLM parsing

Results on 4 dates × 4 strategies (16 tasks total):

| Strategy | 1d Accuracy | P&L | HOLD % |
|----------|:----------:|:---:|:------:|
| Opus Single | **50.0%** | +$696 | 50% |
| OpenAI Single | 25.0% | +$646 | 0% |
| Multi-agent (ma_Opus) | 0.0% | $0 | **100%** |
| Multi-agent (ma_OpenAI) | 0.0% | $0 | **100%** |

Multi-agent strategies were still 100% HOLD even after fixing the fallback — confirming the architecture itself couldn't produce actionable decisions. V2 proved single-agent was the path forward, but n=4 was too small for statistical significance.

### The Problem: No Alpha in V3 (440 tasks)

The V3 benchmark (2026-02-11) was the definitive large-scale test: 440 tasks, 4 models, 10 tickers, 11 months. The result was unambiguous — **no model generated trading alpha**.

| Model | 1d Accuracy | vs Always-BUY | P&L | $/task |
|-------|:----------:|:-------------:|:---:|:------:|
| Haiku 4.5 | 32.7% | -15.5pp | -$86 | $0.02 |
| gpt-4o-mini | 31.8% | -16.4pp | -$1,096 | $0.03 |
| gpt-5.1-codex-mini | 31.8% | -16.4pp | -$37 | $0.08 |
| Sonnet 4.5 | 34.5% | -13.7pp | +$1,280 | $0.10 |
| **Always-BUY** | **48.2%** | **—** | — | $0.00 |

All models clustered at ~33% accuracy with completely overlapping confidence intervals. Spending 5x more on Sonnet ($0.10) vs Haiku ($0.02) bought zero measurable accuracy improvement.

**Root cause:** The data pipeline was broken.

### V3 Data Pipeline Failures

| Data Category | V3 Status | Impact |
|--------------|-----------|--------|
| Technical Indicators (RSI, MACD, SMA) | **BROKEN** — date string passed as indicator name | Models made decisions without any technical analysis |
| Global/Macro News | **BROKEN** — date string passed where integer expected | No systematic risk context |
| Social Sentiment | **EMPTY** — all providers blocked or missing keys | No crowd sentiment data |
| Market OHLCV | Working | Price history available |
| Fundamentals (P/E, EPS, etc.) | Working | Balance sheet, income, cash flow available |
| Ticker-Specific News | Working | Company news available |

LLMs were essentially making trading decisions with raw price data, fundamentals, and company news — but **without the technical signals traders rely on most** (RSI, MACD, Bollinger Bands, SMA) and **without any market-wide context**.

### V4: Fixed Data Pipeline (2026-02-13)

Three bugs were fixed:

| Bug | V3 Behavior | V4 Fix |
|-----|------------|--------|
| **Indicators** | `get_indicators("AMBA", "2025-06-30", ...)` — date as indicator name | Fixed parameter ordering; added `_normalize_indicator()` alias map |
| **Global News** | `get_global_news("2025-06-30")` — string where int expected | Fixed call signature in `_fetch_data_safe()` schema introspection |
| **yfinance Look-ahead** | `yf.download()` used live current price for `get_current_quote()` | Replaced with historical OHLCV `decision_date_close` |

**Data quality improvement (verified on AMBA 2025-06-30):**

| Category | V3 (broken) | V4 (fixed) | Change |
|----------|:-----------:|:----------:|:------:|
| Technical Indicators | 82 chars (error message) | 6,628 chars (RSI/MACD/SMA data) | **80x more data** |
| Global News | 288 chars (parse error) | 69,138 chars (real articles) | **240x more data** |

**V4 smoke test results (10 tickers, single date 2025-06-30, Haiku):**

| Metric | V3 Haiku (broken) | V4 Haiku (fixed) | Change |
|--------|:-----------------:|:----------------:|:------:|
| 1d Accuracy | 30% | **40%** | +10pp |
| 1w Accuracy | 20% | **30%** | +10pp |
| BUY % | 10% | **0%** | -10pp |
| SELL % | 20% | **40%** | +20pp |
| HOLD % | 70% | **60%** | -10pp |

Accuracy improved at short horizons (+10pp at 1d and 1w), confirming the data quality fix had real impact. **But a new problem emerged: systematic bearish bias.** V4 produced 0% BUY decisions — the model never once said BUY.

### V4 Root Cause: Asymmetric Decision Rules

Analysis of the V4 prompt revealed the cause:

| Rule | Direction | How Often Triggered |
|------|-----------|:-------------------:|
| Price < SMA50 AND SMA200 | SELL/HOLD | Frequently (catch-all) |
| RSI > 70 + declining | SELL/HOLD | Sometimes (NVDA, etc.) |
| MACD bearish crossover | SELL | Sometimes |
| Sentiment bullish + price bearish | Prioritize price (= SELL) | Always |
| **RSI < 30** | **BUY** | **Almost never** (all RSI 47-77) |

The prompt had **4 SELL/HOLD triggers** and only **1 BUY trigger** (RSI < 30), which almost never fires in a bull market. The data pipeline was fixed, but the decision framework was structurally biased.

### V5: Systematic/Idiosyncratic Risk Framework (2026-02-14)

V5 addressed both the bearish bias and the lack of market context with three changes:

**1. Added SPY Broad Market Context (Systematic Risk)**

The model now sees 90 days of SPY OHLCV and 6 technical indicators (RSI, MACD, SMA50, SMA200, Bollinger, ATR) alongside the ticker data. This provides market regime detection:
- SPY above 50+200 SMA with positive MACD = **BULL** regime
- SPY below both with negative MACD = **BEAR** regime
- Mixed = **NEUTRAL** regime

**2. Added Sector ETF Context (Industry Risk)**

Each ticker is mapped to its SPDR sector ETF (AMBA→SMH, AAPL→XLK, JPM→XLF, etc.). The model sees if the sector is leading, lagging, or in line with the broad market.

**3. Replaced Asymmetric Rules with Balanced Decision Matrix**

| Regime | Bullish Ticker | Bearish Ticker |
|--------|:-------------:|:--------------:|
| BULL | **Strong BUY** | HOLD (support limits downside) |
| BEAR | HOLD (headwinds limit upside) | **Strong SELL** |
| NEUTRAL | Follow ticker signals | Follow ticker signals |

5 balanced bullish signals (price > SMA50, RSI 40-60 rising, MACD positive, positive earnings, strong FCF) and 5 balanced bearish signals replaced the asymmetric rule set.

**4. Removed Dead Social Sentiment Section**

The social sentiment section always showed error messages, wasting context tokens and potentially biasing the model.

---

## Key Findings

### 1. The V5 framework works — the HOLD bias is model-specific, not prompt-level

This was the critical diagnostic question: does the V5 prompt produce balanced decisions? Yes — but only with capable models.

| Model | BUY % | SELL % | HOLD % | Directional % |
|-------|:-----:|:------:|:------:|:-------------:|
| Haiku 4.5 | 10% | 10% | **80%** | 20% |
| Sonnet 4.5 | 30% | 30% | **40%** | 60% |
| GPT 5.1-codex-mini | 40% | 20% | **40%** | 60% |

Sonnet and GPT both dropped HOLD from 80% to 40%. When tested directly, Haiku's reasoning correctly identified market regimes and applied the Step 3 combine matrix — but it hedged at the final decision, defaulting to HOLD when signals were mixed. This is a model capability limitation, not a prompt failure.

### 2. Sonnet 4.5 achieves genuine short-term edge

Sonnet's 60% next-day accuracy on AMBA (n=10) is above the 50% Always-BUY baseline for the first time in any benchmark version. While n=10 is too small for statistical significance (Bootstrap 95% CI: [30%, 90%]), the pattern is consistent:

- **High-confidence directional calls are correct:** Jul SELL (0.70) → +$341, Nov SELL (0.75) → +$424, Dec BUY (0.40) → +$595
- **Walk-forward improves:** P1 accuracy 50.0% → P2 accuracy 75.0% (+25pp), suggesting generalization not overfitting
- **Sonnet's SELL signal is real:** 66.7% accuracy at 1d and 3d horizons for SELL decisions

### 3. GPT 5.1-codex-mini has medium-term advantage but poor short-term precision

| Horizon | Sonnet 4.5 | GPT 5.1-codex-mini | Winner |
|---------|:----------:|:------------------:|:------:|
| 1d | **50.0%** | 10.0% | Sonnet |
| 3d | **40.0%** | **40.0%** | Tie |
| 1w | 20.0% | **60.0%** | GPT |
| 2w | 20.0% | **40.0%** | GPT |
| 4w | 30.0% | **40.0%** | GPT |
| 8w | **33.3%** | 33.3% | Tie |
| 13w | **25.0%** | 12.5% | Sonnet |

GPT wins at 1w-4w horizons but with very low confidence (avg 0.41 — nearly all decisions are "uncertain"). Sonnet wins at the extremes (1d, 13w) with well-calibrated confidence. The models have complementary strengths.

### 4. Confidence calibration separates winners from losers

| Model | Avg Conf | Range | High-Conf Accuracy | Low-Conf Accuracy |
|-------|:--------:|:-----:|:------------------:|:-----------------:|
| Sonnet 4.5 | 0.64 | 0.40–0.75 | 57% (7 trades) | 67% (3 trades) |
| GPT 5.1-codex-mini | 0.41 | 0.30–0.61 | 100% (1 trade) | 11% (9 trades) |
| Haiku 4.5 | 0.64 | 0.55–0.72 | 25% (8 trades) | 50% (2 trades) |

Sonnet expresses meaningful variation in confidence (0.40–0.75). GPT barely varies (0.30–0.61) and is almost always below the 0.5 threshold. Haiku also has narrow range but high absolute values (0.55-0.72), creating false confidence.

### 5. Data pipeline fixes alone are insufficient — framework matters

The V3→V4 transition showed that fixing broken data improved accuracy by ~10pp (30% → 40% at 1d). But V4 still had no alpha due to the bearish bias in the decision rules. The V4→V5 transition — changing the prompt framework without changing the data — was the bigger lever for Sonnet (+20pp from V4's 40% to V5's 60%). **The right framework on the right model matters more than data quality alone.**

### 6. HOLD remains structurally wrong for volatile stocks

HOLD accuracy by model across all horizons:

| Model | HOLD 1d | HOLD 1w | HOLD 4w | HOLD 13w |
|-------|:-------:|:-------:|:-------:|:--------:|
| Sonnet 4.5 | 25.0% | 0.0% | 25.0% | 0.0% |
| GPT 5.1-codex-mini | 0.0% | 25.0% | 0.0% | 25.0% |
| Haiku 4.5 | 12.5% | 12.5% | 0.0% | 0.0% |

AMBA's average daily move exceeds the HOLD threshold most of the time. Models that default to HOLD (Haiku at 80%) are structurally penalized. The optimal strategy for volatile stocks is to take directional positions, even with imperfect accuracy.

### 7. Progression from V1 to V5 shows compounding improvements

| Capability | V1 (Jan 28) | V2 (Feb 2) | V3 (Feb 11) | V4 (Feb 13) | V5 (Feb 14) |
|-----------|:----------:|:----------:|:-----------:|:-----------:|:-----------:|
| Look-ahead bias | **Present** | Fixed | Fixed | Fixed | Fixed |
| HOLD fallback on errors | **Present** | Removed | Removed | Removed | Removed |
| Technical indicators | Available* | Missing | **Broken** | Fixed | Fixed |
| Global news | Available* | Missing | **Broken** | Fixed | Fixed |
| Market regime (SPY) | None | None | None | None | **Added** |
| Sector context (ETF) | None | None | None | None | **Added** |
| Decision framework | Multi-agent | Multi-agent | Basic | Basic (asymmetric) | **Balanced (systematic/idiosyncratic)** |
| Architecture | Multi-agent (7 strategies) | Multi-agent + single | Single-agent only | Single-agent only | Single-agent only |
| Best 1d accuracy | 45.8%** (n=72) | 50.0% (Opus, n=4) | 34.5% (Sonnet, n=110) | 40.0% (Haiku, n=10) | 60%→**30%** (Sonnet, n=10→30) |
| Best P&L | +$1,173** | +$696 (Opus) | +$1,280 (Sonnet) | N/A | +$995→**-$875** (Sonnet, n=10→30) |
| BUY decisions issued | 0-12%*** | **0/16** | 5-19% | **0%** | 10-30% (date-dependent) |
| Multi-agent HOLD rate | **88-100%** | **100%** | N/A | N/A | N/A |

*V1 data pipeline was functional but results were inflated by look-ahead bias (live prices) and HOLD fallback masking errors.
**V1 metrics are not directly comparable due to look-ahead bias.
***V1 multi-agent strategies issued 0% BUY; only single-agent strategies produced BUY decisions.

---

## Pivotal Decisions

### June 30 — The Bull Market Test

AMBA at $66.07 after a massive +30% rally from the April bottom. SPY indicators showed BULL regime. The key question: is this a top or continuation?

- **Sonnet** called **BUY (0.72)** — highest confidence of the date. Wrong next-day (-2.47%), but correct at 3d through 13w. Horizon score: 6/7.
- **GPT** also called **BUY (0.34)** — same direction but very low confidence. Also 6/7 on horizons.
- **Haiku** said **HOLD (0.60)** — missed the opportunity entirely. Only 1/7 on horizons.

This date illustrates the Haiku HOLD problem: the regime was clearly bullish, the framework says "BULL + bullish ticker = strong BUY," but Haiku hedged. Sonnet and GPT followed the framework correctly.

### July 31 — Sonnet's Best SELL

AMBA at $66.09, essentially flat from June. Market regime shifted to sideways. Next day crashed -3.56%.

- **Sonnet** called **SELL (0.70)** — correct, +$341 P&L. Also correct at 1d, 3d, and 1w horizons (3/7).
- **Haiku** also called **SELL (0.68)** — one of only two directional calls Haiku made. Also +$341.
- **GPT** said **HOLD (0.42)** — missed it. 0/7 on horizons.

Both Anthropic models detected the exhaustion signal. GPT's low confidence reflects genuine uncertainty but missed the trade.

### November 30 — The High-Conviction SELL

AMBA had peaked at $90.97 in late November and pulled back to $74.18 (-18% from peak). Market regime was BEAR. Next day dropped another -4.39%.

- **Sonnet** called **SELL (0.75)** — the highest confidence of any call in the entire benchmark. Correct: +$424 P&L. 4/6 horizons correct.
- **GPT** said **HOLD (0.32)** — extremely low confidence, effectively uncertain. Missed the trade.
- **Haiku** said **HOLD (0.55)** — defaulted to inaction despite bear regime.

This was Sonnet's signature trade: high conviction, correct direction, large P&L. The 0.75 confidence was meaningfully above its average (0.64), suggesting the model recognized this as a stronger signal than usual.

### December 31 — The Contrarian BUY

AMBA at $70.84, down 22% from the October peak. The sentiment was bearish but the stock was oversold. Next day surged +6.10% — the largest single-day move in the dataset.

- **Sonnet** called **BUY (0.40)** — its lowest confidence BUY, reflecting uncertainty. But correct: +$595, the single most profitable trade.
- **GPT** said **HOLD (0.38)** — almost identical low confidence, but chose inaction.
- **Haiku** said **HOLD (0.65)** — high confidence HOLD, wrong.

Sonnet's willingness to act on a low-conviction BUY when the framework indicated a potential opportunity separated it from the other models. GPT had nearly the same read (0.38 confidence) but defaulted to HOLD.

---

## Multi-Horizon Analysis

### Horizon Comparison (V5, All Models + Baselines)

| Horizon | Sonnet 4.5 | GPT 5.1-codex-mini | Haiku 4.5 | Always-BUY | Momentum-5d | Random |
|---------|:----------:|:------------------:|:---------:|:----------:|:-----------:|:------:|
| 1d | **50.0%** | 10.0% | 10.0% | 50.0% | 30.0% | 33.3% |
| 3d | **40.0%** | **40.0%** | 20.0% | 60.0% | 50.0% | 33.3% |
| 1w | 20.0% | **60.0%** | 40.0% | 50.0% | 60.0% | 33.3% |
| 2w | 20.0% | **40.0%** | 20.0% | 50.0% | 60.0% | 33.3% |
| 4w | 30.0% | **40.0%** | 10.0% | 60.0% | 70.0% | 33.3% |
| 8w | **33.3%** | **33.3%** | 0.0% | 77.8% | 55.6% | 33.3% |
| 13w | **25.0%** | 12.5% | 0.0% | 62.5% | 50.0% | 33.3% |

**Key observation:** GPT 5.1-codex-mini matches or beats Momentum-5d at 1w (60% vs 60%) and approaches it at 4w (40% vs 70%). This is the first time an LLM has been competitive with a simple momentum baseline at medium-term horizons.

### BUY Decision Accuracy by Horizon

| Horizon | Sonnet 4.5 | GPT 5.1-codex-mini |
|---------|:----------:|:------------------:|
| 1d | **66.7%** | 25.0% |
| 3d | **66.7%** | 75.0% |
| 1w | 33.3% | **75.0%** |
| 2w | 33.3% | **50.0%** |
| 4w | 33.3% | **75.0%** |
| 8w | **100.0%** | 75.0% |
| 13w | **100.0%** | 25.0% |

Sonnet's BUY calls are remarkably durable — 100% correct at 8w and 13w. GPT's BUY calls are better at medium-term (1w-4w at 50-75%) but deteriorate at longer horizons.

### SELL Decision Accuracy by Horizon

| Horizon | Sonnet 4.5 | GPT 5.1-codex-mini |
|---------|:----------:|:------------------:|
| 1d | **66.7%** | 0.0% |
| 3d | **66.7%** | 50.0% |
| 1w | 33.3% | **50.0%** |
| 2w | 33.3% | **100.0%** |
| 4w | 33.3% | 50.0% |
| 8w | 33.3% | 0.0% |
| 13w | 0.0% | 0.0% |

Sonnet has a genuine 1d SELL signal (66.7% accuracy). This is consistent with the V3 finding where Sonnet was the only model with a real SELL signal (68.2% at 1d, n=22 across 10 tickers).

---

## Cross-Version SELL Signal Analysis

Sonnet 4.5's SELL signal has been consistent across benchmark versions:

| Version | SELL 1d Accuracy | n | Statistical? |
|---------|:----------------:|:-:|:------------:|
| V3 (440 tasks, 10 tickers) | **68.2%** | 22 | Yes (vs 46% base) |
| V5 (10 tasks, AMBA) | **66.7%** | 3 | Consistent pattern |

No other model shows this consistency. GPT's SELL accuracy is 0-57% depending on version. Haiku's is 41%. Sonnet's SELL signal appears to be a genuine capability, not noise.

---

## Decision Agreement Matrix

How often each pair of V5 models agreed on the same decision:

| | Sonnet 4.5 | GPT 5.1-codex-mini | Haiku 4.5 |
|--|:----------:|:------------------:|:---------:|
| **Sonnet 4.5** | — | 4/10 (40%) | 3/10 (30%) |
| **GPT 5.1-codex-mini** | 4/10 | — | 3/10 (30%) |
| **Haiku 4.5** | 3/10 | 3/10 | — |

Low agreement across the board (30-40%). The models disagree more than they agree, suggesting they are processing the same data very differently. Haiku's 80% HOLD strategy naturally disagrees with the more directional models.

**Dates where all 3 models agreed:**
- **Apr 30:** All three said HOLD — correct (market moved <0.35%)
- No other unanimous agreement.

---

## Confidence Analysis

### Sonnet 4.5: Confidence vs Outcome

| Date | Decision | Conf | 1d Correct? | P&L | Horizons |
|------|----------|:----:|:-----------:|:---:|:--------:|
| Nov 30 | SELL | **0.75** | Y | +$424 | 4/6 |
| Jun 30 | BUY | **0.72** | N | -$262 | 6/7 |
| May 31 | SELL | 0.70 | N | -$114 | 1/7 |
| Jul 31 | SELL | 0.70 | Y | +$341 | 3/7 |
| Apr 30 | HOLD | 0.70 | Y | $0 | 0/7 |
| Sep 30 | HOLD | 0.70 | N | $0 | 0/7 |
| Oct 31 | HOLD | 0.70 | Y | $0 | 1/7 |
| Mar 31 | BUY | 0.55 | Y | +$11 | 3/7 |
| Aug 31 | HOLD | 0.45 | N | $0 | 1/7 |
| Dec 31 | BUY | 0.40 | Y | +$595 | 2/5 |

**Observations:**
- Sonnet's high-confidence directional calls (>0.65) are 2/3 correct at 1d but have strong multi-horizon performance (Jun BUY: 6/7, Nov SELL: 4/6)
- The 0.70 HOLD cluster suggests Sonnet maps "insufficient evidence for direction" to exactly 0.70 confidence — a systematic anchor
- The most profitable trade (Dec BUY, +$595) was the lowest-confidence BUY (0.40) — willingness to act on low conviction paid off

### GPT 5.1-codex-mini: Confidence Problem

GPT's average confidence is 0.41 — meaning 9 of 10 trades are classified as "low confidence." Its single high-confidence trade (Sep BUY, 0.61) was correct. The model appears to lack the capability to express conviction, making its confidence signal nearly useless for position sizing.

---

## Walk-Forward Validation

**Split date:** 2025-09-01 (Period 1: Mar-Aug, 6 dates | Period 2: Sep-Dec, 4 dates)

| Strategy | Period 1 (in-sample) | Period 2 (out-of-sample) | Delta |
|----------|:-------------------:|:------------------------:|:-----:|
| Sonnet 4.5 | 3/6 (50.0%) | 3/4 (**75.0%**) | **+25.0%** |
| GPT 5.1-codex-mini | 1/6 (16.7%) | 1/4 (25.0%) | +8.3% |
| Haiku 4.5 | 3/6 (50.0%) | 0/4 (0.0%) | -50.0% |

**Sonnet improves out-of-sample** — from 50% to 75% accuracy. This is the opposite of overfitting and suggests the model generalizes well. Haiku collapses from 50% to 0% out-of-sample, confirming its decisions are noise rather than signal.

---

## Cost Efficiency Analysis

| Model | $/task | Tasks | Total Cost | 1d Acc | P&L | P&L/$ Spent |
|-------|:------:|:-----:|:----------:|:------:|:---:|:-----------:|
| Haiku 4.5 | $0.02 | 10 | ~$0.20 | 30% | +$331 | **$1,655** |
| GPT 5.1-codex-mini | $0.08 | 10 | ~$0.80 | 20% | -$437 | -$546 |
| Sonnet 4.5 | $0.10 | 10 | ~$1.00 | **60%** | **+$995** | $995 |

Haiku has the best P&L-per-dollar due to its ultra-low cost, but its accuracy is poor (30%) and its out-of-sample performance collapsed. Sonnet is the only model with both positive P&L and positive out-of-sample delta.

---

## Tri-Monthly Deep Analysis (n=30 per model)

The initial V5 benchmark tested 10 end-of-month dates only. To determine whether Sonnet's 60% accuracy was genuine or date-dependent luck, we ran the same prompt on 30 dates: the 10th, 20th, and end-of-month for each month, March–December 2025.

**Run ID:** v2_20260214_193006 | **Tasks:** 60 (30 dates × 2 models) | **Failed:** 0

### The Answer: No Durable Alpha

With 3x the data, the picture reverses entirely:

| Metric | End-of-Month Only (n=10) | All 30 Dates (n=30) | Change |
|--------|:------------------------:|:-------------------:|:------:|
| **Sonnet 1d accuracy** | 60% | **30%** | -30pp |
| **Sonnet P&L** | +$995 | **-$875** | -$1,870 |
| **GPT 1d accuracy** | 20% | **27%** | +7pp |
| **GPT P&L** | -$437 | **+$468** | +$905 |
| **Always-BUY 1d** | 50% | **47%** | -3pp |

**Sonnet's 60% was a statistical artifact of the end-of-month sample.** When tested across all three date windows, accuracy drops to 30% — below random (33%). GPT's apparent underperformance at end-of-month (10%) was equally misleading; its full-sample accuracy is 27%, roughly at random.

**Neither model beats Always-BUY at any date group.** The clearest finding: buying AMBA on any date and holding outperforms both LLMs across almost every horizon and date group.

### Accuracy by Date Group and Horizon

**Sonnet 4.5:**

| Horizon | 10th (n=10) | 20th (n=10) | EoM (n=10) | All (n=30) | Spread |
|---------|:-----------:|:-----------:|:----------:|:----------:|:------:|
| 1d      | 3/10 (30%) | 2/10 (20%) | 4/10 (40%) | 9/30 (30%) | 20pp |
| 3d      | 1/10 (10%) | 2/10 (20%) | 4/10 (40%) | 7/30 (23%) | 30pp |
| 1w      | 3/10 (30%) | 3/10 (30%) | 4/10 (40%) | 10/30 (33%) | 10pp |
| 2w      | 1/10 (10%) | 1/10 (10%) | 3/10 (30%) | 5/30 (17%) | 20pp |
| 4w      | 1/10 (10%) | 4/10 (40%) | 2/10 (20%) | 7/30 (23%) | 30pp |
| 8w      | 2/10 (20%) | 1/9 (11%) | 2/9 (22%) | 5/28 (18%) | 11pp |
| 13w     | 3/9 (33%) | 0/8 (0%) | 2/8 (25%) | 5/25 (20%) | 33pp |

**GPT 5.1-codex-mini:**

| Horizon | 10th (n=10) | 20th (n=10) | EoM (n=10) | All (n=30) | Spread |
|---------|:-----------:|:-----------:|:----------:|:----------:|:------:|
| 1d      | 2/10 (20%) | 5/10 (50%) | 1/10 (10%) | 8/30 (27%) | 40pp |
| 3d      | 1/10 (10%) | 3/10 (30%) | 4/10 (40%) | 8/30 (27%) | 30pp |
| 1w      | 2/10 (20%) | 5/10 (50%) | 6/10 (60%) | 13/30 (43%) | 40pp |
| 2w      | 4/10 (40%) | 5/10 (50%) | 3/10 (30%) | 12/30 (40%) | 20pp |
| 4w      | 4/10 (40%) | 3/10 (30%) | 4/10 (40%) | 11/30 (37%) | 10pp |
| 8w      | 4/10 (40%) | 5/9 (56%) | 3/9 (33%) | 12/28 (43%) | 22pp |
| 13w     | 3/9 (33%) | 3/8 (38%) | 1/8 (12%) | 7/25 (28%) | 25pp |

**Key observation:** Both models show 20-40pp spreads between date groups at every horizon. This means accuracy is not stable — it fluctuates wildly depending on which day of the month the model is asked. This is the signature of noise, not signal.

### Decision Distribution: Sonnet's SELL Bias Returns

| Model | Date Group | BUY | SELL | HOLD |
|-------|:----------:|:---:|:----:|:----:|
| Sonnet | 10th | 10% | 40% | 50% |
| Sonnet | 20th | **0%** | **50%** | 50% |
| Sonnet | EoM | 20% | 30% | 50% |
| Sonnet | **ALL** | **10%** | **40%** | **50%** |
| GPT | 10th | 50% | 10% | 40% |
| GPT | 20th | 50% | 30% | 20% |
| GPT | EoM | 40% | 20% | 40% |
| GPT | **ALL** | **47%** | **20%** | **33%** |

Sonnet has a persistent **SELL bias** (40% SELL vs 10% BUY overall). On the 20th of each month, it never once called BUY. The "balanced" 30/30/40 distribution from the end-of-month run was not representative — it was the most balanced of the three date groups.

GPT maintains a consistent BUY-heavy distribution (~47% BUY) across all date groups.

### P&L by Date Group

| Model | 10th | 20th | EoM | Total |
|-------|:----:|:----:|:---:|:-----:|
| Sonnet | **-$1,293** | -$119 | +$538 | **-$875** |
| GPT | +$277 | **+$565** | -$374 | **+$468** |

Sonnet's P&L is entirely dependent on date selection. End-of-month is the only profitable date group (+$538), while 10th-of-month loses $1,293. The Oct 10 SELL call at 0.78 confidence (the highest confidence trade in the entire dataset) lost $1,122 alone — proving that even maximum confidence doesn't predict accuracy.

### Holding Power Analysis

**This is the critical test: if a model gets the 1d direction right, does the call "hold" at longer horizons?**

**GPT — If correct at 1d, still correct at:**

| 3d | 1w | 2w | 4w | 8w | 13w |
|:--:|:--:|:--:|:--:|:--:|:---:|
| 5/8 (62%) | 4/8 (50%) | 4/8 (50%) | 4/8 (50%) | 5/8 (62%) | 3/7 (43%) |

**Sonnet — If correct at 1d, still correct at:**

| 3d | 1w | 2w | 4w | 8w | 13w |
|:--:|:--:|:--:|:--:|:--:|:---:|
| 5/9 (56%) | 2/9 (22%) | 1/9 (11%) | 1/9 (11%) | 1/9 (11%) | 2/8 (25%) |

**Sonnet has no holding power.** When it gets the 1d call right, only 11% of those calls are still correct at 2w or 4w. Its correct 1d predictions rapidly reverse. By contrast, GPT's correct 1d calls maintain 50% accuracy out to 4 weeks — not great, but meaningfully better than Sonnet.

**If WRONG at 1d, how often correct later?**

- **GPT** wrong at 1d (n=22): eventually correct at 1w in 41% of cases
- **Sonnet** wrong at 1d (n=21): eventually correct at 1w in 38% of cases

Both models show similar "recovery" rates, suggesting the longer-horizon accuracy is more a function of AMBA's price trajectory than model intelligence.

### HOLD Is Almost Always Wrong

For trades where each model called HOLD, what would have been the right call?

**Sonnet's 15 HOLD trades:**

| Horizon | BUY would win | SELL would win | HOLD correct | HOLD wrong |
|---------|:-------------:|:--------------:|:------------:|:----------:|
| 1d      | 47% | 40% | **13%** | 87% |
| 1w      | 33% | 47% | **20%** | 80% |
| 4w      | 13% | 67% | **20%** | 80% |
| 13w     | 67% | 33% | **0%** | 100% |

HOLD is correct only 0-20% of the time. AMBA is too volatile for HOLD to be a rational decision at any horizon. Sonnet's 50% HOLD rate structurally costs it P&L — every HOLD is a missed directional opportunity.

### Directional Trades Only: Sonnet's Edge Appears

When filtering to **directional trades only** (excluding HOLDs):

| Model | n | 1d | 3d | 1w | 2w | 4w |
|-------|:-:|:--:|:--:|:--:|:--:|:--:|
| Sonnet | 15 | **46.7%** | **46.7%** | **46.7%** | 33.3% | 26.7% |
| GPT | 20 | 35.0% | 40.0% | **55.0%** | **60.0%** | **55.0%** |

When Sonnet actually commits to a direction, it's 46.7% accurate at 1d — close to random but better than GPT's 35%. However, GPT dominates 1w–4w with 55-60% accuracy on directional trades.

### LLM Consistency: Same Data, Different Decisions

Comparing end-of-month decisions between this run and the previous V5 run (identical cached data):

| Model | Same Decision | Different | Consistency |
|-------|:------------:|:---------:|:-----------:|
| GPT 5.1-codex-mini | 8/10 | 2/10 | **80%** |
| Sonnet 4.5 | 5/10 | **5/10** | **50%** |

**Sonnet is essentially flipping a coin on half its EoM dates.** Given the exact same market data, Sonnet changed its decision on 5/10 dates (Mar, Aug, Sep, Nov, Dec). This non-determinism directly explains how the same model can show 60% accuracy on one run and 40% on another.

GPT is more consistent (80%) — but its consistent decisions are often wrong, so consistency alone doesn't create alpha.

### Always-BUY Comparison by Date Group

| Date Group | Horizon | Always-BUY | Sonnet | GPT | Sonnet vs BUY | GPT vs BUY |
|------------|---------|:----------:|:------:|:---:|:-------------:|:----------:|
| 10th | 1d | 40% | 30% | 20% | -10pp | -20pp |
| 10th | 13w | 67% | 33% | 33% | -33pp | -33pp |
| 20th | 1d | 50% | 20% | 50% | -30pp | +0pp |
| 20th | 13w | 75% | 0% | 38% | **-75pp** | -38pp |
| EoM | 1d | 50% | 40% | 10% | -10pp | -40pp |
| EoM | 13w | 62% | 25% | 12% | -38pp | -50pp |

**No model beats Always-BUY in any date group at any horizon.** The closest is GPT matching Always-BUY at 20th/1d (50% vs 50%). Sonnet at 20th/13w is 0% accurate — 75pp behind Always-BUY.

### Confidence Calibration (n=30)

**Sonnet:**

| Confidence | n | 1d Accuracy | Avg P&L |
|------------|:-:|:-----------:|:-------:|
| Medium (0.4-0.6) | 3 | 1/3 (33%) | +$62 |
| High (0.6-0.75) | 23 | 7/23 (30%) | +$7 |
| Very High (≥ 0.75) | 4 | 1/4 (**25%**) | **-$307** |

Sonnet's highest-confidence bucket (≥0.75) has the **worst accuracy (25%) and worst P&L (-$307)**. Confidence is inversely correlated with accuracy. The Oct 10 SELL at 0.78 (losing $1,122) is the clearest example: maximum confidence, maximum loss.

**GPT:**

| Confidence | n | 1d Accuracy | Avg P&L |
|------------|:-:|:-----------:|:-------:|
| Low (< 0.4) | 8 | 2/8 (25%) | +$58 |
| Medium (0.4-0.6) | 17 | 5/17 (29%) | +$20 |
| High (0.6-0.75) | 3 | 1/3 (33%) | -$115 |

GPT's confidence signal is flat — all buckets are 25-33%. No filtering possible.

### Verdict

**The V5 prompt framework does not generate consistent trading alpha on AMBA.** This conclusion holds across all 30 data points, 7 horizons, and both models:

1. **Sonnet's 60% accuracy was a 10-point fluke.** The same model on the same EoM dates only reproduces 50% of its original decisions. On 30 dates, accuracy drops to 30%. P&L goes from +$995 to -$875.

2. **Neither model beats Always-BUY.** At n=30, both models underperform the simplest possible baseline across all date groups and almost all horizons.

3. **Accuracy is highly date-dependent** (20-40pp spreads between date groups). This proves the models are not responding to stable market features — they are producing pseudo-random outputs that happen to align with market moves on some dates but not others.

4. **Sonnet has zero holding power.** Only 11% of correct 1d calls remain correct at 2w+. This means even when the model is "right," it's right for the wrong reasons — the market just happened to go the same direction.

5. **GPT shows weak medium-term holding power** (50% at 4w, 43% at 13w) — marginally better than random, but on only n=8 correct 1d calls. Not enough to be actionable.

6. **HOLD is almost always wrong on volatile stocks.** Both models waste 33-50% of their trades on HOLD, which is correct 0-20% of the time on AMBA. Future work should either eliminate HOLD or set much higher thresholds.

7. **LLM non-determinism is a fundamental barrier.** Sonnet gives different decisions 50% of the time on identical data. Any "alpha" is inseparable from run-to-run randomness.

---

## Recommendations (Updated Post Tri-Monthly Analysis)

1. **Do not deploy the current V5 single-agent system for live trading** — at n=30, no model shows statistically significant edge over Always-BUY at any horizon
2. **The 10-point end-of-month benchmark was misleading** — future evaluations must use at least 30+ data points per model, ideally across multiple tickers, to distinguish signal from noise
3. **Eliminate HOLD on high-volatility stocks** — AMBA's daily moves exceed HOLD thresholds 80-90% of the time; forcing BUY/SELL would at least remove the structural drag
4. **Investigate determinism** — Sonnet's 50% decision consistency on identical data is a fundamental problem; consider temperature=0, structured outputs, or seed parameters to reduce randomness
5. **GPT's medium-term directional accuracy (55-60% on 1w-4w, directional trades only)** warrants further investigation — filter out HOLD trades and test on a wider ticker set
6. **Consider multi-ticker benchmarks (V6)** — the V3 result (440 tasks, 10 tickers, no alpha) already suggested this; the tri-monthly analysis confirms it for AMBA specifically
7. **Focus on the prompt, not the model** — both Sonnet and GPT show the same fundamental inability to predict next-day moves; the issue is likely the input data quality or decision framework, not model capability
8. **Test with real-time indicators** — the current pipeline uses end-of-day data; intraday signals (volume profile, order flow) might provide genuinely predictive features

---

## Limitations

- **Single ticker (AMBA)** — a volatile semiconductor stock; performance could differ on stable large-caps or defensive sectors
- **V4 was a smoke test only** — 10 tickers, 1 date, Haiku only; no formal V4 benchmark with Sonnet/GPT exists
- **V5 Haiku and V5 Sonnet/GPT were separate runs** — same data (cache hit), but different run IDs
- **Cost estimates are approximate** — token usage was not tracked; costs based on per-task model averages
- **No multi-agent comparison in V5** — V2 showed multi-agent has 100% HOLD bias; not re-tested with V5 prompt
- **Walk-forward P2 has only 4 data points** — Sonnet's 75% P2 accuracy (3/4) was likely noise (confirmed by tri-monthly analysis)
- **Tri-monthly analysis confirms n=10 was insufficient** — the 30-point expansion reversed the primary conclusion from "alpha found" to "no alpha"
- **LLM non-determinism** — Sonnet produces different decisions 50% of the time on identical inputs; any single run is a coin flip

---

## Run Inventory

| Run ID | Date | Models | Period | Tasks | Completed |
|--------|------|--------|--------|:-----:|:---------:|
| v2_20260211_021106 | 2026-02-11 | 4 models (V3) | Mar 2025-Jan 2026 | 440 | 440 |
| v2_20260214_042556 | 2026-02-14 | Haiku 4.5 (V5) | Mar-Dec 2025 | 10 | 10 |
| v2_20260214_132347 | 2026-02-14 | Sonnet 4.5 + GPT 5.1-codex-mini (V5 EoM) | Mar-Dec 2025 | 20 | 20 |
| v2_20260214_193006 | 2026-02-14 | Sonnet 4.5 + GPT 5.1-codex-mini (V5 tri-monthly) | Mar-Dec 2025 | 60 | 60 |

### Run Files

| Run | Checkpoint | Outcomes | Report |
|-----|-----------|----------|--------|
| V3 (v2_20260211_021106) | [checkpoint](../../results/evaluations/backtest_v2_20260211_021106/checkpoint.json) | [outcomes](../../results/evaluations/backtest_v2_20260211_021106/outcomes.json) | [V3 Benchmark](V3_BENCHMARK_2026-02-11_10-TICKERS.md) |
| V5 Haiku (v2_20260214_042556) | [checkpoint](../../results/evaluations/backtest_v2_20260214_042556/checkpoint.json) | [outcomes](../../results/evaluations/backtest_v2_20260214_042556/outcomes.json) | — |
| V5 EoM (v2_20260214_132347) | [checkpoint](../../results/evaluations/backtest_v2_20260214_132347/checkpoint.json) | [outcomes](../../results/evaluations/backtest_v2_20260214_132347/outcomes.json) | — |
| V5 Tri-Monthly (v2_20260214_193006) | [checkpoint](../../results/evaluations/backtest_v2_20260214_193006/checkpoint.json) | [outcomes](../../results/evaluations/backtest_v2_20260214_193006/outcomes.json) | [V5 Tri-Monthly Report](V2_BENCHMARK_2026-02-14_AMBA.md) |

### Prior Benchmark References

| Report | Date | Scope |
|--------|------|-------|
| [V2 Comprehensive](V2_COMPREHENSIVE_RESULTS_2026-02-02.md) | 2026-02-02 | AMBA Jan-Apr 2025, Opus vs OpenAI, single vs multi-agent |
| [V3 10-Ticker](V3_BENCHMARK_2026-02-11_10-TICKERS.md) | 2026-02-11 | 10 tickers, 4 models, 440 tasks |

### Resume / Extend Commands

```bash
# Run V5 Sonnet on 10 tickers (V6 full benchmark)
python -m cli.evaluate_v2 \
    --tickers AAPL,MSFT,NVDA,AMBA,JNJ,XOM,JPM,COST,TSLA,NEE \
    --start 2025-03-01 --end 2025-12-31 \
    --strategies single_sonnet-4-5 \
    --multi-horizon --wait-on-rate-limit

# Compare V5 Sonnet vs V3 Sonnet
python -m cli.evaluate_v2 --compare v2_20260214_132347 v2_20260211_021106
```

---

*Generated 2026-02-14, updated with tri-monthly analysis (v2_20260214_193006). All P&L figures are simulated with $10,000 portfolio, $15 commission per trade. V5 prompt includes SPY market context, sector ETF context (AMBA→SMH), and systematic/idiosyncratic risk decision framework. Total evaluation: 90 tasks across 3 runs (10 Haiku EoM + 20 Sonnet/GPT EoM + 60 Sonnet/GPT tri-monthly).*

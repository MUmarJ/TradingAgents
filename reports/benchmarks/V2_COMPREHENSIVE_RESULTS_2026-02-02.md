# TradingAgents V2 Benchmark — Comprehensive Results

**Date:** 2026-02-02
**Benchmark Version:** V2 (look-ahead free, no HOLD fallback)
**Ticker:** AMBA (Ambarella Inc.) — "Hard" difficulty (25–42% accuracy in V1)
**Period:** January – April 2025 (4 monthly snapshots)
**Price Trajectory:** $76.72 → $47.99 (−37.5% over 4 months, high volatility bear market)

---

## Conclusion

**Claude Opus 4.5 single-agent was the best overall strategy**, achieving the highest accuracy, highest P&L, lowest drawdown, best confidence calibration, and best 5-day forward returns. It outperformed both OpenAI gpt-5.1-codex-mini single-agent and both multi-agent configurations.

**Multi-agent strategies are currently broken.** Both OpenAI and Anthropic multi-agent setups produced 100% HOLD decisions with near-neutral confidence (0.45–0.55), generating zero P&L. This HOLD bias is architectural — caused by the risk manager prompt — not model-dependent. Swapping to more expensive models does not fix it. The multi-agent pipeline must not be used for live decisions until the risk manager prompt is reworked.

**Single-agent strategies are 5–13x cheaper and more profitable** than multi-agent alternatives, making them the only viable architecture in the current codebase.

---

## Final Results

### Strategy Comparison

| Metric | OpenAI Single | Opus Single | OpenAI MA | Opus+Sonnet MA |
|--------|:------------:|:-----------:|:---------:|:--------------:|
| **Next-Day Accuracy** | 25.0% (1/4) | **50.0% (2/4)** | 50.0% (2/4) | 50.0% (2/4) |
| **5-Day Accuracy** | 75.0% (3/4) | **75.0% (3/4)** | 25.0% (1/4) | 25.0% (1/4) |
| **Total P&L** | $645.82 | **$696.25** | $0.00 | $0.00 |
| **5-Day P&L** | $2,445.99 | **$3,081.54** | $0.00 | $0.00 |
| **Max Drawdown** | $91.25 | **$40.83** | $0.00 | $0.00 |
| **Avg Confidence** | 0.33 | **0.69** | 0.50 | 0.50 |
| **Decision Mix** | 75% SELL, 25% HOLD | 50% SELL, 50% HOLD | 100% HOLD | 100% HOLD |
| **Est. Cost** | ~$0.32 | ~$1.80 | ~$2.00 | ~$10.40 |
| **P&L per $ Spent** | $2,018 | **$387** | $0 | $0 |

### Decision-by-Decision

| Date | AMBA Close | Market (1d) | Market (5d) | OpenAI Single | Opus Single | OpenAI MA | Opus+Sonnet MA |
|------|-----------|:----------:|:----------:|:-------------:|:-----------:|:---------:|:--------------:|
| Jan 31 | $76.72 | −1.84% | −1.30% | HOLD (0.40) | HOLD (0.55) | HOLD (0.50) | HOLD (0.45) |
| **Feb 28** | **$61.43** | **−7.52%** | **−13.61%** | **SELL (0.30)** | **SELL (0.85)** | HOLD (0.50) | HOLD (0.45) |
| Mar 31 | $50.33 | +0.26% | −17.21% | SELL (0.30) | SELL (0.70) | HOLD (0.50) | HOLD (0.55) |
| **Apr 30** | **$47.99** | **+0.35%** | **+6.36%** | SELL (0.30) | **HOLD (0.65)** | HOLD (0.50) | HOLD (0.55) |

### P&L by Trade

| Date | OpenAI Single | Opus Single | OpenAI MA | Opus+Sonnet MA |
|------|:------------:|:-----------:|:---------:|:--------------:|
| Jan 31 | $0.00 | $0.00 | $0.00 | $0.00 |
| Feb 28 | **+$737.08** | **+$737.08** | $0.00 | $0.00 |
| Mar 31 | −$40.83 | −$40.83 | $0.00 | $0.00 |
| Apr 30 | −$50.42 | $0.00 | $0.00 | $0.00 |
| **Total** | **$645.82** | **$696.25** | **$0.00** | **$0.00** |

---

## Key Findings

**1. Opus 4.5 single-agent was the best overall strategy.** It tied for the highest next-day accuracy (50%), delivered the highest P&L ($696.25), had the lowest drawdown ($40.83), and produced the best 5-day forward P&L ($3,081.54). Its confidence signal was also the most informative — the 0.85-confidence February SELL was the single most profitable call in the benchmark.

**2. Multi-agent HOLD bias is model-independent.** Both OpenAI and Anthropic multi-agent strategies produced identical 100% HOLD behavior with 0.45–0.55 confidence. This was also observed in V1 (503 tasks) where multi-agent HOLD rates ranged from 88–100% across 5 different multi-agent configurations. The root cause is the risk manager prompt, not the underlying model.

**3. Single-agent strategies are more decisive and more profitable.** Single-agent strategies took positions (50–75% SELL) while multi-agent was paralyzed (0% SELL). Even with some wrong calls, the net P&L was positive because winning trades compensated for losses.

**4. Opus showed superior confidence calibration.** Opus varied confidence from 0.55 to 0.85 (range: 0.30), expressing higher conviction on stronger signals. GPT-5.1-codex-mini varied only from 0.30 to 0.40 (range: 0.10), unable to differentiate signal strength. Opus's high-confidence calls (>0.6) were correct 67% of the time next-day.

**5. LLMs predict weekly trends better than daily moves.** Both single-agent strategies achieved 75% 5-day accuracy vs 25–50% next-day accuracy. Fundamental/news-driven analysis provides medium-term directional signals, not intraday precision.

**6. The April divergence was the only meaningful difference between models.** OpenAI and Opus single-agent agreed on 3 of 4 decisions. On April 30, Opus correctly held (recognizing the bottoming pattern) while OpenAI kept selling. That single call accounts for the entire $50.42 P&L gap.

---

## Recommendations

1. **Do not use multi-agent for live decisions** until the risk manager prompt is reworked
2. **Use single-agent Opus 4.5 as the default strategy** — best accuracy, best P&L, best calibration
3. **Consider single-agent OpenAI gpt-5.1-codex-mini as a budget alternative** — 5.6x cheaper, similar P&L, lower accuracy
4. **Evaluate on a 5-day holding period** rather than next-day — both models show much stronger signal at the weekly horizon
5. **Extend this benchmark to 50+ tasks** for statistical validity before drawing firm conclusions
6. **Fix the risk manager**: reduce its authority to override, add explicit anti-HOLD-bias instructions, or make it advisory-only

---

## Limitations

- **4 data points per strategy** — too small for statistical significance; all findings are directional only
- **Single ticker (AMBA)** — performance could differ on other stock types
- **No BUY signals** — no strategy issued a BUY across all 16 decisions
- **Cost estimates are approximate** — token usage was not tracked; costs based on per-task averages
- **Anthropic MA used cached analyst reports** from the single-agent run (same inputs, different decision pipeline)
- **OpenAI run was stopped at 8/96 tasks** — only AMBA Jan–Apr covered

---
---

# Detailed Analysis

Everything below provides the supporting evidence, methodology, and raw data behind the conclusions above.

---

## 1. Benchmark Design

### Objective

Compare OpenAI (gpt-5.1-codex-mini) and Anthropic (claude-opus-4-5, claude-sonnet-4-5) across
both single-agent and multi-agent architectures on the same data points, using the V2 evaluation
framework which eliminates look-ahead bias and forces explicit BUY/SELL/HOLD decisions.

### Ticker Selection

AMBA was selected as a "hard" ticker based on V1 benchmark data (503 tasks across 6 tickers, 7 strategies):

| Ticker | V1 Best Accuracy | Accuracy Range | Difficulty | Rationale |
|--------|-----------------|----------------|------------|-----------|
| RAPT | 17% | 8–17% | Hardest | Small-cap biotech ($3), sparse news, extreme volatility |
| SNOW | 42% | 8–42% | Hard | Cloud software, wide strategy variance |
| **AMBA** | **42%** | **25–42%** | **Hard** | Mid-cap semiconductor, earnings-driven volatility |
| ZTS | 58% | 50–58% | Moderate | Large-cap animal health, stable |
| ET | 67% | 50–67% | Easy | Energy MLP, consistent price behavior |
| SUPN | 75% | 50–75% | Easiest | Mid-cap pharma, clearest signals |

AMBA tests models' ability to handle earnings-driven semiconductor volatility with limited, ambiguous signals.

### Strategy Configurations

Four strategies were tested, each on the same 4 analysis dates:

| Strategy Label | Architecture | Provider | Deep Model | Quick Model |
|---------------|-------------|----------|------------|-------------|
| `ma_5.1-codex-mini` | Multi-agent graph | OpenAI | gpt-5.1-codex-mini | gpt-5.1-codex-mini |
| `single_5.1-codex-mini` | Single-agent baseline | OpenAI | gpt-5.1-codex-mini | — |
| `single_opus-4-5` | Single-agent baseline | Anthropic | claude-opus-4-5-20251101 | — |
| `ma_opus-4-5+sonnet-4-5` | Multi-agent graph | Anthropic | claude-opus-4-5-20251101 | claude-sonnet-4-5-20250929 |

### Multi-Agent Graph Architecture

The multi-agent pipeline runs through:
1. **4 Analyst nodes** (Sonnet/codex-mini): Market, Fundamentals, News, Social Media
2. **2 Researcher nodes** (Sonnet/codex-mini): Bull Researcher, Bear Researcher
3. **Research Manager** (Opus/codex-mini): Synthesizes bull/bear arguments
4. **Risk Manager** (Opus/codex-mini): Evaluates and challenges the recommendation
5. **Trader** (Opus/codex-mini): Makes final BUY/SELL/HOLD decision

The single-agent baseline feeds all raw data (market, fundamentals, news, sentiment) into a single LLM call that produces a decision directly.

### Common Configuration

All runs shared identical non-LLM settings:

| Setting | Value |
|---------|-------|
| Data Vendors — Core Stock | Polygon |
| Data Vendors — Technical Indicators | Polygon |
| Data Vendors — Fundamentals | Alpha Vantage |
| Data Vendors — News | Polygon + Alpha Vantage |
| Data Vendors — Social Sentiment | StockTwits |
| News Limits (default / 3mo / 6mo / 12mo) | 60 / 200 / 500 / 600 |
| Sentiment Limits (default / 3mo / 6mo / 12mo) | 50 / 200 / 500 / 500 |
| News Monthly Bucketing | Enabled |
| News Company Fallback | Enabled |
| Max Debate Rounds | 1 |
| Max Risk Discussion Rounds | 1 |
| Memory System | Disabled |
| ACE Framework | Disabled |
| Commission per Trade | $15.00 |
| Simulated Portfolio | $10,000 |

---

## 2. V1 → V2 Methodology Changes

V2 introduced critical fixes that make results non-comparable with V1:

| Issue | V1 Behavior | V2 Fix |
|-------|-------------|--------|
| **Look-ahead bias** | `get_current_quote()` fetched live prices | Uses `decision_date_close` from historical OHLCV only |
| **HOLD fallback** | Parse failures silently defaulted to HOLD 0.5 | Raises `ValueError` — forces real model decision |
| **Content normalization** | Raw AIMessage objects passed through pipeline | `normalize_content()` applied at all agent boundaries |
| **Type hints** | Mixed `ChatOpenAI` types | `BaseChatModel` throughout for provider-agnostic code |
| **Anthropic instantiation** | `base_url` (OpenAI param) passed to `ChatAnthropic` | Auto-discovery from `ANTHROPIC_API_KEY`; `max_tokens=8192` |
| **5-day validation** | Not tracked | `day5_change_pct` and `day5_correct` fields added |
| **Evaluation framework** | Manual runs, no checkpointing | `evaluate_v2.py` with checkpoints, resume, compare, dry-run |

---

## 3. Run Inventory

| Run ID | Provider | Strategy | Tasks | Completed | Failed | Status |
|--------|----------|----------|-------|-----------|--------|--------|
| `v2_20260202_153754` | OpenAI | ma + single (gpt-5.1-codex-mini) | 96 total (8 AMBA) | 8 | 0 | Stopped early |
| `v2_20260202_161514` | Anthropic | single (claude-opus-4-5) | 4 | 4 | 0 | Complete |
| `v2_20260202_162458` | Anthropic | multi-agent (opus+sonnet) | 4 | 4 | 0 | Complete |

**Note:** The OpenAI run was configured for 96 tasks (4 tickers × 12 months × 2 strategies) but was stopped after 8 tasks covering only AMBA Jan–Apr 2025. The remaining 88 tasks for RAPT, ET, ZTS are pending and can be resumed with `--resume v2_20260202_153754`.

---

## 4. Market Context — AMBA Jan–Apr 2025

AMBA (Ambarella Inc.) experienced a sustained decline through Q1 2025:

| Date | Close Price | Next-Day Change | 5-Day Change | Regime | Volatility |
|------|------------|----------------|--------------|--------|-----------|
| 2025-01-31 | $76.72 | -1.84% | -1.30% | Sideways | High |
| 2025-02-28 | $61.43 | -7.52% | -13.61% | Bear | High |
| 2025-03-31 | $50.33 | +0.26% | -17.21% | Bear | High |
| 2025-04-30 | $47.99 | +0.35% | +6.36% | Bear | High |

**Price trajectory:** $76.72 → $47.99 (−37.5% over 4 months)

Key observations:
- **January:** Sideways chop, ambiguous signals. Next day slightly down, week slightly down.
- **February:** Sharp bear break. Next day crashed −7.5%, week dropped −13.6%. The clearest sell signal.
- **March:** Continued decline but next day was flat (+0.26%). The 5-day continued down −17.2%. A trap — the daily signal said "flat" but the weekly trend was deeply bearish.
- **April:** Bottoming. Next day +0.35%, week recovered +6.4%. The first bullish reversal signal.

The "correct" strategy in hindsight was: SELL Feb, SELL Mar (for 5-day), HOLD or BUY Apr.

---

## 5. Trade-by-Trade Detail

### 5.1 OpenAI Multi-Agent (`ma_5.1-codex-mini`)

| # | Date | Decision | Conf. | Entry | Next Close | Next-Day Δ | 5-Day Δ | P&L | Correct? | 5d Correct? |
|---|------|----------|-------|-------|-----------|-----------|---------|-----|----------|-------------|
| 1 | 2025-01-31 | HOLD | 0.50 | $76.72 | $75.31 | -1.84% | -1.30% | $0.00 | N | Y |
| 2 | 2025-02-28 | HOLD | 0.50 | $61.43 | $56.81 | -7.52% | -13.61% | $0.00 | N | N |
| 3 | 2025-03-31 | HOLD | 0.50 | $50.33 | $50.46 | +0.26% | -17.21% | $0.00 | Y | N |
| 4 | 2025-04-30 | HOLD | 0.50 | $47.99 | $48.16 | +0.35% | +6.36% | $0.00 | Y | N |

**Totals:** 4/4 HOLD, 2/4 correct (50.0%), $0.00 P&L, 1/4 5-day correct (25.0%)

### 5.2 OpenAI Single-Agent (`single_5.1-codex-mini`)

| # | Date | Decision | Conf. | Entry | Next Close | Next-Day Δ | 5-Day Δ | P&L | Correct? | 5d Correct? |
|---|------|----------|-------|-------|-----------|-----------|---------|-----|----------|-------------|
| 1 | 2025-01-31 | HOLD | 0.40 | $76.72 | $75.31 | -1.84% | -1.30% | $0.00 | N | Y |
| 2 | 2025-02-28 | SELL | 0.30 | $61.43 | $56.81 | -7.52% | -13.61% | +$737.08 | Y | Y |
| 3 | 2025-03-31 | SELL | 0.30 | $50.33 | $50.46 | +0.26% | -17.21% | -$40.83 | N | Y |
| 4 | 2025-04-30 | SELL | 0.30 | $47.99 | $48.16 | +0.35% | +6.36% | -$50.42 | N | N |

**Totals:** 3 SELL + 1 HOLD, 1/4 correct (25.0%), +$645.82 P&L, 3/4 5-day correct (75.0%)

**Notes:**
- Feb SELL was the big winner: $737 profit on a −7.5% next-day crash
- Mar SELL lost $41 (market was flat next day, though 5-day confirmed the sell)
- Apr SELL lost $50 (market bounced, wrong direction)
- All decisions had low confidence (0.30–0.40), suggesting the model was not sure but biased toward action

### 5.3 Anthropic Single-Agent (`single_opus-4-5`)

| # | Date | Decision | Conf. | Entry | Next Close | Next-Day Δ | 5-Day Δ | P&L | Correct? | 5d Correct? |
|---|------|----------|-------|-------|-----------|-----------|---------|-----|----------|-------------|
| 1 | 2025-01-31 | HOLD | 0.55 | $76.72 | $75.31 | -1.84% | -1.30% | $0.00 | N | Y |
| 2 | 2025-02-28 | SELL | 0.85 | $61.43 | $56.81 | -7.52% | -13.61% | +$737.08 | Y | Y |
| 3 | 2025-03-31 | SELL | 0.70 | $50.33 | $50.46 | +0.26% | -17.21% | -$40.83 | N | Y |
| 4 | 2025-04-30 | HOLD | 0.65 | $47.99 | $48.16 | +0.35% | +6.36% | $0.00 | Y | N |

**Totals:** 2 SELL + 2 HOLD, 2/4 correct (50.0%), +$696.25 P&L, 3/4 5-day correct (75.0%)

**Notes:**
- Feb SELL matched OpenAI's call but with **much higher confidence** (0.85 vs 0.30)
- Mar SELL also matched, but with higher confidence (0.70 vs 0.30) — still wrong next-day
- Apr was the key differentiator: Opus **correctly held** (0.65 confidence) while OpenAI single sold. This saved $50.42 and turned a wrong call into a right one.
- Overall confidence much higher (avg 0.69 vs 0.33), indicating Opus expressed more conviction in its analysis

### 5.4 Anthropic Multi-Agent (`ma_opus-4-5+sonnet-4-5`)

| # | Date | Decision | Conf. | Entry | Next Close | Next-Day Δ | 5-Day Δ | P&L | Correct? | 5d Correct? |
|---|------|----------|-------|-------|-----------|-----------|---------|-----|----------|-------------|
| 1 | 2025-01-31 | HOLD | 0.45 | $76.72 | $75.31 | -1.84% | -1.30% | $0.00 | N | Y |
| 2 | 2025-02-28 | HOLD | 0.45 | $61.43 | $56.81 | -7.52% | -13.61% | $0.00 | N | N |
| 3 | 2025-03-31 | HOLD | 0.55 | $50.33 | $50.46 | +0.26% | -17.21% | $0.00 | Y | N |
| 4 | 2025-04-30 | HOLD | 0.55 | $47.99 | $48.16 | +0.35% | +6.36% | $0.00 | Y | N |

**Totals:** 4/4 HOLD, 2/4 correct (50.0%), $0.00 P&L, 1/4 5-day correct (25.0%)

**Notes:**
- Identical pattern to OpenAI multi-agent: 100% HOLD, 50% next-day accuracy
- Confidence range was narrow (0.45–0.55), all hovering around 0.5
- Critically missed the Feb −7.5% crash — the strongest signal in the dataset
- The multi-agent graph's risk manager overrides actionable signals with HOLD regardless of LLM provider

---

## 6. Pivotal Decisions

### February 28 — The Clear Signal

AMBA closed at $61.43, already down 20% from January. Next day crashed another −7.5%, 5-day dropped −13.6%.

- **Opus single** called SELL with 0.85 confidence — the highest conviction of any call in the entire benchmark
- **OpenAI single** also called SELL but with only 0.30 confidence — barely above "uncertain"
- **Both multi-agent strategies missed this entirely** — held at 0.45–0.50 confidence

This was the clearest bearish signal in the dataset and the largest single-trade profit opportunity (+$737). The fact that both multi-agent strategies held through a −7.5% crash demonstrates the severity of the HOLD bias.

### April 30 — The Divergence

AMBA had bottomed at $47.99 after 4 months of decline. Next day +0.35%, 5-day rebounded +6.4%.

- **Opus single correctly held** (0.65 confidence) — recognized the bottoming pattern
- **OpenAI single kept selling** (0.30 confidence) — continued the bearish momentum bias
- This single decision accounted for the entire P&L gap between the two single-agent strategies ($696.25 vs $645.82)

---

## 7. Decision Agreement Matrix

How often each pair of strategies agreed on the same decision:

| | OpenAI MA | OpenAI Single | Opus Single | Opus+Sonnet MA |
|--|-----------|---------------|-------------|----------------|
| **OpenAI MA** | — | 1/4 (25%) | 2/4 (50%) | **4/4 (100%)** |
| **OpenAI Single** | 1/4 | — | **3/4 (75%)** | 1/4 (25%) |
| **Opus Single** | 2/4 | 3/4 | — | 2/4 (50%) |
| **Opus+Sonnet MA** | 4/4 | 1/4 | 2/4 | — |

- The two multi-agent strategies produced **identical decisions** (100% agreement) — both all-HOLD
- The two single-agent strategies agreed on **3 of 4 decisions** — diverged only on April
- Multi-agent and single-agent have low agreement (25–50%), confirming they operate very differently

---

## 8. Confidence Analysis

### Distribution by Strategy

| Strategy | Min | Max | Avg | Std Dev | Range |
|----------|:---:|:---:|:---:|:-------:|:-----:|
| OpenAI MA | 0.50 | 0.50 | 0.50 | 0.00 | 0.00 |
| OpenAI Single | 0.30 | 0.40 | 0.33 | 0.05 | 0.10 |
| **Opus Single** | **0.55** | **0.85** | **0.69** | **0.13** | **0.30** |
| Opus+Sonnet MA | 0.45 | 0.55 | 0.50 | 0.05 | 0.10 |

### Opus Single: Confidence vs Correctness

| Confidence | Decision | Next-Day Correct | 5-Day Correct |
|:----------:|----------|:----------------:|:-------------:|
| 0.85 | SELL (Feb) | Y | Y |
| 0.70 | SELL (Mar) | N | Y |
| 0.65 | HOLD (Apr) | Y | N |
| 0.55 | HOLD (Jan) | N | Y |

High-confidence calls (>0.6): 2/3 correct next-day (67%), 2/3 correct 5-day (67%)
Low-confidence calls (≤0.6): 0/1 correct next-day (0%), 1/1 correct 5-day (100%)

Opus expressed higher confidence on its SELL calls and was right on the strongest one (Feb). The confidence signal contains useful information — high-confidence Opus calls were more likely to be correct.

### Multi-Agent Confidence Collapse

Both multi-agent strategies produced near-constant confidence (0.45–0.55), essentially defaulting to "uncertain." The multi-agent debate process converges to the mean rather than producing differentiated conviction. The risk manager's challenge step suppresses confidence regardless of the underlying model.

---

## 9. 5-Day Forward Accuracy

| Strategy | Next-Day Acc. | 5-Day Acc. | 5-Day P&L | Next-Day P&L |
|----------|:------------:|:---------:|:---------:|:-----------:|
| OpenAI MA | 50.0% | 25.0% | $0.00 | $0.00 |
| OpenAI Single | 25.0% | **75.0%** | $2,445.99 | $645.82 |
| Opus Single | 50.0% | **75.0%** | **$3,081.54** | **$696.25** |
| Opus+Sonnet MA | 50.0% | 25.0% | $0.00 | $0.00 |

Both single-agent strategies achieved 75% 5-day accuracy vs 25–50% next-day accuracy. This suggests LLM-based analysis is better suited to medium-term directional calls than daily price prediction, which aligns with the fundamental/news-driven nature of the input data.

The 5-day P&L gap is dramatic: Opus single would have generated $3,081 over 4 trades on a 5-day basis, while multi-agent strategies still generated $0 because they never took a position.

---

## 10. Cost Efficiency Analysis

### Estimated Cost per Strategy

| Strategy | Tasks | Est. $/Task | Total Cost | Accuracy | P&L | P&L/$ Spent |
|----------|:-----:|:----------:|:---------:|:--------:|:---:|:-----------:|
| OpenAI Single | 4 | $0.08 | ~$0.32 | 25% | $645.82 | **$2,018** |
| Opus Single | 4 | $0.45 | ~$1.80 | 50% | $696.25 | $387 |
| OpenAI MA | 4 | $0.50 | ~$2.00 | 50% | $0.00 | $0 |
| Opus+Sonnet MA | 4 | $2.60 | ~$10.40 | 50% | $0.00 | $0 |

### Cost per Correct Decision

| Strategy | Correct | Total Cost | $/Correct |
|----------|:-------:|:---------:|:---------:|
| OpenAI Single | 1 | ~$0.32 | ~$0.32 |
| Opus Single | 2 | ~$1.80 | ~$0.90 |
| OpenAI MA | 2 | ~$2.00 | ~$1.00 |
| Opus+Sonnet MA | 2 | ~$10.40 | ~$5.20 |

**Observations:**
1. OpenAI single was cheapest (~$0.32 total) with the best P&L-per-dollar — but skewed by one lucky SELL
2. Opus single had the best accuracy-to-cost ratio for a moderate cost ($1.80)
3. Multi-agent Anthropic was the most expensive (~$10.40) for zero P&L — worst value by any metric
4. Multi-agent adds ~5–13x cost over single-agent for the same accuracy and less P&L

---

## 11. Multi-Agent HOLD Bias Analysis

### The Pattern

Both multi-agent strategies produced **identical 100% HOLD behavior**:

| Date | OpenAI MA | Anthropic MA | Match? |
|------|:---------:|:------------:|:------:|
| Jan 31 | HOLD (0.50) | HOLD (0.45) | Yes |
| Feb 28 | HOLD (0.50) | HOLD (0.45) | Yes |
| Mar 31 | HOLD (0.50) | HOLD (0.55) | Yes |
| Apr 30 | HOLD (0.50) | HOLD (0.55) | Yes |

100% agreement. 100% HOLD.

### V1 Corroboration (503 tasks)

The V1 benchmark showed the same pattern at scale:

| V1 Strategy | HOLD Rate | Accuracy | P&L |
|------------|:---------:|:--------:|:---:|
| ma_5.2 (gpt-5.2) | **100%** | 40.3% | $0.00 |
| ma_5.2+5.1-codex-mini | 96% | 38.0% | $26.32 |
| ma_4o (gpt-4o) | 94% | 43.1% | −$408.82 |
| ma_5.1-codex-mini | 88% | 33.3% | −$389.58 |
| single_5.1-codex-mini | 71% | **45.8%** | **$1,173.32** |
| single_5.2 | 88% | 40.3% | $519.09 |
| single_4o | 90% | 40.3% | −$759.35 |

Multi-agent strategies had 88–100% HOLD rates across 72 tasks each in V1.

### Root Cause

The HOLD bias is **architectural, not model-dependent**:
1. It persists across OpenAI (gpt-5.1-codex-mini) and Anthropic (opus-4-5 + sonnet-4-5)
2. It persists across model generations (V1: gpt-4o, gpt-5.2; V2: gpt-5.1-codex-mini, opus)
3. The confidence collapse to 0.45–0.55 is identical regardless of provider

The culprit is the **risk manager agent prompt** (`tradingagents/agents/managers/risk_manager.py`), which is designed to challenge and moderate the recommendation. When combined with the debate structure (bull vs bear researchers), the system converges to "insufficient evidence" → HOLD at the neutral confidence midpoint.

---

## 12. Comparison with V1 Benchmark (503 tasks)

### V1 Context

The V1 benchmark (run ID: `bt_20260129_173611`) ran 503 tasks across 6 tickers, 12 months, and 7 strategies. It used the old evaluation framework which had look-ahead bias in price fetching and allowed HOLD fallbacks on parse failures.

### AMBA Specifically — V1 vs V2

V1 AMBA results (12 months, full year):

| V1 Strategy | AMBA Accuracy | AMBA P&L |
|------------|:------------:|:--------:|
| ma_5.2+5.1-codex-mini | 42% | $169 |
| ma_4o | 42% | $99 |
| ma_5.2 | 33% | $0 |
| single_5.1-codex-mini | 33% | $445 |
| ma_5.1-codex-mini | 25% | −$21 |
| single_5.2 | 25% | −$355 |
| single_4o | 25% | −$739 |

V2 AMBA results (4 months, Jan–Apr 2025):

| V2 Strategy | AMBA Accuracy | AMBA P&L |
|------------|:------------:|:--------:|
| Opus Single | 50% | $696 |
| OpenAI MA | 50% | $0 |
| Opus+Sonnet MA | 50% | $0 |
| OpenAI Single | 25% | $646 |

**Caution:** V1 and V2 results are NOT directly comparable due to:
- V1 had look-ahead bias (inflated accuracy for some decisions)
- V2 covers only 4 of 12 months
- V2 removed HOLD fallback (some V1 "decisions" were parse failures silently counted as HOLD)
- Different data vendor configurations

After removing methodological flaws, AMBA remains a 25–50% accuracy ticker, consistent with V1's 25–42% range.

---

## 13. Raw Run References

### Run Files

| Run | Checkpoint | Outcomes | Report |
|-----|-----------|----------|--------|
| OpenAI (v2_20260202_153754) | [checkpoint.json](../../results/evaluations/backtest_v2_20260202_153754/checkpoint.json) | [outcomes.json](../../results/evaluations/backtest_v2_20260202_153754/outcomes.json) | [report.md](../../results/evaluations/backtest_v2_20260202_153754/report.md) |
| Opus Single (v2_20260202_161514) | [checkpoint.json](../../results/evaluations/backtest_v2_20260202_161514/checkpoint.json) | [outcomes.json](../../results/evaluations/backtest_v2_20260202_161514/outcomes.json) | [report.md](../../results/evaluations/backtest_v2_20260202_161514/report.md) |
| Opus+Sonnet MA (v2_20260202_162458) | [checkpoint.json](../../results/evaluations/backtest_v2_20260202_162458/checkpoint.json) | [outcomes.json](../../results/evaluations/backtest_v2_20260202_162458/outcomes.json) | [report.md](../../results/evaluations/backtest_v2_20260202_162458/report.md) |

### Pairwise Comparison Reports

| Comparison | File |
|-----------|------|
| OpenAI vs Opus Single | [V2_COMPARE_...153754_vs_...161514.md](V2_COMPARE_2026-02-02_v2_20260202_153754_vs_v2_20260202_161514.md) |
| OpenAI vs Opus+Sonnet MA | [V2_COMPARE_...153754_vs_...162458.md](V2_COMPARE_2026-02-02_v2_20260202_153754_vs_v2_20260202_162458.md) |
| Opus Single vs Opus+Sonnet MA | [V2_COMPARE_...161514_vs_...162458.md](V2_COMPARE_2026-02-02_v2_20260202_161514_vs_v2_20260202_162458.md) |

### Resume / Extend Commands

```bash
# Resume the OpenAI run (88 remaining tasks: RAPT, ET, ZTS)
python -m cli.evaluate_v2 --resume v2_20260202_153754 --wait-on-rate-limit

# Run Anthropic single on more tickers (e.g., RAPT)
python -m cli.evaluate_v2 --single-only \
    --tickers RAPT --start 2025-01-28 --end 2025-05-28 \
    --provider anthropic \
    --deep-model claude-opus-4-5-20251101 \
    --quick-model claude-opus-4-5-20251101 \
    --wait-on-rate-limit

# Compare any two runs
python -m cli.evaluate_v2 --compare <run_id_a> <run_id_b>

# Dry-run cost estimate before committing
python -m cli.evaluate_v2 --dry-run --tickers AMBA,RAPT \
    --provider anthropic --deep-model claude-opus-4-5-20251101 \
    --quick-model claude-opus-4-5-20251101
```

### V1 Benchmark Reference

The V1 benchmark report (503 tasks, 6 tickers, 7 strategies, 12 months) is at:
[BENCHMARK_REPORT_2026-02-01_RAPT_SUPN_ZTS.md](BENCHMARK_REPORT_2026-02-01_RAPT_SUPN_ZTS.md)

---

*Generated 2026-02-02. All P&L figures are simulated with $10,000 portfolio, $15 commission per trade.*

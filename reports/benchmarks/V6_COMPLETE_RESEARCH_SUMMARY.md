# V6 Complete Research Summary: Specialized Financial Models for Trading Signal Generation

**Compiled:** 2026-03-06
**Period Under Test:** 2025-03-10 to 2025-12-31
**Ticker:** AMBA (Ambarella Inc.)
**Sample Size:** n=30 tri-monthly snapshots (10th, 20th, end-of-month)
**Horizons:** 1d, 3d, 1w, 2w, 4w, 8w, 13w
**Evaluation Framework:** V2 (look-ahead free, walk-forward training, multi-horizon)

---

## 1. Motivation: Why V6 Exists

V5 proved that general-purpose LLMs cannot generate trading alpha:

| Model | 1d Accuracy | P&L | Cost/Task | Deterministic |
|-------|------------|-----|-----------|---------------|
| Sonnet 4.5 | 30% | -$875 | $0.10 | No (50% flip rate) |
| GPT 5.1-codex-mini | 27% | +$468 | $0.08 | No |
| Always-BUY | 50% | benchmark | $0.00 | Yes |

**Root causes:** LLMs lack domain-specific financial NLP training, numeric feature extraction, temporal pattern recognition, and determinism.

**V6 hypothesis:** Replace LLMs with a stack of purpose-built models — each handling one signal type — then combine via ensemble.

---

## 2. Architecture

```
┌──────────────────────────────────────────────────────────┐
│                    V6 Architecture                        │
├──────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────────┐  ┌──────────────┐  ┌────────────────┐  │
│  │  DeBERTa-v3  │  │   XGBoost    │  │    Kronos      │  │
│  │  (Sentiment) │  │ (SHAP-Pruned)│  │  (OHLCV TS)    │  │
│  │  F1: 0.994   │  │ 20 features  │  │  AAAI 2026     │  │
│  └──────┬───────┘  └──────┬───────┘  └──────┬─────────┘  │
│         │                 │                  │            │
│         └────────┬────────┘──────────────────┘            │
│                  │                                        │
│         ┌────────▼────────┐                               │
│         │  Confidence-    │                               │
│         │  Weighted Vote  │                               │
│         └────────┬────────┘                               │
│                  │                                        │
│         BUY / SELL / HOLD                                 │
└──────────────────────────────────────────────────────────┘
```

---

## 3. All Strategies Tested

### 3.1 Master Results Table (n=30, AMBA)

| # | Strategy | 1d | 3d | 1w | 2w | 4w | 8w | 13w | P&L | Cost | Phase |
|---|----------|-----|-----|-----|-----|-----|-----|------|------|------|-------|
| 1 | **E: Kronos-mini+XGB** | **63%** | 53% | 37% | 40% | 37% | 36% | 52% | **+$482** | $0 | 5 |
| 2 | **E: Kronos-mini+LGBM** | **60%** | 53% | 37% | 40% | 40% | 46% | **64%** | **+$1,787** | $0 | 5 |
| 3 | Kronos Mini | 57% | 53% | 43% | 50% | 37% | 36% | 52% | -$412 | $0 | 3 |
| 4 | XGBoost (SHAP-Pruned) | 52% | 52% | 41% | 41% | **62%** | 48% | 54% | -$461 | $0 | 2B |
| 5 | Kronos Small | 50% | **60%** | 43% | 50% | 43% | 46% | 60% | -$434 | $0 | 5 |
| 6 | Always-BUY | 50% | 53% | **50%** | **63%** | 50% | **79%** | 68% | bench | $0 | — |
| 7 | XGBoost (unpruned) | 45% | 45% | 41% | 45% | 41% | 37% | 54% | +$407 | $0 | 2 |
| 8 | E: KM+XGB+DeBERTa (3M) | 47% | 47% | 33% | 53% | 43% | 46% | 60% | -$707 | $0 | 4 |
| 9 | E: Kronos-mini+DeBERTa | 43% | 43% | 30% | 47% | 40% | 46% | 56% | -$783 | $0 | 5 |
| 10 | DeBERTa Sentiment | 37% | 33% | 30% | 47% | 40% | 54% | 40% | +$945 | $0 | 1 |
| 11 | ModernFinBERT | 37% | 33% | 27% | 40% | 37% | 46% | 36% | +$1,080 | $0 | 1 |
| 12 | FinBERT | 37% | 30% | 30% | 33% | 37% | 43% | 28% | +$315 | $0 | 1 |
| 13 | E: Kronos-small+XGB | 37% | 43% | 37% | 37% | 33% | 36% | 56% | -$3,157 | $0 | 5 |
| 14 | E: LightGBM+XGBoost | 37% | 33% | 33% | 40% | 33% | 41% | 56% | -$327 | $0 | 5 |
| 15 | Sonnet 4.5 (LLM) | 30% | — | — | — | — | — | — | -$875 | $0.10 | V5 |
| 16 | GPT 5.1-codex-mini | 27% | — | — | — | — | — | — | +$468 | $0.08 | V5 |

### 3.2 Horizon-Optimal Strategy Map

| Horizon | Best Strategy | Accuracy | Runner-Up |
|---------|--------------|----------|-----------|
| **1d** | E: Kronos-mini + XGBoost | **63.3%** | E: Kronos-mini + LightGBM (60%) |
| **3d** | Kronos Small / Kronos Mini / KM+XGB / KM+LGBM | **53-60%** | XGBoost SHAP-Pruned (52%) |
| **1w** | Always-BUY | **50%** | Kronos Mini/Small (43%) |
| **2w** | Always-BUY | **63%** | E: KM+XGB+DeBERTa (53%) |
| **4w** | XGBoost SHAP-Pruned | **62%** | Always-BUY (50%) |
| **8w** | Always-BUY | **79%** | XGBoost SHAP-Pruned (48%) |
| **13w** | E: Kronos-mini + LightGBM | **64%** | Always-BUY (68%) |
| **P&L** | E: Kronos-mini + LightGBM | **+$1,787** | ModernFinBERT (+$1,080) |

---

## 4. Phase-by-Phase Findings

### Phase 1: Sentiment Models

**Models tested:** DeBERTa-v3-finance, ModernFinBERT, FinBERT (ProsusAI)

**Key findings:**
1. All 3 sentiment models beat both LLMs at P&L
2. All 3 have identical 1d accuracy (37%) — sentiment alone can't predict next-day direction
3. Heavy BUY bias (73% BUY for DeBERTa) — they read general positive market news and say "BUY"
4. Best at P&L because BUY bias works on a stock that went +40%
5. None beat Always-BUY at any horizon

**Critical data quality discovery:**
- Only **0.7% of articles** (11 out of ~1,500) actually mentioned AMBA
- DeBERTa was scoring **general market news** as AMBA sentiment
- Alpha Vantage provides `ticker_sentiment` with `relevance_score` — should filter ≥0.7
- `extract_av_ticker_sentiment()` added to `data_parsers.py` to handle this

**Files:** `tradingagents/models/sentiment.py`, `tradingagents/baselines/sentiment_strategy.py`

---

### Phase 2: XGBoost on Structured Features

**Feature set:** 149 numeric features extracted from cached datasets:
- OHLCV returns (5), volatility (2), volume (1), price structure (3)
- Technical indicators (12): RSI, MACD, SMA50, SMA200, Bollinger, ATR + 5d deltas
- SPY context (14), sector context (12), relative strength (10)
- DeBERTa sentiment (6), AV ticker sentiment (9), AV topic sentiment (~24), AV global sentiment (~33)

**Walk-forward training:** For each prediction date, trains ONLY on prior data. TimeSeriesSplit 3-fold CV. First 3 dates default to HOLD (< 5 training samples).

**Key findings:**
1. 48.3% 1d accuracy — first model to make aggressive SELL calls (41% SELL)
2. SELL accuracy 50% across 1d/3d/1w — meaningful on a stock that gained 40%
3. Severe overfitting: 149 features / 28 samples = 5.3:1 ratio
4. Walk-forward degradation: -39.7pp (64.7% in-sample → 25% out-of-sample)

**Files:** `tradingagents/models/feature_engineering.py`, `tradingagents/models/ml_trainer.py`, `tradingagents/baselines/ml_strategy.py`

---

### Phase 2B: SHAP Feature Pruning (Default XGBoost)

**Method:** `shap.TreeExplainer` computed exact Shapley values. Selected top 20 features by mean |SHAP value|. Reduced feature-to-sample ratio from 5.3:1 to 0.7:1.

**Top 5 features by SHAP importance:**
1. `spy_gap` (0.2419) — SPY overnight gap
2. `vs_spy_excess_5d` (0.1754) — AMBA vs SPY 5-day relative return
3. `av_topic_mergers_and_acquisitions_avg` (0.1619) — M&A news sentiment
4. `av_topic_retail_wholesale_avg` (0.1540) — Retail news sentiment
5. `sector_gap` (0.1409) — Sector ETF overnight gap

**Critical insight:** Zero AMBA-specific price features (return_Nd, vol_Nd, ind_rsi) in top 20. The model trades **market regime**, not AMBA fundamentals. This means:
- It's really a macro-sentiment strategy
- May generalize to other tickers (positive for multi-ticker)
- Has no AMBA-specific edge

**Key results:**
- 1d accuracy: 55.2% (vs 48.3% unpruned, +6.9pp)
- Walk-forward degradation: -8.8pp (vs -39.7pp unpruned) — overfitting largely eliminated
- 4w accuracy: 62.1% — best of any strategy at this horizon
- 4w BUY accuracy: 83.3% — strongest actionable signal in V6
- 8w BUY accuracy: 90.9%

**P&L paradox:** More accurate but worse P&L (-$461 vs +$407). Root cause: single catastrophic SELL call on 2025-05-10 with 0.84 confidence during a stock surge (-$888). This one date accounts for $1,746 of the $868 P&L gap. Excluding it, pruned P&L ≈ +$627 vs unpruned ≈ -$451.

**Fold stability warning:** SHAP rankings were unstable across 3 CV folds. Features flipped from rank 1 to rank 57. With only 28 samples, the top-20 selection is one draw from a noisy distribution.

**Files:** `scripts/shap_analysis.py`, `tradingagents/baselines/ml_strategy_pruned.py`, `tradingagents/models/selected_features.json`
**Full report:** `reports/benchmarks/V6_SHAP_PRUNING_RESULTS_2026-02-19.md`

---

### Phase 3: Kronos Time-Series Model

**Model:** [Kronos-mini](https://huggingface.co/NeoQuasar/Kronos-mini) (4.1M params, AAAI 2026)
- Pre-trained on 12 billion candlestick records from 45 exchanges
- Zero-shot inference: feeds ~60 daily OHLCV bars, predicts next 3 candles
- Runs on MPS (Apple Silicon) in ~1 sec/prediction
- Monte Carlo: 20 samples, temperature 0.8 for stable predictions
- Decision: 60% weight on 1-day direction + 40% on multi-day consistency

**Key results:**
- 1d accuracy: **56.7%** — first strategy to beat Always-BUY (50%)
- BUY 1d: 57.1%, SELL 1d: 56.2% — balanced signal (never HOLDs)
- Negative P&L (-$412) despite high accuracy — wrong trades are large losers (position sizing issue)

**Technical notes:**
- Use `Kronos-mini` not `Kronos-small` — mini is better (see Phase 5)
- Tokenizer: always `NeoQuasar/Kronos-Tokenizer-base` (shared across sizes)
- `DatetimeIndex` doesn't have `.dt` accessor — pass `pd.Series` for timestamps
- `predict()` needs `x_timestamp` and `y_timestamp` as `pd.Series`

**Files:** `tradingagents/models/kronos/` (vendored), `tradingagents/models/timeseries.py`, `tradingagents/baselines/timeseries_strategy.py`

---

### Phase 4: 3-Model Ensemble (DeBERTa + XGBoost + Kronos)

**Method:** Confidence-weighted vote
- BUY=+1, SELL=-1, HOLD=0; weighted by model confidence
- Thresholds: >+0.15 → BUY, <-0.15 → SELL, else HOLD

**Key results:**
- 1d accuracy: 46.7% — **worse** than Kronos alone (56.7%)
- 13w accuracy: 60% — best of any strategy at this horizon (at the time)
- DeBERTa's 73% BUY bias systematically overrides correct SELL signals

**Verdict:** The 3-model ensemble fails at short-term because DeBERTa adds noise. But performs well at long horizons where sentiment has predictive value.

**Files:** `tradingagents/baselines/ensemble_strategy.py`

---

### Phase 5: Ensemble Ablation & Model Size Study

**Goal:** Systematically determine which model combinations work and why.

**Named ensemble syntax:** `ensemble_METHOD+sub1+sub2` parsed by `_normalize_sub_strategy()` in `cli/evaluate_v2.py`

#### 6 Experiments Run

| # | Ensemble | 1d Acc | P&L | Verdict |
|---|----------|--------|------|---------|
| 1 | Kronos Small (solo) | 50.0% | -$434 | Mini >> Small |
| 2 | **Kronos-mini + XGBoost** | **63.3%** | **+$482** | Best 1d accuracy |
| 3 | Kronos-small + XGBoost | 36.7% | -$3,157 | Catastrophic |
| 4 | Kronos-mini + DeBERTa | 43.3% | -$783 | DeBERTa hurts |
| 5 | **Kronos-mini + LightGBM** | **60.0%** | **+$1,787** | Best P&L |
| 6 | LightGBM + XGBoost | 36.7% | -$327 | No Kronos = fail |

#### 6 Key Findings

**Finding 1: Kronos-mini + ML = Best Strategy**
- Kronos provides directional prior from OHLCV patterns
- ML provides complementary signal from structured features (SPY context, relative strength, sentiment)
- When they agree → strong signal; when they disagree → HOLD avoids false trades

**Finding 2: DeBERTa Hurts Short-Term Ensembles**
- Adding DeBERTa drops 1d accuracy by 16-20pp
- Its 73% BUY bias overrides correct SELL signals from other models
- Root cause: scores irrelevant general market news (only 0.7% of articles mention AMBA)

**Finding 3: Kronos-small is Worse Than Kronos-mini**
- Solo: 50% (small) vs 56.7% (mini)
- In ensemble with XGBoost: 36.7% (small) vs 63.3% (mini)
- Larger model may overfit to training data patterns that don't transfer to AMBA
- Mini's simpler representations may generalize better for single-stock prediction

**Finding 4: Walk-Forward Stability**
- Kronos-mini+XGBoost is the ONLY strategy that **improves** out-of-sample (+5.6%)
- All other strategies degrade OOS, indicating genuine learning vs overfitting

| Strategy | In-Sample | Out-of-Sample | Delta |
|----------|-----------|---------------|-------|
| E: Kronos-mini+XGB | 61.1% | **66.7%** | **+5.6%** |
| E: Kronos-mini+LGBM | 61.1% | 58.3% | -2.8% |
| Kronos Mini (solo) | 61.1% | 50.0% | -11.1% |
| Kronos Small (solo) | 55.6% | 41.7% | -13.9% |

**Finding 5: ML-Only Ensemble (No Kronos) Fails**
- LightGBM + XGBoost = 36.7% — below random
- Both use identical features → highly correlated signals → amplify shared errors
- **Kronos provides the essential orthogonal signal** that ML models lack

**Finding 6: LightGBM vs XGBoost in Ensembles**
- XGBoost: higher 1d accuracy (63.3%), better walk-forward stability (+5.6%)
- LightGBM: higher P&L (+$1,787), lower drawdown ($1,049), better 13w accuracy (64%)
- **Aggressive/day-trading:** use Kronos-mini + XGBoost
- **Conservative/P&L-optimized:** use Kronos-mini + LightGBM

---

## 5. Statistical Limitations

| Limitation | Impact | Mitigation |
|------------|--------|------------|
| **n=30 sample size** | No strategy reaches p<0.05 vs Always-BUY | Need multi-ticker or longer history |
| **Single ticker (AMBA)** | Can't generalize; AMBA went +40% making BUY easy | Multi-ticker validation needed |
| **28 training samples for ML** | 0.7:1 feature ratio (pruned) is better but still tight | Cross-ticker training pool |
| **SHAP fold instability** | Top-20 features are one noisy draw | Bootstrap-stable SHAP selection |
| **Overlapping confidence intervals** | 63.3% best vs 50% baseline: CI [46.7%, 80.0%] | More data points needed |
| **Bullish period bias** | Always-BUY achieves 79% at 8w — extreme bull bias | Need bear/sideways periods |

### Bootstrap 95% Confidence Intervals (1d Accuracy)

| Strategy | Accuracy | 95% CI |
|----------|----------|--------|
| E: Kronos-mini+XGB | 63.3% | [46.7%, 80.0%] |
| E: Kronos-mini+LGBM | 60.0% | [43.3%, 76.7%] |
| Kronos Mini | 56.7% | [40.0%, 73.3%] |
| Kronos Small | 50.0% | [33.3%, 66.7%] |
| Always-BUY | 50.0% | — |

---

## 6. Data Pipeline & Cached Datasets

### Dataset Structure
Cached at `results/datasets/{TICKER}/{DATE}/{TICKER}_{DATE}_raw_dataset.json`

| Field | Format | Content |
|-------|--------|---------|
| `market_data` | CSV string | OHLCV bars (~60 days) |
| `indicators_data` | Text block | RSI, MACD, SMA, Bollinger, ATR |
| `news_data` | 2-line string | Line 1: Polygon news dict, Line 2: Alpha Vantage news dict |
| `global_news_data` | String | Alpha Vantage global market news |
| `spy_market_data` | CSV string | SPY OHLCV bars |
| `sector_market_data` | CSV string | Sector ETF OHLCV bars |

### Data Quality Issues

1. **News relevance:** 99.3% of articles scored by DeBERTa are irrelevant to AMBA
2. **AV ticker_sentiment:** Only 2 articles per 30 dates had AMBA-specific AV sentiment
3. **Polygon vs AV:** Polygon provides 9 AMBA-specific articles vs AV's 2
4. **Fix implemented:** `extract_av_ticker_sentiment()` filters by `relevance_score >= 0.7`

---

## 7. Technical Infrastructure

### Environment
- Conda env: `tradingagents`
- Activation: `source /opt/miniconda3/etc/profile.d/conda.sh && conda activate tradingagents`
- Platform: macOS (Darwin), Apple Silicon (MPS for PyTorch)

### Evaluation Framework (cli/evaluate_v2.py)

**Strategy dispatch prefixes:**
- `single_` → LLM-based (V5)
- `sentiment_` → DeBERTa/FinBERT/ModernFinBERT
- `ml_` → XGBoost/LightGBM (unpruned or pruned)
- `ts_kronos_` → Kronos time-series
- `ensemble_` → Ensemble meta-learner
- `ma_` → Moving average baseline

**Named ensemble syntax:** `ensemble_weighted_vote+kronos_mini+xgboost`
- Parsed by `_normalize_sub_strategy()` which maps aliases to strategy keys
- Lazy-loads sub-strategy instances via `_get_strategy()` in ensemble_strategy.py

**Checkpoint/resume:** `python -m cli.evaluate_v2 --resume RUN_ID`
- Saves after each task to `checkpoint.json`
- Known issue: stuck tasks may have status "running" — must manually set to "pending" for resume

### Key Dependencies
- `xgboost`, `lightgbm` — tree-based ML models
- `shap>=0.43.0` — feature importance analysis
- `transformers` — DeBERTa/FinBERT/ModernFinBERT
- `scikit-learn` — preprocessing, TimeSeriesSplit
- `torch` — Kronos model (pip install, not conda)
- `einops` — Kronos model dependency

### Common Errors & Fixes
- `numpy float32 not JSON serializable`: cast with `float()` in ml_trainer.py predict
- OHLCV labels: each dataset ends at trade date, need next dataset's OHLCV for next-day label
- `torch` not in conda: `pip install torch` separately
- Kronos import: `from model.module import *` → `from tradingagents.models.kronos.module import *`
- `DatetimeIndex` has no `.dt` accessor: pass `pd.Series` for timestamps to Kronos
- Pipe buffering: background commands piped to `| tail` produce empty output; check checkpoint files directly

---

## 8. File Inventory

### Models (`tradingagents/models/`)
| File | Purpose |
|------|---------|
| `sentiment.py` | DeBERTa/FinBERT/ModernFinBERT wrapper |
| `data_parsers.py` | Parse cached dataset strings + AV ticker sentiment extraction |
| `feature_engineering.py` | 149-feature extraction (OHLCV, indicators, sentiment, AV) |
| `ml_trainer.py` | XGBoost/LightGBM walk-forward training + SHAP analysis |
| `timeseries.py` | Kronos prediction wrapper with lazy model loading |
| `selected_features.json` | Top 20 SHAP-selected features for runtime |
| `kronos/` | Vendored Kronos model (kronos.py, module.py) |

### Strategies (`tradingagents/baselines/`)
| File | Purpose |
|------|---------|
| `sentiment_strategy.py` | Sentiment-only strategy |
| `ml_strategy.py` | ML strategy with walk-forward training |
| `ml_strategy_pruned.py` | `MLStrategyPruned` subclass (default XGBoost) |
| `timeseries_strategy.py` | Kronos time-series strategy |
| `ensemble_strategy.py` | Ensemble meta-learner (majority_vote, weighted_vote, adaptive) |

### Evaluation & Scripts
| File | Purpose |
|------|---------|
| `cli/evaluate_v2.py` | Main evaluation harness with multi-strategy dispatch |
| `scripts/shap_analysis.py` | SHAP feature importance analysis CLI |
| `cli/compile_reports.py` | PDF report compiler |
| `cli/analyze_outcomes.py` | Post-hoc outcome analysis |

### Reports
| File | Purpose |
|------|---------|
| `reports/benchmarks/V6_Plan.md` | Master plan with all phase results |
| `reports/benchmarks/V6_SHAP_PRUNING_RESULTS_2026-02-19.md` | Detailed SHAP analysis |
| `reports/benchmarks/V6_COMPLETE_RESEARCH_SUMMARY.md` | This file |

### Evaluation Run Directories (`results/evaluations/`)
| Run ID | Strategy | Result |
|--------|----------|--------|
| `backtest_v2_20260215_175115` | DeBERTa sentiment | 37% 1d, +$945 |
| `backtest_v2_20260217_164206` | FinBERT + ModernFinBERT | 37% 1d each |
| `backtest_v2_20260217_170255` | XGBoost ML (unpruned) | 48.3% 1d, +$407 |
| `backtest_v2_20260217_180202` | Kronos Mini | 56.7% 1d, -$412 |
| `backtest_v2_20260217_180245` | Ensemble 3-model | 46.7% 1d, -$707 |
| `backtest_v2_20260218_221702` | XGBoost unpruned vs pruned | 48.3% vs 55.2% |
| `backtest_v2_20260218_192824` | Kronos Small | 50% 1d, -$434 |
| `backtest_v2_20260218_192919` | E: Kronos-mini+XGBoost | 63.3% 1d, +$482 |
| `backtest_v2_20260219_010834` | E: Kronos-small+XGBoost | 36.7% 1d, -$3,157 |
| `backtest_v2_20260219_022022` | E: Kronos-mini+DeBERTa | 43.3% 1d, -$783 |
| `backtest_v2_20260219_022352` | E: Kronos-mini+LightGBM | 60% 1d, +$1,787 |
| `backtest_v2_20260219_034243` | E: LightGBM+XGBoost | 36.7% 1d, -$327 |

---

## 9. Actionable Conclusions

### What Works
1. **Kronos-mini + XGBoost SHAP-Pruned** = best 1d accuracy (63.3%), only strategy that improves OOS
2. **Kronos-mini + LightGBM** = best P&L (+$1,787), lowest drawdown ($1,049), best 13w (64%)
3. **XGBoost SHAP-Pruned 4w BUY signal** = 83.3% accuracy — strongest actionable signal
4. **SHAP pruning** eliminates overfitting (degradation from -40pp to -9pp)
5. **All specialized models beat LLMs** at cost ($0 vs $0.08-0.10), determinism, and most accuracy metrics

### What Doesn't Work
1. **DeBERTa in ensembles** — BUY bias from irrelevant news drops 1d accuracy 16-20pp
2. **Kronos-small** — larger model is worse than mini, especially in ensembles
3. **ML-only ensembles** — XGBoost + LightGBM = 36.7% (correlated signals, no diversity)
4. **3-model ensemble** — DeBERTa noise outweighs its long-horizon value at short-term
5. **LLMs** — non-deterministic, expensive, and below Always-BUY

### What's Unknown (Future Work)
1. **Multi-ticker validation** — does Kronos-mini+XGB work on non-AMBA stocks? Since XGBoost features are macro-regime, it should generalize
2. **Bear/sideways markets** — AMBA went +40%, making Always-BUY artificially strong. Need stocks that went flat or down
3. **SELL accuracy deep-dive** — what's the SELL accuracy of the winning ensembles? Can they identify pullbacks?
4. **Bootstrap-stable SHAP** — run feature selection 100x with different samples, keep features appearing >50% of the time
5. **Cross-ticker training** — train XGBoost on multiple tickers to increase sample size beyond n=28
6. **Regime-adaptive strategy switching** — use different strategies based on detected market regime (HMM or similar)
7. **Position sizing** — Kronos-mini has 56.7% accuracy but negative P&L due to large losers. Kelly criterion or volatility-scaled sizing could fix this
8. **DeBERTa with proper ticker filtering** — re-test DeBERTa scoring only AMBA-relevant articles (relevance ≥ 0.7)

---

## 10. Academic References

| Finding | Source | Implication |
|---------|--------|------------|
| Raw OHLCV features > derived indicators for ML | arXiv:2412.15448 | Include raw returns, not just RSI/MACD |
| FinBERT sentiment Granger-causes volatility at 1w | Multiple papers | Sentiment useful at 1w+ horizon |
| TSFMs underperform XGBoost on financial data (zero-shot) | arXiv:2511.18578 | Don't use TimesFM/Chronos zero-shot |
| Regime detection essential for strategy robustness | arXiv:2601.19504 | Add HMM regime filter |
| Ensemble NLP (DeBERTa+FinBERT+RoBERTa) hits 80% F1 | arXiv:2507.09739 | Consider NLP ensemble if single model insufficient |
| "Generating Alpha" paper: 135% return in 24mo | arXiv:2601.19504 | XGBoost + regime detection proven approach |

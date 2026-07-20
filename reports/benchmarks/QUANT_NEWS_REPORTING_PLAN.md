# Quant-News Reporting & Prediction Platform Plan

**Date:** 2026-03-06
**Source Project:** TradingAgents (V6 research, `/Users/UmarJahangir/Projects/TradingAgents/`)
**Target Project:** quant-news (`/Users/UmarJahangir/Projects/quant-news/`)
**Reference:** `reports/benchmarks/V6_COMPLETE_RESEARCH_SUMMARY.md`

---

## 1. Objective

Augment the quant-news Dash Web UI to serve as an **internal research platform** for:
1. Running predictions using V6 specialized models + LLM-based analysis
2. Compiling market research reports (single-agent Claude + multi-agent TradingAgents)
3. Tracking prediction accuracy over time for forward-testing / paper trading
4. Comparing prediction methods head-to-head with actual market outcomes

---

## 2. V6 Research Context (from TradingAgents)

### 2.1 Prediction Methods Available

| # | Method Key | Display Name | Source | Cost | Speed | V6 1d Accuracy |
|---|-----------|-------------|--------|------|-------|----------------|
| 1 | `ts_kronos_mini` | Kronos Mini | OHLCV time-series foundation model (4.1M params) | $0 | ~2s | 56.7% |
| 2 | `ml_xgboost_pruned` | XGBoost (SHAP-Pruned) | Walk-forward ML on 20 SHAP-selected features | $0 | ~3s | 51.7% |
| 3 | `sentiment_deberta` | DeBERTa Sentiment | Financial news sentiment (DeBERTa-v3) | $0 | ~5s | 36.7% |
| 4 | `ensemble_kronos+xgb` | Kronos + XGBoost | Best 1d accuracy ensemble | $0 | ~5s | **63.3%** |
| 5 | `ensemble_kronos+lgbm` | Kronos + LightGBM | Best P&L ensemble | $0 | ~5s | 60.0% |
| 6 | `single_claude` | Single Agent (Claude Sonnet 4.6) | LLM market analysis + recommendation | ~$0.05 | ~15s | ~30%* |
| 7 | `multi_agent` | TradingAgents (Multi-Agent) | LangGraph multi-agent debate system | ~$0.50 | ~3min | ~30%* |

*LLM-based methods scored 27-30% in V5 benchmarks but generate valuable research reports.

### 2.2 Key V6 Findings

1. **Best short-term (1d):** Kronos-mini + XGBoost ensemble at 63.3%, the only strategy that improves out-of-sample (+5.6%)
2. **Best P&L:** Kronos-mini + LightGBM at +$1,787/30 trades, lowest drawdown ($1,049)
3. **Best 4-week:** XGBoost SHAP-Pruned at 62.1% (BUY accuracy 83.3%)
4. **DeBERTa hurts short-term ensembles** — 73% BUY bias from irrelevant general market news
5. **Kronos-mini >> Kronos-small** — smaller model generalizes better
6. **ML-only ensembles fail** — need Kronos for orthogonal signal diversity
7. **LLMs are non-deterministic and expensive** — but generate valuable qualitative reports

### 2.3 Strategy Interfaces

All V6 strategies follow the same contract:
```python
def analyze(self, ticker: str, trade_date: str, **kwargs) -> Dict[str, Any]:
    return {
        "decision": "BUY" | "SELL" | "HOLD",
        "confidence": float,  # 0.0-0.95
        "strategy": str,
        "raw_response": str,  # Full analysis text
        "input_tokens": int,
        "output_tokens": int,
        "llm_calls": int,
    }
```

### 2.4 Data Dependencies

Strategies require cached datasets at `TradingAgents/results/datasets/{TICKER}/{DATE}/`:
- `market_data` (OHLCV CSV, ~60 days)
- `indicators_data` (RSI, MACD, SMA, Bollinger, ATR)
- `news_data` (Polygon + Alpha Vantage articles)
- `global_news_data` (macro news)
- `spy_market_data`, `sector_market_data` (market context)

If not cached, data is fetched via TradingAgents tools (requires Alpha Vantage API key + internet).

---

## 3. Target Platform: quant-news

### 3.1 Current Architecture

```
quant-news/
├── app.py                    # Dash app + callbacks (1312 lines)
├── config.py                 # All configuration (dataclasses)
├── services/
│   ├── stock_data.py         # yfinance wrapper
│   ├── cache_service.py      # DuckDB caching (singleton)
│   ├── news_service.py       # News fetching + aggregation
│   ├── llm_service.py        # LM Studio / OpenAI integration
│   └── analytics.py          # Technical indicators
├── layouts/
│   ├── main_layout.py        # 3-column dashboard
│   └── components.py         # Reusable UI components
├── callbacks/
│   └── chart_callbacks.py    # Chart rendering
├── cache/
│   └── quant_news.duckdb     # DuckDB database
└── alpha_vantage_data/       # Cached AV data (19 symbols)
```

- **Tech stack:** Dash + dash-bootstrap-components (DARKLY theme), DuckDB, yfinance, Alpha Vantage, OpenAI
- **Database tables:** stock_prices, stock_info, cache_metadata, news_cache
- **No prediction tracking exists** — this is what we're adding

### 3.2 Integration Approach

**TradingAgents as editable dependency:**
```bash
pip install -e /Users/UmarJahangir/Projects/TradingAgents
```
This makes all `from tradingagents.baselines.X import Y` imports work. TradingAgents already has `pyproject.toml` defining the package.

**Shared dataset cache:** Prediction service points to TradingAgents' `results/datasets/` for cached data, avoiding duplicate API calls.

---

## 4. New Features

### 4.1 Prediction Tracking System

**Data Record Format** (per the user's specification):

| Column | Type | Source |
|--------|------|--------|
| Prediction Method | VARCHAR | Strategy key (display name) |
| Execution Date | TIMESTAMP | When prediction was run |
| Analysis Date | DATE | The trade date being analyzed |
| Ticker | VARCHAR | Stock symbol |
| Recommendation | VARCHAR | BUY / SELL / HOLD |
| Confidence | DOUBLE | 0.0 - 0.95 |
| Open (Actual) | DOUBLE | Actual open on analysis date (filled post-hoc) |
| Close (Actual) | DOUBLE | Actual close on analysis date (filled post-hoc) |
| 1d Correct | BOOLEAN | Was the direction call correct? |
| P&L | DOUBLE | Simulated P&L on $10k position |

**Example records:**

| Prediction Method | Execution Date | Analysis Date | Ticker | Recommendation | Confidence | Open | Close | 1d? | P&L |
|-------------------|---------------|---------------|--------|---------------|------------|------|-------|-----|-----|
| Single Agent (Claude) | 2026-03-06 14:30 | 2026-03-07 | AMBA | BUY | 0.72 | — | — | — | — |
| Kronos Mini | 2026-03-06 14:30 | 2026-03-07 | AMBA | SELL | 0.68 | — | — | — | — |
| Kronos + XGBoost | 2026-03-06 14:30 | 2026-03-07 | AMBA | SELL | 0.85 | — | — | — | — |
| DeBERTa Sentiment | 2026-03-06 14:30 | 2026-03-07 | AMBA | BUY | 0.91 | — | — | — | — |

After market close on 2026-03-07, "Validate Outcomes" fills in actual prices and computes correctness.

### 4.2 Research Report System

**Two report types:**

1. **Single Agent (Claude Sonnet 4.6)**
   - Uses `SingleAgentBaseline.analyze()` from TradingAgents
   - Claude generates a comprehensive market analysis covering:
     - Technical analysis (price action, indicators, support/resistance)
     - Fundamental analysis (financials, valuation, sector context)
     - News & sentiment analysis (recent headlines, market mood)
     - Risk assessment
     - Final recommendation with confidence and rationale
   - Report is the `raw_response` from the analyze call
   - Stored in DuckDB `reports` table as markdown

2. **Multi-Agent TradingAgents (Baseline)**
   - Uses `TradingAgentsGraph.propagate()` from TradingAgents main branch
   - Multi-agent debate system with specialized roles:
     - Market Analyst, Fundamentals Analyst, News Analyst, Social Sentiment Analyst
     - Bull Researcher vs Bear Researcher (adversarial debate)
     - Risk Manager, Research Manager
     - Trader (final decision)
   - Each agent generates a sub-report; all compiled into a single document
   - Reports saved to TradingAgents `results/reports_v2/` AND DuckDB `reports` table

**Report Storage:**
- Markdown content in DuckDB `reports.content` column
- Viewable in the Web UI via `dcc.Markdown` with dark theme styling
- Filterable by ticker, date, report type

### 4.3 Accuracy Dashboard

**Per-method metrics tracked:**
- Total predictions, validated predictions
- 1-day directional accuracy
- Cumulative P&L (simulated $10k per trade)
- Average confidence
- Accuracy by ticker
- Accuracy over time (rolling window)

**Visualizations:**
- Method comparison bar chart (accuracy + P&L)
- Cumulative P&L line chart per method (Plotly, dark theme)
- Confusion matrix per method (BUY/SELL/HOLD actual vs predicted)

---

## 5. Implementation Plan

### Phase 1: Foundation (Database + Service Layer)

| Step | File | Description |
|------|------|-------------|
| 1.1 | `requirements.txt` | Add `anthropic`, `tradingagents` (editable install) |
| 1.2 | `.env.example` | Add `ANTHROPIC_API_KEY`, `TRADINGAGENTS_PATH` |
| 1.3 | `config.py` | Add new config entries to `APIConfig` |
| 1.4 | `services/cache_service.py` | Add 3 new DuckDB tables + CRUD methods |
| 1.5 | **`services/prediction_service.py`** (NEW) | Strategy registry, execution wrapper, outcome validation |

**prediction_service.py design:**
```python
class PredictionService:
    """Wraps TradingAgents V6 strategies for the quant-news platform."""

    METHODS = {
        "ts_kronos_mini":       {"display": "Kronos Mini",           "cost": 0.0,  "est_seconds": 2},
        "ml_xgboost_pruned":    {"display": "XGBoost (SHAP-Pruned)", "cost": 0.0,  "est_seconds": 3},
        "sentiment_deberta":    {"display": "DeBERTa Sentiment",     "cost": 0.0,  "est_seconds": 5},
        "ensemble_kronos+xgb":  {"display": "Kronos + XGBoost",      "cost": 0.0,  "est_seconds": 5},
        "ensemble_kronos+lgbm": {"display": "Kronos + LightGBM",     "cost": 0.0,  "est_seconds": 5},
        "single_claude":        {"display": "Single Agent (Claude)",  "cost": 0.05, "est_seconds": 15},
        "multi_agent":          {"display": "TradingAgents (Multi)",  "cost": 0.50, "est_seconds": 180},
    }

    def run_prediction(self, ticker: str, trade_date: str, method: str) -> dict: ...
    def run_all(self, ticker: str, trade_date: str) -> list[dict]: ...
    def validate_outcomes(self, days_back: int = 7) -> int: ...
    def get_accuracy_stats(self) -> pd.DataFrame: ...
```

### Phase 2: Predictions UI

| Step | File | Description |
|------|------|-------------|
| 2.1 | `layouts/main_layout.py` | Wrap in `dcc.Tabs` (Dashboard / Predictions / Reports) |
| 2.2 | **`layouts/prediction_layout.py`** (NEW) | Prediction page: run panel, history table, filters, stats |
| 2.3 | **`callbacks/prediction_callbacks.py`** (NEW) | Run prediction, refresh table, validate outcomes callbacks |
| 2.4 | `app.py` | Import new callbacks, add tab-switching callback |

### Phase 3: Reports UI

| Step | File | Description |
|------|------|-------------|
| 3.1 | **`layouts/report_layout.py`** (NEW) | Report history table + markdown viewer |
| 3.2 | **`callbacks/report_callbacks.py`** (NEW) | Generate report, view report, filter callbacks |

### Phase 4: Accuracy Dashboard

| Step | File | Description |
|------|------|-------------|
| 4.1 | `layouts/prediction_layout.py` | Add accuracy sub-tab with charts and tables |
| 4.2 | `app.py` | Add startup validation hook |

### Phase 5: Polish

| Step | File | Description |
|------|------|-------------|
| 5.1 | `assets/styles.css` | Decision badges, table styling, report viewer theme |
| 5.2 | `layouts/prediction_layout.py` | Export CSV/PDF buttons |

---

## 6. New Files Summary

| File | Purpose | Lines (est.) |
|------|---------|-------------|
| `services/prediction_service.py` | Core prediction engine wrapping TradingAgents | ~300 |
| `layouts/prediction_layout.py` | Predictions page layout | ~200 |
| `layouts/report_layout.py` | Reports page layout | ~150 |
| `callbacks/prediction_callbacks.py` | Prediction Dash callbacks | ~250 |
| `callbacks/report_callbacks.py` | Report Dash callbacks | ~150 |

## Modified Files Summary

| File | Changes |
|------|---------|
| `config.py` | +10 lines (new config entries) |
| `services/cache_service.py` | +150 lines (new tables + CRUD) |
| `layouts/main_layout.py` | +30 lines (tab wrapper) |
| `app.py` | +20 lines (imports + tab callback + startup validation) |
| `assets/styles.css` | +80 lines (new component styles) |
| `requirements.txt` | +2 lines |
| `.env.example` | +2 lines |

---

## 7. Data Flow

```
User clicks "Run Prediction" (AMBA, 2026-03-07, Kronos+XGBoost)
    │
    ▼
prediction_service.run_prediction("AMBA", "2026-03-07", "ensemble_kronos+xgb")
    │
    ├── Check TradingAgents cached dataset exists?
    │   ├── YES: Load from results/datasets/AMBA/2026-03-07/
    │   └── NO:  Fetch via TradingAgents data tools (Alpha Vantage, yfinance)
    │
    ├── Instantiate EnsembleStrategy(sub_strategies=["ts_kronos_mini", "ml_xgboost_pruned"])
    │   ├── Kronos: Load OHLCV → predict next 3 candles → BUY/SELL + confidence
    │   └── XGBoost: Extract 20 features → walk-forward train → predict → BUY/SELL + confidence
    │   └── Weighted vote: combine signals → final decision
    │
    ├── Result: {decision: "SELL", confidence: 0.85, raw_response: "..."}
    │
    ├── Save to DuckDB predictions table
    │
    └── Return to UI → table row appears

Later: User clicks "Validate Outcomes"
    │
    ▼
prediction_service.validate_outcomes()
    │
    ├── Query unvalidated predictions where trade_date < today - 2 days
    ├── For each: fetch actual OHLCV from yfinance
    ├── Compute: open, close, next_day change, 1d correct, P&L
    ├── Update DuckDB records
    └── Refresh accuracy stats
```

---

## 8. Report Generation Flow

```
User clicks "Generate Report" (AMBA, 2026-03-07, Single Agent Claude)
    │
    ▼
prediction_service → SingleAgentBaseline(model="claude-sonnet-4-6")
    │
    ├── Loads cached dataset (market data, indicators, news, fundamentals)
    ├── Constructs analysis prompt with all data context
    ├── Calls Claude Sonnet 4.6 via Anthropic API
    │
    ├── Claude returns comprehensive markdown report:
    │   ├── Technical Analysis (price action, support/resistance, indicators)
    │   ├── Fundamental Analysis (financials, valuation ratios)
    │   ├── News & Sentiment (recent headlines, market mood)
    │   ├── Risk Assessment (volatility, sector risks)
    │   └── Recommendation: BUY/SELL/HOLD with confidence + rationale
    │
    ├── Save report markdown to DuckDB reports table
    ├── Also save as prediction record (decision + confidence)
    │
    └── Return to UI → report renders in markdown viewer
```

---

## 9. Relationship to V6 Research

This platform enables **forward-testing** of V6 findings:

| V6 Finding | How Platform Tests It |
|------------|----------------------|
| Kronos+XGB best at 1d (63.3% on AMBA) | Track 1d accuracy across multiple tickers over time |
| Kronos+LGBM best P&L (+$1,787 on AMBA) | Track cumulative P&L per method |
| DeBERTa hurts ensembles | Compare DeBERTa solo vs ensembles without it |
| XGBoost 4w BUY signal (83.3%) | Track multi-horizon outcomes (future enhancement) |
| LLMs non-deterministic | Run single_claude multiple times, measure variance |
| Multi-ticker generalization unknown | Run predictions on multiple tickers, compare to AMBA results |

### Critical Question from V6 (now answerable):
> "Can ANY model beat Always-BUY on stocks that went sideways or down?"

The platform will collect predictions across diverse tickers and market conditions, providing the multi-ticker validation that V6's single-ticker (AMBA) study couldn't offer.

---

## 10. Success Criteria

| Criterion | Metric |
|-----------|--------|
| **Functional** | All 7 prediction methods execute successfully from the Web UI |
| **Persistence** | Predictions and reports survive app restart (DuckDB) |
| **Validation** | Actual outcomes auto-filled for predictions older than 2 business days |
| **Accuracy tracking** | Per-method accuracy table updates after validation |
| **Reports** | Single-agent Claude report renders cleanly in dark-theme markdown viewer |
| **Performance** | Local strategies (Kronos, ML, sentiment) complete in < 10 seconds |
| **Non-breaking** | Existing dashboard functionality unchanged |

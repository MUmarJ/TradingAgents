# AI Agent-Driven Trading: Comprehensive Analysis Report

**Date**: January 28, 2026
**System Under Analysis**: TradingAgents (fork of TauricResearch/TradingAgents)
**Branch**: `feat/ace_alpaca`
**Analyst**: Automated Deep Research via Claude Opus 4.5

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [TradingAgents Architecture Review](#2-tradingagents-architecture-review)
3. [Paper-Reported Benchmarks vs Real-World Performance](#3-paper-reported-benchmarks-vs-real-world-performance)
4. [Critical Gaps Found in Deployed System](#4-critical-gaps-found-in-deployed-system)
5. [Academic Landscape: Sentiment Analysis-Based Strategies](#5-academic-landscape-sentiment-analysis-based-strategies)
6. [Academic Landscape: Mean Reversion & Trend Following](#6-academic-landscape-mean-reversion--trend-following)
7. [Academic Landscape: Whale/Insider Transaction Following](#7-academic-landscape-whaleinsider-transaction-following)
8. [Multi-Agent Trading Systems: State of the Art](#8-multi-agent-trading-systems-state-of-the-art)
9. [Report vs Actual Market Data: Gap Analysis](#9-report-vs-actual-market-data-gap-analysis)
10. [Is the Multi-Agent Setup Worth Pursuing?](#10-is-the-multi-agent-setup-worth-pursuing)
11. [Enhancement Roadmap](#11-enhancement-roadmap)
12. [Data Sources Reference Guide](#12-data-sources-reference-guide)
13. [Academic References](#13-academic-references)

---

## 1. Executive Summary

This report presents a comprehensive analysis of AI agent-driven trading strategies with a focus on three pillars: **sentiment analysis-based strategies**, **mean reversion & trend following**, and **whale/insider transaction following**. The analysis was conducted by:

- Thoroughly exploring the TradingAgents codebase (12 agents, 8+ data sources, LangGraph architecture)
- Reviewing 20+ arxiv papers and frameworks (FinGPT, FinRL, QuantAgents, HedgeAgents, FinMem, etc.)
- Comparing generated reports against actual market data from Yahoo Finance and StockTwits
- Analyzing 90+ trade outcomes from the system's own outcome tracker

### Key Findings

| Finding | Severity | Impact |
|---------|----------|--------|
| Report cross-contamination (wrong ticker data) | **CRITICAL** | Decisions based on wrong stock's analysis |
| 93% BUY bias (84/90 trades are BUY, 0 SELL) | **HIGH** | System cannot short or avoid bad trades |
| 20% win rate with -$14,248 total P&L | **HIGH** | Worse than random (50%) |
| Missing catalytic events (RAPT's $2.2B GSK acquisition) | **HIGH** | Biggest movers completely missed |
| Market regime always "unknown" | **MEDIUM** | No regime-aware position sizing |
| Confidence field always null | **MEDIUM** | No signal strength filtering |
| Many outcomes with entry_price = 0.0, validated = false | **MEDIUM** | Incomplete outcome tracking |

### Bottom Line

The multi-agent architecture has theoretical merit, validated by papers like QuantAgents (Sharpe 2.02 in live trading) and HedgeAgents (70% annualized over 3 years). However, the current TradingAgents deployment has critical data integrity bugs that make it perform worse than random. **Fix the plumbing before adding more agents.**

---

## 2. TradingAgents Architecture Review

### 2.1 System Overview

TradingAgents (arXiv: 2412.20138) implements a multi-agent LLM framework with **12 agents** organized in 4 hierarchical layers, inspired by how real trading firms operate.

**Core Technology Stack:**
- **Orchestration**: LangGraph StateGraph
- **LLMs**: GPT-5.1-codex-mini (deep thinking) / GPT-5.2-2025-12-11 (quick tasks)
- **Memory**: ChromaDB with text-embedding-3-small (currently disabled)
- **Self-Improvement**: ACE (Agentic Context Engineering) framework (currently disabled)
- **Broker**: Alpaca (paper + live trading support)

### 2.2 Agent Architecture

```
                    ┌─────────────────────────────────────┐
                    │         ANALYST LAYER                │
                    │                                      │
                    │  Market    Social    News    Fundmtls │
                    │  Analyst   Analyst  Analyst  Analyst  │
                    │  (tools)   (tools)  (tools)  (tools)  │
                    └──────────────┬───────────────────────┘
                                   │ 4 reports
                    ┌──────────────▼───────────────────────┐
                    │         RESEARCH LAYER                │
                    │                                       │
                    │   Bull Researcher ←→ Bear Researcher  │
                    │        (debate, max 2 rounds)         │
                    │               ↓                       │
                    │      Research Manager (judge)          │
                    └──────────────┬────────────────────────┘
                                   │ investment plan
                    ┌──────────────▼────────────────────────┐
                    │          TRADER LAYER                  │
                    │                                        │
                    │  Trader (sentiment vs price validation) │
                    │  + ACE learned strategies (if enabled)  │
                    └──────────────┬─────────────────────────┘
                                   │ trading decision
                    ┌──────────────▼─────────────────────────┐
                    │       RISK MANAGEMENT LAYER             │
                    │                                         │
                    │  Risky ←→ Neutral ←→ Safe/Conservative  │
                    │        (3-way debate)                    │
                    │             ↓                            │
                    │       Risk Judge (final decision)        │
                    │       → BUY / HOLD / SELL                │
                    └─────────────────────────────────────────┘
```

### 2.3 Data Sources Currently Configured

| Category | Primary Vendor | Fallback Vendors | Status |
|----------|---------------|-----------------|--------|
| Core Stock Data (OHLCV) | Yahoo Finance | Alpha Vantage, Local | Working |
| Technical Indicators | Yahoo Finance | Alpha Vantage | Working |
| Fundamental Data | Alpha Vantage | OpenAI, Yahoo Finance | Working |
| News (Company) | Alpha Vantage | Google News, OpenAI, Finnhub | Partial (misses M&A) |
| News (Global/Macro) | Alpha Vantage | OpenAI, Reddit | Working |
| Social Sentiment | Stocktwits | ApeWisdom, Finnhub, Reddit PRAW | Single source only |
| Insider Transactions | Alpha Vantage | Yahoo Finance, Finnhub | Underutilized |
| Insider Sentiment | Finnhub | N/A | Underutilized |

### 2.4 Current Configuration Notes

- **Memory is disabled** (`MEMORY_ENABLED=false`) — ChromaDB situation memory not active
- **ACE is disabled** (`ACE_ENABLED=false`) — Self-improving agents not active
- **News limits**: 60 default, 200 for 3mo, 500 for 6mo, 600 for 12mo recall
- **Monthly bucketing enabled** for temporal diversity in news sampling
- **Social sentiment**: Single source (Stocktwits) rather than aggregated multi-source

---

## 3. Paper-Reported Benchmarks vs Real-World Performance

### 3.1 Original Paper Results (arXiv: 2412.20138)

**Test Period**: January 1 - March 29, 2024 (3 months)
**Stocks Tested**: AAPL, GOOGL, AMZN (3 stocks)
**Baselines**: Buy & Hold, MACD, KDJ&RSI, ZMR (mean reversion), SMA

#### AAPL Performance

| Strategy | Cumulative Return | Annualized Return | Sharpe Ratio | Max Drawdown |
|----------|-------------------|-------------------|--------------|--------------|
| Buy & Hold | -5.23% | -5.09% | -1.29 | 11.90% |
| MACD | -1.49% | -1.48% | -0.81 | 4.53% |
| KDJ & RSI | 2.05% | 2.07% | 1.64 | 1.09% |
| ZMR | 0.57% | 0.57% | 0.17 | 0.86% |
| SMA | -3.20% | -2.97% | -1.72 | 3.67% |
| **TradingAgents** | **26.62%** | **30.50%** | **8.21** | **0.91%** |

#### GOOGL Performance

| Strategy | Cumulative Return | Annualized Return | Sharpe Ratio | Max Drawdown |
|----------|-------------------|-------------------|--------------|--------------|
| Buy & Hold | 7.78% | 8.09% | 1.35 | 13.04% |
| MACD | 6.20% | 6.26% | 2.31 | 1.22% |
| KDJ & RSI | 0.40% | 0.40% | 0.02 | 1.58% |
| SMA | 6.23% | 6.43% | 2.12 | 2.34% |
| **TradingAgents** | **24.36%** | **27.58%** | **6.39** | **1.69%** |

#### AMZN Performance

| Strategy | Cumulative Return | Annualized Return | Sharpe Ratio | Max Drawdown |
|----------|-------------------|-------------------|--------------|--------------|
| Buy & Hold | 17.10% | 17.60% | 3.53 | 3.80% |
| SMA | 11.01% | 11.60% | 2.22 | 3.97% |
| **TradingAgents** | **23.21%** | **24.90%** | **5.60** | **2.11%** |

### 3.2 Concerns About Paper Benchmarks

The paper authors themselves acknowledged: *"The highest Sharpe Ratio exceeds the expected empirical range (SR above 2 = very good, above 3 = excellent). We believe the exceptionally high SR resulted from the phenomenon that there were few pullbacks during that period."*

**Red flags:**
1. **3-month window** on **3 stocks** is far too narrow for statistical significance
2. **Sharpe ratios of 5.6-8.2** are unrealistically high — professional quant funds typically achieve 1.0-3.0
3. **Jan-Mar 2024 was a strong bull market** (S&P 500 +10.2% in Q1 2024), inflating all long-biased strategies
4. **No transaction costs** appear to be included in the reported figures
5. **No out-of-sample validation** on different time periods or market regimes

### 3.3 Our Deployed System's Actual Performance

From outcome tracking data (sessions from Jan 16-23, 2026):

| Metric | Value |
|--------|-------|
| Total Trades | 90 |
| Winning Trades | 18 (20%) |
| Losing Trades | 72 (80%) |
| Total P&L | **-$14,248.31** |
| Average Win | $48.65 |
| Average Loss | -$210.06 |
| Win Rate | **20%** |
| BUY Decisions | 84 (93.3%) |
| SELL Decisions | 0 (0%) |
| HOLD Decisions | 6 (6.7%) |
| BUY Win Rate | 21.4% |
| Market Regime Detection | "unknown" for all trades |
| Confidence Scores | null for all trades |
| Validated Outcomes | Partially (many entry_price = 0.0) |

**The deployed system performs dramatically worse than paper benchmarks.** The 20% win rate is worse than a coin flip. The overwhelming BUY bias (93%) with zero SELL decisions indicates the system cannot effectively go short or avoid positions.

---

## 4. Critical Gaps Found in Deployed System

### 4.1 Gap: Report Cross-Contamination (CRITICAL)

The most severe issue discovered: **analyst reports for one ticker contain analysis of a completely different stock.**

**Evidence:**

| Ticker Being Analyzed | Report Actually Contains | Impact |
|-----------------------|--------------------------|--------|
| SNOW (Snowflake, $210) | BIRK (Birkenstock, $42) analysis | BUY decision based on $42 stock's technicals |
| AMBA (Ambarella, $69) | BIRK (Birkenstock, $42) analysis | -4.35% loss, wrong company analyzed |
| AYI (Acuity Brands, $320) | BIRK (Birkenstock, $42) analysis | -3.36% loss, wrong company analyzed |
| ABNB (Airbnb, $140+) | APD (Air Products, $260) analysis | Decision based on industrial gas company |
| ADP (Automatic Data Processing) | APD (Air Products) analysis | Wrong company fundamentals |

**Root cause**: The LangGraph state (`AgentState`) is not being properly cleared between sequential ticker analyses when running batch analyses. The `market_report`, `sentiment_report`, `news_report`, and `fundamentals_report` fields carry over from a previous ticker's analysis.

**Location**: `tradingagents/graph/propagation.py` and `tradingagents/graph/setup.py` — the `create_initial_state()` method and graph invocation need to ensure complete state isolation between runs.

### 4.2 Gap: Overwhelming BUY Bias

The system produces BUY recommendations 93% of the time. This is not a balanced multi-agent debate outcome — it suggests:

1. **LLM long bias**: Research confirms that GPT-based models exhibit bullish directional bias in financial sentiment analysis (see: "FinGPT aligns closely with upward trends but lags during downturns" — arXiv: 2507.08015)
2. **Prompt design flaw**: The Bull Researcher is more persuasive than the Bear Researcher because the prompts may inadvertently favor constructive arguments
3. **Risk team failure**: The Risky/Safe/Neutral debate is supposed to gate aggressive BUY decisions, but evidently isn't functioning as a counterbalance
4. **No SHORT mechanism**: The system has no explicit pathway for recommending short positions, only BUY/HOLD/SELL of existing positions

### 4.3 Gap: Missing Catalytic Events

**Case study: RAPT Therapeutics (Jan 20, 2026)**

| Timeline | Event | System Response |
|----------|-------|-----------------|
| Pre Jan 20 | RAPT trading at ~$35, clinical-stage biotech | System analyzed ozureprobart clinical data |
| Jan 20 | **GSK announces $2.2B acquisition of RAPT** | **NOT DETECTED by any agent** |
| Jan 20 close | Stock at **$57.57** (+64% from pre-announcement) | System's analysis focused on conference presentations |
| Post Jan 20 | Stock stabilized at ~$57.60 near acquisition price | N/A |

The system's news analyst covered 6 months of clinical data, investor conferences, and analyst coverage but completely missed the single most important catalyst: an acquisition announcement. This reveals:
- **No real-time/breaking news detection**
- **No M&A rumor tracking pipeline**
- **Alpha Vantage news API has latency** for breaking events
- **No event-driven signal processing**

### 4.4 Gap: No Market Regime Detection

Every single trade outcome has `market_regime: "unknown"` and `volatility_regime: "unknown"`. The system makes identical types of decisions regardless of whether the market is trending, mean-reverting, or experiencing high volatility.

State-of-the-art systems (see Section 6) use:
- VIX levels for volatility regime classification
- ADX/trend strength indicators for trend vs range detection
- Online changepoint detection (CPD) for regime transitions
- Yield curve shape for macro regime classification

### 4.5 Gap: No Confidence Scoring

Every trade has `confidence: null`. Without confidence scoring:
- All trades are treated equally regardless of signal quality
- No position sizing based on conviction level
- No filtering of low-confidence signals
- No way to evaluate which types of analysis produce higher-quality signals

### 4.6 Gap: Memory and ACE Disabled

Both `MEMORY_ENABLED` and `ACE_ENABLED` are set to `false`. This means:
- ChromaDB situation memory is not learning from past trades
- The reflection mechanism is not storing lessons
- The ACE skillbook is not accumulating learned strategies
- Each analysis starts from zero with no historical context

These are two of the system's most innovative features (per the paper) and they're turned off.

---

## 5. Academic Landscape: Sentiment Analysis-Based Strategies

### 5.1 Evolution of Sentiment Models

| Generation | Model | Accuracy (FPB) | Trading Sharpe | Year | Reference |
|------------|-------|----------------|----------------|------|-----------|
| 1st Gen | VADER / TextBlob | 60-65% | 0.3-0.5 | 2014 | Hutto & Gilbert |
| 2nd Gen | FinBERT | ~95% | 0.8-1.2 | 2019 | arXiv: 1908.10063 |
| 3rd Gen | FinGPT (fine-tuned LLaMA) | 78-87% | 0.8-1.2 | 2023 | arXiv: 2306.06031 |
| 3rd Gen | FinLlama (fine-tuned Llama2 7B) | N/A | 44.7% > FinBERT | 2024 | arXiv: 2403.12285 |
| 4th Gen | FinDPO (DPO-optimized) | +11% over SFT | **SR 2.0** | 2025 | arXiv: 2507.18417 |
| Zero-shot | GPT-4 (headlines) | 72-78% directional | ~0.75 | 2023 | Lopez-Lira & Tang |

### 5.2 Key Finding: LLMs vs Traditional NLP

- **FinBERT still leads on accuracy** (~95%) for straightforward sentiment classification on labeled datasets
- **LLMs (GPT-4, FinGPT) excel at nuanced reasoning** — understanding sarcasm, conditional sentiment, multi-entity articles
- **FinDPO represents the current frontier** — using Direct Preference Optimization to align LLMs for sentiment that translates to trading alpha (Sharpe 2.0)
- **Bullish bias is a documented LLM problem** — FinGPT "aligns closely with upward trends but lags during downturns" (arXiv: 2507.08015)

### 5.3 FinRL Contest Benchmarks (2024-2025)

The FinRL Contests (arXiv: 2504.02281) serve as the closest thing to a standardized benchmark:

| Team | Approach | Cumulative Return | Sharpe Ratio | Universe |
|------|----------|-------------------|--------------|----------|
| Aethernet42 | Fine-tuned LLaMA-3.2-3B + RLMF | **134.05%** | N/A | 229 trading days |
| Otago Alpha | Ensemble RL + sentiment | N/A | **1.08** (highest) | S&P 500 subset |
| Buy & Hold baseline | Passive | 72.71% | N/A | Same period |

### 5.4 Sentiment Data Sources: Comparison

| Source | Cost | Coverage | Latency | Sentiment Labels | Best For |
|--------|------|----------|---------|-----------------|----------|
| Stocktwits | Free (scraping) | Stock-specific social | Minutes | Built-in Bull/Bear | Retail sentiment |
| ApeWisdom | Free API | Reddit aggregated (WSB, r/stocks) | Hours | Mention count only | Reddit buzz detection |
| Finnhub | API key (free tier) | Reddit + Twitter scored | Hours | Numerical score | Cross-platform sentiment |
| Reddit PRAW | Free (credentials) | Direct Reddit access | Real-time | None (raw text) | Deep discussion analysis |
| Benzinga | Paid ($) | Professional financial news | **Seconds** | None (use LLM) | Breaking news, M&A |
| Polygon.io | Paid ($) | Market data + news | **Seconds** | None | Real-time events |
| Alpha Vantage News | Free tier | General financial news | **Minutes-Hours** | Built-in score | Broad coverage |
| Twitter/X API | Paid ($$$) | Social media | Real-time | None (use LLM) | Viral sentiment shifts |

**Gap in current system**: Using only Stocktwits (single source) when the system supports aggregated multi-source. The aggregated mode (`social_sentiment: "aggregated"` in config) would combine Stocktwits + ApeWisdom + Finnhub for a more robust signal.

---

## 6. Academic Landscape: Mean Reversion & Trend Following

### 6.1 AI-Enhanced Approaches

| Paper | Approach | Key Innovation | Reference |
|-------|----------|----------------|-----------|
| Slow Momentum + Fast Reversion | LSTM + Online CPD | Dynamically balances trend-following and mean-reversion based on detected regime changes | arXiv: 2105.13727 |
| Beyond Trend Following | Deep Learning trend prediction | CNNs/Transformers more robust to noise than linear models for regime detection | arXiv: 2407.13685 |
| Trading Factor Residuals | Transformer attention heads | Individual attention heads learn specific patterns (mean-reversion vs trend-following) | arXiv: 2412.11432 |
| LLM-Guided RL | Hybrid LLM + RL agent | LLM provides market context to RL agent; improved Sharpe + stability over pure RL | arXiv: 2508.02366 |
| Finance-Grounded Optimization | MLP + LSTM ensemble | Combines momentum alpha, reversion alpha, and mean reversion signals | arXiv: 2509.04541 |
| AI in Quantitative Investment (Survey) | Comprehensive survey | RL models preferred for end-to-end portfolio optimization; no need for explicit label construction | arXiv: 2503.21422 |

### 6.2 Key Findings

1. **Regime detection is the critical component** — Systems that dynamically switch between trend-following and mean-reversion based on detected regimes consistently outperform static strategies
2. **Online Changepoint Detection (CPD)** combined with deep learning networks significantly improves response to sudden market transitions
3. **Transformer attention mechanisms** naturally learn to separate mean-reversion and momentum patterns in different attention heads
4. **LLM+RL hybrids** outperform pure RL in both Sharpe ratio and stability (narrower confidence intervals)
5. **Caution on overfitting**: Out-of-sample Sharpe ratios exceeding 10 are reported in some papers (arXiv: 2412.11432), raising concerns about overfitting and missing transaction costs

### 6.3 Relevance to TradingAgents

The current Market Analyst agent uses classic indicators (MACD, RSI, Bollinger Bands, SMAs, EMAs, ATR, VWMA) but:
- Produces **prose analysis** rather than structured signals
- Does **not classify the current regime** (trending, mean-reverting, volatile)
- Has **no changepoint detection** capability
- Technical analysis is **interpreted by LLM** rather than used as quantitative constraints

A dedicated Regime Detection Agent could significantly improve decision quality by gating trade decisions based on the current market state.

---

## 7. Academic Landscape: Whale/Insider Transaction Following

### 7.1 Insider Trading Alpha: Academic Evidence

| Study | Finding | Alpha | Time Horizon |
|-------|---------|-------|-------------|
| Lakonishok & Lee (2001) | Insider purchases predict excess returns | 3-8% | 6-12 months |
| ScienceDirect (Nov 2024) | Speed of reaction to Form 4 filings creates abnormal returns | Significant | Days-weeks |
| ML models on Form 4 | Random Forest / Gradient Boosting on filing features | AUC 0.72-0.78 | Varies |
| Ensemble (insider + fundamentals + sentiment) | Combined signal models | AUC up to 0.82 | Varies |

### 7.2 Strongest Insider Signals

1. **Cluster buys**: Multiple insiders buying within a short timeframe — strongest bullish signal
2. **Open market purchases** (Form 4 code "P"): Insider paid market price with own cash
3. **Transaction volume relative to holdings**: Large increases in insider ownership carry more weight
4. **Buy vs Sell asymmetry**: Insiders sell for many reasons (taxes, diversification); they buy for one reason — they believe the stock will go up
5. **CEO/CFO purchases**: C-suite transactions carry more predictive weight than board member transactions

### 7.3 2025 Insider Landscape

- Overall U.S. market Insider Buy/Sell Ratio: **0.29** (well below long-term average of 0.42)
- Insiders broadly selling after strong 2023-2024 runs
- Sector divergence: Energy/advertising insiders buying on weakness; tech insiders selling into strength

### 7.4 Data Sources for Insider/Whale Tracking

| Platform | Type | Cost | API Available | Key Features |
|----------|------|------|---------------|-------------|
| SEC EDGAR | Official filings | Free | Yes | Form 4, 13F, 13D — raw data |
| OpenInsider | Aggregated insider data | Free | No (scraping) | Screener, cluster buy detection |
| Quiver Quantitative | Alt data platform | $25/mo | Yes (tiered) | Congress trading, insider, lobbying, contracts |
| Unusual Whales | Options flow + insider | Paid | Yes | Dark pool, options flow, insider |
| InsiderCompass | Real-time Form 4 | Paid | Yes | CFO signals, research portfolio |
| TrendVisor | SEC Form 4 tracker | Free tier | No | Real-time insider trade alerts |
| SECForm4.com | Insider analytics | Free/Paid | No | Buy/sell screener, analytics |
| Finviz | Insider screening | Free/Paid | No | Insider trading screener |

### 7.5 Relevance to TradingAgents

The system already has `get_insider_transactions()` and `get_insider_sentiment()` tools but:
- There is **no dedicated insider/whale analysis agent**
- Insider data is available to the Fundamentals Analyst and News Analyst but is **not systematically prioritized**
- **Cluster buy detection** is not implemented
- **Form 4 filing speed** (how quickly to react) is not considered
- The system does not track **13F institutional holdings changes**

---

## 8. Multi-Agent Trading Systems: State of the Art

### 8.1 Comparative Framework Analysis

| System | Year | Agents | Decision Method | Data Sources | Memory | Live Tested? | Reference |
|--------|------|--------|----------------|--------------|--------|-------------|-----------|
| **TradingAgents** | 2024 | 12 | Debate + consensus | 8+ (news, social, fundamentals, technicals, insider) | ChromaDB | No (backtest only) | arXiv: 2412.20138 |
| **QuantAgents** | 2025 | Multiple | Simulated trading | A-stock, HK-stock data | N/A | **Yes (live Q3'24-Q1'25)** | arXiv: 2510.04643 |
| **HedgeAgents** | 2025 | Fund mgr + experts | Multi-asset hedging | Stocks, Forex, Bitcoin | N/A | Simulated (3yr) | arXiv: 2502.13165 |
| **QuantAgent** | 2025 | 4 (Indicator, Pattern, Trend, Risk) | Structured reasoning | 9 instruments (BTC, NASDAQ futures) | N/A | HFT tested | arXiv: 2509.09995 |
| **MarketSenseAI** | 2024 | 1 (structured) | Single agent pipeline | SEC, news, prices | N/A | Backtest only | 2024 |
| **FinMem** | 2024 | 1 | Memory-augmented LLM | News, prices | 3-tier (working, episodic, semantic) | Backtest only | arXiv: 2311.13743 |
| **StockAgent** | 2024 | Multiple (simulation) | Emergent behavior | Simulated market | Agent personality | Market simulation | arXiv: 2407.18957 |
| **FinAgent** | 2024 | 1 | Multimodal (charts + text) | Prices, news, chart images | Dual-level reflection | Backtest only | 2024 |
| **FinRL** | 2020-24 | 1 RL agent | Reward optimization | OHLCV + indicators | Experience replay | Paper trading | arXiv: 2011.09607 |

### 8.2 Performance Comparison

| System | Return | Sharpe Ratio | Win Rate | Test Conditions | Reference |
|--------|--------|--------------|----------|-----------------|-----------|
| **TradingAgents (paper)** | 23-27% (3mo) | 5.6-8.2 | N/A | 3 stocks, 3 months backtest | arXiv: 2412.20138 |
| **TradingAgents (our deploy)** | **-$14,248** | **N/A** | **20%** | **90 trades, Jan 2026** | This report |
| **QuantAgents (live)** | 112% A-stock / 98% HK | **2.02 / 1.76** | **61% / 60%** | **Live trading 6 months** | arXiv: 2510.04643 |
| **HedgeAgents** | 70% annualized | N/A | N/A | 3-year simulation | arXiv: 2502.13165 |
| **MarketSenseAI** | 72.8% cumulative | **2.34** | N/A | Backtest | 2024 |
| **FinMem (AAPL)** | 37.6% | N/A | N/A | Backtest | arXiv: 2311.13743 |
| **FinAgent** | N/A | 1.57-2.32 | N/A | Crypto backtest | 2024 |
| **FinRL (Dow 30 ensemble)** | 63.7% | 1.98 | N/A | Jan'20-May'21 backtest | arXiv: 2011.09607 |
| **FinDPO** | 67% annual | **2.0** | N/A | With 5bps costs | arXiv: 2507.18417 |
| **FinRL Contest winner** | 134% | 1.08 | N/A | 229 trading days | arXiv: 2504.02281 |

### 8.3 Key Observations

1. **QuantAgents is the gold standard** — the only system with meaningful live trading validation (SR 2.02, 61% win rate in real A-stock/HK-stock markets)
2. **MarketSenseAI achieved SR 2.34 with a single agent** — structured reasoning can outperform multi-agent debate
3. **TradingAgents' paper results are outliers** — Sharpe ratios of 5.6-8.2 are not reproducible in broader testing
4. **Our deployed system underperforms all baselines** — 20% win rate with heavy losses
5. **The gap between backtest and live performance is significant** across all systems

---

## 9. Report vs Actual Market Data: Gap Analysis

### 9.1 SNOW (Snowflake) — January 16, 2026

| Dimension | TradingAgents Report | Actual Market Data |
|-----------|---------------------|--------------------|
| **Stock analyzed** | BIRK (Birkenstock) | Should be SNOW |
| **Price range in report** | $40-45 range | SNOW was at **$210.38** |
| **MACD signal** | -0.206, bearish for BIRK | Completely irrelevant to SNOW |
| **RSI reading** | 41.43 for BIRK | Wrong stock |
| **Decision** | BUY | Based on entirely wrong analysis |
| **SNOW actual close Jan 16** | Not analyzed | $210.38 |
| **SNOW actual close Jan 20** | Not analyzed | $206.21 (-2.0%) |
| **SNOW Jan 28 close** | N/A | $216.00 |

**Verdict**: Complete failure — decision made on wrong company's data.

### 9.2 AMBA (Ambarella) — January 16, 2026

| Dimension | TradingAgents Report | Actual Market Data |
|-----------|---------------------|--------------------|
| **Stock analyzed in report** | BIRK (Birkenstock) | Should be AMBA |
| **Decision** | BUY | Based on wrong analysis |
| **Entry price (correct from yfinance)** | $68.73 | $68.73 (this was correct in outcomes) |
| **AMBA actual Jan 20 close** | N/A | $65.74 |
| **P&L** | **-$435.04 (-4.35%)** | Correct calculation, wrong thesis |

**Verdict**: Entry price was correctly captured from market data, but the analysis leading to the BUY decision was based on Birkenstock's technicals, not Ambarella's.

### 9.3 RAPT (RAPT Therapeutics) — January 20, 2026

| Dimension | TradingAgents Report | Actual Market Data | Source |
|-----------|---------------------|--------------------|--------|
| **Clinical analysis** | Detailed ozureprobart Phase 2 data, JPM conference | Accurate | Report |
| **Analyst targets mentioned** | $50.50 consensus, $95 (Piper Sandler) | Accurate | Report |
| **Institutional ownership** | 99.1% | Accurate | Report |
| **Cash runway** | Through mid-2028 ($250M raise) | Accurate | Report |
| **GSK $2.2B acquisition** | **NOT MENTIONED** | **Announced Jan 20** | StockTwits, news |
| **Price Jan 16** | ~$35.10 | $35.10 | Yahoo Finance |
| **Price Jan 20 (post-acquisition)** | Not captured | **$57.57 (+64%)** | Yahoo Finance |
| **Current price (Jan 28)** | N/A | $57.65 (near acquisition price) | Yahoo Finance |
| **StockTwits current sentiment** | Not checked in real-time | Multiple shareholder investigation notices | StockTwits |

**Verdict**: Fundamental analysis was thorough and accurate for the clinical story, but the system completely missed the single event (GSK acquisition) that drove a 64% price move. The M&A catalyst was the only thing that mattered.

### 9.4 Aggregate Analysis: What Actual Prices Show

Using data from stockanalysis.com for tickers analyzed on Jan 16, 2026:

| Ticker | Decision | Entry (Jan 16) | Jan 20 Close | 1-Day Change | System Correct? |
|--------|----------|-----------------|--------------|-------------|-----------------|
| AGX | BUY | $383.18 | $383.86 | +0.18% | Yes |
| AMBA | BUY | $68.73 | $65.74 | -4.35% | No |
| AYI | BUY | $320.43 | $309.67 | -3.36% | No |
| SNOW | BUY | $210.38 | $206.21 | -1.98% | No |
| RAPT | Analysis done | ~$35.10 | $57.57 | +64.0% | N/A (M&A event) |

Of the validated trades from Jan 16: **1 winner, 3 losers** (25% win rate). The one winner (AGX, +0.18%) barely moved.

---

## 10. Is the Multi-Agent Setup Worth Pursuing?

### 10.1 Evidence FOR Multi-Agent

| Argument | Supporting Evidence |
|----------|-------------------|
| Reduces confirmation bias | Bull/Bear debate forces consideration of both sides (TradingAgents design) |
| Role specialization improves data processing | QuantAgents: SR 2.02 with 4 specialized agents in live trading |
| Multi-perspective risk assessment | HedgeAgents: 70% annualized with risky/safe/neutral debate |
| Mirrors real trading firm structure | Professional firms have separate research, trading, and risk functions |
| Scalable to new asset classes | HedgeAgents extended to stocks + forex + crypto |

### 10.2 Evidence AGAINST (or Caveats)

| Argument | Supporting Evidence |
|----------|-------------------|
| Single agent can match or beat multi-agent | MarketSenseAI: SR 2.34 with one agent + structured prompting |
| Cost is significantly higher | TradingAgents: 11+ LLM calls per decision vs. 1-3 for single agent |
| Bug surface area increases | Our system: report cross-contamination bug affects multiple agents |
| Debate can produce false consensus | Our system: 93% BUY rate despite bull/bear debate |
| Diminishing returns from more agents | No paper demonstrates monotonic improvement from adding agents |
| Latency increases linearly | Sequential analyst pipeline means each trade decision takes minutes |

### 10.3 Verdict

**The multi-agent architecture is worth pursuing, but with important caveats:**

1. **Fix the infrastructure first**. No amount of sophisticated reasoning compensates for feeding the wrong data to agents. The report cross-contamination bug alone explains most of the poor performance.

2. **More agents is NOT the answer**. Adding agents increases cost, latency, and bug surface area. Instead, make existing agents more effective:
   - Enable memory (ChromaDB) so agents learn from mistakes
   - Enable ACE so trading strategies accumulate over time
   - Switch to aggregated social sentiment instead of single-source

3. **Add agents only for genuinely distinct capabilities**:
   - A **Regime Detection Agent** adds value because no current agent does this
   - An **Event/Catalyst Agent** adds value because breaking news detection requires different tools than historical analysis
   - A **Quantitative Signal Agent** adds value by providing structured, non-negotiable constraints (e.g., "RSI > 80 = no new longs")

4. **Consider a hybrid architecture**: Use multi-agent for analysis/research but a single, well-calibrated agent for the final decision. The debate adds value for generating arguments, but the decision should be made by one agent with clear decision criteria.

---

## 11. Enhancement Roadmap

### Phase 1: Critical Fixes (Do First)

| # | Enhancement | Expected Impact | Complexity |
|---|-------------|-----------------|------------|
| 1 | **Fix report cross-contamination** — ensure `AgentState` is fully reset between ticker analyses in the batch pipeline | Eliminates wrong-stock decisions | Medium |
| 2 | **Fix BUY bias** — add explicit SELL/SHORT weighting in Research Manager and Risk Judge prompts; add quantitative guardrails (e.g., if RSI > 70 AND bearish MACD, force SELL consideration) | Enables balanced decisions | Low |
| 3 | **Populate confidence scores** — compute from analyst agreement, signal strength, memory match quality | Enables filtering weak signals | Low |
| 4 | **Validate all outcomes** — connect outcome tracker to actual yfinance price data; fix entries with price=0.0 | Accurate performance measurement | Low |

### Phase 2: Enable Existing Features

| # | Enhancement | Expected Impact | Complexity |
|---|-------------|-----------------|------------|
| 5 | **Enable ChromaDB memory** (`MEMORY_ENABLED=true`) | Agents learn from past mistakes | Low (already built) |
| 6 | **Enable ACE framework** (`ACE_ENABLED=true`) | Self-improving trading strategies | Low (already built) |
| 7 | **Switch to aggregated social sentiment** (`social_sentiment: "aggregated"`) | Combines Stocktwits + ApeWisdom + Finnhub | Low (config change) |
| 8 | **Use monthly bucketing for news** (already enabled) with improved deduplication | Better temporal coverage | Low |

### Phase 3: Better Data Sources

| # | Enhancement | Expected Impact | Complexity |
|---|-------------|-----------------|------------|
| 9 | **Add Benzinga or Polygon.io news feed** for real-time M&A and breaking news | Captures catalytic events like RAPT/GSK | Medium |
| 10 | **Add Quiver Quant API** ($25/mo) for Congress trading, insider cluster buys, and alternative data | Insider alpha signals | Medium |
| 11 | **Add OpenInsider scraping** for real-time Form 4 filing alerts | Fast insider signal detection | Medium |
| 12 | **Add SEC EDGAR RSS feed** for 8-K filings (material events, M&A announcements) | Captures material corporate events | Medium |

### Phase 4: New Agents (Add Only After Phases 1-3)

| # | Enhancement | Expected Impact | Complexity |
|---|-------------|-----------------|------------|
| 13 | **Regime Detection Agent** — classifies market as trending/mean-reverting/volatile using VIX, ADX, breadth indicators, yield curve | Gates decisions by market state | High |
| 14 | **Event/Catalyst Agent** — monitors breaking news, M&A, FDA, earnings surprises in real-time | Captures high-impact catalytic events | High |
| 15 | **Quantitative Signal Agent** — outputs structured hard constraints (RSI bands, Bollinger squeeze, volume anomalies) that override LLM prose | Prevents irrational decisions | Medium |
| 16 | **Insider/Whale Tracking Agent** — dedicated analysis of Form 4 cluster buys, 13F institutional changes | Captures insider alpha | Medium |

### Phase 5: Architecture Improvements

| # | Enhancement | Expected Impact | Complexity |
|---|-------------|-----------------|------------|
| 17 | **Implement position sizing based on confidence** — high confidence = larger position, low = smaller or HOLD | Risk-adjusted returns | Medium |
| 18 | **Add stop-loss and take-profit logic** — explicit exit criteria rather than 1-day holding | Limits downside, captures upside | Medium |
| 19 | **Parallelize analyst execution** — run all 4 analysts concurrently instead of sequentially | 4x faster decisions | Medium |
| 20 | **Implement RL layer on top** — use Reinforcement Learning to optimize when to override or trust agent recommendations | Learned meta-decision making | High |
| 21 | **Run extended backtest** — 50+ stocks, 12+ months, across bull/bear/sideways markets | Statistical significance | High |
| 22 | **Paper trade for 3+ months via Alpaca** before trusting live capital | Real-world validation | Low (time) |

---

## 12. Data Sources Reference Guide

### 12.1 Currently Used

| Source | API Key | Category | Configured Vendor |
|--------|---------|----------|-------------------|
| Yahoo Finance (yfinance) | None needed | OHLCV, Indicators | `core_stock_apis`, `technical_indicators` |
| Alpha Vantage | `ALPHA_VANTAGE_API_KEY` | Fundamentals, News, Insider | `fundamental_data`, `news_data` |
| Finnhub | `FINNHUB_API_KEY` | Social sentiment, Insider | Available but secondary |
| Stocktwits | None needed (scraping) | Social sentiment | `social_sentiment` (primary) |
| ApeWisdom | None needed | Reddit aggregated | Available but not primary |
| Polygon.io | `POLYGON_API_KEY` | Market data | Configured but not integrated as vendor |
| Google News | None needed (scraping) | News fallback | Fallback for `news_data` |
| OpenAI | `OPENAI_API_KEY` | News, Fundamentals (LLM-generated) | Fallback |

### 12.2 Recommended Additions

| Source | Cost | Category | Value Add | Priority |
|--------|------|----------|-----------|----------|
| **Benzinga News API** | $99-499/mo | Real-time news | Breaking M&A, earnings, FDA | HIGH |
| **Quiver Quantitative API** | $25/mo | Alternative data | Congress trades, insider clusters, lobbying | HIGH |
| **SEC EDGAR Full-Text Search** | Free | Regulatory filings | 8-K material events, 13F institutions | MEDIUM |
| **OpenInsider** | Free (scraping) | Insider transactions | Real-time Form 4 alerts | MEDIUM |
| **Unusual Whales** | $24-48/mo | Options flow | Dark pool activity, whale trades | LOW |
| **Twitter/X API** | $100-5000/mo | Social sentiment | Viral sentiment shifts | LOW (expensive) |
| **Whale Alert** (crypto) | Free/Paid | On-chain whale tracking | Large wallet movements | LOW (crypto only) |

---

## 13. Academic References

### Multi-Agent LLM Trading Systems

| # | Paper | Authors | Year | arXiv / Source | Key Result |
|---|-------|---------|------|---------------|------------|
| 1 | TradingAgents: Multi-Agents LLM Financial Trading Framework | Xiao, Sun, Luo, Wang | 2024 | [2412.20138](https://arxiv.org/abs/2412.20138) | Multi-agent debate + memory, SR 5.6-8.2 (3 stocks, 3mo) |
| 2 | QuantAgents: Multi-agent via Simulated Trading | — | 2025 | [2510.04643](https://arxiv.org/html/2510.04643v1) | **SR 2.02 in live A-stock trading**, 61% win rate |
| 3 | HedgeAgents: Balanced-aware Multi-agent Trading | — | 2025 | [2502.13165](https://arxiv.org/html/2502.13165v1) | 70% annualized return over 3 years |
| 4 | QuantAgent: Price-Driven Multi-Agent for HFT | — | 2025 | [2509.09995](https://arxiv.org/abs/2509.09995) | 4 specialized agents for HFT |
| 5 | StockAgent: Multi-Agent Stock Trading Simulator | Zhang et al. | 2024 | [2407.18957](https://arxiv.org/abs/2407.18957) | Emergent market behaviors, herding effects |
| 6 | StockBench: Can LLM Agents Trade Profitably? | — | 2025 | [2510.02209](https://arxiv.org/html/2510.02209v1) | First dynamic benchmark for LLM trading agents |
| 7 | InvestorBench: Financial Decision-Making Benchmark | — | 2024 | [2412.18174](https://arxiv.org/html/2412.18174v1) | Standardized LLM agent benchmark |

### Sentiment Analysis for Trading

| # | Paper | Authors | Year | arXiv / Source | Key Result |
|---|-------|---------|------|---------------|------------|
| 8 | FinBERT: Financial Sentiment Analysis | Araci | 2019 | [1908.10063](https://arxiv.org/abs/1908.10063) | ~95% accuracy on Financial PhraseBank |
| 9 | FinGPT: Open-Source Financial LLMs | Yang, Liu, Wang | 2023 | [2306.06031](https://arxiv.org/abs/2306.06031) | 78-87% sentiment accuracy, SR 0.8-1.2 |
| 10 | FinDPO: Preference Optimization for Financial Sentiment | — | 2025 | [2507.18417](https://arxiv.org/abs/2507.18417) | SR 2.0 with 5bps costs, +11% over SFT |
| 11 | FinLlama: Sentiment for Algorithmic Trading | — | 2024 | [2403.12285](https://arxiv.org/html/2403.12285v1) | 44.7% better returns than FinBERT |
| 12 | FinGPT: Dissemination-Aware Sentiment | — | 2025 | [2412.10823](https://arxiv.org/html/2412.10823) | News dissemination breadth improves prediction |
| 13 | Assessing FinGPT Capabilities & Limitations | — | 2025 | [2507.08015](https://arxiv.org/html/2507.08015v1) | Documents FinGPT's bullish bias |
| 14 | Can ChatGPT Forecast Stock Movements? | Lopez-Lira, Tang | 2023 | 2304.07619 | GPT sentiment: SR ~0.75 long-short |
| 15 | FinRL Contests: Benchmarking Financial RL | — | 2025 | [2504.02281](https://arxiv.org/html/2504.02281v3) | Best team: 134% return, SR 1.08 |
| 16 | MarketSenseAI | Guo et al. | 2024 | — | 72.8% cumulative return, SR 2.34 (single agent) |

### Mean Reversion, Trend Following & Regime Detection

| # | Paper | Authors | Year | arXiv / Source | Key Result |
|---|-------|---------|------|---------------|------------|
| 17 | Slow Momentum with Fast Reversion | — | 2021 | [2105.13727](https://arxiv.org/abs/2105.13727) | CPD + LSTM for adaptive momentum/reversion |
| 18 | Beyond Trend Following: Deep Learning | — | 2024 | [2407.13685](https://arxiv.org/html/2407.13685v1) | Deep learning > linear models for regime detection |
| 19 | Deep Learning for Trading Factor Residuals | — | 2024 | [2412.11432](https://arxiv.org/html/2412.11432v1) | Attention heads learn mean-reversion vs momentum |
| 20 | LLM-Guided RL in Quantitative Trading | — | 2025 | [2508.02366](https://arxiv.org/html/2508.02366v2) | Hybrid LLM+RL beats pure RL in Sharpe |
| 21 | Finance-Grounded Optimization for Algo Trading | Khubiyev | 2025 | [2509.04541](https://arxiv.org/pdf/2509.04541) | MLP + LSTM ensemble for multi-signal |
| 22 | From Deep Learning to LLMs: Survey of AI in Quant | — | 2025 | [2503.21422](https://arxiv.org/html/2503.21422v1) | Comprehensive survey, RL preferred for portfolio optimization |

### Insider/Whale Transaction Analysis

| # | Paper / Source | Year | Reference | Key Result |
|---|---------------|------|-----------|------------|
| 23 | Insider filings as trading signals — speed matters | 2024 | [ScienceDirect](https://www.sciencedirect.com/science/article/pii/S1544612324015435) | Prompt reaction to Form 4 creates abnormal returns |
| 24 | Quiver Quantitative (platform) | 2025 | [quiverquant.com](https://www.quiverquant.com/) | Congress + insider + alt data, API available |
| 25 | Unusual Whales (platform) | 2025 | [unusualwhales.com](https://unusualwhales.com/) | Options flow + dark pool + insider |
| 26 | InsiderCompass (platform) | 2025 | [insidercompass.com](https://www.insidercompass.com/) | Real-time Form 4 tracking with research tools |

### Memory & Self-Improvement

| # | Paper | Authors | Year | arXiv / Source | Key Result |
|---|-------|---------|------|---------------|------------|
| 27 | FinMem: Layered Memory for Trading | Yu et al. | 2024 | [2311.13743](https://arxiv.org/abs/2311.13743) | 37.6% return on AAPL with 3-tier memory |
| 28 | FinAgent: Multimodal Foundation Agent | Zhang et al. | 2024 | — | SR 1.57-2.32, dual-level reflection |
| 29 | AlphaFin: RAG-enhanced Stock Chain-of-Thought | Li et al. | 2024 | — | 6-12% improvement over zero-shot |
| 30 | LLM Agents for Investment Management (ACM Survey) | — | 2025 | [ACM ICAIF](https://dl.acm.org/doi/10.1145/3768292.3770387) | Survey of agent foundations and benchmarks |

---

## Appendix A: Outcome Data Summary

### Session: 20260123_053322 (Latest, 90 trades)

```
Total Trades:     90
Winning Trades:   18  (20.0%)
Losing Trades:    72  (80.0%)
Total P&L:        -$14,248.31
Average Win:      $48.65
Average Loss:     -$210.06

Decision Distribution:
  BUY:   84 trades (93.3%)  — Win Rate: 21.4%
  SELL:    0 trades  (0.0%)
  HOLD:    6 trades  (6.7%)

Market Regime:    "unknown" for all trades
Confidence:       null for all trades
Validated:        Partially (many entry_price = 0.0)
```

### Session: 20260121_171449 (22 trades)

```
Total Trades:     22
Winning Trades:    0   (0.0%)
Losing Trades:    22 (100.0%)
Total P&L:        $0.00  (all unvalidated)
BUY:              20 trades (90.9%)
SELL:              0 trades
Validated:        0 of 22
```

---

## Appendix B: Configuration Recommendations

### Immediate Changes (`.env`)

```bash
# Enable learning capabilities
MEMORY_ENABLED=true
ACE_ENABLED=true

# Use aggregated sentiment (combine all sources)
# In default_config.py or via env override:
SOCIAL_SENTIMENT_VENDOR=aggregated
```

### `default_config.py` Changes

```python
"data_vendors": {
    "core_stock_apis": "yfinance",
    "technical_indicators": "yfinance",
    "fundamental_data": "alpha_vantage",
    "news_data": "alpha_vantage",          # Consider adding benzinga
    "social_sentiment": "aggregated",       # Changed from "stocktwits"
}
```

---

*Report generated: January 28, 2026*
*Data sources: TradingAgents codebase, Yahoo Finance, StockTwits, StockAnalysis.com, arXiv, ACM Digital Library, ScienceDirect*
*Note: All trading performance figures from academic papers are backtested unless explicitly labeled as "live trading." Past performance does not guarantee future results.*

"""
Single-agent baseline for A/B comparison with the multi-agent system.

Fetches the same data (market, fundamentals, news, sentiment) and makes
a trading decision with a single LLM call instead of the 12-agent pipeline.

Dataset caching: On first analysis for a ticker/date, all fetched raw data
is saved to results/datasets/{TICKER}/{DATE}/dataset.json. Subsequent
analyses with different models load from cache — no API calls, instant replay.
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from tradingagents.llm import requires_responses_api, ChatOpenAIResponses
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.dataflows.config import set_config
from tradingagents.graph.signal_processing import (
    extract_decision_from_text,
    extract_confidence_from_text,
)

# Import the same data tools used by multi-agent system
from tradingagents.agents.utils.agent_utils import (
    get_stock_data,
    get_current_quote,
    get_indicators,
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_news,
    get_global_news,
)


SINGLE_AGENT_PROMPT = """You are a trading analyst making an investment decision for {ticker} to be executed at market open on {date}.

IMPORTANT: You are analyzing overnight before market opens on {date}.
Only consider information that would have been available BEFORE 9:30 AM ET on {date}.
If you see any timestamps in the data, ignore anything published after {date} 09:30 ET.
Your decision will be executed at market open, so base it on all pre-market information available.
Your decision applies to a holding period of 1-5 trading days. Focus on catalysts and momentum
that will play out within this timeframe. Ignore long-term (months/years) thesis arguments.

DATA DISCIPLINE (mandatory):
- Every price, indicator value, or statistic you cite MUST come verbatim from the data
  blocks below. Never estimate, extrapolate, or invent a number. If a value you need is
  not in the data, write "not in data" instead of guessing.
- Do not prefix price LEVELS with +/- signs; signs belong on returns/changes only.
- Quote each fact once from its canonical block; do not re-derive the same number
  differently in two places.

Analyze ALL of the following data carefully before making your decision.

== BROAD MARKET CONTEXT (S&P 500 / SPY) ==
{spy_market_data}

== BROAD MARKET INDICATORS (SPY) ==
{spy_indicators}

== SECTOR CONTEXT ({sector_etf}) ==
{sector_market_data}

== SECTOR INDICATORS ({sector_etf}) ==
{sector_indicators}

== {ticker} MARKET DATA ==
{market_data}

== {ticker} CURRENT QUOTE ==
{quote_data}

== {ticker} TECHNICAL INDICATORS ==
{indicators_data}

== {ticker} FUNDAMENTALS ==
{fundamentals_data}

== {ticker} BALANCE SHEET ==
{balance_sheet_data}

== {ticker} CASH FLOW ==
{cashflow_data}

== {ticker} INCOME STATEMENT ==
{income_data}

== {ticker} NEWS (Idiosyncratic) ==
{news_data}

== MACRO / GLOBAL NEWS (Systematic) ==
{global_news_data}
{extra_context}
== DECISION FRAMEWORK ==

**Step 1: Market Regime (Systematic Risk)**
Determine the broad market's current regime from the SPY data above:
- SPY above 50 SMA AND 200 SMA with positive MACD = BULL regime
- SPY below 50 SMA AND 200 SMA with negative MACD = BEAR regime
- Mixed signals = NEUTRAL regime

The market regime sets your prior:
- BULL: Default lean is BUY unless ticker-specific evidence overrides
- BEAR: Default lean is SELL unless ticker-specific evidence overrides
- NEUTRAL: No prior — decide purely on ticker-specific evidence

**Step 1b: Sector Regime ({sector_etf})**
Check if {ticker}'s sector is leading, lagging, or in line with the broad market:
- {sector_etf} outperforming SPY = sector tailwind (strengthens BUY case)
- {sector_etf} underperforming SPY = sector headwind (weakens BUY case)
- {sector_etf} in line with SPY = no sector-specific signal

**Step 2: Idiosyncratic Analysis ({ticker}-Specific Risk)**
Analyze {ticker}'s position relative to its own technicals and fundamentals:

Bullish signals (favor BUY):
- Price above 50 SMA (short-term uptrend)
- RSI 40-60 rising (momentum building, not overbought)
- MACD positive or bullish crossover
- Positive earnings surprise or guidance raise in news
- Strong free cash flow growth

Bearish signals (favor SELL):
- Price below both 50 SMA AND 200 SMA (breakdown)
- RSI > 75 with declining volume (exhaustion)
- MACD bearish divergence (price up but MACD declining)
- Negative earnings revision or guidance cut in news
- Deteriorating margins or rising debt

Neutral signals (favor HOLD):
- RSI 45-55 with flat MACD (no momentum)
- No material news catalysts
- Price trading within a tight range (<1% daily moves)

**Step 3: Combine Systematic + Idiosyncratic**
- BULL regime + bullish ticker = strong BUY
- BULL regime + bearish ticker = HOLD (systematic support limits downside)
- BEAR regime + bullish ticker = HOLD (headwinds limit upside)
- BEAR regime + bearish ticker = strong SELL
- NEUTRAL regime = follow ticker-specific signals

**Step 4: Hard Rules (apply before finalizing)**
- EVENT GATE: If a PRECOMPUTED EVENTS block above shows earnings or ex-dividend inside
  the hold window, cap CONFIDENCE at 0.6 and name the event in your risk assessment.
- DRAWDOWN CAUSALITY: If {ticker} is down more than 20% from its period high, you MUST
  state a causal hypothesis for the decline, supported by evidence from the news or
  fundamentals blocks. If no cause is identifiable in the data, write exactly
  "cause unknown — elevated risk" and treat it as a bearish factor.
- COMPUTE, DON'T ASSERT: Any risk/reward claim must use the support/resistance and ATR
  arithmetic from the PRECOMPUTED METRICS block (when present). Do not describe
  volatility or asymmetry qualitatively when the numbers are available.
- SEASONALITY: If citing quarterly cash-flow weakness, compare against the same quarter
  last year (professional-services firms routinely burn cash in Q1), or flag that the
  comparison is unavailable.

**Step 5: Structured Analysis**
Before deciding, work through:
a) What is the market regime? (cite SPY data)
b) Is the sector ({sector_etf}) leading or lagging the market?
c) List the 3 strongest arguments for BUY (cite specific data points)
d) List the 3 strongest arguments for SELL (cite specific data points)
e) Does {ticker}'s thesis align with or diverge from market and sector trends?
f) What is your final conviction and why?

Provide your analysis in this structure:
1. Market Regime Assessment (SPY trend, momentum, key levels)
2. Sector Assessment ({sector_etf} vs SPY — leading, lagging, or in line)
3. Technical Analysis ({ticker} price levels, trend, momentum vs market and sector)
4. Fundamental Assessment (valuation, earnings quality, balance sheet)
5. News Catalyst Analysis (macro events vs sector events vs company-specific news)
6. Risk Assessment (systematic risks, sector risks, and idiosyncratic risks)
7. Falsification Triggers (concrete, checkable conditions that would change your call)
8. Final Decision with rationale

CONFIDENCE SEMANTICS: CONFIDENCE is your estimated probability (0.0-1.0) that the
direction of your call is correct over the 1-5 day hold window. 0.5 means you have no
edge — use it only when the evidence is genuinely balanced, and prefer HOLD in that case.

You MUST end your response with exactly these four lines:
FINAL TRANSACTION PROPOSAL: **BUY** (or **SELL** or **HOLD**)
CONFIDENCE: **0.X**
REASSESS_TO_BUY: <one concrete trigger condition, e.g. "close above 50-day SMA ($X) on >1.2x avg volume">
MOVE_TO_SELL: <one concrete trigger condition, e.g. "close below 20-day support ($X)">
"""


DEFAULT_INDICATORS = ["rsi", "macd", "close_50_sma", "close_200_sma", "boll", "atr"]

# Sector ETF mapping for sector-level context (systematic risk, industry layer).
# Maps common tickers to their SPDR sector ETF.
SECTOR_ETF_MAP = {
    # Technology
    "AAPL": "XLK", "MSFT": "XLK", "GOOG": "XLK", "GOOGL": "XLK", "META": "XLK",
    "CRM": "XLK", "ADBE": "XLK", "ORCL": "XLK", "CSCO": "XLK", "INTC": "XLK",
    # Semiconductors
    "NVDA": "SMH", "AMD": "SMH", "AMBA": "SMH", "AVGO": "SMH", "QCOM": "SMH",
    "TSM": "SMH", "MU": "SMH", "MRVL": "SMH", "LRCX": "SMH", "KLAC": "SMH",
    # Healthcare
    "JNJ": "XLV", "UNH": "XLV", "PFE": "XLV", "ABBV": "XLV", "MRK": "XLV",
    "LLY": "XLV", "TMO": "XLV", "ABT": "XLV", "BMY": "XLV", "AMGN": "XLV",
    # Energy
    "XOM": "XLE", "CVX": "XLE", "COP": "XLE", "SLB": "XLE", "EOG": "XLE",
    "MPC": "XLE", "PSX": "XLE", "VLO": "XLE", "OXY": "XLE", "HAL": "XLE",
    # Financials
    "JPM": "XLF", "BAC": "XLF", "WFC": "XLF", "GS": "XLF", "MS": "XLF",
    "C": "XLF", "BLK": "XLF", "SCHW": "XLF", "AXP": "XLF", "USB": "XLF",
    # Consumer Staples
    "COST": "XLP", "PG": "XLP", "KO": "XLP", "PEP": "XLP", "WMT": "XLP",
    "MDLZ": "XLP", "CL": "XLP", "KMB": "XLP", "GIS": "XLP", "SJM": "XLP",
    # Consumer Discretionary
    "TSLA": "XLY", "AMZN": "XLY", "HD": "XLY", "NKE": "XLY", "MCD": "XLY",
    "SBUX": "XLY", "LOW": "XLY", "TJX": "XLY", "BKNG": "XLY", "CMG": "XLY",
    # Utilities
    "NEE": "XLU", "DUK": "XLU", "SO": "XLU", "D": "XLU", "AEP": "XLU",
    "SRE": "XLU", "EXC": "XLU", "XEL": "XLU", "ED": "XLU", "WEC": "XLU",
    # Industrials
    "CAT": "XLI", "GE": "XLI", "HON": "XLI", "UPS": "XLI", "BA": "XLI",
    "RTX": "XLI", "DE": "XLI", "LMT": "XLI", "MMM": "XLI", "UNP": "XLI",
    # Real Estate
    "AMT": "XLRE", "PLD": "XLRE", "CCI": "XLRE", "EQIX": "XLRE", "SPG": "XLRE",
    # Materials
    "LIN": "XLB", "APD": "XLB", "SHW": "XLB", "ECL": "XLB", "NEM": "XLB",
    # Communication Services
    "DIS": "XLC", "NFLX": "XLC", "TMUS": "XLC", "VZ": "XLC", "T": "XLC",
    "CMCSA": "XLC", "CHTR": "XLC",
}


def _get_sector_etf(ticker: str) -> str:
    """Return the sector ETF for a ticker, defaulting to XLK for unknown tickers."""
    return SECTOR_ETF_MAP.get(ticker.upper(), "XLK")


def _fetch_all_indicators(ticker: str, curr_date: str, look_back_days: int = 60) -> str:
    """Fetch all standard technical indicators for a ticker.

    Calls get_indicators once per indicator name to avoid the parameter
    mismatch that occurs when passing date args to the (symbol, indicator,
    curr_date, look_back_days) schema.
    """
    results = []
    for indicator in DEFAULT_INDICATORS:
        data = _fetch_data_safe(get_indicators, ticker, indicator, curr_date, look_back_days)
        if not data.startswith("Error"):
            results.append(f"=== {indicator.upper()} ===\n{data}")
    return "\n\n".join(results) if results else "No technical indicator data available"


def _smart_truncate(data: str, max_chars: int) -> str:
    """Truncate data at a line boundary instead of mid-line/mid-JSON."""
    if len(data) <= max_chars:
        return data
    cut = data[:max_chars].rfind('\n')
    if cut > max_chars * 0.5:
        return data[:cut] + "\n... [truncated]"
    return data[:max_chars] + "\n... [truncated]"


def _fetch_data_safe(tool_fn, *args) -> str:
    """Call a LangChain tool function safely, returning error string on failure.

    Dynamically reads the tool's parameter names from its schema so we pass
    the correct keys (e.g. 'ticker' not 'symbol').
    """
    try:
        # Read expected parameter names from the tool's Pydantic schema
        schema = {}
        if hasattr(tool_fn, 'args_schema'):
            schema = tool_fn.args_schema.schema()
        param_names = list(schema.get("properties", {}).keys())

        if param_names and len(args) <= len(param_names):
            invoke_args = dict(zip(param_names, args))
        elif len(args) == 1:
            invoke_args = {"ticker": args[0]}
        else:
            invoke_args = dict(zip(["ticker", "start_date", "end_date"], args))

        result = tool_fn.invoke(invoke_args)
        return str(result) if result else "No data available"
    except Exception as e:
        return f"Error fetching data: {e}"


class SingleAgentBaseline:
    """Single-agent baseline that makes trading decisions with one LLM call."""

    def __init__(self, model: str = None, config: Dict[str, Any] = None):
        """Initialize the single-agent baseline.

        Args:
            model: Model name to use. If None, uses config's deep_think_llm.
            config: Configuration dict. If None, uses DEFAULT_CONFIG.
        """
        self.config = config or DEFAULT_CONFIG
        set_config(self.config)

        # Create data cache directory
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        model = model or self.config["deep_think_llm"]
        self.model_name = model

        # Initialize LLM
        provider = self.config["llm_provider"].lower()
        if provider in ["openai", "ollama", "openrouter", "lm studio"]:
            if requires_responses_api(model):
                self.llm = ChatOpenAIResponses(model=model, base_url=self.config["backend_url"])
            else:
                self.llm = ChatOpenAI(model=model, base_url=self.config["backend_url"])
        elif provider == "anthropic":
            # ChatAnthropic auto-discovers endpoint from ANTHROPIC_API_KEY.
            # Only pass a custom URL if the user set a non-default endpoint (e.g., proxy).
            anthropic_kwargs = {"model": model, "max_tokens": 8192}
            backend = self.config.get("backend_url", "")
            if backend and "api.openai.com" not in backend and "api.anthropic.com" not in backend:
                anthropic_kwargs["anthropic_api_url"] = backend
            self.llm = ChatAnthropic(**anthropic_kwargs)
        elif provider == "google":
            self.llm = ChatGoogleGenerativeAI(model=model)
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

    def _dataset_cache_path(self, ticker: str, trade_date: str) -> Path:
        """Return path for cached dataset.

        Files are named {TICKER}_{DATE}_raw_dataset.json for human readability.
        """
        results_dir = self.config.get("results_dir", "./results")
        return Path(results_dir) / "datasets" / ticker / trade_date / f"{ticker}_{trade_date}_raw_dataset.json"

    def _load_cached_dataset(self, ticker: str, trade_date: str) -> Optional[Dict[str, str]]:
        """Load cached raw data if available.

        Checks new filename first, then falls back to legacy 'dataset.json'.
        """
        path = self._dataset_cache_path(ticker, trade_date)
        # Also check legacy filename for backward compatibility
        legacy_path = path.parent / "dataset.json"

        for candidate in [path, legacy_path]:
            if candidate.exists():
                try:
                    with open(candidate) as f:
                        data = json.load(f)
                    if all(k in data for k in ["market_data", "fundamentals_data", "news_data"]):
                        print(f"DATASET CACHE HIT: {ticker} {trade_date} ({candidate.name})")
                        return data
                except (json.JSONDecodeError, KeyError):
                    pass
        return None

    def _save_dataset_cache(self, ticker: str, trade_date: str, data: Dict[str, str]):
        """Save raw data to cache for replay."""
        path = self._dataset_cache_path(ticker, trade_date)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(data, f, indent=2)

    def analyze(self, ticker: str, trade_date: str,
                news_lookback_days: int = 7,
                news_article_limit: int = 50,
                extra_context: str = "") -> Dict[str, Any]:
        """Run single-agent analysis for a ticker on a date.

        Args:
            ticker: Stock ticker symbol
            trade_date: Analysis date in YYYY-MM-DD format
            news_lookback_days: Days to look back for news
            news_article_limit: Max news articles to fetch
            extra_context: Optional pre-validated prompt blocks (computed
                metrics, event calendar, peer relative strength) supplied
                by the caller. Inserted verbatim before the decision framework.

        Returns:
            Dict with decision, confidence, raw_response, triggers, and token counts
        """
        # Try loading from dataset cache first (instant replay, no API calls)
        cached = self._load_cached_dataset(ticker, trade_date)
        if cached:
            market_data = cached["market_data"]
            quote_data = cached["quote_data"]
            indicators_data = cached["indicators_data"]
            fundamentals_data = cached["fundamentals_data"]
            balance_sheet_data = cached["balance_sheet_data"]
            cashflow_data = cached["cashflow_data"]
            income_data = cached["income_data"]
            news_data = cached["news_data"]
            global_news_data = cached["global_news_data"]
            spy_market_data = cached.get("spy_market_data", "No SPY data available")
            spy_indicators = cached.get("spy_indicators", "No SPY indicator data available")
            sector_market_data = cached.get("sector_market_data", "No sector data available")
            sector_indicators = cached.get("sector_indicators", "No sector indicator data available")
            sector_etf = cached.get("sector_etf", _get_sector_etf(ticker))
        else:
            # Calculate date range for market data (90 days of history)
            end_date = trade_date
            trade_dt = datetime.strptime(trade_date, "%Y-%m-%d")
            start_dt = trade_dt - timedelta(days=90)
            start_date = start_dt.strftime("%Y-%m-%d")

            # News window: 14 days back through trade_date 9:30 AM ET.
            # Wide enough for drawdown forensics — a >20% decline needs its
            # causal catalyst in view, and 3 days routinely missed it.
            news_start_date = (trade_dt - timedelta(days=14)).strftime("%Y-%m-%d")

            # Fetch all data (same sources as multi-agent system)
            market_data = _fetch_data_safe(get_stock_data, ticker, start_date, end_date)
            quote_data = _fetch_data_safe(get_current_quote, ticker, trade_date)
            indicators_data = _fetch_all_indicators(ticker, end_date, look_back_days=60)
            fundamentals_data = _fetch_data_safe(get_fundamentals, ticker, trade_date)
            balance_sheet_data = _fetch_data_safe(get_balance_sheet, ticker)
            cashflow_data = _fetch_data_safe(get_cashflow, ticker)
            income_data = _fetch_data_safe(get_income_statement, ticker)
            # News: only from previous day to trade_date 9:30 AM ET (set in polygon_news.py)
            news_data = _fetch_data_safe(get_news, ticker, news_start_date, end_date)
            global_news_data = _fetch_data_safe(get_global_news, trade_date)

            # Fetch broad market context (SPY as systematic risk proxy)
            spy_market_data = _fetch_data_safe(get_stock_data, "SPY", start_date, end_date)
            spy_indicators = _fetch_all_indicators("SPY", end_date, look_back_days=60)

            # Fetch sector ETF context (industry-level systematic risk)
            sector_etf = _get_sector_etf(ticker)
            sector_market_data = _fetch_data_safe(get_stock_data, sector_etf, start_date, end_date)
            sector_indicators = _fetch_all_indicators(sector_etf, end_date, look_back_days=60)

            # Save to cache for future replay
            self._save_dataset_cache(ticker, trade_date, {
                "market_data": market_data,
                "quote_data": quote_data,
                "indicators_data": indicators_data,
                "fundamentals_data": fundamentals_data,
                "balance_sheet_data": balance_sheet_data,
                "cashflow_data": cashflow_data,
                "income_data": income_data,
                "news_data": news_data,
                "global_news_data": global_news_data,
                "spy_market_data": spy_market_data,
                "spy_indicators": spy_indicators,
                "sector_market_data": sector_market_data,
                "sector_indicators": sector_indicators,
                "sector_etf": sector_etf,
                "sentiment_data": "",
                "cached_at": datetime.now().isoformat(),
                "ticker": ticker,
                "trade_date": trade_date,
            })

        # Optional caller-supplied validated blocks (metrics, events, peers)
        extra_block = ""
        if extra_context:
            extra_block = f"\n== PRECOMPUTED METRICS & EVENTS (validated — prefer these numbers) ==\n{_smart_truncate(extra_context, 4000)}\n"

        # Construct prompt with smart truncation (avoids cutting mid-line/mid-JSON)
        prompt = SINGLE_AGENT_PROMPT.format(
            ticker=ticker,
            date=trade_date,
            sector_etf=sector_etf,
            spy_market_data=_smart_truncate(spy_market_data, 4000),
            spy_indicators=_smart_truncate(spy_indicators, 7000),
            sector_market_data=_smart_truncate(sector_market_data, 4000),
            sector_indicators=_smart_truncate(sector_indicators, 4000),
            market_data=_smart_truncate(market_data, 8000),
            quote_data=_smart_truncate(quote_data, 2000),
            indicators_data=_smart_truncate(indicators_data, 8000),
            fundamentals_data=_smart_truncate(fundamentals_data, 4000),
            balance_sheet_data=_smart_truncate(balance_sheet_data, 4000),
            cashflow_data=_smart_truncate(cashflow_data, 4000),
            income_data=_smart_truncate(income_data, 4000),
            news_data=_smart_truncate(news_data, 8000),
            global_news_data=_smart_truncate(global_news_data, 4000),
            extra_context=extra_block,
        )

        # Single LLM call
        from tradingagents.agents.utils.agent_utils import normalize_content

        response = self.llm.invoke(prompt)
        raw_text = normalize_content(response.content) if hasattr(response, "content") else str(response)

        # Extract decision and confidence — raises ValueError if unparseable
        try:
            decision = extract_decision_from_text(raw_text)
        except ValueError:
            # Pattern matching failed — try LLM extraction fallback
            extract_messages = [
                (
                    "system",
                    "Extract the investment decision from this text. "
                    "Respond with exactly one word: BUY, SELL, or HOLD.",
                ),
                ("human", raw_text),
            ]
            extract_result = normalize_content(
                self.llm.invoke(extract_messages).content
            ).strip().upper()

            if extract_result in ("BUY", "SELL", "HOLD"):
                decision = extract_result
            else:
                for keyword in ("BUY", "SELL", "HOLD"):
                    if keyword in extract_result:
                        decision = keyword
                        break
                else:
                    raise ValueError(
                        f"Could not extract decision from LLM response. "
                        f"LLM returned: {extract_result[:200]}"
                    )

        confidence = extract_confidence_from_text(raw_text)

        # Extract falsification triggers (best-effort; absent in older outputs)
        import re as _re
        triggers = {}
        m = _re.search(r"REASSESS_TO_BUY:\s*(.+)", raw_text)
        if m:
            triggers["reassess_to_buy"] = m.group(1).strip().strip("*<>")
        m = _re.search(r"MOVE_TO_SELL:\s*(.+)", raw_text)
        if m:
            triggers["move_to_sell"] = m.group(1).strip().strip("*<>")

        # Extract token usage if available
        input_tokens = 0
        output_tokens = 0
        llm_calls = 1
        if hasattr(response, "response_metadata"):
            meta = response.response_metadata
            # Anthropic format
            usage = meta.get("usage", {})
            if usage:
                input_tokens = usage.get("input_tokens", 0)
                output_tokens = usage.get("output_tokens", 0)
            # OpenAI format fallback
            if not input_tokens:
                usage = meta.get("token_usage", {})
                input_tokens = usage.get("prompt_tokens", 0)
                output_tokens = usage.get("completion_tokens", 0)

        return {
            "decision": decision,
            "confidence": confidence,
            "raw_response": raw_text,
            "model": self.model_name,
            "triggers": triggers,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "llm_calls": llm_calls,
        }

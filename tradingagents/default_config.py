import os

DEFAULT_CONFIG = {
    "project_dir": os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
    "results_dir": os.getenv("TRADINGAGENTS_RESULTS_DIR", "./results"),
    "data_dir": "/Users/yluo/Documents/Code/ScAI/FR1-data",
    "data_cache_dir": os.path.join(
        os.path.abspath(os.path.join(os.path.dirname(__file__), ".")),
        "dataflows/data_cache",
    ),
    # LLM settings (configurable via .env)
    "llm_provider": os.getenv("LLM_PROVIDER", "openai"),
    "deep_think_llm": os.getenv("DEEP_THINK_LLM", "gpt-4o"),
    "quick_think_llm": os.getenv("QUICK_THINK_LLM", "gpt-4o-mini"),
    "backend_url": os.getenv("LLM_BACKEND_URL", "https://api.openai.com/v1"),
    # ACE (Agentic Context Engineering) settings
    "ace_enabled": os.getenv("ACE_ENABLED", "false").lower() == "true",
    "ace_skillbook": os.getenv("ACE_SKILLBOOK", "./results/ace_skillbook.json"),
    # Memory/ChromaDB settings (embedding-based situation memory for researchers)
    "memory_enabled": os.getenv("MEMORY_ENABLED", "true").lower() == "true",
    # Debate and discussion settings
    "max_debate_rounds": 1,
    "max_risk_discuss_rounds": 1,
    "max_recur_limit": 100,
    # Data vendor configuration (all configurable via .env)
    # Category-level configuration (default for all tools in category)
    "data_vendors": {
        "core_stock_apis": os.getenv("DATA_VENDOR_STOCK", "polygon"),
        # Options: polygon, yfinance, alpha_vantage, local
        "technical_indicators": os.getenv("DATA_VENDOR_INDICATORS", "polygon"),
        # Options: polygon (SMA/EMA/RSI/MACD, others fallback to yfinance), yfinance, alpha_vantage, local
        "fundamental_data": os.getenv("DATA_VENDOR_FUNDAMENTALS", "alpha_vantage"),
        # Options: alpha_vantage, yfinance, openai, local (polygon requires $199/mo plan)
        "news_data": os.getenv("DATA_VENDOR_NEWS", "polygon,alpha_vantage"),
        # Options: polygon, alpha_vantage, openai, google, local (comma-separated for multi-source)
        "social_sentiment": os.getenv("SOCIAL_SENTIMENT_VENDOR", "stocktwits"),
        # Options: stocktwits (default), stockgeist, finnhub, aggregated
    },
    # Tool-level configuration (takes precedence over category-level)
    "tool_vendors": {
        # Example: "get_stock_data": "alpha_vantage",  # Override category default
        # Example: "get_news": "openai",               # Override category default
    },
    # News article limits (scale with recall period)
    # Keep limits balanced - 6mo/500 works, so scale proportionally
    "news_limits": {
        "default": int(os.getenv("NEWS_LIMIT_DEFAULT", "50")),
        "3mo": int(os.getenv("NEWS_LIMIT_3MO", "200")),
        "6mo": int(os.getenv("NEWS_LIMIT_6MO", "500")),
        "12mo": int(os.getenv("NEWS_LIMIT_12MO", "500")),  # Cap at 500 to avoid context overflow
    },
    # Social sentiment message limits (match news limits for balanced analysis)
    # Stocktwits: 200 requests/hour rate limit, 30 msgs per request = 6000 msgs/hour capacity
    "sentiment_limits": {
        "default": int(os.getenv("SENTIMENT_LIMIT_DEFAULT", "50")),
        "3mo": int(os.getenv("SENTIMENT_LIMIT_3MO", "200")),
        "6mo": int(os.getenv("SENTIMENT_LIMIT_6MO", "500")),
        "12mo": int(os.getenv("SENTIMENT_LIMIT_12MO", "500")),  # Max ~600 due to pagination limits
    },
    # News monthly bucketing - fetch from each month for true temporal diversity
    # When enabled, long recall periods (>30 days) fetch articles per month separately
    "news_monthly_bucketing": os.getenv("NEWS_MONTHLY_BUCKETING", "false").lower() == "true",
    # News company name fallback - retry with company name if ticker search returns few results
    # Useful for small-cap/obscure tickers that may not be well-indexed by ticker symbol
    "news_company_fallback": os.getenv("NEWS_COMPANY_FALLBACK", "true").lower() == "true",
}

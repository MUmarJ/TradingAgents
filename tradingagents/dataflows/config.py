import os
import tradingagents.default_config as default_config
from typing import Dict, Optional

# Use default config but allow it to be overridden
_config: Optional[Dict] = None
DATA_DIR: Optional[str] = None

# Local LLM providers that don't support OpenAI's web_search_preview
LOCAL_LLM_PROVIDERS = ["ollama", "lm studio"]
# Methods that require OpenAI's web_search_preview tool
OPENAI_ONLY_METHODS = ["get_news", "get_global_news", "get_fundamentals"]
# Data categories where Polygon is a valid vendor
POLYGON_CATEGORIES = ["core_stock_apis", "technical_indicators", "news_data"]


def validate_config(config: Dict):
    """Validate configuration and warn about incompatible settings."""
    data_vendors = config.get("data_vendors", {})
    tool_vendors = config.get("tool_vendors", {})
    llm_provider = config.get("llm_provider", "").lower()

    # Check local LLM + OpenAI vendor incompatibility
    if llm_provider in LOCAL_LLM_PROVIDERS:
        warnings = []
        if data_vendors.get("news_data") == "openai":
            warnings.append("data_vendors.news_data")
        if data_vendors.get("fundamental_data") == "openai":
            warnings.append("data_vendors.fundamental_data")

        for method in OPENAI_ONLY_METHODS:
            if tool_vendors.get(method) == "openai":
                warnings.append(f"tool_vendors.{method}")

        if warnings:
            print(f"WARNING: Using local LLM provider '{llm_provider}' with 'openai' data vendors.")
            print(f"  The following settings use OpenAI's web_search_preview which is not available locally:")
            for w in warnings:
                print(f"    - {w}")
            print("  Recommendation: Change these to 'alpha_vantage', 'polygon', 'google', or 'local'.")

    # Check Polygon API key when polygon is configured
    polygon_in_use = any(data_vendors.get(cat) == "polygon" for cat in POLYGON_CATEGORIES)
    polygon_in_tools = any(v == "polygon" for v in tool_vendors.values())

    if (polygon_in_use or polygon_in_tools) and not os.getenv("POLYGON_API_KEY"):
        print("WARNING: Polygon.io vendor configured but POLYGON_API_KEY is not set.")
        print("  Set POLYGON_API_KEY in your .env file or environment.")
        print("  Get a free API key at https://polygon.io/")

    # Warn if polygon is used for fundamentals (requires $199/mo)
    if data_vendors.get("fundamental_data") == "polygon":
        print("WARNING: Polygon.io fundamental data requires Advanced plan ($199/month).")
        print("  Free tier does NOT include financials. Use 'alpha_vantage' or 'yfinance' instead.")


def initialize_config():
    """Initialize the configuration with default values."""
    global _config, DATA_DIR
    if _config is None:
        _config = default_config.DEFAULT_CONFIG.copy()
        DATA_DIR = _config["data_dir"]


def set_config(config: Dict):
    """Update the configuration with custom values."""
    global _config, DATA_DIR
    if _config is None:
        _config = default_config.DEFAULT_CONFIG.copy()
    _config.update(config)
    DATA_DIR = _config["data_dir"]
    validate_config(_config)


def get_config() -> Dict:
    """Get the current configuration."""
    if _config is None:
        initialize_config()
    return _config.copy()


# Initialize with default config
initialize_config()

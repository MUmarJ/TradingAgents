from langchain_core.messages import HumanMessage, RemoveMessage


def normalize_content(content):
    """Normalize LLM response content to string.

    Gemini returns content as a list of dicts with 'text' keys,
    while OpenAI/Anthropic return a simple string.
    """
    if isinstance(content, list):
        return "".join(
            block.get("text", "") if isinstance(block, dict) else str(block)
            for block in content
        )
    return content


def get_period_description(days: int) -> str:
    """Convert lookback days to human-readable period description."""
    if days <= 7:
        return "the past week"
    elif days <= 30:
        return f"the past {days} days (approximately 1 month)"
    elif days <= 90:
        return f"the past {days} days (approximately 3 months)"
    elif days <= 180:
        return f"the past {days} days (approximately 6 months)"
    else:
        return f"the past {days} days (approximately 1 year)"


# Import tools from separate utility files
from tradingagents.agents.utils.core_stock_tools import (
    get_stock_data,
    get_current_quote
)
from tradingagents.agents.utils.technical_indicators_tools import (
    get_indicators
)
from tradingagents.agents.utils.fundamental_data_tools import (
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement
)
from tradingagents.agents.utils.news_data_tools import (
    get_news,
    get_insider_sentiment,
    get_insider_transactions,
    get_global_news
)
from tradingagents.agents.utils.social_sentiment_tools import (
    get_social_sentiment
)

def create_msg_delete():
    def delete_messages(state):
        """Clear messages and add placeholder for Anthropic compatibility"""
        messages = state["messages"]
        
        # Remove all messages
        removal_operations = [RemoveMessage(id=m.id) for m in messages]
        
        # Add a minimal placeholder message
        placeholder = HumanMessage(content="Continue")
        
        return {"messages": removal_operations + [placeholder]}
    
    return delete_messages


        
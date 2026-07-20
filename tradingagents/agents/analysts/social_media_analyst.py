from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from tradingagents.agents.utils.agent_utils import (
    get_social_sentiment, normalize_content, get_period_description,
)
from tradingagents.dataflows.config import get_config


def _get_sentiment_limit(lookback_days: int) -> int:
    """Get sentiment message limit based on lookback period (mirrors news limits)."""
    config = get_config()
    limits = config.get("sentiment_limits", {})

    if lookback_days <= 7:
        return limits.get("default", 50)
    elif lookback_days <= 90:
        return limits.get("3mo", 200)
    elif lookback_days <= 180:
        return limits.get("6mo", 500)
    else:
        return limits.get("12mo", 500)


def create_social_media_analyst(llm):
    def social_media_analyst_node(state):
        # Check if report is already cached - skip if so
        if state.get("sentiment_report"):
            print("CACHE: Skipping Social Media Analyst - report already loaded from cache")
            cached_msg = AIMessage(content="[Sentiment report loaded from cache]")
            return {"messages": [cached_msg], "sentiment_report": state["sentiment_report"]}

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        news_lookback_days = state.get("news_lookback_days", 7)
        period_desc = get_period_description(news_lookback_days)

        # Get sentiment limit matching news article limit for balance
        sentiment_limit = _get_sentiment_limit(news_lookback_days)

        tools = [
            get_social_sentiment,
        ]

        system_message = (
            f"You are a social media sentiment analyst tasked with analyzing public sentiment, social media discussions, and retail investor mood for a specific company over {period_desc}. "
            f"You will be given a company ticker and your objective is to write a comprehensive report on the social sentiment landscape around this company. "
            f"\n\nUse the get_social_sentiment(ticker, start_date, end_date, limit={sentiment_limit}) tool to fetch sentiment data from multiple sources:\n"
            f"- **Stocktwits**: Dedicated stock social platform with bullish/bearish sentiment labels (primary source)\n"
            f"- **Reddit**: Direct posts from r/wallstreetbets, r/stocks, r/investing (via PRAW)\n"
            f"- **Finnhub**: Social sentiment scores from Reddit and Twitter (if API key configured)\n"
            f"- **Reddit PRAW**: Direct Reddit posts with keyword sentiment analysis (if credentials configured)\n"
            f"\nCalculate start_date as {news_lookback_days} days before the current_date ({current_date}). "
            f"Fetch up to {sentiment_limit} messages/posts for thorough analysis.\n\n"
            f"Your analysis should include:\n"
            f"1. Overall sentiment direction (bullish/bearish/neutral)\n"
            f"2. Trending status on Reddit stock communities\n"
            f"3. Key themes and narratives in discussions\n"
            f"4. Notable sentiment shifts or spikes\n"
            f"5. Comparison of sentiment across different platforms\n"
            f"6. Implications for traders based on retail sentiment\n\n"
            "Provide detailed, actionable insights. Do not simply state 'sentiment is mixed' - dig deeper into what specific groups are saying and why."
            """ Make sure to append a Markdown table at the end summarizing key sentiment metrics from each source.""",
        )

        prompt = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    "You are a helpful AI assistant, collaborating with other assistants."
                    " Use the provided tools to progress towards answering the question."
                    " If you are unable to fully answer, that's OK; another assistant with different tools"
                    " will help where you left off. Execute what you can to make progress."
                    " If you or any other assistant has the FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** or deliverable,"
                    " prefix your response with FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL** so the team knows to stop."
                    " You have access to the following tools: {tool_names}.\n{system_message}"
                    "For your reference, the current date is {current_date}. The current company we want to analyze is {ticker}",
                ),
                MessagesPlaceholder(variable_name="messages"),
            ]
        )

        prompt = prompt.partial(system_message=system_message)
        prompt = prompt.partial(tool_names=", ".join([tool.name for tool in tools]))
        prompt = prompt.partial(current_date=current_date)
        prompt = prompt.partial(ticker=ticker)

        chain = prompt | llm.bind_tools(tools)

        result = chain.invoke(state["messages"])

        report = ""

        if len(result.tool_calls) == 0:
            report = normalize_content(result.content)

        return {
            "messages": [result],
            "sentiment_report": report,
        }

    return social_media_analyst_node

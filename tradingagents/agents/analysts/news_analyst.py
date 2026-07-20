from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import AIMessage
from tradingagents.agents.utils.agent_utils import (
    get_news, get_global_news, normalize_content, get_period_description,
)


def create_news_analyst(llm):
    def news_analyst_node(state):
        # Check if report is already cached - skip if so
        if state.get("news_report"):
            print("CACHE: Skipping News Analyst - report already loaded from cache")
            cached_msg = AIMessage(content="[News report loaded from cache]")
            return {"messages": [cached_msg], "news_report": state["news_report"]}

        current_date = state["trade_date"]
        ticker = state["company_of_interest"]
        news_lookback_days = state.get("news_lookback_days", 7)
        news_article_limit = state.get("news_article_limit", 50)
        period_desc = get_period_description(news_lookback_days)

        tools = [
            get_news,
            get_global_news,
        ]

        system_message = (
            f"You are a news researcher tasked with analyzing recent news and trends over {period_desc}. "
            f"Please write a comprehensive report of the current state of the world that is relevant for trading and macroeconomics. "
            f"Use the available tools: get_news(ticker, start_date, end_date, limit={news_article_limit}) for company-specific news "
            f"(calculate start_date as {news_lookback_days} days before current_date, fetch up to {news_article_limit} articles), "
            f"and get_global_news(curr_date, look_back_days={news_lookback_days}, limit={news_article_limit}) for broader macroeconomic news. "
            "Do not simply state the trends are mixed, provide detailed and finegrained analysis and insights that may help traders make decisions."
            """ Make sure to append a Markdown table at the end of the report to organize key points in the report, organized and easy to read."""
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
                    "For your reference, the current date is {current_date}. We are looking at the company {ticker}",
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
            "news_report": report,
        }

    return news_analyst_node

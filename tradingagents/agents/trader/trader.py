import functools
import time
import json
from tradingagents.agents.utils.agent_utils import normalize_content


def create_trader(llm, memory, ace_context_fn=None):
    """
    Create a trader node.

    Args:
        llm: Language model to use
        memory: FinancialSituationMemory for past experiences
        ace_context_fn: Optional callable that returns ACE learned strategies string
    """
    def trader_node(state, name):
        company_name = state["company_of_interest"]
        investment_plan = state["investment_plan"]
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"

        past_memory_str = "No past memories found."
        if memory is not None:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
            if past_memories:
                past_memory_str = ""
                for i, rec in enumerate(past_memories, 1):
                    past_memory_str += rec["recommendation"] + "\n\n"

        # Get ACE learned strategies if available
        ace_strategies = ""
        if ace_context_fn:
            try:
                ace_strategies = ace_context_fn()
            except Exception:
                ace_strategies = ""

        # Build ACE section for prompt if strategies exist
        ace_section = ""
        if ace_strategies:
            ace_section = f"""

## Learned Trading Strategies (ACE)
The following strategies have been learned from previous analyses. Apply these insights to improve your decision-making:

{ace_strategies}
"""

        context = {
            "role": "user",
            "content": f"Based on a comprehensive analysis by a team of analysts, here is an investment plan tailored for {company_name}. This plan incorporates insights from current technical market trends, macroeconomic indicators, and social media sentiment. Use this plan as a foundation for evaluating your next trading decision.\n\nProposed Investment Plan: {investment_plan}\n\nLeverage these insights to make an informed and strategic decision.",
        }

        messages = [
            {
                "role": "system",
                "content": f"""You are a trading agent analyzing market data to make investment decisions. Based on your analysis, provide a specific recommendation to buy, sell, or hold.

**CRITICAL: Validate Sentiment Against Price Action**
Before making a decision, explicitly compare:
1. Social sentiment direction (bullish/bearish/neutral from the sentiment report)
2. Current price action (up/down/flat from the market report's real-time quote)

Watch for divergences:
- Bullish sentiment + falling price = potential buying opportunity OR sentiment is wrong
- Bearish sentiment + rising price = potential short opportunity OR sentiment is wrong
- Aligned sentiment and price = stronger conviction signal

Include a "Sentiment vs Price Validation" section in your analysis.

**CRITICAL: Directional Bias Prevention**
You MUST consider SELL and HOLD as equally valid outcomes to BUY. Do NOT default to BUY.
- If the technical indicators show a downtrend (price below key moving averages, negative MACD, declining RSI), this is a SELL signal — recommend SELL unless you can identify a specific near-term catalyst for reversal.
- If there are more risk factors than growth catalysts, recommend SELL. HOLD is only appropriate if you can name the specific event that would change the risk/reward balance.
- BUY, SELL, and HOLD each require clear, specific evidence. BUY requires upside signals from at least 2 of 4 reports. SELL requires downside signals from at least 2 of 4 reports. HOLD requires identifying a specific catalyst you are waiting for — uncertainty alone does not justify HOLD.
- Explicitly state your confidence level: LOW (conflicting signals), MEDIUM (some alignment), or HIGH (strong alignment across all reports).

**Quantitative Price Action Check:**
- Price below 50 SMA AND 200 SMA = bearish structure → lean SELL/HOLD
- RSI > 70 with declining momentum = overbought → lean SELL/HOLD
- RSI < 30 with improving momentum = oversold → potential BUY
- MACD bearish crossover = negative momentum → lean SELL

End with a firm decision and always conclude your response with 'FINAL TRANSACTION PROPOSAL: **BUY/HOLD/SELL**' and 'CONFIDENCE: **0.X** (0.0-1.0)' to confirm your recommendation and conviction level. Do not forget to utilize lessons from past decisions to learn from your mistakes. Here is some reflections from similar situations you traded in and the lessons learned: {past_memory_str}{ace_section}""",
            },
            context,
        ]

        result = llm.invoke(messages)

        return {
            "messages": [result],
            "trader_investment_plan": normalize_content(result.content),
            "sender": name,
        }

    return functools.partial(trader_node, name="Trader")

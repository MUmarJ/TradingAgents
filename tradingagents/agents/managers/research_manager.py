import time
import json
from tradingagents.agents.utils.agent_utils import normalize_content


def create_research_manager(llm, memory):
    def research_manager_node(state) -> dict:
        history = state["investment_debate_state"].get("history", "")
        market_research_report = state["market_report"]
        sentiment_report = state["sentiment_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]

        investment_debate_state = state["investment_debate_state"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"

        past_memory_str = ""
        if memory is not None:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""As the portfolio manager and debate facilitator, your role is to critically evaluate this round of debate and make a definitive decision: align with the bear analyst, the bull analyst, or choose Hold.

**CRITICAL — Directional Bias Check:**
- Evaluate the bear case with equal weight as the bull case. SELL is just as valid as BUY.
- Do NOT default to any single decision when uncertain. Weigh the bear and bull arguments on their specific evidence, and choose the direction supported by the stronger case. HOLD is only justified when you can identify a specific pending catalyst (e.g., upcoming earnings, regulatory decision) worth waiting for.
- If price action is bearish (falling moving averages, negative MACD, RSI < 40), the bear case deserves extra weight regardless of bullish sentiment.
- If sentiment is bullish but price is falling, recognize this as a potential divergence that favors caution (HOLD) or bearishness (SELL).
- Before finalizing BUY, explicitly state what would need to be true for SELL to be correct instead, and vice versa.

Summarize the key points from both sides concisely, focusing on the most compelling evidence or reasoning. Your recommendation—Buy, Sell, or Hold—must be clear and actionable, grounded in the debate's strongest arguments.

Additionally, develop a detailed investment plan for the trader. This should include:

Your Recommendation: A decisive stance supported by the most convincing arguments.
Rationale: An explanation of why these arguments lead to your conclusion.
Strategic Actions: Concrete steps for implementing the recommendation.
Confidence Level: Rate your confidence in this decision (Low / Medium / High) based on signal alignment.
Take into account your past mistakes on similar situations. Use these insights to refine your decision-making and ensure you are learning and improving. Present your analysis conversationally, as if speaking naturally, without special formatting.

Here are the analyst reports for reference:
Market Report: {market_research_report}
Sentiment Report: {sentiment_report}
News Report: {news_report}
Fundamentals Report: {fundamentals_report}

Here are your past reflections on mistakes:
\"{past_memory_str}\"

Here is the debate:
Debate History:
{history}"""
        response = llm.invoke(prompt)

        new_investment_debate_state = {
            "judge_decision": normalize_content(response.content),
            "history": investment_debate_state.get("history", ""),
            "bear_history": investment_debate_state.get("bear_history", ""),
            "bull_history": investment_debate_state.get("bull_history", ""),
            "current_response": normalize_content(response.content),
            "count": investment_debate_state["count"],
        }

        return {
            "investment_debate_state": new_investment_debate_state,
            "investment_plan": normalize_content(response.content),
        }

    return research_manager_node

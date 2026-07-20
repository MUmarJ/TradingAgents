import time
import json
from tradingagents.agents.utils.agent_utils import normalize_content


def create_risk_manager(llm, memory):
    def risk_manager_node(state) -> dict:

        company_name = state["company_of_interest"]

        history = state["risk_debate_state"]["history"]
        risk_debate_state = state["risk_debate_state"]
        market_research_report = state["market_report"]
        news_report = state["news_report"]
        fundamentals_report = state["fundamentals_report"]
        sentiment_report = state["sentiment_report"]
        trader_plan = state["investment_plan"]

        curr_situation = f"{market_research_report}\n\n{sentiment_report}\n\n{news_report}\n\n{fundamentals_report}"

        past_memory_str = ""
        if memory is not None:
            past_memories = memory.get_memories(curr_situation, n_matches=2)
            for i, rec in enumerate(past_memories, 1):
                past_memory_str += rec["recommendation"] + "\n\n"

        prompt = f"""As the Risk Management Judge and Debate Facilitator, your goal is to evaluate the debate between three risk analysts—Risky, Neutral, and Safe/Conservative—and determine the best course of action for the trader. Your decision must result in a clear recommendation: Buy, Sell, or Hold.

**CRITICAL DECISION FRAMEWORK — Eliminate Directional Bias:**
- You MUST evaluate SELL as seriously as BUY. A SELL recommendation is equally valid and important.
- HOLD requires specific justification: you must identify a concrete catalyst or event you are waiting for. "Signals conflict" alone is NOT sufficient reason to HOLD — conflicting signals usually mean one direction is more supported than the other. Determine which.
- Before deciding BUY, explicitly ask: "What specific evidence would make this a SELL instead?"
- Before deciding SELL, explicitly ask: "What specific evidence would make this a BUY instead?"
- If the market report shows a downtrend (falling moving averages, negative MACD, RSI < 40), lean SELL — a confirmed downtrend is a SELL signal, not a reason to HOLD indefinitely.
- If sentiment is bullish but price action is bearish, prioritize price action over sentiment.

**CRITICAL: HOLD is the hardest decision to justify, not the easiest.**
HOLD means "the expected value of waiting exceeds the expected value of acting." You MUST state:
(a) What specific event or data point you are waiting for before acting.
(b) A concrete timeframe for that catalyst.
(c) Why acting now (BUY or SELL) has lower expected value than waiting.
If you cannot answer all three, you MUST choose BUY or SELL based on the weight of evidence.

**Quantitative Guardrails — Override LLM Prose When These Conditions Are Met:**
- If the market report mentions RSI > 70 AND declining MACD: recommend SELL or HOLD, never BUY.
- If the market report mentions RSI < 30 AND positive MACD crossover: this is a potential BUY signal.
- If price is below both 50 SMA and 200 SMA: this is a bear market condition — SELL or HOLD.
- If fundamentals show negative earnings growth AND declining revenue: lean SELL.

Guidelines for Decision-Making:
1. **Summarize Key Arguments**: Extract the strongest points from each analyst, focusing on relevance to the context.
2. **Provide Rationale**: Support your recommendation with direct quotes and counterarguments from the debate.
3. **Refine the Trader's Plan**: Start with the trader's original plan, **{trader_plan}**, and adjust it based on the analysts' insights.
4. **Learn from Past Mistakes**: Use lessons from **{past_memory_str}** to address prior misjudgments and improve the decision you are making now to make sure you don't make a wrong BUY/SELL/HOLD call that loses money.
5. **Confidence Assessment**: Rate your confidence in this decision on a scale of 0.0 to 1.0, where:
   - 0.0-0.3 = Low confidence (limited or unreliable data, cannot determine direction)
   - 0.4-0.6 = Moderate confidence (majority of signals point in one direction, but some counter-evidence exists)
   - 0.7-1.0 = High confidence (clear directional signal from at least 3 out of 4 reports)
   NOTE: Conflicting signals do NOT automatically mean low confidence. If 3 reports suggest SELL and 1 suggests BUY, that is moderate-to-high confidence in SELL, not low confidence warranting HOLD.
   Include this as: CONFIDENCE: [score]

Deliverables:
- A clear and actionable recommendation: Buy, Sell, or Hold.
- CONFIDENCE: [0.0-1.0] score reflecting signal quality.
- Detailed reasoning anchored in the debate, analyst reports, and past reflections.

You MUST end your response with exactly these two lines:
FINAL TRANSACTION PROPOSAL: **BUY** (or **SELL** or **HOLD**)
CONFIDENCE: **0.X**

---

**Reference Data (Analyst Reports):**
Market Report: {market_research_report}
Sentiment Report: {sentiment_report}
News Report: {news_report}
Fundamentals Report: {fundamentals_report}

**Analysts Debate History:**
{history}

---

Focus on actionable insights and continuous improvement. Build on past lessons, critically evaluate all perspectives, and ensure each decision advances better outcomes."""

        response = llm.invoke(prompt)

        new_risk_debate_state = {
            "judge_decision": normalize_content(response.content),
            "history": risk_debate_state["history"],
            "risky_history": risk_debate_state["risky_history"],
            "safe_history": risk_debate_state["safe_history"],
            "neutral_history": risk_debate_state["neutral_history"],
            "latest_speaker": "Judge",
            "current_risky_response": risk_debate_state["current_risky_response"],
            "current_safe_response": risk_debate_state["current_safe_response"],
            "current_neutral_response": risk_debate_state["current_neutral_response"],
            "count": risk_debate_state["count"],
        }

        return {
            "risk_debate_state": new_risk_debate_state,
            "final_trade_decision": normalize_content(response.content),
        }

    return risk_manager_node

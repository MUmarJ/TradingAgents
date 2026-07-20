# TradingAgents/graph/signal_processing.py

import re
from typing import Dict, Any, Optional
from langchain_core.language_models import BaseChatModel
from tradingagents.agents.utils.agent_utils import normalize_content


def extract_confidence_from_text(text: str) -> Optional[float]:
    """Extract confidence score from signal text using pattern matching.

    Looks for patterns like:
    - CONFIDENCE: 0.7
    - CONFIDENCE: **HIGH**
    - Confidence Level: Medium
    - CONFIDENCE: **0.85**

    Args:
        text: Signal text to parse

    Returns:
        Confidence as float (0.0-1.0) or None if not found
    """
    if not text:
        return None

    # Try numeric confidence first: CONFIDENCE: 0.7 or CONFIDENCE: **0.7**
    numeric_match = re.search(
        r"CONFIDENCE:\s*\*{0,2}\s*(0?\.\d+|1\.0|1)\s*\*{0,2}",
        text,
        re.IGNORECASE,
    )
    if numeric_match:
        return float(numeric_match.group(1))

    # Try categorical confidence: CONFIDENCE: **HIGH** or Confidence Level: Low
    cat_match = re.search(
        r"CONFIDENCE:\s*\*{0,2}\s*(LOW|MEDIUM|HIGH)\s*\*{0,2}",
        text,
        re.IGNORECASE,
    )
    if cat_match:
        level = cat_match.group(1).upper()
        return {"LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.8}.get(level, 0.5)

    # Try "Confidence Level:" variant
    level_match = re.search(
        r"Confidence\s+Level:\s*\*{0,2}\s*(Low|Medium|High)\s*\*{0,2}",
        text,
        re.IGNORECASE,
    )
    if level_match:
        level = level_match.group(1).upper()
        return {"LOW": 0.25, "MEDIUM": 0.5, "HIGH": 0.8}.get(level, 0.5)

    return None


def extract_decision_from_text(text: str) -> str:
    """Extract trading decision from signal text using pattern matching.

    Tries structured patterns first, falls back to keyword search.

    Args:
        text: Signal text to parse

    Returns:
        "BUY", "SELL", or "HOLD"
    """
    if not text:
        raise ValueError("Cannot extract decision from empty text")

    upper = text.upper()

    # Try structured pattern first: FINAL TRANSACTION PROPOSAL: **BUY**
    proposal_match = re.search(
        r"FINAL\s+TRANSACTION\s+PROPOSAL:\s*\*{0,2}\s*(BUY|SELL|HOLD)\s*\*{0,2}",
        upper,
    )
    if proposal_match:
        return proposal_match.group(1)

    # Try "recommendation: Buy/Sell/Hold"
    rec_match = re.search(
        r"RECOMMENDATION:\s*\*{0,2}\s*(BUY|SELL|HOLD)\s*\*{0,2}",
        upper,
    )
    if rec_match:
        return rec_match.group(1)

    # Try "FINAL DECISION: BUY/SELL/HOLD"
    final_dec_match = re.search(
        r"FINAL\s+DECISION:\s*\*{0,2}\s*(BUY|SELL|HOLD)\s*\*{0,2}",
        upper,
    )
    if final_dec_match:
        return final_dec_match.group(1)

    # Try "DECISION: BUY/SELL/HOLD"
    dec_match = re.search(
        r"DECISION:\s*\*{0,2}\s*(BUY|SELL|HOLD)\s*\*{0,2}",
        upper,
    )
    if dec_match:
        return dec_match.group(1)

    # No structured pattern found — raise instead of silently defaulting to HOLD
    raise ValueError(
        f"No structured decision pattern found in text. "
        f"Last 200 chars: ...{text[-200:]}"
    )


def extract_technical_signals(market_report: str) -> Dict[str, Any]:
    """Parse quantitative signals from market report text.

    Extracts RSI, MACD direction, SMA positions via regex from
    the market analyst's report.

    Args:
        market_report: Text of the market analyst report

    Returns:
        Dict with rsi, macd_direction, sma_position, and signals_summary
    """
    signals = {
        "rsi": None,
        "macd_direction": None,
        "price_vs_sma50": None,
        "price_vs_sma200": None,
        "signals_summary": "",
    }

    if not market_report:
        return signals

    upper = market_report.upper()

    # Extract RSI value
    rsi_match = re.search(r"RSI[:\s]*(?:IS\s+)?(?:AT\s+)?(\d+\.?\d*)", upper)
    if rsi_match:
        signals["rsi"] = float(rsi_match.group(1))

    # Extract MACD direction
    if re.search(r"MACD.*(?:BEARISH|NEGATIVE)\s*(?:CROSSOVER|DIVERGENCE|SIGNAL)", upper):
        signals["macd_direction"] = "bearish"
    elif re.search(r"MACD.*(?:BULLISH|POSITIVE)\s*(?:CROSSOVER|CONVERGENCE|SIGNAL)", upper):
        signals["macd_direction"] = "bullish"
    elif re.search(r"BEARISH.*MACD", upper):
        signals["macd_direction"] = "bearish"
    elif re.search(r"BULLISH.*MACD", upper):
        signals["macd_direction"] = "bullish"

    # Extract SMA position (flexible prefix — may follow "and", "price", or sentence start)
    if re.search(r"(?:BELOW|UNDER)\s+(?:THE\s+)?(?:50|50-DAY)\s*(?:-\s*)?(?:SMA|MA|MOVING)", upper):
        signals["price_vs_sma50"] = "below"
    elif re.search(r"(?:ABOVE|OVER)\s+(?:THE\s+)?(?:50|50-DAY)\s*(?:-\s*)?(?:SMA|MA|MOVING)", upper):
        signals["price_vs_sma50"] = "above"

    if re.search(r"(?:BELOW|UNDER)\s+(?:THE\s+)?(?:200|200-DAY)\s*(?:-\s*)?(?:SMA|MA|MOVING)", upper):
        signals["price_vs_sma200"] = "below"
    elif re.search(r"(?:ABOVE|OVER)\s+(?:THE\s+)?(?:200|200-DAY)\s*(?:-\s*)?(?:SMA|MA|MOVING)", upper):
        signals["price_vs_sma200"] = "above"

    # Build summary
    parts = []
    if signals["rsi"] is not None:
        rsi = signals["rsi"]
        if rsi > 70:
            parts.append(f"RSI at {rsi:.0f}: overbought territory (bearish signal)")
        elif rsi < 30:
            parts.append(f"RSI at {rsi:.0f}: oversold territory (bullish signal)")
        else:
            parts.append(f"RSI at {rsi:.0f}: neutral range")

    if signals["macd_direction"]:
        parts.append(f"MACD: {signals['macd_direction']} signal")

    if signals["price_vs_sma50"]:
        parts.append(f"Price {signals['price_vs_sma50']} 50-day SMA")

    if signals["price_vs_sma200"]:
        parts.append(f"Price {signals['price_vs_sma200']} 200-day SMA")

    signals["signals_summary"] = "; ".join(parts) if parts else "No technical signals extracted"
    return signals


def format_technical_opinion(signals: Dict[str, Any]) -> str:
    """Format technical signals into a structured opinion block for prompt injection.

    Presents ALL perspectives (bullish, bearish, neutral) based on the signals.

    Args:
        signals: Dict from extract_technical_signals()

    Returns:
        Formatted string for injection into risk manager prompt
    """
    if not signals.get("signals_summary") or signals["signals_summary"] == "No technical signals extracted":
        return ""

    lines = ["== TECHNICAL SIGNALS SUMMARY =="]
    lines.append(signals["signals_summary"])

    # Count bullish vs bearish signals
    bearish_count = 0
    bullish_count = 0

    if signals.get("rsi") is not None:
        if signals["rsi"] > 70:
            bearish_count += 1
        elif signals["rsi"] < 30:
            bullish_count += 1

    if signals.get("macd_direction") == "bearish":
        bearish_count += 1
    elif signals.get("macd_direction") == "bullish":
        bullish_count += 1

    if signals.get("price_vs_sma50") == "below":
        bearish_count += 1
    elif signals.get("price_vs_sma50") == "above":
        bullish_count += 1

    if signals.get("price_vs_sma200") == "below":
        bearish_count += 1
    elif signals.get("price_vs_sma200") == "above":
        bullish_count += 1

    if bearish_count > 0 and bullish_count > 0:
        lines.append(f"WARNING: Technical signals conflict ({bullish_count} bullish, {bearish_count} bearish). Weight accordingly.")
    elif bearish_count >= 2:
        lines.append(f"CAUTION: Multiple bearish technical signals ({bearish_count} bearish, {bullish_count} bullish).")
    elif bullish_count >= 2:
        lines.append(f"NOTE: Multiple bullish technical signals ({bullish_count} bullish, {bearish_count} bearish).")

    return "\n".join(lines)


def apply_hard_override(decision: str, signals: Dict[str, Any]) -> tuple:
    """Hard override only when ALL extreme conditions met simultaneously.

    Only overrides BUY -> HOLD when:
    - RSI > 80 AND
    - MACD is bearish AND
    - Price below BOTH 50 AND 200 SMA

    Args:
        decision: Current decision (BUY/SELL/HOLD)
        signals: Dict from extract_technical_signals()

    Returns:
        Tuple of (final_decision, was_overridden, override_reason)
    """
    if decision != "BUY":
        return decision, False, ""

    rsi = signals.get("rsi")
    macd = signals.get("macd_direction")
    sma50 = signals.get("price_vs_sma50")
    sma200 = signals.get("price_vs_sma200")

    # ALL conditions must be met for override
    if (rsi is not None and rsi > 80
            and macd == "bearish"
            and sma50 == "below"
            and sma200 == "below"):
        reason = (f"HARD OVERRIDE: BUY->HOLD (RSI={rsi:.0f}>80, "
                  f"bearish MACD, below both 50/200 SMA)")
        return "HOLD", True, reason

    return decision, False, ""


class SignalProcessor:
    """Processes trading signals to extract actionable decisions and metadata."""

    def __init__(self, quick_thinking_llm: BaseChatModel):
        """Initialize with an LLM for processing."""
        self.quick_thinking_llm = quick_thinking_llm

    def process_signal(self, full_signal: str) -> str:
        """
        Process a full trading signal to extract the core decision.

        Uses deterministic pattern matching first, falls back to LLM only
        if patterns are not found. Raises ValueError if no decision can
        be extracted — never silently defaults to HOLD.

        Args:
            full_signal: Complete trading signal text

        Returns:
            Extracted decision (BUY, SELL, or HOLD)

        Raises:
            ValueError: If no decision can be extracted from the text
        """
        # Try deterministic extraction first (faster, no API call)
        try:
            return extract_decision_from_text(full_signal)
        except ValueError:
            pass  # No pattern found — use LLM fallback

        # LLM fallback: ask model to extract the decision
        messages = [
            (
                "system",
                "You are an efficient assistant designed to analyze paragraphs or financial reports provided by a group of analysts. "
                "Your task is to extract the investment decision: SELL, BUY, or HOLD. "
                "Provide only the extracted decision (SELL, BUY, or HOLD) as your output, without adding any additional text or information.",
            ),
            ("human", full_signal),
        ]
        raw = normalize_content(
            self.quick_thinking_llm.invoke(messages).content
        ).strip().upper()

        if raw in ("BUY", "SELL", "HOLD"):
            return raw
        for keyword in ("BUY", "SELL", "HOLD"):
            if keyword in raw:
                return keyword

        raise ValueError(
            f"LLM fallback could not extract decision. "
            f"LLM returned: {raw[:200]}"
        )

    def process_signal_full(self, full_signal: str) -> Dict[str, Any]:
        """
        Process a full trading signal to extract decision and metadata.

        Args:
            full_signal: Complete trading signal text

        Returns:
            Dict with 'decision' (str) and 'confidence' (float or None)
        """
        decision = self.process_signal(full_signal)
        confidence = extract_confidence_from_text(full_signal)

        return {
            "decision": decision,
            "confidence": confidence,
        }

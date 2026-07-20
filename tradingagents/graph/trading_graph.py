# TradingAgents/graph/trading_graph.py

import os
from pathlib import Path
import json
from datetime import date
from typing import Dict, Any, Tuple, List, Optional

from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI

from langgraph.prebuilt import ToolNode

from tradingagents.llm import requires_responses_api, ChatOpenAIResponses

from tradingagents.agents import *
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.ace import create_trading_ace, TradingACE
from tradingagents.agents.utils.memory import FinancialSituationMemory
from tradingagents.agents.utils.agent_states import (
    AgentState,
    InvestDebateState,
    RiskDebateState,
)
from tradingagents.dataflows.config import set_config

# Import the new abstract tool methods from agent_utils
from tradingagents.agents.utils.agent_utils import (
    get_stock_data,
    get_current_quote,
    get_indicators,
    get_fundamentals,
    get_balance_sheet,
    get_cashflow,
    get_income_statement,
    get_news,
    get_insider_sentiment,
    get_insider_transactions,
    get_global_news,
    get_social_sentiment,
)

from .conditional_logic import ConditionalLogic
from .setup import GraphSetup
from .propagation import Propagator
from .reflection import Reflector
from .signal_processing import (
    SignalProcessor,
    extract_technical_signals,
    format_technical_opinion,
    apply_hard_override,
)


class TradingAgentsGraph:
    """Main class that orchestrates the trading agents framework."""

    def __init__(
        self,
        selected_analysts=["market", "social", "news", "fundamentals"],
        debug=False,
        config: Dict[str, Any] = None,
    ):
        """Initialize the trading agents graph and components.

        Args:
            selected_analysts: List of analyst types to include
            debug: Whether to run in debug mode
            config: Configuration dictionary. If None, uses default config
        """
        self.debug = debug
        self.config = config or DEFAULT_CONFIG

        # Update the interface's config
        set_config(self.config)

        # Create necessary directories
        os.makedirs(
            os.path.join(self.config["project_dir"], "dataflows/data_cache"),
            exist_ok=True,
        )

        # Initialize LLMs
        if self.config["llm_provider"].lower() in ["openai", "ollama", "openrouter", "lm studio"]:
            # Select LLM class based on model - newer models require Responses API
            deep_model = self.config["deep_think_llm"]
            quick_model = self.config["quick_think_llm"]

            if requires_responses_api(deep_model):
                self.deep_thinking_llm = ChatOpenAIResponses(model=deep_model, base_url=self.config["backend_url"])
            else:
                self.deep_thinking_llm = ChatOpenAI(model=deep_model, base_url=self.config["backend_url"])

            if requires_responses_api(quick_model):
                self.quick_thinking_llm = ChatOpenAIResponses(model=quick_model, base_url=self.config["backend_url"])
            else:
                self.quick_thinking_llm = ChatOpenAI(model=quick_model, base_url=self.config["backend_url"])
        elif self.config["llm_provider"].lower() == "anthropic":
            # ChatAnthropic auto-discovers endpoint from ANTHROPIC_API_KEY.
            # Only pass a custom URL if the user set a non-default endpoint (e.g., proxy).
            anthropic_kwargs = {"max_tokens": 8192}
            backend = self.config.get("backend_url", "")
            if backend and "api.openai.com" not in backend and "api.anthropic.com" not in backend:
                anthropic_kwargs["anthropic_api_url"] = backend
            self.deep_thinking_llm = ChatAnthropic(model=self.config["deep_think_llm"], **anthropic_kwargs)
            self.quick_thinking_llm = ChatAnthropic(model=self.config["quick_think_llm"], **anthropic_kwargs)
        elif self.config["llm_provider"].lower() == "google":
            self.deep_thinking_llm = ChatGoogleGenerativeAI(model=self.config["deep_think_llm"])
            self.quick_thinking_llm = ChatGoogleGenerativeAI(model=self.config["quick_think_llm"])
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config['llm_provider']}")
        
        # Initialize memories (if enabled)
        self.memory_enabled = self.config.get("memory_enabled", True)
        self._memory_cache = {}  # Cache scoped memories per ticker
        if self.memory_enabled:
            # Create initial unscoped memories (replaced per-ticker in propagate)
            self.bull_memory = FinancialSituationMemory("bull_memory", self.config)
            self.bear_memory = FinancialSituationMemory("bear_memory", self.config)
            self.trader_memory = FinancialSituationMemory("trader_memory", self.config)
            self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config)
            self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config)
            print("MEMORY: ChromaDB memory system enabled")
        else:
            self.bull_memory = None
            self.bear_memory = None
            self.trader_memory = None
            self.invest_judge_memory = None
            self.risk_manager_memory = None
            print("MEMORY: Memory system disabled")

        # Create tool nodes
        self.tool_nodes = self._create_tool_nodes()

        # Initialize ACE engine if enabled (must be before GraphSetup)
        self.ace_engine = None
        if self.config.get("ace_enabled", False):
            try:
                skillbook_path = self.config.get("ace_skillbook", "./results/ace_skillbook.json")
                self.ace_engine = create_trading_ace(self.config, skillbook_path=skillbook_path)
                print(f"ACE: Engine initialized (skillbook: {skillbook_path})")
            except Exception as e:
                print(f"ACE: Failed to initialize - {e}")
                self.ace_engine = None

        # Initialize components
        self.selected_analysts = selected_analysts
        self.conditional_logic = ConditionalLogic()
        self.graph_setup = GraphSetup(
            self.quick_thinking_llm,
            self.deep_thinking_llm,
            self.tool_nodes,
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
            self.conditional_logic,
            ace_context_fn=self.get_ace_context if self.ace_engine else None,
        )

        self.propagator = Propagator()
        self.reflector = Reflector(self.quick_thinking_llm)
        self.signal_processor = SignalProcessor(self.quick_thinking_llm)

        # State tracking
        self.curr_state = None
        self.ticker = None
        self.log_states_dict = {}  # date to full state dict

        # Set up the graph
        self.graph = self.graph_setup.setup_graph(selected_analysts)

    def _create_tool_nodes(self) -> Dict[str, ToolNode]:
        """Create tool nodes for different data sources using abstract methods."""
        return {
            "market": ToolNode(
                [
                    # Core stock data tools
                    get_stock_data,
                    get_current_quote,
                    # Technical indicators
                    get_indicators,
                ]
            ),
            "social": ToolNode(
                [
                    # Social sentiment tools
                    get_social_sentiment,
                ]
            ),
            "news": ToolNode(
                [
                    # News and insider information
                    get_news,
                    get_global_news,
                    get_insider_sentiment,
                    get_insider_transactions,
                ]
            ),
            "fundamentals": ToolNode(
                [
                    # Fundamental analysis tools
                    get_fundamentals,
                    get_balance_sheet,
                    get_cashflow,
                    get_income_statement,
                ]
            ),
        }

    def _create_scoped_memories(self, ticker: str):
        """Create or retrieve ticker-scoped memories to prevent cross-contamination.

        Each ticker gets its own ChromaDB collections (e.g. "AAPL_bull_memory")
        so memories from one ticker's analysis don't bleed into another's.

        Args:
            ticker: Ticker symbol to scope memories to
        """
        if not self.memory_enabled:
            return

        if ticker in self._memory_cache:
            memories = self._memory_cache[ticker]
            self.bull_memory = memories["bull"]
            self.bear_memory = memories["bear"]
            self.trader_memory = memories["trader"]
            self.invest_judge_memory = memories["invest_judge"]
            self.risk_manager_memory = memories["risk_manager"]
            print(f"MEMORY: Using cached scoped memories for {ticker}")
            return

        self.bull_memory = FinancialSituationMemory("bull_memory", self.config, scope=ticker)
        self.bear_memory = FinancialSituationMemory("bear_memory", self.config, scope=ticker)
        self.trader_memory = FinancialSituationMemory("trader_memory", self.config, scope=ticker)
        self.invest_judge_memory = FinancialSituationMemory("invest_judge_memory", self.config, scope=ticker)
        self.risk_manager_memory = FinancialSituationMemory("risk_manager_memory", self.config, scope=ticker)

        self._memory_cache[ticker] = {
            "bull": self.bull_memory,
            "bear": self.bear_memory,
            "trader": self.trader_memory,
            "invest_judge": self.invest_judge_memory,
            "risk_manager": self.risk_manager_memory,
        }
        print(f"MEMORY: Created scoped memories for {ticker}")

    def _rebuild_graph_with_memories(self):
        """Rebuild the graph with current memory references.

        Called after _create_scoped_memories() to ensure agent closures
        use the correct ticker-scoped memory objects.
        """
        self.graph_setup.set_memories(
            self.bull_memory,
            self.bear_memory,
            self.trader_memory,
            self.invest_judge_memory,
            self.risk_manager_memory,
        )
        self.graph = self.graph_setup.setup_graph(self.selected_analysts)

    def propagate(self, company_name, trade_date, cached_reports: Dict[str, str] = None):
        """Run the trading agents graph for a company on a specific date.

        Args:
            company_name: Ticker symbol of the company
            trade_date: Date of analysis in YYYY-MM-DD format
            cached_reports: Optional dict of pre-loaded reports to skip analyst steps.
                           Keys: "market_report", "sentiment_report", "news_report", "fundamentals_report"
        """
        self.ticker = company_name

        # Scope memories to this ticker and rebuild graph with new memory refs
        self._create_scoped_memories(company_name)
        if self.memory_enabled:
            self._rebuild_graph_with_memories()

        # Initialize state
        init_agent_state = self.propagator.create_initial_state(
            company_name, trade_date
        )

        # Inject cached reports into initial state if provided
        if cached_reports:
            for report_key, content in cached_reports.items():
                if report_key in init_agent_state and content:
                    init_agent_state[report_key] = content
                    print(f"CACHE: Loaded {report_key} from cache ({len(content)} chars)")

        args = self.propagator.get_graph_args()

        if self.debug:
            # Debug mode with tracing
            trace = []
            for chunk in self.graph.stream(init_agent_state, **args):
                if len(chunk["messages"]) == 0:
                    pass
                else:
                    chunk["messages"][-1].pretty_print()
                    trace.append(chunk)

            final_state = trace[-1]
        else:
            # Standard mode without tracing
            final_state = self.graph.invoke(init_agent_state, **args)

        # Store current state for reflection
        self.curr_state = final_state

        # Log state
        self._log_state(trade_date, final_state)

        # Return decision, processed signal, and metadata
        signal_result = self.process_signal_full(final_state["final_trade_decision"])
        decision = signal_result["decision"]

        # Apply quantitative guardrails (hard override for extreme cases only)
        tech_signals = extract_technical_signals(final_state.get("market_report", ""))
        tech_opinion = format_technical_opinion(tech_signals)
        decision, was_overridden, override_reason = apply_hard_override(decision, tech_signals)

        if was_overridden:
            print(f"GUARDRAIL: {override_reason}")

        if tech_opinion:
            # Store for logging/debugging
            final_state["_technical_signals"] = tech_signals
            final_state["_technical_opinion"] = tech_opinion
            final_state["_override_applied"] = was_overridden
            final_state["_override_reason"] = override_reason

        # Validate final decision is one of the expected values
        if decision not in ("BUY", "SELL", "HOLD"):
            raise ValueError(
                f"Invalid final decision '{decision}'. "
                f"Expected BUY, SELL, or HOLD."
            )

        return final_state, decision

    def _log_state(self, trade_date, final_state):
        """Log the final state to a JSON file."""
        # Extract signal metadata (decision + confidence)
        signal_meta = self.process_signal_full(final_state["final_trade_decision"])

        self.log_states_dict[str(trade_date)] = {
            "company_of_interest": final_state["company_of_interest"],
            "trade_date": final_state["trade_date"],
            "decision": signal_meta["decision"],
            "confidence": signal_meta["confidence"],
            "market_report": final_state["market_report"],
            "sentiment_report": final_state["sentiment_report"],
            "news_report": final_state["news_report"],
            "fundamentals_report": final_state["fundamentals_report"],
            "investment_debate_state": {
                "bull_history": final_state["investment_debate_state"]["bull_history"],
                "bear_history": final_state["investment_debate_state"]["bear_history"],
                "history": final_state["investment_debate_state"]["history"],
                "current_response": final_state["investment_debate_state"][
                    "current_response"
                ],
                "judge_decision": final_state["investment_debate_state"][
                    "judge_decision"
                ],
            },
            "trader_investment_decision": final_state["trader_investment_plan"],
            "risk_debate_state": {
                "risky_history": final_state["risk_debate_state"]["risky_history"],
                "safe_history": final_state["risk_debate_state"]["safe_history"],
                "neutral_history": final_state["risk_debate_state"]["neutral_history"],
                "history": final_state["risk_debate_state"]["history"],
                "judge_decision": final_state["risk_debate_state"]["judge_decision"],
            },
            "investment_plan": final_state["investment_plan"],
            "final_trade_decision": final_state["final_trade_decision"],
        }

        # Save to file
        directory = Path(f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/")
        directory.mkdir(parents=True, exist_ok=True)

        with open(
            f"eval_results/{self.ticker}/TradingAgentsStrategy_logs/full_states_log_{trade_date}.json",
            "w",
        ) as f:
            json.dump(self.log_states_dict, f, indent=4)

    def reflect_and_remember(self, returns_losses):
        """Reflect on decisions and update memory based on returns."""
        self.reflector.reflect_bull_researcher(
            self.curr_state, returns_losses, self.bull_memory
        )
        self.reflector.reflect_bear_researcher(
            self.curr_state, returns_losses, self.bear_memory
        )
        self.reflector.reflect_trader(
            self.curr_state, returns_losses, self.trader_memory
        )
        self.reflector.reflect_invest_judge(
            self.curr_state, returns_losses, self.invest_judge_memory
        )
        self.reflector.reflect_risk_manager(
            self.curr_state, returns_losses, self.risk_manager_memory
        )

    def process_signal(self, full_signal):
        """Process a signal to extract the core decision."""
        return self.signal_processor.process_signal(full_signal)

    def process_signal_full(self, full_signal):
        """Process a signal to extract decision and confidence metadata."""
        return self.signal_processor.process_signal_full(full_signal)

    def ace_learn_from_analysis(self, final_state: Dict[str, Any]) -> None:
        """
        Trigger ACE learning from the completed analysis.

        Args:
            final_state: The final state containing all reports and decisions
        """
        if not self.ace_engine:
            return

        try:
            reports = {
                "ticker": final_state.get("company_of_interest", "Unknown"),
                "date": final_state.get("trade_date", "Unknown"),
                "market": final_state.get("market_report", ""),
                "sentiment": final_state.get("sentiment_report", ""),
                "news": final_state.get("news_report", ""),
                "fundamentals": final_state.get("fundamentals_report", ""),
                "plan": final_state.get("investment_plan", ""),
            }
            decision = final_state.get("final_trade_decision", "")

            self.ace_engine.learn_from_analysis(reports, decision)
        except Exception as e:
            print(f"ACE: Learning failed - {e}")

    def get_ace_context(self) -> str:
        """
        Get the learned ACE skills for prompt injection.

        Returns:
            Formatted string of learned trading strategies, or empty string if ACE disabled
        """
        if not self.ace_engine:
            return ""
        return self.ace_engine.get_skills_context()

    def save_ace_skillbook(self, path: Optional[str] = None) -> Optional[str]:
        """
        Save the ACE skillbook to file.

        Args:
            path: Optional custom path, uses config default if not provided

        Returns:
            Path where skillbook was saved, or None if ACE disabled
        """
        if not self.ace_engine:
            return None
        return self.ace_engine.save_skillbook(path)

    def get_ace_stats(self) -> Dict[str, Any]:
        """
        Get ACE statistics.

        Returns:
            Dictionary with ACE stats, or empty dict if ACE disabled
        """
        if not self.ace_engine:
            return {"enabled": False}
        stats = self.ace_engine.get_stats()
        stats["enabled"] = True
        return stats

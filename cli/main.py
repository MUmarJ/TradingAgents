from typing import Optional
import datetime
import typer
from pathlib import Path
from functools import wraps
from rich.console import Console
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
from rich.panel import Panel
from rich.spinner import Spinner
from rich.live import Live
from rich.columns import Columns
from rich.markdown import Markdown
from rich.layout import Layout
from rich.text import Text
from rich.live import Live
from rich.table import Table
from collections import deque
import time
from rich.tree import Tree
from rich import box
from rich.align import Align
from rich.rule import Rule

from tradingagents.graph.trading_graph import TradingAgentsGraph
from tradingagents.default_config import DEFAULT_CONFIG
from tradingagents.backtest.outcome_tracker import OutcomeTracker, TradeOutcome
from cli.models import AnalystType
from cli.utils import *

console = Console()

# Recall period configuration: maps CLI option to lookback days
RECALL_PERIODS = {
    "3mo": 90,    # 3 months
    "6mo": 180,   # 6 months
    "12mo": 365,  # 12 months / 1 year
}

app = typer.Typer(
    name="TradingAgents",
    help="TradingAgents CLI: Multi-Agents LLM Financial Trading Framework",
    add_completion=True,  # Enable shell completion
    invoke_without_command=True,  # Allow running without subcommand
)


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    default_models: bool = typer.Option(
        False,
        "--default-models",
        "-d",
        help="Use optimized default models (gpt-5-mini-2025-08-07 quick, gpt-5.2-2025-09-04 deep) - skips model selection"
    ),
    use_cache: bool = typer.Option(
        False,
        "--cache",
        "-c",
        help="Resume analysis using cached reports - skips analysts that already have reports for the date"
    ),
    recall: Optional[str] = typer.Option(
        None,
        "--recall",
        "-r",
        help="News recall period: 3mo, 6mo, 12mo, or 'all' for all periods. Creates separate report folders per period."
    ),
):
    """TradingAgents CLI - Multi-Agents LLM Financial Trading Framework."""
    if ctx.invoked_subcommand is None:
        # Validate recall option if provided
        if recall is not None:
            recall_lower = recall.lower()
            if recall_lower != "all" and recall_lower not in RECALL_PERIODS:
                console.print(f"[red]Invalid recall period: {recall}. Use 3mo, 6mo, 12mo, or all[/red]")
                raise typer.Exit(1)

        # No subcommand provided, run analyze as default
        run_analysis(use_default_models=default_models, use_cache=use_cache, recall=recall)
        # Update outcomes database
        config = DEFAULT_CONFIG.copy()
        results_dir = config.get("results_dir", "./results")
        processed = update_outcomes_from_results(results_dir)
        if processed > 0:
            console.print(f"[dim]Updated outcomes database with {processed} new entries[/dim]")


# Create a deque to store recent messages with a maximum length
class MessageBuffer:
    def __init__(self, max_length=100):
        self.messages = deque(maxlen=max_length)
        self.tool_calls = deque(maxlen=max_length)
        self.current_report = None
        self.final_report = None  # Store the complete final report
        self.agent_status = {
            # Analyst Team
            "Market Analyst": "pending",
            "Social Analyst": "pending",
            "News Analyst": "pending",
            "Fundamentals Analyst": "pending",
            # Research Team
            "Bull Researcher": "pending",
            "Bear Researcher": "pending",
            "Research Manager": "pending",
            # Trading Team
            "Trader": "pending",
            # Risk Management Team
            "Risky Analyst": "pending",
            "Neutral Analyst": "pending",
            "Safe Analyst": "pending",
            # Portfolio Management Team
            "Portfolio Manager": "pending",
        }
        self.current_agent = None
        self.report_sections = {
            "market_report": None,
            "sentiment_report": None,
            "news_report": None,
            "fundamentals_report": None,
            "investment_plan": None,
            "trader_investment_plan": None,
            "final_trade_decision": None,
        }

    def add_message(self, message_type, content):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.messages.append((timestamp, message_type, content))

    def add_tool_call(self, tool_name, args):
        timestamp = datetime.datetime.now().strftime("%H:%M:%S")
        self.tool_calls.append((timestamp, tool_name, args))

    def update_agent_status(self, agent, status):
        if agent in self.agent_status:
            self.agent_status[agent] = status
            self.current_agent = agent

    def update_report_section(self, section_name, content):
        if section_name in self.report_sections:
            self.report_sections[section_name] = content
            self._update_current_report()

    def _update_current_report(self):
        # For the panel display, only show the most recently updated section
        latest_section = None
        latest_content = None

        # Find the most recently updated section
        for section, content in self.report_sections.items():
            if content is not None:
                latest_section = section
                latest_content = content
               
        if latest_section and latest_content:
            # Format the current section for display
            section_titles = {
                "market_report": "Market Analysis",
                "sentiment_report": "Social Sentiment",
                "news_report": "News Analysis",
                "fundamentals_report": "Fundamentals Analysis",
                "investment_plan": "Research Team Decision",
                "trader_investment_plan": "Trading Team Plan",
                "final_trade_decision": "Portfolio Management Decision",
            }
            self.current_report = (
                f"### {section_titles[latest_section]}\n{latest_content}"
            )

        # Update the final complete report
        self._update_final_report()

    def _update_final_report(self):
        report_parts = []

        # Analyst Team Reports
        if any(
            self.report_sections[section]
            for section in [
                "market_report",
                "sentiment_report",
                "news_report",
                "fundamentals_report",
            ]
        ):
            report_parts.append("## Analyst Team Reports")
            if self.report_sections["market_report"]:
                report_parts.append(
                    f"### Market Analysis\n{self.report_sections['market_report']}"
                )
            if self.report_sections["sentiment_report"]:
                report_parts.append(
                    f"### Social Sentiment\n{self.report_sections['sentiment_report']}"
                )
            if self.report_sections["news_report"]:
                report_parts.append(
                    f"### News Analysis\n{self.report_sections['news_report']}"
                )
            if self.report_sections["fundamentals_report"]:
                report_parts.append(
                    f"### Fundamentals Analysis\n{self.report_sections['fundamentals_report']}"
                )

        # Research Team Reports
        if self.report_sections["investment_plan"]:
            report_parts.append("## Research Team Decision")
            report_parts.append(f"{self.report_sections['investment_plan']}")

        # Trading Team Reports
        if self.report_sections["trader_investment_plan"]:
            report_parts.append("## Trading Team Plan")
            report_parts.append(f"{self.report_sections['trader_investment_plan']}")

        # Portfolio Management Decision
        if self.report_sections["final_trade_decision"]:
            report_parts.append("## Portfolio Management Decision")
            report_parts.append(f"{self.report_sections['final_trade_decision']}")

        self.final_report = "\n\n".join(report_parts) if report_parts else None


message_buffer = MessageBuffer()


def create_layout():
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main"),
        Layout(name="footer", size=3),
    )
    layout["main"].split_column(
        Layout(name="upper", ratio=3), Layout(name="analysis", ratio=5)
    )
    layout["upper"].split_row(
        Layout(name="progress", ratio=2), Layout(name="messages", ratio=3)
    )
    return layout


def update_display(layout, spinner_text=None):
    # Header with welcome message
    layout["header"].update(
        Panel(
            "[bold green]Welcome to TradingAgents CLI[/bold green]\n"
            "[dim]© [Tauric Research](https://github.com/TauricResearch)[/dim]",
            title="Welcome to TradingAgents",
            border_style="green",
            padding=(1, 2),
            expand=True,
        )
    )

    # Progress panel showing agent status
    progress_table = Table(
        show_header=True,
        header_style="bold magenta",
        show_footer=False,
        box=box.SIMPLE_HEAD,  # Use simple header with horizontal lines
        title=None,  # Remove the redundant Progress title
        padding=(0, 2),  # Add horizontal padding
        expand=True,  # Make table expand to fill available space
    )
    progress_table.add_column("Team", style="cyan", justify="center", width=20)
    progress_table.add_column("Agent", style="green", justify="center", width=20)
    progress_table.add_column("Status", style="yellow", justify="center", width=20)

    # Group agents by team
    teams = {
        "Analyst Team": [
            "Market Analyst",
            "Social Analyst",
            "News Analyst",
            "Fundamentals Analyst",
        ],
        "Research Team": ["Bull Researcher", "Bear Researcher", "Research Manager"],
        "Trading Team": ["Trader"],
        "Risk Management": ["Risky Analyst", "Neutral Analyst", "Safe Analyst"],
        "Portfolio Management": ["Portfolio Manager"],
    }

    for team, agents in teams.items():
        # Add first agent with team name
        first_agent = agents[0]
        status = message_buffer.agent_status[first_agent]
        if status == "in_progress":
            spinner = Spinner(
                "dots", text="[blue]in_progress[/blue]", style="bold cyan"
            )
            status_cell = spinner
        else:
            status_color = {
                "pending": "yellow",
                "completed": "green",
                "error": "red",
            }.get(status, "white")
            status_cell = f"[{status_color}]{status}[/{status_color}]"
        progress_table.add_row(team, first_agent, status_cell)

        # Add remaining agents in team
        for agent in agents[1:]:
            status = message_buffer.agent_status[agent]
            if status == "in_progress":
                spinner = Spinner(
                    "dots", text="[blue]in_progress[/blue]", style="bold cyan"
                )
                status_cell = spinner
            else:
                status_color = {
                    "pending": "yellow",
                    "completed": "green",
                    "error": "red",
                }.get(status, "white")
                status_cell = f"[{status_color}]{status}[/{status_color}]"
            progress_table.add_row("", agent, status_cell)

        # Add horizontal line after each team
        progress_table.add_row("─" * 20, "─" * 20, "─" * 20, style="dim")

    layout["progress"].update(
        Panel(progress_table, title="Progress", border_style="cyan", padding=(1, 2))
    )

    # Messages panel showing recent messages and tool calls
    messages_table = Table(
        show_header=True,
        header_style="bold magenta",
        show_footer=False,
        expand=True,  # Make table expand to fill available space
        box=box.MINIMAL,  # Use minimal box style for a lighter look
        show_lines=True,  # Keep horizontal lines
        padding=(0, 1),  # Add some padding between columns
    )
    messages_table.add_column("Time", style="cyan", width=8, justify="center")
    messages_table.add_column("Type", style="green", width=10, justify="center")
    messages_table.add_column(
        "Content", style="white", no_wrap=False, ratio=1
    )  # Make content column expand

    # Combine tool calls and messages
    all_messages = []

    # Add tool calls
    for timestamp, tool_name, args in message_buffer.tool_calls:
        # Truncate tool call args if too long
        if isinstance(args, str) and len(args) > 100:
            args = args[:97] + "..."
        all_messages.append((timestamp, "Tool", f"{tool_name}: {args}"))

    # Add regular messages
    for timestamp, msg_type, content in message_buffer.messages:
        # Convert content to string if it's not already
        content_str = content
        if isinstance(content, list):
            # Handle list of content blocks (Anthropic format)
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get('type') == 'text':
                        text_parts.append(item.get('text', ''))
                    elif item.get('type') == 'tool_use':
                        text_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
                else:
                    text_parts.append(str(item))
            content_str = ' '.join(text_parts)
        elif not isinstance(content_str, str):
            content_str = str(content)
            
        # Truncate message content if too long
        if len(content_str) > 200:
            content_str = content_str[:197] + "..."
        all_messages.append((timestamp, msg_type, content_str))

    # Sort by timestamp
    all_messages.sort(key=lambda x: x[0])

    # Calculate how many messages we can show based on available space
    # Start with a reasonable number and adjust based on content length
    max_messages = 12  # Increased from 8 to better fill the space

    # Get the last N messages that will fit in the panel
    recent_messages = all_messages[-max_messages:]

    # Add messages to table
    for timestamp, msg_type, content in recent_messages:
        # Format content with word wrapping
        wrapped_content = Text(content, overflow="fold")
        messages_table.add_row(timestamp, msg_type, wrapped_content)

    if spinner_text:
        messages_table.add_row("", "Spinner", spinner_text)

    # Add a footer to indicate if messages were truncated
    if len(all_messages) > max_messages:
        messages_table.footer = (
            f"[dim]Showing last {max_messages} of {len(all_messages)} messages[/dim]"
        )

    layout["messages"].update(
        Panel(
            messages_table,
            title="Messages & Tools",
            border_style="blue",
            padding=(1, 2),
        )
    )

    # Analysis panel showing current report
    if message_buffer.current_report:
        layout["analysis"].update(
            Panel(
                Markdown(message_buffer.current_report),
                title="Current Report",
                border_style="green",
                padding=(1, 2),
            )
        )
    else:
        layout["analysis"].update(
            Panel(
                "[italic]Waiting for analysis report...[/italic]",
                title="Current Report",
                border_style="green",
                padding=(1, 2),
            )
        )

    # Footer with statistics
    tool_calls_count = len(message_buffer.tool_calls)
    llm_calls_count = sum(
        1 for _, msg_type, _ in message_buffer.messages if msg_type == "Reasoning"
    )
    reports_count = sum(
        1 for content in message_buffer.report_sections.values() if content is not None
    )

    stats_table = Table(show_header=False, box=None, padding=(0, 2), expand=True)
    stats_table.add_column("Stats", justify="center")
    stats_table.add_row(
        f"Tool Calls: {tool_calls_count} | LLM Calls: {llm_calls_count} | Generated Reports: {reports_count}"
    )

    layout["footer"].update(Panel(stats_table, border_style="grey50"))


def get_user_selections(use_default_models: bool = False):
    """Get all user selections before starting the analysis display.

    Args:
        use_default_models: If True, skip model selection and use default config
                           (gpt-5-mini-2025-08-07 for quick thinking, gpt-5.2-2025-09-04 for deep thinking)
    """
    # Display ASCII art welcome message
    with open("./cli/static/welcome.txt", "r") as f:
        welcome_ascii = f.read()

    # Create welcome box content
    welcome_content = f"{welcome_ascii}\n"
    welcome_content += "[bold green]TradingAgents: Multi-Agents LLM Financial Trading Framework - CLI[/bold green]\n\n"
    welcome_content += "[bold]Workflow Steps:[/bold]\n"
    welcome_content += "I. Analyst Team → II. Research Team → III. Trader → IV. Risk Management → V. Portfolio Management\n\n"
    welcome_content += (
        "[dim]Built by [Tauric Research](https://github.com/TauricResearch)[/dim]"
    )

    # Create and center the welcome box
    welcome_box = Panel(
        welcome_content,
        border_style="green",
        padding=(1, 2),
        title="Welcome to TradingAgents",
        subtitle="Multi-Agents LLM Financial Trading Framework",
    )
    console.print(Align.center(welcome_box))
    console.print()  # Add a blank line after the welcome box

    # Create a boxed questionnaire for each step
    def create_question_box(title, prompt, default=None):
        box_content = f"[bold]{title}[/bold]\n"
        box_content += f"[dim]{prompt}[/dim]"
        if default:
            box_content += f"\n[dim]Default: {default}[/dim]"
        return Panel(box_content, border_style="blue", padding=(1, 2))

    # Step 1: Ticker symbol(s)
    console.print(
        create_question_box(
            "Step 1: Ticker Symbol(s)",
            "Enter ticker symbol(s) to analyze (comma-separated for multiple)",
            "SPY",
        )
    )
    selected_ticker = get_ticker()

    # Step 2: Analysis date
    default_date = datetime.datetime.now().strftime("%Y-%m-%d")
    console.print(
        create_question_box(
            "Step 2: Analysis Date",
            "Enter the analysis date (YYYY-MM-DD)",
            default_date,
        )
    )
    analysis_date = get_analysis_date()

    # Step 3: Select analysts
    console.print(
        create_question_box(
            "Step 3: Analysts Team", "Select your LLM analyst agents for the analysis"
        )
    )
    selected_analysts = select_analysts()
    console.print(
        f"[green]Selected analysts:[/green] {', '.join(analyst.value for analyst in selected_analysts)}"
    )

    # Step 4: Research depth
    console.print(
        create_question_box(
            "Step 4: Research Depth", "Select your research depth level"
        )
    )
    selected_research_depth = select_research_depth()

    # Step 5: OpenAI backend
    console.print(
        create_question_box(
            "Step 5: OpenAI backend", "Select which service to talk to"
        )
    )
    selected_llm_provider, backend_url = select_llm_provider()

    if use_default_models:
        # Use optimized defaults: gpt-5-mini-2025-08-07 (500K TPM) for quick, gpt-5.2-2025-09-04 (500K TPM) for deep
        selected_shallow_thinker = DEFAULT_CONFIG["quick_think_llm"]
        selected_deep_thinker = DEFAULT_CONFIG["deep_think_llm"]
        console.print(
            f"[green]Using default models:[/green] Quick={selected_shallow_thinker}, Deep={selected_deep_thinker}"
        )
    else:
        # Step 6: Quick-Thinking LLM Engine
        console.print(
            create_question_box(
                "Step 6: Quick-Thinking LLM Engine", "Select your quick-thinking model for fast operations"
            )
        )
        selected_shallow_thinker = select_shallow_thinking_agent(selected_llm_provider)

        # Step 7: Deep-Thinking LLM Engine
        console.print(
            create_question_box(
                "Step 7: Deep-Thinking LLM Engine", "Select your deep-thinking model for complex reasoning"
            )
        )
        selected_deep_thinker = select_deep_thinking_agent(selected_llm_provider)

    return {
        "ticker": selected_ticker,
        "analysis_date": analysis_date,
        "analysts": selected_analysts,
        "research_depth": selected_research_depth,
        "llm_provider": selected_llm_provider.lower(),
        "backend_url": backend_url,
        "shallow_thinker": selected_shallow_thinker,
        "deep_thinker": selected_deep_thinker,
    }


def get_ticker():
    """Get ticker symbol(s) from user input. Supports comma-separated symbols."""
    raw_input = typer.prompt("", default="SPY")
    # Split by comma, strip whitespace, convert to uppercase
    symbols = [s.strip().upper() for s in raw_input.split(",") if s.strip()]
    return symbols if len(symbols) > 1 else symbols[0]


def get_analysis_date():
    """Get the analysis date from user input."""
    while True:
        date_str = typer.prompt(
            "", default=datetime.datetime.now().strftime("%Y-%m-%d")
        )
        try:
            # Validate date format and ensure it's not in the future
            analysis_date = datetime.datetime.strptime(date_str, "%Y-%m-%d")
            if analysis_date.date() > datetime.datetime.now().date():
                console.print("[red]Error: Analysis date cannot be in the future[/red]")
                continue
            return date_str
        except ValueError:
            console.print(
                "[red]Error: Invalid date format. Please use YYYY-MM-DD[/red]"
            )


def display_complete_report(final_state):
    """Display the complete analysis report with team-based panels."""
    console.print("\n[bold green]Complete Analysis Report[/bold green]\n")

    # I. Analyst Team Reports
    analyst_reports = []

    # Market Analyst Report
    if final_state.get("market_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["market_report"]),
                title="Market Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # Social Analyst Report
    if final_state.get("sentiment_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["sentiment_report"]),
                title="Social Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # News Analyst Report
    if final_state.get("news_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["news_report"]),
                title="News Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    # Fundamentals Analyst Report
    if final_state.get("fundamentals_report"):
        analyst_reports.append(
            Panel(
                Markdown(final_state["fundamentals_report"]),
                title="Fundamentals Analyst",
                border_style="blue",
                padding=(1, 2),
            )
        )

    if analyst_reports:
        console.print(
            Panel(
                Columns(analyst_reports, equal=True, expand=True),
                title="I. Analyst Team Reports",
                border_style="cyan",
                padding=(1, 2),
            )
        )

    # II. Research Team Reports
    if final_state.get("investment_debate_state"):
        research_reports = []
        debate_state = final_state["investment_debate_state"]

        # Bull Researcher Analysis
        if debate_state.get("bull_history"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["bull_history"]),
                    title="Bull Researcher",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Bear Researcher Analysis
        if debate_state.get("bear_history"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["bear_history"]),
                    title="Bear Researcher",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Research Manager Decision
        if debate_state.get("judge_decision"):
            research_reports.append(
                Panel(
                    Markdown(debate_state["judge_decision"]),
                    title="Research Manager",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        if research_reports:
            console.print(
                Panel(
                    Columns(research_reports, equal=True, expand=True),
                    title="II. Research Team Decision",
                    border_style="magenta",
                    padding=(1, 2),
                )
            )

    # III. Trading Team Reports
    if final_state.get("trader_investment_plan"):
        console.print(
            Panel(
                Panel(
                    Markdown(final_state["trader_investment_plan"]),
                    title="Trader",
                    border_style="blue",
                    padding=(1, 2),
                ),
                title="III. Trading Team Plan",
                border_style="yellow",
                padding=(1, 2),
            )
        )

    # IV. Risk Management Team Reports
    if final_state.get("risk_debate_state"):
        risk_reports = []
        risk_state = final_state["risk_debate_state"]

        # Aggressive (Risky) Analyst Analysis
        if risk_state.get("risky_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["risky_history"]),
                    title="Aggressive Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Conservative (Safe) Analyst Analysis
        if risk_state.get("safe_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["safe_history"]),
                    title="Conservative Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        # Neutral Analyst Analysis
        if risk_state.get("neutral_history"):
            risk_reports.append(
                Panel(
                    Markdown(risk_state["neutral_history"]),
                    title="Neutral Analyst",
                    border_style="blue",
                    padding=(1, 2),
                )
            )

        if risk_reports:
            console.print(
                Panel(
                    Columns(risk_reports, equal=True, expand=True),
                    title="IV. Risk Management Team Decision",
                    border_style="red",
                    padding=(1, 2),
                )
            )

        # V. Portfolio Manager Decision
        if risk_state.get("judge_decision"):
            console.print(
                Panel(
                    Panel(
                        Markdown(risk_state["judge_decision"]),
                        title="Portfolio Manager",
                        border_style="blue",
                        padding=(1, 2),
                    ),
                    title="V. Portfolio Manager Decision",
                    border_style="green",
                    padding=(1, 2),
                )
            )


def update_research_team_status(status):
    """Update status for all research team members and trader."""
    research_team = ["Bull Researcher", "Bear Researcher", "Research Manager", "Trader"]
    for agent in research_team:
        message_buffer.update_agent_status(agent, status)

def extract_content_string(content):
    """Extract string content from various message formats."""
    if isinstance(content, str):
        return content
    elif isinstance(content, list):
        # Handle Anthropic's list format
        text_parts = []
        for item in content:
            if isinstance(item, dict):
                if item.get('type') == 'text':
                    text_parts.append(item.get('text', ''))
                elif item.get('type') == 'tool_use':
                    text_parts.append(f"[Tool: {item.get('name', 'unknown')}]")
            else:
                text_parts.append(str(item))
        return ' '.join(text_parts)
    else:
        return str(content)

def load_cached_reports(results_dir: Path, ticker: str, analysis_date: str) -> dict:
    """Load previously generated reports from cache.

    Args:
        results_dir: Base results directory
        ticker: Stock ticker symbol
        analysis_date: Date of analysis in YYYY-MM-DD format

    Returns:
        Dictionary mapping report names to their content, e.g.:
        {"market_report": "...", "sentiment_report": "...", ...}
    """
    report_dir = results_dir / ticker / analysis_date / "reports"
    cached = {}

    report_files = {
        "market_report": "market_report.md",
        "sentiment_report": "sentiment_report.md",
        "news_report": "news_report.md",
        "fundamentals_report": "fundamentals_report.md",
    }

    for report_key, filename in report_files.items():
        report_path = report_dir / filename
        if report_path.exists():
            try:
                content = report_path.read_text()
                if content.strip():  # Only cache non-empty reports
                    cached[report_key] = content
            except Exception:
                pass

    return cached


def run_analysis(use_default_models: bool = False, use_cache: bool = False, recall: str = None):
    """Run analysis for one or more ticker symbols.

    Args:
        use_default_models: If True, skip model selection and use optimized defaults
                           (gpt-5-mini-2025-08-07 for quick thinking, gpt-5.2-2025-09-04 for deep thinking)
        use_cache: If True, skip analysts that already have cached reports for the date
        recall: News recall period ('3mo', '6mo', '12mo', or 'all')
    """
    # First get all user selections
    selections = get_user_selections(use_default_models=use_default_models)

    # Create config with selected research depth
    config = DEFAULT_CONFIG.copy()
    config["max_debate_rounds"] = selections["research_depth"]
    config["max_risk_discuss_rounds"] = selections["research_depth"]
    config["quick_think_llm"] = selections["shallow_thinker"]
    config["deep_think_llm"] = selections["deep_thinker"]
    config["backend_url"] = selections["backend_url"]
    config["llm_provider"] = selections["llm_provider"].lower()

    # Normalize ticker(s) to list
    tickers = selections["ticker"] if isinstance(selections["ticker"], list) else [selections["ticker"]]

    # Get news limits from config
    news_limits = config.get("news_limits", {
        "default": 50,
        "3mo": 200,
        "6mo": 500,
        "12mo": 1000,
    })

    # Determine recall periods to run (suffix, lookback_days, article_limit)
    if recall is None:
        # Default: 7-day lookback, no recall suffix in folder
        recall_periods = [(None, 7, news_limits.get("default", 50))]
    elif recall.lower() == "all":
        # Run all three recall periods
        recall_periods = [
            ("Recall_3mo", RECALL_PERIODS["3mo"], news_limits.get("3mo", 200)),
            ("Recall_6mo", RECALL_PERIODS["6mo"], news_limits.get("6mo", 500)),
            ("Recall_12mo", RECALL_PERIODS["12mo"], news_limits.get("12mo", 1000)),
        ]
        console.print(f"[bold cyan]Running analysis with all recall periods: 3mo, 6mo, 12mo[/bold cyan]")
    else:
        # Run single recall period
        recall_lower = recall.lower()
        article_limit = news_limits.get(recall_lower, 200)
        recall_periods = [(f"Recall_{recall_lower}", RECALL_PERIODS[recall_lower], article_limit)]
        console.print(f"[bold cyan]Running analysis with {recall_lower} recall period ({RECALL_PERIODS[recall_lower]} days, {article_limit} articles)[/bold cyan]")

    for i, ticker in enumerate(tickers, 1):
        if len(tickers) > 1:
            console.print(f"\n[bold cyan]{'═' * 50}[/bold cyan]")
            console.print(f"[bold cyan]  Analyzing {ticker} ({i}/{len(tickers)})[/bold cyan]")
            console.print(f"[bold cyan]{'═' * 50}[/bold cyan]\n")

        # Create a fresh graph for each ticker to ensure complete state isolation
        graph = TradingAgentsGraph(
            [analyst.value for analyst in selections["analysts"]], config=config, debug=True
        )

        # Run analysis for each recall period
        for recall_suffix, lookback_days, article_limit in recall_periods:
            if len(recall_periods) > 1:
                console.print(f"\n[bold magenta]  Recall period: {recall_suffix} ({lookback_days} days, {article_limit} articles)[/bold magenta]")

            run_single_analysis(
                ticker, selections, config, graph,
                use_cache=use_cache,
                recall_suffix=recall_suffix,
                news_lookback_days=lookback_days,
                news_article_limit=article_limit
            )

        if i < len(tickers):
            console.print(f"\n[dim]Moving to next symbol...[/dim]\n")

    if len(tickers) > 1:
        console.print(f"\n[bold green]Completed analysis for all {len(tickers)} symbols: {', '.join(tickers)}[/bold green]")


def run_single_analysis(
    ticker: str,
    selections: dict,
    config: dict,
    graph: TradingAgentsGraph,
    use_cache: bool = False,
    recall_suffix: str = None,
    news_lookback_days: int = 7,
    news_article_limit: int = 50
):
    """Run analysis for a single ticker symbol.

    Args:
        ticker: Stock ticker symbol
        selections: User selections dict
        config: Configuration dict
        graph: TradingAgentsGraph instance
        use_cache: If True, skip analysts that already have cached reports
        recall_suffix: Optional folder suffix for recall period (e.g., "Recall_3mo")
        news_lookback_days: Number of days to look back for news analysis (default 7)
        news_article_limit: Maximum number of news articles to fetch (default 50)
    """
    # Create result directory with optional recall suffix
    results_dir_base = Path(config["results_dir"])
    if recall_suffix:
        results_dir = results_dir_base / ticker / selections["analysis_date"] / recall_suffix
    else:
        results_dir = results_dir_base / ticker / selections["analysis_date"]
    results_dir.mkdir(parents=True, exist_ok=True)
    report_dir = results_dir / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    log_file = results_dir / "message_tool.log"
    log_file.touch(exist_ok=True)

    # Check for cached reports if cache mode is enabled
    cached_reports = {}
    if use_cache:
        # For recall periods, construct the full path including recall suffix
        if recall_suffix:
            cache_date_path = f"{selections['analysis_date']}/{recall_suffix}"
        else:
            cache_date_path = selections["analysis_date"]
        cached_reports = load_cached_reports(results_dir_base, ticker, cache_date_path)
        if cached_reports:
            cached_list = list(cached_reports.keys())
            console.print(f"[yellow]Cache mode enabled. Found {len(cached_reports)} cached reports: {', '.join(cached_list)}[/yellow]")

    def save_message_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, message_type, content = obj.messages[-1]
            content = content.replace("\n", " ")  # Replace newlines with spaces
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [{message_type}] {content}\n")
        return wrapper
    
    def save_tool_call_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(*args, **kwargs):
            func(*args, **kwargs)
            timestamp, tool_name, args = obj.tool_calls[-1]
            args_str = ", ".join(f"{k}={v}" for k, v in args.items())
            with open(log_file, "a") as f:
                f.write(f"{timestamp} [Tool Call] {tool_name}({args_str})\n")
        return wrapper

    def save_report_section_decorator(obj, func_name):
        func = getattr(obj, func_name)
        @wraps(func)
        def wrapper(section_name, content):
            func(section_name, content)
            if section_name in obj.report_sections and obj.report_sections[section_name] is not None:
                content = obj.report_sections[section_name]
                if content:
                    file_name = f"{section_name}.md"
                    with open(report_dir / file_name, "w") as f:
                        f.write(content)
        return wrapper

    message_buffer.add_message = save_message_decorator(message_buffer, "add_message")
    message_buffer.add_tool_call = save_tool_call_decorator(message_buffer, "add_tool_call")
    message_buffer.update_report_section = save_report_section_decorator(message_buffer, "update_report_section")

    # Now start the display layout
    layout = create_layout()

    with Live(layout, refresh_per_second=4) as live:
        # Initial display
        update_display(layout)

        # Add initial messages
        message_buffer.add_message("System", f"Selected ticker: {ticker}")
        message_buffer.add_message(
            "System", f"Analysis date: {selections['analysis_date']}"
        )
        message_buffer.add_message(
            "System",
            f"Selected analysts: {', '.join(analyst.value for analyst in selections['analysts'])}",
        )
        update_display(layout)

        # Reset agent statuses
        for agent in message_buffer.agent_status:
            message_buffer.update_agent_status(agent, "pending")

        # Reset report sections
        for section in message_buffer.report_sections:
            message_buffer.report_sections[section] = None
        message_buffer.current_report = None
        message_buffer.final_report = None

        # Update agent status to in_progress for the first analyst
        first_analyst = f"{selections['analysts'][0].value.capitalize()} Analyst"
        message_buffer.update_agent_status(first_analyst, "in_progress")
        update_display(layout)

        # Create spinner text
        spinner_text = (
            f"Analyzing {ticker} on {selections['analysis_date']}..."
        )
        update_display(layout, spinner_text)

        # Initialize state and get graph args
        init_agent_state = graph.propagator.create_initial_state(
            ticker, selections["analysis_date"],
            news_lookback_days=news_lookback_days,
            news_article_limit=news_article_limit
        )

        # Inject cached reports if cache mode is enabled
        if cached_reports:
            for report_key, content in cached_reports.items():
                if report_key in init_agent_state and content:
                    init_agent_state[report_key] = content
                    message_buffer.add_message("Cache", f"Loaded {report_key} from cache ({len(content)} chars)")

        args = graph.propagator.get_graph_args()

        # Stream the analysis
        trace = []
        for chunk in graph.graph.stream(init_agent_state, **args):
            if len(chunk["messages"]) > 0:
                # Get the last message from the chunk
                last_message = chunk["messages"][-1]

                # Extract message content and type
                if hasattr(last_message, "content"):
                    content = extract_content_string(last_message.content)  # Use the helper function
                    msg_type = "Reasoning"
                else:
                    content = str(last_message)
                    msg_type = "System"

                # Add message to buffer
                message_buffer.add_message(msg_type, content)                

                # If it's a tool call, add it to tool calls
                if hasattr(last_message, "tool_calls"):
                    for tool_call in last_message.tool_calls:
                        # Handle both dictionary and object tool calls
                        if isinstance(tool_call, dict):
                            message_buffer.add_tool_call(
                                tool_call["name"], tool_call["args"]
                            )
                        else:
                            message_buffer.add_tool_call(tool_call.name, tool_call.args)

                # Update reports and agent status based on chunk content
                # Analyst Team Reports
                if "market_report" in chunk and chunk["market_report"]:
                    message_buffer.update_report_section(
                        "market_report", chunk["market_report"]
                    )
                    message_buffer.update_agent_status("Market Analyst", "completed")
                    # Set next analyst to in_progress
                    if "social" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "Social Analyst", "in_progress"
                        )

                if "sentiment_report" in chunk and chunk["sentiment_report"]:
                    message_buffer.update_report_section(
                        "sentiment_report", chunk["sentiment_report"]
                    )
                    message_buffer.update_agent_status("Social Analyst", "completed")
                    # Set next analyst to in_progress
                    if "news" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "News Analyst", "in_progress"
                        )

                if "news_report" in chunk and chunk["news_report"]:
                    message_buffer.update_report_section(
                        "news_report", chunk["news_report"]
                    )
                    message_buffer.update_agent_status("News Analyst", "completed")
                    # Set next analyst to in_progress
                    if "fundamentals" in selections["analysts"]:
                        message_buffer.update_agent_status(
                            "Fundamentals Analyst", "in_progress"
                        )

                if "fundamentals_report" in chunk and chunk["fundamentals_report"]:
                    message_buffer.update_report_section(
                        "fundamentals_report", chunk["fundamentals_report"]
                    )
                    message_buffer.update_agent_status(
                        "Fundamentals Analyst", "completed"
                    )
                    # Set all research team members to in_progress
                    update_research_team_status("in_progress")

                # Research Team - Handle Investment Debate State
                if (
                    "investment_debate_state" in chunk
                    and chunk["investment_debate_state"]
                ):
                    debate_state = chunk["investment_debate_state"]

                    # Update Bull Researcher status and report
                    if "bull_history" in debate_state and debate_state["bull_history"]:
                        # Keep all research team members in progress
                        update_research_team_status("in_progress")
                        # Extract latest bull response
                        bull_responses = debate_state["bull_history"].split("\n")
                        latest_bull = bull_responses[-1] if bull_responses else ""
                        if latest_bull:
                            message_buffer.add_message("Reasoning", latest_bull)
                            # Update research report with bull's latest analysis
                            message_buffer.update_report_section(
                                "investment_plan",
                                f"### Bull Researcher Analysis\n{latest_bull}",
                            )

                    # Update Bear Researcher status and report
                    if "bear_history" in debate_state and debate_state["bear_history"]:
                        # Keep all research team members in progress
                        update_research_team_status("in_progress")
                        # Extract latest bear response
                        bear_responses = debate_state["bear_history"].split("\n")
                        latest_bear = bear_responses[-1] if bear_responses else ""
                        if latest_bear:
                            message_buffer.add_message("Reasoning", latest_bear)
                            # Update research report with bear's latest analysis
                            message_buffer.update_report_section(
                                "investment_plan",
                                f"{message_buffer.report_sections['investment_plan']}\n\n### Bear Researcher Analysis\n{latest_bear}",
                            )

                    # Update Research Manager status and final decision
                    if (
                        "judge_decision" in debate_state
                        and debate_state["judge_decision"]
                    ):
                        # Keep all research team members in progress until final decision
                        update_research_team_status("in_progress")
                        message_buffer.add_message(
                            "Reasoning",
                            f"Research Manager: {debate_state['judge_decision']}",
                        )
                        # Update research report with final decision
                        message_buffer.update_report_section(
                            "investment_plan",
                            f"{message_buffer.report_sections['investment_plan']}\n\n### Research Manager Decision\n{debate_state['judge_decision']}",
                        )
                        # Mark all research team members as completed
                        update_research_team_status("completed")
                        # Set first risk analyst to in_progress
                        message_buffer.update_agent_status(
                            "Risky Analyst", "in_progress"
                        )

                # Trading Team
                if (
                    "trader_investment_plan" in chunk
                    and chunk["trader_investment_plan"]
                ):
                    message_buffer.update_report_section(
                        "trader_investment_plan", chunk["trader_investment_plan"]
                    )
                    # Set first risk analyst to in_progress
                    message_buffer.update_agent_status("Risky Analyst", "in_progress")

                # Risk Management Team - Handle Risk Debate State
                if "risk_debate_state" in chunk and chunk["risk_debate_state"]:
                    risk_state = chunk["risk_debate_state"]

                    # Update Risky Analyst status and report
                    if (
                        "current_risky_response" in risk_state
                        and risk_state["current_risky_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Risky Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Risky Analyst: {risk_state['current_risky_response']}",
                        )
                        # Update risk report with risky analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Risky Analyst Analysis\n{risk_state['current_risky_response']}",
                        )

                    # Update Safe Analyst status and report
                    if (
                        "current_safe_response" in risk_state
                        and risk_state["current_safe_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Safe Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Safe Analyst: {risk_state['current_safe_response']}",
                        )
                        # Update risk report with safe analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Safe Analyst Analysis\n{risk_state['current_safe_response']}",
                        )

                    # Update Neutral Analyst status and report
                    if (
                        "current_neutral_response" in risk_state
                        and risk_state["current_neutral_response"]
                    ):
                        message_buffer.update_agent_status(
                            "Neutral Analyst", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Neutral Analyst: {risk_state['current_neutral_response']}",
                        )
                        # Update risk report with neutral analyst's latest analysis only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Neutral Analyst Analysis\n{risk_state['current_neutral_response']}",
                        )

                    # Update Portfolio Manager status and final decision
                    if "judge_decision" in risk_state and risk_state["judge_decision"]:
                        message_buffer.update_agent_status(
                            "Portfolio Manager", "in_progress"
                        )
                        message_buffer.add_message(
                            "Reasoning",
                            f"Portfolio Manager: {risk_state['judge_decision']}",
                        )
                        # Update risk report with final decision only
                        message_buffer.update_report_section(
                            "final_trade_decision",
                            f"### Portfolio Manager Decision\n{risk_state['judge_decision']}",
                        )
                        # Mark risk analysts as completed
                        message_buffer.update_agent_status("Risky Analyst", "completed")
                        message_buffer.update_agent_status("Safe Analyst", "completed")
                        message_buffer.update_agent_status(
                            "Neutral Analyst", "completed"
                        )
                        message_buffer.update_agent_status(
                            "Portfolio Manager", "completed"
                        )

                # Update the display
                update_display(layout)

            trace.append(chunk)

        # Get final state and decision
        final_state = trace[-1]
        decision = graph.process_signal(final_state["final_trade_decision"])

        # Trigger ACE learning if enabled
        if graph.ace_engine:
            message_buffer.add_message("ACE", f"Learning from analysis for {ticker}...")
            update_display(layout)
            try:
                graph.ace_learn_from_analysis(final_state)
                graph.save_ace_skillbook()
                ace_stats = graph.get_ace_stats()
                message_buffer.add_message(
                    "ACE", f"Skillbook updated ({ace_stats.get('skills_count', 0)} skills)"
                )
            except Exception as e:
                message_buffer.add_message("ACE", f"Learning failed: {e}")
            update_display(layout)

        # Update all agent statuses to completed
        for agent in message_buffer.agent_status:
            message_buffer.update_agent_status(agent, "completed")

        message_buffer.add_message(
            "Analysis", f"Completed analysis for {selections['analysis_date']}"
        )

        # Update final report sections
        for section in message_buffer.report_sections.keys():
            if section in final_state:
                message_buffer.update_report_section(section, final_state[section])

        # Display the complete final report
        display_complete_report(final_state)

        update_display(layout)


def update_outcomes_from_results(results_dir: str = "./results") -> int:
    """
    Process historical results and update the outcomes database.

    Scans ./results/{TICKER}/{DATE}/ directories for analysis reports
    and logs them to the outcome tracker for future analysis.
    Automatically validates new outcomes against market prices.

    Returns:
        Number of outcomes processed
    """
    from tradingagents.backtest.outcome_tracker import validate_outcome_against_market

    results_path = Path(results_dir)
    if not results_path.exists():
        return 0

    tracker = OutcomeTracker(output_dir=str(results_path / "outcomes"))
    processed = 0

    # Look for ticker directories
    for ticker_dir in sorted(results_path.iterdir()):
        if not ticker_dir.is_dir():
            continue

        # Skip non-ticker directories
        dir_name = ticker_dir.name
        if dir_name in ["outcomes", ".DS_Store"] or dir_name.startswith("."):
            continue

        ticker = dir_name

        # Look for date directories under ticker
        for date_dir in sorted(ticker_dir.iterdir()):
            if not date_dir.is_dir():
                continue

            date_name = date_dir.name
            # Skip if not a date-like name (YYYY-MM-DD)
            if not (len(date_name) >= 8 and "-" in date_name):
                continue

            # Check if already processed (look for marker or existing outcome)
            existing_outcomes = [
                o for o in tracker.outcomes
                if o.ticker == ticker and o.trade_date == date_name
            ]
            if existing_outcomes:
                continue

            # Try to read reports from this date directory
            reports_dir = date_dir / "reports"
            reports_summary = {}

            if reports_dir.exists():
                for report_type in ["market", "sentiment", "news", "fundamentals"]:
                    report_file = reports_dir / f"{report_type}_report.md"
                    if report_file.exists():
                        try:
                            content = report_file.read_text()
                            # Truncate to reasonable summary length
                            reports_summary[report_type] = (
                                content[:200] + "..." if len(content) > 200 else content
                            )
                        except Exception:
                            pass

            # Try to extract decision and confidence from final_trade_decision report
            from tradingagents.graph.signal_processing import (
                extract_decision_from_text,
                extract_confidence_from_text,
            )
            decision = "UNKNOWN"
            confidence = None
            final_decision_file = reports_dir / "final_trade_decision.md"
            if final_decision_file.exists():
                try:
                    content = final_decision_file.read_text()
                    decision = extract_decision_from_text(content)
                    confidence = extract_confidence_from_text(content)
                except ValueError as e:
                    print(f"  Warning: Could not extract decision from {final_decision_file.name}: {e}")
                except Exception as e:
                    print(f"  Warning: Error reading {final_decision_file.name}: {e}")

            # Create outcome record if we have any data
            if reports_summary or decision != "UNKNOWN":
                outcome = TradeOutcome(
                    ticker=ticker,
                    trade_date=date_name,
                    decision=decision,
                    confidence=confidence,
                    reports_summary=reports_summary,
                    entry_price=0.0,
                    exit_price=0.0,
                    pnl=0.0,
                    return_pct=0.0,
                    holding_period_days=0,
                    market_regime="unknown",
                    strategy_name="TradingAgents",
                )
                # Validate against market prices immediately
                outcome = validate_outcome_against_market(outcome)
                tracker.outcomes.append(outcome)
                processed += 1

    # Save if we processed anything
    if processed > 0:
        tracker.save()

    return processed




@app.command()
def outcomes(
    summary: bool = typer.Option(True, "--summary", "-s", help="Show summary statistics"),
    ticker: Optional[str] = typer.Option(None, "--ticker", "-t", help="Filter by ticker"),
    process_historical: bool = typer.Option(
        False, "--process-historical", "-p",
        help="Process all historical results"
    ),
    validate: bool = typer.Option(
        False, "--validate", "-v",
        help="Validate outcomes against actual market prices"
    ),
):
    """Analyze trade outcomes from historical results."""
    from cli.analyze_outcomes import (
        load_all_outcomes,
        process_historical_results,
        print_summary,
        print_ticker_analysis,
    )
    from tradingagents.backtest.outcome_tracker import validate_all_outcomes

    config = DEFAULT_CONFIG.copy()
    results_dir = config.get("results_dir", "./results")
    outcomes_dir = f"{results_dir}/outcomes"

    if process_historical:
        outcomes_list = process_historical_results(results_dir)
        if outcomes_list:
            tracker = OutcomeTracker(output_dir=outcomes_dir)
            tracker.outcomes = outcomes_list
            tracker.save()
            console.print(f"[green]Saved {len(outcomes_list)} outcomes[/green]")
    else:
        outcomes_list = load_all_outcomes(outcomes_dir)

    if not outcomes_list:
        console.print("[yellow]No outcomes found. Run analyses or use --process-historical[/yellow]")
        return

    # Validate against market if requested
    if validate:
        console.print("[cyan]Validating outcomes against market prices...[/cyan]")
        unvalidated = [o for o in outcomes_list if not o.validated]
        if unvalidated:
            outcomes_list = validate_all_outcomes(outcomes_list)
            console.print(f"[green]Validated {len(unvalidated)} outcomes[/green]")

            # Save validated outcomes
            tracker = OutcomeTracker(output_dir=outcomes_dir)
            tracker.outcomes = outcomes_list
            tracker.save()
        else:
            console.print("[dim]All outcomes already validated[/dim]")

    if ticker:
        print_ticker_analysis(outcomes_list, ticker)
    elif summary:
        print_summary(outcomes_list)


if __name__ == "__main__":
    app()

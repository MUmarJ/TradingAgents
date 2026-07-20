"""
Outcome tracking for trade analysis.

This module provides outcome logging without automatic prompt injection,
following research findings that memory-based learning approaches don't
produce statistically significant alpha in long-term evaluations.

The goal is to build an observable dataset for:
1. Human pattern discovery
2. Future RL training data
3. Strategy performance analysis by market regime
"""

import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional

import yfinance as yf

logger = logging.getLogger(__name__)


@dataclass
class TradeOutcome:
    """
    Comprehensive record of a trade outcome.

    Captures the decision context and actual market result
    for later analysis without injecting into future prompts.
    """

    # Trade identification
    ticker: str
    trade_date: str  # Date the decision was made

    # Decision details
    decision: str  # BUY, SELL, HOLD
    confidence: Optional[float] = None  # If provided by strategy

    # Report summaries (key signals that led to decision)
    reports_summary: Dict[str, str] = field(default_factory=dict)

    # Execution details
    entry_price: float = 0.0
    exit_price: float = 0.0
    quantity: float = 0.0
    commission: float = 0.0

    # Outcome metrics
    pnl: float = 0.0
    return_pct: float = 0.0
    holding_period_days: int = 0

    # Market context
    market_regime: str = "unknown"  # bull, bear, sideways
    volatility_regime: str = "unknown"  # low, medium, high

    # Timestamps
    entry_timestamp: Optional[str] = None
    exit_timestamp: Optional[str] = None

    # Metadata
    strategy_name: str = "TradingAgents"

    # Cost tracking (LLM usage per analysis)
    llm_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    estimated_cost_usd: float = 0.0

    # Market validation fields (next-day price movement)
    decision_date_close: float = 0.0  # Close price on decision date
    next_day_open: float = 0.0  # Open price next trading day
    next_day_close: float = 0.0  # Close price next trading day
    next_day_change_pct: float = 0.0  # % change from decision close to next close
    decision_correct: Optional[bool] = None  # Was the decision profitable?
    validated: bool = False  # Has this outcome been validated against market?

    # 5-day forward validation (secondary metric)
    day5_change_pct: Optional[float] = None  # % change over 5 trading days
    day5_correct: Optional[bool] = None  # Was decision correct over 5-day horizon?

    # Multi-horizon validation (1w, 2w, 4w, 8w, 13w forward)
    horizon_outcomes: Optional[Dict[str, Dict[str, Any]]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TradeOutcome":
        """Create from dictionary."""
        # Handle legacy data without new fields
        valid_fields = {f.name for f in cls.__dataclass_fields__.values()}
        filtered_data = {k: v for k, v in data.items() if k in valid_fields}
        return cls(**filtered_data)


@dataclass
class OutcomeStats:
    """Aggregate statistics from outcome tracking."""

    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0

    total_pnl: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    win_rate: float = 0.0

    # By regime
    bull_trades: int = 0
    bull_win_rate: float = 0.0
    bear_trades: int = 0
    bear_win_rate: float = 0.0
    sideways_trades: int = 0
    sideways_win_rate: float = 0.0

    # By decision type
    buy_trades: int = 0
    buy_win_rate: float = 0.0
    sell_trades: int = 0
    sell_win_rate: float = 0.0


class OutcomeTracker:
    """
    Tracks trade outcomes for analysis without prompt injection.

    Builds a dataset that can be used for:
    - Human pattern discovery
    - Future RL training
    - Strategy debugging
    - Performance attribution
    """

    def __init__(
        self,
        output_dir: str = "./results/outcomes",
        auto_save: bool = True,
    ):
        """
        Initialize outcome tracker.

        Args:
            output_dir: Directory to save outcome logs
            auto_save: Whether to save after each trade
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.auto_save = auto_save

        self.outcomes: List[TradeOutcome] = []
        self._session_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        logger.info(f"OutcomeTracker initialized (session: {self._session_id})")

    def record(
        self,
        ticker: str,
        decision: str,
        entry_price: float,
        exit_price: float,
        quantity: float,
        pnl: float,
        entry_timestamp: datetime,
        exit_timestamp: datetime,
        commission: float = 0.0,
        reports_summary: Optional[Dict[str, str]] = None,
        confidence: Optional[float] = None,
        market_regime: str = "unknown",
        volatility_regime: str = "unknown",
        strategy_name: str = "TradingAgents",
    ) -> TradeOutcome:
        """
        Record a completed trade outcome.

        Args:
            ticker: Stock symbol
            decision: Original decision (BUY/SELL)
            entry_price: Entry price
            exit_price: Exit price
            quantity: Number of shares
            pnl: Profit/loss in dollars
            entry_timestamp: When position was opened
            exit_timestamp: When position was closed
            commission: Trading commission
            reports_summary: Key signals from analysis reports
            confidence: Decision confidence if available
            market_regime: bull/bear/sideways
            volatility_regime: low/medium/high
            strategy_name: Name of strategy

        Returns:
            TradeOutcome record
        """
        # Calculate derived metrics
        holding_period = (exit_timestamp - entry_timestamp).days
        return_pct = ((exit_price - entry_price) / entry_price) * 100 if entry_price > 0 else 0.0

        outcome = TradeOutcome(
            ticker=ticker,
            trade_date=entry_timestamp.strftime("%Y-%m-%d"),
            decision=decision.upper(),
            confidence=confidence,
            reports_summary=reports_summary or {},
            entry_price=float(entry_price),
            exit_price=float(exit_price),
            quantity=float(quantity),
            commission=float(commission),
            pnl=float(pnl),
            return_pct=return_pct,
            holding_period_days=holding_period,
            market_regime=market_regime,
            volatility_regime=volatility_regime,
            entry_timestamp=entry_timestamp.isoformat(),
            exit_timestamp=exit_timestamp.isoformat(),
            strategy_name=strategy_name,
        )

        self.outcomes.append(outcome)

        logger.info(
            f"Outcome recorded: {ticker} {decision} "
            f"PnL=${pnl:.2f} ({return_pct:+.2f}%)"
        )

        if self.auto_save:
            self.save()

        return outcome

    def get_stats(self) -> OutcomeStats:
        """
        Calculate aggregate statistics from recorded outcomes.

        Returns:
            OutcomeStats with win rates, averages, etc.
        """
        if not self.outcomes:
            return OutcomeStats()

        stats = OutcomeStats()
        stats.total_trades = len(self.outcomes)

        wins = [o for o in self.outcomes if o.pnl > 0]
        losses = [o for o in self.outcomes if o.pnl <= 0]

        stats.winning_trades = len(wins)
        stats.losing_trades = len(losses)
        stats.total_pnl = sum(o.pnl for o in self.outcomes)

        if wins:
            stats.avg_win = sum(o.pnl for o in wins) / len(wins)
        if losses:
            stats.avg_loss = sum(o.pnl for o in losses) / len(losses)
        if stats.total_trades > 0:
            stats.win_rate = stats.winning_trades / stats.total_trades

        # By regime
        for regime in ["bull", "bear", "sideways"]:
            regime_trades = [o for o in self.outcomes if o.market_regime == regime]
            regime_wins = [o for o in regime_trades if o.pnl > 0]

            if regime == "bull":
                stats.bull_trades = len(regime_trades)
                stats.bull_win_rate = len(regime_wins) / len(regime_trades) if regime_trades else 0.0
            elif regime == "bear":
                stats.bear_trades = len(regime_trades)
                stats.bear_win_rate = len(regime_wins) / len(regime_trades) if regime_trades else 0.0
            else:
                stats.sideways_trades = len(regime_trades)
                stats.sideways_win_rate = len(regime_wins) / len(regime_trades) if regime_trades else 0.0

        # By decision type
        buy_trades = [o for o in self.outcomes if o.decision == "BUY"]
        buy_wins = [o for o in buy_trades if o.pnl > 0]
        stats.buy_trades = len(buy_trades)
        stats.buy_win_rate = len(buy_wins) / len(buy_trades) if buy_trades else 0.0

        sell_trades = [o for o in self.outcomes if o.decision == "SELL"]
        sell_wins = [o for o in sell_trades if o.pnl > 0]
        stats.sell_trades = len(sell_trades)
        stats.sell_win_rate = len(sell_wins) / len(sell_trades) if sell_trades else 0.0

        return stats

    def save(self, path: Optional[str] = None) -> str:
        """
        Save outcomes to JSON file.

        Args:
            path: Custom path, uses default if not provided

        Returns:
            Path where outcomes were saved
        """
        if path is None:
            path = self.output_dir / f"outcomes_{self._session_id}.json"
        else:
            path = Path(path)

        data = {
            "session_id": self._session_id,
            "generated_at": datetime.now().isoformat(),
            "total_outcomes": len(self.outcomes),
            "stats": asdict(self.get_stats()),
            "outcomes": [o.to_dict() for o in self.outcomes],
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Outcomes saved to {path}")
        return str(path)

    def load(self, path: str) -> None:
        """
        Load outcomes from JSON file.

        Args:
            path: Path to outcomes file
        """
        with open(path) as f:
            data = json.load(f)

        self.outcomes = [
            TradeOutcome.from_dict(o) for o in data.get("outcomes", [])
        ]
        self._session_id = data.get("session_id", self._session_id)

        logger.info(f"Loaded {len(self.outcomes)} outcomes from {path}")

    def get_outcomes_by_ticker(self, ticker: str) -> List[TradeOutcome]:
        """Get all outcomes for a specific ticker."""
        return [o for o in self.outcomes if o.ticker == ticker]

    def get_outcomes_by_regime(self, regime: str) -> List[TradeOutcome]:
        """Get all outcomes for a specific market regime."""
        return [o for o in self.outcomes if o.market_regime == regime]

    def get_outcomes_by_date_range(
        self,
        start_date: str,
        end_date: str,
    ) -> List[TradeOutcome]:
        """Get outcomes within a date range."""
        return [
            o for o in self.outcomes
            if start_date <= o.trade_date <= end_date
        ]

    def export_csv(self, path: Optional[str] = None) -> str:
        """
        Export outcomes to CSV for analysis in other tools.

        Args:
            path: Custom path, uses default if not provided

        Returns:
            Path where CSV was saved
        """
        import csv

        if path is None:
            path = self.output_dir / f"outcomes_{self._session_id}.csv"
        else:
            path = Path(path)

        if not self.outcomes:
            logger.warning("No outcomes to export")
            return str(path)

        # Get all fields from first outcome
        fieldnames = list(self.outcomes[0].to_dict().keys())

        with open(path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for outcome in self.outcomes:
                row = outcome.to_dict()
                # Flatten reports_summary to string
                row["reports_summary"] = json.dumps(row["reports_summary"])
                writer.writerow(row)

        logger.info(f"Exported {len(self.outcomes)} outcomes to {path}")
        return str(path)


def detect_market_regime(
    prices: List[float],
    lookback: int = 20,
) -> str:
    """
    Simple market regime detection based on price trend.

    Args:
        prices: Recent price history
        lookback: Number of periods to analyze

    Returns:
        "bull", "bear", or "sideways"
    """
    if len(prices) < lookback:
        return "unknown"

    recent_prices = prices[-lookback:]
    start_price = recent_prices[0]
    end_price = recent_prices[-1]

    change_pct = ((end_price - start_price) / start_price) * 100

    if change_pct > 5:
        return "bull"
    elif change_pct < -5:
        return "bear"
    else:
        return "sideways"


def detect_volatility_regime(
    prices: List[float],
    lookback: int = 20,
) -> str:
    """
    Simple volatility regime detection based on price changes.

    Args:
        prices: Recent price history
        lookback: Number of periods to analyze

    Returns:
        "low", "medium", or "high"
    """
    if len(prices) < lookback:
        return "unknown"

    recent_prices = prices[-lookback:]

    # Calculate daily returns
    returns = []
    for i in range(1, len(recent_prices)):
        daily_return = (recent_prices[i] - recent_prices[i-1]) / recent_prices[i-1]
        returns.append(abs(daily_return))

    avg_volatility = sum(returns) / len(returns) if returns else 0

    if avg_volatility < 0.01:  # < 1% average daily move
        return "low"
    elif avg_volatility < 0.025:  # < 2.5% average daily move
        return "medium"
    else:
        return "high"


# Multi-horizon projection horizons (label -> trading days)
HORIZONS = {
    "1d": 1,    # 1 day = 1 trading day
    "3d": 3,    # 3 days = 3 trading days
    "1w": 5,    # 1 week = 5 trading days
    "2w": 10,   # 2 weeks = 10 trading days
    "4w": 20,   # 4 weeks = 20 trading days
    "8w": 40,   # 8 weeks = 40 trading days
    "13w": 65,  # 13 weeks = 65 trading days
}

# HOLD correctness thresholds by horizon (percentage points)
HOLD_THRESHOLDS = {
    "1d": 0.2,
    "3d": 0.35,
    "1w": 0.5,
    "2w": 0.8,
    "4w": 1.2,
    "8w": 1.8,
    "13w": 2.5,
}


def validate_outcome_against_market(outcome: TradeOutcome) -> TradeOutcome:
    """
    Validate a single outcome against actual market prices.

    Fetches the close price on the decision date and the next trading day's
    open/close to calculate actual returns.

    Args:
        outcome: TradeOutcome to validate

    Returns:
        Updated TradeOutcome with market validation data
    """
    # Transaction costs: ~0.15% round-trip (spread + slippage)
    TRANSACTION_COST_PCT = 0.15

    if outcome.validated:
        return outcome

    try:
        # Parse the decision date
        decision_date = datetime.strptime(outcome.trade_date, "%Y-%m-%d")

        # Fetch enough history for regime detection (30 trading days ~= 45 calendar days)
        # plus a few days after the decision for next-day validation
        start_date = decision_date - timedelta(days=45)
        end_date = decision_date + timedelta(days=130)

        ticker = yf.Ticker(outcome.ticker)
        hist = ticker.history(start=start_date, end=end_date)

        if hist.empty:
            logger.warning(f"No price data found for {outcome.ticker}")
            return outcome

        # Find the decision date's close price
        decision_date_str = decision_date.strftime("%Y-%m-%d")

        # Get trading days from the data
        trading_days = hist.index.strftime("%Y-%m-%d").tolist()

        # Find the decision date or the closest prior trading day
        decision_idx = None
        for i, day in enumerate(trading_days):
            if day == decision_date_str:
                decision_idx = i
                break
            elif day > decision_date_str:
                # Decision was on a non-trading day, use prior trading day
                decision_idx = i - 1 if i > 0 else None
                break

        if decision_idx is None or decision_idx < 0:
            # Decision date is before our data range
            logger.warning(f"Decision date {decision_date_str} not found in price data for {outcome.ticker}")
            return outcome

        # Get decision date close
        decision_close = float(hist.iloc[decision_idx]["Close"])
        outcome.decision_date_close = decision_close

        # Get next trading day prices
        if decision_idx + 1 < len(hist):
            next_day = hist.iloc[decision_idx + 1]
            outcome.next_day_open = float(next_day["Open"])
            outcome.next_day_close = float(next_day["Close"])

            # Calculate percentage change (close to close)
            if decision_close > 0:
                outcome.next_day_change_pct = (
                    (outcome.next_day_close - decision_close) / decision_close
                ) * 100

            # Determine if decision was correct (accounting for transaction costs)
            # BUY is correct if price went up more than transaction costs
            if outcome.decision == "BUY":
                outcome.decision_correct = outcome.next_day_change_pct > TRANSACTION_COST_PCT
            # SELL is correct if price went down more than transaction costs
            elif outcome.decision == "SELL":
                outcome.decision_correct = outcome.next_day_change_pct < -TRANSACTION_COST_PCT
            else:  # HOLD
                # HOLD is "correct" if change was minimal (< 0.5% — tighter threshold)
                outcome.decision_correct = abs(outcome.next_day_change_pct) < 0.5

            # Update P&L fields for a hypothetical $10,000 position
            position_value = 10000.0
            shares = position_value / decision_close
            outcome.entry_price = decision_close
            outcome.exit_price = outcome.next_day_close
            outcome.quantity = shares

            if outcome.decision == "BUY":
                outcome.pnl = (outcome.next_day_close - decision_close) * shares
            elif outcome.decision == "SELL":
                # For SELL, profit if price goes down
                outcome.pnl = (decision_close - outcome.next_day_close) * shares
            else:
                outcome.pnl = 0.0

            # Subtract transaction costs (round-trip: entry + exit)
            spread_cost = position_value * 0.001   # 0.1% spread
            slippage = position_value * 0.0005      # 0.05% slippage
            total_cost = spread_cost + slippage
            outcome.commission = total_cost
            if outcome.decision != "HOLD":
                outcome.pnl -= total_cost

            outcome.return_pct = outcome.next_day_change_pct
            outcome.holding_period_days = 1

        # 5-day forward return (secondary metric)
        if decision_idx is not None and decision_idx + 5 < len(hist):
            day5_close = float(hist.iloc[decision_idx + 5]["Close"])
            if decision_close > 0:
                outcome.day5_change_pct = ((day5_close - decision_close) / decision_close) * 100
                # Use same transaction cost threshold for consistency
                outcome.day5_correct = (
                    (outcome.decision == "BUY" and outcome.day5_change_pct > TRANSACTION_COST_PCT)
                    or (outcome.decision == "SELL" and outcome.day5_change_pct < -TRANSACTION_COST_PCT)
                    or (outcome.decision == "HOLD" and abs(outcome.day5_change_pct) < 1.0)
                )

        # Detect market and volatility regimes using price history up to decision date
        prices_up_to_decision = hist.iloc[:decision_idx + 1]["Close"].tolist()
        if len(prices_up_to_decision) >= 5:
            outcome.market_regime = detect_market_regime(prices_up_to_decision)
            outcome.volatility_regime = detect_volatility_regime(prices_up_to_decision)

        outcome.validated = True
        logger.debug(f"Validated {outcome.ticker} {outcome.trade_date}: {outcome.next_day_change_pct:+.2f}%")

    except Exception as e:
        logger.warning(f"Failed to validate {outcome.ticker} {outcome.trade_date}: {e}")

    return outcome


def validate_multi_horizon_outcome(
    outcome: TradeOutcome,
    horizons: Optional[List[str]] = None,
) -> TradeOutcome:
    """Validate a single outcome against multiple projection horizons.

    Must be called AFTER validate_outcome_against_market() which populates
    decision_date_close. Uses trading days (not calendar days) for accurate
    horizon targeting.

    Args:
        outcome: Validated TradeOutcome.
        horizons: Optional list of horizon labels to validate (e.g. ["1d", "3d", "1w"]).
                  If None, validates all horizons in HORIZONS.
    """
    TRANSACTION_COST_PCT = 0.15

    if not outcome.validated or outcome.decision_date_close <= 0:
        logger.warning(
            f"Cannot validate horizons for {outcome.ticker} {outcome.trade_date}: "
            f"not yet validated or no decision_date_close"
        )
        return outcome

    try:
        decision_date = datetime.strptime(outcome.trade_date, "%Y-%m-%d")

        start_date = decision_date - timedelta(days=45)
        end_date = decision_date + timedelta(days=130)

        ticker = yf.Ticker(outcome.ticker)
        hist = ticker.history(start=start_date, end=end_date)

        if hist.empty:
            logger.warning(f"No price data for multi-horizon validation: {outcome.ticker}")
            return outcome

        trading_days = hist.index.strftime("%Y-%m-%d").tolist()
        decision_date_str = decision_date.strftime("%Y-%m-%d")

        decision_idx = None
        for i, day in enumerate(trading_days):
            if day == decision_date_str:
                decision_idx = i
                break
            elif day > decision_date_str:
                decision_idx = i - 1 if i > 0 else None
                break

        if decision_idx is None or decision_idx < 0:
            logger.warning(
                f"Decision date {decision_date_str} not found for "
                f"multi-horizon validation: {outcome.ticker}"
            )
            return outcome

        decision_close = float(hist.iloc[decision_idx]["Close"])
        horizon_outcomes = {}

        selected = {k: v for k, v in HORIZONS.items()
                    if horizons is None or k in horizons}
        for label, trading_days_forward in selected.items():
            target_idx = decision_idx + trading_days_forward

            if target_idx >= len(hist):
                logger.debug(
                    f"Insufficient data for {label} horizon "
                    f"({outcome.ticker} {outcome.trade_date}): "
                    f"need idx {target_idx}, have {len(hist)}"
                )
                continue

            target_close = float(hist.iloc[target_idx]["Close"])
            change_pct = ((target_close - decision_close) / decision_close) * 100
            target_date = hist.index[target_idx].strftime("%Y-%m-%d")

            hold_threshold = HOLD_THRESHOLDS[label]

            if outcome.decision == "BUY":
                correct = change_pct > TRANSACTION_COST_PCT
            elif outcome.decision == "SELL":
                correct = change_pct < -TRANSACTION_COST_PCT
            else:  # HOLD
                correct = abs(change_pct) < hold_threshold

            horizon_outcomes[label] = {
                "target_date": target_date,
                "target_close": round(target_close, 4),
                "change_pct": round(change_pct, 4),
                "correct": correct,
                "trading_days": trading_days_forward,
                "hold_threshold": hold_threshold,
            }

        outcome.horizon_outcomes = horizon_outcomes
        logger.debug(
            f"Multi-horizon validated {outcome.ticker} {outcome.trade_date}: "
            f"{len(horizon_outcomes)} horizons"
        )

    except Exception as e:
        logger.warning(
            f"Failed multi-horizon validation for "
            f"{outcome.ticker} {outcome.trade_date}: {e}"
        )

    return outcome


def validate_all_outcomes(
    outcomes: List[TradeOutcome],
    progress_callback: Optional[callable] = None,
) -> List[TradeOutcome]:
    """
    Validate all outcomes against market prices.

    Args:
        outcomes: List of outcomes to validate
        progress_callback: Optional callback(current, total) for progress updates

    Returns:
        List of validated outcomes
    """
    validated = []
    total = len(outcomes)

    for i, outcome in enumerate(outcomes):
        if not outcome.validated:
            outcome = validate_outcome_against_market(outcome)
        validated.append(outcome)

        if progress_callback:
            progress_callback(i + 1, total)

    return validated

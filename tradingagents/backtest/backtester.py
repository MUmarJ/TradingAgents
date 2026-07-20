"""
Core backtesting engine.

This module provides the main Backtester class that orchestrates
the backtesting process, managing data, execution, and performance tracking.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Optional, Any, Callable

import pandas as pd

from .config import BacktestConfig
from .data_handler import HistoricalDataHandler
from .execution import ExecutionSimulator, Order, Fill, OrderSide, OrderStatus
from .strategy import BaseStrategy, Signal, Position, PositionSizer, RiskManager
from .performance import PerformanceAnalyzer, PerformanceMetrics
from .exceptions import BacktestError, ExecutionError
from .outcome_tracker import OutcomeTracker, detect_market_regime, detect_volatility_regime


logger = logging.getLogger(__name__)


@dataclass
class BacktestState:
    """Current state of the backtest."""

    timestamp: datetime
    cash: Decimal
    positions: Dict[str, Position] = field(default_factory=dict)
    pending_orders: List[Order] = field(default_factory=list)
    filled_orders: List[Fill] = field(default_factory=list)
    equity_history: List[Dict[str, Any]] = field(default_factory=list)
    trade_history: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def portfolio_value(self) -> Decimal:
        """Calculate total portfolio value."""
        position_value = sum(pos.market_value for pos in self.positions.values())
        return self.cash + position_value


@dataclass
class BacktestResult:
    """Complete backtest results."""

    config: BacktestConfig
    metrics: PerformanceMetrics
    equity_curve: pd.Series
    trades: List[Dict[str, Any]]
    fills: List[Fill]
    signals: List[Signal]
    final_positions: Dict[str, Position]
    final_cash: Decimal
    execution_log: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert results to dictionary."""
        return {
            "config": {
                "initial_capital": float(self.config.initial_capital),
                "start_date": self.config.start_date.isoformat(),
                "end_date": self.config.end_date.isoformat(),
                "tickers": self.config.tickers,
            },
            "metrics": self.metrics.to_dict(),
            "equity_curve": self.equity_curve.to_dict(),
            "num_trades": len(self.trades),
            "num_fills": len(self.fills),
            "num_signals": len(self.signals),
            "final_cash": float(self.final_cash),
            "final_positions": {
                ticker: pos.to_dict() for ticker, pos in self.final_positions.items()
            },
        }


class Backtester:
    """
    Main backtesting engine.

    Coordinates data handling, strategy execution, order management,
    and performance calculation.
    """

    def __init__(self, config: BacktestConfig, outcome_tracker: Optional[OutcomeTracker] = None):
        """
        Initialize backtester.

        Args:
            config: Backtest configuration
            outcome_tracker: Optional outcome tracker for logging trade results
        """
        self.config = config
        self.outcome_tracker = outcome_tracker

        # Initialize components
        self.data_handler = HistoricalDataHandler(
            data_source=config.data_source,
            cache_dir=config.cache_dir,
        )
        self.execution_simulator = ExecutionSimulator(
            slippage_model=config.slippage_model,
            slippage_bps=config.slippage_bps,
            commission_model=config.commission_model,
            commission_per_share=config.commission_per_share,
            commission_min=config.commission_min,
        )
        self.position_sizer = PositionSizer(
            method=config.position_sizing_method,
            params=config.position_sizing_params,
        )
        self.risk_manager = RiskManager(
            max_position_size=config.max_position_size,
            max_leverage=config.max_leverage,
            stop_loss_pct=config.stop_loss_pct,
        )
        self.performance_analyzer = PerformanceAnalyzer(
            risk_free_rate=config.risk_free_rate,
        )

        # State
        self.state: Optional[BacktestState] = None
        self.strategy: Optional[BaseStrategy] = None
        self.all_signals: List[Signal] = []

        # Callbacks
        self._on_bar_callbacks: List[Callable] = []
        self._on_fill_callbacks: List[Callable] = []
        self._on_signal_callbacks: List[Callable] = []

        # Track signals and price history for outcome tracking
        self._position_signals: Dict[str, Signal] = {}  # ticker -> opening signal
        self._price_history: Dict[str, List[float]] = {}  # ticker -> recent prices
        self._reports_summary: Dict[str, Dict[str, str]] = {}  # ticker -> report summaries

        logger.info(f"Backtester initialized with config: {config}")

    def run(self, strategy: BaseStrategy) -> BacktestResult:
        """
        Run backtest with the given strategy.

        Args:
            strategy: Trading strategy to backtest

        Returns:
            BacktestResult with all metrics and data
        """
        logger.info(f"Starting backtest for strategy: {strategy.name}")

        self.strategy = strategy
        self._initialize_state()

        # Load data
        logger.info(f"Loading data for {len(self.config.tickers)} tickers")
        self._load_data()

        # Initialize strategy
        strategy.initialize(self.config.tickers, self.config.start_date)

        # Get trading dates
        trading_dates = self._get_trading_dates()
        logger.info(f"Running backtest over {len(trading_dates)} trading days")

        # Main backtest loop
        for timestamp in trading_dates:
            self._process_bar(timestamp)

        # Finalize
        strategy.finalize()

        # Calculate performance
        equity_curve = self._build_equity_curve()
        metrics = self.performance_analyzer.calculate_metrics(
            equity_curve=equity_curve,
            trades=self.state.trade_history,
        )

        result = BacktestResult(
            config=self.config,
            metrics=metrics,
            equity_curve=equity_curve,
            trades=self.state.trade_history,
            fills=self.state.filled_orders,
            signals=self.all_signals,
            final_positions=self.state.positions.copy(),
            final_cash=self.state.cash,
        )

        logger.info(f"Backtest complete. Final value: ${self.state.portfolio_value:,.2f}")
        logger.info(f"Total return: {metrics.total_return * 100:.2f}%")

        return result

    def _initialize_state(self) -> None:
        """Initialize backtest state."""
        self.state = BacktestState(
            timestamp=self.config.start_date,
            cash=self.config.initial_capital,
        )
        self.all_signals = []

    def _load_data(self) -> None:
        """Load historical data for all tickers."""
        for ticker in self.config.tickers:
            self.data_handler.load_data(
                ticker=ticker,
                start_date=self.config.start_date - timedelta(days=365),  # Extra for indicators
                end_date=self.config.end_date,
            )

    def _get_trading_dates(self) -> List[datetime]:
        """Get list of trading dates in the backtest period."""
        # Use the first ticker's data to determine trading dates
        if not self.config.tickers:
            raise BacktestError("No tickers configured")

        first_ticker = self.config.tickers[0]
        data = self.data_handler.get_data(
            first_ticker,
            self.config.start_date,
            self.config.end_date,
        )

        return sorted(data.index.tolist())

    def _process_bar(self, timestamp: datetime) -> None:
        """Process a single bar/period."""
        self.state.timestamp = timestamp

        # Update position prices
        self._update_positions(timestamp)

        # Check stop losses
        self._check_stop_losses(timestamp)

        # Get data for strategy
        data = self._get_strategy_data(timestamp)

        # Call strategy's on_bar
        self.strategy.on_bar(timestamp, data)

        # Generate signals
        signals = self.strategy.generate_signals(
            timestamp=timestamp,
            data=data,
            positions=self.state.positions,
            portfolio_value=self.state.portfolio_value,
        )

        # Process signals
        for signal in signals:
            self._process_signal(signal, timestamp)

        # Process pending orders
        self._process_pending_orders(timestamp)

        # Record equity
        self.state.equity_history.append({
            "timestamp": timestamp,
            "cash": float(self.state.cash),
            "positions_value": float(
                sum(pos.market_value for pos in self.state.positions.values())
            ),
            "total_value": float(self.state.portfolio_value),
        })

        # Call callbacks
        for callback in self._on_bar_callbacks:
            callback(timestamp, self.state)

    def _update_positions(self, timestamp: datetime) -> None:
        """Update position prices with current market data."""
        for ticker, position in list(self.state.positions.items()):
            try:
                current_price = self.data_handler.get_price(ticker, timestamp)
                if current_price is None:
                    continue

                # Update position
                position.current_price = current_price
                position.unrealized_pnl = (
                    (current_price - position.avg_entry_price) * position.quantity
                )

                # Track price history for regime detection (outcome tracking)
                if ticker not in self._price_history:
                    self._price_history[ticker] = []
                self._price_history[ticker].append(float(current_price))
                # Keep only last 50 prices
                if len(self._price_history[ticker]) > 50:
                    self._price_history[ticker] = self._price_history[ticker][-50:]

            except Exception as e:
                logger.warning(f"Could not update price for {ticker}: {e}")

    def _check_stop_losses(self, timestamp: datetime) -> None:
        """Check and execute stop losses."""
        for ticker, position in list(self.state.positions.items()):
            if self.risk_manager.check_stop_loss(position):
                logger.info(f"Stop loss triggered for {ticker}")

                # Create market sell order
                order = Order(
                    ticker=ticker,
                    side=OrderSide.SELL if position.is_long else OrderSide.BUY,
                    quantity=abs(position.quantity),
                    timestamp=timestamp,
                )
                self.state.pending_orders.append(order)

    def _get_strategy_data(self, timestamp: datetime) -> Dict[str, pd.DataFrame]:
        """Get historical data up to timestamp for all tickers."""
        data = {}
        for ticker in self.config.tickers:
            try:
                df = self.data_handler.get_data(
                    ticker,
                    self.config.start_date - timedelta(days=365),
                    timestamp,
                )
                # Prevent look-ahead bias
                df = df[df.index <= timestamp]
                data[ticker] = df
            except Exception as e:
                logger.warning(f"Could not get data for {ticker}: {e}")

        return data

    def _process_signal(self, signal: Signal, timestamp: datetime) -> None:
        """Process a trading signal."""
        self.all_signals.append(signal)

        # Call signal callbacks
        for callback in self._on_signal_callbacks:
            callback(signal)

        if signal.action == "hold":
            return

        # Track opening signals for outcome tracking (BUY signals open positions)
        if signal.action == "buy":
            self._position_signals[signal.ticker] = signal

        # Risk check
        approved, reason = self.risk_manager.check_signal(
            signal, self.state.positions, self.state.portfolio_value
        )
        if not approved:
            logger.info(f"Signal rejected: {reason}")
            return

        # Get current price
        current_price = self.data_handler.get_price(signal.ticker, timestamp)
        if current_price is None:
            logger.warning(f"No price available for {signal.ticker}")
            return

        # Calculate position size
        quantity = self.position_sizer.calculate_position_size(
            signal=signal,
            portfolio_value=self.state.portfolio_value,
            current_price=current_price,
            max_position_size=self.config.max_position_size,
        )

        if quantity <= 0:
            return

        # For sell signals, adjust quantity to current position
        if signal.action == "sell":
            position = self.state.positions.get(signal.ticker)
            if position:
                quantity = min(quantity, abs(position.quantity))
            else:
                return  # No position to sell

        # Create order
        order = Order(
            ticker=signal.ticker,
            side=OrderSide.BUY if signal.action == "buy" else OrderSide.SELL,
            quantity=quantity,
            timestamp=timestamp,
        )
        self.state.pending_orders.append(order)

    def _process_pending_orders(self, timestamp: datetime) -> None:
        """Process all pending orders."""
        orders_to_process = self.state.pending_orders.copy()
        self.state.pending_orders = []

        for order in orders_to_process:
            try:
                # Get current price
                current_price = self.data_handler.get_price(order.ticker, timestamp)
                if current_price is None:
                    logger.warning(f"No price for {order.ticker}, order cancelled")
                    continue

                # Get OHLC for more realistic execution
                bar_data = self.data_handler.get_bar(order.ticker, timestamp)

                # Simulate execution
                fill = self.execution_simulator.execute_order(
                    order=order,
                    current_price=current_price,
                    timestamp=timestamp,
                    available_cash=self.state.cash,
                    bar_data=bar_data,
                )

                if fill:
                    self._apply_fill(fill)

            except ExecutionError as e:
                logger.warning(f"Order execution failed: {e}")
            except Exception as e:
                logger.error(f"Error processing order: {e}")

    def _apply_fill(self, fill: Fill) -> None:
        """Apply a fill to the portfolio."""
        self.state.filled_orders.append(fill)

        # Update cash
        if fill.side == OrderSide.BUY:
            self.state.cash -= fill.total_cost
        else:
            self.state.cash += fill.total_cost - fill.commission

        # Update positions
        self._update_position_from_fill(fill)

        # Notify strategy
        self.strategy.on_fill(fill)

        # Call fill callbacks
        for callback in self._on_fill_callbacks:
            callback(fill)

        logger.debug(f"Fill applied: {fill}")

    def _update_position_from_fill(self, fill: Fill) -> None:
        """Update position based on fill."""
        ticker = fill.ticker
        position = self.state.positions.get(ticker)

        if fill.side == OrderSide.BUY:
            if position is None:
                # New position
                position = Position(
                    ticker=ticker,
                    quantity=fill.quantity,
                    avg_entry_price=fill.price,
                    current_price=fill.price,
                    unrealized_pnl=Decimal("0"),
                    entry_timestamp=fill.timestamp,
                )
                self.state.positions[ticker] = position
            else:
                # Add to existing position
                total_quantity = position.quantity + fill.quantity
                total_cost = (
                    position.quantity * position.avg_entry_price
                    + fill.quantity * fill.price
                )
                position.avg_entry_price = total_cost / total_quantity
                position.quantity = total_quantity

        else:  # SELL
            if position is None:
                logger.warning(f"Sell fill for non-existent position: {ticker}")
                return

            # Record trade
            pnl = (fill.price - position.avg_entry_price) * fill.quantity - fill.commission
            trade_return = float(pnl / (position.avg_entry_price * fill.quantity))

            self.state.trade_history.append({
                "ticker": ticker,
                "entry_time": position.entry_timestamp,
                "exit_time": fill.timestamp,
                "entry_price": float(position.avg_entry_price),
                "exit_price": float(fill.price),
                "quantity": float(fill.quantity),
                "pnl": float(pnl),
                "return": trade_return,
                "commission": float(fill.commission),
            })

            # Record outcome if tracker is enabled
            if self.outcome_tracker:
                # Detect market regime from price history
                price_history = self._price_history.get(ticker, [])
                market_regime = detect_market_regime(price_history) if price_history else "unknown"
                volatility_regime = detect_volatility_regime(price_history) if price_history else "unknown"

                # Get opening signal info
                opening_signal = self._position_signals.get(ticker)
                decision = "BUY"  # Default, since we're closing a long position
                confidence = None
                if opening_signal:
                    decision = opening_signal.action.upper()
                    confidence = getattr(opening_signal, "confidence", None)

                # Get reports summary if available
                reports_summary = self._reports_summary.get(ticker, {})

                self.outcome_tracker.record(
                    ticker=ticker,
                    decision=decision,
                    entry_price=float(position.avg_entry_price),
                    exit_price=float(fill.price),
                    quantity=float(fill.quantity),
                    pnl=float(pnl),
                    entry_timestamp=position.entry_timestamp,
                    exit_timestamp=fill.timestamp,
                    commission=float(fill.commission),
                    reports_summary=reports_summary,
                    confidence=confidence,
                    market_regime=market_regime,
                    volatility_regime=volatility_regime,
                    strategy_name=self.strategy.name if self.strategy else "Unknown",
                )

                # Clean up tracking data
                if ticker in self._position_signals:
                    del self._position_signals[ticker]
                if ticker in self._reports_summary:
                    del self._reports_summary[ticker]

            # Update position
            position.quantity -= fill.quantity

            if position.quantity <= 0:
                del self.state.positions[ticker]

    def _build_equity_curve(self) -> pd.Series:
        """Build equity curve from history."""
        if not self.state.equity_history:
            return pd.Series()

        df = pd.DataFrame(self.state.equity_history)
        df.set_index("timestamp", inplace=True)
        return df["total_value"]

    def on_bar(self, callback: Callable) -> None:
        """Register a callback for each bar."""
        self._on_bar_callbacks.append(callback)

    def on_fill(self, callback: Callable) -> None:
        """Register a callback for fills."""
        self._on_fill_callbacks.append(callback)

    def on_signal(self, callback: Callable) -> None:
        """Register a callback for signals."""
        self._on_signal_callbacks.append(callback)

    def set_reports_summary(self, ticker: str, reports: Dict[str, str]) -> None:
        """
        Set report summaries for a ticker (for outcome tracking).

        This should be called when a trading decision is made, to associate
        the analysis reports with the subsequent trade outcome.

        Args:
            ticker: Stock symbol
            reports: Dictionary with report summaries (e.g., {"market": "...", "sentiment": "..."})
        """
        self._reports_summary[ticker] = reports


def run_backtest(
    strategy: BaseStrategy,
    tickers: List[str],
    start_date: datetime,
    end_date: datetime,
    initial_capital: Decimal = Decimal("100000"),
    **kwargs,
) -> BacktestResult:
    """
    Convenience function to run a backtest.

    Args:
        strategy: Trading strategy
        tickers: List of tickers to trade
        start_date: Start date
        end_date: End date
        initial_capital: Starting capital
        **kwargs: Additional config options

    Returns:
        BacktestResult
    """
    config = BacktestConfig(
        initial_capital=initial_capital,
        start_date=start_date,
        end_date=end_date,
        tickers=tickers,
        **kwargs,
    )

    backtester = Backtester(config)
    return backtester.run(strategy)

"""
Backtesting framework for TradingAgents.

This module provides a comprehensive backtesting system for evaluating
trading strategies with realistic execution simulation.

Example usage:
    from tradingagents.backtest import (
        Backtester,
        BacktestConfig,
        SimpleMovingAverageStrategy,
        run_backtest,
    )
    from datetime import datetime
    from decimal import Decimal

    # Using convenience function
    result = run_backtest(
        strategy=SimpleMovingAverageStrategy(short_window=50, long_window=200),
        tickers=["AAPL", "GOOGL"],
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2023, 12, 31),
        initial_capital=Decimal("100000"),
    )

    print(result.metrics.summary())

    # Using full configuration
    config = BacktestConfig(
        initial_capital=Decimal("100000"),
        start_date=datetime(2020, 1, 1),
        end_date=datetime(2023, 12, 31),
        tickers=["AAPL", "GOOGL", "MSFT"],
        slippage_bps=5,
        commission_per_share=Decimal("0.005"),
    )

    backtester = Backtester(config)
    result = backtester.run(strategy)
"""

from .config import (
    BacktestConfig,
    WalkForwardConfig,
    MonteCarloConfig,
    OrderType,
    DataSource,
    SlippageModel,
    CommissionModel,
)

from .exceptions import (
    BacktestError,
    DataError,
    DataNotFoundError,
    ExecutionError,
    InsufficientCapitalError,
    ConfigurationError,
    StrategyError,
    PerformanceError,
)

from .data_handler import HistoricalDataHandler

from .execution import (
    ExecutionSimulator,
    Order,
    Fill,
    OrderSide,
    OrderStatus,
)

from .strategy import (
    BaseStrategy,
    Signal,
    Position,
    BuyAndHoldStrategy,
    SimpleMovingAverageStrategy,
    PositionSizer,
    RiskManager,
)

from .performance import (
    PerformanceAnalyzer,
    PerformanceMetrics,
    DrawdownInfo,
    calculate_var,
    calculate_cvar,
)

from .backtester import (
    Backtester,
    BacktestState,
    BacktestResult,
    run_backtest,
)

from .outcome_tracker import (
    OutcomeTracker,
    TradeOutcome,
    OutcomeStats,
    detect_market_regime,
    detect_volatility_regime,
    validate_outcome_against_market,
    validate_multi_horizon_outcome,
    validate_all_outcomes,
    HORIZONS,
    HOLD_THRESHOLDS,
)


__all__ = [
    # Config
    "BacktestConfig",
    "WalkForwardConfig",
    "MonteCarloConfig",
    "OrderType",
    "DataSource",
    "SlippageModel",
    "CommissionModel",
    # Exceptions
    "BacktestError",
    "DataError",
    "DataNotFoundError",
    "ExecutionError",
    "InsufficientCapitalError",
    "ConfigurationError",
    "StrategyError",
    "PerformanceError",
    # Data handling
    "HistoricalDataHandler",
    # Execution
    "ExecutionSimulator",
    "Order",
    "Fill",
    "OrderSide",
    "OrderStatus",
    # Strategy
    "BaseStrategy",
    "Signal",
    "Position",
    "BuyAndHoldStrategy",
    "SimpleMovingAverageStrategy",
    "PositionSizer",
    "RiskManager",
    # Performance
    "PerformanceAnalyzer",
    "PerformanceMetrics",
    "DrawdownInfo",
    "calculate_var",
    "calculate_cvar",
    # Backtester
    "Backtester",
    "BacktestState",
    "BacktestResult",
    "run_backtest",
    # Outcome Tracking
    "OutcomeTracker",
    "TradeOutcome",
    "OutcomeStats",
    "detect_market_regime",
    "detect_volatility_regime",
    "validate_outcome_against_market",
    "validate_multi_horizon_outcome",
    "validate_all_outcomes",
    "HORIZONS",
    "HOLD_THRESHOLDS",
]

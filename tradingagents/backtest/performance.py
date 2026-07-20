"""
Performance metrics calculation for backtesting.

This module provides comprehensive performance analysis including
risk-adjusted returns, drawdown analysis, and statistical metrics.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional, Any, Tuple

import numpy as np
import pandas as pd

from .exceptions import PerformanceError


logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """
    Complete performance metrics for a backtest.

    Attributes:
        total_return: Total return (e.g., 0.25 for 25%)
        annualized_return: Annualized return
        volatility: Annualized volatility (standard deviation)
        sharpe_ratio: Sharpe ratio (assuming 0 risk-free rate)
        sortino_ratio: Sortino ratio (downside deviation)
        max_drawdown: Maximum drawdown
        max_drawdown_duration: Maximum drawdown duration in days
        calmar_ratio: Calmar ratio (return / max drawdown)
        win_rate: Percentage of winning trades
        profit_factor: Gross profit / gross loss
        avg_win: Average winning trade return
        avg_loss: Average losing trade return
        num_trades: Total number of trades
        num_winning_trades: Number of winning trades
        num_losing_trades: Number of losing trades
        best_trade: Best single trade return
        worst_trade: Worst single trade return
        avg_trade_duration: Average trade holding period
        exposure_time: Percentage of time in market
        start_date: Backtest start date
        end_date: Backtest end date
        initial_capital: Starting capital
        final_capital: Ending capital
        benchmark_return: Benchmark return (if applicable)
        alpha: Alpha vs benchmark
        beta: Beta vs benchmark
        information_ratio: Information ratio vs benchmark
    """

    total_return: float = 0.0
    annualized_return: float = 0.0
    volatility: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    max_drawdown: float = 0.0
    max_drawdown_duration: int = 0
    calmar_ratio: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    num_trades: int = 0
    num_winning_trades: int = 0
    num_losing_trades: int = 0
    best_trade: float = 0.0
    worst_trade: float = 0.0
    avg_trade_duration: float = 0.0
    exposure_time: float = 0.0
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    initial_capital: float = 0.0
    final_capital: float = 0.0
    benchmark_return: Optional[float] = None
    alpha: Optional[float] = None
    beta: Optional[float] = None
    information_ratio: Optional[float] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "total_return": self.total_return,
            "annualized_return": self.annualized_return,
            "volatility": self.volatility,
            "sharpe_ratio": self.sharpe_ratio,
            "sortino_ratio": self.sortino_ratio,
            "max_drawdown": self.max_drawdown,
            "max_drawdown_duration": self.max_drawdown_duration,
            "calmar_ratio": self.calmar_ratio,
            "win_rate": self.win_rate,
            "profit_factor": self.profit_factor,
            "avg_win": self.avg_win,
            "avg_loss": self.avg_loss,
            "num_trades": self.num_trades,
            "num_winning_trades": self.num_winning_trades,
            "num_losing_trades": self.num_losing_trades,
            "best_trade": self.best_trade,
            "worst_trade": self.worst_trade,
            "avg_trade_duration": self.avg_trade_duration,
            "exposure_time": self.exposure_time,
            "start_date": self.start_date.isoformat() if self.start_date else None,
            "end_date": self.end_date.isoformat() if self.end_date else None,
            "initial_capital": self.initial_capital,
            "final_capital": self.final_capital,
            "benchmark_return": self.benchmark_return,
            "alpha": self.alpha,
            "beta": self.beta,
            "information_ratio": self.information_ratio,
        }

    def summary(self) -> str:
        """Generate human-readable summary."""
        lines = [
            "=" * 50,
            "PERFORMANCE SUMMARY",
            "=" * 50,
            f"Period: {self.start_date} to {self.end_date}",
            f"Initial Capital: ${self.initial_capital:,.2f}",
            f"Final Capital: ${self.final_capital:,.2f}",
            "",
            "RETURNS",
            "-" * 30,
            f"Total Return: {self.total_return * 100:.2f}%",
            f"Annualized Return: {self.annualized_return * 100:.2f}%",
            f"Volatility: {self.volatility * 100:.2f}%",
            "",
            "RISK-ADJUSTED METRICS",
            "-" * 30,
            f"Sharpe Ratio: {self.sharpe_ratio:.2f}",
            f"Sortino Ratio: {self.sortino_ratio:.2f}",
            f"Calmar Ratio: {self.calmar_ratio:.2f}",
            f"Max Drawdown: {self.max_drawdown * 100:.2f}%",
            f"Max Drawdown Duration: {self.max_drawdown_duration} days",
            "",
            "TRADE STATISTICS",
            "-" * 30,
            f"Total Trades: {self.num_trades}",
            f"Win Rate: {self.win_rate * 100:.2f}%",
            f"Profit Factor: {self.profit_factor:.2f}",
            f"Average Win: {self.avg_win * 100:.2f}%",
            f"Average Loss: {self.avg_loss * 100:.2f}%",
            f"Best Trade: {self.best_trade * 100:.2f}%",
            f"Worst Trade: {self.worst_trade * 100:.2f}%",
            "=" * 50,
        ]

        if self.benchmark_return is not None:
            lines.insert(-1, "")
            lines.insert(-1, "BENCHMARK COMPARISON")
            lines.insert(-1, "-" * 30)
            lines.insert(-1, f"Benchmark Return: {self.benchmark_return * 100:.2f}%")
            if self.alpha is not None:
                lines.insert(-1, f"Alpha: {self.alpha * 100:.2f}%")
            if self.beta is not None:
                lines.insert(-1, f"Beta: {self.beta:.2f}")

        return "\n".join(lines)


@dataclass
class DrawdownInfo:
    """Information about a drawdown period."""

    start_date: datetime
    end_date: Optional[datetime]
    recovery_date: Optional[datetime]
    peak_value: float
    trough_value: float
    drawdown: float
    duration: int
    recovery_duration: Optional[int]


class PerformanceAnalyzer:
    """
    Analyzes backtest results and calculates performance metrics.
    """

    def __init__(
        self,
        risk_free_rate: float = 0.0,
        trading_days_per_year: int = 252,
    ):
        """
        Initialize performance analyzer.

        Args:
            risk_free_rate: Annual risk-free rate for Sharpe/Sortino calculation
            trading_days_per_year: Number of trading days per year
        """
        self.risk_free_rate = risk_free_rate
        self.trading_days_per_year = trading_days_per_year

    def calculate_metrics(
        self,
        equity_curve: pd.Series,
        trades: Optional[List[Dict[str, Any]]] = None,
        benchmark: Optional[pd.Series] = None,
    ) -> PerformanceMetrics:
        """
        Calculate comprehensive performance metrics.

        Args:
            equity_curve: Time series of portfolio values
            trades: List of trade records
            benchmark: Optional benchmark returns series

        Returns:
            PerformanceMetrics object
        """
        if len(equity_curve) < 2:
            raise PerformanceError("Equity curve must have at least 2 data points")

        metrics = PerformanceMetrics()

        # Basic info
        metrics.start_date = equity_curve.index[0]
        metrics.end_date = equity_curve.index[-1]
        metrics.initial_capital = float(equity_curve.iloc[0])
        metrics.final_capital = float(equity_curve.iloc[-1])

        # Calculate returns
        returns = equity_curve.pct_change().dropna()

        # Total and annualized return
        metrics.total_return = (
            metrics.final_capital - metrics.initial_capital
        ) / metrics.initial_capital

        days = (metrics.end_date - metrics.start_date).days
        years = days / 365.25
        if years > 0:
            metrics.annualized_return = (1 + metrics.total_return) ** (1 / years) - 1

        # Volatility
        if len(returns) > 0:
            metrics.volatility = float(
                returns.std() * np.sqrt(self.trading_days_per_year)
            )

        # Sharpe ratio
        if metrics.volatility > 0:
            excess_return = metrics.annualized_return - self.risk_free_rate
            metrics.sharpe_ratio = excess_return / metrics.volatility

        # Sortino ratio
        downside_returns = returns[returns < 0]
        if len(downside_returns) > 0:
            downside_std = float(
                downside_returns.std() * np.sqrt(self.trading_days_per_year)
            )
            if downside_std > 0:
                excess_return = metrics.annualized_return - self.risk_free_rate
                metrics.sortino_ratio = excess_return / downside_std

        # Drawdown analysis
        drawdown_info = self._calculate_drawdowns(equity_curve)
        if drawdown_info:
            max_dd = max(drawdown_info, key=lambda x: abs(x.drawdown))
            metrics.max_drawdown = abs(max_dd.drawdown)
            metrics.max_drawdown_duration = max_dd.duration

        # Calmar ratio
        if metrics.max_drawdown > 0:
            metrics.calmar_ratio = metrics.annualized_return / metrics.max_drawdown

        # Trade statistics
        if trades:
            self._calculate_trade_stats(trades, metrics)

        # Exposure time
        if trades:
            metrics.exposure_time = self._calculate_exposure_time(
                trades, metrics.start_date, metrics.end_date
            )

        # Benchmark comparison
        if benchmark is not None:
            self._calculate_benchmark_metrics(returns, benchmark, metrics)

        return metrics

    def _calculate_drawdowns(self, equity_curve: pd.Series) -> List[DrawdownInfo]:
        """Calculate all drawdown periods."""
        drawdowns = []
        peak = equity_curve.iloc[0]
        peak_date = equity_curve.index[0]
        in_drawdown = False
        dd_start = None
        trough = None
        trough_date = None

        for date, value in equity_curve.items():
            if value >= peak:
                if in_drawdown:
                    # Recovered from drawdown
                    dd = DrawdownInfo(
                        start_date=dd_start,
                        end_date=trough_date,
                        recovery_date=date,
                        peak_value=peak,
                        trough_value=trough,
                        drawdown=(trough - peak) / peak,
                        duration=(trough_date - dd_start).days,
                        recovery_duration=(date - trough_date).days,
                    )
                    drawdowns.append(dd)
                    in_drawdown = False

                peak = value
                peak_date = date
            else:
                if not in_drawdown:
                    in_drawdown = True
                    dd_start = peak_date
                    trough = value
                    trough_date = date
                elif value < trough:
                    trough = value
                    trough_date = date

        # Handle ongoing drawdown
        if in_drawdown:
            dd = DrawdownInfo(
                start_date=dd_start,
                end_date=trough_date,
                recovery_date=None,
                peak_value=peak,
                trough_value=trough,
                drawdown=(trough - peak) / peak,
                duration=(trough_date - dd_start).days,
                recovery_duration=None,
            )
            drawdowns.append(dd)

        return drawdowns

    def _calculate_trade_stats(
        self, trades: List[Dict[str, Any]], metrics: PerformanceMetrics
    ) -> None:
        """Calculate trade-level statistics."""
        if not trades:
            return

        metrics.num_trades = len(trades)

        pnls = [t.get("pnl", 0) for t in trades]
        returns = [t.get("return", 0) for t in trades]

        winning_trades = [r for r in returns if r > 0]
        losing_trades = [r for r in returns if r < 0]

        metrics.num_winning_trades = len(winning_trades)
        metrics.num_losing_trades = len(losing_trades)

        if metrics.num_trades > 0:
            metrics.win_rate = metrics.num_winning_trades / metrics.num_trades

        if winning_trades:
            metrics.avg_win = np.mean(winning_trades)
            metrics.best_trade = max(winning_trades)

        if losing_trades:
            metrics.avg_loss = np.mean(losing_trades)
            metrics.worst_trade = min(losing_trades)

        # Profit factor
        gross_profit = sum(p for p in pnls if p > 0)
        gross_loss = abs(sum(p for p in pnls if p < 0))
        if gross_loss > 0:
            metrics.profit_factor = gross_profit / gross_loss

        # Average trade duration
        durations = []
        for t in trades:
            if "entry_time" in t and "exit_time" in t:
                duration = (t["exit_time"] - t["entry_time"]).days
                durations.append(duration)

        if durations:
            metrics.avg_trade_duration = np.mean(durations)

    def _calculate_exposure_time(
        self,
        trades: List[Dict[str, Any]],
        start_date: datetime,
        end_date: datetime,
    ) -> float:
        """Calculate percentage of time in market."""
        total_days = (end_date - start_date).days
        if total_days <= 0:
            return 0.0

        # Simple approximation: sum of trade durations
        exposure_days = 0
        for t in trades:
            if "entry_time" in t and "exit_time" in t:
                duration = (t["exit_time"] - t["entry_time"]).days
                exposure_days += max(1, duration)

        return min(1.0, exposure_days / total_days)

    def _calculate_benchmark_metrics(
        self,
        returns: pd.Series,
        benchmark: pd.Series,
        metrics: PerformanceMetrics,
    ) -> None:
        """Calculate benchmark comparison metrics."""
        # Align returns
        aligned = pd.concat([returns, benchmark], axis=1, join="inner")
        if len(aligned) < 2:
            return

        strategy_returns = aligned.iloc[:, 0]
        benchmark_returns = aligned.iloc[:, 1]

        # Benchmark total return
        metrics.benchmark_return = (1 + benchmark_returns).prod() - 1

        # Beta
        covariance = strategy_returns.cov(benchmark_returns)
        benchmark_variance = benchmark_returns.var()
        if benchmark_variance > 0:
            metrics.beta = covariance / benchmark_variance

            # Alpha (Jensen's alpha)
            annualized_strategy = (1 + strategy_returns.mean()) ** self.trading_days_per_year - 1
            annualized_benchmark = (1 + benchmark_returns.mean()) ** self.trading_days_per_year - 1
            metrics.alpha = annualized_strategy - (
                self.risk_free_rate + metrics.beta * (annualized_benchmark - self.risk_free_rate)
            )

        # Information ratio
        excess_returns = strategy_returns - benchmark_returns
        tracking_error = excess_returns.std() * np.sqrt(self.trading_days_per_year)
        if tracking_error > 0:
            annualized_excess = excess_returns.mean() * self.trading_days_per_year
            metrics.information_ratio = annualized_excess / tracking_error

    def calculate_rolling_metrics(
        self,
        equity_curve: pd.Series,
        window: int = 252,
    ) -> pd.DataFrame:
        """
        Calculate rolling performance metrics.

        Args:
            equity_curve: Time series of portfolio values
            window: Rolling window size in trading days

        Returns:
            DataFrame with rolling metrics
        """
        returns = equity_curve.pct_change().dropna()

        rolling = pd.DataFrame(index=returns.index)

        # Rolling return
        rolling["return"] = (1 + returns).rolling(window).apply(
            lambda x: x.prod() - 1, raw=True
        )

        # Rolling volatility
        rolling["volatility"] = returns.rolling(window).std() * np.sqrt(
            self.trading_days_per_year
        )

        # Rolling Sharpe
        rolling["sharpe"] = (
            rolling["return"] - self.risk_free_rate
        ) / rolling["volatility"]

        # Rolling max drawdown
        def calc_max_dd(x):
            cumret = (1 + x).cumprod()
            peak = cumret.expanding().max()
            dd = (cumret - peak) / peak
            return dd.min()

        rolling["max_drawdown"] = returns.rolling(window).apply(calc_max_dd, raw=False)

        return rolling


def calculate_var(
    returns: pd.Series, confidence_level: float = 0.95, method: str = "historical"
) -> float:
    """
    Calculate Value at Risk (VaR).

    Args:
        returns: Returns series
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        method: VaR method ('historical', 'parametric')

    Returns:
        VaR value (positive number representing potential loss)
    """
    if method == "historical":
        return -float(np.percentile(returns, (1 - confidence_level) * 100))
    elif method == "parametric":
        from scipy import stats
        z_score = stats.norm.ppf(1 - confidence_level)
        return -(returns.mean() + z_score * returns.std())
    else:
        raise ValueError(f"Unknown VaR method: {method}")


def calculate_cvar(returns: pd.Series, confidence_level: float = 0.95) -> float:
    """
    Calculate Conditional Value at Risk (CVaR / Expected Shortfall).

    Args:
        returns: Returns series
        confidence_level: Confidence level (e.g., 0.95 for 95%)

    Returns:
        CVaR value (positive number representing expected loss beyond VaR)
    """
    var = calculate_var(returns, confidence_level, method="historical")
    tail_returns = returns[returns <= -var]
    if len(tail_returns) == 0:
        return var
    return -float(tail_returns.mean())

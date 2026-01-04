"""
Performance Tracker

Real-time performance monitoring and metrics calculation.
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import numpy as np


@dataclass
class PerformanceMetrics:
    """Snapshot of performance metrics."""

    timestamp: datetime
    total_pnl: float
    daily_pnl: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    current_drawdown: float
    win_rate: float
    profit_factor: float
    avg_trade_pnl: float
    trade_count: int
    exposure: float


class PerformanceTracker:
    """
    Real-time performance tracking.

    Tracks:
    - P&L (gross/net, realized/unrealized)
    - Risk-adjusted metrics (Sharpe, Sortino, Calmar)
    - Drawdown (current and max)
    - Trade statistics
    - Per-model performance

    Parameters:
        initial_capital: Starting capital
        risk_free_rate: Annual risk-free rate for Sharpe
    """

    def __init__(self, initial_capital: float = 100000.0, risk_free_rate: float = 0.04):
        self.initial_capital = initial_capital
        self.risk_free_rate = risk_free_rate

        # P&L tracking
        self.daily_returns: List[float] = []
        self.nav_history: List[float] = [initial_capital]
        self.trade_pnls: List[float] = []

        # Drawdown tracking
        self.peak_nav = initial_capital
        self.max_drawdown = 0.0

        # Per-model tracking
        self.model_pnls: Dict[str, List[float]] = {}
        self.model_trades: Dict[str, int] = {}

        # Daily tracking
        self.today_pnl = 0.0
        self.today_trades = 0

    @property
    def current_nav(self) -> float:
        """Current NAV."""
        return self.nav_history[-1] if self.nav_history else self.initial_capital

    @property
    def total_return(self) -> float:
        """Total return since inception."""
        return (self.current_nav / self.initial_capital) - 1

    @property
    def current_drawdown(self) -> float:
        """Current drawdown from peak."""
        if self.peak_nav == 0:
            return 0.0
        return (self.peak_nav - self.current_nav) / self.peak_nav

    def record_nav(self, nav: float):
        """
        Record NAV update.

        Args:
            nav: Current NAV
        """
        if self.nav_history:
            daily_return = (nav / self.nav_history[-1]) - 1
            self.daily_returns.append(daily_return)

        self.nav_history.append(nav)

        # Update peak and drawdown
        if nav > self.peak_nav:
            self.peak_nav = nav

        dd = self.current_drawdown
        if dd > self.max_drawdown:
            self.max_drawdown = dd

    def record_trade(self, pnl: float, model_name: Optional[str] = None):
        """
        Record a completed trade.

        Args:
            pnl: Trade P&L
            model_name: Name of model that generated signal
        """
        self.trade_pnls.append(pnl)
        self.today_pnl += pnl
        self.today_trades += 1

        if model_name:
            if model_name not in self.model_pnls:
                self.model_pnls[model_name] = []
                self.model_trades[model_name] = 0

            self.model_pnls[model_name].append(pnl)
            self.model_trades[model_name] += 1

    def end_of_day(self):
        """Process end of day."""
        self.today_pnl = 0.0
        self.today_trades = 0

    def calculate_sharpe(self, returns: Optional[List[float]] = None, annualize: bool = True) -> float:
        """
        Calculate Sharpe ratio.

        Sharpe = (μ - rf) / σ

        Args:
            returns: Return series (uses daily_returns if None)
            annualize: Whether to annualize

        Returns:
            Sharpe ratio
        """
        returns = returns or self.daily_returns

        if len(returns) < 2:
            return 0.0

        mean_return = np.mean(returns)
        std_return = np.std(returns, ddof=1)

        if std_return < 1e-8:
            return 0.0 if mean_return <= 0 else 10.0

        daily_rf = self.risk_free_rate / 252
        sharpe = (mean_return - daily_rf) / std_return

        if annualize:
            sharpe *= np.sqrt(252)

        return sharpe

    def calculate_sortino(self, returns: Optional[List[float]] = None, annualize: bool = True) -> float:
        """
        Calculate Sortino ratio.

        Sortino = (μ - rf) / σ_downside

        Uses only negative returns for denominator.

        Args:
            returns: Return series
            annualize: Whether to annualize

        Returns:
            Sortino ratio
        """
        returns = returns or self.daily_returns

        if len(returns) < 2:
            return 0.0

        mean_return = np.mean(returns)
        daily_rf = self.risk_free_rate / 252

        # Downside deviation
        downside_returns = [r for r in returns if r < 0]

        if len(downside_returns) < 2:
            return self.calculate_sharpe(returns, annualize)

        downside_std = np.std(downside_returns, ddof=1)

        if downside_std < 1e-8:
            return 10.0 if mean_return > daily_rf else 0.0

        sortino = (mean_return - daily_rf) / downside_std

        if annualize:
            sortino *= np.sqrt(252)

        return sortino

    def calculate_calmar(self, lookback_days: int = 252) -> float:
        """
        Calculate Calmar ratio.

        Calmar = Annual Return / Max Drawdown

        Args:
            lookback_days: Days for calculation

        Returns:
            Calmar ratio
        """
        if self.max_drawdown < 1e-8:
            return 0.0

        if len(self.daily_returns) < lookback_days:
            return 0.0

        recent_returns = self.daily_returns[-lookback_days:]
        annual_return = np.prod(1 + np.array(recent_returns)) ** (252 / len(recent_returns)) - 1

        return annual_return / self.max_drawdown

    def calculate_win_rate(self, trades: Optional[List[float]] = None) -> float:
        """
        Calculate trade win rate.

        Args:
            trades: Trade P&L list

        Returns:
            Win rate (0-1)
        """
        trades = trades or self.trade_pnls

        if not trades:
            return 0.0

        wins = sum(1 for t in trades if t > 0)
        return wins / len(trades)

    def calculate_profit_factor(self, trades: Optional[List[float]] = None) -> float:
        """
        Calculate profit factor.

        Profit Factor = Gross Profit / Gross Loss

        Args:
            trades: Trade P&L list

        Returns:
            Profit factor
        """
        trades = trades or self.trade_pnls

        if not trades:
            return 0.0

        gross_profit = sum(t for t in trades if t > 0)
        gross_loss = abs(sum(t for t in trades if t < 0))

        if gross_loss < 1e-8:
            return 10.0 if gross_profit > 0 else 0.0

        return gross_profit / gross_loss

    def get_metrics(self) -> PerformanceMetrics:
        """
        Get current performance metrics snapshot.

        Returns:
            PerformanceMetrics dataclass
        """
        return PerformanceMetrics(
            timestamp=datetime.now(),
            total_pnl=self.current_nav - self.initial_capital,
            daily_pnl=self.today_pnl,
            sharpe_ratio=self.calculate_sharpe(),
            sortino_ratio=self.calculate_sortino(),
            max_drawdown=self.max_drawdown,
            current_drawdown=self.current_drawdown,
            win_rate=self.calculate_win_rate(),
            profit_factor=self.calculate_profit_factor(),
            avg_trade_pnl=np.mean(self.trade_pnls) if self.trade_pnls else 0.0,
            trade_count=len(self.trade_pnls),
            exposure=0.0,  # Would need portfolio data
        )

    def get_model_performance(self) -> Dict[str, Dict]:
        """
        Get per-model performance breakdown.

        Returns:
            Dictionary of model -> performance metrics
        """
        result = {}

        for model, pnls in self.model_pnls.items():
            if not pnls:
                continue

            wins = sum(1 for p in pnls if p > 0)

            result[model] = {
                "total_pnl": sum(pnls),
                "avg_pnl": np.mean(pnls),
                "trade_count": len(pnls),
                "win_rate": wins / len(pnls),
                "profit_factor": self.calculate_profit_factor(pnls),
                "sharpe": self._calculate_trade_sharpe(pnls),
            }

        return result

    def _calculate_trade_sharpe(self, pnls: List[float]) -> float:
        """Calculate Sharpe from trade P&Ls."""
        if len(pnls) < 2:
            return 0.0

        mean_pnl = np.mean(pnls)
        std_pnl = np.std(pnls, ddof=1)

        if std_pnl < 1e-8:
            return 0.0

        # Assume ~2 trades per day on average
        return (mean_pnl / std_pnl) * np.sqrt(252 * 2)

"""
Portfolio Manager

Tracks open positions, calculates portfolio metrics,
and manages position-level operations.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
import numpy as np

from ..core import TradeOrder, OrderSide


@dataclass
class Position:
    """Individual position tracking."""

    symbol: str
    quantity: float
    avg_entry_price: float
    current_price: float
    side: OrderSide
    opened_at: datetime = field(default_factory=datetime.now)
    realized_pnl: float = 0.0

    @property
    def market_value(self) -> float:
        """Current market value."""
        return abs(self.quantity) * self.current_price

    @property
    def unrealized_pnl(self) -> float:
        """Unrealized P&L."""
        if self.side == OrderSide.BUY:
            return self.quantity * (self.current_price - self.avg_entry_price)
        else:
            return self.quantity * (self.avg_entry_price - self.current_price)

    @property
    def pnl_pct(self) -> float:
        """P&L as percentage of entry value."""
        entry_value = abs(self.quantity) * self.avg_entry_price
        if entry_value == 0:
            return 0.0
        return self.unrealized_pnl / entry_value


class PortfolioManager:
    """
    Manages portfolio positions and calculates metrics.

    Features:
    - Position tracking and updates
    - P&L calculation (realized and unrealized)
    - Exposure calculations
    - Portfolio statistics
    """

    def __init__(self, initial_capital: float = 100000.0):
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions: Dict[str, Position] = {}
        self.trade_history: List[Dict] = []
        self.daily_pnl_history: List[float] = []

    @property
    def nav(self) -> float:
        """Net Asset Value = Cash + Market Value of Positions."""
        positions_value = sum(p.market_value for p in self.positions.values())
        return self.cash + positions_value

    @property
    def total_exposure(self) -> float:
        """Total exposure as fraction of NAV."""
        if self.nav == 0:
            return 0.0
        total = sum(p.market_value for p in self.positions.values())
        return total / self.nav

    @property
    def net_exposure(self) -> float:
        """Net long-short exposure as fraction of NAV."""
        if self.nav == 0:
            return 0.0

        long_value = sum(p.market_value for p in self.positions.values() if p.side == OrderSide.BUY)
        short_value = sum(p.market_value for p in self.positions.values() if p.side == OrderSide.SELL)

        return (long_value - short_value) / self.nav

    @property
    def total_unrealized_pnl(self) -> float:
        """Total unrealized P&L across all positions."""
        return sum(p.unrealized_pnl for p in self.positions.values())

    def update_price(self, symbol: str, price: float):
        """
        Update current price for a position.

        Args:
            symbol: Trading symbol
            price: Current price
        """
        if symbol in self.positions:
            self.positions[symbol].current_price = price

    def open_position(self, symbol: str, quantity: float, price: float, side: OrderSide):
        """
        Open a new position or add to existing.

        Args:
            symbol: Trading symbol
            quantity: Number of units
            price: Entry price
            side: Buy or sell
        """
        cost = quantity * price

        if symbol in self.positions:
            # Add to existing position
            pos = self.positions[symbol]

            if pos.side == side:
                # Same direction - average in
                total_qty = pos.quantity + quantity
                total_cost = pos.quantity * pos.avg_entry_price + quantity * price
                pos.avg_entry_price = total_cost / total_qty
                pos.quantity = total_qty
            else:
                # Opposite direction - reduce position
                if quantity >= pos.quantity:
                    # Close position and potentially reverse
                    realized = pos.quantity * (price - pos.avg_entry_price)
                    if pos.side == OrderSide.SELL:
                        realized = -realized
                    pos.realized_pnl += realized
                    self.cash += realized

                    remaining = quantity - pos.quantity
                    if remaining > 0:
                        # Reverse position
                        pos.quantity = remaining
                        pos.avg_entry_price = price
                        pos.side = side
                    else:
                        # Position closed
                        del self.positions[symbol]
                else:
                    # Partial close
                    realized = quantity * (price - pos.avg_entry_price)
                    if pos.side == OrderSide.SELL:
                        realized = -realized
                    pos.realized_pnl += realized
                    self.cash += realized
                    pos.quantity -= quantity
        else:
            # New position
            self.positions[symbol] = Position(
                symbol=symbol, quantity=quantity, avg_entry_price=price, current_price=price, side=side
            )

        # Adjust cash
        if side == OrderSide.BUY:
            self.cash -= cost
        else:
            self.cash += cost

        # Record trade
        self.trade_history.append(
            {
                "timestamp": datetime.now(),
                "symbol": symbol,
                "side": side.value,
                "quantity": quantity,
                "price": price,
                "value": cost,
            }
        )

    def close_position(self, symbol: str, price: float) -> float:
        """
        Close entire position.

        Args:
            symbol: Trading symbol
            price: Close price

        Returns:
            Realized P&L
        """
        if symbol not in self.positions:
            return 0.0

        pos = self.positions[symbol]

        # Calculate P&L
        if pos.side == OrderSide.BUY:
            realized = pos.quantity * (price - pos.avg_entry_price)
            self.cash += pos.quantity * price
        else:
            realized = pos.quantity * (pos.avg_entry_price - price)
            self.cash -= pos.quantity * price

        # Record trade
        self.trade_history.append(
            {
                "timestamp": datetime.now(),
                "symbol": symbol,
                "side": "close",
                "quantity": pos.quantity,
                "price": price,
                "realized_pnl": realized,
            }
        )

        # Remove position
        del self.positions[symbol]

        return realized

    def get_position(self, symbol: str) -> Optional[Position]:
        """Get position for symbol."""
        return self.positions.get(symbol)

    def get_portfolio_stats(self) -> Dict:
        """
        Calculate portfolio statistics.

        Returns:
            Dictionary of portfolio metrics
        """
        # Position counts
        long_count = sum(1 for p in self.positions.values() if p.side == OrderSide.BUY)
        short_count = sum(1 for p in self.positions.values() if p.side == OrderSide.SELL)

        # P&L stats
        total_realized = sum(p.realized_pnl for p in self.positions.values())

        # Daily returns (if history available)
        if len(self.daily_pnl_history) > 1:
            returns = np.array(self.daily_pnl_history)
            sharpe = np.mean(returns) / (np.std(returns) + 1e-8) * np.sqrt(252)
            max_dd = self._calculate_max_drawdown(returns)
        else:
            sharpe = 0.0
            max_dd = 0.0

        return {
            "nav": self.nav,
            "cash": self.cash,
            "positions_value": self.nav - self.cash,
            "total_exposure": f"{self.total_exposure:.2%}",
            "net_exposure": f"{self.net_exposure:.2%}",
            "long_positions": long_count,
            "short_positions": short_count,
            "total_unrealized_pnl": self.total_unrealized_pnl,
            "total_realized_pnl": total_realized,
            "total_pnl": self.total_unrealized_pnl + total_realized,
            "return_pct": f"{(self.nav / self.initial_capital - 1):.2%}",
            "sharpe_ratio": sharpe,
            "max_drawdown": f"{max_dd:.2%}",
            "trade_count": len(self.trade_history),
        }

    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown from returns series."""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdowns = (running_max - cumulative) / running_max
        return np.max(drawdowns)

    def record_daily_pnl(self):
        """Record end of day P&L for statistics."""
        if self.daily_pnl_history:
            prev_nav = self.daily_pnl_history[-1]
            daily_return = (self.nav - prev_nav) / prev_nav if prev_nav > 0 else 0
        else:
            daily_return = (self.nav / self.initial_capital) - 1

        self.daily_pnl_history.append(self.nav)

    def get_positions_summary(self) -> List[Dict]:
        """Get summary of all positions."""
        return [
            {
                "symbol": pos.symbol,
                "side": pos.side.value,
                "quantity": pos.quantity,
                "avg_entry": pos.avg_entry_price,
                "current_price": pos.current_price,
                "market_value": pos.market_value,
                "unrealized_pnl": pos.unrealized_pnl,
                "pnl_pct": f"{pos.pnl_pct:.2%}",
                "weight": pos.market_value / self.nav if self.nav > 0 else 0,
            }
            for pos in self.positions.values()
        ]

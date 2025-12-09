"""
AI Trading System - Living Lab Architecture

A self-learning, volatility-aware trading system with:
- Multi-horizon alpha models
- Risk-aware position sizing
- Regime detection and adaptation
- Continuous learning loop
"""

from .core import (
    MarketRegime,
    AlphaSignal,
    PositionSize,
    RiskCheckResult,
    TradeOrder,
    OrderType,
    OrderSide,
)

__version__ = "1.0.0"

__all__ = [
    "MarketRegime",
    "AlphaSignal",
    "PositionSize",
    "RiskCheckResult",
    "TradeOrder",
    "OrderType",
    "OrderSide",
]

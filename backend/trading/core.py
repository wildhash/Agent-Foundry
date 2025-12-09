"""
Core data types and interfaces for the trading system.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import numpy as np


class MarketRegime(Enum):
    """Market regime classifications."""
    TRENDING_UP = "trending_up"
    TRENDING_DOWN = "trending_down"
    MEAN_REVERTING = "mean_reverting"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    CRISIS = "crisis"
    NORMAL = "normal"


class OrderType(Enum):
    """Order types for execution."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"
    TWAP = "twap"
    VWAP = "vwap"


class OrderSide(Enum):
    """Order side."""
    BUY = "buy"
    SELL = "sell"


@dataclass
class AlphaSignal:
    """
    Alpha signal from a model.

    Attributes:
        value: Signal strength in [-1, +1] range
        confidence: Confidence level in [0, 1] range
        regime_filter: Active regime filter (if any)
        components: Breakdown of signal components
        model_name: Name of the generating model
        timestamp: Signal generation time
    """
    value: float
    confidence: float
    regime_filter: str
    components: Dict[str, Any] = field(default_factory=dict)
    model_name: str = ""
    timestamp: datetime = field(default_factory=datetime.now)

    def __post_init__(self):
        # Validate ranges
        self.value = np.clip(self.value, -1.0, 1.0)
        self.confidence = np.clip(self.confidence, 0.0, 1.0)

    @property
    def is_active(self) -> bool:
        """Check if signal is active (non-zero with confidence)."""
        return abs(self.value) > 0.01 and self.confidence > 0.1

    @property
    def direction(self) -> str:
        """Get signal direction."""
        if self.value > 0.01:
            return "LONG"
        elif self.value < -0.01:
            return "SHORT"
        return "NEUTRAL"


@dataclass
class PositionSize:
    """
    Calculated position size with metadata.

    Attributes:
        percent_of_nav: Position as percentage of NAV
        dollar_amount: Position in dollar terms
        num_units: Number of units/contracts
        vol_scalar: Volatility scaling factor applied
        raw_signal: Original signal strength
        capped: Whether position was capped by limits
    """
    percent_of_nav: float
    dollar_amount: float
    num_units: float = 0.0
    vol_scalar: float = 1.0
    raw_signal: float = 0.0
    capped: bool = False

    def scale(self, factor: float) -> "PositionSize":
        """Return a scaled copy of this position."""
        return PositionSize(
            percent_of_nav=self.percent_of_nav * factor,
            dollar_amount=self.dollar_amount * factor,
            num_units=self.num_units * factor,
            vol_scalar=self.vol_scalar,
            raw_signal=self.raw_signal,
            capped=self.capped or factor < 1.0
        )


@dataclass
class RiskCheckResult:
    """
    Result of risk limit checks.

    Attributes:
        approved: Whether the trade is approved
        violations: List of violated limits
        adjusted_position: Position after risk adjustments
        risk_score: Overall risk score [0, 1]
    """
    approved: bool
    violations: List[str] = field(default_factory=list)
    adjusted_position: Optional[PositionSize] = None
    risk_score: float = 0.0

    @property
    def has_violations(self) -> bool:
        return len(self.violations) > 0


@dataclass
class TradeOrder:
    """
    Trade order to be executed.

    Attributes:
        symbol: Trading symbol
        side: Buy or sell
        order_type: Type of order
        quantity: Order quantity
        limit_price: Limit price (if applicable)
        stop_price: Stop price (if applicable)
        time_in_force: Order time in force
        client_order_id: Client-side order ID
        metadata: Additional order metadata
    """
    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    time_in_force: str = "GTC"
    client_order_id: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.client_order_id:
            self.client_order_id = f"ord_{datetime.now().strftime('%Y%m%d%H%M%S%f')}"


@dataclass
class MarketData:
    """
    Market data snapshot.

    Attributes:
        symbol: Trading symbol
        timestamp: Data timestamp
        open: Open price
        high: High price
        low: Low price
        close: Close price
        volume: Trading volume
        bid: Best bid price
        ask: Best ask price
        bid_size: Bid size
        ask_size: Ask size
    """
    symbol: str
    timestamp: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float
    bid: float = 0.0
    ask: float = 0.0
    bid_size: float = 0.0
    ask_size: float = 0.0

    @property
    def mid_price(self) -> float:
        """Calculate mid price."""
        if self.bid > 0 and self.ask > 0:
            return (self.bid + self.ask) / 2
        return self.close

    @property
    def spread(self) -> float:
        """Calculate bid-ask spread."""
        if self.bid > 0 and self.ask > 0:
            return self.ask - self.bid
        return 0.0

    @property
    def spread_bps(self) -> float:
        """Calculate spread in basis points."""
        if self.mid_price > 0:
            return (self.spread / self.mid_price) * 10000
        return 0.0


@dataclass
class FeatureSet:
    """
    Calculated features for a symbol at a point in time.

    Attributes:
        symbol: Trading symbol
        timestamp: Feature calculation time
        features: Dictionary of feature name -> value
    """
    symbol: str
    timestamp: datetime
    features: Dict[str, float] = field(default_factory=dict)

    def get(self, name: str, default: float = 0.0) -> float:
        """Get feature value with default."""
        return self.features.get(name, default)

    def __getitem__(self, key: str) -> float:
        return self.features[key]

    def __contains__(self, key: str) -> bool:
        return key in self.features


@dataclass
class DecisionLog:
    """
    Log entry for a trading decision (for learning and audit).

    Attributes:
        timestamp: Decision time
        symbol: Trading symbol
        features: Features at decision time
        signals: Alpha signals from each model
        regime: Detected market regime
        position_before: Position before trade
        position_after: Position after trade
        order: Generated order (if any)
        model_version: Version of models used
    """
    timestamp: datetime
    symbol: str
    features: Dict[str, float]
    signals: Dict[str, AlphaSignal]
    regime: MarketRegime
    position_before: float
    position_after: float
    order: Optional[TradeOrder]
    model_version: str = "1.0.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "timestamp": self.timestamp.isoformat(),
            "symbol": self.symbol,
            "features": self.features,
            "signals": {
                name: {
                    "value": sig.value,
                    "confidence": sig.confidence,
                    "direction": sig.direction
                }
                for name, sig in self.signals.items()
            },
            "regime": self.regime.value,
            "position_before": self.position_before,
            "position_after": self.position_after,
            "order": self.order.client_order_id if self.order else None,
            "model_version": self.model_version
        }

"""
Execution Engine

Central execution management with order lifecycle handling.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Callable
import logging
import asyncio

from ..core import TradeOrder, OrderType, OrderSide, PositionSize, MarketRegime
from .algorithms import TWAPAlgorithm, VWAPAlgorithm, ChildOrder
from .slippage import SlippageModel, SlippageEstimate

logger = logging.getLogger(__name__)


class OrderStatus(Enum):
    """Order lifecycle status."""
    PENDING = "pending"
    SUBMITTED = "submitted"
    PARTIAL = "partial"
    FILLED = "filled"
    CANCELLED = "cancelled"
    REJECTED = "rejected"


@dataclass
class OrderState:
    """Tracks state of an order."""
    order: TradeOrder
    status: OrderStatus
    submitted_at: Optional[datetime] = None
    filled_quantity: float = 0.0
    avg_fill_price: float = 0.0
    fills: List[Dict] = field(default_factory=list)
    child_orders: List[ChildOrder] = field(default_factory=list)
    slippage_estimate: Optional[SlippageEstimate] = None
    actual_slippage_bps: float = 0.0


class ExecutionEngine:
    """
    Central execution engine.
    
    Responsibilities:
    - Convert position targets to orders
    - Execute using appropriate algorithm
    - Track fills and calculate slippage
    - Adapt execution style to market conditions
    
    Parameters:
        default_algorithm: Default execution algorithm
        slippage_model: Slippage estimation model
    """
    
    def __init__(
        self,
        default_algorithm: str = "twap",
        max_order_value: float = 100000.0,
        min_order_value: float = 100.0
    ):
        self.default_algorithm = default_algorithm
        self.max_order_value = max_order_value
        self.min_order_value = min_order_value
        
        self.slippage_model = SlippageModel()
        self.twap = TWAPAlgorithm()
        self.vwap = VWAPAlgorithm()
        
        # Order tracking
        self.orders: Dict[str, OrderState] = {}
        self.completed_orders: List[OrderState] = []
        
        # Callbacks
        self._on_fill: Optional[Callable] = None
        self._on_complete: Optional[Callable] = None
    
    def create_order(
        self,
        symbol: str,
        target: PositionSize,
        current_position: float,
        current_price: float,
        regime: MarketRegime = MarketRegime.NORMAL
    ) -> Optional[TradeOrder]:
        """
        Create order from position target.
        
        Args:
            symbol: Trading symbol
            target: Target position size
            current_position: Current position quantity
            current_price: Current market price
            regime: Market regime for algorithm selection
            
        Returns:
            TradeOrder or None if no trade needed
        """
        # Calculate required trade
        target_quantity = target.num_units
        trade_quantity = target_quantity - current_position
        
        # Check if trade is significant
        trade_value = abs(trade_quantity * current_price)
        
        if trade_value < self.min_order_value:
            return None
        
        if trade_value > self.max_order_value:
            trade_quantity = (
                self.max_order_value / current_price * 
                np.sign(trade_quantity)
            )
        
        # Determine side
        side = OrderSide.BUY if trade_quantity > 0 else OrderSide.SELL
        
        # Select order type based on regime
        order_type = self._select_order_type(regime, trade_value)
        
        return TradeOrder(
            symbol=symbol,
            side=side,
            order_type=order_type,
            quantity=abs(trade_quantity),
            metadata={
                "target_position": target.percent_of_nav,
                "regime": regime.value,
                "signal_strength": target.raw_signal
            }
        )
    
    def _select_order_type(
        self,
        regime: MarketRegime,
        order_value: float
    ) -> OrderType:
        """
        Select order type based on conditions.
        
        Args:
            regime: Market regime
            order_value: Order value
            
        Returns:
            Appropriate order type
        """
        # Large orders in normal/low vol: use TWAP/VWAP
        if order_value > 10000:
            if regime in [MarketRegime.NORMAL, MarketRegime.LOW_VOLATILITY]:
                return OrderType.VWAP if self.default_algorithm == "vwap" else OrderType.TWAP
        
        # High volatility: use limit orders
        if regime == MarketRegime.HIGH_VOLATILITY:
            return OrderType.LIMIT
        
        # Default to market for smaller orders
        return OrderType.MARKET
    
    async def submit(
        self,
        order: TradeOrder,
        mid_price: float,
        daily_volume: float = 1000000.0,
        volatility: float = 0.20,
        spread_bps: float = 10.0
    ) -> str:
        """
        Submit order for execution.
        
        Args:
            order: Order to execute
            mid_price: Current mid price
            daily_volume: Daily dollar volume
            volatility: Current volatility
            spread_bps: Current spread in bps
            
        Returns:
            Order ID
        """
        # Estimate slippage
        order_value = order.quantity * mid_price
        estimate = self.slippage_model.estimate(
            order_size=order_value,
            daily_volume=daily_volume,
            volatility=volatility,
            spread_bps=spread_bps,
            is_buy=order.side == OrderSide.BUY
        )
        
        # Create order state
        state = OrderState(
            order=order,
            status=OrderStatus.SUBMITTED,
            submitted_at=datetime.now(),
            slippage_estimate=estimate
        )
        
        # Generate execution schedule for algo orders
        if order.order_type in [OrderType.TWAP, OrderType.VWAP]:
            algo = self.twap if order.order_type == OrderType.TWAP else self.vwap
            state.child_orders = algo.generate_schedule(
                total_quantity=order.quantity,
                limit_price=order.limit_price
            )
        
        self.orders[order.client_order_id] = state
        
        logger.info(
            f"Order submitted: {order.client_order_id} "
            f"{order.side.value} {order.quantity:.2f} {order.symbol} "
            f"est_slippage={estimate.total_cost_bps:.1f}bps"
        )
        
        return order.client_order_id
    
    def record_fill(
        self,
        order_id: str,
        fill_quantity: float,
        fill_price: float,
        timestamp: Optional[datetime] = None
    ):
        """
        Record a fill for an order.
        
        Args:
            order_id: Order ID
            fill_quantity: Filled quantity
            fill_price: Fill price
            timestamp: Fill timestamp
        """
        if order_id not in self.orders:
            logger.warning(f"Unknown order ID: {order_id}")
            return
        
        state = self.orders[order_id]
        
        # Update fill tracking
        old_filled = state.filled_quantity
        state.filled_quantity += fill_quantity
        
        # Update average price
        if state.filled_quantity > 0:
            state.avg_fill_price = (
                (old_filled * state.avg_fill_price + fill_quantity * fill_price) /
                state.filled_quantity
            )
        
        # Record fill
        state.fills.append({
            "quantity": fill_quantity,
            "price": fill_price,
            "timestamp": timestamp or datetime.now()
        })
        
        # Update status
        if state.filled_quantity >= state.order.quantity:
            state.status = OrderStatus.FILLED
            self._on_order_complete(state)
        else:
            state.status = OrderStatus.PARTIAL
        
        # Callback
        if self._on_fill:
            self._on_fill(order_id, fill_quantity, fill_price)
    
    def _on_order_complete(self, state: OrderState):
        """Handle order completion."""
        order = state.order
        
        # Calculate actual slippage
        # (Compare avg fill to mid price at submission)
        # Note: In production, track the mid price at submission
        if state.slippage_estimate:
            predicted = state.slippage_estimate.total_cost_bps
            # Actual slippage would need the reference price
            # This is a placeholder
            state.actual_slippage_bps = predicted * 1.1  # Assume 10% worse
            
            # Record for model calibration
            self.slippage_model.record_execution(
                predicted, state.actual_slippage_bps
            )
        
        # Move to completed
        self.completed_orders.append(state)
        del self.orders[order.client_order_id]
        
        logger.info(
            f"Order completed: {order.client_order_id} "
            f"avg_price={state.avg_fill_price:.2f}"
        )
        
        # Callback
        if self._on_complete:
            self._on_complete(order.client_order_id, state)
    
    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order.
        
        Args:
            order_id: Order ID to cancel
            
        Returns:
            True if cancelled successfully
        """
        if order_id not in self.orders:
            return False
        
        state = self.orders[order_id]
        
        if state.status in [OrderStatus.FILLED, OrderStatus.CANCELLED]:
            return False
        
        state.status = OrderStatus.CANCELLED
        self.completed_orders.append(state)
        del self.orders[order_id]
        
        logger.info(f"Order cancelled: {order_id}")
        return True
    
    def get_order_status(self, order_id: str) -> Optional[OrderState]:
        """Get current order state."""
        return self.orders.get(order_id)
    
    def get_execution_style(
        self,
        regime: MarketRegime,
        urgency: float = 0.5
    ) -> Dict:
        """
        Get execution style parameters for current conditions.
        
        Args:
            regime: Market regime
            urgency: How urgent is this trade (0-1)
            
        Returns:
            Dictionary of execution parameters
        """
        styles = {
            MarketRegime.LOW_VOLATILITY: {
                "algorithm": "vwap",
                "duration_minutes": 30,
                "aggression": "passive",
                "use_limit_orders": True
            },
            MarketRegime.NORMAL: {
                "algorithm": "twap",
                "duration_minutes": 60,
                "aggression": "neutral",
                "use_limit_orders": True
            },
            MarketRegime.HIGH_VOLATILITY: {
                "algorithm": "twap",
                "duration_minutes": 90,
                "aggression": "passive",
                "use_limit_orders": True,
                "smaller_slices": True
            },
            MarketRegime.TRENDING_UP: {
                "algorithm": "twap",
                "duration_minutes": 45,
                "aggression": "aggressive" if urgency > 0.7 else "neutral",
                "use_limit_orders": False
            },
            MarketRegime.TRENDING_DOWN: {
                "algorithm": "twap",
                "duration_minutes": 45,
                "aggression": "aggressive" if urgency > 0.7 else "neutral",
                "use_limit_orders": False
            },
            MarketRegime.CRISIS: {
                "algorithm": "twap",
                "duration_minutes": 120,
                "aggression": "very_passive",
                "use_limit_orders": True,
                "smaller_slices": True,
                "pause_on_volatility_spike": True
            },
        }
        
        return styles.get(regime, styles[MarketRegime.NORMAL])
    
    def get_statistics(self) -> Dict:
        """Get execution statistics."""
        if not self.completed_orders:
            return {"status": "no_completed_orders"}
        
        total_orders = len(self.completed_orders)
        filled_orders = [
            o for o in self.completed_orders
            if o.status == OrderStatus.FILLED
        ]
        
        slippages = [
            o.actual_slippage_bps for o in filled_orders
            if o.actual_slippage_bps > 0
        ]
        
        return {
            "total_orders": total_orders,
            "filled_orders": len(filled_orders),
            "fill_rate": len(filled_orders) / total_orders if total_orders > 0 else 0,
            "avg_slippage_bps": sum(slippages) / len(slippages) if slippages else 0,
            "pending_orders": len(self.orders),
            "slippage_model_accuracy": self.slippage_model.get_model_accuracy()
        }


# Add missing import
import numpy as np

"""
Execution Algorithms

TWAP, VWAP, and adaptive execution strategies.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional
import numpy as np

from ..core import TradeOrder, OrderType, OrderSide


@dataclass
class ChildOrder:
    """Child order from slicing algorithm."""

    sequence: int
    quantity: float
    scheduled_time: datetime
    limit_price: Optional[float]
    executed: bool = False
    fill_price: Optional[float] = None
    fill_quantity: float = 0.0


class TWAPAlgorithm:
    """
    Time-Weighted Average Price (TWAP) execution.

    Slices order evenly across time intervals.
    Simple but effective for reducing market impact.

    Parameters:
        duration_minutes: Total execution duration
        num_slices: Number of child orders
        randomize_timing: Add randomness to slice timing
    """

    def __init__(
        self, duration_minutes: int = 60, num_slices: int = 10, randomize_timing: bool = True, randomize_pct: float = 0.2
    ):
        self.duration_minutes = duration_minutes
        self.num_slices = num_slices
        self.randomize_timing = randomize_timing
        self.randomize_pct = randomize_pct

    def generate_schedule(
        self, total_quantity: float, start_time: Optional[datetime] = None, limit_price: Optional[float] = None
    ) -> List[ChildOrder]:
        """
        Generate TWAP execution schedule.

        Args:
            total_quantity: Total quantity to execute
            start_time: Schedule start time
            limit_price: Limit price (optional)

        Returns:
            List of child orders
        """
        if start_time is None:
            start_time = datetime.now()

        # Calculate slice size
        base_slice_size = total_quantity / self.num_slices

        # Time between slices
        interval_seconds = (self.duration_minutes * 60) / self.num_slices

        schedule = []
        remaining_qty = total_quantity

        for i in range(self.num_slices):
            # Calculate time for this slice
            base_time = start_time + timedelta(seconds=i * interval_seconds)

            if self.randomize_timing:
                # Add random offset (±20% of interval)
                offset = np.random.uniform(-self.randomize_pct * interval_seconds, self.randomize_pct * interval_seconds)
                scheduled_time = base_time + timedelta(seconds=offset)
            else:
                scheduled_time = base_time

            # Calculate quantity (last slice gets remainder)
            if i == self.num_slices - 1:
                slice_qty = remaining_qty
            else:
                # Slight randomization of slice size
                slice_qty = base_slice_size * np.random.uniform(0.9, 1.1)
                slice_qty = min(slice_qty, remaining_qty)

            remaining_qty -= slice_qty

            schedule.append(ChildOrder(sequence=i, quantity=slice_qty, scheduled_time=scheduled_time, limit_price=limit_price))

        return schedule

    def get_theoretical_price(self, prices: List[float], volumes: Optional[List[float]] = None) -> float:
        """
        Calculate theoretical TWAP from price series.

        Args:
            prices: Price series during execution
            volumes: Volume series (ignored for TWAP)

        Returns:
            TWAP price
        """
        if not prices:
            return 0.0
        return np.mean(prices)


class VWAPAlgorithm:
    """
    Volume-Weighted Average Price (VWAP) execution.

    Slices order proportional to expected volume profile.
    Better for minimizing impact in liquid markets.

    Parameters:
        duration_minutes: Total execution duration
        num_slices: Number of child orders
        volume_profile: Expected volume distribution (optional)
    """

    def __init__(self, duration_minutes: int = 60, num_slices: int = 10, volume_profile: Optional[List[float]] = None):
        self.duration_minutes = duration_minutes
        self.num_slices = num_slices

        # Default U-shaped volume profile if not provided
        if volume_profile is None:
            # Typical intraday volume: higher at open/close
            self.volume_profile = self._generate_u_shaped_profile(num_slices)
        else:
            # Normalize provided profile
            total = sum(volume_profile)
            self.volume_profile = [v / total for v in volume_profile]

    def _generate_u_shaped_profile(self, n: int) -> List[float]:
        """Generate U-shaped intraday volume profile."""
        # Higher at ends, lower in middle
        x = np.linspace(0, 1, n)
        profile = 0.5 + 2 * (x - 0.5) ** 2

        # Normalize
        return list(profile / profile.sum())

    def generate_schedule(
        self,
        total_quantity: float,
        start_time: Optional[datetime] = None,
        limit_price: Optional[float] = None,
        actual_volume: Optional[List[float]] = None,
    ) -> List[ChildOrder]:
        """
        Generate VWAP execution schedule.

        Args:
            total_quantity: Total quantity to execute
            start_time: Schedule start time
            limit_price: Limit price (optional)
            actual_volume: Actual volume profile (overrides default)

        Returns:
            List of child orders
        """
        if start_time is None:
            start_time = datetime.now()

        # Use actual volume if provided
        if actual_volume is not None and len(actual_volume) == self.num_slices:
            total_vol = sum(actual_volume)
            profile = [v / total_vol for v in actual_volume] if total_vol > 0 else self.volume_profile
        else:
            profile = self.volume_profile

        # Time between slices
        interval_seconds = (self.duration_minutes * 60) / self.num_slices

        schedule = []

        for i in range(self.num_slices):
            scheduled_time = start_time + timedelta(seconds=i * interval_seconds)
            slice_qty = total_quantity * profile[i]

            schedule.append(ChildOrder(sequence=i, quantity=slice_qty, scheduled_time=scheduled_time, limit_price=limit_price))

        return schedule

    def get_theoretical_price(self, prices: List[float], volumes: List[float]) -> float:
        """
        Calculate theoretical VWAP from price and volume series.

        Args:
            prices: Price series during execution
            volumes: Volume series during execution

        Returns:
            VWAP price
        """
        if not prices or not volumes:
            return 0.0

        if len(prices) != len(volumes):
            raise ValueError("Prices and volumes must have same length")

        total_value = sum(p * v for p, v in zip(prices, volumes))
        total_volume = sum(volumes)

        if total_volume == 0:
            return np.mean(prices)

        return total_value / total_volume

    def update_profile(self, actual_volumes: List[float], learning_rate: float = 0.1):
        """
        Update volume profile based on actual observations.

        Args:
            actual_volumes: Observed volume profile
            learning_rate: Weight for new observations
        """
        if len(actual_volumes) != len(self.volume_profile):
            return

        # Normalize actual
        total = sum(actual_volumes)
        if total > 0:
            normalized = [v / total for v in actual_volumes]

            # Exponential moving average update
            self.volume_profile = [
                (1 - learning_rate) * old + learning_rate * new for old, new in zip(self.volume_profile, normalized)
            ]


class AdaptiveAlgorithm:
    """
    Adaptive execution that adjusts based on market conditions.

    Combines TWAP/VWAP with real-time adjustments:
    - Speed up if favorable price move
    - Slow down if adverse price move
    - Pause if volatility spikes
    """

    def __init__(
        self,
        base_algorithm: str = "twap",
        urgency: float = 0.5,  # 0 = passive, 1 = aggressive
        price_tolerance: float = 0.002,  # 20 bps
    ):
        self.base_algorithm = base_algorithm
        self.urgency = urgency
        self.price_tolerance = price_tolerance

        if base_algorithm == "twap":
            self._algo = TWAPAlgorithm()
        else:
            self._algo = VWAPAlgorithm()

    def should_accelerate(self, entry_price: float, current_price: float, is_buy: bool) -> bool:
        """
        Check if we should accelerate execution.

        Accelerate if price is moving favorably.

        Args:
            entry_price: Price when order started
            current_price: Current market price
            is_buy: True if buy order

        Returns:
            True if should accelerate
        """
        price_change = (current_price - entry_price) / entry_price

        if is_buy:
            # Accelerate if price dropping
            return price_change < -self.price_tolerance * (1 - self.urgency)
        else:
            # Accelerate if price rising
            return price_change > self.price_tolerance * (1 - self.urgency)

    def should_pause(self, current_vol: float, baseline_vol: float, vol_threshold: float = 2.0) -> bool:
        """
        Check if we should pause execution.

        Pause if volatility is too high.

        Args:
            current_vol: Current volatility
            baseline_vol: Normal volatility level
            vol_threshold: Multiple of baseline to pause

        Returns:
            True if should pause
        """
        return current_vol > baseline_vol * vol_threshold

    def adjust_slice_size(self, base_size: float, entry_price: float, current_price: float, is_buy: bool) -> float:
        """
        Adjust slice size based on price movement.

        Args:
            base_size: Original slice size
            entry_price: Order entry price
            current_price: Current price
            is_buy: True if buy order

        Returns:
            Adjusted slice size
        """
        price_change = (current_price - entry_price) / entry_price

        # Calculate adjustment factor
        if is_buy:
            # Larger slices if price dropping, smaller if rising
            adjustment = 1 - price_change / self.price_tolerance
        else:
            # Larger slices if price rising, smaller if dropping
            adjustment = 1 + price_change / self.price_tolerance

        # Clamp adjustment
        adjustment = np.clip(adjustment, 0.5, 2.0)

        # Apply urgency
        adjustment = 1 + (adjustment - 1) * self.urgency

        return base_size * adjustment

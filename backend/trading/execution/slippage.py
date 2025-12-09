"""
Slippage Models

Estimate and track execution costs.
"""

from dataclasses import dataclass
import numpy as np


@dataclass
class SlippageEstimate:
    """Estimated slippage for an order."""
    spread_cost_bps: float       # Bid-ask spread cost
    market_impact_bps: float     # Market impact estimate
    total_cost_bps: float        # Total estimated cost
    confidence: float            # Confidence in estimate


class SlippageModel:
    """
    Slippage and market impact model.

    Components:
    1. Spread cost: Half the bid-ask spread
    2. Market impact: Square-root model based on participation rate

    Market Impact Formula:
    ---------------------
    impact = σ * √(volume_pct) * sign(side)

    Where:
    - σ = daily volatility
    - volume_pct = order_size / daily_volume
    """

    def __init__(
        self,
        impact_coefficient: float = 0.1,
        permanent_impact_ratio: float = 0.5
    ):
        """
        Initialize slippage model.

        Args:
            impact_coefficient: Impact scaling factor
            permanent_impact_ratio: Fraction of impact that's permanent
        """
        self.impact_coefficient = impact_coefficient
        self.permanent_impact_ratio = permanent_impact_ratio

        # Historical tracking
        self.predicted_slippage: list = []
        self.actual_slippage: list = []

    def estimate(
        self,
        order_size: float,
        daily_volume: float,
        volatility: float,
        spread_bps: float,
        is_buy: bool = True
    ) -> SlippageEstimate:
        """
        Estimate slippage for an order.

        Args:
            order_size: Order size in dollars
            daily_volume: Average daily dollar volume
            volatility: Daily volatility (decimal)
            spread_bps: Bid-ask spread in basis points
            is_buy: True if buy order

        Returns:
            SlippageEstimate with cost breakdown
        """
        # Spread cost (cross the spread)
        spread_cost_bps = spread_bps / 2

        # Participation rate
        if daily_volume > 0:
            participation = order_size / daily_volume
        else:
            participation = 0.01  # Default assumption

        # Square-root market impact model
        # impact = η * σ * √(Q/V)
        market_impact = (
            self.impact_coefficient *
            volatility *
            np.sqrt(participation) *
            10000  # Convert to bps
        )

        # Total cost
        total_cost = spread_cost_bps + market_impact

        # Confidence based on data quality
        confidence = 0.7 if daily_volume > 0 else 0.3

        return SlippageEstimate(
            spread_cost_bps=spread_cost_bps,
            market_impact_bps=market_impact,
            total_cost_bps=total_cost,
            confidence=confidence
        )

    def estimate_execution_price(
        self,
        mid_price: float,
        order_size: float,
        daily_volume: float,
        volatility: float,
        spread_bps: float,
        is_buy: bool = True
    ) -> float:
        """
        Estimate execution price including slippage.

        Args:
            mid_price: Current mid price
            order_size: Order size in dollars
            daily_volume: Average daily volume
            volatility: Daily volatility
            spread_bps: Bid-ask spread in bps
            is_buy: True if buying

        Returns:
            Estimated execution price
        """
        estimate = self.estimate(
            order_size, daily_volume, volatility, spread_bps, is_buy
        )

        slippage_pct = estimate.total_cost_bps / 10000

        if is_buy:
            return mid_price * (1 + slippage_pct)
        else:
            return mid_price * (1 - slippage_pct)

    def record_execution(
        self,
        predicted_bps: float,
        actual_bps: float
    ):
        """
        Record actual vs predicted slippage for model calibration.

        Args:
            predicted_bps: Predicted slippage
            actual_bps: Actual realized slippage
        """
        self.predicted_slippage.append(predicted_bps)
        self.actual_slippage.append(actual_bps)

        # Keep last 1000 records
        if len(self.predicted_slippage) > 1000:
            self.predicted_slippage = self.predicted_slippage[-1000:]
            self.actual_slippage = self.actual_slippage[-1000:]

    def get_model_accuracy(self) -> dict:
        """
        Get model accuracy statistics.

        Returns:
            Dictionary with accuracy metrics
        """
        if len(self.predicted_slippage) < 10:
            return {"status": "insufficient_data"}

        predicted = np.array(self.predicted_slippage)
        actual = np.array(self.actual_slippage)

        error = predicted - actual

        return {
            "mae": np.mean(np.abs(error)),
            "rmse": np.sqrt(np.mean(error ** 2)),
            "bias": np.mean(error),
            "correlation": np.corrcoef(predicted, actual)[0, 1],
            "num_samples": len(predicted)
        }

    def calibrate(self):
        """
        Calibrate model based on historical data.

        Updates impact_coefficient to minimize prediction error.
        """
        if len(self.actual_slippage) < 50:
            return  # Need more data

        # Simple calibration: adjust coefficient based on bias
        predicted = np.array(self.predicted_slippage[-100:])
        actual = np.array(self.actual_slippage[-100:])

        if np.mean(predicted) > 0:
            ratio = np.mean(actual) / np.mean(predicted)

            # Smooth adjustment
            self.impact_coefficient *= 0.9 + 0.1 * ratio

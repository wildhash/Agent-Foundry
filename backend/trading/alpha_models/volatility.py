"""
Volatility Breakout Alpha Model

Captures volatility expansion signals for breakout trading.
Uses GARCH-style volatility forecasting and regime detection.

Mathematical Foundation:
-----------------------
Signal triggered when:
1. Current vol > k * historical vol (expansion)
2. Price breaks key level (high/low of lookback)
3. Volume confirms (above average)

Position direction follows breakout direction.
"""

from datetime import datetime
from typing import Optional, Tuple
import numpy as np
import pandas as pd

from .base import BaseAlphaModel
from ..core import AlphaSignal, FeatureSet


class VolatilityBreakoutModel(BaseAlphaModel):
    """
    Volatility breakout alpha model.

    Captures volatility expansion signals that often precede
    large directional moves. Uses ATR-based breakout levels
    with volume confirmation.

    Parameters:
        atr_period: Period for ATR calculation
        breakout_multiple: ATR multiple for breakout threshold
        vol_expansion_threshold: Vol expansion ratio to trigger
        volume_threshold: Volume ratio above average to confirm
        lookback: Lookback for historical range
    """

    def __init__(
        self,
        atr_period: int = 14,
        breakout_multiple: float = 1.5,
        vol_expansion_threshold: float = 1.5,
        volume_threshold: float = 1.2,
        lookback: int = 20,
        name: str = "volatility_breakout",
    ):
        super().__init__(name=name, lookback_periods=max(atr_period, lookback) * 2, min_data_points=max(atr_period, lookback))

        self.atr_period = atr_period
        self.breakout_multiple = breakout_multiple
        self.vol_expansion_threshold = vol_expansion_threshold
        self.volume_threshold = volume_threshold
        self.lookback = lookback

    def get_required_features(self) -> list:
        """Features required by volatility model."""
        return ["atr", "realized_vol", "vol_regime", "volume_ratio", "range_position"]

    def generate_signal(self, ohlcv: pd.DataFrame, features: Optional[FeatureSet] = None) -> AlphaSignal:
        """
        Generate volatility breakout signal.

        Process:
        1. Calculate ATR and check for vol expansion
        2. Check for price breakout above/below range
        3. Confirm with volume
        4. Generate signal in breakout direction

        Args:
            ohlcv: DataFrame with OHLCV data
            features: Pre-calculated features (optional)

        Returns:
            AlphaSignal for breakout direction
        """
        # Validate data
        if not self.validate_data(ohlcv):
            return self.null_signal("INVALID_DATA")

        if len(ohlcv) < self.min_data_points:
            return self.null_signal("INSUFFICIENT_DATA")

        # Calculate components
        atr, atr_ratio = self._calculate_atr_expansion(ohlcv)
        breakout_direction, breakout_strength = self._check_breakout(ohlcv)
        volume_confirmed = self._check_volume_confirmation(ohlcv)

        # Check for vol expansion
        if atr_ratio < self.vol_expansion_threshold:
            signal = AlphaSignal(
                value=0.0,
                confidence=0.0,
                regime_filter="LOW_VOL",
                components={"atr": atr, "atr_ratio": atr_ratio, "threshold": self.vol_expansion_threshold},
                model_name=self.name,
                timestamp=datetime.now(),
            )
            self._store_signal(signal)
            return signal

        # Check for breakout
        if breakout_direction == 0:
            signal = AlphaSignal(
                value=0.0,
                confidence=0.0,
                regime_filter="NO_BREAKOUT",
                components={"atr": atr, "atr_ratio": atr_ratio, "breakout_strength": breakout_strength},
                model_name=self.name,
                timestamp=datetime.now(),
            )
            self._store_signal(signal)
            return signal

        # Calculate signal strength
        # Combine: vol expansion * breakout strength * volume factor
        vol_factor = min((atr_ratio - 1) / (self.vol_expansion_threshold - 1), 2.0)
        volume_factor = 1.5 if volume_confirmed else 0.8

        signal_value = breakout_direction * breakout_strength * vol_factor * volume_factor
        signal_value = np.clip(signal_value, -1.0, 1.0)

        # Confidence based on multiple confirmations
        confirmations = sum([atr_ratio >= self.vol_expansion_threshold, abs(breakout_strength) > 0.5, volume_confirmed])
        confidence = confirmations / 3.0

        signal = AlphaSignal(
            value=signal_value,
            confidence=confidence,
            regime_filter="BREAKOUT_ACTIVE",
            components={
                "atr": atr,
                "atr_ratio": atr_ratio,
                "breakout_direction": breakout_direction,
                "breakout_strength": breakout_strength,
                "volume_confirmed": volume_confirmed,
                "vol_factor": vol_factor,
            },
            model_name=self.name,
            timestamp=datetime.now(),
        )

        self._store_signal(signal)
        return signal

    def _calculate_atr_expansion(self, ohlcv: pd.DataFrame) -> Tuple[float, float]:
        """
        Calculate ATR and its expansion ratio.

        ATR expansion = current ATR / average ATR over longer period

        Args:
            ohlcv: OHLCV DataFrame

        Returns:
            Tuple of (current ATR, expansion ratio)
        """
        high = ohlcv["high"].values
        low = ohlcv["low"].values
        close = ohlcv["close"].values

        # True Range
        tr = np.maximum(high[1:] - low[1:], np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))

        if len(tr) < self.atr_period * 2:
            return 0.0, 1.0

        # Current ATR (EMA)
        current_atr = self._ema(tr[-self.atr_period :], self.atr_period)[-1]

        # Historical average ATR (longer lookback)
        historical_atr = np.mean(tr[-self.lookback * 2 : -self.atr_period])

        if historical_atr < 1e-8:
            return current_atr, 1.0

        expansion_ratio = current_atr / historical_atr

        return current_atr, expansion_ratio

    def _check_breakout(self, ohlcv: pd.DataFrame) -> Tuple[int, float]:
        """
        Check for price breakout above/below recent range.

        Args:
            ohlcv: OHLCV DataFrame

        Returns:
            Tuple of (direction: -1/0/+1, strength: 0-1)
        """
        close = ohlcv["close"].values
        high = ohlcv["high"].values
        low = ohlcv["low"].values

        # Recent range (excluding current bar)
        recent_high = np.max(high[-self.lookback - 1 : -1])
        recent_low = np.min(low[-self.lookback - 1 : -1])
        range_size = recent_high - recent_low

        current_close = close[-1]

        if range_size < 1e-8:
            return 0, 0.0

        # Check for upside breakout
        if current_close > recent_high:
            overshoot = (current_close - recent_high) / range_size
            strength = min(overshoot, 1.0)
            return 1, strength

        # Check for downside breakout
        if current_close < recent_low:
            overshoot = (recent_low - current_close) / range_size
            strength = min(overshoot, 1.0)
            return -1, strength

        return 0, 0.0

    def _check_volume_confirmation(self, ohlcv: pd.DataFrame) -> bool:
        """
        Check if current volume confirms breakout.

        Args:
            ohlcv: OHLCV DataFrame

        Returns:
            True if volume confirms breakout
        """
        volume = ohlcv["volume"].values

        if len(volume) < self.lookback:
            return False

        current_volume = volume[-1]
        avg_volume = np.mean(volume[-self.lookback : -1])

        if avg_volume < 1e-8:
            return False

        volume_ratio = current_volume / avg_volume

        return volume_ratio >= self.volume_threshold

    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        Calculate Exponential Moving Average.

        Args:
            data: Input array
            period: EMA period

        Returns:
            EMA array
        """
        if len(data) < period:
            return np.array([np.mean(data)]) if len(data) > 0 else np.array([0.0])

        alpha = 2 / (period + 1)
        result = np.zeros(len(data))
        result[0] = data[0]

        for i in range(1, len(data)):
            result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]

        return result

    def calculate_garch_forecast(
        self, returns: np.ndarray, omega: float = 0.00001, alpha: float = 0.1, beta: float = 0.85
    ) -> float:
        """
        Simple GARCH(1,1) volatility forecast.

        σ²_{t+1} = ω + α * r²_t + β * σ²_t

        Args:
            returns: Return series
            omega: Long-term variance weight
            alpha: Return shock weight
            beta: Previous variance weight

        Returns:
            Forecasted volatility (annualized)
        """
        if len(returns) < 20:
            return np.std(returns) * np.sqrt(252)

        # Initialize with sample variance
        var = np.var(returns[-20:])

        # Update through recent returns
        for r in returns[-10:]:
            var = omega + alpha * r**2 + beta * var

        # Forecast next period
        forecast_var = omega + alpha * returns[-1] ** 2 + beta * var

        # Annualize
        return np.sqrt(forecast_var * 252)

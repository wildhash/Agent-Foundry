"""
Momentum Alpha Model

Captures trending price movements using volatility-adjusted momentum (VAM)
with ADX trend strength filtering.

Mathematical Foundation:
-----------------------
VAM_t = Σ(w_i * r_i) / σ_t

Where:
- w_i = exponential decay weights
- r_i = log returns
- σ_t = rolling volatility

Only generates signals when ADX > threshold (strong trend).
"""

from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from .base import BaseAlphaModel
from ..core import AlphaSignal, FeatureSet


class MomentumAlphaModel(BaseAlphaModel):
    """
    Volatility-adjusted momentum alpha model.
    
    Captures trending price movements while normalizing
    for volatility regime. Uses ADX as trend filter.
    
    Parameters:
        lookbacks: List of lookback periods for multi-scale momentum
        decay_lambda: Exponential decay rate for weighting
        adx_threshold: Minimum ADX for trend confirmation
        adx_period: Period for ADX calculation
        max_signal: Maximum signal magnitude before normalization
    """
    
    def __init__(
        self,
        lookbacks: List[int] = [5, 10, 20, 60],
        decay_lambda: float = 0.1,
        adx_threshold: float = 25.0,
        adx_period: int = 14,
        max_signal: float = 3.0,
        name: str = "momentum"
    ):
        super().__init__(
            name=name,
            lookback_periods=max(lookbacks) + adx_period + 10,
            min_data_points=max(lookbacks)
        )
        
        self.lookbacks = lookbacks
        self.decay_lambda = decay_lambda
        self.adx_threshold = adx_threshold
        self.adx_period = adx_period
        self.max_signal = max_signal
    
    def get_required_features(self) -> list:
        """Features required by momentum model."""
        return [
            "log_returns",
            "realized_vol",
            "adx",
            "trend_direction"
        ]
    
    def generate_signal(
        self,
        ohlcv: pd.DataFrame,
        features: Optional[FeatureSet] = None
    ) -> AlphaSignal:
        """
        Generate momentum alpha signal.
        
        Process:
        1. Calculate VAM for each lookback period
        2. Average across lookbacks
        3. Apply ADX trend filter
        4. Normalize to [-1, +1] range
        
        Args:
            ohlcv: DataFrame with OHLCV data
            features: Pre-calculated features (optional)
            
        Returns:
            AlphaSignal with momentum direction and strength
        """
        # Validate data
        if not self.validate_data(ohlcv):
            return self.null_signal("INVALID_DATA")
        
        # Calculate log returns
        returns = np.log(
            ohlcv['close'] / ohlcv['close'].shift(1)
        ).dropna().values
        
        if len(returns) < self.min_data_points:
            return self.null_signal("INSUFFICIENT_DATA")
        
        # Calculate VAM for each lookback
        vam_signals = []
        for lb in self.lookbacks:
            if len(returns) >= lb:
                vam = self._calculate_vam(returns, lb)
                vam_signals.append(vam)
        
        if not vam_signals:
            return self.null_signal("NO_VALID_LOOKBACKS")
        
        # Equal-weighted average across lookbacks
        combined_vam = np.mean(vam_signals)
        
        # Calculate ADX for trend filter
        adx = self._calculate_adx(
            ohlcv['high'].values,
            ohlcv['low'].values,
            ohlcv['close'].values,
            self.adx_period
        )
        
        # Apply ADX filter
        if adx < self.adx_threshold:
            signal = AlphaSignal(
                value=0.0,
                confidence=0.0,
                regime_filter="ADX_FILTER",
                components={
                    "vam": combined_vam,
                    "adx": adx,
                    "threshold": self.adx_threshold,
                    "vam_by_lookback": dict(zip(self.lookbacks, vam_signals))
                },
                model_name=self.name,
                timestamp=datetime.now()
            )
            self._store_signal(signal)
            return signal
        
        # Clip to max signal
        signal_value = np.clip(combined_vam, -self.max_signal, self.max_signal)
        
        # Normalize to [-1, +1] range
        normalized_signal = signal_value / self.max_signal
        
        # Confidence based on ADX strength above threshold
        confidence = min((adx - self.adx_threshold) / 25.0, 1.0)
        
        signal = AlphaSignal(
            value=normalized_signal,
            confidence=confidence,
            regime_filter="TRENDING",
            components={
                "vam": combined_vam,
                "adx": adx,
                "signal_raw": signal_value,
                "vam_by_lookback": dict(zip(self.lookbacks, vam_signals))
            },
            model_name=self.name,
            timestamp=datetime.now()
        )
        
        self._store_signal(signal)
        return signal
    
    def _calculate_vam(self, returns: np.ndarray, lookback: int) -> float:
        """
        Calculate Volatility-Adjusted Momentum.
        
        VAM = Σ(w_i * r_i) / σ
        
        Args:
            returns: Array of log returns
            lookback: Number of periods to use
            
        Returns:
            VAM value (not normalized)
        """
        if len(returns) < lookback:
            return 0.0
        
        recent_returns = returns[-lookback:]
        
        # Exponential decay weights (most recent = highest weight)
        weights = np.exp(-self.decay_lambda * np.arange(lookback))
        weights = weights[::-1]  # Reverse so most recent is last
        weights = weights / weights.sum()  # Normalize
        
        # Weighted return sum
        weighted_return = np.sum(weights * recent_returns)
        
        # Volatility normalization
        vol = np.std(recent_returns)
        if vol < 1e-8:
            return 0.0
        
        return weighted_return / vol
    
    def _calculate_adx(
        self,
        high: np.ndarray,
        low: np.ndarray,
        close: np.ndarray,
        period: int = 14
    ) -> float:
        """
        Calculate Average Directional Index (ADX).
        
        ADX measures trend strength regardless of direction.
        ADX > 25 suggests strong trend.
        
        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: Smoothing period
            
        Returns:
            ADX value (0-100)
        """
        if len(high) < period + 1:
            return 0.0
        
        # True Range
        tr = np.maximum(
            high[1:] - low[1:],
            np.maximum(
                np.abs(high[1:] - close[:-1]),
                np.abs(low[1:] - close[:-1])
            )
        )
        
        # Plus/Minus Directional Movement
        plus_dm = np.where(
            (high[1:] - high[:-1]) > (low[:-1] - low[1:]),
            np.maximum(high[1:] - high[:-1], 0),
            0
        )
        
        minus_dm = np.where(
            (low[:-1] - low[1:]) > (high[1:] - high[:-1]),
            np.maximum(low[:-1] - low[1:], 0),
            0
        )
        
        # Wilder's smoothing
        atr = self._wilder_smooth(tr, period)
        plus_di = 100 * self._wilder_smooth(plus_dm, period) / (atr + 1e-8)
        minus_di = 100 * self._wilder_smooth(minus_dm, period) / (atr + 1e-8)
        
        # Directional Index
        dx = 100 * np.abs(plus_di - minus_di) / (plus_di + minus_di + 1e-8)
        
        # Average Directional Index
        adx = self._wilder_smooth(dx, period)
        
        return adx[-1] if len(adx) > 0 else 0.0
    
    def _wilder_smooth(self, data: np.ndarray, period: int) -> np.ndarray:
        """
        Apply Wilder's exponential smoothing.
        
        Uses: EMA_t = (value_t + (period-1) * EMA_{t-1}) / period
        
        Args:
            data: Input array
            period: Smoothing period
            
        Returns:
            Smoothed array
        """
        if len(data) < period:
            return np.array([np.mean(data)]) if len(data) > 0 else np.array([0.0])
        
        result = np.zeros(len(data) - period + 1)
        result[0] = np.mean(data[:period])
        
        for i in range(1, len(result)):
            result[i] = (data[period - 1 + i] + (period - 1) * result[i-1]) / period
        
        return result
    
    def get_trend_direction(self, ohlcv: pd.DataFrame) -> float:
        """
        Get current trend direction (-1 to +1).
        
        Args:
            ohlcv: OHLCV DataFrame
            
        Returns:
            Trend direction score
        """
        if len(ohlcv) < 20:
            return 0.0
        
        # Simple: sign of 20-period return
        returns_20 = np.log(ohlcv['close'].iloc[-1] / ohlcv['close'].iloc[-20])
        
        # Normalize roughly
        return np.clip(returns_20 * 10, -1.0, 1.0)

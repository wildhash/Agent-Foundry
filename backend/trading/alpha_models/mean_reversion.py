"""
Mean Reversion Alpha Model

Exploits temporary price dislocations from statistical equilibrium
using z-score signals with Hurst exponent filtering.

Mathematical Foundation:
-----------------------
z_t = (P_t - μ_{t,n}) / σ_{t,n}

Signal = -sign(z_t) * min(|z_t|, max_signal)

Only generates signals when Hurst < 0.5 (mean-reverting regime).
"""

from datetime import datetime
from typing import Optional
import numpy as np
import pandas as pd

from .base import BaseAlphaModel
from ..core import AlphaSignal, FeatureSet


class MeanReversionAlphaModel(BaseAlphaModel):
    """
    Mean-reversion alpha model.
    
    Exploits temporary price dislocations from fair value.
    Uses z-score for signal strength and Hurst exponent
    to filter for mean-reverting market conditions.
    
    Parameters:
        lookback: Rolling window for mean/std calculation
        entry_threshold: Minimum z-score to generate signal
        hurst_threshold: Maximum Hurst exponent (< 0.5 = mean-reverting)
        hurst_lookback: Lookback for Hurst calculation
        max_signal: Maximum signal magnitude
    """
    
    def __init__(
        self,
        lookback: int = 20,
        entry_threshold: float = 2.0,
        hurst_threshold: float = 0.5,
        hurst_lookback: int = 100,
        max_signal: float = 2.5,
        name: str = "mean_reversion"
    ):
        super().__init__(
            name=name,
            lookback_periods=max(lookback, hurst_lookback) + 10,
            min_data_points=lookback
        )
        
        self.lookback = lookback
        self.entry_threshold = entry_threshold
        self.hurst_threshold = hurst_threshold
        self.hurst_lookback = hurst_lookback
        self.max_signal = max_signal
    
    def get_required_features(self) -> list:
        """Features required by mean-reversion model."""
        return [
            "zscore",
            "hurst_exponent",
            "bollinger_position",
            "realized_vol"
        ]
    
    def generate_signal(
        self,
        ohlcv: pd.DataFrame,
        features: Optional[FeatureSet] = None
    ) -> AlphaSignal:
        """
        Generate mean-reversion alpha signal.
        
        Process:
        1. Calculate Hurst exponent to verify mean-reverting regime
        2. Calculate z-score of current price vs rolling mean
        3. Generate contrarian signal if z-score exceeds threshold
        
        Args:
            ohlcv: DataFrame with OHLCV data
            features: Pre-calculated features (optional)
            
        Returns:
            AlphaSignal with mean-reversion direction and strength
        """
        # Validate data
        if not self.validate_data(ohlcv):
            return self.null_signal("INVALID_DATA")
        
        prices = ohlcv['close'].values
        
        if len(prices) < self.min_data_points:
            return self.null_signal("INSUFFICIENT_DATA")
        
        # Calculate Hurst exponent
        hurst = self._calculate_hurst(prices)
        
        # Check if market is mean-reverting
        if hurst >= self.hurst_threshold:
            signal = AlphaSignal(
                value=0.0,
                confidence=0.0,
                regime_filter="HURST_FILTER",
                components={
                    "hurst": hurst,
                    "threshold": self.hurst_threshold,
                    "regime": "trending" if hurst > 0.5 else "random_walk"
                },
                model_name=self.name,
                timestamp=datetime.now()
            )
            self._store_signal(signal)
            return signal
        
        # Calculate z-score
        zscore = self._calculate_zscore(prices)
        
        # Calculate Bollinger Band position for additional context
        bb_position = self._calculate_bollinger_position(prices)
        
        # Check if z-score exceeds entry threshold
        if abs(zscore) < self.entry_threshold:
            signal = AlphaSignal(
                value=0.0,
                confidence=0.0,
                regime_filter="THRESHOLD_FILTER",
                components={
                    "hurst": hurst,
                    "zscore": zscore,
                    "threshold": self.entry_threshold,
                    "bb_position": bb_position
                },
                model_name=self.name,
                timestamp=datetime.now()
            )
            self._store_signal(signal)
            return signal
        
        # Mean-reversion: negative z-score → positive signal (buy)
        # Positive z-score → negative signal (sell)
        signal_value = -np.clip(zscore, -self.max_signal, self.max_signal)
        normalized_signal = signal_value / self.max_signal
        
        # Confidence based on how mean-reverting the series is
        # Lower Hurst = more mean-reverting = higher confidence
        confidence = (self.hurst_threshold - hurst) / self.hurst_threshold
        confidence = max(0.0, min(1.0, confidence))
        
        # Boost confidence if z-score is extreme
        zscore_factor = min(abs(zscore) / 3.0, 1.0)
        confidence = (confidence + zscore_factor) / 2
        
        signal = AlphaSignal(
            value=normalized_signal,
            confidence=confidence,
            regime_filter="MEAN_REVERTING",
            components={
                "hurst": hurst,
                "zscore": zscore,
                "bb_position": bb_position,
                "entry_threshold": self.entry_threshold
            },
            model_name=self.name,
            timestamp=datetime.now()
        )
        
        self._store_signal(signal)
        return signal
    
    def _calculate_zscore(self, prices: np.ndarray) -> float:
        """
        Calculate z-score of current price vs rolling mean.
        
        z = (P_current - μ) / σ
        
        Args:
            prices: Price array
            
        Returns:
            Z-score value
        """
        if len(prices) < self.lookback:
            return 0.0
        
        recent = prices[-self.lookback:]
        current = prices[-1]
        
        mean = np.mean(recent)
        std = np.std(recent, ddof=1)  # Sample std
        
        if std < 1e-8:
            return 0.0
        
        return (current - mean) / std
    
    def _calculate_hurst(self, prices: np.ndarray) -> float:
        """
        Estimate Hurst exponent via R/S analysis.
        
        H < 0.5: Mean-reverting (anti-persistent)
        H = 0.5: Random walk (Brownian motion)
        H > 0.5: Trending (persistent)
        
        Args:
            prices: Price array
            
        Returns:
            Hurst exponent estimate
        """
        max_lag = min(self.hurst_lookback, len(prices) // 2)
        
        if len(prices) < max_lag or max_lag < 10:
            return 0.5  # Default to random walk
        
        # Use subset of lags for efficiency
        lags = list(range(10, max_lag, max(1, max_lag // 20)))
        
        if len(lags) < 3:
            return 0.5
        
        rs_values = []
        
        for lag in lags:
            # Calculate R/S for this lag
            n_subseries = len(prices) // lag
            rs_list = []
            
            for i in range(n_subseries):
                start = i * lag
                end = start + lag
                subseries = prices[start:end]
                
                if len(subseries) < 2:
                    continue
                
                mean = np.mean(subseries)
                deviations = subseries - mean
                cumulative = np.cumsum(deviations)
                
                r = np.max(cumulative) - np.min(cumulative)  # Range
                s = np.std(subseries, ddof=1)  # Std dev
                
                if s > 1e-8:
                    rs_list.append(r / s)
            
            if rs_list:
                rs_values.append((lag, np.mean(rs_list)))
        
        if len(rs_values) < 3:
            return 0.5
        
        # Linear regression in log-log space
        log_lags = np.log([x[0] for x in rs_values])
        log_rs = np.log([x[1] for x in rs_values])
        
        # Simple linear regression
        slope, _ = np.polyfit(log_lags, log_rs, 1)
        
        # Clamp to reasonable range
        return np.clip(slope, 0.0, 1.0)
    
    def _calculate_bollinger_position(
        self,
        prices: np.ndarray,
        num_std: float = 2.0
    ) -> float:
        """
        Calculate position within Bollinger Bands.
        
        Returns value in [-1, +1]:
        -1 = at lower band
         0 = at middle (SMA)
        +1 = at upper band
        
        Args:
            prices: Price array
            num_std: Number of standard deviations for bands
            
        Returns:
            Band position
        """
        if len(prices) < self.lookback:
            return 0.0
        
        recent = prices[-self.lookback:]
        current = prices[-1]
        
        sma = np.mean(recent)
        std = np.std(recent, ddof=1)
        
        if std < 1e-8:
            return 0.0
        
        # Distance from middle in terms of std devs
        distance = (current - sma) / (num_std * std)
        
        return np.clip(distance, -1.0, 1.0)
    
    def get_half_life(self, prices: np.ndarray) -> float:
        """
        Estimate mean-reversion half-life using Ornstein-Uhlenbeck model.
        
        Half-life = ln(2) / λ
        
        Where λ is estimated from:
        ΔP_t = λ * (μ - P_{t-1}) + ε_t
        
        Args:
            prices: Price array
            
        Returns:
            Half-life in periods (or inf if not mean-reverting)
        """
        if len(prices) < 20:
            return float('inf')
        
        # Calculate price changes
        delta_p = np.diff(prices)
        lagged_p = prices[:-1]
        
        # Simple regression: ΔP = α + β * P_{-1}
        # β should be negative for mean-reversion
        X = np.column_stack([np.ones(len(lagged_p)), lagged_p])
        y = delta_p
        
        try:
            coeffs = np.linalg.lstsq(X, y, rcond=None)[0]
            beta = coeffs[1]
            
            if beta >= 0:
                return float('inf')  # Not mean-reverting
            
            # λ = -β, half-life = ln(2) / λ
            lambda_param = -beta
            half_life = np.log(2) / lambda_param
            
            return max(1.0, half_life)
            
        except np.linalg.LinAlgError:
            return float('inf')

"""
Base class for alpha models.
"""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict, Any, Optional
import pandas as pd
import numpy as np

from ..core import AlphaSignal, FeatureSet


class BaseAlphaModel(ABC):
    """
    Abstract base class for alpha signal generators.

    All alpha models must implement:
    - generate_signal(): Produce alpha signal from features/data
    - get_required_features(): List features needed by this model
    """

    def __init__(
        self,
        name: str,
        lookback_periods: int = 100,
        min_data_points: int = 20
    ):
        """
        Initialize base alpha model.

        Args:
            name: Model identifier
            lookback_periods: Number of historical periods needed
            min_data_points: Minimum data points required for signal
        """
        self.name = name
        self.lookback_periods = lookback_periods
        self.min_data_points = min_data_points
        self.last_signal: Optional[AlphaSignal] = None
        self.signal_history: list = []

    @abstractmethod
    def generate_signal(
        self,
        ohlcv: pd.DataFrame,
        features: Optional[FeatureSet] = None
    ) -> AlphaSignal:
        """
        Generate alpha signal from market data.

        Args:
            ohlcv: DataFrame with columns [open, high, low, close, volume]
            features: Pre-calculated features (optional)

        Returns:
            AlphaSignal with value in [-1, +1] range
        """
        pass

    @abstractmethod
    def get_required_features(self) -> list:
        """
        Get list of feature names required by this model.

        Returns:
            List of feature name strings
        """
        pass

    def validate_data(self, ohlcv: pd.DataFrame) -> bool:
        """
        Validate input data meets requirements.

        Args:
            ohlcv: Input DataFrame

        Returns:
            True if data is valid
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']

        # Check columns exist
        if not all(col in ohlcv.columns for col in required_cols):
            return False

        # Check minimum data points
        if len(ohlcv) < self.min_data_points:
            return False

        # Check for NaN values in required columns
        if ohlcv[required_cols].isna().any().any():
            return False

        return True

    def null_signal(self, reason: str = "INVALID_DATA") -> AlphaSignal:
        """
        Return a null signal when unable to generate.

        Args:
            reason: Reason for null signal

        Returns:
            AlphaSignal with zero value
        """
        return AlphaSignal(
            value=0.0,
            confidence=0.0,
            regime_filter=reason,
            components={"reason": reason},
            model_name=self.name,
            timestamp=datetime.now()
        )

    def _store_signal(self, signal: AlphaSignal):
        """Store signal in history for analysis."""
        self.last_signal = signal
        self.signal_history.append({
            "timestamp": signal.timestamp,
            "value": signal.value,
            "confidence": signal.confidence
        })

        # Keep last 1000 signals
        if len(self.signal_history) > 1000:
            self.signal_history = self.signal_history[-1000:]

    def get_signal_stats(self) -> Dict[str, float]:
        """
        Get statistics about recent signals.

        Returns:
            Dictionary with signal statistics
        """
        if not self.signal_history:
            return {
                "mean": 0.0,
                "std": 0.0,
                "min": 0.0,
                "max": 0.0,
                "count": 0
            }

        values = [s["value"] for s in self.signal_history]
        return {
            "mean": np.mean(values),
            "std": np.std(values),
            "min": np.min(values),
            "max": np.max(values),
            "count": len(values)
        }

    def to_dict(self) -> Dict[str, Any]:
        """Convert model info to dictionary."""
        return {
            "name": self.name,
            "lookback_periods": self.lookback_periods,
            "min_data_points": self.min_data_points,
            "required_features": self.get_required_features(),
            "signal_stats": self.get_signal_stats()
        }

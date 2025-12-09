"""
Feature Engineering Pipeline

Real-time feature calculation with point-in-time correctness.
All features use only information available at decision time.

Categories:
- Price features: returns, volatility, VWAP deviations
- Volume features: volume ratio, order book imbalance
- Regime features: volatility regime, trend/MR labels
- Cross-sectional: relative strength, factor exposures
"""

from .engine import FeatureEngine
from .calculators import (
    PriceFeatures,
    VolumeFeatures,
    TechnicalFeatures,
    RegimeFeatures,
)

__all__ = [
    "FeatureEngine",
    "PriceFeatures",
    "VolumeFeatures",
    "TechnicalFeatures",
    "RegimeFeatures",
]

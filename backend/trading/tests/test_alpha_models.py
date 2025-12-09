"""
Tests for alpha models.
"""

import pytest
import numpy as np
import pandas as pd

from ..alpha_models import (
    MomentumAlphaModel,
    MeanReversionAlphaModel,
    VolatilityBreakoutModel,
    AlphaEnsemble
)
from ..core import MarketRegime


def generate_ohlcv(n: int = 200, trend: float = 0.0, vol: float = 0.02) -> pd.DataFrame:
    """Generate synthetic OHLCV data."""
    np.random.seed(42)

    # Generate price series
    returns = np.random.normal(trend, vol, n)
    prices = 100 * np.exp(np.cumsum(returns))

    # Generate OHLCV
    data = {
        'open': prices * (1 + np.random.uniform(-0.005, 0.005, n)),
        'high': prices * (1 + np.abs(np.random.normal(0, 0.01, n))),
        'low': prices * (1 - np.abs(np.random.normal(0, 0.01, n))),
        'close': prices,
        'volume': np.random.uniform(1000, 10000, n)
    }

    return pd.DataFrame(data)


class TestMomentumModel:
    """Tests for momentum alpha model."""

    def test_init(self):
        """Test model initialization."""
        model = MomentumAlphaModel()
        assert model.name == "momentum"
        assert len(model.lookbacks) > 0

    def test_generate_signal_trending(self):
        """Test signal generation in trending market."""
        model = MomentumAlphaModel()

        # Generate uptrending data
        ohlcv = generate_ohlcv(n=200, trend=0.002, vol=0.01)

        signal = model.generate_signal(ohlcv)

        assert signal is not None
        assert -1 <= signal.value <= 1
        assert 0 <= signal.confidence <= 1
        assert signal.model_name == "momentum"

    def test_generate_signal_ranging(self):
        """Test signal generation in ranging market."""
        model = MomentumAlphaModel()

        # Generate ranging data (low trend)
        ohlcv = generate_ohlcv(n=200, trend=0.0, vol=0.02)

        signal = model.generate_signal(ohlcv)

        # Should filter out low ADX signals
        assert signal is not None

    def test_insufficient_data(self):
        """Test handling of insufficient data."""
        model = MomentumAlphaModel()

        ohlcv = generate_ohlcv(n=10)  # Too short

        signal = model.generate_signal(ohlcv)

        assert signal.value == 0.0
        assert signal.regime_filter in ["INVALID_DATA", "INSUFFICIENT_DATA"]


class TestMeanReversionModel:
    """Tests for mean-reversion model."""

    def test_init(self):
        """Test model initialization."""
        model = MeanReversionAlphaModel()
        assert model.name == "mean_reversion"
        assert model.entry_threshold > 0

    def test_generate_signal(self):
        """Test signal generation."""
        model = MeanReversionAlphaModel()

        # Generate mean-reverting data
        ohlcv = generate_ohlcv(n=200, trend=0.0, vol=0.015)

        signal = model.generate_signal(ohlcv)

        assert signal is not None
        assert -1 <= signal.value <= 1

    def test_hurst_calculation(self):
        """Test Hurst exponent calculation."""
        model = MeanReversionAlphaModel()

        # Random walk should have H ≈ 0.5
        np.random.seed(123)
        random_walk = np.cumsum(np.random.randn(500))

        hurst = model._calculate_hurst(random_walk)

        # Hurst should be clamped to [0, 1]
        assert 0.0 <= hurst <= 1.0

    def test_zscore_extreme(self):
        """Test z-score with extreme values."""
        model = MeanReversionAlphaModel()

        # Generate data with extreme deviation
        prices = np.concatenate([
            np.full(100, 100),  # Flat
            np.linspace(100, 120, 50)  # Big move up
        ])

        zscore = model._calculate_zscore(prices)

        # Should be positive (price above mean)
        assert zscore > 0


class TestVolatilityModel:
    """Tests for volatility breakout model."""

    def test_init(self):
        """Test model initialization."""
        model = VolatilityBreakoutModel()
        assert model.name == "volatility_breakout"

    def test_generate_signal(self):
        """Test signal generation."""
        model = VolatilityBreakoutModel()

        ohlcv = generate_ohlcv(n=200)

        signal = model.generate_signal(ohlcv)

        assert signal is not None
        assert -1 <= signal.value <= 1

    def test_atr_calculation(self):
        """Test ATR expansion calculation."""
        model = VolatilityBreakoutModel()

        ohlcv = generate_ohlcv(n=200)

        atr, ratio = model._calculate_atr_expansion(ohlcv)

        assert atr >= 0
        assert ratio > 0


class TestAlphaEnsemble:
    """Tests for alpha ensemble."""

    def test_init(self):
        """Test ensemble initialization."""
        models = {
            "momentum": MomentumAlphaModel(),
            "mean_reversion": MeanReversionAlphaModel()
        }

        ensemble = AlphaEnsemble(models)

        assert len(ensemble.models) == 2

    def test_combined_signal(self):
        """Test combined signal generation."""
        models = {
            "momentum": MomentumAlphaModel(),
            "mean_reversion": MeanReversionAlphaModel()
        }

        ensemble = AlphaEnsemble(models)
        ohlcv = generate_ohlcv(n=200)

        signal = ensemble.generate_combined_signal(
            ohlcv=ohlcv,
            regime=MarketRegime.NORMAL
        )

        assert signal is not None
        assert signal.model_name == "ensemble"
        assert "model_signals" in signal.components

    def test_regime_weights(self):
        """Test regime-specific weights."""
        models = {
            "momentum": MomentumAlphaModel(),
            "mean_reversion": MeanReversionAlphaModel()
        }

        ensemble = AlphaEnsemble(models)

        # Check different regimes have different weights
        trending_weights = ensemble.regime_weights[MarketRegime.TRENDING_UP]
        mr_weights = ensemble.regime_weights[MarketRegime.MEAN_REVERTING]

        # Momentum should be higher in trending
        assert trending_weights.get("momentum", 0) > mr_weights.get("momentum", 0)
        # Mean-reversion should be higher in MR regime
        assert mr_weights.get("mean_reversion", 0) > trending_weights.get("mean_reversion", 0)

    def test_thompson_sampling(self):
        """Test Thompson Sampling updates."""
        models = {"momentum": MomentumAlphaModel()}
        ensemble = AlphaEnsemble(models)

        # Record some outcomes
        ensemble.update_thompson_params("momentum", success=True, magnitude=0.5)
        ensemble.update_thompson_params("momentum", success=True, magnitude=0.3)
        ensemble.update_thompson_params("momentum", success=False, magnitude=0.2)

        # Alpha should be higher than beta (more successes)
        assert ensemble.ts_params["momentum"]["alpha"] > ensemble.ts_params["momentum"]["beta"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

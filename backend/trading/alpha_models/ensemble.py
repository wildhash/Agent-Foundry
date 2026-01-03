"""
Alpha Ensemble - Combines multiple alpha models.

Uses volatility-weighted combination with regime-adaptive weights.
Implements Thompson Sampling for adaptive model allocation.
"""

from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from .base import BaseAlphaModel
from ..core import AlphaSignal, FeatureSet, MarketRegime


class AlphaEnsemble:
    """
    Combines multiple alpha models into a single signal.

    Features:
    - Volatility-weighted signal combination
    - Regime-adaptive model weights
    - Thompson Sampling for online weight learning
    - Performance tracking per model

    Parameters:
        models: Dictionary of model_name -> BaseAlphaModel
        default_weights: Default weights if no regime-specific
        min_confidence: Minimum confidence to include signal
    """

    def __init__(
        self,
        models: Dict[str, BaseAlphaModel],
        default_weights: Optional[Dict[str, float]] = None,
        min_confidence: float = 0.1,
    ):
        self.models = models
        self.default_weights = default_weights or {name: 1.0 / len(models) for name in models}
        self.min_confidence = min_confidence

        # Regime-specific weights
        self.regime_weights: Dict[MarketRegime, Dict[str, float]] = {
            MarketRegime.TRENDING_UP: {"momentum": 0.6, "mean_reversion": 0.1, "volatility_breakout": 0.3},
            MarketRegime.TRENDING_DOWN: {"momentum": 0.6, "mean_reversion": 0.1, "volatility_breakout": 0.3},
            MarketRegime.MEAN_REVERTING: {"momentum": 0.1, "mean_reversion": 0.7, "volatility_breakout": 0.2},
            MarketRegime.HIGH_VOLATILITY: {"momentum": 0.3, "mean_reversion": 0.2, "volatility_breakout": 0.5},
            MarketRegime.LOW_VOLATILITY: {"momentum": 0.4, "mean_reversion": 0.5, "volatility_breakout": 0.1},
            MarketRegime.CRISIS: {"momentum": 0.0, "mean_reversion": 0.0, "volatility_breakout": 0.0},
            MarketRegime.NORMAL: {"momentum": 0.4, "mean_reversion": 0.4, "volatility_breakout": 0.2},
        }

        # Thompson Sampling state (alpha, beta for each model)
        self.ts_params: Dict[str, Dict[str, float]] = {name: {"alpha": 1.0, "beta": 1.0} for name in models}

        # Performance tracking
        self.model_performance: Dict[str, List[float]] = {name: [] for name in models}

    def generate_combined_signal(
        self,
        ohlcv: pd.DataFrame,
        regime: MarketRegime = MarketRegime.NORMAL,
        features: Optional[FeatureSet] = None,
        use_thompson_sampling: bool = False,
    ) -> AlphaSignal:
        """
        Generate combined signal from all models.

        Args:
            ohlcv: OHLCV DataFrame
            regime: Current market regime
            features: Pre-calculated features
            use_thompson_sampling: Use adaptive weights

        Returns:
            Combined AlphaSignal
        """
        # Generate signals from all models
        signals: Dict[str, AlphaSignal] = {}
        for name, model in self.models.items():
            signals[name] = model.generate_signal(ohlcv, features)

        # Get weights for current regime
        if use_thompson_sampling:
            weights = self._get_thompson_weights()
        else:
            weights = self.regime_weights.get(regime, self.default_weights)

        # Filter weights to only include models we have
        weights = {k: v for k, v in weights.items() if k in signals}

        # Normalize weights
        total_weight = sum(weights.values())
        if total_weight > 0:
            weights = {k: v / total_weight for k, v in weights.items()}

        # Combine signals (confidence-weighted)
        combined_value = 0.0
        combined_confidence = 0.0
        total_weight_used = 0.0

        components = {}
        for name, signal in signals.items():
            if signal.confidence >= self.min_confidence:
                weight = weights.get(name, 0.0)

                # Weight by both model weight and signal confidence
                effective_weight = weight * signal.confidence
                combined_value += signal.value * effective_weight
                combined_confidence += signal.confidence * weight
                total_weight_used += effective_weight

                components[name] = {
                    "value": signal.value,
                    "confidence": signal.confidence,
                    "weight": weight,
                    "effective_weight": effective_weight,
                    "regime_filter": signal.regime_filter,
                }

        # Normalize combined signal
        if total_weight_used > 0:
            combined_value /= total_weight_used

        return AlphaSignal(
            value=np.clip(combined_value, -1.0, 1.0),
            confidence=min(combined_confidence, 1.0),
            regime_filter=regime.value,
            components={
                "model_signals": components,
                "weights_used": weights,
                "regime": regime.value,
                "total_weight_used": total_weight_used,
            },
            model_name="ensemble",
            timestamp=datetime.now(),
        )

    def _get_thompson_weights(self) -> Dict[str, float]:
        """
        Get weights using Thompson Sampling.

        Samples from Beta distribution for each model
        based on historical success/failure counts.

        Returns:
            Dictionary of model weights
        """
        samples = {}
        for name, params in self.ts_params.items():
            # Sample from Beta distribution
            sample = np.random.beta(params["alpha"], params["beta"])
            samples[name] = sample

        # Convert to weights (softmax-like)
        total = sum(samples.values())
        if total > 0:
            return {k: v / total for k, v in samples.items()}
        return self.default_weights

    def update_thompson_params(self, model_name: str, success: bool, magnitude: float = 1.0):
        """
        Update Thompson Sampling parameters based on outcome.

        Args:
            model_name: Name of model to update
            success: Whether the signal was successful
            magnitude: Magnitude of success/failure (0-1)
        """
        if model_name not in self.ts_params:
            return

        if success:
            self.ts_params[model_name]["alpha"] += magnitude
        else:
            self.ts_params[model_name]["beta"] += magnitude

        # Decay old observations (keep priors from growing too large)
        decay = 0.99
        for name in self.ts_params:
            self.ts_params[name]["alpha"] = max(1.0, self.ts_params[name]["alpha"] * decay)
            self.ts_params[name]["beta"] = max(1.0, self.ts_params[name]["beta"] * decay)

    def record_model_performance(self, model_name: str, pnl: float):
        """
        Record P&L outcome for a model's signal.

        Args:
            model_name: Model name
            pnl: P&L from following the signal
        """
        if model_name in self.model_performance:
            self.model_performance[model_name].append(pnl)

            # Keep last 100 outcomes
            if len(self.model_performance[model_name]) > 100:
                self.model_performance[model_name] = self.model_performance[model_name][-100:]

            # Update Thompson Sampling
            success = pnl > 0
            magnitude = min(abs(pnl) * 10, 1.0)  # Scale P&L to 0-1
            self.update_thompson_params(model_name, success, magnitude)

    def get_model_statistics(self) -> Dict[str, Dict[str, float]]:
        """
        Get performance statistics for each model.

        Returns:
            Dictionary of model stats
        """
        stats = {}
        for name, pnls in self.model_performance.items():
            if pnls:
                wins = sum(1 for p in pnls if p > 0)
                stats[name] = {
                    "total_trades": len(pnls),
                    "win_rate": wins / len(pnls),
                    "avg_pnl": np.mean(pnls),
                    "total_pnl": sum(pnls),
                    "sharpe": np.mean(pnls) / (np.std(pnls) + 1e-8) * np.sqrt(252),
                    "ts_alpha": self.ts_params[name]["alpha"],
                    "ts_beta": self.ts_params[name]["beta"],
                    "ts_mean": self.ts_params[name]["alpha"] / (self.ts_params[name]["alpha"] + self.ts_params[name]["beta"]),
                }
            else:
                stats[name] = {
                    "total_trades": 0,
                    "win_rate": 0.0,
                    "avg_pnl": 0.0,
                    "total_pnl": 0.0,
                    "sharpe": 0.0,
                    "ts_alpha": self.ts_params[name]["alpha"],
                    "ts_beta": self.ts_params[name]["beta"],
                    "ts_mean": 0.5,
                }
        return stats

    def set_regime_weights(self, regime: MarketRegime, weights: Dict[str, float]):
        """
        Set custom weights for a specific regime.

        Args:
            regime: Market regime
            weights: Model weights
        """
        self.regime_weights[regime] = weights

    def get_active_models(self, regime: MarketRegime) -> List[str]:
        """
        Get list of models with non-zero weight for regime.

        Args:
            regime: Market regime

        Returns:
            List of active model names
        """
        weights = self.regime_weights.get(regime, self.default_weights)
        return [name for name, weight in weights.items() if weight > 0]

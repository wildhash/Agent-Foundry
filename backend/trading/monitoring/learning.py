"""
Online Learning and Model Selection

Implements:
- Incremental model updates
- Thompson Sampling for model selection
- Walk-forward validation
- Model promotion/demotion logic
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional, Callable
import numpy as np
import logging

logger = logging.getLogger(__name__)


@dataclass
class ModelRecord:
    """Track record for a model."""
    name: str
    version: str
    is_production: bool
    is_shadow: bool
    created_at: datetime
    last_updated: datetime
    trade_count: int = 0
    total_pnl: float = 0.0
    sharpe_ratio: float = 0.0
    win_rate: float = 0.0
    pnl_history: List[float] = field(default_factory=list)

    # Thompson Sampling parameters
    ts_alpha: float = 1.0
    ts_beta: float = 1.0


class ModelSelector:
    """
    Multi-armed bandit for model selection.

    Uses Thompson Sampling to balance:
    - Exploitation: Use best-performing model
    - Exploration: Try other models to gather data

    Parameters:
        exploration_rate: Base exploration rate
        min_trades_for_selection: Minimum trades before evaluation
        decay_factor: How much to discount older performance
    """

    def __init__(
        self,
        exploration_rate: float = 0.1,
        min_trades_for_selection: int = 20,
        decay_factor: float = 0.99
    ):
        self.exploration_rate = exploration_rate
        self.min_trades_for_selection = min_trades_for_selection
        self.decay_factor = decay_factor

        self.models: Dict[str, ModelRecord] = {}
        self.selection_history: List[Dict] = []

    def register_model(
        self,
        name: str,
        version: str,
        is_production: bool = False,
        is_shadow: bool = True
    ):
        """
        Register a model for selection.

        Args:
            name: Model name
            version: Model version
            is_production: Whether this is the production model
            is_shadow: Whether to run in shadow mode
        """
        self.models[name] = ModelRecord(
            name=name,
            version=version,
            is_production=is_production,
            is_shadow=is_shadow,
            created_at=datetime.now(),
            last_updated=datetime.now()
        )

        logger.info(f"Registered model: {name} v{version} (production={is_production})")

    def record_outcome(
        self,
        model_name: str,
        pnl: float,
        was_correct: bool
    ):
        """
        Record trading outcome for a model.

        Args:
            model_name: Model name
            pnl: Trade P&L
            was_correct: Whether prediction was correct
        """
        if model_name not in self.models:
            return

        record = self.models[model_name]

        # Update statistics
        record.trade_count += 1
        record.total_pnl += pnl
        record.pnl_history.append(pnl)
        record.last_updated = datetime.now()

        # Keep last 100 trades
        if len(record.pnl_history) > 100:
            record.pnl_history = record.pnl_history[-100:]

        # Update derived metrics
        if record.pnl_history:
            wins = sum(1 for p in record.pnl_history if p > 0)
            record.win_rate = wins / len(record.pnl_history)

            if len(record.pnl_history) > 10:
                mean_pnl = np.mean(record.pnl_history)
                std_pnl = np.std(record.pnl_history)
                if std_pnl > 0:
                    record.sharpe_ratio = mean_pnl / std_pnl * np.sqrt(252)

        # Update Thompson Sampling parameters
        magnitude = min(abs(pnl) * 100, 1.0)  # Normalize P&L
        if was_correct:
            record.ts_alpha += magnitude
        else:
            record.ts_beta += magnitude

        # Apply decay
        record.ts_alpha = max(1.0, record.ts_alpha * self.decay_factor)
        record.ts_beta = max(1.0, record.ts_beta * self.decay_factor)

    def select_model(self) -> str:
        """
        Select model using Thompson Sampling.

        Returns:
            Name of selected model
        """
        if not self.models:
            return ""

        # Sample from Beta distribution for each model
        samples = {}
        for name, record in self.models.items():
            if record.trade_count < self.min_trades_for_selection:
                # Encourage exploration for new models
                samples[name] = np.random.beta(1, 1)
            else:
                samples[name] = np.random.beta(record.ts_alpha, record.ts_beta)

        # Select model with highest sample
        selected = max(samples, key=samples.get)

        # Record selection
        self.selection_history.append({
            "timestamp": datetime.now(),
            "selected": selected,
            "samples": samples
        })

        return selected

    def get_model_weights(self) -> Dict[str, float]:
        """
        Get allocation weights for each model.

        Based on expected value (mean of Beta distribution).

        Returns:
            Dictionary of model -> weight
        """
        weights = {}

        for name, record in self.models.items():
            # Expected value of Beta distribution
            ev = record.ts_alpha / (record.ts_alpha + record.ts_beta)
            weights[name] = ev

        # Normalize
        total = sum(weights.values())
        if total > 0:
            weights = {k: v / total for k, v in weights.items()}

        return weights

    def get_leaderboard(self) -> List[Dict]:
        """
        Get model performance leaderboard.

        Returns:
            Sorted list of model stats
        """
        leaderboard = []

        for name, record in self.models.items():
            leaderboard.append({
                "name": name,
                "version": record.version,
                "is_production": record.is_production,
                "trade_count": record.trade_count,
                "total_pnl": record.total_pnl,
                "sharpe_ratio": record.sharpe_ratio,
                "win_rate": record.win_rate,
                "ts_mean": record.ts_alpha / (record.ts_alpha + record.ts_beta)
            })

        # Sort by Sharpe ratio
        return sorted(leaderboard, key=lambda x: x["sharpe_ratio"], reverse=True)


class OnlineLearner:
    """
    Online/incremental model updates.

    Implements:
    - Rolling window retraining
    - Incremental parameter updates
    - Walk-forward validation

    Parameters:
        retrain_frequency_days: How often to retrain
        min_samples_for_retrain: Minimum samples before retrain
        validation_window_days: Walk-forward validation window
    """

    def __init__(
        self,
        retrain_frequency_days: int = 7,
        min_samples_for_retrain: int = 1000,
        validation_window_days: int = 30,
        train_callback: Optional[Callable] = None
    ):
        self.retrain_frequency_days = retrain_frequency_days
        self.min_samples_for_retrain = min_samples_for_retrain
        self.validation_window_days = validation_window_days
        self.train_callback = train_callback

        # Training state
        self.last_retrain: Optional[datetime] = None
        self.samples_since_retrain: int = 0
        self.retrain_history: List[Dict] = []

        # Validation results
        self.validation_results: List[Dict] = []

    def add_sample(
        self,
        features: Dict[str, float],
        target: float,
        prediction: Optional[float] = None
    ):
        """
        Add new training sample.

        Args:
            features: Feature dictionary
            target: Actual target value
            prediction: Model prediction (for tracking error)
        """
        self.samples_since_retrain += 1

    def should_retrain(self) -> bool:
        """
        Check if model should be retrained.

        Returns:
            True if retrain conditions met
        """
        # Check minimum samples
        if self.samples_since_retrain < self.min_samples_for_retrain:
            return False

        # Check time since last retrain
        if self.last_retrain is None:
            return True

        days_since = (datetime.now() - self.last_retrain).days
        return days_since >= self.retrain_frequency_days

    def trigger_retrain(
        self,
        train_data: Dict,
        model_name: str
    ) -> Dict:
        """
        Trigger model retraining.

        Args:
            train_data: Training data
            model_name: Name of model to retrain

        Returns:
            Training result dictionary
        """
        logger.info(f"Triggering retrain for {model_name}")

        result = {
            "model_name": model_name,
            "timestamp": datetime.now(),
            "samples_used": self.samples_since_retrain,
            "status": "completed"
        }

        # Call training callback if provided
        if self.train_callback:
            try:
                train_result = self.train_callback(train_data, model_name)
                result.update(train_result)
            except Exception as e:
                result["status"] = "failed"
                result["error"] = str(e)
                logger.error(f"Retrain failed: {e}")

        # Update state
        self.last_retrain = datetime.now()
        self.samples_since_retrain = 0
        self.retrain_history.append(result)

        return result

    def walk_forward_validate(
        self,
        predictions: List[float],
        actuals: List[float],
        window_size: int = 50
    ) -> Dict:
        """
        Walk-forward validation.

        Evaluates model on rolling out-of-sample windows.

        Args:
            predictions: Model predictions
            actuals: Actual outcomes
            window_size: Size of each validation window

        Returns:
            Validation results
        """
        if len(predictions) != len(actuals):
            raise ValueError("Predictions and actuals must have same length")

        n = len(predictions)
        if n < window_size * 2:
            return {"status": "insufficient_data"}

        # Calculate metrics for each window
        window_metrics = []

        for i in range(0, n - window_size, window_size):
            end = min(i + window_size, n)

            window_preds = np.array(predictions[i:end])
            window_actuals = np.array(actuals[i:end])

            # Direction accuracy
            pred_direction = np.sign(window_preds)
            actual_direction = np.sign(window_actuals)
            accuracy = np.mean(pred_direction == actual_direction)

            # MSE
            mse = np.mean((window_preds - window_actuals) ** 2)

            # Correlation
            if np.std(window_preds) > 0 and np.std(window_actuals) > 0:
                corr = np.corrcoef(window_preds, window_actuals)[0, 1]
            else:
                corr = 0.0

            window_metrics.append({
                "window_start": i,
                "accuracy": accuracy,
                "mse": mse,
                "correlation": corr
            })

        # Aggregate
        result = {
            "status": "completed",
            "num_windows": len(window_metrics),
            "avg_accuracy": np.mean([w["accuracy"] for w in window_metrics]),
            "avg_mse": np.mean([w["mse"] for w in window_metrics]),
            "avg_correlation": np.mean([w["correlation"] for w in window_metrics]),
            "accuracy_trend": self._calculate_trend(
                [w["accuracy"] for w in window_metrics]
            ),
            "window_details": window_metrics
        }

        self.validation_results.append(result)
        return result

    def _calculate_trend(self, values: List[float]) -> str:
        """Calculate trend in metric series."""
        if len(values) < 3:
            return "insufficient_data"

        # Simple linear regression slope
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]

        if slope > 0.01:
            return "improving"
        elif slope < -0.01:
            return "degrading"
        else:
            return "stable"

    def should_promote_model(
        self,
        candidate_sharpe: float,
        production_sharpe: float,
        min_improvement: float = 0.2
    ) -> bool:
        """
        Decide if candidate should replace production.

        Args:
            candidate_sharpe: Candidate model Sharpe ratio
            production_sharpe: Production model Sharpe ratio
            min_improvement: Required improvement to promote

        Returns:
            True if candidate should be promoted
        """
        if production_sharpe <= 0:
            return candidate_sharpe > 0.5  # Minimum bar

        improvement = (candidate_sharpe - production_sharpe) / production_sharpe
        return improvement >= min_improvement

    def should_demote_model(
        self,
        current_sharpe: float,
        historical_sharpe: float,
        min_sharpe: float = 0.5,
        max_degradation: float = 0.3
    ) -> bool:
        """
        Decide if model should be demoted from production.

        Args:
            current_sharpe: Current rolling Sharpe
            historical_sharpe: Historical average Sharpe
            min_sharpe: Minimum acceptable Sharpe
            max_degradation: Maximum acceptable degradation

        Returns:
            True if model should be demoted
        """
        # Below minimum threshold
        if current_sharpe < min_sharpe:
            return True

        # Significant degradation from historical
        if historical_sharpe > 0:
            degradation = (historical_sharpe - current_sharpe) / historical_sharpe
            if degradation >= max_degradation:
                return True

        return False

    def get_learning_summary(self) -> Dict:
        """Get summary of learning state."""
        return {
            "last_retrain": self.last_retrain.isoformat() if self.last_retrain else None,
            "samples_since_retrain": self.samples_since_retrain,
            "total_retrains": len(self.retrain_history),
            "validation_runs": len(self.validation_results),
            "should_retrain": self.should_retrain()
        }

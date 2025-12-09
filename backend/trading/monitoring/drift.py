"""
Drift Detection

Monitors for concept drift and distribution shifts
that may indicate model degradation.
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import numpy as np
from scipy import stats


@dataclass
class DriftResult:
    """Result of drift detection test."""
    feature_name: str
    test_type: str
    statistic: float
    p_value: float
    drift_detected: bool
    severity: str  # low, medium, high
    timestamp: datetime


class DriftDetector:
    """
    Detects concept drift in features and predictions.
    
    Methods:
    - KS Test: Compare feature distributions
    - PSI: Population Stability Index
    - Prediction Error Drift: Monitor error distribution
    
    Parameters:
        window_size: Reference window size
        p_value_threshold: Threshold for drift detection
        psi_threshold: PSI threshold for drift
    """
    
    def __init__(
        self,
        window_size: int = 1000,
        p_value_threshold: float = 0.05,
        psi_threshold: float = 0.25
    ):
        self.window_size = window_size
        self.p_value_threshold = p_value_threshold
        self.psi_threshold = psi_threshold
        
        # Reference distributions
        self.reference_data: Dict[str, np.ndarray] = {}
        
        # Drift history
        self.drift_history: List[DriftResult] = []
    
    def set_reference(
        self,
        feature_name: str,
        data: np.ndarray
    ):
        """
        Set reference distribution for a feature.
        
        Args:
            feature_name: Feature name
            data: Reference data array
        """
        self.reference_data[feature_name] = np.array(data[-self.window_size:])
    
    def test_ks(
        self,
        feature_name: str,
        current_data: np.ndarray
    ) -> DriftResult:
        """
        Kolmogorov-Smirnov test for distribution shift.
        
        Compares current distribution to reference.
        
        Args:
            feature_name: Feature name
            current_data: Current data array
            
        Returns:
            DriftResult with test outcome
        """
        if feature_name not in self.reference_data:
            return DriftResult(
                feature_name=feature_name,
                test_type="ks",
                statistic=0.0,
                p_value=1.0,
                drift_detected=False,
                severity="none",
                timestamp=datetime.now()
            )
        
        reference = self.reference_data[feature_name]
        
        # Two-sample KS test
        statistic, p_value = stats.ks_2samp(reference, current_data)
        
        # Determine drift
        drift_detected = p_value < self.p_value_threshold
        
        # Severity based on statistic magnitude
        if statistic > 0.3:
            severity = "high"
        elif statistic > 0.15:
            severity = "medium"
        elif drift_detected:
            severity = "low"
        else:
            severity = "none"
        
        result = DriftResult(
            feature_name=feature_name,
            test_type="ks",
            statistic=statistic,
            p_value=p_value,
            drift_detected=drift_detected,
            severity=severity,
            timestamp=datetime.now()
        )
        
        self.drift_history.append(result)
        return result
    
    def test_psi(
        self,
        feature_name: str,
        current_data: np.ndarray,
        n_bins: int = 10
    ) -> DriftResult:
        """
        Population Stability Index test.
        
        PSI = Σ (actual% - expected%) * ln(actual% / expected%)
        
        PSI < 0.1: No significant change
        0.1 <= PSI < 0.25: Moderate change
        PSI >= 0.25: Significant change
        
        Args:
            feature_name: Feature name
            current_data: Current data array
            n_bins: Number of bins
            
        Returns:
            DriftResult with PSI outcome
        """
        if feature_name not in self.reference_data:
            return DriftResult(
                feature_name=feature_name,
                test_type="psi",
                statistic=0.0,
                p_value=1.0,
                drift_detected=False,
                severity="none",
                timestamp=datetime.now()
            )
        
        reference = self.reference_data[feature_name]
        
        # Create bins from reference data
        bin_edges = np.percentile(
            reference,
            np.linspace(0, 100, n_bins + 1)
        )
        bin_edges[-1] = np.inf
        bin_edges[0] = -np.inf
        
        # Calculate expected (reference) and actual (current) percentages
        expected_counts = np.histogram(reference, bins=bin_edges)[0]
        actual_counts = np.histogram(current_data, bins=bin_edges)[0]
        
        expected_pct = expected_counts / len(reference)
        actual_pct = actual_counts / len(current_data)
        
        # Avoid division by zero
        expected_pct = np.clip(expected_pct, 0.0001, 1)
        actual_pct = np.clip(actual_pct, 0.0001, 1)
        
        # Calculate PSI
        psi = np.sum(
            (actual_pct - expected_pct) * np.log(actual_pct / expected_pct)
        )
        
        # Determine drift
        drift_detected = psi >= self.psi_threshold
        
        if psi >= 0.25:
            severity = "high"
        elif psi >= 0.1:
            severity = "medium"
        elif psi >= 0.05:
            severity = "low"
        else:
            severity = "none"
        
        result = DriftResult(
            feature_name=feature_name,
            test_type="psi",
            statistic=psi,
            p_value=1.0 - psi,  # Pseudo p-value
            drift_detected=drift_detected,
            severity=severity,
            timestamp=datetime.now()
        )
        
        self.drift_history.append(result)
        return result
    
    def test_prediction_drift(
        self,
        predictions: np.ndarray,
        actuals: np.ndarray,
        reference_errors: Optional[np.ndarray] = None
    ) -> DriftResult:
        """
        Test for drift in prediction errors.
        
        Args:
            predictions: Model predictions
            actuals: Actual outcomes
            reference_errors: Reference error distribution
            
        Returns:
            DriftResult for prediction drift
        """
        # Calculate current errors
        current_errors = predictions - actuals
        
        if reference_errors is None:
            if "prediction_errors" not in self.reference_data:
                # Store as reference
                self.set_reference("prediction_errors", current_errors)
                return DriftResult(
                    feature_name="prediction_errors",
                    test_type="error_drift",
                    statistic=0.0,
                    p_value=1.0,
                    drift_detected=False,
                    severity="none",
                    timestamp=datetime.now()
                )
            reference_errors = self.reference_data["prediction_errors"]
        
        # KS test on error distributions
        result = self.test_ks("prediction_errors", current_errors)
        result.test_type = "error_drift"
        
        return result
    
    def test_all_features(
        self,
        current_features: Dict[str, np.ndarray]
    ) -> Dict[str, DriftResult]:
        """
        Test all features for drift.
        
        Args:
            current_features: Dictionary of feature -> data
            
        Returns:
            Dictionary of feature -> DriftResult
        """
        results = {}
        
        for name, data in current_features.items():
            # Run both KS and PSI tests
            ks_result = self.test_ks(name, data)
            psi_result = self.test_psi(name, data)
            
            # Use the more severe result
            if psi_result.drift_detected or ks_result.drift_detected:
                if psi_result.statistic > ks_result.statistic:
                    results[name] = psi_result
                else:
                    results[name] = ks_result
            else:
                results[name] = ks_result
        
        return results
    
    def get_drift_summary(self) -> Dict:
        """
        Get summary of recent drift detections.
        
        Returns:
            Summary dictionary
        """
        if not self.drift_history:
            return {"status": "no_drift_tests"}
        
        recent = self.drift_history[-100:]  # Last 100 tests
        
        drifting = [r for r in recent if r.drift_detected]
        
        by_severity = {
            "high": [r for r in drifting if r.severity == "high"],
            "medium": [r for r in drifting if r.severity == "medium"],
            "low": [r for r in drifting if r.severity == "low"]
        }
        
        return {
            "total_tests": len(recent),
            "drift_detected": len(drifting),
            "drift_rate": len(drifting) / len(recent),
            "high_severity": len(by_severity["high"]),
            "medium_severity": len(by_severity["medium"]),
            "low_severity": len(by_severity["low"]),
            "drifting_features": list(set(r.feature_name for r in drifting))
        }
    
    def should_retrain(self, threshold: float = 0.3) -> bool:
        """
        Determine if model should be retrained based on drift.
        
        Args:
            threshold: Drift rate threshold for retraining
            
        Returns:
            True if retraining recommended
        """
        summary = self.get_drift_summary()
        
        if summary.get("status") == "no_drift_tests":
            return False
        
        # Retrain if:
        # 1. Drift rate exceeds threshold
        # 2. Any high severity drift
        if summary["drift_rate"] > threshold:
            return True
        
        if summary["high_severity"] > 0:
            return True
        
        return False

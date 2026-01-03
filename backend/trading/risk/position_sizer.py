"""
Volatility-Targeted Position Sizing

Mathematical Framework:
----------------------
Position size = (σ_target / σ_asset) * signal * risk_budget

This keeps risk constant regardless of asset volatility.
If volatility doubles, position size halves.

Also implements:
- Kelly Criterion (fractional)
- Correlation-aware portfolio sizing
- Maximum position limits
"""

from dataclasses import dataclass
from typing import Dict, Optional
import numpy as np

from ..core import PositionSize, AlphaSignal


@dataclass
class SizingConfig:
    """Configuration for position sizing."""
    target_vol: float = 0.15           # 15% annualized target
    lookback_days: int = 20            # Vol calculation lookback
    max_leverage: float = 2.0          # Maximum leverage
    min_position: float = 0.01         # Minimum position (1%)
    vol_floor: float = 0.05            # Minimum vol assumption
    vol_ceiling: float = 1.0           # Maximum vol assumption
    kelly_fraction: float = 0.5        # Half-Kelly
    max_position_pct: float = 0.20     # Max single position


class VolatilityTargetedSizer:
    """
    Position sizing using volatility targeting.
    
    Core Insight:
    ------------
    Traditional fixed-size positions have variable risk.
    Vol-targeting fixes risk by varying position size.
    
    When vol is high → smaller positions
    When vol is low → larger positions
    
    Formula:
    -------
    position_pct = (target_vol / asset_vol) * signal_strength * risk_budget
    
    Parameters:
        config: SizingConfig with all parameters
    """
    
    def __init__(self, config: Optional[SizingConfig] = None):
        self.config = config or SizingConfig()
    
    def calculate_realized_vol(
        self,
        returns: np.ndarray,
        annualize: bool = True,
        use_ewma: bool = True
    ) -> float:
        """
        Calculate realized volatility from return series.
        
        Uses EWMA for more responsive estimation.
        
        Args:
            returns: Array of returns
            annualize: Whether to annualize
            use_ewma: Use exponentially weighted moving average
            
        Returns:
            Volatility estimate
        """
        if len(returns) < 2:
            return self.config.target_vol  # Default to target
        
        if use_ewma:
            # EWMA volatility (decay ~0.94 for daily data)
            decay = 0.94
            n = len(returns)
            weights = np.array([decay ** i for i in range(n)])
            weights = weights[::-1] / weights.sum()
            
            variance = np.sum(weights * (returns ** 2))
            vol = np.sqrt(variance)
        else:
            # Simple standard deviation
            vol = np.std(returns, ddof=1)
        
        if annualize:
            vol *= np.sqrt(252)
        
        # Apply floor and ceiling
        vol = np.clip(vol, self.config.vol_floor, self.config.vol_ceiling)
        
        return vol
    
    def size_position(
        self,
        signal: AlphaSignal,
        asset_vol: float,
        nav: float,
        risk_budget_pct: float = 1.0,
        current_price: float = 1.0
    ) -> PositionSize:
        """
        Calculate position size using volatility targeting.
        
        Mathematical Formula:
        --------------------
        w = (σ_target / σ_asset) * signal * risk_budget
        
        Example:
        -------
        If σ_target = 15%, σ_asset = 30%, signal = 0.5, risk_budget = 100%
        Then: w = (0.15 / 0.30) * 0.5 * 1.0 = 0.25 = 25% of NAV
        
        Args:
            signal: Alpha signal with value in [-1, +1]
            asset_vol: Current asset annualized volatility
            nav: Net Asset Value
            risk_budget_pct: Fraction of NAV to risk (default 100%)
            current_price: Current asset price (for unit calculation)
            
        Returns:
            PositionSize with all sizing information
        """
        # Clamp volatility to reasonable bounds
        asset_vol = np.clip(
            asset_vol,
            self.config.vol_floor,
            self.config.vol_ceiling
        )
        
        # Calculate volatility scalar
        vol_scalar = self.config.target_vol / asset_vol
        
        # Apply signal strength and confidence
        signal_strength = signal.value * signal.confidence
        
        # Calculate raw position percentage
        raw_position_pct = vol_scalar * signal_strength * risk_budget_pct
        
        # Apply leverage constraint
        position_pct = np.clip(
            raw_position_pct,
            -self.config.max_leverage,
            self.config.max_leverage
        )
        
        # Apply single position limit
        position_pct = np.clip(
            position_pct,
            -self.config.max_position_pct,
            self.config.max_position_pct
        )
        
        # Apply minimum position threshold
        if abs(position_pct) < self.config.min_position:
            position_pct = 0.0
        
        # Calculate dollar amount
        dollar_amount = position_pct * nav
        
        # Calculate number of units
        num_units = dollar_amount / current_price if current_price > 0 else 0.0
        
        return PositionSize(
            percent_of_nav=position_pct,
            dollar_amount=dollar_amount,
            num_units=num_units,
            vol_scalar=vol_scalar,
            raw_signal=signal.value,
            capped=abs(raw_position_pct) != abs(position_pct)
        )
    
    def kelly_size(
        self,
        win_rate: float,
        win_loss_ratio: float,
        max_pct: float = 0.25
    ) -> float:
        """
        Calculate position size using Kelly Criterion.
        
        Full Kelly:
        ----------
        f* = (p * b - q) / b
        
        Where:
        - p = win probability
        - q = 1 - p = loss probability
        - b = win/loss ratio
        
        Args:
            win_rate: Historical win rate (0-1)
            win_loss_ratio: Average win / average loss
            max_pct: Maximum position as fraction of capital
            
        Returns:
            Optimal position fraction (using half-Kelly)
        """
        if win_rate <= 0 or win_rate >= 1:
            return 0.0
        if win_loss_ratio <= 0:
            return 0.0
        
        p = win_rate
        q = 1 - p
        b = win_loss_ratio
        
        # Full Kelly
        full_kelly = (p * b - q) / b
        
        if full_kelly <= 0:
            return 0.0
        
        # Apply fraction (typically half-Kelly for safety)
        fractional_kelly = full_kelly * self.config.kelly_fraction
        
        # Cap at maximum
        return min(fractional_kelly, max_pct)
    
    def adjust_for_correlation(
        self,
        positions: Dict[str, PositionSize],
        correlation_matrix: np.ndarray,
        asset_vols: np.ndarray,
        max_portfolio_vol: float = 0.20
    ) -> Dict[str, PositionSize]:
        """
        Scale positions if portfolio volatility exceeds target.
        
        Portfolio Vol:
        -------------
        σ_portfolio = sqrt(w' * Σ * w)
        
        Where Σ is the covariance matrix.
        
        Args:
            positions: Dictionary of symbol -> PositionSize
            correlation_matrix: Correlation matrix (NxN)
            asset_vols: Array of asset volatilities
            max_portfolio_vol: Maximum portfolio volatility
            
        Returns:
            Adjusted positions dictionary
        """
        if not positions:
            return positions
        
        symbols = list(positions.keys())
        n = len(symbols)
        
        # Extract weights
        weights = np.array([positions[s].percent_of_nav for s in symbols])
        
        # Construct covariance matrix
        vol_diag = np.diag(asset_vols[:n])
        cov_matrix = vol_diag @ correlation_matrix[:n, :n] @ vol_diag
        
        # Calculate portfolio volatility
        portfolio_vol = np.sqrt(weights @ cov_matrix @ weights)
        
        # Scale if exceeds max
        if portfolio_vol > max_portfolio_vol:
            scale_factor = max_portfolio_vol / portfolio_vol
            
            for symbol in symbols:
                pos = positions[symbol]
                positions[symbol] = PositionSize(
                    percent_of_nav=pos.percent_of_nav * scale_factor,
                    dollar_amount=pos.dollar_amount * scale_factor,
                    num_units=pos.num_units * scale_factor,
                    vol_scalar=pos.vol_scalar,
                    raw_signal=pos.raw_signal,
                    capped=True
                )
        
        return positions
    
    def calculate_marginal_var(
        self,
        current_positions: Dict[str, float],
        proposed_position: float,
        symbol: str,
        covariance_matrix: np.ndarray,
        symbol_index: int
    ) -> float:
        """
        Calculate marginal Value-at-Risk of adding a position.
        
        Marginal VaR = ∂VaR/∂w_i = (Σ * w)_i / σ_portfolio * VaR
        
        Args:
            current_positions: Current position weights
            proposed_position: Proposed position weight
            symbol: Symbol to add
            covariance_matrix: Portfolio covariance matrix
            symbol_index: Index of symbol in cov matrix
            
        Returns:
            Marginal VaR
        """
        symbols = list(current_positions.keys())
        n = len(symbols)
        
        if n == 0 or symbol_index >= len(covariance_matrix):
            return 0.0
        
        # Current weights
        weights = np.zeros(len(covariance_matrix))
        for i, s in enumerate(symbols):
            weights[i] = current_positions[s]
        
        # Add proposed position
        weights[symbol_index] = proposed_position
        
        # Portfolio volatility
        portfolio_var = weights @ covariance_matrix @ weights
        portfolio_vol = np.sqrt(portfolio_var)
        
        if portfolio_vol < 1e-8:
            return 0.0
        
        # Marginal contribution
        marginal = (covariance_matrix @ weights)[symbol_index] / portfolio_vol
        
        # VaR at 95% confidence (1.645 * sigma)
        return 1.645 * marginal

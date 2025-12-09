"""
Central Risk Manager

Implements multi-layer risk controls:
1. Account-level: Daily loss limits, max drawdown
2. Strategy-level: Rolling Sharpe checks, strategy-specific limits
3. Position-level: Hard stops, volatility-scaled stops

Provides kill switch functionality for emergency shutdown.
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum
import logging
import numpy as np

from ..core import PositionSize, RiskCheckResult

logger = logging.getLogger(__name__)


class RiskViolationType(Enum):
    """Types of risk limit violations."""
    DAILY_LOSS = "daily_loss"
    MAX_DRAWDOWN = "max_drawdown"
    POSITION_SIZE = "position_size"
    SECTOR_EXPOSURE = "sector_exposure"
    CORRELATION_EXPOSURE = "correlation_exposure"
    LEVERAGE = "leverage"
    LIQUIDITY = "liquidity"
    VOLATILITY = "volatility"


@dataclass
class RiskLimits:
    """Risk limit configuration."""
    max_daily_loss_pct: float = 0.02       # 2% daily loss limit
    max_drawdown_pct: float = 0.10         # 10% max drawdown
    max_position_pct: float = 0.20         # 20% max single position
    max_sector_exposure: float = 0.40      # 40% max sector exposure
    max_correlation_exposure: float = 0.60 # 60% max correlated exposure
    max_leverage: float = 2.0              # 2x max leverage
    min_liquidity_ratio: float = 0.01      # Position < 1% of daily volume
    max_vol_position: float = 0.50         # 50% position in high vol


@dataclass
class RiskState:
    """Current risk state tracking."""
    daily_pnl: float = 0.0
    peak_nav: float = 0.0
    current_nav: float = 0.0
    start_of_day_nav: float = 0.0
    total_exposure: float = 0.0
    sector_exposures: Dict[str, float] = field(default_factory=dict)
    kill_switch_active: bool = False
    kill_switch_reason: str = ""
    violations_today: List[RiskViolationType] = field(default_factory=list)


class RiskManager:
    """
    Central risk management with multiple safety layers.
    
    Layers:
    ------
    1. Pre-trade checks: Validate before order submission
    2. Position monitoring: Track open positions
    3. Portfolio monitoring: Track aggregate risk
    4. Kill switch: Emergency shutdown capability
    
    Parameters:
        limits: RiskLimits configuration
    """
    
    def __init__(self, limits: Optional[RiskLimits] = None):
        self.limits = limits or RiskLimits()
        self.state = RiskState()
        self._position_stops: Dict[str, float] = {}
        self._strategy_performance: Dict[str, List[float]] = {}
    
    # ==========================================
    # NAV and P&L Tracking
    # ==========================================
    
    def update_nav(self, nav: float):
        """
        Update NAV and track peak/drawdown.
        
        Args:
            nav: Current Net Asset Value
        """
        self.state.current_nav = nav
        self.state.peak_nav = max(self.state.peak_nav, nav)
        
        # Check drawdown limit
        if self.current_drawdown >= self.limits.max_drawdown_pct:
            self._activate_kill_switch(
                f"Max drawdown exceeded: {self.current_drawdown:.2%}"
            )
    
    def update_pnl(self, pnl: float):
        """
        Update daily P&L.
        
        Args:
            pnl: P&L amount
        """
        self.state.daily_pnl += pnl
        
        # Check daily loss limit
        if self.daily_loss_pct >= self.limits.max_daily_loss_pct:
            self._activate_kill_switch(
                f"Daily loss limit exceeded: {self.daily_loss_pct:.2%}"
            )
    
    def reset_daily_metrics(self):
        """Reset metrics at start of trading day."""
        self.state.daily_pnl = 0.0
        self.state.start_of_day_nav = self.state.current_nav
        self.state.violations_today = []
        
        # Don't reset kill switch - requires manual reset
    
    @property
    def current_drawdown(self) -> float:
        """Current drawdown from peak."""
        if self.state.peak_nav == 0:
            return 0.0
        return (self.state.peak_nav - self.state.current_nav) / self.state.peak_nav
    
    @property
    def daily_loss_pct(self) -> float:
        """Current daily loss percentage."""
        if self.state.start_of_day_nav == 0:
            return 0.0
        if self.state.daily_pnl >= 0:
            return 0.0
        return -self.state.daily_pnl / self.state.start_of_day_nav
    
    # ==========================================
    # Pre-Trade Risk Checks
    # ==========================================
    
    def check_limits(
        self,
        proposed_position: PositionSize,
        symbol: str = "",
        sector: str = "",
        daily_volume: float = 0.0,
        current_vol: float = 0.15
    ) -> RiskCheckResult:
        """
        Comprehensive pre-trade risk check.
        
        Checks:
        1. Kill switch status
        2. Daily loss limit
        3. Drawdown limit
        4. Position size limit
        5. Sector exposure limit
        6. Leverage limit
        7. Liquidity limit
        8. Volatility-adjusted limit
        
        Args:
            proposed_position: Position to check
            symbol: Trading symbol
            sector: Sector/industry
            daily_volume: Average daily dollar volume
            current_vol: Current asset volatility
            
        Returns:
            RiskCheckResult with approval status and violations
        """
        violations = []
        
        # 1. Kill switch
        if self.state.kill_switch_active:
            return RiskCheckResult(
                approved=False,
                violations=[f"KILL_SWITCH: {self.state.kill_switch_reason}"],
                adjusted_position=None,
                risk_score=1.0
            )
        
        # 2. Daily loss limit
        if self.daily_loss_pct >= self.limits.max_daily_loss_pct:
            violations.append(
                f"{RiskViolationType.DAILY_LOSS.value}: "
                f"{self.daily_loss_pct:.2%} >= {self.limits.max_daily_loss_pct:.2%}"
            )
        
        # 3. Drawdown limit
        if self.current_drawdown >= self.limits.max_drawdown_pct:
            violations.append(
                f"{RiskViolationType.MAX_DRAWDOWN.value}: "
                f"{self.current_drawdown:.2%} >= {self.limits.max_drawdown_pct:.2%}"
            )
        
        # 4. Position size limit
        if abs(proposed_position.percent_of_nav) > self.limits.max_position_pct:
            violations.append(
                f"{RiskViolationType.POSITION_SIZE.value}: "
                f"{proposed_position.percent_of_nav:.2%} > {self.limits.max_position_pct:.2%}"
            )
        
        # 5. Sector exposure limit
        if sector:
            current_sector = self.state.sector_exposures.get(sector, 0.0)
            new_sector = current_sector + proposed_position.percent_of_nav
            if abs(new_sector) > self.limits.max_sector_exposure:
                violations.append(
                    f"{RiskViolationType.SECTOR_EXPOSURE.value}: "
                    f"{new_sector:.2%} > {self.limits.max_sector_exposure:.2%}"
                )
        
        # 6. Leverage limit
        new_exposure = self.state.total_exposure + abs(proposed_position.percent_of_nav)
        if new_exposure > self.limits.max_leverage:
            violations.append(
                f"{RiskViolationType.LEVERAGE.value}: "
                f"{new_exposure:.2f}x > {self.limits.max_leverage:.2f}x"
            )
        
        # 7. Liquidity limit
        if daily_volume > 0:
            position_volume_pct = abs(proposed_position.dollar_amount) / daily_volume
            if position_volume_pct > self.limits.min_liquidity_ratio:
                violations.append(
                    f"{RiskViolationType.LIQUIDITY.value}: "
                    f"{position_volume_pct:.2%} > {self.limits.min_liquidity_ratio:.2%} of daily volume"
                )
        
        # 8. Volatility-adjusted limit
        if current_vol > 0.40:  # High vol regime
            effective_limit = self.limits.max_vol_position
            if abs(proposed_position.percent_of_nav) > effective_limit:
                violations.append(
                    f"{RiskViolationType.VOLATILITY.value}: "
                    f"High vol ({current_vol:.0%}) - position {proposed_position.percent_of_nav:.2%} > {effective_limit:.2%}"
                )
        
        # Calculate risk score (0 = no risk, 1 = max risk)
        risk_score = self._calculate_risk_score(proposed_position)
        
        if violations:
            return RiskCheckResult(
                approved=False,
                violations=violations,
                adjusted_position=None,
                risk_score=risk_score
            )
        
        return RiskCheckResult(
            approved=True,
            violations=[],
            adjusted_position=proposed_position,
            risk_score=risk_score
        )
    
    def _calculate_risk_score(self, position: PositionSize) -> float:
        """
        Calculate overall risk score for position.
        
        Args:
            position: Proposed position
            
        Returns:
            Risk score from 0 (low) to 1 (high)
        """
        scores = []
        
        # Position size score
        pos_score = abs(position.percent_of_nav) / self.limits.max_position_pct
        scores.append(min(pos_score, 1.0))
        
        # Daily loss proximity score
        loss_score = self.daily_loss_pct / self.limits.max_daily_loss_pct
        scores.append(min(loss_score, 1.0))
        
        # Drawdown proximity score
        dd_score = self.current_drawdown / self.limits.max_drawdown_pct
        scores.append(min(dd_score, 1.0))
        
        # Leverage score
        leverage_score = self.state.total_exposure / self.limits.max_leverage
        scores.append(min(leverage_score, 1.0))
        
        return np.mean(scores)
    
    # ==========================================
    # Position Scaling
    # ==========================================
    
    def scale_for_risk(
        self,
        position: PositionSize,
        urgency: float = 0.5
    ) -> PositionSize:
        """
        Scale position based on current risk utilization.
        
        As we approach risk limits, gradually reduce position sizes.
        
        Args:
            position: Proposed position
            urgency: How important is this trade (0-1)
                    Higher urgency = less scaling
            
        Returns:
            Scaled position
        """
        # Calculate remaining headroom for each limit
        dd_headroom = max(0, self.limits.max_drawdown_pct - self.current_drawdown)
        dd_ratio = dd_headroom / self.limits.max_drawdown_pct
        
        daily_headroom = max(0, self.limits.max_daily_loss_pct - self.daily_loss_pct)
        daily_ratio = daily_headroom / self.limits.max_daily_loss_pct
        
        # Minimum headroom determines base scale
        base_scale = min(dd_ratio, daily_ratio)
        
        # Apply non-linear scaling (more aggressive reduction near limits)
        # sqrt gives smoother reduction curve
        scale_factor = np.sqrt(base_scale)
        
        # Adjust for urgency (high urgency = less reduction)
        scale_factor = scale_factor ** (1 - 0.5 * urgency)
        
        # Never scale up, only down
        scale_factor = min(scale_factor, 1.0)
        
        return position.scale(scale_factor)
    
    # ==========================================
    # Position-Level Risk
    # ==========================================
    
    def set_stop_loss(
        self,
        symbol: str,
        entry_price: float,
        stop_pct: float = 0.02,
        vol_scaled: bool = True,
        current_vol: float = 0.15
    ):
        """
        Set stop loss for a position.
        
        Args:
            symbol: Trading symbol
            entry_price: Entry price
            stop_pct: Stop loss percentage (default 2%)
            vol_scaled: Scale stop by volatility
            current_vol: Current asset volatility
        """
        if vol_scaled:
            # Scale stop by vol ratio (higher vol = wider stop)
            vol_scale = current_vol / 0.15  # Normalize to 15% baseline
            adjusted_stop_pct = stop_pct * vol_scale
        else:
            adjusted_stop_pct = stop_pct
        
        # Calculate stop price
        stop_price = entry_price * (1 - adjusted_stop_pct)
        self._position_stops[symbol] = stop_price
        
        logger.info(
            f"Set stop for {symbol}: entry={entry_price:.2f}, "
            f"stop={stop_price:.2f} ({adjusted_stop_pct:.2%})"
        )
    
    def check_stop(self, symbol: str, current_price: float) -> bool:
        """
        Check if stop loss is triggered.
        
        Args:
            symbol: Trading symbol
            current_price: Current price
            
        Returns:
            True if stop is triggered
        """
        if symbol not in self._position_stops:
            return False
        
        stop_price = self._position_stops[symbol]
        return current_price <= stop_price
    
    def update_trailing_stop(
        self,
        symbol: str,
        current_price: float,
        trail_pct: float = 0.02
    ):
        """
        Update trailing stop for a position.
        
        Args:
            symbol: Trading symbol
            current_price: Current price
            trail_pct: Trailing distance percentage
        """
        if symbol not in self._position_stops:
            return
        
        # New stop level
        new_stop = current_price * (1 - trail_pct)
        
        # Only update if higher than current stop
        if new_stop > self._position_stops[symbol]:
            self._position_stops[symbol] = new_stop
    
    # ==========================================
    # Strategy-Level Risk
    # ==========================================
    
    def record_strategy_trade(self, strategy: str, pnl: float):
        """
        Record trade outcome for strategy.
        
        Args:
            strategy: Strategy name
            pnl: Trade P&L
        """
        if strategy not in self._strategy_performance:
            self._strategy_performance[strategy] = []
        
        self._strategy_performance[strategy].append(pnl)
        
        # Keep last 50 trades
        if len(self._strategy_performance[strategy]) > 50:
            self._strategy_performance[strategy] = \
                self._strategy_performance[strategy][-50:]
    
    def check_strategy_health(
        self,
        strategy: str,
        min_sharpe: float = 0.5,
        min_trades: int = 10
    ) -> bool:
        """
        Check if strategy is healthy enough to trade.
        
        Args:
            strategy: Strategy name
            min_sharpe: Minimum rolling Sharpe ratio
            min_trades: Minimum trades before checking
            
        Returns:
            True if strategy is healthy
        """
        if strategy not in self._strategy_performance:
            return True  # No history, allow trading
        
        trades = self._strategy_performance[strategy]
        
        if len(trades) < min_trades:
            return True  # Not enough history
        
        # Calculate rolling Sharpe (annualized)
        mean_pnl = np.mean(trades)
        std_pnl = np.std(trades)
        
        if std_pnl < 1e-8:
            return mean_pnl > 0
        
        sharpe = mean_pnl / std_pnl * np.sqrt(252)
        
        return sharpe >= min_sharpe
    
    # ==========================================
    # Kill Switch
    # ==========================================
    
    def _activate_kill_switch(self, reason: str):
        """
        Activate emergency kill switch.
        
        Args:
            reason: Reason for activation
        """
        self.state.kill_switch_active = True
        self.state.kill_switch_reason = reason
        
        logger.critical(f"KILL SWITCH ACTIVATED: {reason}")
        
        # In production: send alerts, close positions, etc.
    
    def reset_kill_switch(self, authorization: str):
        """
        Reset kill switch (requires authorization).
        
        Args:
            authorization: Authorization code
        """
        # In production: verify authorization
        logger.warning(f"Kill switch reset with auth: {authorization}")
        
        self.state.kill_switch_active = False
        self.state.kill_switch_reason = ""
    
    # ==========================================
    # Reporting
    # ==========================================
    
    def get_risk_summary(self) -> Dict:
        """Get current risk summary."""
        return {
            "nav": self.state.current_nav,
            "peak_nav": self.state.peak_nav,
            "current_drawdown": f"{self.current_drawdown:.2%}",
            "max_drawdown_limit": f"{self.limits.max_drawdown_pct:.2%}",
            "daily_pnl": self.state.daily_pnl,
            "daily_loss_pct": f"{self.daily_loss_pct:.2%}",
            "daily_loss_limit": f"{self.limits.max_daily_loss_pct:.2%}",
            "total_exposure": f"{self.state.total_exposure:.2%}",
            "max_leverage": f"{self.limits.max_leverage:.2f}x",
            "kill_switch_active": self.state.kill_switch_active,
            "kill_switch_reason": self.state.kill_switch_reason,
            "violations_today": len(self.state.violations_today)
        }

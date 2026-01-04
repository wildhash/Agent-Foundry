"""
Main Trading System - Living Lab Implementation

Integrates all components into a cohesive trading system:
- Data layer (feature engine)
- Alpha models (momentum, mean-reversion, volatility)
- Risk management (volatility targeting, position sizing)
- Execution engine
- Monitoring and learning

Usage:
------
from trading.trading_system import TradingSystem

# Initialize
system = TradingSystem(
    initial_capital=100000,
    target_volatility=0.15
)

# Add data
system.update_market_data(market_data)

# Run trading loop (single iteration)
decision = system.trading_iteration("BTC-USD")

# Or run continuous loop
await system.run_async()
"""

from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional, Any
import asyncio
import logging
import numpy as np
import pandas as pd

from .core import MarketRegime, AlphaSignal, PositionSize, TradeOrder, MarketData, FeatureSet, DecisionLog, OrderSide
from .alpha_models import MomentumAlphaModel, MeanReversionAlphaModel, VolatilityBreakoutModel, AlphaEnsemble
from .risk import VolatilityTargetedSizer, RiskManager, PortfolioManager
from .features import FeatureEngine
from .execution import ExecutionEngine
from .monitoring import PerformanceTracker, DriftDetector, OnlineLearner, ModelSelector

logger = logging.getLogger(__name__)


@dataclass
class TradingConfig:
    """Trading system configuration."""

    # Capital and risk
    initial_capital: float = 100000.0
    target_volatility: float = 0.15
    max_position_pct: float = 0.20
    max_daily_loss_pct: float = 0.02
    max_drawdown_pct: float = 0.10

    # Execution
    min_trade_interval_seconds: float = 60.0
    max_order_value: float = 50000.0

    # Learning
    enable_online_learning: bool = True
    retrain_frequency_days: int = 7

    # Models
    enable_momentum: bool = True
    enable_mean_reversion: bool = True
    enable_volatility: bool = True


class TradingSystem:
    """
    Main trading system orchestrator.

    The "living lab" implementation that:
    - Always trades
    - Always measures
    - Always updates

    Parameters:
        config: TradingConfig with all settings
    """

    def __init__(self, config: Optional[TradingConfig] = None):
        self.config = config or TradingConfig()

        # Initialize components
        self._init_models()
        self._init_risk()
        self._init_execution()
        self._init_monitoring()

        # State
        self.is_running = False
        self.last_trade_time: Dict[str, datetime] = {}
        self.decision_logs: List[DecisionLog] = []

    def _init_models(self):
        """Initialize alpha models."""
        models = {}

        if self.config.enable_momentum:
            models["momentum"] = MomentumAlphaModel()

        if self.config.enable_mean_reversion:
            models["mean_reversion"] = MeanReversionAlphaModel()

        if self.config.enable_volatility:
            models["volatility_breakout"] = VolatilityBreakoutModel()

        self.alpha_models = models
        self.ensemble = AlphaEnsemble(models)
        self.feature_engine = FeatureEngine()

    def _init_risk(self):
        """Initialize risk management."""
        from .risk.position_sizer import SizingConfig
        from .risk.risk_manager import RiskLimits

        sizing_config = SizingConfig(target_vol=self.config.target_volatility, max_position_pct=self.config.max_position_pct)
        self.position_sizer = VolatilityTargetedSizer(sizing_config)

        risk_limits = RiskLimits(
            max_daily_loss_pct=self.config.max_daily_loss_pct,
            max_drawdown_pct=self.config.max_drawdown_pct,
            max_position_pct=self.config.max_position_pct,
        )
        self.risk_manager = RiskManager(risk_limits)
        self.portfolio = PortfolioManager(self.config.initial_capital)

    def _init_execution(self):
        """Initialize execution engine."""
        self.execution = ExecutionEngine(max_order_value=self.config.max_order_value)

    def _init_monitoring(self):
        """Initialize monitoring and learning."""
        self.performance = PerformanceTracker(initial_capital=self.config.initial_capital)
        self.drift_detector = DriftDetector()
        self.model_selector = ModelSelector()

        if self.config.enable_online_learning:
            self.online_learner = OnlineLearner(retrain_frequency_days=self.config.retrain_frequency_days)
        else:
            self.online_learner = None

        # Register models with selector
        for name in self.alpha_models:
            self.model_selector.register_model(name=name, version="1.0.0", is_production=True, is_shadow=False)

    def update_market_data(self, data: MarketData):
        """
        Update with new market data.

        Args:
            data: MarketData object
        """
        self.feature_engine.update(data)
        self.portfolio.update_price(data.symbol, data.close)

    def update_batch(self, ohlcv: pd.DataFrame, symbol: str):
        """
        Update with batch OHLCV data.

        Args:
            ohlcv: DataFrame with OHLCV
            symbol: Trading symbol
        """
        self.feature_engine.update_batch(ohlcv, symbol)
        if len(ohlcv) > 0:
            self.portfolio.update_price(symbol, ohlcv["close"].iloc[-1])

    def detect_regime(self, features: FeatureSet) -> MarketRegime:
        """
        Detect current market regime from features.

        Args:
            features: Current feature set

        Returns:
            Detected market regime
        """
        vol = features.get("realized_vol_20", 0.15)
        vol_regime = features.get("vol_regime", 1)
        trend_regime = features.get("trend_regime", 0)
        hurst = features.get("hurst", 0.5)

        # Crisis detection (extreme volatility)
        if vol > 0.50:
            return MarketRegime.CRISIS

        # Trend detection
        if trend_regime == 1:
            momentum = features.get("momentum_20", 0)
            if momentum > 0:
                return MarketRegime.TRENDING_UP
            else:
                return MarketRegime.TRENDING_DOWN

        # Mean-reversion detection
        if hurst < 0.45:
            return MarketRegime.MEAN_REVERTING

        # Volatility-based regimes
        if vol_regime == 0:
            return MarketRegime.LOW_VOLATILITY
        elif vol_regime == 2:
            return MarketRegime.HIGH_VOLATILITY

        return MarketRegime.NORMAL

    def trading_iteration(self, symbol: str, force: bool = False) -> Optional[DecisionLog]:
        """
        Run single trading iteration for a symbol.

        Process:
        1. Get latest features
        2. Detect regime
        3. Generate alpha signals
        4. Combine signals (regime-weighted)
        5. Calculate position size (vol-targeted)
        6. Check risk limits
        7. Generate order if passed

        Args:
            symbol: Trading symbol
            force: Force trade even if interval not met

        Returns:
            DecisionLog or None if no action
        """
        # Check trade interval
        if not force and symbol in self.last_trade_time:
            elapsed = (datetime.now() - self.last_trade_time[symbol]).total_seconds()
            if elapsed < self.config.min_trade_interval_seconds:
                return None

        # Get OHLCV data
        ohlcv = self.feature_engine.get_ohlcv(symbol)
        if ohlcv is None or len(ohlcv) < 50:
            logger.warning(f"Insufficient data for {symbol}")
            return None

        # Get features
        features = self.feature_engine.get_features(symbol)

        # Detect regime
        regime = self.detect_regime(features)

        # Generate alpha signals
        signals = {}
        for name, model in self.alpha_models.items():
            signals[name] = model.generate_signal(ohlcv, features)

        # Combine signals
        combined_signal = self.ensemble.generate_combined_signal(ohlcv=ohlcv, regime=regime, features=features)

        # Get current volatility
        current_vol = features.get("ewma_vol", 0.15)
        current_price = ohlcv["close"].iloc[-1]

        # Calculate position size
        target_position = self.position_sizer.size_position(
            signal=combined_signal, asset_vol=current_vol, nav=self.portfolio.nav, current_price=current_price
        )

        # Get current position
        current_pos = self.portfolio.get_position(symbol)
        current_qty = current_pos.quantity if current_pos else 0.0

        # Check risk limits
        risk_check = self.risk_manager.check_limits(proposed_position=target_position, symbol=symbol, current_vol=current_vol)

        # Update NAV tracking
        self.risk_manager.update_nav(self.portfolio.nav)

        order = None
        if risk_check.approved and combined_signal.is_active:
            # Scale position for current risk state
            scaled_position = self.risk_manager.scale_for_risk(target_position, urgency=abs(combined_signal.value))

            # Create order
            order = self.execution.create_order(
                symbol=symbol, target=scaled_position, current_position=current_qty, current_price=current_price, regime=regime
            )

            if order:
                self.last_trade_time[symbol] = datetime.now()

        # Create decision log
        log = DecisionLog(
            timestamp=datetime.now(),
            symbol=symbol,
            features=features.features,
            signals={name: sig for name, sig in signals.items()},
            regime=regime,
            position_before=current_qty,
            position_after=target_position.num_units if risk_check.approved else current_qty,
            order=order,
        )

        self.decision_logs.append(log)

        # Keep last 10000 logs
        if len(self.decision_logs) > 10000:
            self.decision_logs = self.decision_logs[-10000:]

        return log

    def record_fill(self, symbol: str, quantity: float, price: float, side: OrderSide):
        """
        Record a trade fill.

        Args:
            symbol: Trading symbol
            quantity: Filled quantity
            price: Fill price
            side: Order side
        """
        # Update portfolio
        self.portfolio.open_position(symbol, quantity, price, side)

        # Record for performance tracking
        # (P&L will be calculated when position closes)

    def close_position(self, symbol: str, price: float) -> float:
        """
        Close a position and record P&L.

        Args:
            symbol: Trading symbol
            price: Close price

        Returns:
            Realized P&L
        """
        pnl = self.portfolio.close_position(symbol, price)

        # Record P&L
        self.performance.record_trade(pnl)
        self.risk_manager.update_pnl(pnl)

        # Get model that generated the signal
        recent_log = self._find_recent_log(symbol)
        if recent_log:
            # Find best performing signal
            best_model = max(recent_log.signals.items(), key=lambda x: abs(x[1].value))[0]

            # Update model selector
            self.model_selector.record_outcome(model_name=best_model, pnl=pnl, was_correct=pnl > 0)

            # Update ensemble Thompson Sampling
            self.ensemble.record_model_performance(best_model, pnl)

        return pnl

    def _find_recent_log(self, symbol: str, max_age_minutes: int = 60) -> Optional[DecisionLog]:
        """Find recent decision log for symbol."""
        cutoff = datetime.now() - pd.Timedelta(minutes=max_age_minutes)

        for log in reversed(self.decision_logs):
            if log.symbol == symbol and log.timestamp > cutoff:
                return log

        return None

    async def run_async(self, symbols: List[str], interval_seconds: float = 60.0, max_iterations: Optional[int] = None):
        """
        Run continuous trading loop asynchronously.

        Args:
            symbols: List of symbols to trade
            interval_seconds: Loop interval
            max_iterations: Maximum iterations (None = infinite)
        """
        self.is_running = True
        iteration = 0

        logger.info(f"Starting trading loop for {symbols}")

        try:
            while self.is_running:
                if max_iterations and iteration >= max_iterations:
                    break

                for symbol in symbols:
                    try:
                        log = self.trading_iteration(symbol)

                        if log and log.order:
                            logger.info(
                                f"Generated order: {log.order.side.value} "
                                f"{log.order.quantity:.4f} {symbol} "
                                f"(regime={log.regime.value})"
                            )
                    except Exception as e:
                        logger.error(f"Error in trading iteration for {symbol}: {e}")

                # Check for retraining
                if self.online_learner and self.online_learner.should_retrain():
                    logger.info("Triggering model retrain...")
                    # Would call retrain here

                iteration += 1
                await asyncio.sleep(interval_seconds)

        except asyncio.CancelledError:
            logger.info("Trading loop cancelled")
        finally:
            self.is_running = False

    def stop(self):
        """Stop the trading loop."""
        self.is_running = False

    def get_status(self) -> Dict[str, Any]:
        """
        Get current system status.

        Returns:
            Status dictionary
        """
        return {
            "is_running": self.is_running,
            "portfolio": self.portfolio.get_portfolio_stats(),
            "risk": self.risk_manager.get_risk_summary(),
            "performance": {
                "sharpe": self.performance.calculate_sharpe(),
                "sortino": self.performance.calculate_sortino(),
                "max_drawdown": self.performance.max_drawdown,
                "total_trades": len(self.performance.trade_pnls),
            },
            "models": self.model_selector.get_leaderboard(),
            "execution": self.execution.get_statistics(),
            "decisions_logged": len(self.decision_logs),
        }

    def get_model_performance(self) -> Dict[str, Dict]:
        """Get detailed model performance."""
        return self.model_selector.get_leaderboard()

    def export_decision_logs(self) -> List[Dict]:
        """Export decision logs for analysis."""
        return [log.to_dict() for log in self.decision_logs]


# Example usage
def create_example_system() -> TradingSystem:
    """Create example trading system with default config."""
    config = TradingConfig(
        initial_capital=100000.0,
        target_volatility=0.15,
        max_position_pct=0.20,
        max_daily_loss_pct=0.02,
        enable_momentum=True,
        enable_mean_reversion=True,
        enable_volatility=True,
    )

    return TradingSystem(config)

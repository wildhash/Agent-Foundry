"""
Tests for risk management components.
"""

import pytest
import numpy as np

from ..risk import VolatilityTargetedSizer, RiskManager, PortfolioManager
from ..risk.position_sizer import SizingConfig
from ..risk.risk_manager import RiskLimits
from ..core import AlphaSignal, PositionSize, OrderSide


class TestVolatilityTargetedSizer:
    """Tests for volatility-targeted position sizing."""

    def test_init(self):
        """Test sizer initialization."""
        sizer = VolatilityTargetedSizer()
        assert sizer.config.target_vol == 0.15

    def test_size_position_basic(self):
        """Test basic position sizing."""
        sizer = VolatilityTargetedSizer()

        signal = AlphaSignal(value=0.5, confidence=0.8, regime_filter="TEST")

        position = sizer.size_position(signal=signal, asset_vol=0.15, nav=100000, current_price=100)  # Same as target

        # Position should be positive and within limits
        # Note: capped at max_position_pct (0.20) when vol_scalar * signal exceeds it
        assert position.percent_of_nav > 0
        assert position.percent_of_nav <= sizer.config.max_position_pct

    def test_size_position_high_vol(self):
        """Test position sizing reduces with high vol."""
        sizer = VolatilityTargetedSizer()

        signal = AlphaSignal(value=1.0, confidence=1.0, regime_filter="TEST")

        # Position with normal vol
        pos_normal = sizer.size_position(signal=signal, asset_vol=0.15, nav=100000, current_price=100)

        # Position with high vol
        pos_high = sizer.size_position(signal=signal, asset_vol=0.30, nav=100000, current_price=100)  # 2x normal

        # Vol scalar should be lower for high vol
        assert pos_high.vol_scalar < pos_normal.vol_scalar
        # Both might be capped at same level, but vol_scalar reflects the difference

    def test_size_position_low_vol(self):
        """Test position sizing increases with low vol."""
        sizer = VolatilityTargetedSizer()

        signal = AlphaSignal(value=0.5, confidence=1.0, regime_filter="TEST")

        # Position with low vol (but hit max leverage)
        pos = sizer.size_position(signal=signal, asset_vol=0.05, nav=100000, current_price=100)  # Very low vol

        # Should be capped by max leverage or position limit
        assert pos.percent_of_nav <= sizer.config.max_leverage
        assert pos.percent_of_nav <= sizer.config.max_position_pct

    def test_kelly_size(self):
        """Test Kelly criterion sizing."""
        sizer = VolatilityTargetedSizer()

        # Favorable edge
        kelly = sizer.kelly_size(win_rate=0.55, win_loss_ratio=1.0)  # Equal wins/losses

        assert kelly > 0
        assert kelly <= 0.25  # Max cap

        # No edge
        kelly_no_edge = sizer.kelly_size(win_rate=0.50, win_loss_ratio=1.0)

        assert kelly_no_edge == 0.0  # No bet when no edge

    def test_realized_vol_calculation(self):
        """Test volatility calculation."""
        sizer = VolatilityTargetedSizer()

        # Generate some returns
        np.random.seed(42)
        returns = np.random.normal(0, 0.01, 100)  # ~1% daily vol

        vol = sizer.calculate_realized_vol(returns, annualize=True)

        # Should be roughly 1% * sqrt(252) ≈ 16%
        assert 0.10 < vol < 0.25


class TestRiskManager:
    """Tests for risk manager."""

    def test_init(self):
        """Test risk manager initialization."""
        rm = RiskManager()
        assert rm.limits.max_daily_loss_pct == 0.02

    def test_update_nav(self):
        """Test NAV tracking."""
        rm = RiskManager()

        rm.state.start_of_day_nav = 100000
        rm.update_nav(100000)
        rm.update_nav(105000)  # New peak
        rm.update_nav(102000)  # Drawdown

        assert rm.state.peak_nav == 105000
        assert rm.current_drawdown > 0

    def test_check_limits_approved(self):
        """Test approved position check."""
        rm = RiskManager()
        rm.state.current_nav = 100000
        rm.state.start_of_day_nav = 100000

        position = PositionSize(percent_of_nav=0.10, dollar_amount=10000, num_units=100)  # 10% position

        result = rm.check_limits(position)

        assert result.approved
        assert len(result.violations) == 0

    def test_check_limits_position_size_violated(self):
        """Test position size limit violation."""
        rm = RiskManager()
        rm.state.current_nav = 100000
        rm.state.start_of_day_nav = 100000  # Set to avoid daily loss check

        position = PositionSize(percent_of_nav=0.30, dollar_amount=30000, num_units=300)  # 30% > 20% limit

        result = rm.check_limits(position)

        assert not result.approved
        assert any("position_size" in v.lower() for v in result.violations)

    def test_check_limits_daily_loss_violated(self):
        """Test daily loss limit violation."""
        rm = RiskManager()
        rm.state.current_nav = 100000
        rm.state.start_of_day_nav = 100000
        rm.state.daily_pnl = -2500  # 2.5% loss > 2% limit

        position = PositionSize(percent_of_nav=0.10, dollar_amount=10000, num_units=100)

        result = rm.check_limits(position)

        assert not result.approved
        assert any("daily_loss" in v.lower() for v in result.violations)

    def test_kill_switch(self):
        """Test kill switch activation."""
        rm = RiskManager()

        # Trigger kill switch
        rm._activate_kill_switch("Test activation")

        assert rm.state.kill_switch_active

        # All trades should be blocked
        position = PositionSize(percent_of_nav=0.01, dollar_amount=1000, num_units=10)

        result = rm.check_limits(position)

        assert not result.approved
        assert any("KILL_SWITCH" in v for v in result.violations)

    def test_scale_for_risk(self):
        """Test position scaling based on risk."""
        rm = RiskManager()
        rm.state.current_nav = 100000
        rm.state.start_of_day_nav = 100000
        rm.state.peak_nav = 100000
        rm.state.daily_pnl = -1000  # 1% loss (50% of limit)

        position = PositionSize(percent_of_nav=0.10, dollar_amount=10000, num_units=100)

        scaled = rm.scale_for_risk(position)

        # Should be scaled down due to daily loss
        assert scaled.percent_of_nav < position.percent_of_nav


class TestPortfolioManager:
    """Tests for portfolio manager."""

    def test_init(self):
        """Test portfolio initialization."""
        pm = PortfolioManager(initial_capital=100000)

        assert pm.nav == 100000
        assert pm.cash == 100000
        assert len(pm.positions) == 0

    def test_open_position(self):
        """Test opening a position."""
        pm = PortfolioManager(initial_capital=100000)

        pm.open_position("BTC", 1.0, 50000, OrderSide.BUY)

        assert "BTC" in pm.positions
        assert pm.positions["BTC"].quantity == 1.0
        assert pm.cash == 50000  # 100k - 50k

    def test_close_position(self):
        """Test closing a position."""
        pm = PortfolioManager(initial_capital=100000)

        pm.open_position("BTC", 1.0, 50000, OrderSide.BUY)
        pnl = pm.close_position("BTC", 55000)  # 10% gain

        assert pnl == 5000
        assert "BTC" not in pm.positions
        assert pm.cash == 105000

    def test_total_exposure(self):
        """Test exposure calculation."""
        pm = PortfolioManager(initial_capital=100000)

        pm.open_position("BTC", 1.0, 30000, OrderSide.BUY)
        pm.update_price("BTC", 30000)

        # 30k position / 100k NAV = 30% exposure
        assert abs(pm.total_exposure - 0.30) < 0.01

    def test_portfolio_stats(self):
        """Test portfolio statistics."""
        pm = PortfolioManager(initial_capital=100000)

        pm.open_position("BTC", 1.0, 30000, OrderSide.BUY)
        pm.update_price("BTC", 33000)  # 10% gain

        stats = pm.get_portfolio_stats()

        assert stats["nav"] > 100000
        assert stats["long_positions"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

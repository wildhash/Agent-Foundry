"""
Feature Calculators

Individual feature calculation classes.
All calculations are vectorized for performance.
"""

from typing import Dict, Optional
import numpy as np
import pandas as pd


class PriceFeatures:
    """
    Price-based features.

    Includes:
    - Log returns (various horizons)
    - Realized volatility (EWMA and rolling)
    - Price momentum
    - VWAP deviation
    """

    @staticmethod
    def log_returns(prices: np.ndarray, periods: int = 1) -> np.ndarray:
        """
        Calculate log returns.

        r_t = ln(P_t / P_{t-n})

        Args:
            prices: Price array
            periods: Return period

        Returns:
            Log return array
        """
        if len(prices) <= periods:
            return np.zeros(len(prices))

        returns = np.zeros(len(prices))
        returns[periods:] = np.log(prices[periods:] / prices[:-periods])
        return returns

    @staticmethod
    def realized_volatility(returns: np.ndarray, window: int = 20, annualize: bool = True) -> np.ndarray:
        """
        Rolling realized volatility.

        Args:
            returns: Return array
            window: Rolling window
            annualize: Whether to annualize

        Returns:
            Volatility array
        """
        vol = pd.Series(returns).rolling(window).std().values

        if annualize:
            vol *= np.sqrt(252)

        return np.nan_to_num(vol, nan=0.15)

    @staticmethod
    def ewma_volatility(returns: np.ndarray, decay: float = 0.94, annualize: bool = True) -> np.ndarray:
        """
        EWMA volatility (RiskMetrics style).

        σ²_t = λ * σ²_{t-1} + (1-λ) * r²_{t-1}

        Args:
            returns: Return array
            decay: Decay factor (lambda)
            annualize: Whether to annualize

        Returns:
            EWMA vol array
        """
        n = len(returns)
        variance = np.zeros(n)
        variance[0] = returns[0] ** 2 if n > 0 else 0.0001

        for i in range(1, n):
            variance[i] = decay * variance[i - 1] + (1 - decay) * returns[i - 1] ** 2

        vol = np.sqrt(variance)

        if annualize:
            vol *= np.sqrt(252)

        return vol

    @staticmethod
    def momentum(prices: np.ndarray, lookbacks: list = [5, 10, 20, 60]) -> Dict[str, np.ndarray]:
        """
        Price momentum at various horizons.

        Args:
            prices: Price array
            lookbacks: List of lookback periods

        Returns:
            Dictionary of momentum arrays
        """
        result = {}
        for lb in lookbacks:
            if len(prices) > lb:
                mom = np.zeros(len(prices))
                mom[lb:] = (prices[lb:] / prices[:-lb]) - 1
                result[f"momentum_{lb}"] = mom
            else:
                result[f"momentum_{lb}"] = np.zeros(len(prices))

        return result

    @staticmethod
    def vwap_deviation(prices: np.ndarray, volume: np.ndarray, window: int = 20) -> np.ndarray:
        """
        Deviation from VWAP as percentage.

        VWAP = Σ(P_i * V_i) / Σ(V_i)
        Deviation = (P - VWAP) / VWAP

        Args:
            prices: Price array
            volume: Volume array
            window: Rolling window

        Returns:
            VWAP deviation array
        """
        n = len(prices)
        deviation = np.zeros(n)

        for i in range(window, n):
            p = prices[i - window : i]
            v = volume[i - window : i]

            if v.sum() > 0:
                vwap = (p * v).sum() / v.sum()
                deviation[i] = (prices[i] - vwap) / vwap if vwap > 0 else 0

        return deviation


class VolumeFeatures:
    """
    Volume-based features.

    Includes:
    - Volume ratio (vs average)
    - Volume trend
    - Dollar volume
    - Order book imbalance (if available)
    """

    @staticmethod
    def volume_ratio(volume: np.ndarray, window: int = 20) -> np.ndarray:
        """
        Volume relative to rolling average.

        Args:
            volume: Volume array
            window: Average window

        Returns:
            Volume ratio array
        """
        avg_volume = pd.Series(volume).rolling(window).mean().values
        ratio = np.where(avg_volume > 0, volume / avg_volume, 1.0)
        return np.nan_to_num(ratio, nan=1.0)

    @staticmethod
    def volume_trend(volume: np.ndarray, short_window: int = 5, long_window: int = 20) -> np.ndarray:
        """
        Volume trend (short MA / long MA).

        Args:
            volume: Volume array
            short_window: Short MA period
            long_window: Long MA period

        Returns:
            Volume trend array
        """
        short_ma = pd.Series(volume).rolling(short_window).mean().values
        long_ma = pd.Series(volume).rolling(long_window).mean().values

        trend = np.where(long_ma > 0, short_ma / long_ma - 1, 0.0)
        return np.nan_to_num(trend, nan=0.0)

    @staticmethod
    def dollar_volume(prices: np.ndarray, volume: np.ndarray) -> np.ndarray:
        """Dollar volume (price * volume)."""
        return prices * volume

    @staticmethod
    def order_book_imbalance(bid_size: np.ndarray, ask_size: np.ndarray) -> np.ndarray:
        """
        Order book imbalance.

        Imbalance = (Bid - Ask) / (Bid + Ask)
        Range: [-1, +1]

        Args:
            bid_size: Bid queue size
            ask_size: Ask queue size

        Returns:
            Imbalance array
        """
        total = bid_size + ask_size
        imbalance = np.where(total > 0, (bid_size - ask_size) / total, 0.0)
        return imbalance


class TechnicalFeatures:
    """
    Technical analysis features.

    Includes:
    - RSI (Relative Strength Index)
    - MACD
    - Bollinger Band position
    - ATR (Average True Range)
    """

    @staticmethod
    def rsi(prices: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Relative Strength Index.

        RSI = 100 - 100 / (1 + RS)
        RS = Avg Gain / Avg Loss

        Args:
            prices: Price array
            period: RSI period

        Returns:
            RSI array (0-100)
        """
        n = len(prices)
        if n < period + 1:
            return np.full(n, 50.0)

        # Calculate price changes
        delta = np.diff(prices)

        gains = np.where(delta > 0, delta, 0)
        losses = np.where(delta < 0, -delta, 0)

        # Initial averages
        avg_gain = np.zeros(n - 1)
        avg_loss = np.zeros(n - 1)

        avg_gain[period - 1] = np.mean(gains[:period])
        avg_loss[period - 1] = np.mean(losses[:period])

        # Wilder's smoothing
        for i in range(period, n - 1):
            avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i]) / period
            avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i]) / period

        # RSI calculation
        rs = np.where(avg_loss > 0, avg_gain / avg_loss, 100)
        rsi = 100 - 100 / (1 + rs)

        # Pad to match input length
        result = np.full(n, 50.0)
        result[1:] = rsi

        return result

    @staticmethod
    def macd(prices: np.ndarray, fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, np.ndarray]:
        """
        MACD (Moving Average Convergence Divergence).

        Args:
            prices: Price array
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line period

        Returns:
            Dictionary with macd, signal, histogram
        """

        def ema(data: np.ndarray, period: int) -> np.ndarray:
            alpha = 2 / (period + 1)
            result = np.zeros_like(data)
            result[0] = data[0]
            for i in range(1, len(data)):
                result[i] = alpha * data[i] + (1 - alpha) * result[i - 1]
            return result

        fast_ema = ema(prices, fast)
        slow_ema = ema(prices, slow)

        macd_line = fast_ema - slow_ema
        signal_line = ema(macd_line, signal)
        histogram = macd_line - signal_line

        return {"macd": macd_line, "macd_signal": signal_line, "macd_histogram": histogram}

    @staticmethod
    def bollinger_position(prices: np.ndarray, window: int = 20, num_std: float = 2.0) -> np.ndarray:
        """
        Position within Bollinger Bands.

        Returns value in [-1, +1]:
        -1 = at lower band
         0 = at middle (SMA)
        +1 = at upper band

        Args:
            prices: Price array
            window: SMA window
            num_std: Number of standard deviations

        Returns:
            Band position array
        """
        sma = pd.Series(prices).rolling(window).mean().values
        std = pd.Series(prices).rolling(window).std().values

        # Distance from middle in terms of std devs
        position = np.where(std > 0, (prices - sma) / (num_std * std), 0.0)

        # Clip to [-1, +1]
        return np.clip(np.nan_to_num(position, nan=0.0), -1.0, 1.0)

    @staticmethod
    def atr(high: np.ndarray, low: np.ndarray, close: np.ndarray, period: int = 14) -> np.ndarray:
        """
        Average True Range.

        Args:
            high: High prices
            low: Low prices
            close: Close prices
            period: ATR period

        Returns:
            ATR array
        """
        n = len(high)
        if n < 2:
            return np.zeros(n)

        # True Range
        tr = np.maximum(high[1:] - low[1:], np.maximum(np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))

        # ATR (Wilder's smoothing)
        atr_arr = np.zeros(n)
        if len(tr) >= period:
            atr_arr[period] = np.mean(tr[:period])
            for i in range(period + 1, n):
                atr_arr[i] = (atr_arr[i - 1] * (period - 1) + tr[i - 1]) / period

        return atr_arr


class RegimeFeatures:
    """
    Market regime features.

    Includes:
    - Volatility regime (low/normal/high)
    - Trend regime (trending/ranging)
    - Hurst exponent estimate
    - Liquidity regime
    """

    @staticmethod
    def volatility_regime(
        vol: np.ndarray, low_percentile: float = 25, high_percentile: float = 75, lookback: int = 252
    ) -> np.ndarray:
        """
        Classify volatility regime.

        Returns:
        - 0: Low volatility
        - 1: Normal volatility
        - 2: High volatility

        Args:
            vol: Volatility array
            low_percentile: Low vol threshold percentile
            high_percentile: High vol threshold percentile
            lookback: Lookback for percentile calculation

        Returns:
            Regime labels (0, 1, 2)
        """
        n = len(vol)
        regime = np.ones(n)  # Default to normal

        for i in range(lookback, n):
            historical = vol[i - lookback : i]
            low_thresh = np.percentile(historical, low_percentile)
            high_thresh = np.percentile(historical, high_percentile)

            if vol[i] < low_thresh:
                regime[i] = 0
            elif vol[i] > high_thresh:
                regime[i] = 2

        return regime.astype(int)

    @staticmethod
    def trend_regime(prices: np.ndarray, adx_period: int = 14, adx_threshold: float = 25.0) -> np.ndarray:
        """
        Classify trend regime based on ADX.

        Returns:
        - 0: Ranging/mean-reverting
        - 1: Trending

        Args:
            prices: Price array
            adx_period: ADX calculation period
            adx_threshold: Threshold for trending

        Returns:
            Regime labels (0, 1)
        """
        # Simplified ADX approximation
        n = len(prices)
        regime = np.zeros(n)

        if n < adx_period * 2:
            return regime

        # Use price momentum as proxy for trend strength
        for i in range(adx_period, n):
            window = prices[i - adx_period : i]

            # Directional movement
            returns = np.diff(window) / window[:-1]

            # Trend strength = abs(sum of returns) / sum of abs(returns)
            # Ranges from 0 (choppy) to 1 (pure trend)
            if len(returns) > 0:
                total_return = np.abs(np.sum(returns))
                total_movement = np.sum(np.abs(returns))

                if total_movement > 0:
                    trend_strength = total_return / total_movement
                    regime[i] = 1 if trend_strength > 0.3 else 0

        return regime.astype(int)

    @staticmethod
    def hurst_exponent(prices: np.ndarray, max_lag: int = 100) -> np.ndarray:
        """
        Rolling Hurst exponent estimate.

        H < 0.5: Mean-reverting
        H = 0.5: Random walk
        H > 0.5: Trending

        Args:
            prices: Price array
            max_lag: Maximum lag for R/S analysis

        Returns:
            Hurst exponent array
        """
        n = len(prices)
        hurst = np.full(n, 0.5)  # Default to random walk

        window = min(max_lag * 2, n // 2)

        for i in range(window, n):
            segment = prices[i - window : i]

            # Simplified R/S analysis
            lags = [10, 20, 40]
            lags = [l for l in lags if l < window // 2]

            if len(lags) < 2:
                continue

            rs_values = []
            for lag in lags:
                n_sub = window // lag
                rs_list = []

                for j in range(n_sub):
                    sub = segment[j * lag : (j + 1) * lag]
                    if len(sub) < 2:
                        continue

                    mean = np.mean(sub)
                    cumdev = np.cumsum(sub - mean)
                    r = np.max(cumdev) - np.min(cumdev)
                    s = np.std(sub, ddof=1)

                    if s > 0:
                        rs_list.append(r / s)

                if rs_list:
                    rs_values.append((lag, np.mean(rs_list)))

            if len(rs_values) >= 2:
                log_lags = np.log([x[0] for x in rs_values])
                log_rs = np.log([x[1] for x in rs_values])
                slope, _ = np.polyfit(log_lags, log_rs, 1)
                hurst[i] = np.clip(slope, 0.0, 1.0)

        return hurst

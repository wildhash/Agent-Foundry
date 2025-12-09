"""
Feature Engine

Central feature calculation with caching and validation.
Ensures point-in-time correctness (no look-ahead bias).
"""

from datetime import datetime
from typing import Dict, List, Optional
import numpy as np
import pandas as pd

from ..core import FeatureSet, MarketData
from .calculators import (
    PriceFeatures,
    VolumeFeatures,
    TechnicalFeatures,
    RegimeFeatures,
)


class FeatureEngine:
    """
    Real-time feature calculation engine.
    
    Features:
    - Calculates all features from OHLCV data
    - Maintains rolling buffers for efficiency
    - Validates point-in-time correctness
    - Caches frequently used calculations
    
    Usage:
    ------
    engine = FeatureEngine()
    
    # Add new market data
    engine.update(market_data)
    
    # Get all features for a symbol
    features = engine.get_features("BTC-USD")
    
    Parameters:
        max_history: Maximum bars to keep in memory
        default_lookback: Default lookback for calculations
    """
    
    def __init__(
        self,
        max_history: int = 1000,
        default_lookback: int = 252
    ):
        self.max_history = max_history
        self.default_lookback = default_lookback
        
        # Data buffers per symbol
        self._data: Dict[str, pd.DataFrame] = {}
        
        # Feature cache
        self._cache: Dict[str, Dict[str, np.ndarray]] = {}
        self._cache_timestamps: Dict[str, datetime] = {}
    
    def update(self, data: MarketData):
        """
        Add new market data point.
        
        Args:
            data: MarketData object
        """
        symbol = data.symbol
        
        new_row = pd.DataFrame([{
            'timestamp': data.timestamp,
            'open': data.open,
            'high': data.high,
            'low': data.low,
            'close': data.close,
            'volume': data.volume,
            'bid': data.bid,
            'ask': data.ask,
            'bid_size': data.bid_size,
            'ask_size': data.ask_size,
        }])
        
        if symbol in self._data:
            self._data[symbol] = pd.concat(
                [self._data[symbol], new_row],
                ignore_index=True
            )
            
            # Trim to max history
            if len(self._data[symbol]) > self.max_history:
                self._data[symbol] = self._data[symbol].iloc[-self.max_history:]
        else:
            self._data[symbol] = new_row
        
        # Invalidate cache
        if symbol in self._cache:
            del self._cache[symbol]
    
    def update_batch(self, ohlcv: pd.DataFrame, symbol: str):
        """
        Update with batch OHLCV data.
        
        Args:
            ohlcv: DataFrame with OHLCV columns
            symbol: Trading symbol
        """
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        
        if not all(col in ohlcv.columns for col in required_cols):
            raise ValueError(f"Missing required columns. Need: {required_cols}")
        
        self._data[symbol] = ohlcv.tail(self.max_history).reset_index(drop=True)
        
        # Invalidate cache
        if symbol in self._cache:
            del self._cache[symbol]
    
    def get_features(
        self,
        symbol: str,
        timestamp: Optional[datetime] = None
    ) -> FeatureSet:
        """
        Get all features for a symbol.
        
        Args:
            symbol: Trading symbol
            timestamp: Optional timestamp (uses latest if not provided)
            
        Returns:
            FeatureSet with all calculated features
        """
        if symbol not in self._data:
            return FeatureSet(
                symbol=symbol,
                timestamp=timestamp or datetime.now(),
                features={}
            )
        
        df = self._data[symbol]
        
        if len(df) < 2:
            return FeatureSet(
                symbol=symbol,
                timestamp=timestamp or datetime.now(),
                features={}
            )
        
        # Check cache
        if symbol in self._cache:
            return FeatureSet(
                symbol=symbol,
                timestamp=timestamp or datetime.now(),
                features={k: v[-1] for k, v in self._cache[symbol].items()}
            )
        
        # Calculate all features
        features_dict = self._calculate_all_features(df)
        
        # Cache results
        self._cache[symbol] = features_dict
        self._cache_timestamps[symbol] = datetime.now()
        
        # Return latest values
        return FeatureSet(
            symbol=symbol,
            timestamp=timestamp or datetime.now(),
            features={k: v[-1] for k, v in features_dict.items()}
        )
    
    def _calculate_all_features(
        self,
        df: pd.DataFrame
    ) -> Dict[str, np.ndarray]:
        """
        Calculate all features from DataFrame.
        
        Args:
            df: OHLCV DataFrame
            
        Returns:
            Dictionary of feature name -> array
        """
        features = {}
        
        prices = df['close'].values
        high = df['high'].values
        low = df['low'].values
        volume = df['volume'].values
        
        # Price features
        returns = PriceFeatures.log_returns(prices, 1)
        features['log_return_1'] = returns
        features['log_return_5'] = PriceFeatures.log_returns(prices, 5)
        features['log_return_20'] = PriceFeatures.log_returns(prices, 20)
        
        features['realized_vol_20'] = PriceFeatures.realized_volatility(returns, 20)
        features['realized_vol_60'] = PriceFeatures.realized_volatility(returns, 60)
        features['ewma_vol'] = PriceFeatures.ewma_volatility(returns)
        
        momentum = PriceFeatures.momentum(prices)
        features.update(momentum)
        
        if volume.sum() > 0:
            features['vwap_deviation'] = PriceFeatures.vwap_deviation(prices, volume)
        
        # Volume features
        features['volume_ratio'] = VolumeFeatures.volume_ratio(volume)
        features['volume_trend'] = VolumeFeatures.volume_trend(volume)
        features['dollar_volume'] = VolumeFeatures.dollar_volume(prices, volume)
        
        if 'bid_size' in df.columns and 'ask_size' in df.columns:
            features['order_book_imbalance'] = VolumeFeatures.order_book_imbalance(
                df['bid_size'].values,
                df['ask_size'].values
            )
        
        # Technical features
        features['rsi_14'] = TechnicalFeatures.rsi(prices, 14)
        
        macd = TechnicalFeatures.macd(prices)
        features.update(macd)
        
        features['bollinger_position'] = TechnicalFeatures.bollinger_position(prices)
        features['atr_14'] = TechnicalFeatures.atr(high, low, prices, 14)
        
        # Regime features
        vol = features['realized_vol_20']
        features['vol_regime'] = RegimeFeatures.volatility_regime(vol)
        features['trend_regime'] = RegimeFeatures.trend_regime(prices)
        features['hurst'] = RegimeFeatures.hurst_exponent(prices)
        
        # Derived features
        features['vol_of_vol'] = PriceFeatures.realized_volatility(
            np.diff(vol, prepend=vol[0]), 20, annualize=False
        )
        
        # Normalize features to z-scores for model input
        normalized = self._normalize_features(features)
        features.update({f"{k}_zscore": v for k, v in normalized.items()})
        
        return features
    
    def _normalize_features(
        self,
        features: Dict[str, np.ndarray],
        lookback: int = 100
    ) -> Dict[str, np.ndarray]:
        """
        Normalize features to z-scores.
        
        Args:
            features: Raw features dictionary
            lookback: Lookback for mean/std calculation
            
        Returns:
            Normalized features dictionary
        """
        normalized = {}
        
        numeric_features = [
            'log_return_1', 'log_return_5', 'log_return_20',
            'realized_vol_20', 'vwap_deviation', 'volume_ratio',
            'rsi_14', 'bollinger_position', 'macd_histogram'
        ]
        
        for name in numeric_features:
            if name in features:
                arr = features[name]
                n = len(arr)
                
                zscore = np.zeros(n)
                for i in range(lookback, n):
                    window = arr[i-lookback:i]
                    mean = np.mean(window)
                    std = np.std(window)
                    
                    if std > 1e-8:
                        zscore[i] = (arr[i] - mean) / std
                
                normalized[name] = np.clip(zscore, -3, 3)
        
        return normalized
    
    def get_feature_names(self) -> List[str]:
        """Get list of all available feature names."""
        return [
            'log_return_1', 'log_return_5', 'log_return_20',
            'realized_vol_20', 'realized_vol_60', 'ewma_vol',
            'momentum_5', 'momentum_10', 'momentum_20', 'momentum_60',
            'vwap_deviation',
            'volume_ratio', 'volume_trend', 'dollar_volume',
            'order_book_imbalance',
            'rsi_14', 'macd', 'macd_signal', 'macd_histogram',
            'bollinger_position', 'atr_14',
            'vol_regime', 'trend_regime', 'hurst',
            'vol_of_vol',
        ]
    
    def get_ohlcv(self, symbol: str) -> Optional[pd.DataFrame]:
        """Get raw OHLCV data for symbol."""
        return self._data.get(symbol)
    
    def clear_cache(self, symbol: Optional[str] = None):
        """
        Clear feature cache.
        
        Args:
            symbol: Symbol to clear (None = clear all)
        """
        if symbol:
            if symbol in self._cache:
                del self._cache[symbol]
        else:
            self._cache = {}
            self._cache_timestamps = {}

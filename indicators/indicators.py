"""
Technical Indicators Module
Provides classes for calculating various technical analysis indicators
"""

import pandas as pd
import numpy as np
from typing import Union, Optional, Tuple


class BaseIndicator:
    """Base class for all technical indicators"""
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize indicator with market data
        
        Args:
            data: DataFrame with OHLCV data (open, high, low, close, volume)
        """
        self.data = data.copy()
        self._validate_data()
    
    def _validate_data(self):
        """Validate that required columns exist"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in self.data.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
    
    def calculate(self) -> pd.Series:
        """Calculate the indicator - to be implemented by subclasses"""
        raise NotImplementedError


class SMA(BaseIndicator):
    """Simple Moving Average"""
    
    def __init__(self, data: pd.DataFrame, period: int = 20):
        super().__init__(data)
        self.period = period
    
    def calculate(self) -> pd.Series:
        """Calculate Simple Moving Average"""
        return self.data['close'].rolling(window=self.period).mean()


class EMA(BaseIndicator):
    """Exponential Moving Average"""
    
    def __init__(self, data: pd.DataFrame, period: int = 20):
        super().__init__(data)
        self.period = period
    
    def calculate(self) -> pd.Series:
        """Calculate Exponential Moving Average"""
        return self.data['close'].ewm(span=self.period).mean()


class VWAP(BaseIndicator):
    """Volume Weighted Average Price"""
    
    def __init__(self, data: pd.DataFrame, period: Optional[int] = None):
        super().__init__(data)
        self.period = period
    
    def calculate(self) -> pd.Series:
        """Calculate VWAP"""
        typical_price = (self.data['high'] + self.data['low'] + self.data['close']) / 3
        volume_price = typical_price * self.data['volume']
        
        if self.period:
            # Rolling VWAP
            cumsum_volume_price = volume_price.rolling(window=self.period).sum()
            cumsum_volume = self.data['volume'].rolling(window=self.period).sum()
        else:
            # Cumulative VWAP
            cumsum_volume_price = volume_price.cumsum()
            cumsum_volume = self.data['volume'].cumsum()
        
        return cumsum_volume_price / cumsum_volume


class RSI(BaseIndicator):
    """Relative Strength Index"""
    
    def __init__(self, data: pd.DataFrame, period: int = 14):
        super().__init__(data)
        self.period = period
    
    def calculate(self) -> pd.Series:
        """Calculate RSI"""
        delta = self.data['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


class ATR(BaseIndicator):
    """Average True Range"""
    
    def __init__(self, data: pd.DataFrame, period: int = 14):
        super().__init__(data)
        self.period = period
    
    def calculate(self) -> pd.Series:
        """Calculate Average True Range"""
        high_low = self.data['high'] - self.data['low']
        high_close = np.abs(self.data['high'] - self.data['close'].shift())
        low_close = np.abs(self.data['low'] - self.data['close'].shift())
        
        true_range = np.maximum(high_low, np.maximum(high_close, low_close))
        return true_range.rolling(window=self.period).mean()


class MACD(BaseIndicator):
    """Moving Average Convergence Divergence"""
    
    def __init__(self, data: pd.DataFrame, fast: int = 12, slow: int = 26, signal: int = 9):
        super().__init__(data)
        self.fast = fast
        self.slow = slow
        self.signal = signal
    
    def calculate(self) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate MACD line, signal line, and histogram"""
        ema_fast = self.data['close'].ewm(span=self.fast).mean()
        ema_slow = self.data['close'].ewm(span=self.slow).mean()
        
        macd_line = ema_fast - ema_slow
        signal_line = macd_line.ewm(span=self.signal).mean()
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram


class BollingerBands(BaseIndicator):
    """Bollinger Bands"""
    
    def __init__(self, data: pd.DataFrame, period: int = 20, std_dev: float = 2.0):
        super().__init__(data)
        self.period = period
        self.std_dev = std_dev
    
    def calculate(self) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Calculate upper band, middle band (SMA), and lower band"""
        middle_band = self.data['close'].rolling(window=self.period).mean()
        std = self.data['close'].rolling(window=self.period).std()
        
        upper_band = middle_band + (std * self.std_dev)
        lower_band = middle_band - (std * self.std_dev)
        
        return upper_band, middle_band, lower_band


class Stochastic(BaseIndicator):
    """Stochastic Oscillator"""
    
    def __init__(self, data: pd.DataFrame, k_period: int = 14, d_period: int = 3):
        super().__init__(data)
        self.k_period = k_period
        self.d_period = d_period
    
    def calculate(self) -> Tuple[pd.Series, pd.Series]:
        """Calculate %K and %D lines"""
        lowest_low = self.data['low'].rolling(window=self.k_period).min()
        highest_high = self.data['high'].rolling(window=self.k_period).max()
        
        k_line = 100 * ((self.data['close'] - lowest_low) / (highest_high - lowest_low))
        d_line = k_line.rolling(window=self.d_period).mean()
        
        return k_line, d_line


class VolumeProfile(BaseIndicator):
    """Volume Profile Analysis"""
    
    def __init__(self, data: pd.DataFrame, price_levels: int = 50):
        super().__init__(data)
        self.price_levels = price_levels
    
    def calculate(self) -> pd.DataFrame:
        """Calculate volume profile by price levels"""
        # Create price bins
        price_range = self.data['high'].max() - self.data['low'].min()
        bin_size = price_range / self.price_levels
        
        # Assign each trade to a price bin
        self.data['price_bin'] = pd.cut(
            self.data['close'], 
            bins=self.price_levels, 
            labels=False
        )
        
        # Group by price bin and sum volume
        volume_profile = self.data.groupby('price_bin')['volume'].sum().reset_index()
        volume_profile['price_level'] = (
            self.data['low'].min() + 
            (volume_profile['price_bin'] + 0.5) * bin_size
        )
        
        return volume_profile[['price_level', 'volume']].sort_values('price_level')

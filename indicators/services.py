"""
Technical Indicators Service
Provides easy access to all technical indicators
"""

import pandas as pd
from typing import Dict, Any, Optional
from .indicators import (
    SMA, EMA, VWAP, RSI, ATR, MACD, 
    BollingerBands, Stochastic, VolumeProfile
)


class TechnicalAnalysisService:
    """Service for calculating technical indicators"""
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize with market data
        
        Args:
            data: DataFrame with OHLCV data
        """
        self.data = self._preprocess_data(data)
    
    def _preprocess_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Preprocess data to ensure correct format
        
        Args:
            data: Raw market data
            
        Returns:
            Preprocessed DataFrame
        """
        # Ensure column names are lowercase
        data = data.copy()
        data.columns = data.columns.str.lower()
        
        # Check if we have the required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in data.columns]
        
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Sort by index (assuming it's datetime)
        if not data.index.is_monotonic_increasing:
            data = data.sort_index()
        
        return data
    
    def calculate_all_indicators(self, config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Calculate all available indicators
        
        Args:
            config: Dictionary with indicator parameters
            
        Returns:
            DataFrame with original data + all indicators
        """
        if config is None:
            config = self._get_default_config()
        
        result = self.data.copy()
        
        # Trend indicators
        if config.get('sma', True):
            result['sma_20'] = SMA(self.data, period=20).calculate()
            result['sma_50'] = SMA(self.data, period=50).calculate()
        
        if config.get('ema', True):
            result['ema_20'] = EMA(self.data, period=20).calculate()
            result['ema_50'] = EMA(self.data, period=50).calculate()
        
        if config.get('vwap', True):
            result['vwap'] = VWAP(self.data).calculate()
        
        # Momentum indicators
        if config.get('rsi', True):
            result['rsi'] = RSI(self.data, period=14).calculate()
        
        if config.get('macd', True):
            macd_line, signal_line, histogram = MACD(self.data).calculate()
            result['macd_line'] = macd_line
            result['macd_signal'] = signal_line
            result['macd_histogram'] = histogram
        
        if config.get('stochastic', True):
            k_line, d_line = Stochastic(self.data).calculate()
            result['stoch_k'] = k_line
            result['stoch_d'] = d_line
        
        # Volatility indicators
        if config.get('atr', True):
            result['atr'] = ATR(self.data, period=14).calculate()
        
        if config.get('bollinger_bands', True):
            upper, middle, lower = BollingerBands(self.data).calculate()
            result['bb_upper'] = upper
            result['bb_middle'] = middle
            result['bb_lower'] = lower
        
        return result
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration for indicators"""
        return {
            'sma': True,
            'ema': True,
            'vwap': True,
            'rsi': True,
            'macd': True,
            'stochastic': True,
            'atr': True,
            'bollinger_bands': True
        }
    
    def get_indicator(self, indicator_name: str, **kwargs) -> pd.Series:
        """
        Get a specific indicator
        
        Args:
            indicator_name: Name of the indicator
            **kwargs: Parameters for the indicator
            
        Returns:
            Calculated indicator values
        """
        indicator_map = {
            'sma': SMA,
            'ema': EMA,
            'vwap': VWAP,
            'rsi': RSI,
            'atr': ATR,
            'macd': MACD,
            'bollinger_bands': BollingerBands,
            'stochastic': Stochastic,
            'volume_profile': VolumeProfile
        }
        
        if indicator_name not in indicator_map:
            raise ValueError(f"Unknown indicator: {indicator_name}")
        
        indicator_class = indicator_map[indicator_name]
        indicator = indicator_class(self.data, **kwargs)
        
        return indicator.calculate()
    
    def get_trend_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive trend analysis
        
        Returns:
            Dictionary with trend analysis results
        """
        # Calculate key trend indicators
        sma_20 = SMA(self.data, period=20).calculate()
        sma_50 = SMA(self.data, period=50).calculate()
        ema_20 = EMA(self.data, period=20).calculate()
        
        # Get latest values
        current_price = self.data['close'].iloc[-1]
        current_sma_20 = sma_20.iloc[-1]
        current_sma_50 = sma_50.iloc[-1]
        current_ema_20 = ema_20.iloc[-1]
        
        # Determine trend
        if current_price > current_sma_20 > current_sma_50:
            trend = "Strong Uptrend"
        elif current_price > current_sma_20:
            trend = "Uptrend"
        elif current_price < current_sma_20 < current_sma_50:
            trend = "Strong Downtrend"
        elif current_price < current_sma_20:
            trend = "Downtrend"
        else:
            trend = "Sideways"
        
        return {
            'trend': trend,
            'current_price': current_price,
            'sma_20': current_sma_20,
            'sma_50': current_sma_50,
            'ema_20': current_ema_20,
            'price_vs_sma_20': ((current_price - current_sma_20) / current_sma_20) * 100,
            'price_vs_sma_50': ((current_price - current_sma_50) / current_sma_50) * 100
        }
    
    def get_momentum_analysis(self) -> Dict[str, Any]:
        """
        Get comprehensive momentum analysis
        
        Returns:
            Dictionary with momentum analysis results
        """
        rsi = RSI(self.data, period=14).calculate()
        macd_line, signal_line, histogram = MACD(self.data).calculate()
        
        current_rsi = rsi.iloc[-1]
        current_macd = macd_line.iloc[-1]
        current_signal = signal_line.iloc[-1]
        current_histogram = histogram.iloc[-1]
        
        # RSI interpretation
        if current_rsi > 70:
            rsi_signal = "Overbought"
        elif current_rsi < 30:
            rsi_signal = "Oversold"
        else:
            rsi_signal = "Neutral"
        
        # MACD interpretation
        if current_macd > current_signal:
            macd_signal = "Bullish"
        else:
            macd_signal = "Bearish"
        
        return {
            'rsi': current_rsi,
            'rsi_signal': rsi_signal,
            'macd_line': current_macd,
            'macd_signal_line': current_signal,
            'macd_histogram': current_histogram,
            'macd_signal': macd_signal
        }

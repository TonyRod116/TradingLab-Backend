"""
Advanced Technical Indicators - Integrated from engine_v2.py
"""

import pandas as pd
import numpy as np
from typing import Tuple, Dict, Any


class AdvancedIndicators:
    """Advanced technical indicators integrated from engine_v2.py"""
    
    @staticmethod
    def SMA(series: pd.Series, length: int) -> pd.Series:
        """Simple Moving Average"""
        return series.rolling(length, min_periods=length).mean()

    @staticmethod
    def EMA(series: pd.Series, length: int) -> pd.Series:
        """Exponential Moving Average"""
        return series.ewm(span=length, adjust=False, min_periods=length).mean()

    @staticmethod
    def RSI(series: pd.Series, length: int = 14) -> pd.Series:
        """Relative Strength Index"""
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        roll_up = up.ewm(alpha=1/length, adjust=False).mean()
        roll_down = down.ewm(alpha=1/length, adjust=False).mean()
        rs = roll_up / (roll_down.replace(0, np.nan))
        rsi = 100 - (100 / (1 + rs))
        return rsi.fillna(50)

    @staticmethod
    def ATR(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
        """Average True Range"""
        prev_close = close.shift(1)
        tr = pd.concat([
            (high - low),
            (high - prev_close).abs(),
            (low - prev_close).abs()
        ], axis=1).max(axis=1)
        return tr.ewm(alpha=1/length, adjust=False).mean()

    @staticmethod
    def Bollinger(series: pd.Series, length: int = 20, mult: float = 2.0) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """Bollinger Bands"""
        m = AdvancedIndicators.SMA(series, length)
        sd = series.rolling(length, min_periods=length).std()
        upper = m + mult*sd
        lower = m - mult*sd
        return upper, m, lower

    @staticmethod
    def VWAP(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Volume Weighted Average Price"""
        typical = (high + low + close)/3.0
        cum_vol = volume.cumsum()
        cum_tpv = (typical*volume).cumsum()
        return cum_tpv / cum_vol.replace(0, np.nan)

    @staticmethod
    def CCI(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 20) -> pd.Series:
        """Commodity Channel Index"""
        typical = (high + low + close) / 3
        sma = typical.rolling(length, min_periods=length).mean()
        mad = typical.rolling(length, min_periods=length).apply(lambda x: np.mean(np.abs(x - x.mean())))
        cci = (typical - sma) / (0.015 * mad)
        return cci.fillna(0)

    @staticmethod
    def Stochastic(high: pd.Series, low: pd.Series, close: pd.Series, k_period: int = 14, d_period: int = 3) -> Tuple[pd.Series, pd.Series]:
        """Stochastic Oscillator"""
        lowest_low = low.rolling(k_period, min_periods=k_period).min()
        highest_high = high.rolling(k_period, min_periods=k_period).max()
        k_percent = 100 * (close - lowest_low) / (highest_high - lowest_low)
        d_percent = k_percent.rolling(d_period, min_periods=d_period).mean()
        return k_percent.fillna(50), d_percent.fillna(50)

    @staticmethod
    def Williams_R(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
        """Williams %R"""
        highest_high = high.rolling(length, min_periods=length).max()
        lowest_low = low.rolling(length, min_periods=length).min()
        wr = -100 * (highest_high - close) / (highest_high - lowest_low)
        return wr.fillna(-50)

    @staticmethod
    def OBV(close: pd.Series, volume: pd.Series) -> pd.Series:
        """On Balance Volume"""
        price_change = close.diff()
        obv = np.where(price_change > 0, volume, 
                      np.where(price_change < 0, -volume, 0)).cumsum()
        return pd.Series(obv, index=close.index)

    @staticmethod
    def AD_Line(high: pd.Series, low: pd.Series, close: pd.Series, volume: pd.Series) -> pd.Series:
        """Accumulation/Distribution Line"""
        clv = ((close - low) - (high - close)) / (high - low)
        clv = clv.fillna(0)  # Handle division by zero
        ad = (clv * volume).cumsum()
        return ad

    @staticmethod
    def MACD(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """MACD Indicator"""
        ema_fast = AdvancedIndicators.EMA(close, fast)
        ema_slow = AdvancedIndicators.EMA(close, slow)
        macd_line = ema_fast - ema_slow
        signal_line = AdvancedIndicators.EMA(macd_line, signal)
        histogram = macd_line - signal_line
        return macd_line, signal_line, histogram

    @staticmethod
    def ADX(high: pd.Series, low: pd.Series, close: pd.Series, length: int = 14) -> pd.Series:
        """Average Directional Index"""
        # True Range
        tr = AdvancedIndicators.ATR(high, low, close, 1)
        
        # Directional Movement
        dm_plus = high.diff()
        dm_minus = -low.diff()
        
        dm_plus = dm_plus.where((dm_plus > dm_minus) & (dm_plus > 0), 0)
        dm_minus = dm_minus.where((dm_minus > dm_plus) & (dm_minus > 0), 0)
        
        # Smoothed values
        atr_smooth = tr.ewm(alpha=1/length, adjust=False).mean()
        dm_plus_smooth = dm_plus.ewm(alpha=1/length, adjust=False).mean()
        dm_minus_smooth = dm_minus.ewm(alpha=1/length, adjust=False).mean()
        
        # Directional Indicators
        di_plus = 100 * (dm_plus_smooth / atr_smooth)
        di_minus = 100 * (dm_minus_smooth / atr_smooth)
        
        # ADX
        dx = 100 * abs(di_plus - di_minus) / (di_plus + di_minus)
        adx = dx.ewm(alpha=1/length, adjust=False).mean()
        
        return adx.fillna(0)

    @staticmethod
    def ParabolicSAR(high: pd.Series, low: pd.Series, close: pd.Series, 
                     acceleration: float = 0.02, maximum: float = 0.2) -> pd.Series:
        """Parabolic Stop and Reverse"""
        psar = pd.Series(index=close.index, dtype=float)
        trend = pd.Series(index=close.index, dtype=int)
        af = pd.Series(index=close.index, dtype=float)
        ep = pd.Series(index=close.index, dtype=float)
        
        # Initialize
        psar.iloc[0] = low.iloc[0]
        trend.iloc[0] = 1
        af.iloc[0] = acceleration
        ep.iloc[0] = high.iloc[0]
        
        for i in range(1, len(close)):
            # Update trend
            if trend.iloc[i-1] == 1:  # Uptrend
                if low.iloc[i] <= psar.iloc[i-1]:
                    trend.iloc[i] = -1
                    psar.iloc[i] = ep.iloc[i-1]
                    af.iloc[i] = acceleration
                    ep.iloc[i] = low.iloc[i]
                else:
                    trend.iloc[i] = 1
                    psar.iloc[i] = psar.iloc[i-1] + af.iloc[i-1] * (ep.iloc[i-1] - psar.iloc[i-1])
                    if high.iloc[i] > ep.iloc[i-1]:
                        ep.iloc[i] = high.iloc[i]
                        af.iloc[i] = min(af.iloc[i-1] + acceleration, maximum)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
                        af.iloc[i] = af.iloc[i-1]
            else:  # Downtrend
                if high.iloc[i] >= psar.iloc[i-1]:
                    trend.iloc[i] = 1
                    psar.iloc[i] = ep.iloc[i-1]
                    af.iloc[i] = acceleration
                    ep.iloc[i] = high.iloc[i]
                else:
                    trend.iloc[i] = -1
                    psar.iloc[i] = psar.iloc[i-1] + af.iloc[i-1] * (ep.iloc[i-1] - psar.iloc[i-1])
                    if low.iloc[i] < ep.iloc[i-1]:
                        ep.iloc[i] = low.iloc[i]
                        af.iloc[i] = min(af.iloc[i-1] + acceleration, maximum)
                    else:
                        ep.iloc[i] = ep.iloc[i-1]
                        af.iloc[i] = af.iloc[i-1]
        
        return psar

    @staticmethod
    def Ichimoku(high: pd.Series, low: pd.Series, close: pd.Series, 
                 conversion: int = 9, base: int = 26, leading_span_b: int = 52, 
                 displacement: int = 26) -> Dict[str, pd.Series]:
        """Ichimoku Cloud"""
        # Conversion Line (Tenkan-sen)
        conversion_line = (high.rolling(conversion).max() + low.rolling(conversion).min()) / 2
        
        # Base Line (Kijun-sen)
        base_line = (high.rolling(base).max() + low.rolling(base).min()) / 2
        
        # Leading Span A (Senkou Span A)
        leading_span_a = ((conversion_line + base_line) / 2).shift(displacement)
        
        # Leading Span B (Senkou Span B)
        leading_span_b_line = ((high.rolling(leading_span_b).max() + low.rolling(leading_span_b).min()) / 2).shift(displacement)
        
        # Lagging Span (Chikou Span)
        lagging_span = close.shift(-displacement)
        
        return {
            'conversion_line': conversion_line,
            'base_line': base_line,
            'leading_span_a': leading_span_a,
            'leading_span_b': leading_span_b_line,
            'lagging_span': lagging_span
        }


def compute_advanced_indicator(df: pd.DataFrame, indicator_id: str, params: Dict[str, Any]) -> pd.Series:
    """
    Compute advanced indicator from engine_v2.py
    
    Args:
        df: DataFrame with OHLCV data
        indicator_id: Indicator identifier
        params: Indicator parameters
    
    Returns:
        Computed indicator series
    """
    indicator_id = indicator_id.upper()
    
    # Price data
    if indicator_id == "CLOSE": return df["close"]
    if indicator_id == "OPEN": return df["open"]
    if indicator_id == "HIGH": return df["high"]
    if indicator_id == "LOW": return df["low"]
    if indicator_id == "VOLUME": return df["volume"]
    
    # Basic indicators
    if indicator_id == "SMA": return AdvancedIndicators.SMA(df["close"], int(params.get("length", 20)))
    if indicator_id == "EMA": return AdvancedIndicators.EMA(df["close"], int(params.get("length", 20)))
    if indicator_id == "RSI": return AdvancedIndicators.RSI(df["close"], int(params.get("length", 14)))
    if indicator_id == "ATR": return AdvancedIndicators.ATR(df["high"], df["low"], df["close"], int(params.get("length", 14)))
    
    # Bollinger Bands
    if indicator_id == "BOLLINGER_UPPER":
        u, _, _ = AdvancedIndicators.Bollinger(df["close"], int(params.get("length", 20)), float(params.get("mult", 2.0)))
        return u
    if indicator_id == "BOLLINGER_MIDDLE":
        _, m, _ = AdvancedIndicators.Bollinger(df["close"], int(params.get("length", 20)), float(params.get("mult", 2.0)))
        return m
    if indicator_id == "BOLLINGER_LOWER":
        _, _, l = AdvancedIndicators.Bollinger(df["close"], int(params.get("length", 20)), float(params.get("mult", 2.0)))
        return l
    
    # Volume indicators
    if indicator_id == "VWAP": return AdvancedIndicators.VWAP(df["high"], df["low"], df["close"], df["volume"])
    if indicator_id == "OBV": return AdvancedIndicators.OBV(df["close"], df["volume"])
    if indicator_id == "AD_LINE": return AdvancedIndicators.AD_Line(df["high"], df["low"], df["close"], df["volume"])
    
    # Oscillators
    if indicator_id == "CCI": return AdvancedIndicators.CCI(df["high"], df["low"], df["close"], int(params.get("length", 20)))
    if indicator_id == "WILLIAMS_R": return AdvancedIndicators.Williams_R(df["high"], df["low"], df["close"], int(params.get("length", 14)))
    
    # Stochastic
    if indicator_id == "STOCH_K":
        k, _ = AdvancedIndicators.Stochastic(df["high"], df["low"], df["close"], 
                                           int(params.get("k_period", 14)), int(params.get("d_period", 3)))
        return k
    if indicator_id == "STOCH_D":
        _, d = AdvancedIndicators.Stochastic(df["high"], df["low"], df["close"], 
                                           int(params.get("k_period", 14)), int(params.get("d_period", 3)))
        return d
    
    # MACD
    if indicator_id == "MACD":
        macd, _, _ = AdvancedIndicators.MACD(df["close"], 
                                           int(params.get("fast", 12)), 
                                           int(params.get("slow", 26)), 
                                           int(params.get("signal", 9)))
        return macd
    if indicator_id == "MACD_SIGNAL":
        _, signal, _ = AdvancedIndicators.MACD(df["close"], 
                                             int(params.get("fast", 12)), 
                                             int(params.get("slow", 26)), 
                                             int(params.get("signal", 9)))
        return signal
    if indicator_id == "MACD_HISTOGRAM":
        _, _, histogram = AdvancedIndicators.MACD(df["close"], 
                                                int(params.get("fast", 12)), 
                                                int(params.get("slow", 26)), 
                                                int(params.get("signal", 9)))
        return histogram
    
    # Advanced indicators
    if indicator_id == "ADX": return AdvancedIndicators.ADX(df["high"], df["low"], df["close"], int(params.get("length", 14)))
    if indicator_id == "PARABOLIC_SAR": return AdvancedIndicators.ParabolicSAR(df["high"], df["low"], df["close"], 
                                                                              float(params.get("acceleration", 0.02)), 
                                                                              float(params.get("maximum", 0.2)))
    
    # Ichimoku
    if indicator_id == "ICHIMOKU_CONVERSION":
        ichimoku = AdvancedIndicators.Ichimoku(df["high"], df["low"], df["close"], 
                                              int(params.get("conversion", 9)), 
                                              int(params.get("base", 26)), 
                                              int(params.get("leading_span_b", 52)), 
                                              int(params.get("displacement", 26)))
        return ichimoku['conversion_line']
    if indicator_id == "ICHIMOKU_BASE":
        ichimoku = AdvancedIndicators.Ichimoku(df["high"], df["low"], df["close"], 
                                              int(params.get("conversion", 9)), 
                                              int(params.get("base", 26)), 
                                              int(params.get("leading_span_b", 52)), 
                                              int(params.get("displacement", 26)))
        return ichimoku['base_line']
    if indicator_id == "ICHIMOKU_LEADING_A":
        ichimoku = AdvancedIndicators.Ichimoku(df["high"], df["low"], df["close"], 
                                              int(params.get("conversion", 9)), 
                                              int(params.get("base", 26)), 
                                              int(params.get("leading_span_b", 52)), 
                                              int(params.get("displacement", 26)))
        return ichimoku['leading_span_a']
    if indicator_id == "ICHIMOKU_LEADING_B":
        ichimoku = AdvancedIndicators.Ichimoku(df["high"], df["low"], df["close"], 
                                              int(params.get("conversion", 9)), 
                                              int(params.get("base", 26)), 
                                              int(params.get("leading_span_b", 52)), 
                                              int(params.get("displacement", 26)))
        return ichimoku['leading_span_b']
    if indicator_id == "ICHIMOKU_LAGGING":
        ichimoku = AdvancedIndicators.Ichimoku(df["high"], df["low"], df["close"], 
                                              int(params.get("conversion", 9)), 
                                              int(params.get("base", 26)), 
                                              int(params.get("leading_span_b", 52)), 
                                              int(params.get("displacement", 26)))
        return ichimoku['lagging_span']
    
    raise ValueError(f"Indicador no soportado: {indicator_id}")


def get_available_indicators() -> Dict[str, Dict[str, Any]]:
    """Get list of all available advanced indicators with their parameters"""
    return {
        "SMA": {"params": ["length"], "defaults": {"length": 20}},
        "EMA": {"params": ["length"], "defaults": {"length": 20}},
        "RSI": {"params": ["length"], "defaults": {"length": 14}},
        "ATR": {"params": ["length"], "defaults": {"length": 14}},
        "BOLLINGER_UPPER": {"params": ["length", "mult"], "defaults": {"length": 20, "mult": 2.0}},
        "BOLLINGER_MIDDLE": {"params": ["length", "mult"], "defaults": {"length": 20, "mult": 2.0}},
        "BOLLINGER_LOWER": {"params": ["length", "mult"], "defaults": {"length": 20, "mult": 2.0}},
        "VWAP": {"params": [], "defaults": {}},
        "CCI": {"params": ["length"], "defaults": {"length": 20}},
        "STOCH_K": {"params": ["k_period", "d_period"], "defaults": {"k_period": 14, "d_period": 3}},
        "STOCH_D": {"params": ["k_period", "d_period"], "defaults": {"k_period": 14, "d_period": 3}},
        "WILLIAMS_R": {"params": ["length"], "defaults": {"length": 14}},
        "OBV": {"params": [], "defaults": {}},
        "AD_LINE": {"params": [], "defaults": {}},
        "MACD": {"params": ["fast", "slow", "signal"], "defaults": {"fast": 12, "slow": 26, "signal": 9}},
        "MACD_SIGNAL": {"params": ["fast", "slow", "signal"], "defaults": {"fast": 12, "slow": 26, "signal": 9}},
        "MACD_HISTOGRAM": {"params": ["fast", "slow", "signal"], "defaults": {"fast": 12, "slow": 26, "signal": 9}},
        "ADX": {"params": ["length"], "defaults": {"length": 14}},
        "PARABOLIC_SAR": {"params": ["acceleration", "maximum"], "defaults": {"acceleration": 0.02, "maximum": 0.2}},
        "ICHIMOKU_CONVERSION": {"params": ["conversion", "base", "leading_span_b", "displacement"], 
                              "defaults": {"conversion": 9, "base": 26, "leading_span_b": 52, "displacement": 26}},
        "ICHIMOKU_BASE": {"params": ["conversion", "base", "leading_span_b", "displacement"], 
                         "defaults": {"conversion": 9, "base": 26, "leading_span_b": 52, "displacement": 26}},
        "ICHIMOKU_LEADING_A": {"params": ["conversion", "base", "leading_span_b", "displacement"], 
                              "defaults": {"conversion": 9, "base": 26, "leading_span_b": 52, "displacement": 26}},
        "ICHIMOKU_LEADING_B": {"params": ["conversion", "base", "leading_span_b", "displacement"], 
                              "defaults": {"conversion": 9, "base": 26, "leading_span_b": 52, "displacement": 26}},
        "ICHIMOKU_LAGGING": {"params": ["conversion", "base", "leading_span_b", "displacement"], 
                            "defaults": {"conversion": 9, "base": 26, "leading_span_b": 52, "displacement": 26}},
        "CLOSE": {"params": [], "defaults": {}},
        "OPEN": {"params": [], "defaults": {}},
        "HIGH": {"params": [], "defaults": {}},
        "LOW": {"params": [], "defaults": {}},
        "VOLUME": {"params": [], "defaults": {}}
    }

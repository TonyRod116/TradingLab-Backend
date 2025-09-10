import re
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta


class QuantConnectNaturalLanguageParser:
    """
    Parser that converts natural language strategy descriptions to QuantConnect Python code
    """
    
    def __init__(self):
        # Comprehensive symbol patterns
        self.symbol_patterns = {
            # US Equities
            'spy': 'SPY', 'spdr s&p 500': 'SPY', 's&p 500': 'SPY',
            'qqq': 'QQQ', 'nasdaq 100': 'QQQ',
            'iwm': 'IWM', 'russell 2000': 'IWM',
            'dia': 'DIA', 'dow jones': 'DIA',
            'apple': 'AAPL', 'aapl': 'AAPL',
            'microsoft': 'MSFT', 'msft': 'MSFT',
            'google': 'GOOGL', 'googl': 'GOOGL', 'alphabet': 'GOOGL',
            'amazon': 'AMZN', 'amzn': 'AMZN',
            'tesla': 'TSLA', 'tsla': 'TSLA',
            'meta': 'META', 'facebook': 'META',
            'nvidia': 'NVDA', 'nvda': 'NVDA',
            'netflix': 'NFLX', 'nflx': 'NFLX',
            'uber': 'UBER', 'uber': 'UBER',
            'airbnb': 'ABNB', 'abnb': 'ABNB',
            
            # Forex Major Pairs
            'eur/usd': 'EURUSD', 'eurusd': 'EURUSD', 'euro dollar': 'EURUSD',
            'gbp/usd': 'GBPUSD', 'gbpusd': 'GBPUSD', 'pound dollar': 'GBPUSD',
            'usd/jpy': 'USDJPY', 'usdjpy': 'USDJPY', 'dollar yen': 'USDJPY',
            'usd/chf': 'USDCHF', 'usdchf': 'USDCHF', 'dollar franc': 'USDCHF',
            'aud/usd': 'AUDUSD', 'audusd': 'AUDUSD', 'aussie dollar': 'AUDUSD',
            'usd/cad': 'USDCAD', 'usdcad': 'USDCAD', 'dollar loonie': 'USDCAD',
            'nzd/usd': 'NZDUSD', 'nzdusd': 'NZDUSD', 'kiwi dollar': 'NZDUSD',
            
            # Forex Cross Pairs
            'eur/gbp': 'EURGBP', 'eurgbp': 'EURGBP', 'euro pound': 'EURGBP',
            'eur/jpy': 'EURJPY', 'eurjpy': 'EURJPY', 'euro yen': 'EURJPY',
            'gbp/jpy': 'GBPJPY', 'gbpjpy': 'GBPJPY', 'pound yen': 'GBPJPY',
            'eur/chf': 'EURCHF', 'eurchf': 'EURCHF', 'euro franc': 'EURCHF',
            'gbp/chf': 'GBPCHF', 'gbpchf': 'GBPCHF', 'pound franc': 'GBPCHF',
            'aud/jpy': 'AUDJPY', 'audjpy': 'AUDJPY', 'aussie yen': 'AUDJPY',
            'cad/jpy': 'CADJPY', 'cadjpy': 'CADJPY', 'loonie yen': 'CADJPY',
            
            # Futures
            'es': 'ES', 'e-mini s&p 500': 'ES', 'sp500 futures': 'ES',
            'nq': 'NQ', 'e-mini nasdaq': 'NQ', 'nasdaq futures': 'NQ',
            'ym': 'YM', 'e-mini dow': 'YM', 'dow futures': 'YM',
            'rt': 'RTY', 'e-mini russell': 'RTY', 'russell futures': 'RTY',
            'gc': 'GC', 'gold futures': 'GC', 'gold': 'GC',
            'si': 'SI', 'silver futures': 'SI', 'silver': 'SI',
            'cl': 'CL', 'crude oil': 'CL', 'oil': 'CL', 'wti': 'CL',
            'ng': 'NG', 'natural gas': 'NG', 'gas': 'NG',
            'zb': 'ZB', '30 year treasury': 'ZB', 'bonds': 'ZB',
            'zn': 'ZN', '10 year treasury': 'ZN', 'treasury': 'ZN',
            'zf': 'ZF', '5 year treasury': 'ZF',
            'zt': 'ZT', '2 year treasury': 'ZT',
            
            # Commodities
            'corn': 'ZC', 'wheat': 'ZW', 'soybeans': 'ZS',
            'coffee': 'KC', 'sugar': 'SB', 'cocoa': 'CC',
            'cotton': 'CT', 'lumber': 'LBS', 'orange juice': 'OJ',
            'cattle': 'LC', 'lean hogs': 'LH', 'feeder cattle': 'FC',
            'platinum': 'PL', 'palladium': 'PA', 'copper': 'HG',
            
            # Cryptocurrencies
            'bitcoin': 'BTCUSD', 'btc': 'BTCUSD', 'btc/usd': 'BTCUSD',
            'ethereum': 'ETHUSD', 'eth': 'ETHUSD', 'eth/usd': 'ETHUSD',
            'litecoin': 'LTCUSD', 'ltc': 'LTCUSD', 'ltc/usd': 'LTCUSD',
            'ripple': 'XRPUSD', 'xrp': 'XRPUSD', 'xrp/usd': 'XRPUSD',
            'cardano': 'ADAUSD', 'ada': 'ADAUSD', 'ada/usd': 'ADAUSD',
            'polkadot': 'DOTUSD', 'dot': 'DOTUSD', 'dot/usd': 'DOTUSD',
            'chainlink': 'LINKUSD', 'link': 'LINKUSD', 'link/usd': 'LINKUSD',
            'uniswap': 'UNIUSD', 'uni': 'UNIUSD', 'uni/usd': 'UNIUSD',
            'solana': 'SOLUSD', 'sol': 'SOLUSD', 'sol/usd': 'SOLUSD',
            'avalanche': 'AVAXUSD', 'avax': 'AVAXUSD', 'avax/usd': 'AVAXUSD',
            
            # Crypto Futures
            'btc futures': 'BTC', 'bitcoin futures': 'BTC',
            'eth futures': 'ETH', 'ethereum futures': 'ETH',
            
            # Indices
            'vix': 'VIX', 'volatility index': 'VIX',
            'dxy': 'DXY', 'dollar index': 'DXY',
            'tnx': 'TNX', '10 year yield': 'TNX',
            'fngu': 'FNGU', 'fang': 'FNGU',
            'arkk': 'ARKK', 'ark innovation': 'ARKK',
            'tqqq': 'TQQQ', '3x nasdaq': 'TQQQ',
            'sqqq': 'SQQQ', '3x inverse nasdaq': 'SQQQ',
            'spxl': 'SPXL', '3x sp500': 'SPXL',
            'spxs': 'SPXS', '3x inverse sp500': 'SPXS'
        }
        
        self.indicator_patterns = {
            # Moving Averages
            'sma': 'SimpleMovingAverage', 'simple moving average': 'SimpleMovingAverage',
            'ema': 'ExponentialMovingAverage', 'exponential moving average': 'ExponentialMovingAverage',
            'wma': 'WeightedMovingAverage', 'weighted moving average': 'WeightedMovingAverage',
            'vwma': 'VolumeWeightedAveragePrice', 'vwap': 'VolumeWeightedAveragePrice',
            'hull': 'HullMovingAverage', 'hull moving average': 'HullMovingAverage',
            'kama': 'KaufmanAdaptiveMovingAverage', 'kaufman': 'KaufmanAdaptiveMovingAverage',
            'tema': 'TripleExponentialMovingAverage', 'triple ema': 'TripleExponentialMovingAverage',
            'dema': 'DoubleExponentialMovingAverage', 'double ema': 'DoubleExponentialMovingAverage',
            
            # Oscillators
            'rsi': 'RelativeStrengthIndex', 'relative strength index': 'RelativeStrengthIndex',
            'stoch': 'Stochastic', 'stochastic': 'Stochastic', 'stoch rsi': 'StochasticRSI',
            'williams': 'WilliamsPercentR', 'williams %r': 'WilliamsPercentR', '%r': 'WilliamsPercentR',
            'cci': 'CommodityChannelIndex', 'commodity channel index': 'CommodityChannelIndex',
            'roc': 'RateOfChange', 'rate of change': 'RateOfChange',
            'momentum': 'Momentum', 'mom': 'Momentum',
            'ultimate': 'UltimateOscillator', 'ultimate oscillator': 'UltimateOscillator',
            'awesome': 'AwesomeOscillator', 'awesome oscillator': 'AwesomeOscillator',
            'aroon': 'AroonOscillator', 'aroon oscillator': 'AroonOscillator',
            'aroon up': 'AroonUp', 'aroon down': 'AroonDown',
            'mfi': 'MoneyFlowIndex', 'money flow index': 'MoneyFlowIndex',
            'cmf': 'ChaikinMoneyFlow', 'chaikin money flow': 'ChaikinMoneyFlow',
            'obv': 'OnBalanceVolume', 'on balance volume': 'OnBalanceVolume',
            'ad': 'AccumulationDistribution', 'accumulation distribution': 'AccumulationDistribution',
            'adx': 'AverageDirectionalIndex', 'average directional index': 'AverageDirectionalIndex',
            'di+': 'PlusDirectionalIndicator', 'plus di': 'PlusDirectionalIndicator',
            'di-': 'MinusDirectionalIndicator', 'minus di': 'MinusDirectionalIndicator',
            'dx': 'DirectionalMovementIndex', 'directional movement': 'DirectionalMovementIndex',
            
            # Trend Indicators
            'macd': 'MACD', 'macd line': 'MACD',
            'macd signal': 'MACDSignal', 'macd histogram': 'MACDHistogram',
            'parabolic': 'ParabolicStopAndReverse', 'psar': 'ParabolicStopAndReverse',
            'sar': 'ParabolicStopAndReverse', 'parabolic sar': 'ParabolicStopAndReverse',
            'ichimoku': 'IchimokuKinkoHyo', 'ichimoku cloud': 'IchimokuKinkoHyo',
            'tenkan': 'TenkanSen', 'tenkan sen': 'TenkanSen',
            'kijun': 'KijunSen', 'kijun sen': 'KijunSen',
            'senkou a': 'SenkouSpanA', 'senkou span a': 'SenkouSpanA',
            'senkou b': 'SenkouSpanB', 'senkou span b': 'SenkouSpanB',
            'chikou': 'ChikouSpan', 'chikou span': 'ChikouSpan',
            'supertrend': 'SuperTrend', 'super trend': 'SuperTrend',
            'trix': 'TRIX', 'trix oscillator': 'TRIX',
            'dmi': 'DirectionalMovementIndex', 'directional movement index': 'DirectionalMovementIndex',
            
            # Volatility Indicators
            'bb': 'BollingerBands', 'bollinger': 'BollingerBands', 'bollinger bands': 'BollingerBands',
            'bb upper': 'BollingerBandsUpperBand', 'bb lower': 'BollingerBandsLowerBand',
            'bb middle': 'BollingerBandsMiddleBand', 'bb width': 'BollingerBandsWidth',
            'bb %b': 'BollingerBandsPercentB', 'bb percent b': 'BollingerBandsPercentB',
            'atr': 'AverageTrueRange', 'average true range': 'AverageTrueRange',
            'natr': 'NormalizedAverageTrueRange', 'normalized atr': 'NormalizedAverageTrueRange',
            'keltner': 'KeltnerChannels', 'keltner channels': 'KeltnerChannels',
            'donchian': 'DonchianChannel', 'donchian channel': 'DonchianChannel',
            'dc upper': 'DonchianChannelUpperBand', 'dc lower': 'DonchianChannelLowerBand',
            'dc middle': 'DonchianChannelMiddleBand',
            'regression': 'LinearRegression', 'linear regression': 'LinearRegression',
            'lr slope': 'LinearRegressionSlope', 'lr intercept': 'LinearRegressionIntercept',
            'lr r-squared': 'LinearRegressionRSquared',
            
            # Volume Indicators
            'vwap': 'VolumeWeightedAveragePrice', 'volume weighted average price': 'VolumeWeightedAveragePrice',
            'vwma': 'VolumeWeightedMovingAverage', 'volume weighted moving average': 'VolumeWeightedMovingAverage',
            'vwap upper': 'VolumeWeightedAveragePriceUpperBand', 'vwap lower': 'VolumeWeightedAveragePriceLowerBand',
            'volume': 'Volume', 'vol': 'Volume',
            'volume sma': 'VolumeSMA', 'volume ema': 'VolumeEMA',
            'volume rate of change': 'VolumeRateOfChange', 'volume roc': 'VolumeRateOfChange',
            'ease of movement': 'EaseOfMovement', 'eom': 'EaseOfMovement',
            'force index': 'ForceIndex', 'fi': 'ForceIndex',
            'ease of movement': 'EaseOfMovement', 'eom': 'EaseOfMovement',
            'klinger': 'KlingerVolumeOscillator', 'klinger oscillator': 'KlingerVolumeOscillator',
            'volume oscillator': 'VolumeOscillator', 'vo': 'VolumeOscillator',
            'volume price trend': 'VolumePriceTrend', 'vpt': 'VolumePriceTrend',
            'negative volume index': 'NegativeVolumeIndex', 'nvi': 'NegativeVolumeIndex',
            'positive volume index': 'PositiveVolumeIndex', 'pvi': 'PositiveVolumeIndex',
            
            # Order Flow Indicators (Advanced)
            'order flow': 'OrderFlow', 'of': 'OrderFlow',
            'delta': 'Delta', 'buying pressure': 'Delta',
            'volume delta': 'VolumeDelta', 'vd': 'VolumeDelta',
            'cumulative delta': 'CumulativeDelta', 'cd': 'CumulativeDelta',
            'volume profile': 'VolumeProfile', 'vp': 'VolumeProfile',
            'poc': 'PointOfControl', 'point of control': 'PointOfControl',
            'value area': 'ValueArea', 'va': 'ValueArea',
            'va high': 'ValueAreaHigh', 'va low': 'ValueAreaLow',
            'market profile': 'MarketProfile', 'mp': 'MarketProfile',
            'time price opportunity': 'TimePriceOpportunity', 'tpo': 'TimePriceOpportunity',
            'footprint': 'Footprint', 'order book': 'OrderBook',
            'bid ask spread': 'BidAskSpread', 'spread': 'BidAskSpread',
            'bid volume': 'BidVolume', 'ask volume': 'AskVolume',
            'imbalance': 'Imbalance', 'order imbalance': 'Imbalance',
            
            # Support and Resistance
            'pivot': 'PivotPoints', 'pivot points': 'PivotPoints',
            'pp': 'PivotPoint', 'pivot point': 'PivotPoint',
            'r1': 'Resistance1', 'r2': 'Resistance2', 'r3': 'Resistance3',
            's1': 'Support1', 's2': 'Support2', 's3': 'Support3',
            'fibonacci': 'FibonacciRetracements', 'fib retracements': 'FibonacciRetracements',
            'fib extensions': 'FibonacciExtensions', 'fibonacci extensions': 'FibonacciExtensions',
            'fib fan': 'FibonacciFan', 'fibonacci fan': 'FibonacciFan',
            'fib arcs': 'FibonacciArcs', 'fibonacci arcs': 'FibonacciArcs',
            'fib time zones': 'FibonacciTimeZones', 'fibonacci time zones': 'FibonacciTimeZones',
            
            # Market Structure
            'swing high': 'SwingHigh', 'swing low': 'SwingLow',
            'higher high': 'HigherHigh', 'higher low': 'HigherLow',
            'lower high': 'LowerHigh', 'lower low': 'LowerLow',
            'trend line': 'TrendLine', 'trendline': 'TrendLine',
            'channel': 'PriceChannel', 'price channel': 'PriceChannel',
            'envelope': 'PriceEnvelope', 'price envelope': 'PriceEnvelope',
            'regression channel': 'RegressionChannel', 'linear regression channel': 'RegressionChannel',
            
            # Candlestick Patterns
            'doji': 'Doji', 'hammer': 'Hammer', 'hanging man': 'HangingMan',
            'shooting star': 'ShootingStar', 'inverted hammer': 'InvertedHammer',
            'engulfing': 'Engulfing', 'harami': 'Harami', 'piercing': 'Piercing',
            'dark cloud': 'DarkCloud', 'morning star': 'MorningStar',
            'evening star': 'EveningStar', 'three white soldiers': 'ThreeWhiteSoldiers',
            'three black crows': 'ThreeBlackCrows', 'tweezer': 'Tweezer',
            'inside bar': 'InsideBar', 'outside bar': 'OutsideBar',
            'pin bar': 'PinBar', 'wick': 'Wick',
            
            # Statistical Indicators
            'standard deviation': 'StandardDeviation', 'std dev': 'StandardDeviation',
            'variance': 'Variance', 'skewness': 'Skewness', 'kurtosis': 'Kurtosis',
            'correlation': 'Correlation', 'beta': 'Beta', 'alpha': 'Alpha',
            'sharpe ratio': 'SharpeRatio', 'sortino ratio': 'SortinoRatio',
            'calmar ratio': 'CalmarRatio', 'information ratio': 'InformationRatio',
            'treynor ratio': 'TreynorRatio', 'jensen alpha': 'JensenAlpha',
            
            # Custom Indicators
            'zigzag': 'ZigZag', 'fractal': 'Fractal', 'gator': 'GatorOscillator',
            'alligator': 'Alligator', 'gator oscillator': 'GatorOscillator',
            'fisher': 'FisherTransform', 'fisher transform': 'FisherTransform',
            'inverse fisher': 'InverseFisherTransform', 'inverse fisher transform': 'InverseFisherTransform',
            'mass index': 'MassIndex', 'mass': 'MassIndex',
            'median price': 'MedianPrice', 'typical price': 'TypicalPrice',
            'weighted close': 'WeightedClose', 'heikin ashi': 'HeikinAshi',
            'renko': 'Renko', 'kagi': 'Kagi', 'point and figure': 'PointAndFigure',
            'three line break': 'ThreeLineBreak', 'line break': 'LineBreak'
        }
        
        self.timeframe_patterns = {
            # Standard Timeframes
            'tick': 'Resolution.Tick', 'tick data': 'Resolution.Tick',
            'second': 'Resolution.Second', '1s': 'Resolution.Second', '1 second': 'Resolution.Second',
            'minute': 'Resolution.Minute', '1m': 'Resolution.Minute', '1 minute': 'Resolution.Minute',
            'hour': 'Resolution.Hour', '1h': 'Resolution.Hour', '1 hour': 'Resolution.Hour',
            'daily': 'Resolution.Daily', '1d': 'Resolution.Daily', '1 day': 'Resolution.Daily',
            
            # Custom Timeframes (using TimeSpan)
            '2m': 'TimeSpan.FromMinutes(2)', '2 minutes': 'TimeSpan.FromMinutes(2)',
            '3m': 'TimeSpan.FromMinutes(3)', '3 minutes': 'TimeSpan.FromMinutes(3)',
            '4m': 'TimeSpan.FromMinutes(4)', '4 minutes': 'TimeSpan.FromMinutes(4)',
            '5m': 'TimeSpan.FromMinutes(5)', '5 minutes': 'TimeSpan.FromMinutes(5)',
            '6m': 'TimeSpan.FromMinutes(6)', '6 minutes': 'TimeSpan.FromMinutes(6)',
            '7m': 'TimeSpan.FromMinutes(7)', '7 minutes': 'TimeSpan.FromMinutes(7)',
            '8m': 'TimeSpan.FromMinutes(8)', '8 minutes': 'TimeSpan.FromMinutes(8)',
            '9m': 'TimeSpan.FromMinutes(9)', '9 minutes': 'TimeSpan.FromMinutes(9)',
            '10m': 'TimeSpan.FromMinutes(10)', '10 minutes': 'TimeSpan.FromMinutes(10)',
            '12m': 'TimeSpan.FromMinutes(12)', '12 minutes': 'TimeSpan.FromMinutes(12)',
            '15m': 'TimeSpan.FromMinutes(15)', '15 minutes': 'TimeSpan.FromMinutes(15)',
            '20m': 'TimeSpan.FromMinutes(20)', '20 minutes': 'TimeSpan.FromMinutes(20)',
            '30m': 'TimeSpan.FromMinutes(30)', '30 minutes': 'TimeSpan.FromMinutes(30)',
            '45m': 'TimeSpan.FromMinutes(45)', '45 minutes': 'TimeSpan.FromMinutes(45)',
            
            # Hourly Timeframes
            '2h': 'TimeSpan.FromHours(2)', '2 hours': 'TimeSpan.FromHours(2)',
            '3h': 'TimeSpan.FromHours(3)', '3 hours': 'TimeSpan.FromHours(3)',
            '4h': 'TimeSpan.FromHours(4)', '4 hours': 'TimeSpan.FromHours(4)',
            '6h': 'TimeSpan.FromHours(6)', '6 hours': 'TimeSpan.FromHours(6)',
            '8h': 'TimeSpan.FromHours(8)', '8 hours': 'TimeSpan.FromHours(8)',
            '12h': 'TimeSpan.FromHours(12)', '12 hours': 'TimeSpan.FromHours(12)',
            
            # Daily Timeframes
            '2d': 'TimeSpan.FromDays(2)', '2 days': 'TimeSpan.FromDays(2)',
            '3d': 'TimeSpan.FromDays(3)', '3 days': 'TimeSpan.FromDays(3)',
            'weekly': 'TimeSpan.FromDays(7)', '1w': 'TimeSpan.FromDays(7)', '1 week': 'TimeSpan.FromDays(7)',
            '2w': 'TimeSpan.FromDays(14)', '2 weeks': 'TimeSpan.FromDays(14)',
            'monthly': 'TimeSpan.FromDays(30)', '1m': 'TimeSpan.FromDays(30)', '1 month': 'TimeSpan.FromDays(30)',
            'quarterly': 'TimeSpan.FromDays(90)', '3m': 'TimeSpan.FromDays(90)', '3 months': 'TimeSpan.FromDays(90)',
            'yearly': 'TimeSpan.FromDays(365)', '1y': 'TimeSpan.FromDays(365)', '1 year': 'TimeSpan.FromDays(365)',
            
            # Common Trading Timeframes
            'scalp': 'TimeSpan.FromMinutes(1)', 'scalping': 'TimeSpan.FromMinutes(1)',
            'intraday': 'TimeSpan.FromMinutes(5)', 'day trading': 'TimeSpan.FromMinutes(5)',
            'swing': 'TimeSpan.FromHours(4)', 'swing trading': 'TimeSpan.FromHours(4)',
            'position': 'TimeSpan.FromDays(1)', 'position trading': 'TimeSpan.FromDays(1)',
            'long term': 'TimeSpan.FromDays(7)', 'long-term': 'TimeSpan.FromDays(7)',
            
            # Forex Specific
            'm1': 'TimeSpan.FromMinutes(1)', 'm5': 'TimeSpan.FromMinutes(5)',
            'm15': 'TimeSpan.FromMinutes(15)', 'm30': 'TimeSpan.FromMinutes(30)',
            'h1': 'TimeSpan.FromHours(1)', 'h4': 'TimeSpan.FromHours(4)',
            'd1': 'TimeSpan.FromDays(1)', 'w1': 'TimeSpan.FromDays(7)',
            'mn1': 'TimeSpan.FromDays(30)',
            
            # Crypto Specific
            '1min': 'TimeSpan.FromMinutes(1)', '5min': 'TimeSpan.FromMinutes(5)',
            '15min': 'TimeSpan.FromMinutes(15)', '30min': 'TimeSpan.FromMinutes(30)',
            '1hour': 'TimeSpan.FromHours(1)', '4hour': 'TimeSpan.FromHours(4)',
            '1day': 'TimeSpan.FromDays(1)', '1week': 'TimeSpan.FromDays(7)',
            '1month': 'TimeSpan.FromDays(30)',
            
            # Futures Specific
            '1tick': 'Resolution.Tick', 'tick': 'Resolution.Tick',
            '1sec': 'Resolution.Second', '1min': 'TimeSpan.FromMinutes(1)',
            '5min': 'TimeSpan.FromMinutes(5)', '15min': 'TimeSpan.FromMinutes(15)',
            '30min': 'TimeSpan.FromMinutes(30)', '1hr': 'TimeSpan.FromHours(1)',
            '4hr': 'TimeSpan.FromHours(4)', '1day': 'TimeSpan.FromDays(1)',
            
            # Alternative Names
            'intraday': 'TimeSpan.FromMinutes(5)', 'day trade': 'TimeSpan.FromMinutes(5)',
            'scalping': 'TimeSpan.FromMinutes(1)', 'scalp': 'TimeSpan.FromMinutes(1)',
            'swing trade': 'TimeSpan.FromHours(4)', 'swing': 'TimeSpan.FromHours(4)',
            'position trade': 'TimeSpan.FromDays(1)', 'position': 'TimeSpan.FromDays(1)',
            'long term trade': 'TimeSpan.FromDays(7)', 'long term': 'TimeSpan.FromDays(7)',
            'investing': 'TimeSpan.FromDays(30)', 'investment': 'TimeSpan.FromDays(30)'
        }
        
        self.action_patterns = {
            # Basic Actions
            'buy': 'self.MarketOrder', 'purchase': 'self.MarketOrder', 'go long': 'self.MarketOrder',
            'sell': 'self.MarketOrder', 'exit': 'self.MarketOrder', 'close': 'self.MarketOrder',
            'long': 'self.SetHoldings', 'short': 'self.SetHoldings',
            'liquidate': 'self.Liquidate', 'close all': 'self.Liquidate', 'exit all': 'self.Liquidate',
            
            # Advanced Actions
            'market buy': 'self.MarketOrder', 'market sell': 'self.MarketOrder',
            'limit buy': 'self.LimitOrder', 'limit sell': 'self.LimitOrder',
            'stop buy': 'self.StopMarketOrder', 'stop sell': 'self.StopMarketOrder',
            'stop limit buy': 'self.StopLimitOrder', 'stop limit sell': 'self.StopLimitOrder',
            'trailing stop': 'self.TrailingStopOrder', 'trailing stop loss': 'self.TrailingStopOrder',
            
            # Position Sizing
            'set holdings': 'self.SetHoldings', 'set position': 'self.SetHoldings',
            'percentage': 'self.SetHoldings', 'percent': 'self.SetHoldings',
            'full position': 'self.SetHoldings', 'max position': 'self.SetHoldings',
            'partial position': 'self.SetHoldings', 'half position': 'self.SetHoldings',
            'quarter position': 'self.SetHoldings', 'small position': 'self.SetHoldings',
            
            # Risk Management
            'stop loss': 'self.StopLossOrder', 'stop loss order': 'self.StopLossOrder',
            'take profit': 'self.TakeProfitOrder', 'take profit order': 'self.TakeProfitOrder',
            'bracket order': 'self.BracketOrder', 'bracket': 'self.BracketOrder',
            'oco order': 'self.OneCancelsOther', 'oco': 'self.OneCancelsOther',
            'if touched': 'self.IfTouchedOrder', 'if touched order': 'self.IfTouchedOrder',
            
            # Portfolio Management
            'rebalance': 'self.Rebalance', 'rebalance portfolio': 'self.Rebalance',
            'equal weight': 'self.EqualWeight', 'equal weighting': 'self.EqualWeight',
            'market cap weight': 'self.MarketCapWeight', 'cap weighted': 'self.MarketCapWeight',
            'inverse weight': 'self.InverseWeight', 'inverse weighting': 'self.InverseWeight',
            'momentum weight': 'self.MomentumWeight', 'momentum weighting': 'self.MomentumWeight',
            'volatility weight': 'self.VolatilityWeight', 'vol weighting': 'self.VolatilityWeight',
            
            # Options (if available)
            'call option': 'self.CallOption', 'put option': 'self.PutOption',
            'buy call': 'self.CallOption', 'buy put': 'self.PutOption',
            'sell call': 'self.SellCall', 'sell put': 'self.SellPut',
            'covered call': 'self.CoveredCall', 'cash secured put': 'self.CashSecuredPut',
            'straddle': 'self.Straddle', 'strangle': 'self.Strangle',
            'iron condor': 'self.IronCondor', 'butterfly': 'self.Butterfly',
            'calendar spread': 'self.CalendarSpread', 'diagonal spread': 'self.DiagonalSpread',
            
            # Futures Specific
            'futures long': 'self.FuturesLong', 'futures short': 'self.FuturesShort',
            'roll futures': 'self.RollFutures', 'futures roll': 'self.RollFutures',
            'margin call': 'self.MarginCall', 'margin requirement': 'self.MarginRequirement',
            
            # Forex Specific
            'forex long': 'self.ForexLong', 'forex short': 'self.ForexShort',
            'currency pair': 'self.CurrencyPair', 'fx pair': 'self.CurrencyPair',
            'carry trade': 'self.CarryTrade', 'interest rate arbitrage': 'self.CarryTrade',
            
            # Crypto Specific
            'crypto long': 'self.CryptoLong', 'crypto short': 'self.CryptoShort',
            'staking': 'self.Staking', 'yield farming': 'self.YieldFarming',
            'liquidity provision': 'self.LiquidityProvision', 'lp': 'self.LiquidityProvision',
            
            # Alternative Actions
            'hedge': 'self.Hedge', 'hedging': 'self.Hedge',
            'arbitrage': 'self.Arbitrage', 'arb': 'self.Arbitrage',
            'pairs trade': 'self.PairsTrade', 'pair trading': 'self.PairsTrade',
            'mean reversion': 'self.MeanReversion', 'contrarian': 'self.MeanReversion',
            'momentum': 'self.Momentum', 'trend following': 'self.Momentum',
            'scalping': 'self.Scalping', 'scalp': 'self.Scalping',
            'swing trading': 'self.SwingTrading', 'swing': 'self.SwingTrading',
            'day trading': 'self.DayTrading', 'day trade': 'self.DayTrading',
            'position trading': 'self.PositionTrading', 'position': 'self.PositionTrading',
            'investing': 'self.Investing', 'investment': 'self.Investing'
        }
        
        # Backtest period patterns
        self.backtest_period_patterns = {
            # Specific periods
            'last year': {'years': 1, 'months': 0, 'days': 0},
            'last 2 years': {'years': 2, 'months': 0, 'days': 0},
            'last 3 years': {'years': 3, 'months': 0, 'days': 0},
            'last 4 years': {'years': 4, 'months': 0, 'days': 0},
            'last 5 years': {'years': 5, 'months': 0, 'days': 0},
            'last 10 years': {'years': 10, 'months': 0, 'days': 0},
            'last month': {'years': 0, 'months': 1, 'days': 0},
            'last 2 months': {'years': 0, 'months': 2, 'days': 0},
            'last 3 months': {'years': 0, 'months': 3, 'days': 0},
            'last 6 months': {'years': 0, 'months': 6, 'days': 0},
            'last 9 months': {'years': 0, 'months': 9, 'days': 0},
            'last week': {'years': 0, 'months': 0, 'days': 7},
            'last 2 weeks': {'years': 0, 'months': 0, 'days': 14},
            'last 3 weeks': {'years': 0, 'months': 0, 'days': 21},
            'last month': {'years': 0, 'months': 1, 'days': 0},
            'last quarter': {'years': 0, 'months': 3, 'days': 0},
            'last semester': {'years': 0, 'months': 6, 'days': 0},
            'last 2 quarters': {'years': 0, 'months': 6, 'days': 0},
            'last 3 quarters': {'years': 0, 'months': 9, 'days': 0},
            'last 4 quarters': {'years': 1, 'months': 0, 'days': 0},
            'last 6 quarters': {'years': 1, 'months': 6, 'days': 0},
            'last 8 quarters': {'years': 2, 'months': 0, 'days': 0},
            'last 12 quarters': {'years': 3, 'months': 0, 'days': 0},
            'last 16 quarters': {'years': 4, 'months': 0, 'days': 0},
            'last 20 quarters': {'years': 5, 'months': 0, 'days': 0},
            
            # Alternative expressions
            'past year': {'years': 1, 'months': 0, 'days': 0},
            'past 2 years': {'years': 2, 'months': 0, 'days': 0},
            'past 3 years': {'years': 3, 'months': 0, 'days': 0},
            'past 5 years': {'years': 5, 'months': 0, 'days': 0},
            'past month': {'years': 0, 'months': 1, 'days': 0},
            'past 3 months': {'years': 0, 'months': 3, 'days': 0},
            'past 6 months': {'years': 0, 'months': 6, 'days': 0},
            'past week': {'years': 0, 'months': 0, 'days': 7},
            'past 2 weeks': {'years': 0, 'months': 0, 'days': 14},
            'past quarter': {'years': 0, 'months': 3, 'days': 0},
            'past 2 quarters': {'years': 0, 'months': 6, 'days': 0},
            'past 3 quarters': {'years': 0, 'months': 9, 'days': 0},
            'past 4 quarters': {'years': 1, 'months': 0, 'days': 0},
            
            # Recent periods
            'recent year': {'years': 1, 'months': 0, 'days': 0},
            'recent 2 years': {'years': 2, 'months': 0, 'days': 0},
            'recent 3 years': {'years': 3, 'months': 0, 'days': 0},
            'recent 5 years': {'years': 5, 'months': 0, 'days': 0},
            'recent month': {'years': 0, 'months': 1, 'days': 0},
            'recent 3 months': {'years': 0, 'months': 3, 'days': 0},
            'recent 6 months': {'years': 0, 'months': 6, 'days': 0},
            'recent quarter': {'years': 0, 'months': 3, 'days': 0},
            'recent 2 quarters': {'years': 0, 'months': 6, 'days': 0},
            'recent 3 quarters': {'years': 0, 'months': 9, 'days': 0},
            'recent 4 quarters': {'years': 1, 'months': 0, 'days': 0},
            
            # Specific timeframes
            '1 year': {'years': 1, 'months': 0, 'days': 0},
            '2 years': {'years': 2, 'months': 0, 'days': 0},
            '3 years': {'years': 3, 'months': 0, 'days': 0},
            '4 years': {'years': 4, 'months': 0, 'days': 0},
            '5 years': {'years': 5, 'months': 0, 'days': 0},
            '10 years': {'years': 10, 'months': 0, 'days': 0},
            '1 month': {'years': 0, 'months': 1, 'days': 0},
            '2 months': {'years': 0, 'months': 2, 'days': 0},
            '3 months': {'years': 0, 'months': 3, 'days': 0},
            '6 months': {'years': 0, 'months': 6, 'days': 0},
            '9 months': {'years': 0, 'months': 9, 'days': 0},
            '1 week': {'years': 0, 'months': 0, 'days': 7},
            '2 weeks': {'years': 0, 'months': 0, 'days': 14},
            '3 weeks': {'years': 0, 'months': 0, 'days': 21},
            '1 quarter': {'years': 0, 'months': 3, 'days': 0},
            '2 quarters': {'years': 0, 'months': 6, 'days': 0},
            '3 quarters': {'years': 0, 'months': 9, 'days': 0},
            '4 quarters': {'years': 1, 'months': 0, 'days': 0},
            '6 quarters': {'years': 1, 'months': 6, 'days': 0},
            '8 quarters': {'years': 2, 'months': 0, 'days': 0},
            '12 quarters': {'years': 3, 'months': 0, 'days': 0},
            '16 quarters': {'years': 4, 'months': 0, 'days': 0},
            '20 quarters': {'years': 5, 'months': 0, 'days': 0},
            
            # Trading periods
            'ytd': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_to_date'},
            'year to date': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_to_date'},
            'mtd': {'years': 0, 'months': 0, 'days': 0, 'special': 'month_to_date'},
            'month to date': {'years': 0, 'months': 0, 'days': 0, 'special': 'month_to_date'},
            'qtd': {'years': 0, 'months': 0, 'days': 0, 'special': 'quarter_to_date'},
            'quarter to date': {'years': 0, 'months': 0, 'days': 0, 'special': 'quarter_to_date'},
            
            # Market cycles
            'bull market': {'years': 3, 'months': 0, 'days': 0, 'special': 'bull_market'},
            'bear market': {'years': 1, 'months': 6, 'days': 0, 'special': 'bear_market'},
            'covid period': {'years': 0, 'months': 0, 'days': 0, 'special': 'covid_period'},
            'covid crash': {'years': 0, 'months': 0, 'days': 0, 'special': 'covid_crash'},
            'covid recovery': {'years': 0, 'months': 0, 'days': 0, 'special': 'covid_recovery'},
            'financial crisis': {'years': 0, 'months': 0, 'days': 0, 'special': 'financial_crisis'},
            'dot com bubble': {'years': 0, 'months': 0, 'days': 0, 'special': 'dot_com_bubble'},
            'dot com crash': {'years': 0, 'months': 0, 'days': 0, 'special': 'dot_com_crash'},
            
            # Specific years
            '2020': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_2020'},
            '2021': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_2021'},
            '2022': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_2022'},
            '2023': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_2023'},
            '2024': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_2024'},
            '2019': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_2019'},
            '2018': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_2018'},
            '2017': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_2017'},
            '2016': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_2016'},
            '2015': {'years': 0, 'months': 0, 'days': 0, 'special': 'year_2015'},
            
            # Decades
            '2010s': {'years': 0, 'months': 0, 'days': 0, 'special': 'decade_2010s'},
            '2020s': {'years': 0, 'months': 0, 'days': 0, 'special': 'decade_2020s'},
            'last decade': {'years': 0, 'months': 0, 'days': 0, 'special': 'decade_2010s'},
            'current decade': {'years': 0, 'months': 0, 'days': 0, 'special': 'decade_2020s'},
            
            # Maximum periods
            'all time': {'years': 0, 'months': 0, 'days': 0, 'special': 'all_time'},
            'maximum': {'years': 0, 'months': 0, 'days': 0, 'special': 'all_time'},
            'full history': {'years': 0, 'months': 0, 'days': 0, 'special': 'all_time'},
            'complete history': {'years': 0, 'months': 0, 'days': 0, 'special': 'all_time'},
            'entire history': {'years': 0, 'months': 0, 'days': 0, 'special': 'all_time'},
            
            # Short periods for testing
            '1 day': {'years': 0, 'months': 0, 'days': 1},
            '2 days': {'years': 0, 'months': 0, 'days': 2},
            '3 days': {'years': 0, 'months': 0, 'days': 3},
            '5 days': {'years': 0, 'months': 0, 'days': 5},
            '10 days': {'years': 0, 'months': 0, 'days': 10},
            '15 days': {'years': 0, 'months': 0, 'days': 15},
            '20 days': {'years': 0, 'months': 0, 'days': 20},
            '30 days': {'years': 0, 'months': 1, 'days': 0},
            '45 days': {'years': 0, 'months': 0, 'days': 45},
            '60 days': {'years': 0, 'months': 2, 'days': 0},
            '90 days': {'years': 0, 'months': 3, 'days': 0},
            '120 days': {'years': 0, 'months': 4, 'days': 0},
            '150 days': {'years': 0, 'months': 5, 'days': 0},
            '180 days': {'years': 0, 'months': 6, 'days': 0},
            '270 days': {'years': 0, 'months': 9, 'days': 0},
            '365 days': {'years': 1, 'months': 0, 'days': 0},
            '500 days': {'years': 1, 'months': 4, 'days': 15},
            '730 days': {'years': 2, 'months': 0, 'days': 0},
            '1000 days': {'years': 2, 'months': 9, 'days': 0},
            '1500 days': {'years': 4, 'months': 1, 'days': 0},
            '2000 days': {'years': 5, 'months': 6, 'days': 0},
            '2500 days': {'years': 6, 'months': 10, 'days': 0},
            '3000 days': {'years': 8, 'months': 2, 'days': 0},
            '3650 days': {'years': 10, 'months': 0, 'days': 0}
        }
        
        # Complex trading conditions
        self.condition_patterns = {
            # Price Conditions
            'price above': 'price_above', 'price below': 'price_below',
            'price crosses above': 'price_crosses_above', 'price crosses below': 'price_crosses_below',
            'price breaks above': 'price_breaks_above', 'price breaks below': 'price_breaks_below',
            'price touches': 'price_touches', 'price bounces off': 'price_bounces_off',
            'price rejects': 'price_rejects', 'price holds': 'price_holds',
            'price consolidates': 'price_consolidates', 'price ranges': 'price_ranges',
            'price trends up': 'price_trends_up', 'price trends down': 'price_trends_down',
            'price makes new high': 'price_new_high', 'price makes new low': 'price_new_low',
            'price retraces': 'price_retraces', 'price pulls back': 'price_pulls_back',
            'price gaps up': 'price_gaps_up', 'price gaps down': 'price_gaps_down',
            'price fills gap': 'price_fills_gap', 'price tests support': 'price_tests_support',
            'price tests resistance': 'price_tests_resistance', 'price breaks support': 'price_breaks_support',
            'price breaks resistance': 'price_breaks_resistance',
            
            # Indicator Conditions
            'indicator above': 'indicator_above', 'indicator below': 'indicator_below',
            'indicator crosses above': 'indicator_crosses_above', 'indicator crosses below': 'indicator_crosses_below',
            'indicator diverges': 'indicator_diverges', 'indicator converges': 'indicator_converges',
            'indicator overbought': 'indicator_overbought', 'indicator oversold': 'indicator_oversold',
            'indicator neutral': 'indicator_neutral', 'indicator bullish': 'indicator_bullish',
            'indicator bearish': 'indicator_bearish', 'indicator strong': 'indicator_strong',
            'indicator weak': 'indicator_weak', 'indicator rising': 'indicator_rising',
            'indicator falling': 'indicator_falling', 'indicator flat': 'indicator_flat',
            'indicator accelerating': 'indicator_accelerating', 'indicator decelerating': 'indicator_decelerating',
            
            # Volume Conditions
            'volume above average': 'volume_above_average', 'volume below average': 'volume_below_average',
            'volume spike': 'volume_spike', 'volume surge': 'volume_surge',
            'volume dry up': 'volume_dry_up', 'volume exhaustion': 'volume_exhaustion',
            'volume confirmation': 'volume_confirmation', 'volume divergence': 'volume_divergence',
            'volume breakout': 'volume_breakout', 'volume breakdown': 'volume_breakdown',
            'volume accumulation': 'volume_accumulation', 'volume distribution': 'volume_distribution',
            'volume climax': 'volume_climax', 'volume capitulation': 'volume_capitulation',
            
            # Time Conditions
            'market open': 'market_open', 'market close': 'market_close',
            'pre market': 'pre_market', 'after hours': 'after_hours',
            'lunch time': 'lunch_time', 'power hour': 'power_hour',
            'first hour': 'first_hour', 'last hour': 'last_hour',
            'opening bell': 'opening_bell', 'closing bell': 'closing_bell',
            'fomc meeting': 'fomc_meeting', 'earnings season': 'earnings_season',
            'options expiration': 'options_expiration', 'triple witching': 'triple_witching',
            'month end': 'month_end', 'quarter end': 'quarter_end',
            'year end': 'year_end', 'holiday': 'holiday',
            
            # Market Conditions
            'bull market': 'bull_market', 'bear market': 'bear_market',
            'sideways market': 'sideways_market', 'choppy market': 'choppy_market',
            'trending market': 'trending_market', 'ranging market': 'ranging_market',
            'volatile market': 'volatile_market', 'calm market': 'calm_market',
            'risk on': 'risk_on', 'risk off': 'risk_off',
            'flight to quality': 'flight_to_quality', 'risk appetite': 'risk_appetite',
            'market sentiment': 'market_sentiment', 'fear and greed': 'fear_and_greed',
            'put call ratio': 'put_call_ratio', 'vix spike': 'vix_spike',
            'vix low': 'vix_low', 'vix high': 'vix_high',
            
            # Pattern Conditions
            'double top': 'double_top', 'double bottom': 'double_bottom',
            'triple top': 'triple_top', 'triple bottom': 'triple_bottom',
            'head and shoulders': 'head_and_shoulders', 'inverse head and shoulders': 'inverse_head_and_shoulders',
            'cup and handle': 'cup_and_handle', 'flag': 'flag', 'pennant': 'pennant',
            'triangle': 'triangle', 'ascending triangle': 'ascending_triangle',
            'descending triangle': 'descending_triangle', 'symmetrical triangle': 'symmetrical_triangle',
            'wedge': 'wedge', 'rising wedge': 'rising_wedge', 'falling wedge': 'falling_wedge',
            'channel': 'channel', 'ascending channel': 'ascending_channel',
            'descending channel': 'descending_channel', 'horizontal channel': 'horizontal_channel',
            'diamond': 'diamond', 'megaphone': 'megaphone', 'broadening formation': 'broadening_formation',
            
            # Candlestick Patterns
            'doji': 'doji', 'hammer': 'hammer', 'hanging man': 'hanging_man',
            'shooting star': 'shooting_star', 'inverted hammer': 'inverted_hammer',
            'engulfing': 'engulfing', 'harami': 'harami', 'piercing': 'piercing',
            'dark cloud': 'dark_cloud', 'morning star': 'morning_star',
            'evening star': 'evening_star', 'three white soldiers': 'three_white_soldiers',
            'three black crows': 'three_black_crows', 'tweezer': 'tweezer',
            'inside bar': 'inside_bar', 'outside bar': 'outside_bar',
            'pin bar': 'pin_bar', 'wick rejection': 'wick_rejection',
            
            # Multi-timeframe Conditions
            'higher timeframe trend': 'htf_trend', 'lower timeframe entry': 'ltf_entry',
            'timeframe alignment': 'timeframe_alignment', 'timeframe divergence': 'timeframe_divergence',
            'multi timeframe': 'multi_timeframe', 'confluence': 'confluence',
            'multiple confirmations': 'multiple_confirmations', 'strong signal': 'strong_signal',
            'weak signal': 'weak_signal', 'mixed signals': 'mixed_signals',
            
            # Risk Conditions
            'stop loss hit': 'stop_loss_hit', 'take profit hit': 'take_profit_hit',
            'trailing stop': 'trailing_stop', 'breakeven': 'breakeven',
            'risk reward': 'risk_reward', 'risk management': 'risk_management',
            'position sizing': 'position_sizing', 'portfolio heat': 'portfolio_heat',
            'drawdown': 'drawdown', 'max drawdown': 'max_drawdown',
            'correlation': 'correlation', 'diversification': 'diversification'
        }
    
    def parse_strategy_description(self, description: str, strategy_data: Dict[str, Any] = None) -> str:
        """
        Parse natural language description to QuantConnect Python code
        """
        if not description:
            return self._generate_default_code()
        
        # Extract key components from description
        symbols = self._extract_symbols(description)
        indicators = self._extract_indicators(description)
        timeframe = self._extract_timeframe(description)
        backtest_period = self._extract_backtest_period(description)
        actions = self._extract_actions(description)
        conditions = self._extract_conditions(description)
        
        # Generate code based on extracted components
        return self._generate_strategy_code(
            symbols=symbols,
            indicators=indicators,
            timeframe=timeframe,
            actions=actions,
            conditions=conditions,
            backtest_period=backtest_period,
            strategy_data=strategy_data
        )
    
    def _extract_symbols(self, description: str) -> List[str]:
        """Extract trading symbols from description"""
        symbols = []
        description_lower = description.lower()
        
        for pattern, symbol in self.symbol_patterns.items():
            if pattern in description_lower:
                symbols.append(symbol)
        
        # If no symbols found, default to SPY
        if not symbols:
            symbols = ['SPY']
        
        return symbols
    
    def _extract_indicators(self, description: str) -> List[Dict[str, Any]]:
        """Extract technical indicators from description"""
        indicators = []
        description_lower = description.lower()
        
        # SMA patterns
        sma_match = re.search(r'sma\s*\(?\s*(\d+)\s*\)?', description_lower)
        if sma_match:
            indicators.append({
                'type': 'SimpleMovingAverage',
                'period': int(sma_match.group(1)),
                'name': 'sma'
            })
        
        # EMA patterns
        ema_match = re.search(r'ema\s*\(?\s*(\d+)\s*\)?', description_lower)
        if ema_match:
            indicators.append({
                'type': 'ExponentialMovingAverage',
                'period': int(ema_match.group(1)),
                'name': 'ema'
            })
        
        # RSI patterns
        rsi_match = re.search(r'rsi\s*\(?\s*(\d+)\s*\)?', description_lower)
        if rsi_match:
            indicators.append({
                'type': 'RelativeStrengthIndex',
                'period': int(rsi_match.group(1)),
                'name': 'rsi'
            })
        
        # MACD patterns
        if 'macd' in description_lower:
            indicators.append({
                'type': 'MACD',
                'fast': 12,
                'slow': 26,
                'signal': 9,
                'name': 'macd'
            })
        
        # Bollinger Bands patterns
        bb_match = re.search(r'bollinger\s*\(?\s*(\d+)\s*\)?', description_lower)
        if bb_match:
            indicators.append({
                'type': 'BollingerBands',
                'period': int(bb_match.group(1)),
                'std': 2,
                'name': 'bb'
            })
        
        return indicators
    
    def _extract_timeframe(self, description: str) -> str:
        """Extract timeframe from description"""
        description_lower = description.lower()
        
        for pattern, resolution in self.timeframe_patterns.items():
            if pattern in description_lower:
                return resolution
    
    def _extract_backtest_period(self, description: str) -> Dict[str, Any]:
        """Extract backtest period from description"""
        description_lower = description.lower()
        
        for pattern, period_config in self.backtest_period_patterns.items():
            if pattern in description_lower:
                return period_config
        
        # Default to 3 years if no period specified
        return {'years': 3, 'months': 0, 'days': 0}
    
    def _extract_actions(self, description: str) -> List[Dict[str, Any]]:
        """Extract trading actions from description"""
        actions = []
        description_lower = description.lower()
        
        # Buy patterns
        if any(word in description_lower for word in ['buy', 'long', 'purchase']):
            actions.append({
                'type': 'buy',
                'condition': 'positive'
            })
        
        # Sell patterns
        if any(word in description_lower for word in ['sell', 'short', 'exit']):
            actions.append({
                'type': 'sell',
                'condition': 'negative'
            })
        
        return actions
    
    def _extract_conditions(self, description: str) -> List[Dict[str, Any]]:
        """Extract trading conditions from description"""
        conditions = []
        description_lower = description.lower()
        
        # Price above/below conditions
        if 'above' in description_lower and 'sma' in description_lower:
            conditions.append({
                'type': 'price_above_indicator',
                'indicator': 'sma',
                'action': 'buy'
            })
        
        if 'below' in description_lower and 'sma' in description_lower:
            conditions.append({
                'type': 'price_below_indicator',
                'indicator': 'sma',
                'action': 'sell'
            })
        
        # RSI conditions
        if 'rsi' in description_lower:
            if 'oversold' in description_lower or 'below 30' in description_lower:
                conditions.append({
                    'type': 'rsi_oversold',
                    'threshold': 30,
                    'action': 'buy'
                })
            elif 'overbought' in description_lower or 'above 70' in description_lower:
                conditions.append({
                    'type': 'rsi_overbought',
                    'threshold': 70,
                    'action': 'sell'
                })
        
        return conditions
    
    def _generate_strategy_code(self, symbols: List[str], indicators: List[Dict], 
                              timeframe: str, actions: List[Dict], 
                              conditions: List[Dict], strategy_data: Dict = None, 
                              backtest_period: Dict[str, Any] = None) -> str:
        """Generate complete QuantConnect strategy code with advanced features"""
        
        # Determine market type and add appropriate symbols
        market_type = self._determine_market_type(symbols[0])
        
        # Calculate start and end dates based on backtest period
        start_date, end_date = self._calculate_backtest_dates(backtest_period)
        
        # Start with imports and class definition
        code = """from AlgorithmImports import *
import numpy as np
from datetime import datetime, timedelta

class AdvancedTradingAlgorithm(QCAlgorithm):
    def Initialize(self):
        # Set start and end dates
        self.SetStartDate({start_year}, {start_month}, {start_day})
        self.SetEndDate({end_year}, {end_month}, {end_day})
        self.SetCash(100000)""".format(
            start_year=start_date.year,
            start_month=start_date.month,
            start_day=start_date.day,
            end_year=end_date.year,
            end_month=end_date.month,
            end_day=end_date.day
        )
        
        # Set benchmark
        self.SetBenchmark("SPY")
        
        # Set timezone
        self.SetTimeZone("America/New_York")
        
        # Add symbols based on market type
        """
        
        # Add symbols with appropriate market type
        for symbol in symbols:
            if market_type == 'forex':
                code += f'        self.AddForex("{symbol}", {timeframe})\n'
            elif market_type == 'futures':
                code += f'        self.AddFuture("{symbol}", {timeframe})\n'
            elif market_type == 'crypto':
                code += f'        self.AddCrypto("{symbol}", {timeframe})\n'
            elif market_type == 'commodity':
                code += f'        self.AddCommodity("{symbol}", {timeframe})\n'
            else:
                code += f'        self.AddEquity("{symbol}", {timeframe})\n'
        
        # Add indicators with advanced configurations
        if indicators:
            code += "\n        # Add technical indicators\n"
            for indicator in indicators:
                code += self._generate_indicator_code(indicator, symbols[0])
        
        # Add risk management
        code += """
        # Risk management
        self.SetRiskManagement(CompositeRiskManagementModel(
            MaximumDrawdownPercentPerSecurity(0.02),
            MaximumUnrealizedProfitPercentPerSecurity(0.01)
        ))
        
        # Position sizing
        self.SetPortfolioConstruction(EqualWeightingPortfolioConstructionModel())
        
        # Execution model
        self.SetExecution(ImmediateExecutionModel())
        
        # Data normalization
        self.SetDataNormalizationMode(DataNormalizationMode.Raw)
        
        # Warm up period
        self.SetWarmUp(200, Resolution.Daily)
        """
        
        # Add OnData method with advanced logic
        code += """
    def OnData(self, data):
        # Skip if warming up
        if self.IsWarmingUp:
            return
            
        # Check if indicators are ready
        if not self._indicators_ready():
            return
        """
        
        # Add trading logic based on conditions
        if conditions:
            code += "        # Trading logic based on conditions\n"
            for condition in conditions:
                code += self._generate_condition_code(condition, symbols[0])
        else:
            # Default advanced strategy
            code += f"        # Advanced buy and hold with rebalancing\n"
            code += f"        if not self.Portfolio.Invested:\n"
            code += f"            self.SetHoldings('{symbols[0]}', 0.95)  # Leave 5% cash\n"
        
        # Add advanced exit conditions
        code += """
        # Advanced exit conditions
        self._check_exit_conditions()
        
    def _indicators_ready(self):
        """Check if all indicators are ready"""
        return True  # Implement indicator readiness check
        
    def _check_exit_conditions(self):
        """Check various exit conditions"""
        # Implement advanced exit logic
        pass
        
    def OnOrderEvent(self, orderEvent):
        """Handle order events"""
        if orderEvent.Status == OrderStatus.Filled:
            self.Debug(f"Order filled: {orderEvent}")
            
    def OnEndOfAlgorithm(self):
        """Called at the end of the algorithm"""
        self.Debug("Algorithm completed")
        """
        
        return code
    
    def _calculate_backtest_dates(self, backtest_period: Dict[str, Any]) -> tuple:
        """Calculate start and end dates for backtest based on period configuration"""
        from datetime import datetime, timedelta
        
        if not backtest_period:
            backtest_period = {'years': 3, 'months': 0, 'days': 0}
        
        # Get current date
        end_date = datetime.now()
        
        # Handle special periods
        if 'special' in backtest_period:
            special = backtest_period['special']
            
            if special == 'year_to_date':
                start_date = datetime(end_date.year, 1, 1)
            elif special == 'month_to_date':
                start_date = datetime(end_date.year, end_date.month, 1)
            elif special == 'quarter_to_date':
                quarter = (end_date.month - 1) // 3 + 1
                start_date = datetime(end_date.year, (quarter - 1) * 3 + 1, 1)
            elif special == 'covid_period':
                start_date = datetime(2020, 1, 1)
                end_date = datetime(2021, 12, 31)
            elif special == 'covid_crash':
                start_date = datetime(2020, 2, 1)
                end_date = datetime(2020, 4, 30)
            elif special == 'covid_recovery':
                start_date = datetime(2020, 4, 1)
                end_date = datetime(2021, 12, 31)
            elif special == 'financial_crisis':
                start_date = datetime(2007, 1, 1)
                end_date = datetime(2009, 12, 31)
            elif special == 'dot_com_bubble':
                start_date = datetime(1998, 1, 1)
                end_date = datetime(2000, 3, 31)
            elif special == 'dot_com_crash':
                start_date = datetime(2000, 3, 1)
                end_date = datetime(2002, 12, 31)
            elif special == 'bull_market':
                start_date = datetime(2009, 3, 1)
                end_date = datetime(2020, 2, 29)
            elif special == 'bear_market':
                start_date = datetime(2007, 10, 1)
                end_date = datetime(2009, 3, 31)
            elif special.startswith('year_'):
                year = int(special.split('_')[1])
                start_date = datetime(year, 1, 1)
                end_date = datetime(year, 12, 31)
            elif special == 'decade_2010s':
                start_date = datetime(2010, 1, 1)
                end_date = datetime(2019, 12, 31)
            elif special == 'decade_2020s':
                start_date = datetime(2020, 1, 1)
                end_date = datetime.now()
            elif special == 'all_time':
                start_date = datetime(2000, 1, 1)  # Default to year 2000
                end_date = datetime.now()
            else:
                # Default to 3 years
                start_date = end_date - timedelta(days=365*3)
        else:
            # Calculate start date based on years, months, days
            years = backtest_period.get('years', 0)
            months = backtest_period.get('months', 0)
            days = backtest_period.get('days', 0)
            
            # Calculate total days
            total_days = years * 365 + months * 30 + days
            
            # Calculate start date
            start_date = end_date - timedelta(days=total_days)
        
        return start_date, end_date
    
    def _determine_market_type(self, symbol: str) -> str:
        """Determine market type based on symbol"""
        forex_symbols = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD']
        futures_symbols = ['ES', 'NQ', 'YM', 'RTY', 'GC', 'SI', 'CL', 'NG', 'ZB', 'ZN']
        crypto_symbols = ['BTCUSD', 'ETHUSD', 'LTCUSD', 'XRPUSD', 'ADAUSD', 'DOTUSD']
        commodity_symbols = ['ZC', 'ZW', 'ZS', 'KC', 'SB', 'CC', 'CT', 'LC', 'LH']
        
        if symbol in forex_symbols:
            return 'forex'
        elif symbol in futures_symbols:
            return 'futures'
        elif symbol in crypto_symbols:
            return 'crypto'
        elif symbol in commodity_symbols:
            return 'commodity'
        else:
            return 'equity'
    
    def _generate_indicator_code(self, indicator: Dict, symbol: str) -> str:
        """Generate code for specific indicator"""
        indicator_type = indicator.get('type', 'SMA')
        period = indicator.get('period', 20)
        name = indicator.get('name', indicator_type.lower())
        
        code = ""
        
        if indicator_type == 'SimpleMovingAverage':
            code = f"        self.{name} = self.SMA(self.Symbol('{symbol}'), {period})\n"
        elif indicator_type == 'ExponentialMovingAverage':
            code = f"        self.{name} = self.EMA(self.Symbol('{symbol}'), {period})\n"
        elif indicator_type == 'RelativeStrengthIndex':
            code = f"        self.{name} = self.RSI(self.Symbol('{symbol}'), {period})\n"
        elif indicator_type == 'MACD':
            fast = indicator.get('fast', 12)
            slow = indicator.get('slow', 26)
            signal = indicator.get('signal', 9)
            code = f"        self.{name} = self.MACD(self.Symbol('{symbol}'), {fast}, {slow}, {signal})\n"
        elif indicator_type == 'BollingerBands':
            std = indicator.get('std', 2)
            code = f"        self.{name} = self.BB(self.Symbol('{symbol}'), {period}, {std})\n"
        elif indicator_type == 'VolumeWeightedAveragePrice':
            code = f"        self.{name} = self.VWAP(self.Symbol('{symbol}'))\n"
        elif indicator_type == 'AverageTrueRange':
            code = f"        self.{name} = self.ATR(self.Symbol('{symbol}'), {period})\n"
        elif indicator_type == 'Stochastic':
            k_period = indicator.get('k_period', 14)
            d_period = indicator.get('d_period', 3)
            code = f"        self.{name} = self.STO(self.Symbol('{symbol}'), {k_period}, {d_period})\n"
        elif indicator_type == 'WilliamsPercentR':
            code = f"        self.{name} = self.WILR(self.Symbol('{symbol}'), {period})\n"
        elif indicator_type == 'CommodityChannelIndex':
            code = f"        self.{name} = self.CCI(self.Symbol('{symbol}'), {period})\n"
        elif indicator_type == 'ParabolicStopAndReverse':
            af_start = indicator.get('af_start', 0.02)
            af_increment = indicator.get('af_increment', 0.02)
            af_maximum = indicator.get('af_maximum', 0.2)
            code = f"        self.{name} = self.PSAR(self.Symbol('{symbol}'), {af_start}, {af_increment}, {af_maximum})\n"
        elif indicator_type == 'IchimokuKinkoHyo':
            tenkan = indicator.get('tenkan', 9)
            kijun = indicator.get('kijun', 26)
            senkou_b = indicator.get('senkou_b', 52)
            code = f"        self.{name} = self.ICHIMOKU(self.Symbol('{symbol}'), {tenkan}, {kijun}, {senkou_b})\n"
        else:
            # Default to SMA for unknown indicators
            code = f"        self.{name} = self.SMA(self.Symbol('{symbol}'), {period})\n"
        
        return code
    
    def _generate_condition_code(self, condition: Dict, symbol: str) -> str:
        """Generate code for specific trading condition"""
        condition_type = condition.get('type', 'price_above_indicator')
        action = condition.get('action', 'buy')
        threshold = condition.get('threshold', 0.5)
        
        code = ""
        
        if condition_type == 'price_above_indicator':
            indicator = condition.get('indicator', 'sma')
            code = f"        if self.Securities['{symbol}'].Price > self.{indicator}.Current.Value:\n"
            if action == 'buy':
                code += f"            self.SetHoldings('{symbol}', {threshold})\n"
            else:
                code += f"            self.Liquidate('{symbol}')\n"
        elif condition_type == 'price_below_indicator':
            indicator = condition.get('indicator', 'sma')
            code = f"        elif self.Securities['{symbol}'].Price < self.{indicator}.Current.Value:\n"
            if action == 'sell':
                code += f"            self.Liquidate('{symbol}')\n"
            else:
                code += f"            self.SetHoldings('{symbol}', -{threshold})\n"
        elif condition_type == 'rsi_oversold':
            code = f"        if self.rsi.Current.Value < {threshold}:\n"
            code += f"            self.SetHoldings('{symbol}', 0.5)\n"
        elif condition_type == 'rsi_overbought':
            code = f"        elif self.rsi.Current.Value > {threshold}:\n"
            code += f"            self.Liquidate('{symbol}')\n"
        elif condition_type == 'macd_bullish_cross':
            code = f"        if self.macd.Current.Value > self.macd.Signal.Current.Value and self.macd.Previous.Value <= self.macd.Signal.Previous.Value:\n"
            code += f"            self.SetHoldings('{symbol}', 0.8)\n"
        elif condition_type == 'macd_bearish_cross':
            code = f"        elif self.macd.Current.Value < self.macd.Signal.Current.Value and self.macd.Previous.Value >= self.macd.Signal.Previous.Value:\n"
            code += f"            self.Liquidate('{symbol}')\n"
        elif condition_type == 'bollinger_squeeze':
            code = f"        if self.bb.UpperBand.Current.Value - self.bb.LowerBand.Current.Value < self.bb.MiddleBand.Current.Value * 0.1:\n"
            code += f"            # Bollinger squeeze detected, prepare for breakout\n"
            code += f"            pass\n"
        elif condition_type == 'volume_spike':
            code = f"        if self.Securities['{symbol}'].Volume > self.Securities['{symbol}'].Volume.Average(20) * 2:\n"
            code += f"            # Volume spike detected\n"
            code += f"            pass\n"
        else:
            # Default condition
            code = f"        # Custom condition: {condition_type}\n"
            code += f"        pass\n"
        
        return code
    
    def _generate_default_code(self) -> str:
        """Generate default QuantConnect code"""
        return """from AlgorithmImports import *

class TradingAlgorithm(QCAlgorithm):
    def Initialize(self):
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)
        
        # Add SPY
        self.AddEquity("SPY", Resolution.Daily)
        
        # Add SMA indicator
        self.sma = self.SMA(self.Symbol("SPY"), 20)
        
    def OnData(self, data):
        if not self.Portfolio.Invested:
            if self.Securities["SPY"].Price > self.sma.Current.Value:
                self.SetHoldings("SPY", 1.0)
        
        # Exit if price drops below SMA
        if self.Portfolio.Invested and self.Securities["SPY"].Price < self.sma.Current.Value * 0.95:
            self.Liquidate("SPY")
"""
    
    def parse_advanced_strategy(self, strategy_data: Dict[str, Any]) -> str:
        """
        Parse advanced strategy data structure to QuantConnect code
        """
        if not strategy_data:
            return self._generate_default_code()
        
        # Extract components from strategy data
        symbols = strategy_data.get('symbols', ['SPY'])
        indicators = strategy_data.get('indicators', [])
        rules = strategy_data.get('rules', [])
        timeframe = strategy_data.get('timeframe', 'Resolution.Daily')
        
        # Generate code based on advanced data structure
        return self._generate_advanced_strategy_code(symbols, indicators, rules, timeframe)
    
    def _generate_advanced_strategy_code(self, symbols: List[str], indicators: List[Dict], 
                                       rules: List[Dict], timeframe: str) -> str:
        """Generate advanced strategy code from structured data"""
        
        code = """from AlgorithmImports import *

class TradingAlgorithm(QCAlgorithm):
    def Initialize(self):
        # Set start and end dates
        self.SetStartDate(2020, 1, 1)
        self.SetEndDate(2023, 12, 31)
        self.SetCash(100000)
        
        # Add symbols
"""
        
        # Add symbols
        for symbol in symbols:
            code += f'        self.AddEquity("{symbol}", {timeframe})\n'
        
        # Add indicators
        if indicators:
            code += "\n        # Add indicators\n"
            for indicator in indicators:
                indicator_type = indicator.get('type', 'SMA')
                period = indicator.get('period', 20)
                name = indicator.get('name', indicator_type.lower())
                
                if indicator_type == 'SMA':
                    code += f"        self.{name} = self.SMA(self.Symbol('{symbols[0]}'), {period})\n"
                elif indicator_type == 'EMA':
                    code += f"        self.{name} = self.EMA(self.Symbol('{symbols[0]}'), {period})\n"
                elif indicator_type == 'RSI':
                    code += f"        self.{name} = self.RSI(self.Symbol('{symbols[0]}'), {period})\n"
        
        # Add OnData method with rules
        code += """
    def OnData(self, data):
        # Check if indicators are ready
        if not self.Portfolio.Invested:
        """
        
        # Add rules logic
        for rule in rules:
            condition = rule.get('condition', {})
            action = rule.get('action', {})
            
            if condition.get('type') == 'price_above_indicator':
                indicator_name = condition.get('indicator', 'sma')
                code += f"            if self.Securities['{symbols[0]}'].Price > self.{indicator_name}.Current.Value:\n"
                if action.get('type') == 'buy':
                    code += f"                self.SetHoldings('{symbols[0]}', {action.get('quantity', 1.0)})\n"
        
        code += f"""
        # Exit conditions
        if self.Portfolio.Invested and self.Securities['{symbols[0]}'].Price < self.sma.Current.Value * 0.95:
"""
        
        return code

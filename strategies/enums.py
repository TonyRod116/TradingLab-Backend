"""
Enums and constants for trading strategies
"""

# Supported symbols
SUPPORTED_SYMBOLS = [
    'ES', 'NQ', 'YM', 'RTY',  # Equity Index Futures
    'GC', 'SI', 'CL', 'NG',   # Commodities
    'EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD', 'NZDUSD',  # Forex
    'BTC', 'ETH', 'LTC', 'XRP', 'ADA', 'DOT',  # Crypto
    'SPY', 'QQQ', 'IWM', 'DIA', 'VIX', 'ARKK', 'TQQQ', 'SQQQ',  # ETFs
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA'  # Stocks
]

# Supported timeframes
SUPPORTED_TIMEFRAMES = [
    '1m', '2m', '3m', '4m', '5m', '6m', '7m', '8m', '9m', '10m', '12m', '15m', '20m', '30m', '45m',
    '1h', '2h', '3h', '4h', '6h', '8h', '12h',
    '1d', '2d', '3d',
    '1w', '2w',
    '1M', '3M',
    '1Y'
]

# Supported indicators
SUPPORTED_INDICATORS = [
    # Moving Averages
    'sma_20', 'sma_50', 'sma_200',
    'ema_20', 'ema_50', 'ema_200',
    'vwap',
    # VWAP Bands
    'vwap_plus_0_5', 'vwap_plus_1_0', 'vwap_plus_1_5', 'vwap_plus_2_0', 'vwap_plus_2_5',
    'vwap_minus_0_5', 'vwap_minus_1_0', 'vwap_minus_1_5', 'vwap_minus_2_0', 'vwap_minus_2_5',
    # Momentum
    'rsi', 'rsi_20', 'rsi_30', 'rsi_50', 'rsi_70', 'rsi_80',
    'macd', 'macd_signal', 'macd_histogram',
    'stochastic_k', 'stochastic_d',
    # Volatility
    'atr', 'bb_upper', 'bb_middle', 'bb_lower',
    # Price Data
    'open', 'high', 'low', 'close', 'volume'
]

# Supported operators
SUPPORTED_OPERATORS = [
    'gt', 'lt', 'gte', 'lte', 'eq', 'ne',
    'cross_up', 'cross_down'
]

# Supported stop loss types
STOP_LOSS_TYPES = ['percentage', 'points', 'ticks', 'atr']

# Supported take profit types
TAKE_PROFIT_TYPES = ['percentage', 'points', 'ticks', 'atr']

# Strategy status
STRATEGY_STATUS = ['DRAFT', 'READY', 'ACTIVE', 'INACTIVE']

# Rule types
RULE_TYPES = ['condition', 'action', 'filter']

# Action types
ACTION_TYPES = ['buy', 'sell', 'close', 'modify', 'wait']

# Logical operators
LOGICAL_OPERATORS = ['and', 'or']

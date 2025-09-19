"""
Enums and constants for trading strategies
"""

# Supported symbols - SOLO ES (E-mini S&P 500)
SUPPORTED_SYMBOLS = [
    'ES'  # E-mini S&P 500 - único símbolo disponible
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

# ---- NUEVO: alias y normalización ----
SYMBOL_ALIASES = {
    # SOLO ES (E-mini S&P 500) - único símbolo disponible
    'es': 'ES', 'sp500': 'ES', 'spx': 'ES', 's&p500': 'ES', 's&p': 'ES',
    'sp500futures': 'ES', 'emini': 'ES', 'emini_sp500': 'ES', 'sp500_emini': 'ES'
}

TIMEFRAME_ALIASES = {
    '1d': '1d', 'd': '1d', 'daily': '1d',
    '1h': '1h', 'h': '1h', 'hour': '1h',
    '15m': '15m', '5m': '5m', '1m': '1m',
    '2m': '2m', '3m': '3m', '4m': '4m', '6m': '6m', '7m': '7m', '8m': '8m', '9m': '9m', '10m': '10m',
    '12m': '12m', '20m': '20m', '30m': '30m', '45m': '45m',
    '2h': '2h', '3h': '3h', '4h': '4h', '6h': '6h', '8h': '8h', '12h': '12h',
    '2d': '2d', '3d': '3d',
    '1w': '1w', '2w': '2w', 'weekly': '1w',
    '1m': '1M', '3m': '3M', 'monthly': '1M',
    '1y': '1Y', 'yearly': '1Y'
}

INDICATOR_ALIASES = {
    'sma': 'SMA', 'ema': 'EMA', 'rsi': 'RSI', 'macd': 'MACD', 'atr': 'ATR',
    'vwap': 'VWAP', 'stochastic': 'STOCHASTIC', 'bb': 'BB', 'bollinger': 'BB'
}

OPERATOR_ALIASES = {
    '&&': 'and', '||': 'or', '>': 'gt', '<': 'lt', '>=': 'gte', '<=': 'lte',
    '==': 'eq', '!=': 'ne', '=': 'eq'
}

STOP_TP_ALIASES = {
    'take profit': 'take_profit', 'take-profit': 'take_profit', 'takeprofit': 'take_profit',
    'stop loss': 'stop_loss', 'stop-loss': 'stop_loss', 'stoploss': 'stop_loss'
}

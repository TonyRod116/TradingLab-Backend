from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class DSLToLeanService:
    """
    Service that converts DSL to executable LEAN (QuantConnect) Python code
    """
    
    def generate_lean(self, dsl: Dict[str, Any]) -> str:
        """
        Generate complete LEAN algorithm from DSL
        """
        try:
            code_parts = []
            
            # Header and imports
            code_parts.append(self._generate_header())
            
            # Class definition and Initialize method
            code_parts.append(self._generate_initialize(dsl))
            
            # OnData method with entry/exit logic
            code_parts.append(self._generate_ondata(dsl))
            
            # Helper methods
            code_parts.append(self._generate_helper_methods(dsl))
            
            # Footer
            code_parts.append(self._generate_footer())
            
            return '\n\n'.join(code_parts)
            
        except Exception as e:
            logger.error(f"Error generating LEAN code: {e}")
            raise ValueError(f"Failed to generate LEAN code: {str(e)}")
    
    def _generate_header(self) -> str:
        """Generate imports and class header"""
        return '''# AUTO-GENERATED
from AlgorithmImports import *
from datetime import datetime, timedelta
import numpy as np

class TradingStrategy(QCAlgorithm):
    def __init__(self):
        super().__init__()
        self.indicators = {}
        self.entry_conditions_met = False
        self.position_size = 0
        self.entry_price = 0
        self.stop_loss_price = 0
        self.take_profit_price = 0'''
    
    def _generate_initialize(self, dsl: Dict[str, Any]) -> str:
        """Generate Initialize method"""
        universe = dsl['universe']
        timeframe = dsl['timeframe']
        positioning = dsl['positioning']
        
        # Parse dates
        start_date = timeframe['start']
        end_date = timeframe['end']
        resolution = timeframe['resolution']
        
        # Get symbol
        symbol = universe.get('symbol', 'SPY')
        
        # Get resolution enum
        resolution_map = {
            'Minute': 'Resolution.Minute',
            'Second': 'Resolution.Second', 
            'Hour': 'Resolution.Hour',
            'Daily': 'Resolution.Daily'
        }
        res_enum = resolution_map.get(resolution, 'Resolution.Minute')
        
        code = f'''    def Initialize(self):
        # Set start and end dates
        self.SetStartDate({start_date[:4]}, {start_date[5:7]}, {start_date[8:10]})
        self.SetEndDate({end_date[:4]}, {end_date[5:7]}, {end_date[8:10]})
        
        # Set cash
        self.SetCash(100000)
        
        # Add symbol
        self.symbol = self.AddEquity("{symbol}", {res_enum}).Symbol
        
        # Set benchmark
        self.SetBenchmark("{symbol}")
        
        # Initialize indicators based on entry rules
        self._initialize_indicators()
        
        # Set warm up period
        self.SetWarmUp(50, {res_enum})
        
        # Position sizing
        self.risk_per_trade = {positioning['risk_per_trade_pct']} / 100.0
        self.max_positions = {positioning['max_concurrent_positions']}
        self.position_side = "{positioning['side']}"
        
        self.Debug("Strategy initialized")'''
        
        return code
    
    def _generate_ondata(self, dsl: Dict[str, Any]) -> str:
        """Generate OnData method with entry/exit logic"""
        entry_rules = dsl['entry_rules']
        exit_rules = dsl['exit_rules']
        positioning = dsl['positioning']
        symbol = dsl['universe']['symbol']
        
        # Generate entry conditions
        entry_conditions = self._generate_entry_conditions(entry_rules, symbol)
        
        # Generate exit conditions
        exit_conditions = self._generate_exit_conditions(exit_rules, symbol)
        
        code = f'''    def OnData(self, data):
        # Skip if warming up
        if self.IsWarmingUp:
            return
            
        # Check if indicators are ready
        if not self._indicators_ready():
            return
            
        # Check if we can enter new positions
        if self._can_enter_position():
            if {entry_conditions}:
                self._enter_position(data)
        
        # Check exit conditions for existing positions
        if self.Portfolio.Invested:
            if {exit_conditions}:
                self._exit_position(data)'''
        
        return code
    
    def _generate_helper_methods(self, dsl: Dict[str, Any]) -> str:
        """Generate helper methods"""
        entry_rules = dsl['entry_rules']
        exit_rules = dsl['exit_rules']
        
        # Generate indicator initialization
        indicator_init = self._generate_indicator_initialization(entry_rules)
        
        code = f'''    def _initialize_indicators(self):
        """Initialize all required indicators"""
        {indicator_init}
        
    def _indicators_ready(self) -> bool:
        """Check if all indicators are ready"""
        return all(indicator.IsReady for indicator in self.indicators.values())
        
    def _can_enter_position(self) -> bool:
        """Check if we can enter a new position"""
        if self.position_side == "long_only" and self.Portfolio.Invested:
            return False
        if self.position_side == "short_only" and self.Portfolio.Invested:
            return False
        if self.position_side == "both" and len(self.Portfolio) >= self.max_positions:
            return False
        return True
        
    def _check_entry_conditions(self, data) -> bool:
        """Check if entry conditions are met"""
        # This will be populated based on entry rules
        return False
        
    def _enter_position(self, data):
        """Enter a new position"""
        # This will be populated based on positioning rules
        pass
        
    def _check_exit_conditions(self, data) -> bool:
        """Check if exit conditions are met"""
        # This will be populated based on exit rules
        return False
        
    def _exit_position(self, data):
        """Exit current position"""
        self.Liquidate(self.symbol)
        self.Debug(f"Exited position at {data[self.symbol].Price}")
        
    def _calculate_position_size(self, data) -> float:
        """Calculate position size based on risk management"""
        if not self.indicators.get('atr'):
            return self.risk_per_trade
            
        # ATR-based position sizing
        atr = self.indicators['atr'].Current.Value
        stop_distance = atr * 2.0  # 2 ATR stop
        position_size = (self.Portfolio.Cash * self.risk_per_trade) / stop_distance
        return min(position_size, 1.0)  # Max 100% of portfolio'''
        
        return code
    
    def _generate_footer(self) -> str:
        """Generate footer methods"""
        return '''    def OnOrderEvent(self, orderEvent):
        """Handle order events"""
        if orderEvent.Status == OrderStatus.Filled:
            self.Debug(f"Order filled: {orderEvent}")
            
    def OnEndOfAlgorithm(self):
        """Called at the end of the algorithm"""
        self.Debug("Algorithm completed")'''
    
    def _generate_indicator_code(self, indicator_config: Dict[str, Any]) -> str:
        """Generate code for a specific indicator"""
        indicator = indicator_config['indicator']
        period = indicator_config.get('period', 14)
        
        if indicator == 'VWAP':
            return f'self.indicators["vwap"] = self.VWAP(self.symbol, {period})'
        elif indicator == 'SMA':
            return f'self.indicators["sma_{period}"] = self.SMA(self.symbol, {period})'
        elif indicator == 'EMA':
            return f'self.indicators["ema_{period}"] = self.EMA(self.symbol, {period})'
        elif indicator == 'RSI':
            return f'self.indicators["rsi_{period}"] = self.RSI(self.symbol, {period})'
        elif indicator == 'MACD':
            return f'self.indicators["macd"] = self.MACD(self.symbol, 12, 26, 9)'
        
        return ''
    
    def _generate_condition_code(self, condition: Dict[str, Any]) -> str:
        """Generate code for a specific condition"""
        if condition['type'] == 'indicator_condition':
            return self._generate_indicator_condition_code(condition)
        elif condition['type'] == 'orderflow_condition':
            return self._generate_orderflow_condition_code(condition)
        
        return ''
    
    def _generate_indicator_condition_code(self, condition: Dict[str, Any]) -> str:
        """Generate code for indicator condition"""
        left = condition['left']
        operator = condition['operator']
        right = condition['right']
        
        # This is a simplified version - in practice you'd need more complex logic
        # to handle all the different operators and combinations
        return f'# Indicator condition: {left["indicator"]} {operator} {right}'
    
    def _generate_orderflow_condition_code(self, condition: Dict[str, Any]) -> str:
        """Generate code for orderflow condition"""
        name = condition['name']
        lookback = condition['lookback_bars']
        threshold = condition['threshold']
        
        return f'# Orderflow condition: {name} with {lookback} bars, threshold {threshold}'
    
    def _generate_entry_conditions(self, entry_rules: List[Dict[str, Any]], symbol: str) -> str:
        """Generate entry conditions from DSL rules"""
        conditions = []
        
        for rule in entry_rules:
            if rule['type'] == 'indicator_condition':
                condition = self._generate_indicator_condition(rule, symbol)
                conditions.append(condition)
            elif rule['type'] == 'orderflow_condition':
                condition = self._generate_orderflow_condition(rule, symbol)
                conditions.append(condition)
        
        if not conditions:
            return "False"  # No entry conditions
        
        return " and ".join(conditions)
    
    def _generate_exit_conditions(self, exit_rules: List[Dict[str, Any]], symbol: str) -> str:
        """Generate exit conditions from DSL rules"""
        conditions = []
        
        for rule in exit_rules:
            if rule['type'] == 'take_profit':
                if 'rr' in rule and rule['rr']:
                    conditions.append(f"self._check_take_profit_rr({rule['rr']})")
                elif 'target_pct' in rule and rule['target_pct']:
                    conditions.append(f"self._check_take_profit_pct({rule['target_pct']})")
            elif rule['type'] == 'stop_loss':
                if 'atr_mult' in rule and rule['atr_mult']:
                    conditions.append(f"self._check_stop_loss_atr({rule['atr_mult']})")
                elif 'pct' in rule and rule['pct']:
                    conditions.append(f"self._check_stop_loss_pct({rule['pct']})")
        
        if not conditions:
            return "False"  # No exit conditions
        
        return " or ".join(conditions)
    
    def _generate_indicator_condition(self, rule: Dict[str, Any], symbol: str) -> str:
        """Generate code for an indicator condition"""
        left = rule['left']
        operator = rule['operator']
        right = rule['right']
        
        # Get indicator name
        indicator_name = self._get_indicator_name(left['indicator'], left.get('period', 14))
        
        # Generate left side
        if left['indicator'] == 'VWAP':
            left_code = f"self.indicators['{indicator_name}'].Current.Value"
        else:
            left_code = f"self.indicators['{indicator_name}'].Current.Value"
        
        # Generate right side
        if 'value' in right and right['value'] is not None:
            right_code = str(right['value'])
        elif 'indicator' in right and right['indicator']:
            right_indicator = self._get_indicator_name(right['indicator']['indicator'], right['indicator'].get('period', 14))
            right_code = f"self.indicators['{right_indicator}'].Current.Value"
        else:
            right_code = "0"
        
        # Generate operator
        operator_map = {
            'lt': '<',
            'gt': '>',
            'cross_above': '>',
            'cross_below': '<',
            'cross_below_or_equal': '<='
        }
        op = operator_map.get(operator, '<')
        
        # For cross conditions, we need to check current vs previous
        if operator.startswith('cross'):
            if operator == 'cross_above':
                return f"({left_code} > {right_code} and self.indicators['{indicator_name}'].Previous.Value <= {right_code})"
            elif operator == 'cross_below':
                return f"({left_code} < {right_code} and self.indicators['{indicator_name}'].Previous.Value >= {right_code})"
            elif operator == 'cross_below_or_equal':
                return f"({left_code} <= {right_code} and self.indicators['{indicator_name}'].Previous.Value > {right_code})"
        
        return f"({left_code} {op} {right_code})"
    
    def _generate_orderflow_condition(self, rule: Dict[str, Any], symbol: str) -> str:
        """Generate code for an orderflow condition"""
        name = rule['name']
        lookback = rule['lookback_bars']
        threshold = rule['threshold']
        
        # This is a simplified implementation
        # In a real system, you'd need more sophisticated order flow analysis
        return f"self._check_orderflow_{name}({lookback}, {threshold})"
    
    def _get_indicator_name(self, indicator: str, period: int) -> str:
        """Get the indicator variable name"""
        if indicator == 'VWAP':
            return 'vwap'
        elif indicator == 'SMA':
            return f'sma_{period}'
        elif indicator == 'EMA':
            return f'ema_{period}'
        elif indicator == 'RSI':
            return f'rsi_{period}'
        elif indicator == 'MACD':
            return 'macd'
        else:
            return f'{indicator.lower()}_{period}'
    
    def _generate_indicator_initialization(self, entry_rules: List[Dict[str, Any]]) -> str:
        """Generate indicator initialization code"""
        indicators = set()
        
        for rule in entry_rules:
            if rule['type'] == 'indicator_condition':
                left = rule['left']
                right = rule['right']
                
                # Add left indicator
                indicators.add((left['indicator'], left.get('period', 14)))
                
                # Add right indicator if it's an indicator
                if 'indicator' in right and right['indicator']:
                    indicators.add((right['indicator']['indicator'], right['indicator'].get('period', 14)))
        
        # Generate initialization code
        init_code = []
        for indicator, period in indicators:
            if indicator == 'VWAP':
                init_code.append(f"        self.indicators['vwap'] = self.VWAP(self.symbol, {period})")
            elif indicator == 'SMA':
                init_code.append(f"        self.indicators['sma_{period}'] = self.SMA(self.symbol, {period})")
            elif indicator == 'EMA':
                init_code.append(f"        self.indicators['ema_{period}'] = self.EMA(self.symbol, {period})")
            elif indicator == 'RSI':
                init_code.append(f"        self.indicators['rsi_{period}'] = self.RSI(self.symbol, {period})")
            elif indicator == 'MACD':
                init_code.append(f"        self.indicators['macd'] = self.MACD(self.symbol, 12, 26, 9)")
        
        # Add ATR for stop loss calculations
        init_code.append("        self.indicators['atr'] = self.ATR(self.symbol, 14)")
        
        return '\n'.join(init_code) if init_code else "        pass"

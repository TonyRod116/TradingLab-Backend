"""
Simple LEAN code generator for Strategy Builder
"""

from typing import Dict, Any


class SimpleLeanGenerator:
    """Simple LEAN code generator for Strategy Builder data"""
    
    def generate_lean(self, strategy_data: Dict[str, Any]) -> str:
        """Generate simple LEAN code from strategy data"""
        
        rules = strategy_data.get('rules', {})
        symbols = rules.get('symbols', ['SPY'])
        timeframe = rules.get('timeframe', 'daily')
        
        # Convert timeframe to LEAN resolution
        resolution_map = {
            'daily': 'Resolution.Daily',
            'hourly': 'Resolution.Hour',
            'minute': 'Resolution.Minute'
        }
        resolution = resolution_map.get(timeframe, 'Resolution.Daily')
        
        # Get entry and exit conditions
        entry_conditions = rules.get('entry_conditions', [])
        exit_conditions = rules.get('exit_conditions', [])
        
        # Generate symbol code
        symbol_code = []
        for symbol in symbols:
            symbol_code.append(f'        self.AddEquity("{symbol}", {resolution})')
        
        # Generate indicator initialization
        indicator_code = self._generate_indicators(entry_conditions + exit_conditions)
        
        # Generate entry/exit logic
        entry_logic = self._generate_entry_logic(entry_conditions)
        exit_logic = self._generate_exit_logic(exit_conditions)
        
        lean_code = f'''# AUTO-GENERATED LEAN CODE
from AlgorithmImports import *
from datetime import datetime, timedelta

class TradingStrategy(QCAlgorithm):
    def Initialize(self):
        # Set dates
        self.SetStartDate(DateTime(2023, 1, 1))
        self.SetEndDate(DateTime(2024, 1, 1))
        
        # Set cash
        self.SetCash(100000)
        
        # Set benchmark
        self.SetBenchmark("SPY")
        
        # Add symbols
{chr(10).join(symbol_code)}
        
        # Initialize indicators
{indicator_code}
        
        # Position tracking
        self.entry_price = 0
        self.position_size = 0
        self.is_in_position = False
    
    def OnData(self, data):
        # Skip if no data
        if not data.Bars.ContainsKey(self.Symbol):
            return
        
        # Get current price
        current_price = data.Bars[self.Symbol].Close
        
        # Entry logic
{entry_logic}
        
        # Exit logic
{exit_logic}
    
    def EnterPosition(self, price):
        """Enter a long position"""
        if not self.is_in_position:
            self.SetHoldings(self.Symbol, 1.0)
            self.entry_price = price
            self.is_in_position = True
            self.Debug(f"Entered position at {{price}}")
    
    def ExitPosition(self, price):
        """Exit the current position"""
        if self.is_in_position:
            self.Liquidate(self.Symbol)
            self.is_in_position = False
            self.Debug(f"Exited position at {{price}}")
    
    def IsEntryConditionMet(self, data):
        """Check if entry conditions are met"""
        if not data.Bars.ContainsKey(self.Symbol):
            return False
        
        current_price = data.Bars[self.Symbol].Close
        
        # Simple RSI entry condition
        if hasattr(self, 'rsi') and self.rsi.IsReady:
            return self.rsi.Current.Value < 30
        
        return False
    
    def IsExitConditionMet(self, data):
        """Check if exit conditions are met"""
        if not data.Bars.ContainsKey(self.Symbol):
            return False
        
        current_price = data.Bars[self.Symbol].Close
        
        # Simple RSI exit condition
        if hasattr(self, 'rsi') and self.rsi.IsReady:
            return self.rsi.Current.Value > 70
        
        return False
'''
        
        return lean_code
    
    def _generate_indicators(self, conditions):
        """Generate indicator initialization code"""
        indicator_code = []
        
        # Check if RSI is needed
        needs_rsi = any('RSI' in str(cond) for cond in conditions)
        if needs_rsi:
            indicator_code.append('        # RSI indicator')
            indicator_code.append('        self.rsi = self.RSI(self.Symbol, 14)')
        
        # Check if SMA is needed
        needs_sma = any('SMA' in str(cond) for cond in conditions)
        if needs_sma:
            indicator_code.append('        # SMA indicator')
            indicator_code.append('        self.sma = self.SMA(self.Symbol, 20)')
        
        return '\n'.join(indicator_code) if indicator_code else '        # No indicators needed'
    
    def _generate_entry_logic(self, entry_conditions):
        """Generate entry logic"""
        if not entry_conditions:
            return '        # No entry conditions'
        
        logic = ['        # Entry conditions']
        logic.append('        if self.IsEntryConditionMet(data):')
        logic.append('            self.EnterPosition(current_price)')
        
        return '\n'.join(logic)
    
    def _generate_exit_logic(self, exit_conditions):
        """Generate exit logic"""
        if not exit_conditions:
            return '        # No exit conditions'
        
        logic = ['        # Exit conditions']
        logic.append('        if self.IsExitConditionMet(data):')
        logic.append('            self.ExitPosition(current_price)')
        
        return '\n'.join(logic)

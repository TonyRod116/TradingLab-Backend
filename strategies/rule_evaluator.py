"""
Real Rule Evaluator for Strategy Backtesting
Evaluates actual strategy rules using technical indicators
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from decimal import Decimal

from indicators.services import TechnicalAnalysisService


class StrategyRuleEvaluator:
    """Evaluates strategy rules using real technical indicators"""
    
    def __init__(self, data: pd.DataFrame):
        """
        Initialize rule evaluator with market data
        
        Args:
            data: DataFrame with OHLCV market data
        """
        self.data = data
        self.indicators_service = TechnicalAnalysisService(data)
        self.indicators_data = None
        self._calculate_all_indicators()
    
    def _calculate_all_indicators(self):
        """Pre-calculate all indicators for the entire dataset"""
        try:
            self.indicators_data = self.indicators_service.calculate_all_indicators()
        except Exception as e:
            print(f"Warning: Could not calculate indicators: {e}")
            self.indicators_data = self.data.copy()
    
    def evaluate_entry_rules(self, row_index: int, entry_rules: Dict) -> bool:
        """
        Evaluate entry rules for a specific data point
        
        Args:
            row_index: Index of current data row
            entry_rules: Entry rules configuration from strategy
            
        Returns:
            True if entry conditions are met
        """
        if not entry_rules or not isinstance(entry_rules, dict):
            return False
        
        try:
            # Handle different rule formats
            if 'rules' in entry_rules:
                # Multiple rules format
                return self._evaluate_rule_set(row_index, entry_rules['rules'])
            elif 'condition_type' in entry_rules:
                # Single rule format
                return self._evaluate_single_rule(row_index, entry_rules)
            else:
                # Legacy or simple format - try to parse
                return self._evaluate_legacy_rules(row_index, entry_rules)
                
        except Exception as e:
            print(f"Error evaluating entry rules: {e}")
            return False
    
    def evaluate_exit_rules(self, row_index: int, exit_rules: Dict, 
                          position: Dict) -> Optional[str]:
        """
        Evaluate exit rules for a specific data point
        
        Args:
            row_index: Index of current data row
            exit_rules: Exit rules configuration from strategy
            position: Current position information
            
        Returns:
            Exit reason if conditions are met, None otherwise
        """
        if not exit_rules or not isinstance(exit_rules, dict):
            return None
        
        try:
            # Handle different rule formats
            if 'rules' in exit_rules:
                # Multiple rules format
                if self._evaluate_rule_set(row_index, exit_rules['rules']):
                    return "Rule Exit"
            elif 'condition_type' in exit_rules:
                # Single rule format
                if self._evaluate_single_rule(row_index, exit_rules):
                    return "Rule Exit"
            else:
                # Legacy or simple format
                if self._evaluate_legacy_rules(row_index, exit_rules):
                    return "Rule Exit"
                    
        except Exception as e:
            print(f"Error evaluating exit rules: {e}")
            
        return None
    
    def _evaluate_rule_set(self, row_index: int, rules: List[Dict]) -> bool:
        """Evaluate a set of rules (AND logic by default)"""
        if not rules:
            return False
        
        for rule in rules:
            if rule.get('rule_type') == 'condition':
                if not self._evaluate_single_rule(row_index, rule):
                    return False
            elif rule.get('rule_type') == 'action':
                # Action rules don't affect entry/exit evaluation
                continue
        
        return True
    
    def _evaluate_single_rule(self, row_index: int, rule: Dict) -> bool:
        """Evaluate a single rule condition"""
        condition_type = rule.get('condition_type', 'indicator')
        
        if condition_type == 'indicator':
            return self._evaluate_indicator_condition(row_index, rule)
        elif condition_type == 'price':
            return self._evaluate_price_condition(row_index, rule)
        elif condition_type == 'volume':
            return self._evaluate_volume_condition(row_index, rule)
        else:
            print(f"Unknown condition type: {condition_type}")
            return False
    
    def _evaluate_indicator_condition(self, row_index: int, rule: Dict) -> bool:
        """Evaluate indicator-based conditions"""
        left_operand = rule.get('left_operand', '')
        operator = rule.get('operator', '')
        right_operand = rule.get('right_operand', '')
        
        # Get left value (indicator or price)
        left_value = self._get_value(row_index, left_operand)
        if left_value is None:
            return False
        
        # Get right value (could be number, indicator, or price)
        right_value = self._get_value(row_index, right_operand)
        if right_value is None:
            return False
        
        # Apply operator
        return self._apply_operator(left_value, operator, right_value)
    
    def _evaluate_price_condition(self, row_index: int, rule: Dict) -> bool:
        """Evaluate price-based conditions"""
        return self._evaluate_indicator_condition(row_index, rule)
    
    def _evaluate_volume_condition(self, row_index: int, rule: Dict) -> bool:
        """Evaluate volume-based conditions"""
        return self._evaluate_indicator_condition(row_index, rule)
    
    def _evaluate_legacy_rules(self, row_index: int, rules: Dict) -> bool:
        """Handle legacy or simple rule formats"""
        # For now, implement a simple fallback
        # This could be expanded based on actual legacy formats found
        return False
    
    def _get_value(self, row_index: int, operand: str) -> Optional[float]:
        """
        Get value for an operand (indicator, price, or number)
        
        Args:
            row_index: Current data row index
            operand: Operand name or value
            
        Returns:
            Float value or None if not found
        """
        if row_index >= len(self.indicators_data):
            return None
        
        row = self.indicators_data.iloc[row_index]
        
        # Check if it's a direct number
        try:
            return float(operand)
        except ValueError:
            pass
        
        # Map common operand names to column names
        operand_mapping = {
            'close': 'close',
            'open': 'open', 
            'high': 'high',
            'low': 'low',
            'volume': 'volume',
            'rsi': 'rsi',
            'sma_20': 'sma_20',
            'sma_50': 'sma_50',
            'ema_20': 'ema_20',
            'ema_50': 'ema_50',
            'vwap': 'vwap',
            'atr': 'atr',
            'macd_line': 'macd_line',
            'macd_signal': 'macd_signal',
            'macd_histogram': 'macd_histogram',
            'stoch_k': 'stoch_k',
            'stoch_d': 'stoch_d',
            'bb_upper': 'bb_upper',
            'bb_middle': 'bb_middle',
            'bb_lower': 'bb_lower'
        }
        
        # Get column name
        column_name = operand_mapping.get(operand.lower(), operand.lower())
        
        # Check if column exists and get value
        if column_name in row.index:
            value = row[column_name]
            if pd.notna(value):
                return float(value)
        
        # Try alternative names
        if operand.lower() == 'price':
            return float(row['close']) if 'close' in row.index else None
        
        return None
    
    def _apply_operator(self, left: float, operator: str, right: float) -> bool:
        """
        Apply comparison operator
        
        Args:
            left: Left operand value
            operator: Comparison operator
            right: Right operand value
            
        Returns:
            Boolean result of comparison
        """
        operators = {
            'gt': lambda l, r: l > r,
            '>': lambda l, r: l > r,
            'gte': lambda l, r: l >= r,
            '>=': lambda l, r: l >= r,
            'lt': lambda l, r: l < r,
            '<': lambda l, r: l < r,
            'lte': lambda l, r: l <= r,
            '<=': lambda l, r: l <= r,
            'eq': lambda l, r: abs(l - r) < 1e-6,  # Float equality
            '==': lambda l, r: abs(l - r) < 1e-6,
            'ne': lambda l, r: abs(l - r) >= 1e-6,
            '!=': lambda l, r: abs(l - r) >= 1e-6,
            'above': lambda l, r: l > r,
            'below': lambda l, r: l < r,
        }
        
        op_func = operators.get(operator.lower())
        if op_func:
            return op_func(left, right)
        
        # Handle crossing operators (need historical data)
        if operator.lower() in ['crosses_above', 'crosses_below']:
            return self._handle_crossing_operator(left, right, operator.lower())
        
        print(f"Unknown operator: {operator}")
        return False
    
    def _handle_crossing_operator(self, left: float, right: float, 
                                operator: str) -> bool:
        """Handle crossing operators (requires historical context)"""
        # For now, approximate with simple comparison
        # TODO: Implement proper crossing detection with previous values
        if operator == 'crosses_above':
            return left > right
        elif operator == 'crosses_below':
            return left < right
        return False
    
    def get_current_indicators(self, row_index: int) -> Dict[str, float]:
        """Get all current indicator values for debugging"""
        if row_index >= len(self.indicators_data):
            return {}
        
        row = self.indicators_data.iloc[row_index]
        return {col: float(val) for col, val in row.items() 
                if pd.notna(val) and col != 'date'}
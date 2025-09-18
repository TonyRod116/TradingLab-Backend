"""
Backtesting Engine using optimized Parquet data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple, Optional, Union
import time
import re

from market_data.parquet_service import ParquetDataService
from .models import Strategy, BacktestResult, Trade, EquityCurvePoint
from .metrics_calculator import (
    calculate_all_metrics, calculate_strategy_rating, get_rating_color
)

# ES (E-mini S&P 500) constants
ES_TICK = 0.25                # tamaño de tick de ES
ES_POINT_VALUE = 50.0         # $ por punto de ES

# Indicator patterns for dynamic calculation
INDICATOR_PATTERNS = {
    r'^sma_(\d+)$':        'sma',
    r'^ema_(\d+)$':        'ema',
    r'^rsi(?:_(\d+))?$':   'rsi',        # rsi, rsi_20, rsi_30...
    r'^vwap$':             'vwap',
    r'^vwap_(plus|minus)_(\d+_\d)$': 'vwap_band',   # vwap_plus_1_5 (1.5σ)
    r'^bb_(upper|middle|lower)(?:_(\d+))?$': 'bb',   # bb_upper, bb_middle, bb_lower(_20)
    r'^macd$':             'macd',
    r'^macd_signal$':      'macd_signal',
    r'^macd_histogram$':   'macd_histogram',
    r'^stochastic_k$':     'stoch_k',
    r'^stochastic_d$':     'stoch_d',
    r'^(open|high|low|close|volume)$': 'price'
}


class BacktestEngine:
    """Engine for backtesting trading strategies using Parquet data"""
    
    def __init__(self):
        self.parquet_service = ParquetDataService()
        self._prev_row_cache = None  # For cross_up/cross_down detection
    
    def run_backtest(self, strategy: Strategy, start_date: datetime, end_date: datetime,
                    initial_capital: Decimal = None, commission: Decimal = Decimal('4.00'),
                    slippage: Decimal = Decimal('0.5'), chunk_size: int = 10000) -> BacktestResult:
        """
        Run backtest for a strategy
        
        Args:
            strategy: Strategy to backtest
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Initial capital (uses strategy.initial_capital if None)
            commission: Commission per trade
            slippage: Slippage percentage
        
        Returns:
            BacktestResult with performance metrics
        """
        # Use strategy's initial capital if not provided
        if initial_capital is None:
            initial_capital = strategy.initial_capital
        start_time = time.time()
        
        try:
            # Validate operands before processing
            self._validate_operands(strategy)
            
            # Get market data using optimized Parquet service
            df = self.parquet_service.get_candles(
                symbol=strategy.symbol,
                timeframe=strategy.timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                raise ValueError(f"No data found for {strategy.symbol} {strategy.timeframe}")

            # Calculate required indicators
            df = self._ensure_indicators(df, strategy)
            
            # Determine data source
            data_source = 'parquet' if self.parquet_service.is_parquet_available(
                strategy.symbol, strategy.timeframe
            ) else 'database'
            
            # Run backtest simulation with chunking for large datasets
            trades, performance, equity_points = self._simulate_strategy_optimized(
                df, strategy, initial_capital, commission, slippage, chunk_size
            )
            
            # Calculate execution time
            execution_time = time.time() - start_time
            
            # Create backtest result
            backtest_result = BacktestResult.objects.create(
                strategy=strategy,
                user=strategy.user,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                commission=commission,
                slippage=slippage,
                execution_time=execution_time,
                data_source=data_source,
                **performance
            )
            
            # Save trades in bulk for better performance
            if trades:
                trade_objects = [
                    Trade(backtest=backtest_result, **trade_data) 
                    for trade_data in trades
                ]
                Trade.objects.bulk_create(trade_objects)
            
            # Save equity curve points in bulk for better performance
            if equity_points:
                equity_objects = [
                    EquityCurvePoint(
                        backtest=backtest_result,
                        timestamp=point['timestamp'],
                        equity_value=point['equity_value'],
                        drawdown=point['drawdown']
                    )
                    for point in equity_points
                ]
                EquityCurvePoint.objects.bulk_create(equity_objects)
            
            return backtest_result
            
        except Exception as e:
            raise Exception(f"Backtest failed: {str(e)}")
    
    def _simulate_strategy_optimized(self, df: pd.DataFrame, strategy: Strategy,
                                   initial_capital: Decimal, commission: Decimal,
                                   slippage: Decimal, chunk_size: int = 10000) -> Tuple[List[Dict], Dict, List[Dict]]:
        """
        Optimized strategy simulation using vectorized operations
        
        Args:
            df: Market data DataFrame
            strategy: Strategy to simulate
            initial_capital: Initial capital
            commission: Commission per trade
            slippage: Slippage percentage
            chunk_size: Size of chunks for processing large datasets
        
        Returns:
            Tuple of (trades_list, performance_metrics, equity_curve_points)
        """
        trades = []
        equity_points = []  # Store all equity curve points
        portfolio_value = float(initial_capital)
        current_position = None
        peak_value = portfolio_value
        max_drawdown = 0
        
        # Process data in chunks for large datasets
        total_rows = len(df)
        if total_rows > chunk_size:
            # Process in chunks
            for start_idx in range(0, total_rows, chunk_size):
                end_idx = min(start_idx + chunk_size, total_rows)
                chunk_df = df.iloc[start_idx:end_idx]
                
                chunk_trades, portfolio_value, current_position, peak_value, max_drawdown, chunk_equity_points = self._process_chunk(
                    chunk_df, strategy, portfolio_value, current_position, 
                    peak_value, max_drawdown, commission, slippage
                )
                trades.extend(chunk_trades)
                equity_points.extend(chunk_equity_points)
        else:
            # Process entire dataset at once
            trades, portfolio_value, current_position, peak_value, max_drawdown, equity_points = self._process_chunk(
                df, strategy, portfolio_value, current_position, 
                peak_value, max_drawdown, commission, slippage
            )
        
        # Calculate final performance metrics
        performance = self._calculate_performance_metrics(trades, initial_capital, portfolio_value, max_drawdown)
        
        return trades, performance, equity_points
    
    def _process_chunk(self, chunk_df: pd.DataFrame, strategy: Strategy, 
                      portfolio_value: float, current_position: Optional[Dict],
                      peak_value: float, max_drawdown: float, commission: Decimal,
                      slippage: Decimal) -> Tuple[List[Dict], float, Optional[Dict], float, float, List[Dict]]:
        """
        Process a chunk of data efficiently
        """
        trades = []
        equity_points = []  # Store equity curve points for this chunk
        
        # Convert to list for iteration (more efficient than iterrows)
        data_list = chunk_df.to_dict('records')
        
        for row in data_list:
            current_price = float(row['close'])
            current_date = row['date']
            
            # Check for entry signals
            if current_position is None:
                if self._check_entry_conditions(row, strategy.entry_rules):
                    # Enter position
                    entry_price = self._apply_slippage(current_price, slippage, 'buy')
                    qty = self._position_size(strategy, row, entry_price)
                    current_position = {
                        'action': 'buy',
                        'entry_price': entry_price,
                        'entry_date': current_date,
                        'quantity': qty
                    }
            
            # Check for exit signals
            elif current_position is not None:
                exit_reason = self._check_exit_conditions(
                    row, current_position, strategy.exit_rules,
                    strategy.stop_loss_type, strategy.stop_loss_value,
                    strategy.take_profit_type, strategy.take_profit_value
                )
                
                if exit_reason:
                    # Exit position
                    exit_price = self._apply_slippage(current_price, slippage, 'sell')
                    
                    # Calculate trade metrics
                    trade_duration = (current_date - current_position['entry_date']).total_seconds() * 1000
                    
                    # P&L monetario correcto para ES
                    side_sign = 1.0 if current_position['action'] == 'buy' else -1.0
                    raw_points = (exit_price - current_position['entry_price']) * side_sign  # en puntos de precio
                    pnl = raw_points * ES_POINT_VALUE * current_position['quantity']
                    
                    trade_commission = float(commission)  # si es por round-trip; si es por lado, multiplica por 2
                    trade_slippage = 0.0                  # ya "metido" en entry/exit
                    net_pnl = pnl - trade_commission - trade_slippage
                    
                    # Create trade record
                    trade_data = {
                        'action': current_position['action'],
                        'entry_price': current_position['entry_price'],
                        'exit_price': exit_price,
                        'entry_date': current_position['entry_date'],
                        'exit_date': current_date,
                        'quantity': current_position['quantity'],
                        'pnl': pnl,
                        'commission': trade_commission,
                        'slippage': trade_slippage,
                        'net_pnl': net_pnl,
                        'reason': exit_reason,
                        'duration': int(trade_duration)
                    }
                    trades.append(trade_data)
                    
                    # Update portfolio value
                    portfolio_value += net_pnl
                    
                    # Update drawdown tracking
                    if portfolio_value > peak_value:
                        peak_value = portfolio_value
                    else:
                        current_drawdown = (peak_value - portfolio_value) / peak_value
                        if current_drawdown > max_drawdown:
                            max_drawdown = current_drawdown
                    
                    # Reset position
                    current_position = None
            
            # Update cache for cross detection
            self._prev_row_cache = row
            
            # Create equity curve point for this timestamp (only every 100th point to reduce data)
            if len(equity_points) % 100 == 0 or len(equity_points) == 0:
                current_drawdown = (peak_value - portfolio_value) / peak_value if peak_value > 0 else 0
                equity_points.append({
                    'timestamp': current_date,
                    'equity_value': portfolio_value,
                    'drawdown': current_drawdown
                })
        
        return trades, portfolio_value, current_position, peak_value, max_drawdown, equity_points
    
    def _calculate_performance_metrics(self, trades: List[Dict], initial_capital: Decimal, 
                                     final_value: float, max_drawdown: float) -> Dict:
        """
        Calculate performance metrics efficiently
        """
        if not trades:
            return {
                'total_return': Decimal('0'),
                'total_return_percent': Decimal('0'),
                'total_trades': 0,
                'winning_trades': 0,
                'losing_trades': 0,
                'win_rate': Decimal('0'),
                'profit_factor': Decimal('0'),
                'avg_win': Decimal('0'),
                'avg_loss': Decimal('0'),
                'largest_win': Decimal('0'),
                'largest_loss': Decimal('0'),
                'max_drawdown': Decimal('0'),
                'max_drawdown_percent': Decimal('0'),
                'sharpe_ratio': None,
                'sortino_ratio': None,
                'calmar_ratio': None,
                'volatility': None,
                'recovery_factor': None,
                'max_consecutive_wins': 0,
                'max_consecutive_losses': 0,
                'avg_trade_duration': None,
                'trades_per_month': None,
                'expectancy': None,
                'rating': 'Poor',
                'rating_color': '#ff6b6b',
                'summary_description': 'No trades executed'
            }
        
        # Use the existing metrics calculator for consistency
        return calculate_all_metrics(trades, float(initial_capital), 
                                   trades[0]['entry_date'], trades[-1]['exit_date'])
    
    def _simulate_strategy(self, df: pd.DataFrame, strategy: Strategy,
                          initial_capital: Decimal, commission: Decimal,
                          slippage: Decimal) -> Tuple[List[Dict], Dict]:
        """
        Simulate strategy execution
        
        Args:
            df: Market data DataFrame
            strategy: Strategy to simulate
            initial_capital: Initial capital
            commission: Commission per trade
            slippage: Slippage percentage
        
        Returns:
            Tuple of (trades_list, performance_metrics)
        """
        trades = []
        portfolio_value = float(initial_capital)
        current_position = None
        peak_value = portfolio_value
        max_drawdown = 0
        
        # Convert DataFrame to list for iteration
        data_list = df.to_dict('records')
        
        for i, row in enumerate(data_list):
            current_price = float(row['close'])
            current_date = row['date']
            
            # Check for entry signals
            if current_position is None:
                if self._check_entry_conditions(row, strategy.entry_rules):
                    # Enter position
                    entry_price = self._apply_slippage(current_price, slippage, 'buy')
                    qty = self._position_size(strategy, row, entry_price)
                    current_position = {
                        'action': 'buy',
                        'entry_price': entry_price,
                        'entry_date': current_date,
                        'quantity': qty
                    }
            
            # Check for exit signals
            elif current_position is not None:
                exit_reason = self._check_exit_conditions(
                    row, current_position, strategy.exit_rules,
                    strategy.stop_loss_type, strategy.stop_loss_value,
                    strategy.take_profit_type, strategy.take_profit_value
                )
                
                if exit_reason:
                    # Exit position
                    exit_price = self._apply_slippage(current_price, slippage, 'sell')
                    
                    # Calculate trade P&L
                    trade_pnl = self._calculate_trade_pnl(
                        current_position, exit_price, commission
                    )
                    
                    # Create trade record
                    trade_data = {
                        'action': current_position['action'],
                        'entry_price': current_position['entry_price'],
                        'exit_price': exit_price,
                        'entry_date': current_position['entry_date'],
                        'exit_date': current_date,
                        'quantity': current_position['quantity'],
                        'pnl': trade_pnl['gross_pnl'],
                        'commission': float(commission),
                        'slippage': float(slippage),
                        'net_pnl': trade_pnl['net_pnl'],
                        'reason': exit_reason,
                        'duration': int((current_date - current_position['entry_date']).total_seconds() * 1000)
                    }
                    
                    trades.append(trade_data)
                    
                    # Update portfolio value
                    portfolio_value += float(trade_pnl['net_pnl'])
                    
                    # Update drawdown tracking
                    if portfolio_value > peak_value:
                        peak_value = portfolio_value
                    
                    current_drawdown = (peak_value - portfolio_value) / peak_value
                    if current_drawdown > max_drawdown:
                        max_drawdown = current_drawdown
                    
                    current_position = None
        
        # Calculate performance metrics using comprehensive calculator
        performance = self._calculate_performance_metrics(
            trades, initial_capital, df['date'].min(), df['date'].max()
        )
        
        return trades, performance
    
    def _check_entry_conditions(self, row: Dict, entry_rules: Union[List[Dict], Dict]) -> bool:
        """
        Check if entry conditions are met
        
        Args:
            row: Current market data row
            entry_rules: Entry rules configuration
        
        Returns:
            True if entry conditions are met
        """
        if not entry_rules:
            return False
        
        # Handle both list and dict formats
        rules = entry_rules if isinstance(entry_rules, list) else [entry_rules]
        
        # Process each entry rule
        for rule in rules:
            if rule.get('rule_type') == 'condition' and rule.get('action_type') == 'buy':
                conditions = rule.get('conditions', [])
                if self._evaluate_rule_conditions(row, conditions):
                    return True
        
        return False
    
    def _evaluate_rule_conditions(self, row: dict, conditions: list) -> bool:
        """Evaluate a list of conditions for a rule including cross detection"""
        if not conditions:
            return True

        result = None
        prev_row = getattr(self, "_prev_row_cache", None)  # guarda el último row procesado
        
        for cond in conditions:
            left  = self._get_operand_value(row,  cond.get('left_operand'))
            right = self._get_operand_value(row,  cond.get('right_operand'))
            prev_left = self._get_operand_value(prev_row, cond.get('left_operand'))  if prev_row else None
            prev_right= self._get_operand_value(prev_row, cond.get('right_operand')) if prev_row else None

            ok = self._evaluate_condition(left, cond.get('operator'), right, prev_left, prev_right)
            result = ok if result is None else ((result and ok) if (cond.get('logical_operator','and')=='and') else (result or ok))
        
        return bool(result)
    
    def _get_operand_value(self, row: dict, operand: str) -> float:
        """Get the value of an operand from market data using regex patterns"""
        if not operand:
            return float(row['close'])
        
        # Check if it's a numeric literal
        try:
            return float(operand)
        except (ValueError, TypeError):
            pass
        
        op = operand.lower()

        # precios
        if op in ('open','high','low','close','volume'):
            return float(row[op])

        # sma/ema parametrizados
        m = re.match(r'^(sma|ema)_(\d+)$', op)
        if m:
            col = f"{m.group(1)}_{m.group(2)}"
            return float(row.get(col, row['close']))

        # rsi parametrizado (por defecto 14)
        m = re.match(r'^rsi(?:_(\d+))?$', op)
        if m:
            col = f"rsi_{m.group(1) or 14}"
            return float(row.get(col, 50.0))

        # vwap y bandas
        if op == 'vwap':
            return float(row.get('vwap', row['close']))
        m = re.match(r'^vwap_(plus|minus)_(\d+_\d)$', op)
        if m:
            col = f"vwap_{m.group(1)}_{m.group(2)}"
            return float(row.get(col, row['close']))

        # bollinger (default 20 si no se especificó)
        m = re.match(r'^bb_(upper|middle|lower)(?:_(\d+))?$', op)
        if m:
            col = f"bb_{m.group(1)}_{m.group(2) or 20}"
            return float(row.get(col, row['close']))

        # macd / signal / hist
        if op in ('macd','macd_signal','macd_histogram','stochastic_k','stochastic_d'):
            return float(row.get(op, row['close']))

        # fallback
        return float(row['close'])
    
    def _evaluate_condition(self, left_value: float, operator: str, right_value: float,
                            prev_left: float = None, prev_right: float = None) -> bool:
        """Evaluate a single condition including cross_up/cross_down"""
        op = (operator or '').lower()
        if op in ('lt','<'):   return left_value <  right_value
        if op in ('le','lte','<='): return left_value <= right_value
        if op in ('gt','>'):   return left_value >  right_value
        if op in ('ge','gte','>='): return left_value >= right_value
        if op in ('eq','=='):  return left_value == right_value
        if op in ('ne','!='):  return left_value != right_value
        if op == 'cross_up' and prev_left is not None and prev_right is not None:
            return prev_left <= prev_right and left_value > right_value
        if op == 'cross_down' and prev_left is not None and prev_right is not None:
            return prev_left >= prev_right and left_value < right_value
        return False
    
    def _check_exit_conditions(self, row: Dict, position: Dict, exit_rules: Dict,
                              stop_loss_type: str, stop_loss_value: Decimal,
                              take_profit_type: str, take_profit_value: Decimal) -> Optional[str]:
        """
        Check if exit conditions are met - unified for ES
        
        Args:
            row: Current market data row
            position: Current position
            exit_rules: Exit rules configuration
            stop_loss_type: Stop loss type
            stop_loss_value: Stop loss value
            take_profit_type: Take profit type
            take_profit_value: Take profit value
        
        Returns:
            Exit reason if conditions are met, None otherwise
        """
        current_price = float(row['close'])
        entry_price = float(position['entry_price'])
        side_sign = 1.0 if position['action'] == 'buy' else -1.0

        # puntos recorridos desde la entrada (positivo si va a favor de la posición)
        moved_points = (current_price - entry_price) * side_sign

        # objetivos en puntos
        atr_val = float(row.get("atr") or 0.0)
        tp_points = self._points_from_spec(str(take_profit_type), float(take_profit_value or 0), entry_price, atr_val)
        sl_points = self._points_from_spec(str(stop_loss_type), float(stop_loss_value or 0), entry_price, atr_val)

        # take profit primero
        if tp_points > 0 and moved_points >= tp_points:
            return "Take Profit"

        # stop loss
        if sl_points > 0 and moved_points <= -sl_points:
            return "Stop Loss"

        # reglas de salida adicionales
        if exit_rules:
            rules = exit_rules if isinstance(exit_rules, list) else [exit_rules]
            for rule in rules:
                if rule.get('rule_type') == 'condition' and rule.get('action_type') == 'sell':
                    if self._evaluate_rule_conditions(row, rule.get('conditions', [])):
                        return f"Exit Rule: {rule.get('name', 'Unknown')}"

        return None
    
    def _apply_slippage(self, price: float, slippage: Decimal, action: str) -> float:
        """
        Apply slippage to price
        
        Args:
            price: Original price
            slippage: Slippage percentage
            action: Buy or sell action
        
        Returns:
            Price with slippage applied
        """
        slippage_factor = float(slippage) / 100
        
        if action == 'buy':
            return price * (1 + slippage_factor)
        else:
            return price * (1 - slippage_factor)
    
    def _calculate_trade_pnl(self, position: Dict, exit_price: float, commission: Decimal) -> Dict:
        """
        Calculate trade P&L
        
        Args:
            position: Position details
            exit_price: Exit price
            commission: Commission per trade
        
        Returns:
            Dictionary with gross and net P&L
        """
        entry_price = float(position['entry_price'])
        quantity = position['quantity']
        
        if position['action'] == 'buy':
            gross_pnl = (exit_price - entry_price) * quantity
        else:
            gross_pnl = (entry_price - exit_price) * quantity
        
        net_pnl = gross_pnl - float(commission)
        
        return {
            'gross_pnl': gross_pnl,
            'net_pnl': net_pnl
        }
    
    def _safe_decimal(self, value):
        """Safely convert value to Decimal, handling inf and None values"""
        if value is None:
            return None
        if isinstance(value, (int, float)):
            if value == float('inf') or value == float('-inf'):
                return Decimal('0')  # Convert inf to 0 for database storage
            if np.isnan(value):
                return Decimal('0')  # Convert NaN to 0
            # Limit values to prevent database overflow (max 999999.9999)
            if abs(value) > 999999:
                value = 999999 if value > 0 else -999999
        try:
            decimal_value = Decimal(str(value))
            # Additional check for decimal precision
            if decimal_value > Decimal('999999.9999'):
                return Decimal('999999.9999')
            elif decimal_value < Decimal('-999999.9999'):
                return Decimal('-999999.9999')
            return decimal_value
        except (ValueError, TypeError, OverflowError):
            return Decimal('0')

    def _calculate_performance_metrics(self, trades: List[Dict], initial_capital: Decimal,
                                     start_date: datetime, end_date: datetime) -> Dict:
        """
        Calculate comprehensive performance metrics using the new metrics calculator
        
        Args:
            trades: List of trade data
            initial_capital: Initial capital
            start_date: Backtest start date
            end_date: Backtest end date
        
        Returns:
            Dictionary with all performance metrics
        """
        if not trades:
            return self._get_empty_performance_metrics()
        
        # Use the comprehensive metrics calculator
        metrics = calculate_all_metrics(
            trades_data=trades,
            initial_capital=float(initial_capital),
            start_date=start_date,
            end_date=end_date
        )
        
        # Calculate rating and summary
        rating = calculate_strategy_rating(metrics)
        rating_color = get_rating_color(rating)
        summary = self._generate_summary_description(metrics, rating)
        
        # Convert to Decimal for database storage using safe conversion
        return {
            'total_return': self._safe_decimal(metrics['total_return']),
            'total_return_percent': self._safe_decimal(metrics['total_return_percent']),
            'total_trades': metrics['total_trades'],
            'winning_trades': metrics['winning_trades'],
            'losing_trades': metrics['losing_trades'],
            'win_rate': self._safe_decimal(metrics['win_rate']),
            'profit_factor': self._safe_decimal(metrics['profit_factor']),
            'avg_win': self._safe_decimal(metrics['avg_win']),
            'avg_loss': self._safe_decimal(metrics['avg_loss']),
            'largest_win': self._safe_decimal(metrics['largest_win']),
            'largest_loss': self._safe_decimal(metrics['largest_loss']),
            'sharpe_ratio': self._safe_decimal(metrics['sharpe_ratio']),
            'sortino_ratio': self._safe_decimal(metrics['sortino_ratio']),
            'calmar_ratio': self._safe_decimal(metrics['calmar_ratio']),
            'volatility': self._safe_decimal(metrics['volatility']),
            'max_drawdown': self._safe_decimal(metrics['max_drawdown']),
            'max_drawdown_percent': self._safe_decimal(metrics['max_drawdown_percent']),
            'recovery_factor': self._safe_decimal(metrics['recovery_factor']),
            'max_consecutive_wins': metrics['max_consecutive_wins'],
            'max_consecutive_losses': metrics['max_consecutive_losses'],
            'avg_trade_duration': self._safe_decimal(metrics['avg_trade_duration']),
            'trades_per_month': self._safe_decimal(metrics['trades_per_month']),
            'expectancy': self._safe_decimal(metrics['expectancy']),
            'rating': rating,
            'rating_color': rating_color,
            'summary_description': summary
        }
    
    def _generate_summary_description(self, metrics: Dict, rating: str) -> str:
        """Generate a summary description based on metrics and rating"""
        descriptions = {
            'Excellent': f"Outstanding performance with {metrics['total_return_percent']:.1f}% return and {metrics['win_rate']:.1f}% win rate",
            'Very Good': f"Strong performance with {metrics['total_return_percent']:.1f}% return and good risk management",
            'Good': f"Solid performance with {metrics['total_return_percent']:.1f}% return and {metrics['win_rate']:.1f}% win rate",
            'Fair': f"Moderate performance with {metrics['total_return_percent']:.1f}% return, needs optimization",
            'Poor': f"Poor performance with {metrics['total_return_percent']:.1f}% return and significant risk"
        }
        return descriptions.get(rating, "Performance analysis completed")
    
    def _calculate_rating(self, total_return_percent: float, win_rate: float,
                         profit_factor: float, max_drawdown: float) -> Tuple[str, str, str]:
        """
        Calculate strategy rating
        
        Args:
            total_return_percent: Total return percentage
            win_rate: Win rate percentage
            profit_factor: Profit factor
            max_drawdown: Maximum drawdown
        
        Returns:
            Tuple of (rating, color, description)
        """
        score = 0
        
        # Return score
        if total_return_percent > 20:
            score += 3
        elif total_return_percent > 10:
            score += 2
        elif total_return_percent > 0:
            score += 1
        
        # Win rate score
        if win_rate > 70:
            score += 2
        elif win_rate > 60:
            score += 1
        
        # Profit factor score
        if profit_factor > 2:
            score += 2
        elif profit_factor > 1.5:
            score += 1
        
        # Drawdown penalty
        if max_drawdown > 0.2:
            score -= 2
        elif max_drawdown > 0.1:
            score -= 1
        
        # Determine rating
        if score >= 6:
            return "Excellent", "#2ecc71", "Outstanding performance with excellent risk management"
        elif score >= 4:
            return "Very Good", "#4ecdc4", "Strong performance with good risk management"
        elif score >= 2:
            return "Good", "#45b7d1", "Positive performance with acceptable risk"
        elif score >= 0:
            return "Fair", "#f39c12", "Moderate performance with some concerns"
        else:
            return "Poor", "#e74c3c", "Poor performance with significant risk"
    
    def _get_empty_performance_metrics(self) -> Dict:
        """Get empty performance metrics for strategies with no trades"""
        return {
            'total_return': Decimal('0'),
            'total_return_percent': Decimal('0'),
            'total_trades': 0,
            'winning_trades': 0,
            'losing_trades': 0,
            'win_rate': Decimal('0'),
            'profit_factor': Decimal('0'),
            'avg_win': Decimal('0'),
            'avg_loss': Decimal('0'),
            'largest_win': Decimal('0'),
            'largest_loss': Decimal('0'),
            'sharpe_ratio': None,
            'sortino_ratio': None,
            'calmar_ratio': None,
            'volatility': None,
            'max_drawdown': Decimal('0'),
            'max_drawdown_percent': Decimal('0'),
            'recovery_factor': None,
            'max_consecutive_wins': 0,
            'max_consecutive_losses': 0,
            'avg_trade_duration': None,
            'trades_per_month': None,
            'expectancy': None,
            'rating': 'Poor',
            'rating_color': '#e74c3c',
            'summary_description': 'No trades executed during backtest period'
        }
    
    def _needed_operands(self, strategy) -> set:
        """Extract all operands needed from strategy rules"""
        ops = set()
        for rules in (getattr(strategy, "entry_rules", []), getattr(strategy, "exit_rules", [])):
            if not rules: 
                continue
            rules_list = rules if isinstance(rules, list) else [rules]
            for r in rules_list:
                for c in r.get("conditions", []):
                    for side in ("left_operand","right_operand"):
                        op = str(c.get(side) or "").strip()
                        if op: ops.add(op)
        return ops

    def _validate_operands(self, strategy):
        """Validate that all operands are supported"""
        bad = []
        for op in self._needed_operands(strategy):
            # Check if it's a numeric value (literal number)
            try:
                float(op)
                continue  # Skip validation for numeric literals
            except (ValueError, TypeError):
                pass
            
            # Check if it's a supported indicator pattern
            ok = any(re.match(pat, op) for pat in INDICATOR_PATTERNS.keys())
            if not ok:
                bad.append(op)
        if bad:
            raise ValueError(f"Operando(s) no soportado(s): {bad}. Ajusta la estrategia o amplía el motor.")
    
    def _ensure_indicators(self, df: pd.DataFrame, strategy) -> pd.DataFrame:
        """Calculate only the indicators needed by the strategy rules"""
        df = df.copy()
        needed = self._needed_operands(strategy)

        # helpers base
        close = df["close"].astype(float)
        high  = df["high"].astype(float)  if "high"   in df else None
        low   = df["low"].astype(float)   if "low"    in df else None
        vol   = df["volume"].astype(float)if "volume" in df else None

        def parse(op):
            for pat, key in INDICATOR_PATTERNS.items():
                m = re.match(pat, op)
                if m: return key, m.groups()
            return None, None

        # flags para saber qué calcular
        need_sma, need_ema, sma_ps, ema_ps = False, False, set(), set()
        need_rsi, rsi_ps = False, set()
        need_vwap, need_vwap_bands, vwap_sigmas = False, False, set()
        need_bb, bb_ps = False, set()
        need_macd, need_stoch = False, False

        for op in needed:
            key, groups = parse(op)
            if key == 'sma':
                need_sma = True; sma_ps.add(int(groups[0]))
            elif key == 'ema':
                need_ema = True; ema_ps.add(int(groups[0]))
            elif key == 'rsi':
                need_rsi = True; rsi_ps.add(int(groups[0] or 14))
            elif key == 'vwap':
                need_vwap = True
            elif key == 'vwap_band':
                need_vwap = True; need_vwap_bands = True
                sign, sigma = groups[0], float(groups[1].replace('_','.'))
                vwap_sigmas.add((sign, sigma))
            elif key == 'bb':
                need_bb = True; bb_ps.add(int(groups[1] or 20))
            elif key in ('macd','macd_signal','macd_histogram'):
                need_macd = True
            elif key in ('stoch_k','stoch_d'):
                need_stoch = True
            elif key == 'price':
                pass  # ohlcv ya está
            else:
                # Operando desconocido -> lo dejamos y se resolverá a 'close' en _get_operand_value
                pass

        # --- Cálculos ---
        # SMA/EMA
        if need_sma:
            for p in sorted(sma_ps):
                df[f"sma_{p}"] = close.rolling(p, min_periods=p).mean()
        if need_ema:
            for p in sorted(ema_ps):
                df[f"ema_{p}"] = close.ewm(span=p, adjust=False).mean()

        # RSI (Wilder)
        if need_rsi:
            delta = close.diff()
            up = delta.clip(lower=0); down = -delta.clip(upper=0)
            for p in sorted(rsi_ps):
                roll_up = up.ewm(alpha=1/p, adjust=False).mean()
                roll_dn = down.ewm(alpha=1/p, adjust=False).mean()
                rs = roll_up / (roll_dn.replace(0, 1e-12))
                df[f"rsi_{p}"] = 100 - (100/(1+rs))

        # VWAP (rolling diario simple; si no hay sesiones, usa rolling 390 barras para intradía)
        if need_vwap:
            if vol is None or high is None or low is None:
                raise ValueError("VWAP requiere high/low/close/volume.")
            tp = (high + low + close) / 3.0
            # rolling intradía aproximado: 390 barras para 1m; ajusta por timeframe si quieres
            window = 390 if len(df) > 500 else min(100, max(1, len(df)//5))
            cum_pv = (tp * vol).rolling(window, min_periods=window//5).sum()
            cum_v  = vol.rolling(window, min_periods=window//5).sum()
            df["vwap"] = cum_pv / (cum_v.replace(0, 1e-12))
            if need_vwap_bands:
                # σ rolling sobre TP (alternativa: sobre close)
                std = tp.rolling(window, min_periods=window//5).std()
                for sign, s in vwap_sigmas:
                    band = df["vwap"] + (std * s if sign == "plus" else -std * s)
                    df[f"vwap_{sign}_{str(s).replace('.','_')}"] = band

        # Bollinger Bands (sobre close)
        if need_bb:
            for p in sorted(bb_ps):
                ma = close.rolling(p, min_periods=p).mean()
                sd = close.rolling(p, min_periods=p).std()
                df[f"bb_middle_{p}"] = ma
                df[f"bb_upper_{p}"]  = ma + 2*sd
                df[f"bb_lower_{p}"]  = ma - 2*sd

        # MACD (12,26,9)
        if need_macd:
            ema12 = close.ewm(span=12, adjust=False).mean()
            ema26 = close.ewm(span=26, adjust=False).mean()
            macd = ema12 - ema26
            signal = macd.ewm(span=9, adjust=False).mean()
            df["macd"] = macd
            df["macd_signal"] = signal
            df["macd_histogram"] = macd - signal

        # Stochastic (14,3)
        if need_stoch:
            low14  = low.rolling(14, min_periods=14).min()
            high14 = high.rolling(14, min_periods=14).max()
            k = 100 * (close - low14) / ((high14 - low14).replace(0, 1e-12))
            df["stochastic_k"] = k
            df["stochastic_d"] = k.rolling(3, min_periods=3).mean()

        # Limpieza mínima: no elimines demasiado, o matarás señales iniciales
        return df
    
    def _points_from_spec(self, kind: str, value: float, entry_price: float, atr: float | None) -> float:
        """
        Devuelve la distancia en **puntos** de ES (no ticks, no %), desde un valor y su tipo.
        kind: 'percentage' | 'points' | 'ticks' | 'atr'
        value: magnitud definida por el usuario
        entry_price: precio de entrada
        atr: atr actual (si aplica)
        """
        k = (kind or "").lower()
        if k == "percentage":
            return (entry_price * (value / 100.0))
        if k == "points":
            return value
        if k == "ticks":
            return value * ES_TICK
        if k == "atr":
            return (atr or 0.0) * value
        return 0.0
    
    def _position_size(self, strategy, row, entry_price):
        """Calculate position size based on fixed risk percentage"""
        risk_pct = 0.01  # 1% risk per trade
        stop_type = getattr(strategy, "stop_loss_type", "percentage")
        stop_val = float(getattr(strategy, "stop_loss_value", 0) or 0)
        if stop_val <= 0:
            return 1

        atr_val = float(row.get("atr") or 0.0)
        sl_points = self._points_from_spec(stop_type, stop_val, entry_price, atr_val)
        if sl_points <= 0:
            return 1

        per_contract_risk = sl_points * ES_POINT_VALUE
        budget = float(strategy.initial_capital) * risk_pct
        qty = max(1, int(budget // per_contract_risk))
        return qty

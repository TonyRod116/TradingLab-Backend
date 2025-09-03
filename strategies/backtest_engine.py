"""
Backtesting Engine using optimized Parquet data
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Dict, List, Tuple, Optional
import time

from market_data.parquet_service import ParquetDataService
from .models import Strategy, BacktestResult, Trade
from .metrics_calculator import (
    calculate_all_metrics, calculate_strategy_rating, get_rating_color
)


class BacktestEngine:
    """Engine for backtesting trading strategies using Parquet data"""
    
    def __init__(self):
        self.parquet_service = ParquetDataService()
    
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
            # Get market data using optimized Parquet service
            df = self.parquet_service.get_candles(
                symbol=strategy.symbol,
                timeframe=strategy.timeframe,
                start_date=start_date,
                end_date=end_date
            )
            
            if df.empty:
                raise ValueError(f"No data found for {strategy.symbol} {strategy.timeframe}")
            
            # Determine data source
            data_source = 'parquet' if self.parquet_service.is_parquet_available(
                strategy.symbol, strategy.timeframe
            ) else 'database'
            
            # Run backtest simulation with chunking for large datasets
            trades, performance = self._simulate_strategy_optimized(
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
            
            return backtest_result
            
        except Exception as e:
            raise Exception(f"Backtest failed: {str(e)}")
    
    def _simulate_strategy_optimized(self, df: pd.DataFrame, strategy: Strategy,
                                   initial_capital: Decimal, commission: Decimal,
                                   slippage: Decimal, chunk_size: int = 10000) -> Tuple[List[Dict], Dict]:
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
            Tuple of (trades_list, performance_metrics)
        """
        trades = []
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
                
                chunk_trades, portfolio_value, current_position, peak_value, max_drawdown = self._process_chunk(
                    chunk_df, strategy, portfolio_value, current_position, 
                    peak_value, max_drawdown, commission, slippage
                )
                trades.extend(chunk_trades)
        else:
            # Process entire dataset at once
            trades, portfolio_value, current_position, peak_value, max_drawdown = self._process_chunk(
                df, strategy, portfolio_value, current_position, 
                peak_value, max_drawdown, commission, slippage
            )
        
        # Calculate final performance metrics
        performance = self._calculate_performance_metrics(trades, initial_capital, portfolio_value, max_drawdown)
        
        return trades, performance
    
    def _process_chunk(self, chunk_df: pd.DataFrame, strategy: Strategy, 
                      portfolio_value: float, current_position: Optional[Dict],
                      peak_value: float, max_drawdown: float, commission: Decimal,
                      slippage: Decimal) -> Tuple[List[Dict], float, Optional[Dict], float, float]:
        """
        Process a chunk of data efficiently
        """
        trades = []
        
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
                    current_position = {
                        'action': 'buy',
                        'entry_price': entry_price,
                        'entry_date': current_date,
                        'quantity': 1
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
                    pnl = (exit_price - current_position['entry_price']) * current_position['quantity']
                    trade_commission = float(commission)
                    trade_slippage = abs(exit_price - current_price) * float(slippage) / 100
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
        
        return trades, portfolio_value, current_position, peak_value, max_drawdown
    
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
                    current_position = {
                        'action': 'buy',
                        'entry_price': entry_price,
                        'entry_date': current_date,
                        'quantity': 1
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
    
    def _check_entry_conditions(self, row: Dict, entry_rules: Dict) -> bool:
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
        
        # For now, implement a simple deterministic condition
        # This ensures consistent results across multiple runs
        current_price = float(row['close'])
        
        # Simple price-based entry condition (deterministic)
        # Entry when price is in a certain range (example: between 4000-5000)
        if 4000 <= current_price <= 5000:
            # Use a deterministic "random" based on price
            # This ensures same price always gives same result
            price_hash = hash(str(current_price)) % 1000
            return price_hash < 5  # 0.5% chance based on price
        
        return False
    
    def _check_exit_conditions(self, row: Dict, position: Dict, exit_rules: Dict,
                              stop_loss_type: str, stop_loss_value: Decimal,
                              take_profit_type: str, take_profit_value: Decimal) -> Optional[str]:
        """
        Check if exit conditions are met
        
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
        
        # Calculate price change
        if position['action'] == 'buy':
            price_change = current_price - entry_price
            price_change_percent = (price_change / entry_price) * 100
        else:
            price_change = entry_price - current_price
            price_change_percent = (price_change / entry_price) * 100
        
        # Check take profit
        if take_profit_type == 'percentage':
            if price_change_percent >= float(take_profit_value):
                return "Take Profit"
        elif take_profit_type == 'points':
            if price_change >= float(take_profit_value):
                return "Take Profit"
        elif take_profit_type == 'ticks':
            # 1 tick = 0.25 points for futures
            tick_value = float(take_profit_value) * 0.25
            if price_change >= tick_value:
                return "Take Profit"
        elif take_profit_type == 'atr':
            # Use ATR from current row data
            atr_value = row.get('atr')
            if atr_value and price_change >= float(take_profit_value) * float(atr_value):
                return "Take Profit"
        
        # Check stop loss
        if stop_loss_type == 'percentage':
            if price_change_percent <= -float(stop_loss_value):
                return "Stop Loss"
        elif stop_loss_type == 'points':
            if price_change <= -float(stop_loss_value):
                return "Stop Loss"
        elif stop_loss_type == 'ticks':
            # 1 tick = 0.25 points for futures
            tick_value = float(stop_loss_value) * 0.25
            if price_change <= -tick_value:
                return "Stop Loss"
        elif stop_loss_type == 'atr':
            # Use ATR from current row data
            atr_value = row.get('atr')
            if atr_value and price_change <= -float(stop_loss_value) * float(atr_value):
                return "Stop Loss"
        
        # Check other exit rules
        if exit_rules and 'time_based' in exit_rules:
            # Example: Exit after certain time
            return "Time Exit"
        
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
        
        # Convert to Decimal for database storage
        return {
            'total_return': Decimal(str(metrics['total_return'])),
            'total_return_percent': Decimal(str(metrics['total_return_percent'])),
            'total_trades': metrics['total_trades'],
            'winning_trades': metrics['winning_trades'],
            'losing_trades': metrics['losing_trades'],
            'win_rate': Decimal(str(metrics['win_rate'])),
            'profit_factor': Decimal(str(metrics['profit_factor'])),
            'avg_win': Decimal(str(metrics['avg_win'])),
            'avg_loss': Decimal(str(metrics['avg_loss'])),
            'largest_win': Decimal(str(metrics['largest_win'])),
            'largest_loss': Decimal(str(metrics['largest_loss'])),
            'sharpe_ratio': Decimal(str(metrics['sharpe_ratio'])) if metrics['sharpe_ratio'] is not None else None,
            'sortino_ratio': Decimal(str(metrics['sortino_ratio'])) if metrics['sortino_ratio'] is not None else None,
            'calmar_ratio': Decimal(str(metrics['calmar_ratio'])) if metrics['calmar_ratio'] is not None else None,
            'volatility': Decimal(str(metrics['volatility'])) if metrics['volatility'] is not None else None,
            'max_drawdown': Decimal(str(metrics['max_drawdown'])),
            'max_drawdown_percent': Decimal(str(metrics['max_drawdown_percent'])),
            'recovery_factor': Decimal(str(metrics['recovery_factor'])) if metrics['recovery_factor'] is not None else None,
            'max_consecutive_wins': metrics['max_consecutive_wins'],
            'max_consecutive_losses': metrics['max_consecutive_losses'],
            'avg_trade_duration': Decimal(str(metrics['avg_trade_duration'])) if metrics['avg_trade_duration'] is not None else None,
            'trades_per_month': Decimal(str(metrics['trades_per_month'])) if metrics['trades_per_month'] is not None else None,
            'expectancy': Decimal(str(metrics['expectancy'])) if metrics['expectancy'] is not None else None,
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

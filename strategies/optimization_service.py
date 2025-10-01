"""
Advanced Optimization Service - Integrated from engine_v2.py
"""

import itertools
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass

from .backtest_engine import BacktestEngine
from .models import Strategy
from .advanced_indicators import compute_advanced_indicator, get_available_indicators


@dataclass
class OptimizationResult:
    """Result of optimization process"""
    best_params: Dict[str, Any]
    best_sharpe: float
    all_results: List[Dict[str, Any]]
    optimization_time: float


@dataclass
class WalkForwardResult:
    """Result of walk-forward optimization"""
    train_results: List[Dict[str, Any]]
    test_results: List[Dict[str, Any]]
    best_params: Dict[str, Any]
    oos_performance: Dict[str, Any]
    oos_equity_curve: List[Dict[str, Any]]
    oos_trades: List[Dict[str, Any]]


class OptimizationService:
    """Advanced optimization service integrated from engine_v2.py"""
    
    def __init__(self):
        self.backtest_engine = BacktestEngine()
    
    def grid_search_optimization(self, strategy: Strategy, param_ranges: Dict[str, List], 
                                start_date: datetime, end_date: datetime,
                                initial_capital: float = 100000.0) -> OptimizationResult:
        """
        Perform grid search optimization
        
        Args:
            strategy: Strategy to optimize
            param_ranges: Dictionary of parameter ranges to test
            start_date: Optimization start date
            end_date: Optimization end date
            initial_capital: Initial capital for backtesting
        
        Returns:
            OptimizationResult with best parameters and results
        """
        import time
        start_time = time.time()
        
        best_params = None
        best_sharpe = -float('inf')
        results = []
        
        # Generate all parameter combinations
        param_names = list(param_ranges.keys())
        param_values = list(param_ranges.values())
        
        for param_combo in itertools.product(*param_values):
            params = dict(zip(param_names, param_combo))
            
            try:
                # Create strategy with these parameters
                optimized_strategy = self._create_strategy_with_params(strategy, params)
                
                # Run backtest
                backtest_result = self.backtest_engine.run_backtest(
                    optimized_strategy, start_date, end_date, 
                    initial_capital=initial_capital
                )
                
                # Extract metrics
                sharpe = float(backtest_result.sharpe_ratio or 0)
                total_return = float(backtest_result.total_return or 0)
                max_drawdown = float(backtest_result.max_drawdown or 0)
                win_rate = float(backtest_result.win_rate or 0)
                profit_factor = float(backtest_result.profit_factor or 0)
                
                result = {
                    "params": params,
                    "sharpe": sharpe,
                    "total_return": total_return,
                    "max_drawdown": max_drawdown,
                    "win_rate": win_rate,
                    "profit_factor": profit_factor,
                    "trades": backtest_result.total_trades
                }
                
                results.append(result)
                
                # Update best parameters
                if sharpe > best_sharpe:
                    best_sharpe = sharpe
                    best_params = params
                    
            except Exception as e:
                # Skip invalid parameter combinations
                continue
        
        optimization_time = time.time() - start_time
        
        return OptimizationResult(
            best_params=best_params or {},
            best_sharpe=best_sharpe,
            all_results=results[:50],  # Limit to 50 results
            optimization_time=optimization_time
        )
    
    def walk_forward_optimization(self, strategy: Strategy, param_ranges: Dict[str, List],
                                 train_months: int = 6, test_months: int = 1, 
                                 step_months: int = 1, start_date: datetime = None,
                                 end_date: datetime = None) -> WalkForwardResult:
        """
        Perform walk-forward optimization
        
        Args:
            strategy: Strategy to optimize
            param_ranges: Dictionary of parameter ranges to test
            train_months: Training period in months
            test_months: Testing period in months
            step_months: Step size in months
            start_date: Start date (uses strategy's default if None)
            end_date: End date (uses strategy's default if None)
        
        Returns:
            WalkForwardResult with walk-forward analysis
        """
        # Get market data to determine date range
        df = self.backtest_engine.parquet_service.get_candles(
            symbol=strategy.symbol,
            timeframe=strategy.timeframe,
            start_date=start_date or datetime(2020, 1, 1),
            end_date=end_date or datetime.now()
        )
        
        if df.empty:
            raise ValueError(f"No data found for {strategy.symbol} {strategy.timeframe}")
        
        start_date = df.index[0]
        end_date = df.index[-1]
        
        train_results = []
        test_results = []
        best_params_history = []
        
        current_date = start_date
        while current_date < end_date:
            train_end = current_date + pd.DateOffset(months=train_months)
            test_start = train_end
            test_end = test_start + pd.DateOffset(months=test_months)
            
            if test_end > end_date:
                break
            
            # Check minimum data requirements
            train_df = df[(df.index >= current_date) & (df.index < train_end)]
            test_df = df[(df.index >= test_start) & (df.index < test_end)]
            
            if len(train_df) < 100 or len(test_df) < 20:
                current_date += pd.DateOffset(months=step_months)
                continue
            
            # Optimize on training data
            best_params = None
            best_sharpe = -float('inf')
            
            param_names = list(param_ranges.keys())
            param_values = list(param_ranges.values())
            
            for param_combo in itertools.product(*param_values):
                params = dict(zip(param_names, param_combo))
                
                try:
                    optimized_strategy = self._create_strategy_with_params(strategy, params)
                    
                    # Run backtest on training data
                    train_result = self.backtest_engine.run_backtest(
                        optimized_strategy, current_date, train_end
                    )
                    
                    sharpe = float(train_result.sharpe_ratio or 0)
                    if sharpe > best_sharpe:
                        best_sharpe = sharpe
                        best_params = params
                        
                except Exception:
                    continue
            
            if best_params:
                best_params_history.append(best_params)
                
                # Test on out-of-sample data
                optimized_strategy = self._create_strategy_with_params(strategy, best_params)
                test_result = self.backtest_engine.run_backtest(
                    optimized_strategy, test_start, test_end
                )
                
                train_results.append({
                    "period": f"{current_date.strftime('%Y-%m')} to {train_end.strftime('%Y-%m')}",
                    "best_params": best_params,
                    "best_sharpe": best_sharpe
                })
                
                test_results.append({
                    "period": f"{test_start.strftime('%Y-%m')} to {test_end.strftime('%Y-%m')}",
                    "metrics": {
                        "Total Return": float(test_result.total_return or 0),
                        "Sharpe Ratio": float(test_result.sharpe_ratio or 0),
                        "Max Drawdown": float(test_result.max_drawdown or 0),
                        "Win Rate": float(test_result.win_rate or 0),
                        "Profit Factor": float(test_result.profit_factor or 0)
                    },
                    "trades": test_result.total_trades
                })
            
            current_date += pd.DateOffset(months=step_months)
        
        # Calculate out-of-sample performance
        oos_performance = self._calculate_oos_performance(test_results)
        
        return WalkForwardResult(
            train_results=train_results,
            test_results=test_results,
            best_params=best_params_history[-1] if best_params_history else {},
            oos_performance=oos_performance,
            oos_equity_curve=[],  # Would need to be calculated from individual results
            oos_trades=[]  # Would need to be calculated from individual results
        )
    
    def _create_strategy_with_params(self, strategy: Strategy, params: Dict[str, Any]) -> Strategy:
        """
        Create a strategy with modified parameters
        
        Args:
            strategy: Original strategy
            params: Parameters to modify
        
        Returns:
            New strategy with modified parameters
        """
        # Create a copy of the strategy
        new_strategy = Strategy(
            name=f"{strategy.name}_optimized",
            symbol=strategy.symbol,
            timeframe=strategy.timeframe,
            entry_rules=strategy.entry_rules,
            exit_rules=strategy.exit_rules,
            stop_loss_type=strategy.stop_loss_type,
            stop_loss_value=strategy.stop_loss_value,
            take_profit_type=strategy.take_profit_type,
            take_profit_value=strategy.take_profit_value,
            initial_capital=strategy.initial_capital
        )
        
        # Replace parameters in rules
        if new_strategy.entry_rules:
            self._replace_params_in_rules(new_strategy.entry_rules, params)
        
        if new_strategy.exit_rules:
            self._replace_params_in_rules(new_strategy.exit_rules, params)
        
        return new_strategy
    
    def _replace_params_in_rules(self, rules: List[Dict], params: Dict[str, Any]):
        """
        Replace parameters in strategy rules recursively
        
        Args:
            rules: List of rules to modify
            params: Parameters to replace
        """
        for rule in rules:
            if isinstance(rule, dict):
                if "conditions" in rule:
                    for condition in rule["conditions"]:
                        if "left_operand" in condition:
                            self._replace_params_in_operand(condition["left_operand"], params)
                        if "right_operand" in condition:
                            self._replace_params_in_operand(condition["right_operand"], params)
    
    def _replace_params_in_operand(self, operand: str, params: Dict[str, Any]):
        """
        Replace parameters in operand string
        
        Args:
            operand: Operand string to modify
            params: Parameters to replace
        """
        # This is a simplified version - in practice, you'd need more sophisticated
        # parameter replacement logic based on your operand format
        for param_name, param_value in params.items():
            if param_name in operand:
                operand = operand.replace(param_name, str(param_value))
    
    def _calculate_oos_performance(self, test_results: List[Dict]) -> Dict[str, Any]:
        """
        Calculate out-of-sample performance metrics
        
        Args:
            test_results: List of test period results
        
        Returns:
            Dictionary with OOS performance metrics
        """
        if not test_results:
            return {}
        
        all_returns = []
        all_sharpes = []
        all_drawdowns = []
        all_trades = []
        
        for result in test_results:
            metrics = result.get("metrics", {})
            all_returns.append(metrics.get("Total Return", 0))
            all_sharpes.append(metrics.get("Sharpe Ratio", 0))
            all_drawdowns.append(metrics.get("Max Drawdown", 0))
            all_trades.append(result.get("trades", 0))
        
        return {
            "Average Return": np.mean(all_returns),
            "Total Return": np.sum(all_returns),
            "Sharpe Ratio": np.mean(all_sharpes),
            "Max Drawdown": np.mean(all_drawdowns),
            "Total Trades": sum(all_trades),
            "Consistency": len([r for r in all_returns if r > 0]) / len(all_returns) if all_returns else 0,
            "Best Period": max(all_returns) if all_returns else 0,
            "Worst Period": min(all_returns) if all_returns else 0
        }
    
    def get_available_indicators(self) -> Dict[str, Dict[str, Any]]:
        """Get list of all available indicators"""
        return get_available_indicators()
    
    def validate_strategy_parameters(self, strategy: Strategy, param_ranges: Dict[str, List]) -> bool:
        """
        Validate that strategy parameters are compatible with optimization ranges
        
        Args:
            strategy: Strategy to validate
            param_ranges: Parameter ranges to validate against
        
        Returns:
            True if validation passes
        """
        # This would contain validation logic to ensure parameter ranges
        # are compatible with the strategy's operand format
        return True

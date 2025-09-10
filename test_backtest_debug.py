#!/usr/bin/env python
"""
Script to test backtest engine and debug why no trades are generated
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from strategies.models import Strategy
from strategies.backtest_engine import BacktestEngine

def test_backtest_engine():
    """Test the backtest engine with a simple strategy"""
    
    # Create a test strategy
    strategy_data = {
        'name': 'Test Strategy Debug',
        'description': 'Test strategy for debugging',
        'symbol': 'ES',
        'timeframe': '1m',
        'initial_capital': 100000,
        'entry_rules': {'rsi_oversold': 30},  # Simple RSI rule
        'exit_rules': {'time_based': True},   # Time-based exit
        'stop_loss_type': 'percentage',
        'stop_loss_value': 2.0,
        'take_profit_type': 'percentage',
        'take_profit_value': 4.0
    }
    
    # Create strategy object (without saving to DB)
    strategy = Strategy(
        name=strategy_data['name'],
        description=strategy_data['description'],
        symbol=strategy_data['symbol'],
        timeframe=strategy_data['timeframe'],
        initial_capital=strategy_data['initial_capital'],
        entry_rules=strategy_data['entry_rules'],
        exit_rules=strategy_data['exit_rules'],
        stop_loss_type=strategy_data['stop_loss_type'],
        stop_loss_value=strategy_data['stop_loss_value'],
        take_profit_type=strategy_data['take_profit_type'],
        take_profit_value=strategy_data['take_profit_value']
    )
    
    print(f"🔍 [TEST] Strategy created: {strategy.name}")
    print(f"🔍 [TEST] Entry rules: {strategy.entry_rules}")
    print(f"🔍 [TEST] Exit rules: {strategy.exit_rules}")
    
    # Test backtest engine
    engine = BacktestEngine()
    
    try:
        # Run backtest
        start_date = datetime(2020, 1, 1)
        end_date = datetime(2020, 1, 31)  # Just one month for testing
        
        print(f"🔍 [TEST] Running backtest from {start_date} to {end_date}")
        
        result = engine.run_backtest(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            initial_capital=Decimal('100000'),
            commission=Decimal('4.00'),
            slippage=Decimal('0.5')
        )
        
        print(f"🔍 [TEST] Backtest completed!")
        print(f"🔍 [TEST] Total trades: {result.total_trades}")
        print(f"🔍 [TEST] Total return: {result.total_return}")
        print(f"🔍 [TEST] Win rate: {result.win_rate}")
        
        # Check if trades were generated
        if result.total_trades > 0:
            print("✅ SUCCESS: Trades were generated!")
        else:
            print("❌ PROBLEM: No trades were generated!")
            
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_backtest_engine()

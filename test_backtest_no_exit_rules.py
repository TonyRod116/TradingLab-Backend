#!/usr/bin/env python3
"""
Test script to verify backtest with only entry rules (no exit rules)
"""

import os
import sys
import django
from decimal import Decimal

# Add the project directory to Python path
sys.path.append('/home/tonirod/code/ga/projects/TradingLab-Backend-Clean')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from strategies.backtest_engine import BacktestEngine
from strategies.models import Strategy
from users.models import User

def test_backtest_no_exit_rules():
    """Test the backtest engine with only entry rules"""
    
    print("🧪 Testing Backtest Engine with Only Entry Rules")
    print("=" * 60)
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    # Create a test strategy with only entry rules (no exit rules)
    strategy_data = {
        'name': 'Test Entry Only Strategy',
        'description': 'Test strategy with only entry rules',
        'symbol': 'ES',
        'timeframe': '1h',
        'entry_rules': [
            {
                'name': 'Simple Price Entry',
                'rule_type': 'condition',
                'action_type': 'buy',
                'conditions': [
                    {
                        'left_operand': 'close',
                        'operator': 'gt',
                        'right_operand': 'open',
                        'logical_operator': 'and'
                    }
                ],
                'priority': 1,
                'parameters': {}
            }
        ],
        'exit_rules': [],  # Empty exit rules - rely only on stop loss and take profit
        'stop_loss_type': 'percentage',
        'stop_loss_value': Decimal('2.0'),
        'take_profit_type': 'percentage',
        'take_profit_value': Decimal('4.0'),
        'initial_capital': Decimal('100000'),
        'status': 'READY'
    }
    
    # Create strategy
    strategy = Strategy.objects.create(
        user=user,
        **strategy_data
    )
    
    print(f"✅ Created strategy: {strategy.name} (ID: {strategy.id})")
    print(f"   - Entry rules: {len(strategy.entry_rules)}")
    print(f"   - Exit rules: {len(strategy.exit_rules)}")
    
    # Test the backtest engine
    engine = BacktestEngine()
    
    # Test rule evaluation with sample data
    sample_row = {
        'date': '2023-01-01',
        'open': 4000.0,
        'high': 4010.0,
        'low': 3990.0,
        'close': 4005.0,
        'volume': 1000000
    }
    
    print("\n🔍 Testing Rule Evaluation:")
    print(f"   - Sample data: {sample_row}")
    
    # Test entry conditions
    entry_result = engine._check_entry_conditions(sample_row, strategy.entry_rules)
    print(f"   - Entry conditions met: {entry_result}")
    
    # Test exit conditions (should only use stop loss/take profit)
    sample_position = {
        'action': 'buy',
        'entry_price': 4000.0
    }
    
    exit_result = engine._check_exit_conditions(
        sample_row, sample_position, strategy.exit_rules,
        strategy.stop_loss_type, strategy.stop_loss_value,
        strategy.take_profit_type, strategy.take_profit_value
    )
    print(f"   - Exit conditions met: {exit_result}")
    
    # Run a full backtest
    print("\n🚀 Running Full Backtest:")
    try:
        from datetime import datetime
        from django.utils import timezone
        
        start_date = timezone.make_aware(datetime(2023, 1, 1))
        end_date = timezone.make_aware(datetime(2023, 1, 31))
        
        result = engine.run_backtest(
            strategy, 
            start_date, 
            end_date,
            initial_capital=Decimal('100000'),
            commission=Decimal('4.0'),
            slippage=Decimal('0.5')
        )
        
        print(f"   - Backtest Result ID: {result.id}")
        print(f"   - Total trades: {result.total_trades}")
        print(f"   - Win rate: {result.win_rate}%")
        print(f"   - Total return: {result.total_return}%")
        print(f"   - Profit factor: {result.profit_factor}")
        print(f"   - Max drawdown: {result.max_drawdown}%")
        
        # Get trades from the result
        trades = result.trades.all()
        if trades:
            print("   - Sample trades:")
            for i, trade in enumerate(trades[:5]):  # Show first 5 trades
                print(f"     Trade {i+1}: {trade.action} at {trade.entry_price} -> {trade.exit_price} ({trade.pnl})")
        else:
            print("   - No trades generated")
            
    except Exception as e:
        print(f"   - Error running backtest: {e}")
        import traceback
        traceback.print_exc()
    
    # Clean up
    strategy.delete()
    print(f"\n✅ Test completed - strategy deleted")

if __name__ == '__main__':
    test_backtest_no_exit_rules()

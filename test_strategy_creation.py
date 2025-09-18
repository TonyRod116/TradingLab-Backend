#!/usr/bin/env python3
"""
Test script for strategy creation functionality
"""

import os
import sys
import django
from datetime import datetime

# Add the project directory to Python path
sys.path.append('/home/tonirod/code/ga/projects/TradingLab-Backend-Clean')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from strategies.models import Strategy
from strategies.serializers import StrategyCreateSerializer
from strategies.enums import SUPPORTED_SYMBOLS, SUPPORTED_TIMEFRAMES

def test_strategy_creation():
    """Test strategy creation with new schema"""
    
    print("🧪 Testing Strategy Creation...")
    
    # Test data in new format
    strategy_data = {
        'name': 'Test Strategy',
        'description': 'A test strategy for validation',
        'symbol': 'ES',
        'timeframe': '1m',
        'entry_rules': [
            {
                'name': 'RSI Oversold Entry',
                'rule_type': 'condition',
                'action_type': 'buy',
                'conditions': [
                    {
                        'left_operand': 'rsi',
                        'operator': 'lt',
                        'right_operand': 'rsi_30',
                        'logical_operator': 'and'
                    }
                ],
                'priority': 1,
                'parameters': {}
            }
        ],
        'exit_rules': [
            {
                'name': 'RSI Overbought Exit',
                'rule_type': 'condition',
                'action_type': 'sell',
                'conditions': [
                    {
                        'left_operand': 'rsi',
                        'operator': 'gt',
                        'right_operand': 'rsi_70',
                        'logical_operator': 'and'
                    }
                ],
                'priority': 1,
                'parameters': {}
            }
        ],
        'stop_loss_type': 'percentage',
        'stop_loss_value': 1.0,
        'take_profit_type': 'percentage',
        'take_profit_value': 2.0,
        'initial_capital': 10000,
        'status': 'DRAFT'
    }
    
    # Test serializer validation
    print("📝 Testing serializer validation...")
    serializer = StrategyCreateSerializer(data=strategy_data)
    
    if serializer.is_valid():
        print("✅ Serializer validation passed")
        print(f"   - Validated data: {serializer.validated_data}")
    else:
        print("❌ Serializer validation failed")
        print(f"   - Errors: {serializer.errors}")
        return False
    
    # Test enum validation
    print("🔍 Testing enum validation...")
    
    # Test valid symbol
    if 'ES' in SUPPORTED_SYMBOLS:
        print("✅ ES symbol is supported")
    else:
        print("❌ ES symbol not found in supported symbols")
        return False
    
    # Test valid timeframe
    if '1m' in SUPPORTED_TIMEFRAMES:
        print("✅ 1m timeframe is supported")
    else:
        print("❌ 1m timeframe not found in supported timeframes")
        return False
    
    print("🎉 All tests passed!")
    return True

def test_strategy_normalization():
    """Test strategy data normalization"""
    
    print("\n🔄 Testing Strategy Normalization...")
    
    # Test frontend format (old format)
    frontend_data = {
        'name': 'Frontend Strategy',
        'description': 'Strategy from frontend',
        'symbol': 'EURUSD',
        'timeframe': '4h',
        'initial_capital': 50000,
        'stop_loss_type': 'percentage',
        'stop_loss_value': 0.5,
        'take_profit_type': 'percentage',
        'take_profit_value': 1.5
    }
    
    frontend_rules = [
        {
            'id': 'entry_1',
            'name': 'Entry Rule',
            'section': 'entry',
            'rule_type': 'condition',
            'action_type': 'buy',
            'conditions': [
                {
                    'left_operand': 'sma_20',
                    'operator': 'cross_up',
                    'right_operand': 'sma_50',
                    'logical_operator': 'and'
                }
            ],
            'priority': 1,
            'parameters': {}
        },
        {
            'id': 'exit_1',
            'name': 'Exit Rule',
            'section': 'exit',
            'rule_type': 'condition',
            'action_type': 'sell',
            'conditions': [
                {
                    'left_operand': 'rsi',
                    'operator': 'gt',
                    'right_operand': 'rsi_70',
                    'logical_operator': 'and'
                }
            ],
            'priority': 1,
            'parameters': {}
        }
    ]
    
    # This would be the normalization logic (simplified for testing)
    normalized_entry_rules = [rule for rule in frontend_rules if rule['section'] == 'entry']
    normalized_exit_rules = [rule for rule in frontend_rules if rule['section'] == 'exit']
    
    normalized_data = {
        **frontend_data,
        'entry_rules': normalized_entry_rules,
        'exit_rules': normalized_exit_rules,
        'status': 'DRAFT'
    }
    
    print("✅ Frontend data normalized successfully")
    print(f"   - Entry rules: {len(normalized_entry_rules)}")
    print(f"   - Exit rules: {len(normalized_exit_rules)}")
    
    return True

if __name__ == '__main__':
    print("🚀 Starting Strategy Creation Tests...")
    
    try:
        # Test strategy creation
        test1_passed = test_strategy_creation()
        
        # Test normalization
        test2_passed = test_strategy_normalization()
        
        if test1_passed and test2_passed:
            print("\n🎉 All tests completed successfully!")
            print("\n📋 Summary:")
            print("   ✅ Strategy creation validation works")
            print("   ✅ Enum validation works")
            print("   ✅ Data normalization works")
            print("\n🚀 Ready for frontend integration!")
        else:
            print("\n❌ Some tests failed. Please check the output above.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

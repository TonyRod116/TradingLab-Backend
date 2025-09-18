#!/usr/bin/env python3
"""
Test script to verify that exit rules are optional
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

from strategies.serializers import StrategyCreateSerializer
from users.models import User

def test_optional_exit_rules():
    """Test that exit rules are optional in the serializer"""
    
    print("🧪 Testing Optional Exit Rules in Serializer")
    print("=" * 60)
    
    # Create a test user
    user, created = User.objects.get_or_create(
        username='testuser',
        defaults={'email': 'test@example.com'}
    )
    
    # Test data with only entry rules (no exit rules)
    strategy_data = {
        'name': 'Test Strategy No Exit Rules',
        'description': 'Test strategy with only entry rules',
        'symbol': 'ES',
        'timeframe': '1h',
        'entry_rules': [
            {
                'name': 'Simple Entry',
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
        'exit_rules': [],  # Empty exit rules
        'stop_loss_type': 'percentage',
        'stop_loss_value': Decimal('2.0'),
        'take_profit_type': 'percentage',
        'take_profit_value': Decimal('4.0'),
        'initial_capital': Decimal('100000'),
        'status': 'READY'
    }
    
    print("✅ Testing serializer validation with empty exit rules...")
    
    # Test serializer validation
    serializer = StrategyCreateSerializer(data=strategy_data)
    
    if serializer.is_valid():
        print("✅ Serializer validation passed - exit rules are optional!")
        print(f"   - Entry rules: {len(serializer.validated_data['entry_rules'])}")
        print(f"   - Exit rules: {len(serializer.validated_data['exit_rules'])}")
        print(f"   - Status: {serializer.validated_data['status']}")
    else:
        print("❌ Serializer validation failed:")
        for field, errors in serializer.errors.items():
            print(f"   - {field}: {errors}")
    
    # Test data with no exit_rules field at all
    strategy_data_no_exit = {
        'name': 'Test Strategy No Exit Field',
        'description': 'Test strategy without exit_rules field',
        'symbol': 'ES',
        'timeframe': '1h',
        'entry_rules': [
            {
                'name': 'Simple Entry',
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
        # No exit_rules field at all
        'stop_loss_type': 'percentage',
        'stop_loss_value': Decimal('2.0'),
        'take_profit_type': 'percentage',
        'take_profit_value': Decimal('4.0'),
        'initial_capital': Decimal('100000'),
        'status': 'READY'
    }
    
    print("\n✅ Testing serializer validation without exit_rules field...")
    
    serializer2 = StrategyCreateSerializer(data=strategy_data_no_exit)
    
    if serializer2.is_valid():
        print("✅ Serializer validation passed - exit_rules field is optional!")
        print(f"   - Entry rules: {len(serializer2.validated_data['entry_rules'])}")
        print(f"   - Exit rules: {len(serializer2.validated_data.get('exit_rules', []))}")
        print(f"   - Status: {serializer2.validated_data['status']}")
    else:
        print("❌ Serializer validation failed:")
        for field, errors in serializer2.errors.items():
            print(f"   - {field}: {errors}")
    
    print(f"\n✅ Test completed")

if __name__ == '__main__':
    test_optional_exit_rules()

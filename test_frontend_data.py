#!/usr/bin/env python3
"""
Test script to verify what the frontend is actually sending
"""

import os
import sys
import django
import json
from decimal import Decimal

# Add the project directory to Python path
sys.path.append('/home/tonirod/code/ga/projects/TradingLab-Backend-Clean')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from strategies.serializers import StrategyCreateSerializer
from users.models import User

def test_frontend_data_format():
    """Test the exact data format that frontend sends"""
    
    print("🧪 Testing Frontend Data Format")
    print("=" * 60)
    
    # Simulate what the frontend sends when user skips exit rules
    frontend_data = {
        'name': 'Test Frontend Data',
        'description': 'Test strategy from frontend',
        'symbol': 'ES',
        'timeframe': '1h',
        'entry_rules': [
            {
                'name': 'Entry Rule 1',
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
        'exit_rules': [],  # Empty array from frontend
        'stop_loss_type': 'percentage',
        'stop_loss_value': 2.0,
        'take_profit_type': 'percentage',
        'take_profit_value': 4.0,
        'initial_capital': 100000,
        'status': 'READY'
    }
    
    print("✅ Testing with empty exit_rules array...")
    print(f"   - exit_rules type: {type(frontend_data['exit_rules'])}")
    print(f"   - exit_rules length: {len(frontend_data['exit_rules'])}")
    print(f"   - exit_rules content: {frontend_data['exit_rules']}")
    
    serializer = StrategyCreateSerializer(data=frontend_data)
    
    if serializer.is_valid():
        print("✅ Serializer validation passed!")
        print(f"   - Entry rules: {len(serializer.validated_data['entry_rules'])}")
        print(f"   - Exit rules: {len(serializer.validated_data['exit_rules'])}")
        print(f"   - Status: {serializer.validated_data['status']}")
    else:
        print("❌ Serializer validation failed:")
        for field, errors in serializer.errors.items():
            print(f"   - {field}: {errors}")
    
    # Test with no exit_rules field at all
    frontend_data_no_exit = {
        'name': 'Test Frontend Data No Exit',
        'description': 'Test strategy without exit_rules field',
        'symbol': 'ES',
        'timeframe': '1h',
        'entry_rules': [
            {
                'name': 'Entry Rule 1',
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
        'stop_loss_value': 2.0,
        'take_profit_type': 'percentage',
        'take_profit_value': 4.0,
        'initial_capital': 100000,
        'status': 'READY'
    }
    
    print("\n✅ Testing without exit_rules field...")
    print(f"   - Has exit_rules: {'exit_rules' in frontend_data_no_exit}")
    
    serializer2 = StrategyCreateSerializer(data=frontend_data_no_exit)
    
    if serializer2.is_valid():
        print("✅ Serializer validation passed!")
        print(f"   - Entry rules: {len(serializer2.validated_data['entry_rules'])}")
        print(f"   - Exit rules: {len(serializer2.validated_data.get('exit_rules', []))}")
        print(f"   - Status: {serializer2.validated_data['status']}")
    else:
        print("❌ Serializer validation failed:")
        for field, errors in serializer2.errors.items():
            print(f"   - {field}: {errors}")
    
    print(f"\n✅ Frontend data format test completed")

if __name__ == '__main__':
    test_frontend_data_format()

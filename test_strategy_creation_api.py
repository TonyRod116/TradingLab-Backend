#!/usr/bin/env python3
"""
Test script to verify strategy creation API works without exit rules
"""

import os
import sys
import django
import requests
import json
from decimal import Decimal

# Add the project directory to Python path
sys.path.append('/home/tonirod/code/ga/projects/TradingLab-Backend-Clean')

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from users.models import User
from django.contrib.auth import authenticate

def test_strategy_creation_api():
    """Test strategy creation API with optional exit rules"""
    
    print("🧪 Testing Strategy Creation API with Optional Exit Rules")
    print("=" * 70)
    
    # Test data with only entry rules (no exit rules)
    strategy_data = {
        'name': 'Test Strategy API No Exit Rules',
        'description': 'Test strategy with only entry rules via API',
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
        'stop_loss_value': 2.0,
        'take_profit_type': 'percentage',
        'take_profit_value': 4.0,
        'initial_capital': 100000,
        'status': 'READY'
    }
    
    print("✅ Testing API endpoint with empty exit rules...")
    
    # Test API endpoint
    url = 'http://localhost:8000/api/strategies/'
    headers = {
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    try:
        response = requests.post(url, json=strategy_data, headers=headers, timeout=10)
        print(f"   - Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ API request successful!")
            print(f"   - Strategy ID: {result.get('id')}")
            print(f"   - Strategy Name: {result.get('name')}")
            print(f"   - Entry Rules: {len(result.get('entry_rules', []))}")
            print(f"   - Exit Rules: {len(result.get('exit_rules', []))}")
            print(f"   - Status: {result.get('status')}")
        else:
            print("❌ API request failed:")
            print(f"   - Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    # Test data with no exit_rules field at all
    strategy_data_no_exit = {
        'name': 'Test Strategy API No Exit Field',
        'description': 'Test strategy without exit_rules field via API',
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
        'stop_loss_value': 2.0,
        'take_profit_type': 'percentage',
        'take_profit_value': 4.0,
        'initial_capital': 100000,
        'status': 'READY'
    }
    
    print("\n✅ Testing API endpoint without exit_rules field...")
    
    try:
        response = requests.post(url, json=strategy_data_no_exit, headers=headers, timeout=10)
        print(f"   - Status Code: {response.status_code}")
        
        if response.status_code == 201:
            result = response.json()
            print("✅ API request successful!")
            print(f"   - Strategy ID: {result.get('id')}")
            print(f"   - Strategy Name: {result.get('name')}")
            print(f"   - Entry Rules: {len(result.get('entry_rules', []))}")
            print(f"   - Exit Rules: {len(result.get('exit_rules', []))}")
            print(f"   - Status: {result.get('status')}")
        else:
            print("❌ API request failed:")
            print(f"   - Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
    
    print(f"\n✅ API test completed")

if __name__ == '__main__':
    test_strategy_creation_api()
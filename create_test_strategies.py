#!/usr/bin/env python
"""
Script to create test strategies for different users
"""
import os
import sys
import django
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from strategies.models import Strategy, BacktestResult, EquityCurvePoint
from django.contrib.auth.models import User

def create_test_users():
    """Create test users if they don't exist"""
    users = [
        {'username': 'alice', 'email': 'alice@test.com'},
        {'username': 'bob', 'email': 'bob@test.com'},
        {'username': 'charlie', 'email': 'charlie@test.com'},
    ]
    
    created_users = []
    for user_data in users:
        user, created = User.objects.get_or_create(
            username=user_data['username'],
            defaults={'email': user_data['email']}
        )
        if created:
            user.set_password('password123')
            user.save()
            print(f"✅ Created user: {user.username}")
        else:
            print(f"ℹ️ User already exists: {user.username}")
        created_users.append(user)
    
    return created_users

def create_test_strategies(users):
    """Create test strategies for different users"""
    strategies_data = [
        {
            'name': 'Alice RSI Strategy',
            'description': 'RSI-based strategy by Alice',
            'symbol': 'ES',
            'timeframe': '1h',
            'entry_rules': {'rsi_oversold': 30},
            'exit_rules': {'time_based': True},
            'stop_loss_type': 'percentage',
            'stop_loss_value': '2.0000',
            'take_profit_type': 'percentage',
            'take_profit_value': '4.0000',
            'initial_capital': '50000.00',
            'user': users[0]
        },
        {
            'name': 'Bob Moving Average Strategy',
            'description': 'MA crossover strategy by Bob',
            'symbol': 'NQ',
            'timeframe': '30m',
            'entry_rules': {'price_above_ma': 20},
            'exit_rules': {'time_based': True},
            'stop_loss_type': 'atr',
            'stop_loss_value': '1.5000',
            'take_profit_type': 'atr',
            'take_profit_value': '3.0000',
            'initial_capital': '75000.00',
            'user': users[1]
        },
        {
            'name': 'Charlie MACD Strategy',
            'description': 'MACD momentum strategy by Charlie',
            'symbol': 'ES',
            'timeframe': '4h',
            'entry_rules': {'macd_signal': True},
            'exit_rules': {'time_based': True},
            'stop_loss_type': 'points',
            'stop_loss_value': '20.0000',
            'take_profit_type': 'points',
            'take_profit_value': '40.0000',
            'initial_capital': '100000.00',
            'user': users[2]
        }
    ]
    
    created_strategies = []
    for strategy_data in strategies_data:
        strategy, created = Strategy.objects.get_or_create(
            name=strategy_data['name'],
            user=strategy_data['user'],
            defaults=strategy_data
        )
        if created:
            print(f"✅ Created strategy: {strategy.name} for {strategy.user.username}")
        else:
            print(f"ℹ️ Strategy already exists: {strategy.name}")
        created_strategies.append(strategy)
    
    return created_strategies

def main():
    """Create test data"""
    print("🚀 Creating test users and strategies...")
    
    # Create users
    users = create_test_users()
    
    # Create strategies
    strategies = create_test_strategies(users)
    
    print(f"✅ Created {len(users)} users and {len(strategies)} strategies")
    print("🎯 Now you should see strategies from different users in Community Backtests!")

if __name__ == "__main__":
    main()

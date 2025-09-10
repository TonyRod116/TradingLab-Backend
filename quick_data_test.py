#!/usr/bin/env python
"""
Quick test to generate minimal data and test backtest
"""
import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from market_data.models import HistoricalData
from strategies.models import Strategy
from strategies.backtest_engine import BacktestEngine

def create_minimal_data():
    """Create minimal test data"""
    print("🔍 [QUICK] Creating minimal test data...")
    
    # Clear existing data
    HistoricalData.objects.filter(symbol='ES', timeframe='1m').delete()
    
    # Create 1000 records of test data
    base_price = 4000
    current_time = datetime(2024, 1, 1, 9, 30)  # Start of trading day
    
    records = []
    for i in range(1000):
        # Simple random walk
        change = (i % 100 - 50) * 0.1  # Oscillating price
        price = base_price + change
        
        records.append(HistoricalData(
            symbol='ES',
            timeframe='1m',
            date=current_time + timedelta(minutes=i),
            open_price=Decimal(str(price)),
            high_price=Decimal(str(price + 0.5)),
            low_price=Decimal(str(price - 0.5)),
            close_price=Decimal(str(price + 0.1)),
            volume=1000
        ))
    
    HistoricalData.objects.bulk_create(records)
    print(f"✅ [QUICK] Created {len(records)} test records")

def test_backtest():
    """Test backtest with minimal data"""
    print("🔍 [QUICK] Testing backtest...")
    
    # Create test strategy
    strategy = Strategy(
        name='Quick Test Strategy',
        description='Test strategy',
        symbol='ES',
        timeframe='1m',
        initial_capital=100000,
        entry_rules={'rsi_oversold': 30},
        exit_rules={'time_based': True},
        stop_loss_type='percentage',
        stop_loss_value=2.0,
        take_profit_type='percentage',
        take_profit_value=4.0
    )
    
    # Test backtest engine
    engine = BacktestEngine()
    
    try:
        result = engine.run_backtest(
            strategy=strategy,
            start_date=datetime(2024, 1, 1),
            end_date=datetime(2024, 1, 2),
            initial_capital=Decimal('100000'),
            commission=Decimal('4.00'),
            slippage=Decimal('0.5')
        )
        
        print(f"✅ [QUICK] Backtest completed!")
        print(f"✅ [QUICK] Total trades: {result.total_trades}")
        print(f"✅ [QUICK] Total return: {result.total_return}")
        
    except Exception as e:
        print(f"❌ [QUICK] Backtest failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_minimal_data()
    test_backtest()

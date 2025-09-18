#!/usr/bin/env python3
"""
Check what data is available in Parquet files
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

from market_data.parquet_service import ParquetDataService
from datetime import datetime, timedelta

def check_parquet_data():
    """Check what data is available in Parquet files"""
    
    print("📊 Checking Parquet Data Availability")
    print("=" * 50)
    
    parquet_service = ParquetDataService()
    
    # Check available symbols and timeframes
    try:
        available_data = parquet_service.get_available_data()
        print(f"Available data: {available_data}")
    except Exception as e:
        print(f"Error getting available data: {e}")
    
    # Test specific symbol and timeframe
    test_symbols = ['ES', 'NQ', 'YM', 'RTY']
    test_timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
    
    print("\nTesting data availability:")
    for symbol in test_symbols:
        for timeframe in test_timeframes:
            try:
                is_available = parquet_service.is_parquet_available(symbol, timeframe)
                if is_available:
                    print(f"  ✅ {symbol} {timeframe} - Available")
                    
                    # Try to get a small sample
                    try:
                        end_date = datetime.now()
                        start_date = end_date - timedelta(days=7)
                        df = parquet_service.get_candles(symbol, timeframe, start_date, end_date)
                        print(f"    Sample data: {len(df)} records from {df['date'].min()} to {df['date'].max()}")
                    except Exception as e:
                        print(f"    Error getting sample: {e}")
                else:
                    print(f"  ❌ {symbol} {timeframe} - Not available")
            except Exception as e:
                print(f"  ❌ {symbol} {timeframe} - Error: {e}")

if __name__ == '__main__':
    check_parquet_data()

#!/usr/bin/env python3
"""
Check what historical data is available
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

from strategies.models import HistoricalData
from django.db import models

def check_historical_data():
    """Check what historical data is available"""
    
    print("📊 Checking Historical Data Availability")
    print("=" * 50)
    
    # Check total count
    total_count = HistoricalData.objects.count()
    print(f"Total records: {total_count}")
    
    if total_count == 0:
        print("❌ No historical data found!")
        return
    
    # Check unique symbols and timeframes
    symbols = HistoricalData.objects.values_list('symbol', flat=True).distinct()
    timeframes = HistoricalData.objects.values_list('timeframe', flat=True).distinct()
    
    print(f"Symbols: {list(symbols)}")
    print(f"Timeframes: {list(timeframes)}")
    
    # Check date ranges
    min_date = HistoricalData.objects.aggregate(min_date=models.Min('date'))['min_date']
    max_date = HistoricalData.objects.aggregate(max_date=models.Max('date'))['max_date']
    print(f"Date range: {min_date} to {max_date}")
    
    # Show sample data
    print("\nSample data:")
    for data in HistoricalData.objects.all()[:5]:
        print(f"  {data.symbol} {data.timeframe} - {data.date} - O:{data.open} H:{data.high} L:{data.low} C:{data.close}")

if __name__ == '__main__':
    check_historical_data()

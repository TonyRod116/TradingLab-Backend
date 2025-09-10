#!/usr/bin/env python
"""
Script to generate test market data for backtesting
"""
import os
import sys
import django
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from market_data.models import HistoricalData

def generate_test_data():
    """Generate realistic test data for ES futures"""
    
    print("🔍 [DATA] Generating test market data...")
    
    # Generate 5 years of 1-minute data
    start_date = datetime(2020, 1, 1)
    end_date = datetime(2024, 12, 31)
    
    # Create date range for 1-minute intervals
    date_range = pd.date_range(start=start_date, end=end_date, freq='1min')
    
    # Filter for trading hours (9:30 AM - 4:00 PM EST, Monday-Friday)
    trading_hours = []
    for dt in date_range:
        if dt.weekday() < 5:  # Monday-Friday
            if 9.5 <= dt.hour + dt.minute/60 <= 16:  # 9:30 AM - 4:00 PM
                trading_hours.append(dt)
    
    print(f"🔍 [DATA] Generated {len(trading_hours)} trading minutes")
    
    # Generate realistic price data
    base_price = 4000  # Starting price for ES
    prices = []
    current_price = base_price
    
    for i, dt in enumerate(trading_hours):
        # Random walk with slight upward bias
        change = np.random.normal(0, 0.5)  # Small random change
        current_price += change
        
        # Ensure price stays in realistic range
        current_price = max(3000, min(6500, current_price))
        
        # Generate OHLCV
        open_price = current_price
        high_price = current_price + abs(np.random.normal(0, 1))
        low_price = current_price - abs(np.random.normal(0, 1))
        close_price = current_price + np.random.normal(0, 0.3)
        volume = int(np.random.normal(1000, 200))
        
        prices.append({
            'symbol': 'ES',
            'timeframe': '1m',
            'timestamp': dt,
            'open': round(open_price, 2),
            'high': round(high_price, 2),
            'low': round(low_price, 2),
            'close': round(close_price, 2),
            'volume': max(1, volume)
        })
        
        current_price = close_price
        
        if i % 10000 == 0:
            print(f"🔍 [DATA] Generated {i} records...")
    
    print(f"🔍 [DATA] Generated {len(prices)} price records")
    
    # Convert to DataFrame
    df = pd.DataFrame(prices)
    
    # Add technical indicators
    df['sma_20'] = df['close'].rolling(window=20).mean()
    df['sma_50'] = df['close'].rolling(window=50).mean()
    df['rsi'] = calculate_rsi(df['close'], 14)
    df['atr'] = calculate_atr(df, 14)
    
    print("🔍 [DATA] Added technical indicators")
    
    # Save to database
    print("🔍 [DATA] Saving to database...")
    
    # Clear existing data
    HistoricalData.objects.filter(symbol='ES', timeframe='1m').delete()
    
    # Save in batches
    batch_size = 1000
    for i in range(0, len(df), batch_size):
        batch = df.iloc[i:i+batch_size]
        
        records = []
        for _, row in batch.iterrows():
            records.append(HistoricalData(
                symbol=row['symbol'],
                timeframe=row['timeframe'],
                timestamp=row['timestamp'],
                open_price=Decimal(str(row['open'])),
                high_price=Decimal(str(row['high'])),
                low_price=Decimal(str(row['low'])),
                close_price=Decimal(str(row['close'])),
                volume=int(row['volume']),
                sma_20=Decimal(str(row['sma_20'])) if pd.notna(row['sma_20']) else None,
                sma_50=Decimal(str(row['sma_50'])) if pd.notna(row['sma_50']) else None,
                rsi=Decimal(str(row['rsi'])) if pd.notna(row['rsi']) else None,
                atr=Decimal(str(row['atr'])) if pd.notna(row['atr']) else None
            ))
        
        HistoricalData.objects.bulk_create(records)
        
        if i % 50000 == 0:
            print(f"🔍 [DATA] Saved {i} records to database...")
    
    print("✅ [DATA] Test data generation completed!")
    print(f"✅ [DATA] Total records: {len(df)}")
    print(f"✅ [DATA] Date range: {df['timestamp'].min()} to {df['timestamp'].max()}")
    print(f"✅ [DATA] Price range: {df['close'].min():.2f} to {df['close'].max():.2f}")

def calculate_rsi(prices, period=14):
    """Calculate RSI indicator"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_atr(df, period=14):
    """Calculate Average True Range"""
    high_low = df['high'] - df['low']
    high_close = np.abs(df['high'] - df['close'].shift())
    low_close = np.abs(df['low'] - df['close'].shift())
    
    ranges = pd.concat([high_low, high_close, low_close], axis=1)
    true_range = np.max(ranges, axis=1)
    atr = true_range.rolling(period).mean()
    return atr

if __name__ == "__main__":
    generate_test_data()

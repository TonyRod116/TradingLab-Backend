"""
Example usage of Technical Indicators
"""

import pandas as pd
import numpy as np
from services import TechnicalAnalysisService


def create_sample_data():
    """Create sample OHLCV data for testing"""
    np.random.seed(42)
    
    # Generate 100 days of sample data
    dates = pd.date_range('2024-01-01', periods=100, freq='D')
    
    # Start with a base price and add some trend + noise
    base_price = 100
    trend = np.linspace(0, 20, 100)  # Upward trend
    noise = np.random.normal(0, 2, 100)
    
    close_prices = base_price + trend + noise
    
    # Generate OHLC data
    data = []
    for i, (date, close) in enumerate(zip(dates, close_prices)):
        # Generate realistic OHLC from close price
        volatility = np.random.uniform(0.5, 2.0)
        
        high = close + np.random.uniform(0, volatility)
        low = close - np.random.uniform(0, volatility)
        open_price = np.random.uniform(low, high)
        
        # Ensure OHLC relationship
        high = max(high, open_price, close)
        low = min(low, open_price, close)
        
        volume = np.random.randint(1000, 10000)
        
        data.append({
            'date': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        })
    
    df = pd.DataFrame(data)
    df.set_index('date', inplace=True)
    
    return df


def main():
    """Main example function"""
    print("=== Technical Indicators Example ===\n")
    
    # Create sample data
    print("1. Creating sample OHLCV data...")
    sample_data = create_sample_data()
    print(f"   Created {len(sample_data)} data points")
    print(f"   Date range: {sample_data.index[0]} to {sample_data.index[-1]}")
    print(f"   Price range: ${sample_data['low'].min():.2f} - ${sample_data['high'].max():.2f}")
    print()
    
    # Initialize service
    print("2. Initializing Technical Analysis Service...")
    ta_service = TechnicalAnalysisService(sample_data)
    print("   ✅ Service initialized successfully")
    print()
    
    # Calculate all indicators
    print("3. Calculating all indicators...")
    try:
        all_indicators = ta_service.calculate_all_indicators()
        print(f"   ✅ Calculated {len(all_indicators.columns)} columns")
        print(f"   Available indicators: {list(all_indicators.columns)}")
        print()
    except Exception as e:
        print(f"   ❌ Error calculating indicators: {e}")
        return
    
    # Show sample of results
    print("4. Sample results (last 5 rows):")
    print(all_indicators.tail()[['open', 'high', 'low', 'close', 'sma_20', 'rsi', 'atr']].round(2))
    print()
    
    # Get trend analysis
    print("5. Trend Analysis:")
    try:
        trend_analysis = ta_service.get_trend_analysis()
        for key, value in trend_analysis.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
        print()
    except Exception as e:
        print(f"   ❌ Error in trend analysis: {e}")
    
    # Get momentum analysis
    print("6. Momentum Analysis:")
    try:
        momentum_analysis = ta_service.get_momentum_analysis()
        for key, value in momentum_analysis.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.2f}")
            else:
                print(f"   {key}: {value}")
        print()
    except Exception as e:
        print(f"   ❌ Error in momentum analysis: {e}")
    
    # Test individual indicators
    print("7. Testing individual indicators:")
    try:
        # Test VWAP
        vwap = ta_service.get_indicator('vwap')
        print(f"   VWAP (last value): {vwap.iloc[-1]:.2f}")
        
        # Test Bollinger Bands
        bb_upper, bb_middle, bb_lower = ta_service.get_indicator('bollinger_bands')
        print(f"   Bollinger Bands (last values):")
        print(f"     Upper: {bb_upper.iloc[-1]:.2f}")
        print(f"     Middle: {bb_middle.iloc[-1]:.2f}")
        print(f"     Lower: {bb_lower.iloc[-1]:.2f}")
        
        # Test MACD
        macd_line, signal_line, histogram = ta_service.get_indicator('macd')
        print(f"   MACD (last values):")
        print(f"     Line: {macd_line.iloc[-1]:.2f}")
        print(f"     Signal: {signal_line.iloc[-1]:.2f}")
        print(f"     Histogram: {histogram.iloc[-1]:.2f}")
        
    except Exception as e:
        print(f"   ❌ Error testing individual indicators: {e}")
    
    print("\n=== Example completed successfully! ===")


if __name__ == "__main__":
    main()

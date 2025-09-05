#!/usr/bin/env python3
"""
Test script to verify that real rule evaluation is working
Run this to see the difference between fake and real rule evaluation
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from strategies.rule_evaluator import StrategyRuleEvaluator

def create_test_data():
    """Create synthetic market data for testing"""
    dates = pd.date_range(start='2023-01-01', end='2023-01-31', freq='1H')
    
    # Create realistic price data
    base_price = 4500
    price_data = []
    current_price = base_price
    
    for i, date in enumerate(dates):
        # Add some random walk
        change = np.random.randn() * 2
        current_price += change
        
        # Keep price in reasonable range
        current_price = max(4000, min(5000, current_price))
        
        # Create OHLC data
        high = current_price + abs(np.random.randn()) * 3
        low = current_price - abs(np.random.randn()) * 3
        open_price = current_price + np.random.randn() * 1
        
        price_data.append({
            'date': date,
            'open': open_price,
            'high': high,
            'low': low,
            'close': current_price,
            'volume': int(1000 + np.random.randn() * 200)
        })
    
    return pd.DataFrame(price_data)

def test_rsi_strategy():
    """Test RSI-based strategy rules"""
    print("=== Testing RSI Strategy Rules ===")
    
    # Create test data
    df = create_test_data()
    print(f"Created {len(df)} rows of test data")
    
    # Create rule evaluator
    try:
        evaluator = StrategyRuleEvaluator(df)
        print("✓ Rule evaluator created successfully")
    except Exception as e:
        print(f"✗ Failed to create rule evaluator: {e}")
        return
    
    # Test RSI oversold entry rule
    rsi_entry_rule = {
        "rule_type": "condition",
        "condition_type": "indicator", 
        "left_operand": "rsi",
        "operator": "lt",
        "right_operand": "30"
    }
    
    # Test on a few data points
    entry_signals = 0
    for i in range(50, len(df)):  # Start after indicators warm up
        try:
            is_entry = evaluator.evaluate_entry_rules(i, rsi_entry_rule)
            if is_entry:
                entry_signals += 1
                row = evaluator.indicators_data.iloc[i]
                print(f"Entry signal at index {i}: RSI = {row.get('rsi', 'N/A'):.2f}, Price = {row['close']:.2f}")
        except Exception as e:
            print(f"Error evaluating at index {i}: {e}")
    
    print(f"Total entry signals found: {entry_signals}")
    
    # Show some indicator values for verification
    print("\n=== Sample Indicator Values ===")
    sample_row = evaluator.indicators_data.iloc[100]
    indicators = evaluator.get_current_indicators(100)
    print("Available indicators:")
    for indicator, value in indicators.items():
        if not pd.isna(value):
            print(f"  {indicator}: {value:.4f}")

def test_sma_crossover():
    """Test SMA crossover strategy"""
    print("\n=== Testing SMA Crossover Strategy ===")
    
    df = create_test_data()
    evaluator = StrategyRuleEvaluator(df)
    
    # Test SMA 20 > SMA 50 crossover
    sma_crossover_rule = {
        "rule_type": "condition",
        "condition_type": "indicator",
        "left_operand": "sma_20", 
        "operator": "gt",
        "right_operand": "sma_50"
    }
    
    crossover_signals = 0
    for i in range(50, len(df)):
        try:
            is_entry = evaluator.evaluate_entry_rules(i, sma_crossover_rule)
            if is_entry:
                crossover_signals += 1
                row = evaluator.indicators_data.iloc[i]
                sma_20 = row.get('sma_20', 0)
                sma_50 = row.get('sma_50', 0)
                print(f"Crossover at index {i}: SMA20 = {sma_20:.2f}, SMA50 = {sma_50:.2f}, Price = {row['close']:.2f}")
        except Exception as e:
            print(f"Error at index {i}: {e}")
    
    print(f"Total crossover signals: {crossover_signals}")

if __name__ == "__main__":
    print("Testing REAL Rule Evaluation System")
    print("=" * 50)
    
    try:
        test_rsi_strategy()
        test_sma_crossover()
        print("\n✓ All tests completed!")
        print("\nNOTE: If you see entry signals above, then REAL rule evaluation is working!")
        print("If you see warnings or no signals, check the rule format or indicator calculations.")
        
    except Exception as e:
        print(f"✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
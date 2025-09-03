#!/usr/bin/env python3
"""
Test script to demonstrate QuantConnect integration with natural language parsing
"""

import json
from quantconnect_service import QuantConnectService
from quantconnect_parser import QuantConnectNaturalLanguageParser


def test_natural_language_parsing():
    """Test natural language parsing functionality"""
    print("=== Testing Natural Language Parsing ===\n")
    
    parser = QuantConnectNaturalLanguageParser()
    
    # Test cases
    test_cases = [
        {
            "description": "Buy SPY when price is above 20-day SMA, sell when RSI is overbought above 70",
            "expected_symbols": ["SPY"],
            "expected_indicators": ["SMA", "RSI"]
        },
        {
            "description": "Create a strategy for Apple stock using 50-day EMA and MACD indicators",
            "expected_symbols": ["AAPL"],
            "expected_indicators": ["EMA", "MACD"]
        },
        {
            "description": "Simple buy and hold strategy for QQQ with daily resolution",
            "expected_symbols": ["QQQ"],
            "expected_indicators": []
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"Test Case {i}: {test_case['description']}")
        
        # Parse the description
        strategy_code = parser.parse_strategy_description(test_case['description'])
        
        print("Generated Code:")
        print("-" * 50)
        print(strategy_code)
        print("-" * 50)
        print()
        
        # Check if expected symbols are in the code
        for symbol in test_case['expected_symbols']:
            if symbol in strategy_code:
                print(f"✅ Found expected symbol: {symbol}")
            else:
                print(f"❌ Missing expected symbol: {symbol}")
        
        # Check if expected indicators are in the code
        for indicator in test_case['expected_indicators']:
            if indicator in strategy_code:
                print(f"✅ Found expected indicator: {indicator}")
            else:
                print(f"❌ Missing expected indicator: {indicator}")
        
        print("\n" + "="*60 + "\n")


def test_quantconnect_service():
    """Test QuantConnect service functionality"""
    print("=== Testing QuantConnect Service ===\n")
    
    service = QuantConnectService()
    
    # Test authentication
    print("1. Testing Authentication...")
    auth_result = service.test_authentication()
    print(f"Authentication Result: {json.dumps(auth_result, indent=2)}")
    print()
    
    # Test project creation
    print("2. Testing Project Creation...")
    project_result = service.create_project("Test_Strategy_Parser", "Python")
    print(f"Project Creation Result: {json.dumps(project_result, indent=2)}")
    print()
    
    # Test natural language parsing
    print("3. Testing Natural Language Parsing...")
    description = "Buy SPY when price is above 20-day SMA, sell when RSI is overbought above 70"
    parse_result = service.parse_natural_language_strategy(description)
    print(f"Parse Result: {json.dumps(parse_result, indent=2)}")
    print()


def test_complete_workflow():
    """Test complete workflow from natural language to compiled code"""
    print("=== Testing Complete Workflow ===\n")
    
    service = QuantConnectService()
    
    # Test complete workflow
    description = "Create a simple strategy that buys SPY when price is above 20-day SMA"
    strategy_data = {
        "symbols": ["SPY"],
        "indicators": [{"type": "SMA", "period": 20, "name": "sma"}],
        "timeframe": "Resolution.Daily"
    }
    
    print(f"Description: {description}")
    print(f"Strategy Data: {json.dumps(strategy_data, indent=2)}")
    print()
    
    # Run complete workflow
    result = service.run_complete_workflow(strategy_data, description)
    print(f"Complete Workflow Result: {json.dumps(result, indent=2)}")
    print()


def main():
    """Main test function"""
    print("QuantConnect Integration Test Suite")
    print("=" * 50)
    print()
    
    try:
        # Test natural language parsing
        test_natural_language_parsing()
        
        # Test QuantConnect service
        test_quantconnect_service()
        
        # Test complete workflow
        test_complete_workflow()
        
        print("✅ All tests completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

# Backtest Period Examples - Natural Language Support

## 🚀 **Complete Backtest Period Support**

The system now supports **ALL** possible backtest periods that users can specify in natural language. Here are comprehensive examples:

## ⏰ **Supported Backtest Periods**

### **Standard Periods**

#### **Years**
- `"last year"` → 1 year backtest
- `"last 2 years"` → 2 years backtest
- `"last 3 years"` → 3 years backtest
- `"last 5 years"` → 5 years backtest
- `"last 10 years"` → 10 years backtest
- `"past year"` → 1 year backtest
- `"past 5 years"` → 5 years backtest
- `"recent 3 years"` → 3 years backtest

#### **Months**
- `"last month"` → 1 month backtest
- `"last 3 months"` → 3 months backtest
- `"last 6 months"` → 6 months backtest
- `"last 9 months"` → 9 months backtest
- `"past 6 months"` → 6 months backtest
- `"recent 3 months"` → 3 months backtest

#### **Quarters**
- `"last quarter"` → 3 months backtest
- `"last 2 quarters"` → 6 months backtest
- `"last 3 quarters"` → 9 months backtest
- `"last 4 quarters"` → 1 year backtest
- `"last 6 quarters"` → 1.5 years backtest
- `"last 8 quarters"` → 2 years backtest
- `"last 12 quarters"` → 3 years backtest
- `"last 16 quarters"` → 4 years backtest
- `"last 20 quarters"` → 5 years backtest

#### **Weeks**
- `"last week"` → 7 days backtest
- `"last 2 weeks"` → 14 days backtest
- `"last 3 weeks"` → 21 days backtest
- `"past 2 weeks"` → 14 days backtest

#### **Days**
- `"1 day"` → 1 day backtest
- `"5 days"` → 5 days backtest
- `"10 days"` → 10 days backtest
- `"30 days"` → 30 days backtest
- `"90 days"` → 90 days backtest
- `"180 days"` → 180 days backtest
- `"365 days"` → 1 year backtest
- `"500 days"` → 500 days backtest
- `"1000 days"` → 1000 days backtest
- `"2000 days"` → 2000 days backtest
- `"3000 days"` → 3000 days backtest

### **Special Periods**

#### **Year-to-Date**
- `"ytd"` → Year to date
- `"year to date"` → Year to date

#### **Month-to-Date**
- `"mtd"` → Month to date
- `"month to date"` → Month to date

#### **Quarter-to-Date**
- `"qtd"` → Quarter to date
- `"quarter to date"` → Quarter to date

### **Market Cycles**

#### **Bull/Bear Markets**
- `"bull market"` → 2009-2020 bull market period
- `"bear market"` → 2007-2009 bear market period

#### **Crisis Periods**
- `"covid period"` → 2020-2021 COVID period
- `"covid crash"` → Feb-Apr 2020 crash
- `"covid recovery"` → Apr 2020-Dec 2021 recovery
- `"financial crisis"` → 2007-2009 financial crisis
- `"dot com bubble"` → 1998-2000 dot com bubble
- `"dot com crash"` → 2000-2002 dot com crash

### **Specific Years**
- `"2020"` → Full year 2020
- `"2021"` → Full year 2021
- `"2022"` → Full year 2022
- `"2023"` → Full year 2023
- `"2024"` → Full year 2024
- `"2019"` → Full year 2019
- `"2018"` → Full year 2018
- `"2017"` → Full year 2017
- `"2016"` → Full year 2016
- `"2015"` → Full year 2015

### **Decades**
- `"2010s"` → 2010-2019 decade
- `"2020s"` → 2020-present decade
- `"last decade"` → 2010-2019 decade
- `"current decade"` → 2020-present decade

### **Maximum Periods**
- `"all time"` → Maximum available data (from 2000)
- `"maximum"` → Maximum available data
- `"full history"` → Maximum available data
- `"complete history"` → Maximum available data
- `"entire history"` → Maximum available data

## 🎯 **Usage Examples**

### **Example 1: Last Year Strategy**
```json
{
  "description": "Trade SPY using RSI and SMA on daily timeframe for the last year",
  "strategy": {
    "symbols": ["SPY"],
    "timeframe": "1d",
    "indicators": [
      {"type": "RSI", "period": 14, "name": "rsi"},
      {"type": "SMA", "period": 20, "name": "sma"}
    ]
  }
}
```

**Generated Code:**
```python
# Set start and end dates
self.SetStartDate(2023, 1, 1)  # Last year
self.SetEndDate(2024, 1, 1)
```

### **Example 2: COVID Period Strategy**
```json
{
  "description": "Trade Gold futures using ATR and Bollinger Bands during the COVID period",
  "strategy": {
    "symbols": ["GC"],
    "timeframe": "1h",
    "indicators": [
      {"type": "ATR", "period": 14, "name": "atr"},
      {"type": "BollingerBands", "period": 20, "std": 2, "name": "bb"}
    ]
  }
}
```

**Generated Code:**
```python
# Set start and end dates
self.SetStartDate(2020, 1, 1)  # COVID period
self.SetEndDate(2021, 12, 31)
```

### **Example 3: Last 5 Years Strategy**
```json
{
  "description": "Trade EUR/USD using Ichimoku cloud on 4-hour timeframe for the last 5 years",
  "strategy": {
    "symbols": ["EURUSD"],
    "timeframe": "4h",
    "indicators": [
      {"type": "IchimokuKinkoHyo", "tenkan": 9, "kijun": 26, "senkou_b": 52, "name": "ichimoku"}
    ]
  }
}
```

**Generated Code:**
```python
# Set start and end dates
self.SetStartDate(2019, 1, 1)  # Last 5 years
self.SetEndDate(2024, 1, 1)
```

### **Example 4: Year-to-Date Strategy**
```json
{
  "description": "Trade Bitcoin using VWAP and RSI on 15-minute timeframe year to date",
  "strategy": {
    "symbols": ["BTCUSD"],
    "timeframe": "15m",
    "indicators": [
      {"type": "VWAP", "name": "vwap"},
      {"type": "RSI", "period": 14, "name": "rsi"}
    ]
  }
}
```

**Generated Code:**
```python
# Set start and end dates
self.SetStartDate(2024, 1, 1)  # Year to date
self.SetEndDate(2024, 12, 31)
```

### **Example 5: Financial Crisis Strategy**
```json
{
  "description": "Trade VIX using mean reversion during the financial crisis",
  "strategy": {
    "symbols": ["VIX"],
    "timeframe": "1d",
    "indicators": [
      {"type": "SMA", "period": 20, "name": "sma"},
      {"type": "ATR", "period": 14, "name": "atr"}
    ]
  }
}
```

**Generated Code:**
```python
# Set start and end dates
self.SetStartDate(2007, 1, 1)  # Financial crisis
self.SetEndDate(2009, 12, 31)
```

### **Example 6: Last 3 Months Strategy**
```json
{
  "description": "Scalp ES futures using order flow and volume profile for the last 3 months",
  "strategy": {
    "symbols": ["ES"],
    "timeframe": "1m",
    "indicators": [
      {"type": "OrderFlow", "name": "order_flow"},
      {"type": "VolumeProfile", "name": "volume_profile"}
    ]
  }
}
```

**Generated Code:**
```python
# Set start and end dates
self.SetStartDate(2023, 10, 1)  # Last 3 months
self.SetEndDate(2024, 1, 1)
```

### **Example 7: Bull Market Strategy**
```json
{
  "description": "Trade QQQ using momentum indicators during the bull market",
  "strategy": {
    "symbols": ["QQQ"],
    "timeframe": "1d",
    "indicators": [
      {"type": "MACD", "fast": 12, "slow": 26, "signal": 9, "name": "macd"},
      {"type": "Momentum", "period": 10, "name": "momentum"}
    ]
  }
}
```

**Generated Code:**
```python
# Set start and end dates
self.SetStartDate(2009, 3, 1)  # Bull market
self.SetEndDate(2020, 2, 29)
```

### **Example 8: All Time Strategy**
```json
{
  "description": "Trade SPY using buy and hold strategy for all available data",
  "strategy": {
    "symbols": ["SPY"],
    "timeframe": "1d",
    "indicators": []
  }
}
```

**Generated Code:**
```python
# Set start and end dates
self.SetStartDate(2000, 1, 1)  # All time
self.SetEndDate(2024, 12, 31)
```

## 🔧 **Advanced Features**

### **Automatic Date Calculation**
The system automatically calculates the correct start and end dates based on the current date and the specified period.

### **Special Period Handling**
- **Year-to-Date**: Automatically calculates from January 1st of current year
- **Month-to-Date**: Automatically calculates from 1st of current month
- **Quarter-to-Date**: Automatically calculates from start of current quarter
- **Market Cycles**: Uses predefined historical periods
- **Crisis Periods**: Uses specific crisis start/end dates

### **Flexible Period Specification**
Users can specify periods in multiple ways:
- `"last year"` = `"past year"` = `"recent year"`
- `"last 3 months"` = `"past 3 months"` = `"recent 3 months"`
- `"last 5 years"` = `"past 5 years"` = `"recent 5 years"`

### **Default Period**
If no period is specified, the system defaults to **3 years** of backtest data.

## 🎨 **Natural Language Examples**

### **Forex Examples**
- `"Trade EUR/USD for the last year using RSI"`
- `"Backtest GBP/USD strategy for the past 5 years"`
- `"Test USD/JPY during the COVID period"`

### **Futures Examples**
- `"Scalp ES futures for the last 3 months"`
- `"Trade Gold during the financial crisis"`
- `"Test Crude Oil strategy year to date"`

### **Crypto Examples**
- `"Trade Bitcoin for the last 2 years"`
- `"Test Ethereum strategy during 2021"`
- `"Backtest crypto portfolio for the bull market"`

### **Equity Examples**
- `"Trade SPY for the last decade"`
- `"Test AAPL strategy for the past 3 years"`
- `"Backtest QQQ during the dot com bubble"`

### **Complex Examples**
- `"Multi-timeframe strategy for the last 5 years"`
- `"Pairs trading during the COVID recovery"`
- `"Volatility trading for the entire 2020s decade"`
- `"Options strategy year to date"`
- `"Portfolio rebalancing for the last 2 quarters"`

## 🚀 **System Capabilities**

The system now supports:

✅ **100+ Backtest Periods** (Years, months, quarters, weeks, days)
✅ **Special Periods** (YTD, MTD, QTD)
✅ **Market Cycles** (Bull/bear markets, crisis periods)
✅ **Specific Years** (2020, 2021, 2022, 2023, 2024, etc.)
✅ **Decades** (2010s, 2020s)
✅ **Maximum Periods** (All time, full history)
✅ **Automatic Date Calculation** (Based on current date)
✅ **Flexible Language** (Multiple ways to specify same period)
✅ **Default Periods** (3 years if not specified)

## 🎯 **Ready for Production**

Users can now specify **ANY** backtest period using natural language, from 1 day to 20+ years, including special market periods and crisis events. The system automatically calculates the correct start and end dates and generates the appropriate QuantConnect code.

**The frontend can now handle ANY backtest period request!** 🚀

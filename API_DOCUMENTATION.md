# TradingLab API Documentation

## Overview
This document describes the REST API endpoints for the TradingLab strategy creation and backtesting platform.

## Base URL
- Development: `http://localhost:8000`
- Production: `https://tradelab-39583a78c028.herokuapp.com`

## Authentication
All API endpoints require JWT authentication. Include the token in the Authorization header:
```
Authorization: Bearer YOUR_JWT_TOKEN
```

## Strategy Creation API

### Create Strategy
**POST** `/api/strategies/`

Creates a new trading strategy with validation.

#### Request Body
```json
{
  "name": "string",
  "description": "string",
  "symbol": "string",  // Must be from supported symbols
  "timeframe": "string",  // Must be from supported timeframes
  "entry_rules": [
    {
      "name": "string",
      "rule_type": "condition|action|filter",
      "action_type": "buy|sell|close|modify|wait",  // Required for action rules
      "conditions": [
        {
          "left_operand": "string",  // Must be from supported indicators
          "operator": "gt|lt|gte|lte|eq|ne|cross_up|cross_down",
          "right_operand": "string",
          "logical_operator": "and|or"
        }
      ],
      "priority": 1,
      "parameters": {}
    }
  ],
  "exit_rules": [
    {
      "name": "string",
      "rule_type": "condition|action|filter",
      "action_type": "buy|sell|close|modify|wait",
      "conditions": [
        {
          "left_operand": "string",
          "operator": "gt|lt|gte|lte|eq|ne|cross_up|cross_down",
          "right_operand": "string",
          "logical_operator": "and|or"
        }
      ],
      "priority": 1,
      "parameters": {}
    }
  ],
  "stop_loss_type": "percentage|points|ticks|atr",
  "stop_loss_value": 1.0,
  "take_profit_type": "percentage|points|ticks|atr",
  "take_profit_value": 2.0,
  "initial_capital": 10000,
  "status": "DRAFT|READY|ACTIVE|INACTIVE"
}
```

#### Response
**201 Created**
```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "symbol": "string",
  "timeframe": "string",
  "entry_rules": [...],
  "exit_rules": [...],
  "stop_loss_type": "string",
  "stop_loss_value": 1.0,
  "take_profit_type": "string",
  "take_profit_value": 2.0,
  "initial_capital": 10000,
  "status": "DRAFT",
  "is_active": true,
  "is_public": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

**400 Bad Request**
```json
{
  "field_name": ["Error message"],
  "entry_rules": ["At least one entry rule is required"]
}
```

### Get Supported Enums
**GET** `/api/strategies/enums/`

Returns all supported values for strategy creation.

#### Response
**200 OK**
```json
{
  "symbols": ["ES", "NQ", "YM", "RTY", "GC", "SI", "CL", "NG", "EURUSD", "GBPUSD", "USDJPY", "USDCHF", "AUDUSD", "USDCAD", "NZDUSD", "BTC", "ETH", "LTC", "XRP", "ADA", "DOT", "SPY", "QQQ", "IWM", "DIA", "VIX", "ARKK", "TQQQ", "SQQQ", "AAPL", "MSFT", "GOOGL", "AMZN", "TSLA", "META", "NVDA"],
  "timeframes": ["1m", "2m", "3m", "4m", "5m", "6m", "7m", "8m", "9m", "10m", "12m", "15m", "20m", "30m", "45m", "1h", "2h", "3h", "4h", "6h", "8h", "12h", "1d", "2d", "3d", "1w", "2w", "1M", "3M", "1Y"],
  "indicators": ["sma_20", "sma_50", "sma_200", "ema_20", "ema_50", "ema_200", "vwap", "rsi", "rsi_20", "rsi_30", "rsi_50", "rsi_70", "rsi_80", "macd", "macd_signal", "macd_histogram", "stochastic_k", "stochastic_d", "atr", "bb_upper", "bb_middle", "bb_lower", "open", "high", "low", "close", "volume"],
  "operators": ["gt", "lt", "gte", "lte", "eq", "ne", "cross_up", "cross_down"],
  "stop_loss_types": ["percentage", "points", "ticks", "atr"],
  "take_profit_types": ["percentage", "points", "ticks", "atr"],
  "strategy_status": ["DRAFT", "READY", "ACTIVE", "INACTIVE"],
  "rule_types": ["condition", "action", "filter"],
  "action_types": ["buy", "sell", "close", "modify", "wait"],
  "logical_operators": ["and", "or"]
}
```

## Backtesting API

### Run Backtest (Full)
**POST** `/api/strategies/{id}/backtest/`

Runs a complete backtest with detailed results.

#### Request Body
```json
{
  "start_date": "2020-01-01T00:00:00Z",
  "end_date": "2024-12-31T23:59:59Z",
  "initial_capital": 10000,  // Optional, uses strategy default if not provided
  "commission": 4.00,
  "slippage": 0.5
}
```

#### Response
**201 Created**
```json
{
  "strategy": {
    "id": 1,
    "name": "string",
    "symbol": "string",
    "timeframe": "string",
    // ... full strategy object
  },
  "settings": {
    "start_date": "2020-01-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z",
    "initial_capital": 10000,
    "commission": 4.00,
    "slippage": 0.5
  },
  "trades": [
    {
      "id": 1,
      "action": "buy",
      "entry_price": 4500.0,
      "exit_price": 4510.0,
      "entry_date": "2020-01-01T09:30:00Z",
      "exit_date": "2020-01-01T10:30:00Z",
      "quantity": 1,
      "pnl": 10.0,
      "commission": 4.0,
      "slippage": 0.5,
      "net_pnl": 5.5,
      "reason": "Take Profit",
      "duration": 3600000
    }
  ],
  "performance": {
    "total_return": 1500.0,
    "total_return_percent": 15.0,
    "sharpe_ratio": 1.25,
    "max_drawdown": -500.0,
    "max_drawdown_percent": -5.0,
    "win_rate": 0.65,
    "profit_factor": 1.8,
    "total_trades": 100,
    "winning_trades": 65,
    "losing_trades": 35,
    "avg_win": 25.0,
    "avg_loss": -15.0,
    "largest_win": 100.0,
    "largest_loss": -50.0
  },
  "summary": {
    "rating": "Good",
    "color": "#00d4aa",
    "description": "Strategy shows consistent profitability with good risk management"
  },
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### Run Backtest (Simple)
**POST** `/api/strategies/{id}/run_backtest/`

Runs a backtest with simplified parameters and response.

#### Request Body
```json
{
  "start_date": "2020-01-01T00:00:00Z",  // Optional
  "end_date": "2024-12-31T23:59:59Z",    // Optional
  "initial_capital": 10000,              // Optional
  "commission": 4.00,                    // Optional
  "slippage": 0.5                        // Optional
}
```

#### Response
**201 Created**
```json
{
  "success": true,
  "backtest_id": 123,
  "message": "Backtest completed successfully",
  "performance": {
    "total_return": 1500.0,
    "total_return_percent": 15.0,
    "sharpe_ratio": 1.25,
    "max_drawdown": -500.0,
    "max_drawdown_percent": -5.0,
    "win_rate": 0.65,
    "profit_factor": 1.8,
    "total_trades": 100,
    "winning_trades": 65,
    "losing_trades": 35
  }
}
```

**422 Unprocessable Entity**
```json
{
  "error": "Strategy must be in READY status to run backtest. Current status: DRAFT"
}
```

## Strategy Management API

### Get All Strategies
**GET** `/api/strategies/`

Returns paginated list of user's strategies.

#### Query Parameters
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 20, max: 100)

#### Response
**200 OK**
```json
{
  "count": 25,
  "next": "http://localhost:8000/api/strategies/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "name": "string",
      "description": "string",
      "symbol": "string",
      "timeframe": "string",
      "status": "DRAFT",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z",
      "win_rate": 65.0,
      "total_trades": 100,
      "profit_factor": 1.8,
      "max_drawdown": -5.0,
      "sharpe_ratio": 1.25,
      "total_return": 1500.0,
      "total_return_percent": 15.0,
      "rating": "Good",
      "rating_color": "#00d4aa"
    }
  ]
}
```

### Get Strategy Details
**GET** `/api/strategies/{id}/`

Returns detailed information about a specific strategy.

#### Response
**200 OK**
```json
{
  "id": 1,
  "name": "string",
  "description": "string",
  "symbol": "string",
  "timeframe": "string",
  "entry_rules": [...],
  "exit_rules": [...],
  "stop_loss_type": "percentage",
  "stop_loss_value": 1.0,
  "take_profit_type": "percentage",
  "take_profit_value": 2.0,
  "initial_capital": 10000,
  "status": "READY",
  "is_active": true,
  "is_public": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z",
  "backtests": [...],
  "backtest_count": 5,
  "latest_backtest": {...}
}
```

### Update Strategy
**PUT** `/api/strategies/{id}/`

Updates an existing strategy.

#### Request Body
Same as create strategy, but all fields are optional.

#### Response
**200 OK**
```json
{
  "id": 1,
  "name": "Updated Strategy Name",
  // ... updated strategy object
}
```

### Delete Strategy
**DELETE** `/api/strategies/{id}/`

Deletes a strategy.

#### Response
**204 No Content**

## Error Responses

### 400 Bad Request
```json
{
  "field_name": ["Error message"],
  "non_field_errors": ["General error message"]
}
```

### 401 Unauthorized
```json
{
  "detail": "Authentication credentials were not provided."
}
```

### 403 Forbidden
```json
{
  "detail": "You do not have permission to perform this action."
}
```

### 404 Not Found
```json
{
  "detail": "Not found."
}
```

### 422 Unprocessable Entity
```json
{
  "error": "Strategy must be in READY status to run backtest. Current status: DRAFT"
}
```

### 500 Internal Server Error
```json
{
  "error": "Backtest failed: Error message"
}
```

## Rate Limiting
- Strategy creation: 10 requests per minute
- Backtest execution: 5 requests per minute
- General API: 100 requests per minute

## Pagination
All list endpoints support pagination with the following parameters:
- `page`: Page number (1-based)
- `page_size`: Number of items per page (max 100)

Response includes:
- `count`: Total number of items
- `next`: URL for next page (null if last page)
- `previous`: URL for previous page (null if first page)
- `results`: Array of items for current page

## Examples

### Create a Simple RSI Strategy
```bash
curl -X POST http://localhost:8000/api/strategies/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "name": "RSI Mean Reversion",
    "description": "Buy when RSI is oversold, sell when overbought",
    "symbol": "ES",
    "timeframe": "5m",
    "entry_rules": [
      {
        "name": "RSI Oversold Entry",
        "rule_type": "condition",
        "action_type": "buy",
        "conditions": [
          {
            "left_operand": "rsi",
            "operator": "lt",
            "right_operand": "rsi_30",
            "logical_operator": "and"
          }
        ],
        "priority": 1,
        "parameters": {}
      }
    ],
    "exit_rules": [
      {
        "name": "RSI Overbought Exit",
        "rule_type": "condition",
        "action_type": "sell",
        "conditions": [
          {
            "left_operand": "rsi",
            "operator": "gt",
            "right_operand": "rsi_70",
            "logical_operator": "and"
          }
        ],
        "priority": 1,
        "parameters": {}
      }
    ],
    "stop_loss_type": "percentage",
    "stop_loss_value": 1.0,
    "take_profit_type": "percentage",
    "take_profit_value": 2.0,
    "initial_capital": 10000,
    "status": "DRAFT"
  }'
```

### Run a Backtest
```bash
curl -X POST http://localhost:8000/api/strategies/1/run_backtest/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "start_date": "2020-01-01T00:00:00Z",
    "end_date": "2024-12-31T23:59:59Z"
  }'
```

## Changelog

### Version 1.1.0 (Current)
- Added strategy status field (DRAFT, READY, ACTIVE, INACTIVE)
- Added comprehensive validation for all fields
- Added enums endpoint for supported values
- Added simplified backtest endpoint
- Improved error messages and validation
- Added natural language strategy support

### Version 1.0.0
- Initial API release
- Basic strategy creation and management
- Backtest execution
- User authentication

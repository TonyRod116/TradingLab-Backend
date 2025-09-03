# Trading Strategy Rule Builder

A comprehensive system for creating, managing, and executing automated trading strategies using a visual rule builder.

## Features

- **Visual Rule Builder**: Create complex trading strategies using an intuitive interface
- **Technical Indicators**: Support for SMA, EMA, RSI, MACD, Bollinger Bands, and more
- **Strategy Templates**: Pre-built strategies to get started quickly
- **Backtesting Engine**: Test strategies against historical data
- **Real-time Execution**: Execute strategies in live markets
- **Performance Analytics**: Track win rate, profit factor, and drawdown

## Architecture

### Backend (Django)
- **Models**: Strategy, StrategyRule, StrategyExecution
- **Services**: Rule engine, backtesting, execution engine
- **API**: RESTful endpoints for all operations
- **Authentication**: JWT-based security

### Frontend (React)
- **Strategy Manager**: Create and manage strategies
- **Rule Builder**: Visual interface for building rules
- **Dashboard**: Monitor strategy performance
- **Responsive Design**: Works on all devices

## Quick Start

### 1. Backend Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py makemigrations
python manage.py migrate

# Start server
python manage.py runserver
```

### 2. Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm start
```

### 3. Create Your First Strategy

1. Open the Strategy Manager
2. Click "Create New Strategy"
3. Fill in basic information (name, symbol, timeframe)
4. Click "Edit Rules" to open the Rule Builder
5. Add conditions and actions
6. Save and test your strategy

## API Endpoints

### Strategies
- `GET /api/strategies/strategies/` - List strategies
- `POST /api/strategies/strategies/` - Create strategy
- `GET /api/strategies/strategies/{id}/` - Get strategy details
- `PUT /api/strategies/strategies/{id}/` - Update strategy
- `DELETE /api/strategies/strategies/{id}/` - Delete strategy

### Rules
- `GET /api/strategies/strategies/{id}/rules/` - List rules
- `POST /api/strategies/strategies/{id}/rules/` - Create rule
- `PUT /api/strategies/strategies/{id}/rules/{rule_id}/` - Update rule
- `DELETE /api/strategies/strategies/{id}/rules/{rule_id}/` - Delete rule

### Rule Builder
- `GET /api/strategies/strategies/{id}/rule-builder/` - Available indicators
- `GET /api/strategies/strategies/{id}/rule-builder/operators/` - Available operators
- `GET /api/strategies/strategies/{id}/rule-builder/actions/` - Available actions
- `POST /api/strategies/strategies/{id}/rule-builder/test/` - Test rule

### Backtesting
- `POST /api/strategies/strategies/{id}/backtest/run/` - Run backtest
- `GET /api/strategies/strategies/{id}/backtest/history/` - Backtest history

## Rule Types

### 1. Condition Rules
Evaluate market conditions:
```json
{
  "name": "RSI Oversold",
  "rule_type": "condition",
  "condition_type": "indicator",
  "left_operand": "rsi",
  "operator": "lt",
  "right_operand": "30"
}
```

### 2. Action Rules
Execute trading actions:
```json
{
  "name": "Buy Signal",
  "rule_type": "action",
  "action_type": "buy",
  "parameters": {
    "position_size": "1.00",
    "stop_loss": "50",
    "take_profit": "100"
  }
}
```

## Risk Management Options

The system supports multiple risk management methods for stop loss and take profit:

### Stop Loss & Take Profit Types
- **Percentage**: Risk as percentage of entry price (e.g., 0.5% = 0.5)
- **Points**: Risk in price points (e.g., 2.0 points)
- **Ticks**: Risk in ticks (1 tick = 0.25 points for futures, e.g., 8 ticks = 2.0 points)
- **ATR**: Risk based on Average True Range multiplier (e.g., 2.0 ATR)

### Example Risk Configurations
```json
{
  "stop_loss_type": "ticks",
  "stop_loss_value": "8",
  "take_profit_type": "atr", 
  "take_profit_value": "2.0"
}
```

### 3. Filter Rules
Modify or cancel actions:
```json
{
  "name": "Volume Filter",
  "rule_type": "filter",
  "condition_type": "volume",
  "left_operand": "volume",
  "operator": "gt",
  "right_operand": "avg_volume_20"
}
```

## Available Indicators

### Trend Indicators
- **SMA**: Simple Moving Average
- **EMA**: Exponential Moving Average
- **VWAP**: Volume Weighted Average Price

### Momentum Indicators
- **RSI**: Relative Strength Index
- **MACD**: Moving Average Convergence Divergence
- **Stochastic**: Stochastic Oscillator

### Volatility Indicators
- **ATR**: Average True Range
- **Bollinger Bands**: Upper, Middle, Lower bands

### Price Action
- **Open/High/Low/Close**: OHLC prices
- **Volume**: Trading volume

## Available Operators

- `gt`: Greater than (>)
- `gte`: Greater than or equal (>=)
- `lt`: Less than (<)
- `lte`: Less than or equal (<=)
- `eq`: Equal (==)
- `ne`: Not equal (!=)
- `crosses_above`: Crosses above
- `crosses_below`: Crosses below
- `above`: Above
- `below`: Below

## Available Actions

- `buy`: Open long position
- `sell`: Open short position
- `close`: Close position
- `modify`: Modify position parameters
- `wait`: Wait for next signal

## Strategy Examples

### Moving Average Crossover
```json
{
  "name": "MA Crossover",
  "rules": [
    {
      "name": "SMA 20 > SMA 50",
      "rule_type": "condition",
      "left_operand": "sma_20",
      "operator": "gt",
      "right_operand": "sma_50"
    },
    {
      "name": "Buy Signal",
      "rule_type": "action",
      "action_type": "buy"
    }
  ]
}
```

### RSI Mean Reversion
```json
{
  "name": "RSI Mean Reversion",
  "rules": [
    {
      "name": "RSI < 30",
      "rule_type": "condition",
      "left_operand": "rsi",
      "operator": "lt",
      "right_operand": "30"
    },
    {
      "name": "Buy Signal",
      "rule_type": "action",
      "action_type": "buy"
    }
  ]
}
```

### Breakout Strategy
```json
{
  "name": "Breakout Strategy",
  "rules": [
    {
      "name": "Price > High 20",
      "rule_type": "condition",
      "left_operand": "close_price",
      "operator": "gt",
      "right_operand": "high_20"
    },
    {
      "name": "Volume > Avg Volume",
      "rule_type": "condition",
      "left_operand": "volume",
      "operator": "gt",
      "right_operand": "avg_volume_20"
    },
    {
      "name": "Buy Signal",
      "rule_type": "action",
      "action_type": "buy"
    }
  ]
}
```

## Frontend Components

### StrategyManager
Main component for managing strategies:
- Create new strategies
- Use templates
- Manage existing strategies
- Run backtests

### StrategyRuleBuilder
Visual interface for building rules:
- Drag and drop rule creation
- Real-time validation
- Rule testing
- Priority management

## Styling

The system includes comprehensive CSS styling:
- Responsive design
- Modern UI components
- Consistent color scheme
- Mobile-friendly interface

## Development

### Adding New Indicators
1. Extend the `BaseIndicator` class
2. Add to `TechnicalAnalysisService`
3. Update the API endpoints
4. Add to frontend indicator list

### Adding New Actions
1. Extend the `ACTION_TYPES` in models
2. Update the execution engine
3. Add to frontend action list

### Custom Rule Types
1. Extend the `RULE_TYPES` in models
2. Update the rule engine
3. Add validation logic
4. Update frontend components

## Testing

### Backend Tests
```bash
python manage.py test strategies
python manage.py test indicators
python manage.py test backtests
```

### Frontend Tests
```bash
npm test
npm run test:coverage
```

## Deployment

### Production Settings
1. Set `DEBUG = False`
2. Configure database
3. Set up static files
4. Configure CORS
5. Set up SSL

### Docker
```bash
docker build -t strategy-builder .
docker run -p 8000:8000 strategy-builder
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the examples

## Roadmap

- [ ] Machine learning integration
- [ ] Advanced backtesting features
- [ ] Real-time market data
- [ ] Portfolio management
- [ ] Risk management tools
- [ ] Social trading features
- [ ] Mobile app
- [ ] API rate limiting
- [ ] WebSocket support
- [ ] Multi-currency support

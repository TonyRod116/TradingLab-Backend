# Manual QA Script - Strategy Creation Flow

## Overview
This script provides step-by-step instructions to manually test the strategy creation flow in TradingLab.

## Prerequisites
- Frontend running on http://localhost:5173
- Backend running on http://localhost:8000 (or deployed URL)
- User account created and logged in

## Test Cases

### 1. Visual Builder Strategy Creation

#### Test Steps:
1. **Navigate to Strategies Page**
   - Go to http://localhost:5173/strategies
   - Verify you're logged in
   - Click on "Create Strategy" tab

2. **Fill Basic Information**
   - Strategy Name: "Test RSI Strategy"
   - Description: "RSI mean reversion strategy for testing"
   - Timeframe: Select "5m"
   - Click "Next"

3. **Configure Risk Management**
   - Initial Capital: 10000
   - Position Size: 1
   - Stop Loss: 1% (percentage)
   - Take Profit: 2% (percentage)
   - Commission: 4.00
   - Slippage: 0.5
   - Click "Next"

4. **Create Entry Rules**
   - Click "Add Entry Rule"
   - Rule Name: "RSI Oversold Entry"
   - Rule Type: Condition
   - Left Operand: RSI
   - Operator: Less than
   - Right Operand: RSI 30
   - Click "Add Rule"
   - Click "Next"

5. **Create Exit Rules**
   - Click "Add Exit Rule"
   - Rule Name: "RSI Overbought Exit"
   - Rule Type: Condition
   - Left Operand: RSI
   - Operator: Greater than
   - Right Operand: RSI 70
   - Click "Add Rule"
   - Click "Next"

6. **Review and Run Backtest**
   - Verify all information is correct
   - Click "Backtest"
   - Wait for backtest to complete
   - Verify results are displayed

#### Expected Results:
- ✅ Strategy is created successfully
- ✅ Backtest runs without errors
- ✅ Results show performance metrics
- ✅ Strategy appears in "My Strategies" list

### 2. Natural Language Strategy Creation

#### Test Steps:
1. **Navigate to Natural Language Tab**
   - Go to http://localhost:5173/strategies
   - Click on "Natural Language" tab

2. **Enter Strategy Description**
   - Use example: "Buy EURUSD on H4 when price crosses above SMA(20) and RSI(14) < 30. SL 1%, TP 2%, capital 10k."
   - Click "Parse Strategy"

3. **Review Parsed Strategy**
   - Verify symbol is detected as "EURUSD"
   - Verify timeframe is detected as "4h"
   - Verify capital is detected as 10000
   - Verify stop loss is 1%
   - Verify take profit is 2%
   - Click "Create Strategy"

4. **Run Backtest**
   - Strategy should be created and backtest should start
   - Wait for completion
   - Verify results

#### Expected Results:
- ✅ Natural language is parsed correctly
- ✅ Strategy is created with correct parameters
- ✅ Backtest runs successfully
- ✅ Results are displayed

### 3. Strategy Status Validation

#### Test Steps:
1. **Create Strategy in DRAFT Status**
   - Create a strategy but don't run backtest
   - Check strategy status in database or API

2. **Try to Run Backtest on DRAFT Strategy**
   - Attempt to run backtest on DRAFT strategy
   - Should get validation error

3. **Update Strategy to READY Status**
   - Update strategy status to READY
   - Run backtest
   - Should succeed

#### Expected Results:
- ✅ DRAFT strategies cannot run backtests
- ✅ READY strategies can run backtests
- ✅ Proper error messages are shown

### 4. API Endpoint Testing

#### Test Steps:
1. **Test Strategy Creation API**
   ```bash
   curl -X POST http://localhost:8000/api/strategies/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{
       "name": "API Test Strategy",
       "description": "Strategy created via API",
       "symbol": "ES",
       "timeframe": "1m",
       "entry_rules": [...],
       "exit_rules": [...],
       "stop_loss_type": "percentage",
       "stop_loss_value": 1.0,
       "take_profit_type": "percentage",
       "take_profit_value": 2.0,
       "initial_capital": 10000,
       "status": "DRAFT"
     }'
   ```

2. **Test Enums Endpoint**
   ```bash
   curl http://localhost:8000/api/strategies/enums/
   ```

3. **Test Run Backtest API**
   ```bash
   curl -X POST http://localhost:8000/api/strategies/1/run_backtest/ \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -d '{}'
   ```

#### Expected Results:
- ✅ Strategy creation returns 201 with strategy data
- ✅ Enums endpoint returns all supported values
- ✅ Run backtest returns performance metrics

### 5. Error Handling Testing

#### Test Steps:
1. **Test Invalid Symbol**
   - Try to create strategy with unsupported symbol
   - Should get validation error

2. **Test Invalid Timeframe**
   - Try to create strategy with unsupported timeframe
   - Should get validation error

3. **Test Missing Required Fields**
   - Try to create strategy without name
   - Should get validation error

4. **Test Invalid Rule Format**
   - Try to create strategy with malformed rules
   - Should get validation error

#### Expected Results:
- ✅ Proper validation errors are returned
- ✅ Error messages are clear and helpful
- ✅ Frontend displays errors appropriately

## Database Verification

### Check Strategy Table
```sql
SELECT id, name, symbol, timeframe, status, created_at 
FROM strategies 
ORDER BY created_at DESC 
LIMIT 10;
```

### Check Backtest Results
```sql
SELECT s.name, br.total_return_percent, br.win_rate, br.total_trades
FROM strategies s
JOIN backtest_results br ON s.id = br.strategy_id
ORDER BY br.created_at DESC
LIMIT 10;
```

## Performance Testing

### Test Large Strategy Creation
1. Create strategy with 10+ entry rules
2. Create strategy with 10+ exit rules
3. Verify performance is acceptable

### Test Concurrent Backtests
1. Start multiple backtests simultaneously
2. Verify all complete successfully
3. Check for any race conditions

## Browser Compatibility

### Test on Different Browsers
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)

### Test on Different Devices
- Desktop (1920x1080)
- Tablet (768x1024)
- Mobile (375x667)

## Security Testing

### Test Authentication
1. Try to create strategy without authentication
2. Try to access other user's strategies
3. Verify proper 401/403 responses

### Test Input Validation
1. Try SQL injection in strategy name
2. Try XSS in strategy description
3. Verify inputs are properly sanitized

## Rollback Plan

If issues are found:

1. **Frontend Rollback**
   ```bash
   cd /home/tonirod/code/ga/projects/TradingLab/trading-lab
   git checkout main
   npm run build
   ```

2. **Backend Rollback**
   ```bash
   cd /home/tonirod/code/ga/projects/TradingLab-Backend-Clean
   git checkout main
   python manage.py migrate strategies 0017  # Rollback to previous migration
   ```

3. **Database Rollback**
   ```sql
   ALTER TABLE strategies DROP COLUMN status;
   ```

## Success Criteria

- ✅ All test cases pass
- ✅ No console errors in browser
- ✅ No server errors in logs
- ✅ Performance is acceptable (< 5s for backtest)
- ✅ UI is responsive and user-friendly
- ✅ Error messages are clear and helpful

## Reporting

After completing all tests, document:
- Test results for each case
- Any bugs found with steps to reproduce
- Performance metrics
- Browser compatibility issues
- Recommendations for improvements

"""
Backtest views for preview and batch operations
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.utils.dateparse import parse_datetime
from decimal import Decimal
import logging

from .backtest_engine import BacktestEngine
from .models import Strategy

logger = logging.getLogger(__name__)


class BacktestPreviewView(APIView):
    """
    Preview backtest without persisting to database
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Run backtest preview with strategy configuration
        
        Body:
        {
            "name": "Strategy Name",
            "description": "Strategy Description", 
            "symbol": "ES",
            "timeframe": "5m",
            "initial_capital": 100000,
            "entry_rules": [...],
            "exit_rules": [...],
            "stop_loss_type": "points",
            "stop_loss_value": 2.0,
            "take_profit_type": "points", 
            "take_profit_value": 4.0,
            "start_date": "2020-01-01T00:00:00Z",
            "end_date": "2024-12-31T23:59:59Z",
            "commission": 4.00,
            "slippage": 0.25  // in points (0.25 = 1 tick)
        }
        """
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['symbol', 'timeframe', 'entry_rules', 'start_date', 'end_date']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Create strategy object in memory (not persisted)
            strategy = Strategy(
                user=request.user,
                name=data.get('name', 'Preview Strategy'),
                description=data.get('description', ''),
                symbol=data['symbol'],
                timeframe=data['timeframe'],
                initial_capital=Decimal(str(data.get('initial_capital', 100000))),
                entry_rules=data['entry_rules'],
                exit_rules=data.get('exit_rules', []),
                stop_loss_type=data.get('stop_loss_type', 'points'),
                stop_loss_value=Decimal(str(data.get('stop_loss_value', 2.0))),
                take_profit_type=data.get('take_profit_type', 'points'),
                take_profit_value=Decimal(str(data.get('take_profit_value', 4.0))),
                status='READY'
            )
            
            # Parse dates
            start_date = parse_datetime(data['start_date'])
            end_date = parse_datetime(data['end_date'])
            
            if not start_date or not end_date:
                return Response(
                    {'error': 'Invalid date format. Use ISO format: YYYY-MM-DDTHH:MM:SSZ'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert slippage from ticks to points if needed
            slippage = Decimal(str(data.get('slippage', 0.25)))
            # If slippage looks like ticks (integer or small decimal), convert to points
            if slippage <= 1.0 and slippage > 0:
                slippage = slippage * Decimal('0.25')  # Convert ticks to points
            
            # Run backtest computation
            engine = BacktestEngine()
            trades, performance, equity_points = engine.compute_backtest(
                strategy=strategy,
                start_date=start_date,
                end_date=end_date,
                initial_capital=strategy.initial_capital,
                commission=Decimal(str(data.get('commission', 4.00))),
                slippage=slippage,
                chunk_size=data.get('chunk_size', 10000)
            )
            
            # Return results without persisting
            return Response({
                'performance': performance,
                'trades': trades,
                'equity_curve': equity_points,
                'settings': {
                    'symbol': strategy.symbol,
                    'timeframe': strategy.timeframe,
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'initial_capital': float(strategy.initial_capital),
                    'commission': float(data.get('commission', 4.00)),
                    'slippage': float(slippage),
                    'stop_loss_type': strategy.stop_loss_type,
                    'stop_loss_value': float(strategy.stop_loss_value),
                    'take_profit_type': strategy.take_profit_type,
                    'take_profit_value': float(strategy.take_profit_value)
                }
            }, status=status.HTTP_200_OK)
            
        except ValueError as e:
            # Validation errors (semantic validation, etc.)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"BacktestPreviewView error: {str(e)}")
            return Response(
                {'error': f'Backtest preview failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class BacktestBatchView(APIView):
    """
    Run multiple backtests with different parameters
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Run multiple backtest scenarios
        
        Body:
        {
            "base_config": {
                "symbol": "ES",
                "timeframe": "5m", 
                "entry_rules": [...],
                "exit_rules": [...],
                "start_date": "2020-01-01T00:00:00Z",
                "end_date": "2024-12-31T23:59:59Z"
            },
            "scenarios": [
                {
                    "name": "Conservative",
                    "slippage": 0.5,
                    "commission": 4.0,
                    "stop_loss_value": 1.0,
                    "take_profit_value": 2.0
                },
                {
                    "name": "Aggressive", 
                    "slippage": 0.25,
                    "commission": 2.0,
                    "stop_loss_value": 2.0,
                    "take_profit_value": 4.0
                }
            ]
        }
        """
        try:
            data = request.data
            base_config = data.get('base_config', {})
            scenarios = data.get('scenarios', [])
            
            if not scenarios:
                return Response(
                    {'error': 'No scenarios provided'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            results = []
            engine = BacktestEngine()
            
            for scenario in scenarios:
                try:
                    # Merge base config with scenario
                    config = {**base_config, **scenario}
                    
                    # Create strategy object
                    strategy = Strategy(
                        user=request.user,
                        name=scenario.get('name', f"Scenario {len(results) + 1}"),
                        description=scenario.get('description', ''),
                        symbol=config.get('symbol', 'ES'),
                        timeframe=config.get('timeframe', '5m'),
                        initial_capital=Decimal(str(config.get('initial_capital', 100000))),
                        entry_rules=config.get('entry_rules', []),
                        exit_rules=config.get('exit_rules', []),
                        stop_loss_type=config.get('stop_loss_type', 'points'),
                        stop_loss_value=Decimal(str(config.get('stop_loss_value', 2.0))),
                        take_profit_type=config.get('take_profit_type', 'points'),
                        take_profit_value=Decimal(str(config.get('take_profit_value', 4.0))),
                        status='READY'
                    )
                    
                    # Parse dates
                    start_date = parse_datetime(config['start_date'])
                    end_date = parse_datetime(config['end_date'])
                    
                    # Convert slippage
                    slippage = Decimal(str(config.get('slippage', 0.25)))
                    if slippage <= 1.0 and slippage > 0:
                        slippage = slippage * Decimal('0.25')
                    
                    # Run backtest
                    trades, performance, equity_points = engine.compute_backtest(
                        strategy=strategy,
                        start_date=start_date,
                        end_date=end_date,
                        initial_capital=strategy.initial_capital,
                        commission=Decimal(str(config.get('commission', 4.00))),
                        slippage=slippage
                    )
                    
                    results.append({
                        'scenario_name': scenario.get('name', f"Scenario {len(results) + 1}"),
                        'performance': performance,
                        'trades_count': len(trades),
                        'settings': {
                            'slippage': float(slippage),
                            'commission': float(config.get('commission', 4.00)),
                            'stop_loss_value': float(strategy.stop_loss_value),
                            'take_profit_value': float(strategy.take_profit_value)
                        }
                    })
                    
                except Exception as e:
                    results.append({
                        'scenario_name': scenario.get('name', f"Scenario {len(results) + 1}"),
                        'error': str(e),
                        'performance': None,
                        'trades_count': 0
                    })
            
            return Response({
                'results': results,
                'total_scenarios': len(scenarios),
                'successful_scenarios': len([r for r in results if 'error' not in r])
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"BacktestBatchView error: {str(e)}")
            return Response(
                {'error': f'Batch backtest failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )




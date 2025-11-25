"""
Views for trading strategies and backtesting
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
from decimal import Decimal
import threading
import uuid
import logging

logger = logging.getLogger(__name__)

from .models import Strategy, BacktestResult, Trade, EquityCurvePoint
from .serializers import (
    StrategySerializer, StrategyListSerializer, StrategySummarySerializer, StrategyCreateSerializer,
    BacktestResultSerializer, TradeSerializer, BacktestRequestSerializer, BacktestResponseSerializer, 
    EquityCurvePointSerializer
)
from .backtest_engine import BacktestEngine
from .enums import (
    SUPPORTED_SYMBOLS, SUPPORTED_TIMEFRAMES, SUPPORTED_INDICATORS, SUPPORTED_OPERATORS,
    STOP_LOSS_TYPES, TAKE_PROFIT_TYPES, STRATEGY_STATUS, RULE_TYPES, ACTION_TYPES, LOGICAL_OPERATORS
)


class StrategyPagination(PageNumberPagination):
    """Custom pagination for strategies"""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


class StrategyViewSet(viewsets.ModelViewSet):
    """ViewSet for trading strategies"""
    
    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StrategyPagination
    
    def get_serializer_class(self):
        """Use appropriate serializer based on action"""
        if self.action == 'list':
            return StrategyListSerializer
        elif self.action == 'create':
            return StrategyCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return StrategyCreateSerializer  # Use create serializer for updates to get normalization
        return StrategySerializer
    
    def get_queryset(self):
        """Return different querysets based on the action"""
        base_queryset = Strategy.objects.all().select_related('user')
        
        if self.action == 'list':
            queryset = base_queryset.filter(user=self.request.user).prefetch_related('backtests')
            return queryset
        
        if self.action in ['update', 'partial_update', 'destroy']:
            # Minimal queryset without heavy prefetching to avoid unnecessary conversions
            return base_queryset.filter(user=self.request.user)
        
        # For other detail actions, allow access to all strategies but prefetch related data
        queryset = base_queryset.prefetch_related(
            'backtests__trades',
            'backtests__equity_curve'
        )
        
        # Force evaluation to ensure prefetch_related works
        list(queryset)
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    def perform_update(self, serializer):
        """Ensure user can only update their own strategies"""
        strategy = self.get_object()
        if strategy.user != self.request.user:
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You can only update your own strategies")
        serializer.save()
    
    def create(self, request, *args, **kwargs):
        """Create a new strategy with detailed logging"""
        try:
            logger.info(f"🔍 StrategyViewSet.create - User: {request.user}")
            logger.info(f"🔍 StrategyViewSet.create - Data: {request.data}")
            
            serializer = self.get_serializer(data=request.data)
            logger.info(f"🔍 StrategyViewSet.create - Serializer valid: {serializer.is_valid()}")
            
            if not serializer.is_valid():
                logger.error(f"🔍 StrategyViewSet.create - Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            logger.info(f"🔍 StrategyViewSet.create - Saving strategy...")
            serializer.save(user=request.user)
            logger.info(f"🔍 StrategyViewSet.create - Strategy saved successfully: {serializer.instance.id}")
            
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"🔍 StrategyViewSet.create - Error: {str(e)}")
            logger.error(f"🔍 StrategyViewSet.create - Error type: {type(e)}")
            import traceback
            logger.error(f"🔍 StrategyViewSet.create - Traceback: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def update(self, request, *args, **kwargs):
        """Update an existing strategy with detailed logging"""
        partial = kwargs.pop('partial', False)
        try:
            strategy = self.get_object()
            logger.info(f"🔧 StrategyViewSet.update - User: {request.user}")
            logger.info(f"🔧 StrategyViewSet.update - Strategy ID: {strategy.id}")
            logger.info(f"🔧 StrategyViewSet.update - Partial: {partial}")
            logger.info(f"🔧 StrategyViewSet.update - Incoming data: {request.data}")

            if strategy.user != request.user:
                logger.warning(f"🔧 StrategyViewSet.update - Forbidden update attempt by {request.user} on strategy {strategy.id}")
                return Response({'error': 'You can only update your own strategies'}, status=status.HTTP_403_FORBIDDEN)

            serializer = self.get_serializer(strategy, data=request.data, partial=partial)
            if not serializer.is_valid():
                logger.error(f"🔧 StrategyViewSet.update - Serializer errors: {serializer.errors}")
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()
            logger.info(f"🔧 StrategyViewSet.update - Strategy updated successfully: {strategy.id}")
            return Response(serializer.data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.error(f"🔧 StrategyViewSet.update - Error: {str(e)}")
            logger.error(f"🔧 StrategyViewSet.update - Error type: {type(e)}")
            import traceback
            logger.error(f"🔧 StrategyViewSet.update - Traceback: {traceback.format_exc()}")
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True, methods=['post'])
    def backtest(self, request, pk=None):
        """
        Run backtest for a strategy (synchronous)
        
        POST /api/strategies/{id}/backtest/
        """
        logger.info(f"🔍 [BACKTEST] Starting backtest for strategy ID: {pk}")
        logger.info(f"🔍 [BACKTEST] Request data: {request.data}")
        logger.info(f"🔍 [BACKTEST] User: {request.user}")
        
        from .date_validator import BacktestDateValidator
        
        try:
            strategy = self.get_object()
            logger.info(f"🔍 [BACKTEST] Strategy retrieved: {strategy.id} - {strategy.name}")
            logger.info(f"🔍 [BACKTEST] Strategy status: {strategy.status}")
            logger.info(f"🔍 [BACKTEST] Strategy symbol: {strategy.symbol}, timeframe: {strategy.timeframe}")
        except Exception as e:
            logger.error(f"🔍 [BACKTEST] Error getting strategy: {str(e)}")
            import traceback
            logger.error(f"🔍 [BACKTEST] Traceback: {traceback.format_exc()}")
            return Response(
                {'error': f'Strategy not found: {str(e)}'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if strategy is ready for backtesting
        if strategy.status != 'READY':
            logger.warning(f"🔍 [BACKTEST] Strategy not ready. Status: {strategy.status}")
            return Response(
                {'error': f'Strategy must be in READY status to run backtest. Current status: {strategy.status}'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        # Validate request data
        logger.info(f"🔍 [BACKTEST] Validating request data...")
        serializer = BacktestRequestSerializer(data=request.data)
        if not serializer.is_valid():
            logger.error(f"🔍 [BACKTEST] Serializer validation failed: {serializer.errors}")
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        logger.info(f"🔍 [BACKTEST] Serializer validated successfully. Validated data: {serializer.validated_data}")
        
        try:
            # Allow frontend to override key strategy parameters for the backtest run
            logger.info(f"🔍 [BACKTEST] Applying parameter overrides...")
            override_fields = [
                'symbol', 'timeframe', 'stop_loss_type', 'stop_loss_value',
                'take_profit_type', 'take_profit_value'
            ]
            for field in override_fields:
                value = serializer.validated_data.get(field)
                if value is not None:
                    logger.info(f"🔍 [BACKTEST] Overriding {field}: {getattr(strategy, field, None)} -> {value}")
                    setattr(strategy, field, value)

            # Validate and adjust dates
            logger.info(f"🔍 [BACKTEST] Validating dates...")
            logger.info(f"🔍 [BACKTEST] Start date from serializer: {serializer.validated_data.get('start_date')}")
            logger.info(f"🔍 [BACKTEST] End date from serializer: {serializer.validated_data.get('end_date')}")
            validator = BacktestDateValidator()
            start_date, end_date, validation_info = validator.validate_and_adjust_dates(
                strategy.symbol,
                strategy.timeframe,
                serializer.validated_data['start_date'],
                serializer.validated_data['end_date']
            )
            logger.info(f"🔍 [BACKTEST] Validated dates - Start: {start_date}, End: {end_date}")
            logger.info(f"🔍 [BACKTEST] Validation info: {validation_info}")
            
            if not validation_info['valid']:
                return Response({
                    'error': validation_info.get('error', 'Invalid date range'),
                    'available_range': validation_info.get('available_range')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Estimate data size and warn if large
            estimation = validator.estimate_data_size(
                strategy.timeframe,
                start_date,
                end_date
            )
            
            # Return warning for large datasets (but don't block)
            warnings = []
            if validation_info.get('adjusted'):
                warnings.extend(validation_info.get('warnings', []))
            if estimation['should_warn']:
                warnings.append(f"Large dataset: ~{estimation['estimated_rows']:,} rows. Estimated time: {estimation['estimated_time']}")
            
            # Use strategy's initial capital if not provided in request
            initial_capital = serializer.validated_data.get('initial_capital')
            if initial_capital is None:
                initial_capital = strategy.initial_capital
            logger.info(f"🔍 [BACKTEST] Initial capital: {initial_capital}")
            logger.info(f"🔍 [BACKTEST] Commission: {serializer.validated_data['commission']}")
            logger.info(f"🔍 [BACKTEST] Slippage: {serializer.validated_data['slippage']}")
            
            # Run backtest with adjusted dates
            logger.info(f"🔍 [BACKTEST] Creating BacktestEngine...")
            backtest_engine = BacktestEngine()
            logger.info(f"🔍 [BACKTEST] Running backtest...")
            logger.info(f"🔍 [BACKTEST] Strategy: {strategy.id}, Symbol: {strategy.symbol}, Timeframe: {strategy.timeframe}")
            logger.info(f"🔍 [BACKTEST] Date range: {start_date} to {end_date}")
            backtest_result = backtest_engine.run_backtest(
                strategy=strategy,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital,
                commission=serializer.validated_data['commission'],
                slippage=serializer.validated_data['slippage']
            )
            logger.info(f"🔍 [BACKTEST] Backtest completed. Result ID: {backtest_result.id}")
            logger.info(f"🔍 [BACKTEST] Total return: {backtest_result.total_return}")
            logger.info(f"🔍 [BACKTEST] Total trades: {backtest_result.total_trades}")
            
            # Get trades
            logger.info(f"🔍 [BACKTEST] Fetching trades...")
            trades = backtest_result.trades.all()
            logger.info(f"🔍 [BACKTEST] Number of trades: {trades.count()}")
            
            # Calculate additional metrics from trades
            logger.info(f"🔍 [BACKTEST] Calculating metrics...")
            logger.info(f"🔍 [BACKTEST] Backtest result total_return: {backtest_result.total_return}, type: {type(backtest_result.total_return)}")
            logger.info(f"🔍 [BACKTEST] Backtest result initial_capital: {backtest_result.initial_capital}, type: {type(backtest_result.initial_capital)}")
            logger.info(f"🔍 [BACKTEST] Backtest result max_drawdown: {backtest_result.max_drawdown}, type: {type(backtest_result.max_drawdown)}")
            logger.info(f"🔍 [BACKTEST] Backtest result win_rate: {backtest_result.win_rate}, type: {type(backtest_result.win_rate)}")
            logger.info(f"🔍 [BACKTEST] Backtest result profit_factor: {backtest_result.profit_factor}, type: {type(backtest_result.profit_factor)}")
            
            try:
                total_return_percent = float((backtest_result.total_return / backtest_result.initial_capital) * 100) if backtest_result.initial_capital and backtest_result.initial_capital > 0 else 0.0
                logger.info(f"🔍 [BACKTEST] Calculated total_return_percent: {total_return_percent}")
            except Exception as e:
                logger.error(f"🔍 [BACKTEST] Error calculating total_return_percent: {str(e)}")
                total_return_percent = 0.0
            
            try:
                max_drawdown_percent = float(backtest_result.max_drawdown * 100) if backtest_result.max_drawdown is not None else 0.0
                logger.info(f"🔍 [BACKTEST] Calculated max_drawdown_percent: {max_drawdown_percent}")
            except Exception as e:
                logger.error(f"🔍 [BACKTEST] Error calculating max_drawdown_percent: {str(e)}")
                max_drawdown_percent = 0.0
            
            # Calculate win/loss statistics from trades
            logger.info(f"🔍 [BACKTEST] Processing trades for win/loss stats...")
            trades_list = list(trades)
            logger.info(f"🔍 [BACKTEST] Trades list length: {len(trades_list)}")
            
            try:
                winning_trades_list = [t for t in trades_list if t.pnl and float(t.pnl) > 0]
                losing_trades_list = [t for t in trades_list if t.pnl and float(t.pnl) < 0]
                logger.info(f"🔍 [BACKTEST] Winning trades: {len(winning_trades_list)}, Losing trades: {len(losing_trades_list)}")
                
                avg_win = float(sum(float(t.pnl) for t in winning_trades_list) / len(winning_trades_list)) if winning_trades_list else 0.0
                avg_loss = float(sum(float(t.pnl) for t in losing_trades_list) / len(losing_trades_list)) if losing_trades_list else 0.0
                largest_win = float(max((float(t.pnl) for t in winning_trades_list), default=0)) if winning_trades_list else 0.0
                largest_loss = float(min((float(t.pnl) for t in losing_trades_list), default=0)) if losing_trades_list else 0.0
                logger.info(f"🔍 [BACKTEST] Win/Loss stats - avg_win: {avg_win}, avg_loss: {avg_loss}, largest_win: {largest_win}, largest_loss: {largest_loss}")
            except Exception as e:
                logger.error(f"🔍 [BACKTEST] Error calculating win/loss stats: {str(e)}")
                import traceback
                logger.error(f"🔍 [BACKTEST] Traceback: {traceback.format_exc()}")
                avg_win = 0.0
                avg_loss = 0.0
                largest_win = 0.0
                largest_loss = 0.0
            
            # Calculate rating and color based on win_rate and profit_factor
            try:
                win_rate_float = float(backtest_result.win_rate) if backtest_result.win_rate is not None else 0.0
                profit_factor_float = float(backtest_result.profit_factor) if backtest_result.profit_factor is not None else 0.0
                logger.info(f"🔍 [BACKTEST] Win rate: {win_rate_float}, Profit factor: {profit_factor_float}")
            except Exception as e:
                logger.error(f"🔍 [BACKTEST] Error converting win_rate/profit_factor: {str(e)}")
                win_rate_float = 0.0
                profit_factor_float = 0.0
            
            if win_rate_float >= 60 and profit_factor_float >= 1.5:
                rating = "Excellent"
                rating_color = "green"
            elif win_rate_float >= 50 and profit_factor_float >= 1.2:
                rating = "Good"
                rating_color = "blue"
            elif win_rate_float >= 40 and profit_factor_float >= 1.0:
                rating = "Average"
                rating_color = "orange"
            else:
                rating = "Poor"
                rating_color = "red"
            
            # Generate summary description
            summary_description = f"Backtest completed with {backtest_result.total_trades} trades. " \
                                f"Total return: {total_return_percent:.2f}%. " \
                                f"Win rate: {win_rate_float:.1f}%. " \
                                f"Profit factor: {profit_factor_float:.2f}."
            
            logger.info(f"🔍 [BACKTEST] Rating: {rating}, Color: {rating_color}")
            
            # Prepare response
            logger.info(f"🔍 [BACKTEST] Preparing response data...")
            try:
                strategy_data = StrategySerializer(strategy).data
                logger.info(f"🔍 [BACKTEST] Strategy data serialized successfully")
            except Exception as e:
                logger.error(f"🔍 [BACKTEST] Error serializing strategy: {str(e)}")
                import traceback
                logger.error(f"🔍 [BACKTEST] Traceback: {traceback.format_exc()}")
                raise
            
            try:
                trades_data = TradeSerializer(trades, many=True).data
                logger.info(f"🔍 [BACKTEST] Trades data serialized successfully. Count: {len(trades_data)}")
            except Exception as e:
                logger.error(f"🔍 [BACKTEST] Error serializing trades: {str(e)}")
                import traceback
                logger.error(f"🔍 [BACKTEST] Traceback: {traceback.format_exc()}")
                raise
            
            try:
                performance_data = {
                    'total_return': float(backtest_result.total_return),
                    'total_return_percent': total_return_percent,
                    'sharpe_ratio': float(backtest_result.sharpe_ratio) if backtest_result.sharpe_ratio else None,
                    'max_drawdown': float(backtest_result.max_drawdown),
                    'max_drawdown_percent': max_drawdown_percent,
                    'win_rate': win_rate_float,
                    'profit_factor': profit_factor_float,
                    'total_trades': backtest_result.total_trades,
                    'winning_trades': backtest_result.winning_trades,
                    'losing_trades': backtest_result.losing_trades,
                    'avg_win': avg_win,
                    'avg_loss': avg_loss,
                    'largest_win': largest_win,
                    'largest_loss': largest_loss
                }
                logger.info(f"🔍 [BACKTEST] Performance data prepared successfully")
            except Exception as e:
                logger.error(f"🔍 [BACKTEST] Error preparing performance data: {str(e)}")
                import traceback
                logger.error(f"🔍 [BACKTEST] Traceback: {traceback.format_exc()}")
                raise
            
            response_data = {
                'strategy': strategy_data,
                'settings': serializer.validated_data,
                'trades': trades_data,
                'performance': performance_data,
                'summary': {
                    'rating': rating,
                    'color': rating_color,
                    'description': summary_description
                },
                'timestamp': backtest_result.created_at,
                'warnings': warnings if warnings else None,
                'estimation': estimation
            }
            
            logger.info(f"🔍 [BACKTEST] Response data prepared successfully. Returning response...")
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"🔍 StrategyViewSet.backtest - Error: {str(e)}")
            logger.error(f"🔍 StrategyViewSet.backtest - Error type: {type(e)}")
            import traceback
            logger.error(f"🔍 StrategyViewSet.backtest - Traceback: {traceback.format_exc()}")
            return Response(
                {'error': f'Backtest failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def run_backtest(self, request, pk=None):
        """
        Run backtest for a strategy (simplified endpoint)
        
        POST /api/strategies/{id}/run_backtest/
        """
        strategy = self.get_object()
        
        # Check if strategy is ready for backtesting
        if strategy.status != 'READY':
            return Response(
                {'error': f'Strategy must be in READY status to run backtest. Current status: {strategy.status}'},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY
            )
        
        # Default backtest parameters
        backtest_data = {
            'start_date': request.data.get('start_date', '2020-01-01T00:00:00Z'),
            'end_date': request.data.get('end_date', '2024-12-31T23:59:59Z'),
            'initial_capital': request.data.get('initial_capital', strategy.initial_capital),
            'commission': request.data.get('commission', 4.00),
            'slippage': request.data.get('slippage', 0.5)
        }
        
        # Validate request data
        serializer = BacktestRequestSerializer(data=backtest_data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Run backtest
            backtest_engine = BacktestEngine()
            backtest_result = backtest_engine.run_backtest(
                strategy=strategy,
                start_date=serializer.validated_data['start_date'],
                end_date=serializer.validated_data['end_date'],
                initial_capital=serializer.validated_data['initial_capital'],
                commission=serializer.validated_data['commission'],
                slippage=serializer.validated_data['slippage']
            )
            
            # Return simplified response
            return Response({
                'success': True,
                'backtest_id': backtest_result.id,
                'message': 'Backtest completed successfully',
                'performance': {
                    'total_return': float(backtest_result.total_return),
                    'total_return_percent': float(backtest_result.total_return_percent),
                    'sharpe_ratio': float(backtest_result.sharpe_ratio) if backtest_result.sharpe_ratio else None,
                    'max_drawdown': float(backtest_result.max_drawdown),
                    'max_drawdown_percent': float(backtest_result.max_drawdown_percent),
                    'win_rate': float(backtest_result.win_rate),
                    'profit_factor': float(backtest_result.profit_factor),
                    'total_trades': backtest_result.total_trades,
                    'winning_trades': backtest_result.winning_trades,
                    'losing_trades': backtest_result.losing_trades
                }
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Backtest failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=True, methods=['post'])
    def backtest_async(self, request, pk=None):
        """
        Run backtest for a strategy asynchronously
        
        POST /api/strategies/{id}/backtest_async/
        """
        strategy = self.get_object()
        
        # Validate request data
        serializer = BacktestRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Generate unique task ID
        task_id = str(uuid.uuid4())
        
        # Store task status in cache
        cache.set(f"backtest_task_{task_id}", {
            'status': 'pending',
            'progress': 0,
            'message': 'Starting backtest...',
            'strategy_id': strategy.id,
            'user_id': request.user.id,
            'created_at': timezone.now().isoformat()
        }, timeout=3600)  # 1 hour timeout
        
        # Start backtest in background thread
        def run_backtest():
            try:
                # Update status
                cache.set(f"backtest_task_{task_id}", {
                    'status': 'running',
                    'progress': 10,
                    'message': 'Loading market data...',
                    'strategy_id': strategy.id,
                    'user_id': request.user.id,
                    'created_at': cache.get(f"backtest_task_{task_id}")['created_at']
                }, timeout=3600)
                
                # Use strategy's initial capital if not provided in request
                initial_capital = serializer.validated_data.get('initial_capital')
                if initial_capital is None:
                    initial_capital = strategy.initial_capital

                # Apply temporary overrides for the backtest run
                override_fields = [
                    'symbol', 'timeframe', 'stop_loss_type', 'stop_loss_value',
                    'take_profit_type', 'take_profit_value'
                ]
                for field in override_fields:
                    value = serializer.validated_data.get(field)
                    if value is not None:
                        setattr(strategy, field, value)
                
                # Run backtest
                backtest_engine = BacktestEngine()
                backtest_result = backtest_engine.run_backtest(
                    strategy=strategy,
                    start_date=serializer.validated_data['start_date'],
                    end_date=serializer.validated_data['end_date'],
                    initial_capital=initial_capital,
                    commission=serializer.validated_data['commission'],
                    slippage=serializer.validated_data['slippage']
                )
                
                # Update status to completed
                cache.set(f"backtest_task_{task_id}", {
                    'status': 'completed',
                    'progress': 100,
                    'message': 'Backtest completed successfully',
                    'strategy_id': strategy.id,
                    'user_id': request.user.id,
                    'backtest_id': backtest_result.id,
                    'created_at': cache.get(f"backtest_task_{task_id}")['created_at'],
                    'completed_at': timezone.now().isoformat()
                }, timeout=3600)
                
            except Exception as e:
                # Update status to failed
                cache.set(f"backtest_task_{task_id}", {
                    'status': 'failed',
                    'progress': 0,
                    'message': f'Backtest failed: {str(e)}',
                    'strategy_id': strategy.id,
                    'user_id': request.user.id,
                    'created_at': cache.get(f"backtest_task_{task_id}")['created_at'],
                    'failed_at': timezone.now().isoformat()
                }, timeout=3600)
        
        # Start background thread
        thread = threading.Thread(target=run_backtest)
        thread.daemon = True
        thread.start()
        
        return Response({
            'task_id': task_id,
            'status': 'pending',
            'message': 'Backtest started in background'
        }, status=status.HTTP_202_ACCEPTED)

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def enums(self, request):
        """Return enum values used by the frontend strategy builder."""

        return Response({
            'symbols': SUPPORTED_SYMBOLS,
            'timeframes': SUPPORTED_TIMEFRAMES,
            'indicators': SUPPORTED_INDICATORS,
            'operators': SUPPORTED_OPERATORS,
            'stop_loss_types': STOP_LOSS_TYPES,
            'take_profit_types': TAKE_PROFIT_TYPES,
            'strategy_status': STRATEGY_STATUS,
            'rule_types': RULE_TYPES,
            'action_types': ACTION_TYPES,
            'logical_operators': LOGICAL_OPERATORS,
        })
    
    @action(detail=False, methods=['get'])
    def backtest_status(self, request):
        """
        Get backtest task status
        
        GET /api/strategies/backtest_status/?task_id=<task_id>
        """
        task_id = request.query_params.get('task_id')
        if not task_id:
            return Response({'error': 'task_id parameter required'}, status=status.HTTP_400_BAD_REQUEST)
        
        task_data = cache.get(f"backtest_task_{task_id}")
        if not task_data:
            return Response({'error': 'Task not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if user owns this task
        if task_data.get('user_id') != request.user.id:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        
        return Response(task_data)
    
    @action(detail=True, methods=['get'])
    def backtests(self, request, pk=None):
        """
        Get all backtests for a strategy
        
        GET /api/strategies/{id}/backtests/
        """
        strategy = self.get_object()
        backtests = strategy.backtests.all()
        
        serializer = BacktestResultSerializer(backtests, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def latest_backtest(self, request, pk=None):
        """
        Get latest backtest for a strategy
        
        GET /api/strategies/{id}/latest_backtest/
        """
        strategy = self.get_object()
        latest_backtest = strategy.backtests.first()
        
        if not latest_backtest:
            return Response(
                {'error': 'No backtests found for this strategy'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = BacktestResultSerializer(latest_backtest)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """
        Get lightweight summary of all strategies with backtest metrics (fast loading)
        
        GET /api/strategies/summary/
        """
        strategies = Strategy.objects.filter(user=request.user).prefetch_related(
            'backtests'
        ).select_related('user')
        
        serializer = StrategySummarySerializer(strategies, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], permission_classes=[])
    def community(self, request):
        """
        Get public strategies from all users for community view (no authentication required)
        
        GET /api/strategies/community/
        """
        try:
            # Get only PUBLIC strategies from all users for community view
            strategies = Strategy.objects.filter(is_public=True).prefetch_related('backtests__equity_curve').select_related('user').order_by('-created_at')
            
            # Serialize with summary data
            serializer = StrategySummarySerializer(strategies, many=True)
            
            return Response({
                'count': len(serializer.data),
                'results': serializer.data
            })
            
        except Exception as e:
            return Response(
                {'error': f'Failed to load community strategies: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'], permission_classes=[])
    def enums(self, request):
        """
        Get all supported enums for strategy creation
        
        GET /api/strategies/enums/
        """
        return Response({
            'symbols': SUPPORTED_SYMBOLS,
            'timeframes': SUPPORTED_TIMEFRAMES,
            'indicators': SUPPORTED_INDICATORS,
            'operators': SUPPORTED_OPERATORS,
            'stop_loss_types': STOP_LOSS_TYPES,
            'take_profit_types': TAKE_PROFIT_TYPES,
            'strategy_status': STRATEGY_STATUS,
            'rule_types': RULE_TYPES,
            'action_types': ACTION_TYPES,
            'logical_operators': LOGICAL_OPERATORS
        })
    
    @action(detail=False, methods=['get'], permission_classes=[])
    def available_date_range(self, request):
        """
        Get available date range for a symbol/timeframe combination
        
        GET /api/strategies/available_date_range/?symbol=ES&timeframe=5m
        """
        from .date_validator import BacktestDateValidator
        
        symbol = request.query_params.get('symbol', 'ES')
        timeframe = request.query_params.get('timeframe', '5m')
        
        validator = BacktestDateValidator()
        min_date, max_date = validator.get_available_date_range(symbol, timeframe)
        
        if min_date is None or max_date is None:
            return Response({
                'error': 'No data available for this symbol/timeframe combination'
            }, status=status.HTTP_404_NOT_FOUND)
        
        return Response({
            'symbol': symbol,
            'timeframe': timeframe,
            'min_date': min_date.isoformat() if min_date else None,
            'max_date': max_date.isoformat() if max_date else None,
            'available_days': (max_date - min_date).days if min_date and max_date else 0
        })


class BacktestResultViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for backtest results"""
    
    serializer_class = BacktestResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return BacktestResult.objects.filter(strategy__user=self.request.user)
    
    @action(detail=True, methods=['get'])
    def trades(self, request, pk=None):
        """
        Get trades for a backtest result
        
        GET /api/backtest-results/{id}/trades/
        """
        backtest_result = self.get_object()
        trades = backtest_result.trades.all()
        
        serializer = TradeSerializer(trades, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def performance_summary(self, request, pk=None):
        """
        Get performance summary for a backtest result
        
        GET /api/backtest-results/{id}/performance_summary/
        """
        backtest_result = self.get_object()
        
        summary = {
            'total_return': float(backtest_result.total_return),
            'total_return_percent': float(backtest_result.total_return_percent),
            'sharpe_ratio': float(backtest_result.sharpe_ratio) if backtest_result.sharpe_ratio else None,
            'max_drawdown': float(backtest_result.max_drawdown),
            'max_drawdown_percent': float(backtest_result.max_drawdown_percent),
            'win_rate': float(backtest_result.win_rate),
            'profit_factor': float(backtest_result.profit_factor),
            'total_trades': backtest_result.total_trades,
            'winning_trades': backtest_result.winning_trades,
            'losing_trades': backtest_result.losing_trades,
            'avg_win': float(backtest_result.avg_win),
            'avg_loss': float(backtest_result.avg_loss),
            'largest_win': float(backtest_result.largest_win),
            'largest_loss': float(backtest_result.largest_loss),
            'rating': backtest_result.rating,
            'rating_color': backtest_result.rating_color,
            'summary_description': backtest_result.summary_description,
            'execution_time': float(backtest_result.execution_time) if backtest_result.execution_time else None,
            'data_source': backtest_result.data_source
        }
        
        return Response(summary)
    
    @action(detail=True, methods=['get'], url_path='debug-equity')
    def debug_equity(self, request, pk=None):
        """
        Debug endpoint to check equity curve data
        
        GET /api/strategies/{id}/debug-equity/
        """
        strategy = self.get_object()
        latest_backtest = strategy.backtests.first()
        
        if not latest_backtest:
            return Response({'error': 'No backtest found'})
        
        equity_points = latest_backtest.equity_curve.all()
        
        return Response({
            'strategy_id': strategy.id,
            'strategy_name': strategy.name,
            'backtest_id': latest_backtest.id,
            'equity_points_count': equity_points.count(),
            'equity_points': [
                {
                    'timestamp': point.timestamp,
                    'equity_value': float(point.equity_value),
                    'drawdown': float(point.drawdown)
                } for point in equity_points[:5]  # First 5 points
            ]
        })
    
    @action(detail=True, methods=['get'])
    def equity_curve(self, request, pk=None):
        """
        Get equity curve data for charting
        
        GET /api/backtest-results/{id}/equity_curve/
        """
        backtest_result = self.get_object()
        equity_points = backtest_result.equity_curve.all()
        
        serializer = EquityCurvePointSerializer(equity_points, many=True)
        return Response(serializer.data)


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for individual trades"""
    
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Trade.objects.filter(backtest__user=self.request.user)
"""
Views for trading strategies and backtesting
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal

from .models import Strategy, BacktestResult, Trade
from .serializers import (
    StrategySerializer, BacktestResultSerializer, TradeSerializer,
    BacktestRequestSerializer, BacktestResponseSerializer
)
from .backtest_engine import BacktestEngine


class StrategyViewSet(viewsets.ModelViewSet):
    """ViewSet for trading strategies"""
    
    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Strategy.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def backtest(self, request, pk=None):
        """
        Run backtest for a strategy
        
        POST /api/strategies/{id}/backtest/
        """
        strategy = self.get_object()
        
        # Validate request data
        serializer = BacktestRequestSerializer(data=request.data)
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
            
            # Get trades
            trades = backtest_result.trades.all()
            
            # Prepare response
            response_data = {
                'strategy': StrategySerializer(strategy).data,
                'settings': serializer.validated_data,
                'trades': TradeSerializer(trades, many=True).data,
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
                    'losing_trades': backtest_result.losing_trades,
                    'avg_win': float(backtest_result.avg_win),
                    'avg_loss': float(backtest_result.avg_loss),
                    'largest_win': float(backtest_result.largest_win),
                    'largest_loss': float(backtest_result.largest_loss)
                },
                'summary': {
                    'rating': backtest_result.rating,
                    'color': backtest_result.rating_color,
                    'description': backtest_result.summary_description
                },
                'timestamp': backtest_result.created_at
            }
            
            return Response(response_data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'Backtest failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
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


class BacktestResultViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for backtest results"""
    
    serializer_class = BacktestResultSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return BacktestResult.objects.filter(user=self.request.user)
    
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


class TradeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for individual trades"""
    
    serializer_class = TradeSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Trade.objects.filter(backtest__user=self.request.user)
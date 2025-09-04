"""
Views for trading strategies and backtesting
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
from decimal import Decimal
import threading
import uuid

from .models import Strategy, BacktestResult, Trade, EquityCurvePoint
from .serializers import (
    StrategySerializer, StrategyListSerializer, StrategySummarySerializer, BacktestResultSerializer, TradeSerializer,
    BacktestRequestSerializer, BacktestResponseSerializer, EquityCurvePointSerializer
)
from .backtest_engine import BacktestEngine
from .schemas import NLToStrategyRequest, NLToStrategyResponse, BacktestRequest, BacktestResponse
from .services.nl_to_dsl import NLToDSLService


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
        """Use lightweight serializer for list view"""
        if self.action == 'list':
            return StrategyListSerializer
        return StrategySerializer
    
    def get_queryset(self):
        """Optimize queryset with prefetch_related for list view"""
        queryset = Strategy.objects.filter(user=self.request.user)
        
        if self.action == 'list':
            # For list view, only prefetch the latest backtest
            queryset = queryset.prefetch_related(
                'backtests'
            ).select_related('user')
        else:
            # For detail view, prefetch all backtests and trades with optimized queries
            queryset = queryset.prefetch_related(
                'backtests__trades',
                'backtests__equity_curve'
            ).select_related('user')
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def backtest(self, request, pk=None):
        """
        Run backtest for a strategy (synchronous)
        
        POST /api/strategies/{id}/backtest/
        """
        strategy = self.get_object()
        
        # Validate request data
        serializer = BacktestRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Use strategy's initial capital if not provided in request
            initial_capital = serializer.validated_data.get('initial_capital')
            if initial_capital is None:
                initial_capital = strategy.initial_capital
            
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


# New DSL-based views
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
import uuid


class NLToStrategyView(APIView):
    """
    Convert natural language trading rules to DSL and LEAN code
    
    POST /api/nl-to-strategy/
    """
    permission_classes = []  # Remove authentication for testing
    
    def post(self, request):
        try:
            # Validate request
            request_data = NLToStrategyRequest(**request.data)
            
            # Convert to DSL
            service = NLToDSLService()
            response = service.convert_to_dsl(
                text=request_data.text,
                defaults=request_data.defaults or {}
            )
            
            return Response(response.dict(), status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Failed to convert natural language: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class RunBacktestView(APIView):
    """
    Run backtest with DSL or LEAN code (stub implementation)
    
    POST /api/run-backtest/
    """
    permission_classes = []  # Remove authentication for testing
    
    def post(self, request):
        try:
            # Validate request
            request_data = BacktestRequest(**request.data)
            
            # Generate fake backtest result for now
            backtest_id = str(uuid.uuid4())
            
            # Mock results
            fake_results = {
                'total_return': 15.67,
                'total_return_percent': 15.67,
                'sharpe_ratio': 1.23,
                'max_drawdown': -8.45,
                'max_drawdown_percent': -8.45,
                'win_rate': 65.0,
                'profit_factor': 1.89,
                'total_trades': 45,
                'winning_trades': 29,
                'losing_trades': 16,
                'avg_win': 2.34,
                'avg_loss': -1.45,
                'largest_win': 8.90,
                'largest_loss': -4.20
            }
            
            response = BacktestResponse(
                success=True,
                backtest_id=backtest_id,
                results=fake_results
            )
            
            return Response(response.dict(), status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response(
                {'error': f'Backtest failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


# Frontend integration snippet (commented out)
"""
FRONTEND INTEGRATION SNIPPET (React):

import React, { useState } from 'react';

const TradingStrategyConverter = () => {
  const [text, setText] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/nl-to-strategy/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({ text })
      });

      if (!response.ok) {
        throw new Error('Failed to convert strategy');
      }

      const data = await response.json();
      setResult(data);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder="Describe your trading strategy in natural language..."
          rows={4}
          cols={50}
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Converting...' : 'Convert to Strategy'}
        </button>
      </form>

      {error && <div style={{color: 'red'}}>{error}</div>}

      {result && (
        <div>
          <h3>Strategy DSL:</h3>
          <pre>{JSON.stringify(result.dsl, null, 2)}</pre>
          
          <h3>LEAN Code:</h3>
          <pre>{result.lean_code}</pre>
          
          {result.warnings.length > 0 && (
            <div>
              <h4>Warnings:</h4>
              <ul>
                {result.warnings.map((warning, i) => (
                  <li key={i}>{warning}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default TradingStrategyConverter;
"""
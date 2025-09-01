"""
Django REST Framework views for Technical Indicators
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
import os

from .models import Symbol, IndicatorResult, AnalysisResult, IndicatorConfiguration
from .serializers import (
    SymbolSerializer, IndicatorResultSerializer, AnalysisResultSerializer,
    IndicatorConfigurationSerializer, IndicatorCalculationRequestSerializer,
    TrendAnalysisSerializer, MomentumAnalysisSerializer
)
from .services import TechnicalAnalysisService


class SymbolViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for trading symbols"""
    
    queryset = Symbol.objects.filter(is_active=True)
    serializer_class = SymbolSerializer
    permission_classes = [IsAuthenticated]
    
    @action(detail=True, methods=['get'])
    def indicators(self, request, pk=None):
        """Get indicators for a specific symbol"""
        symbol = self.get_object()
        
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        limit = int(request.query_params.get('limit', 100))
        
        # Build queryset
        queryset = IndicatorResult.objects.filter(symbol=symbol)
        
        if start_date:
            queryset = queryset.filter(timestamp__gte=start_date)
        if end_date:
            queryset = queryset.filter(timestamp__lte=end_date)
        
        queryset = queryset.order_by('-timestamp')[:limit]
        
        serializer = IndicatorResultSerializer(queryset, many=True)
        return Response(serializer.data)


class IndicatorResultViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for indicator results"""
    
    queryset = IndicatorResult.objects.all()
    serializer_class = IndicatorResultSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ['symbol', 'timestamp']
    search_fields = ['symbol__name']
    ordering_fields = ['timestamp', 'close_price', 'volume']
    ordering = ['-timestamp']
    
    @action(detail=False, methods=['post'])
    def calculate(self, request):
        """Calculate indicators for a symbol"""
        serializer = IndicatorCalculationRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        data = serializer.validated_data
        symbol_name = data['symbol']
        
        try:
            # Check if we have parquet data for this symbol
            parquet_file = f"data/indicators/{symbol_name}_with_indicators.parquet"
            
            if not os.path.exists(parquet_file):
                return Response(
                    {'error': f'No data found for symbol {symbol_name}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Read parquet data
            df = pd.read_parquet(parquet_file)
            
            # Filter by date if specified
            if data.get('start_date'):
                df = df[df.index >= data['start_date']]
            if data.get('end_date'):
                df = df[df.index <= data['end_date']]
            
            # Get latest data
            latest_data = df.tail(100)  # Last 100 records
            
            # Convert to list of dictionaries
            results = []
            for timestamp, row in latest_data.iterrows():
                result = {
                    'timestamp': timestamp.isoformat(),
                    'open_price': float(row['open']),
                    'high_price': float(row['high']),
                    'low_price': float(row['low']),
                    'close_price': float(row['close']),
                    'volume': int(row['volume']),
                    'sma_20': float(row['sma_20']) if pd.notna(row['sma_20']) else None,
                    'sma_50': float(row['sma_50']) if pd.notna(row['sma_50']) else None,
                    'ema_20': float(row['ema_20']) if pd.notna(row['ema_20']) else None,
                    'ema_50': float(row['ema_50']) if pd.notna(row['ema_50']) else None,
                    'vwap': float(row['vwap']) if pd.notna(row['vwap']) else None,
                    'rsi': float(row['rsi']) if pd.notna(row['rsi']) else None,
                    'macd_line': float(row['macd_line']) if pd.notna(row['macd_line']) else None,
                    'macd_signal': float(row['macd_signal']) if pd.notna(row['macd_signal']) else None,
                    'macd_histogram': float(row['macd_histogram']) if pd.notna(row['macd_histogram']) else None,
                    'stoch_k': float(row['stoch_k']) if pd.notna(row['stoch_k']) else None,
                    'stoch_d': float(row['stoch_d']) if pd.notna(row['stoch_d']) else None,
                    'atr': float(row['atr']) if pd.notna(row['atr']) else None,
                    'bb_upper': float(row['bb_upper']) if pd.notna(row['bb_upper']) else None,
                    'bb_middle': float(row['bb_middle']) if pd.notna(row['bb_middle']) else None,
                    'bb_lower': float(row['bb_lower']) if pd.notna(row['bb_lower']) else None,
                }
                results.append(result)
            
            return Response({
                'symbol': symbol_name,
                'count': len(results),
                'results': results
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error calculating indicators: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest indicator results for all symbols"""
        symbols = request.query_params.getlist('symbols', [])
        
        if symbols:
            queryset = IndicatorResult.objects.filter(symbol__name__in=symbols)
        else:
            queryset = IndicatorResult.objects.all()
        
        # Get latest result for each symbol
        latest_results = []
        for symbol in Symbol.objects.filter(is_active=True):
            latest = queryset.filter(symbol=symbol).order_by('-timestamp').first()
            if latest:
                latest_results.append(latest)
        
        serializer = IndicatorResultSerializer(latest_results, many=True)
        return Response(serializer.data)


class AnalysisResultViewSet(viewsets.ModelViewSet):
    """ViewSet for analysis results"""
    
    queryset = AnalysisResult.objects.all()
    serializer_class = AnalysisResultSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'])
    def analyze_trend(self, request):
        """Perform trend analysis for a symbol"""
        symbol_name = request.data.get('symbol')
        if not symbol_name:
            return Response(
                {'error': 'Symbol is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get symbol
            symbol = get_object_or_404(Symbol, name=symbol_name, is_active=True)
            
            # Read parquet data
            parquet_file = f"data/indicators/{symbol_name}_with_indicators.parquet"
            if not os.path.exists(parquet_file):
                return Response(
                    {'error': f'No data found for symbol {symbol_name}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            df = pd.read_parquet(parquet_file)
            
            # Initialize service and get trend analysis
            ta_service = TechnicalAnalysisService(df)
            trend_analysis = ta_service.get_trend_analysis()
            
            # Save analysis result
            analysis_result = AnalysisResult.objects.create(
                symbol=symbol,
                analysis_type='trend',
                timestamp=timezone.now(),
                analysis_data=trend_analysis,
                created_by=request.user
            )
            
            serializer = AnalysisResultSerializer(analysis_result)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Error analyzing trend: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def analyze_momentum(self, request):
        """Perform momentum analysis for a symbol"""
        symbol_name = request.data.get('symbol')
        if not symbol_name:
            return Response(
                {'error': 'Symbol is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Get symbol
            symbol = get_object_or_404(Symbol, name=symbol_name, is_active=True)
            
            # Read parquet data
            parquet_file = f"data/indicators/{symbol_name}_with_indicators.parquet"
            if not os.path.exists(parquet_file):
                return Response(
                    {'error': f'No data found for symbol {symbol_name}'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            df = pd.read_parquet(parquet_file)
            
            # Initialize service and get momentum analysis
            ta_service = TechnicalAnalysisService(df)
            momentum_analysis = ta_service.get_momentum_analysis()
            
            # Save analysis result
            analysis_result = AnalysisResult.objects.create(
                symbol=symbol,
                analysis_type='momentum',
                timestamp=timezone.now(),
                analysis_data=momentum_analysis,
                created_by=request.user
            )
            
            serializer = AnalysisResultSerializer(analysis_result)
            return Response(serializer.data)
            
        except Exception as e:
            return Response(
                {'error': f'Error analyzing momentum: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class IndicatorConfigurationViewSet(viewsets.ModelViewSet):
    """ViewSet for indicator configurations"""
    
    queryset = IndicatorConfiguration.objects.all()
    serializer_class = IndicatorConfigurationSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

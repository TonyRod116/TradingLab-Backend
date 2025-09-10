"""
Optimized views using Parquet files for better performance
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

from .models import HistoricalData, DataImportLog
from .parquet_service import ParquetDataService
from .serializers import (
    HistoricalDataSerializer, 
    HistoricalDataListSerializer,
    DataImportLogSerializer,
    DataSummarySerializer
)


class OptimizedHistoricalDataViewSet(viewsets.ModelViewSet):
    """Optimized ViewSet for historical OHLCV data using Parquet files"""
    
    queryset = HistoricalData.objects.all()
    serializer_class = HistoricalDataSerializer
    permission_classes = [IsAuthenticated]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parquet_service = ParquetDataService()
    
    def get_queryset(self):
        """Get queryset with filters - used for metadata and fallback"""
        queryset = HistoricalData.objects.all()
        
        # Apply basic filters for metadata
        symbol = self.request.query_params.get('symbol', None)
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        
        timeframe = self.request.query_params.get('timeframe', None)
        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)
        
        return queryset
    
    def list(self, request, *args, **kwargs):
        """Optimized list view using Parquet files when available"""
        symbol = request.query_params.get('symbol', 'ES')
        timeframe = request.query_params.get('timeframe', '1m')
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        limit = request.query_params.get('limit', None)
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        # Parse limit
        limit_int = None
        if limit and limit.isdigit():
            limit_int = int(limit)
        
        try:
            # Try to get data from Parquet service
            df = self.parquet_service.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_dt,
                end_date=end_dt,
                limit=limit_int
            )
            
            if df.empty:
                return Response(
                    {'error': 'No data found for specified parameters'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Convert DataFrame to list of dictionaries
            data = df.to_dict('records')
            
            # Add metadata
            response_data = {
                'count': len(data),
                'symbol': symbol,
                'timeframe': timeframe,
                'data_source': 'parquet' if self.parquet_service.is_parquet_available(symbol, timeframe) else 'database',
                'results': data
            }
            
            return Response(response_data)
            
        except Exception as e:
            return Response(
                {'error': f'Error retrieving data: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get data summary statistics using optimized service"""
        symbol = request.query_params.get('symbol', 'ES')
        timeframe = request.query_params.get('timeframe', '1m')
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                pass
        
        try:
            # Get data using optimized service
            df = self.parquet_service.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                start_date=start_dt,
                end_date=end_dt
            )
            
            if df.empty:
                return Response(
                    {'error': 'No data found for specified symbol and period'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Calculate statistics
            total_candles = len(df)
            avg_volume = df['volume'].mean()
            max_price = df['high'].max()
            min_price = df['low'].min()
            
            # Count candle types
            bullish_candles = (df['close'] > df['open']).sum()
            bearish_candles = (df['close'] < df['open']).sum()
            doji_candles = (df['close'] == df['open']).sum()
            
            # Calculate price change
            first_candle = df.iloc[0]
            last_candle = df.iloc[-1]
            price_change = last_candle['close'] - first_candle['open']
            price_change_percent = (price_change / first_candle['open']) * 100
            
            summary_data = {
                'symbol': symbol,
                'timeframe': timeframe,
                'start_date': first_candle['date'],
                'end_date': last_candle['date'],
                'total_candles': total_candles,
                'avg_volume': float(avg_volume),
                'max_price': float(max_price),
                'min_price': float(min_price),
                'price_change': float(price_change),
                'price_change_percent': float(price_change_percent),
                'bullish_candles': int(bullish_candles),
                'bearish_candles': int(bearish_candles),
                'doji_candles': int(doji_candles),
                'data_source': 'parquet' if self.parquet_service.is_parquet_available(symbol, timeframe) else 'database'
            }
            
            return Response(summary_data)
            
        except Exception as e:
            return Response(
                {'error': f'Error calculating summary: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def latest(self, request):
        """Get latest candle for a symbol and timeframe"""
        symbol = request.query_params.get('symbol', 'ES')
        timeframe = request.query_params.get('timeframe', '1m')
        
        try:
            latest_candle = self.parquet_service.get_latest_candle(symbol, timeframe)
            
            if latest_candle is None:
                return Response(
                    {'error': 'No data found for specified symbol and timeframe'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            return Response(latest_candle)
            
        except Exception as e:
            return Response(
                {'error': f'Error retrieving latest candle: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def technical_indicators(self, request):
        """Calculate technical indicators using optimized data access"""
        symbol = request.query_params.get('symbol', 'ES')
        timeframe = request.query_params.get('timeframe', '1m')
        period = int(request.query_params.get('period', 14))
        limit = int(request.query_params.get('limit', 200))  # Get more data for calculations
        
        try:
            # Get data using optimized service
            df = self.parquet_service.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                limit=limit
            )
            
            if df.empty:
                return Response(
                    {'error': 'No data found for specified symbol'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            if len(df) < period:
                return Response(
                    {'error': f'At least {period} periods required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Calculate technical indicators
            df['sma'] = df['close'].rolling(window=period).mean()
            df['ema'] = df['close'].ewm(span=period).mean()
            df['rsi'] = self._calculate_rsi(df['close'], period)
            
            # Get latest values
            latest = df.iloc[-1]
            
            indicators = {
                'symbol': symbol,
                'timeframe': timeframe,
                'period': period,
                'current_price': float(latest['close']),
                'sma': float(latest['sma']) if pd.notna(latest['sma']) else None,
                'ema': float(latest['ema']) if pd.notna(latest['ema']) else None,
                'rsi': float(latest['rsi']) if pd.notna(latest['rsi']) else None,
                'price_vs_sma': float(latest['close'] - latest['sma']) if pd.notna(latest['sma']) else None,
                'price_vs_ema': float(latest['close'] - latest['ema']) if pd.notna(latest['ema']) else None,
                'data_source': 'parquet' if self.parquet_service.is_parquet_available(symbol, timeframe) else 'database'
            }
            
            return Response(indicators)
            
        except Exception as e:
            return Response(
                {'error': f'Error calculating indicators: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def performance_stats(self, request):
        """Get performance statistics for the service"""
        try:
            stats = self.parquet_service.get_performance_stats()
            return Response(stats)
        except Exception as e:
            return Response(
                {'error': f'Error getting performance stats: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['get'])
    def available_timeframes(self, request):
        """Get available timeframes for a symbol"""
        symbol = request.query_params.get('symbol', 'ES')
        
        try:
            available = self.parquet_service.get_available_timeframes(symbol)
            
            # Also check database for comparison
            db_timeframes = list(HistoricalData.objects.filter(symbol=symbol).values_list('timeframe', flat=True).distinct())
            
            return Response({
                'symbol': symbol,
                'parquet_available': available,
                'database_available': db_timeframes,
                'all_available': list(set(available + db_timeframes))
            })
            
        except Exception as e:
            return Response(
                {'error': f'Error getting available timeframes: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def warm_cache(self, request):
        """Warm up cache with recent data"""
        symbol = request.data.get('symbol', 'ES')
        timeframes = request.data.get('timeframes', None)
        days_back = request.data.get('days_back', 30)
        
        try:
            results = self.parquet_service.warm_cache(symbol, timeframes, days_back)
            return Response({
                'message': 'Cache warming completed',
                'results': results
            })
        except Exception as e:
            return Response(
                {'error': f'Error warming cache: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi


class DataImportLogViewSet(viewsets.ModelViewSet):
    """ViewSet for data import logs"""
    
    queryset = DataImportLog.objects.all()
    serializer_class = DataImportLogSerializer
    permission_classes = [IsAuthenticated]

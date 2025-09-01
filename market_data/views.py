from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Avg, Max, Min, Count, Q
from django.utils import timezone
from datetime import datetime, timedelta
import pandas as pd

from .models import HistoricalData, DataImportLog
from .serializers import (
    HistoricalDataSerializer, 
    HistoricalDataListSerializer,
    DataImportLogSerializer,
    DataSummarySerializer
)


class HistoricalDataViewSet(viewsets.ModelViewSet):
    """ViewSet for historical OHLCV data"""
    
    queryset = HistoricalData.objects.all()
    serializer_class = HistoricalDataSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = HistoricalData.objects.all()
        
        # Filters
        symbol = self.request.query_params.get('symbol', None)
        if symbol:
            queryset = queryset.filter(symbol=symbol)
        
        timeframe = self.request.query_params.get('timeframe', None)
        if timeframe:
            queryset = queryset.filter(timeframe=timeframe)
        
        start_date = self.request.query_params.get('start_date', None)
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                pass
        
        end_date = self.request.query_params.get('end_date', None)
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                pass
        
        # Ordering
        order_by = self.request.query_params.get('order_by', '-date')
        if order_by in ['date', '-date', 'open_price', '-open_price', 'volume', '-volume']:
            queryset = queryset.order_by(order_by)
        
        # Limit results
        limit = self.request.query_params.get('limit', None)
        if limit and limit.isdigit():
            queryset = queryset[:int(limit)]
        
        return queryset
    
    def get_serializer_class(self):
        if self.action == 'list':
            return HistoricalDataListSerializer
        return HistoricalDataSerializer
    
    @action(detail=False, methods=['get'])
    def summary(self, request):
        """Get data summary statistics"""
        symbol = request.query_params.get('symbol', 'ES')
        timeframe = request.query_params.get('timeframe', '1m')
        start_date = request.query_params.get('start_date', None)
        end_date = request.query_params.get('end_date', None)
        
        queryset = HistoricalData.objects.filter(symbol=symbol, timeframe=timeframe)
        
        if start_date:
            try:
                start_date = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                queryset = queryset.filter(date__gte=start_date)
            except ValueError:
                pass
        
        if end_date:
            try:
                end_date = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                queryset = queryset.filter(date__lte=end_date)
            except ValueError:
                pass
        
        if not queryset.exists():
            return Response(
                {'error': 'No data found for specified symbol and period'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Calculate statistics
        first_candle = queryset.order_by('date').first()
        last_candle = queryset.order_by('-date').first()
        
        stats = queryset.aggregate(
            total_candles=Count('id'),
            avg_volume=Avg('volume'),
            max_price=Max('high_price'),
            min_price=Min('low_price'),
            bullish_candles=Count('id', filter=Q(close_price__gt='open_price')),
            bearish_candles=Count('id', filter=Q(close_price__lt='open_price')),
            doji_candles=Count('id', filter=Q(close_price='open_price'))
        )
        
        # Calculate price change
        price_change = last_candle.close_price - first_candle.open_price
        price_change_percent = (price_change / first_candle.open_price) * 100
        
        summary_data = {
            'symbol': symbol,
            'timeframe': timeframe,
            'start_date': first_candle.date,
            'end_date': last_candle.date,
            'total_candles': stats['total_candles'],
            'avg_volume': stats['avg_volume'],
            'max_price': stats['max_price'],
            'min_price': stats['min_price'],
            'price_change': price_change,
            'price_change_percent': price_change_percent,
            'bullish_candles': stats['bullish_candles'],
            'bearish_candles': stats['bearish_candles'],
            'doji_candles': stats['doji_candles']
        }
        
        serializer = DataSummarySerializer(summary_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def technical_indicators(self, request):
        """Calculate basic technical indicators"""
        symbol = request.query_params.get('symbol', 'ES')
        timeframe = request.query_params.get('timeframe', '1m')
        period = int(request.query_params.get('period', 14))
        
        queryset = HistoricalData.objects.filter(symbol=symbol, timeframe=timeframe).order_by('date')
        
        if not queryset.exists():
            return Response(
                {'error': 'No data found for specified symbol'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Convert to DataFrame for calculations
        data = list(queryset.values('date', 'close_price', 'volume'))
        df = pd.DataFrame(data)
        
        if len(df) < period:
            return Response(
                {'error': f'At least {period} periods required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate technical indicators
        df['sma'] = df['close_price'].rolling(window=period).mean()
        df['ema'] = df['close_price'].ewm(span=period).mean()
        df['rsi'] = self._calculate_rsi(df['close_price'], period)
        
        # Get latest values
        latest = df.iloc[-1]
        
        indicators = {
            'symbol': symbol,
            'timeframe': timeframe,
            'period': period,
            'current_price': float(latest['close_price']),
            'sma': float(latest['sma']) if pd.notna(latest['sma']) else None,
            'ema': float(latest['ema']) if pd.notna(latest['ema']) else None,
            'rsi': float(latest['rsi']) if pd.notna(latest['rsi']) else None,
            'price_vs_sma': float(latest['close_price'] - latest['sma']) if pd.notna(latest['sma']) else None,
            'price_vs_ema': float(latest['close_price'] - latest['ema']) if pd.notna(latest['ema']) else None,
        }
        
        return Response(indicators)
    
    def _calculate_rsi(self, prices, period=14):
        """Calculate RSI (Relative Strength Index)"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi
    
    @action(detail=False, methods=['get'])
    def candlestick_patterns(self, request):
        """Identify candlestick patterns"""
        symbol = request.query_params.get('symbol', 'ES')
        timeframe = request.query_params.get('timeframe', '1m')
        limit = int(request.query_params.get('limit', 100))
        
        queryset = HistoricalData.objects.filter(symbol=symbol, timeframe=timeframe).order_by('-date')[:limit]
        
        if not queryset.exists():
            return Response(
                {'error': 'No data found for specified symbol'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        patterns = []
        for candle in queryset:
            pattern = self._identify_candlestick_pattern(candle)
            if pattern:
                patterns.append({
                    'date': candle.date,
                    'pattern': pattern,
                    'open': float(candle.open_price),
                    'high': float(candle.high_price),
                    'low': float(candle.low_price),
                    'close': float(candle.close_price),
                    'volume': candle.volume
                })
        
        return Response({
            'symbol': symbol,
            'timeframe': timeframe,
            'patterns_found': len(patterns),
            'patterns': patterns
        })
    
    def _identify_candlestick_pattern(self, candle):
        """Identify individual candlestick pattern"""
        body_size = abs(candle.body_size)
        upper_shadow = candle.upper_shadow
        lower_shadow = candle.lower_shadow
        
        # Basic patterns
        if candle.is_doji:
            if upper_shadow > 2 * body_size and lower_shadow > 2 * body_size:
                return 'Long-Legged Doji'
            elif upper_shadow > 2 * body_size:
                return 'Gravestone Doji'
            elif lower_shadow > 2 * body_size:
                return 'Dragonfly Doji'
            else:
                return 'Doji'
        
        if candle.is_bullish:
            if body_size > 2 * (upper_shadow + lower_shadow):
                return 'Strong Bullish'
            elif lower_shadow > 2 * body_size:
                return 'Hammer'
        
        if candle.is_bearish:
            if body_size > 2 * (upper_shadow + lower_shadow):
                return 'Strong Bearish'
            elif upper_shadow > 2 * body_size:
                return 'Shooting Star'
        
        return None


class DataImportLogViewSet(viewsets.ModelViewSet):
    """ViewSet for data import logs"""
    
    queryset = DataImportLog.objects.all()
    serializer_class = DataImportLogSerializer
    permission_classes = [IsAuthenticated]

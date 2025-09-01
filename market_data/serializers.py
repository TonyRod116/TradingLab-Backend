from rest_framework import serializers
from .models import HistoricalData, DataImportLog


class HistoricalDataSerializer(serializers.ModelSerializer):
    """Serializer for historical OHLCV data"""
    
    body_size = serializers.ReadOnlyField()
    upper_shadow = serializers.ReadOnlyField()
    lower_shadow = serializers.ReadOnlyField()
    is_bullish = serializers.ReadOnlyField()
    is_bearish = serializers.ReadOnlyField()
    is_doji = serializers.ReadOnlyField()
    
    class Meta:
        model = HistoricalData
        fields = [
            'id', 'symbol', 'timeframe', 'date', 'open_price', 'high_price', 'low_price', 
            'close_price', 'volume', 'body_size', 'upper_shadow', 'lower_shadow',
            'is_bullish', 'is_bearish', 'is_doji', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class HistoricalDataListSerializer(serializers.ModelSerializer):
    """Simplified serializer for data lists"""
    
    class Meta:
        model = HistoricalData
        fields = ['id', 'symbol', 'timeframe', 'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume']


class DataImportLogSerializer(serializers.ModelSerializer):
    """Serializer for data import logs"""
    
    class Meta:
        model = DataImportLog
        fields = ['id', 'file_name', 'file_path', 'symbol', 'timeframe', 'total_rows', 
                 'imported_rows', 'skipped_rows', 'start_date', 'end_date', 'status', 
                 'error_message', 'processing_time', 'created_at', 'updated_at']


class DataSummarySerializer(serializers.Serializer):
    """Serializer for data summary statistics"""
    
    symbol = serializers.CharField()
    timeframe = serializers.CharField()
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    total_candles = serializers.IntegerField()
    avg_volume = serializers.DecimalField(max_digits=15, decimal_places=2)
    max_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    min_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_change = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_change_percent = serializers.DecimalField(max_digits=5, decimal_places=2)
    bullish_candles = serializers.IntegerField()
    bearish_candles = serializers.IntegerField()
    doji_candles = serializers.IntegerField()

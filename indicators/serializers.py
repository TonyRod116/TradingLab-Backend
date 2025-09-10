"""
Django REST Framework serializers for Technical Indicators
"""

from rest_framework import serializers
from .models import Symbol, IndicatorResult, AnalysisResult, IndicatorConfiguration


class SymbolSerializer(serializers.ModelSerializer):
    """Serializer for Symbol model"""
    
    class Meta:
        model = Symbol
        fields = ['id', 'name', 'description', 'is_active', 'created_at', 'updated_at']


class IndicatorResultSerializer(serializers.ModelSerializer):
    """Serializer for IndicatorResult model"""
    
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    
    class Meta:
        model = IndicatorResult
        fields = [
            'id', 'symbol', 'symbol_name', 'timestamp',
            'open_price', 'high_price', 'low_price', 'close_price', 'volume',
            'sma_20', 'sma_50', 'ema_20', 'ema_50', 'vwap',
            'rsi', 'macd_line', 'macd_signal', 'macd_histogram',
            'stoch_k', 'stoch_d', 'atr', 'bb_upper', 'bb_middle', 'bb_lower',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']


class AnalysisResultSerializer(serializers.ModelSerializer):
    """Serializer for AnalysisResult model"""
    
    symbol_name = serializers.CharField(source='symbol.name', read_only=True)
    analysis_type_display = serializers.CharField(source='get_analysis_type_display', read_only=True)
    
    class Meta:
        model = AnalysisResult
        fields = [
            'id', 'symbol', 'symbol_name', 'analysis_type', 'analysis_type_display',
            'timestamp', 'analysis_data', 'created_by', 'created_at', 'notes'
        ]
        read_only_fields = ['created_at', 'created_by']


class IndicatorConfigurationSerializer(serializers.ModelSerializer):
    """Serializer for IndicatorConfiguration model"""
    
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = IndicatorConfiguration
        fields = [
            'id', 'name', 'description',
            'sma_periods', 'ema_periods', 'rsi_period',
            'macd_fast', 'macd_slow', 'macd_signal',
            'atr_period', 'bb_period', 'bb_std_dev',
            'is_active', 'created_by', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at', 'created_by']


class IndicatorCalculationRequestSerializer(serializers.Serializer):
    """Serializer for indicator calculation requests"""
    
    symbol = serializers.CharField(max_length=20)
    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    indicators = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=False
    )
    config_id = serializers.IntegerField(required=False)


class TrendAnalysisSerializer(serializers.Serializer):
    """Serializer for trend analysis results"""
    
    trend = serializers.CharField(max_length=50)
    current_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    sma_20 = serializers.DecimalField(max_digits=10, decimal_places=2)
    sma_50 = serializers.DecimalField(max_digits=10, decimal_places=2)
    ema_20 = serializers.DecimalField(max_digits=10, decimal_places=2)
    price_vs_sma_20 = serializers.DecimalField(max_digits=5, decimal_places=2)
    price_vs_sma_50 = serializers.DecimalField(max_digits=5, decimal_places=2)


class MomentumAnalysisSerializer(serializers.Serializer):
    """Serializer for momentum analysis results"""
    
    rsi = serializers.DecimalField(max_digits=5, decimal_places=2)
    rsi_signal = serializers.CharField(max_length=20)
    macd_line = serializers.DecimalField(max_digits=10, decimal_places=2)
    macd_signal_line = serializers.DecimalField(max_digits=10, decimal_places=2)
    macd_histogram = serializers.DecimalField(max_digits=10, decimal_places=2)
    macd_signal = serializers.CharField(max_length=20)

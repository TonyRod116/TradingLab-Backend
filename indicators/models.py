"""
Django models for Technical Indicators
"""

from django.db import models
from django.conf import settings
from django.utils import timezone


class Symbol(models.Model):
    """Trading symbol (e.g., ESU0, ESZ0)"""
    
    name = models.CharField(max_length=20, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name


class IndicatorResult(models.Model):
    """Stores calculated technical indicators for a symbol at a specific time"""
    
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='indicator_results')
    timestamp = models.DateTimeField()
    
    # OHLCV data
    open_price = models.DecimalField(max_digits=10, decimal_places=2)
    high_price = models.DecimalField(max_digits=10, decimal_places=2)
    low_price = models.DecimalField(max_digits=10, decimal_places=2)
    close_price = models.DecimalField(max_digits=10, decimal_places=2)
    volume = models.BigIntegerField()
    
    # Trend indicators
    sma_20 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sma_50 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ema_20 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    ema_50 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    vwap = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Momentum indicators
    rsi = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    macd_line = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    macd_signal = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    macd_histogram = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stoch_k = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    stoch_d = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    
    # Volatility indicators
    atr = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bb_upper = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bb_middle = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    bb_lower = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['symbol', 'timestamp']
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['symbol', 'timestamp']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.symbol.name} - {self.timestamp}"


class AnalysisResult(models.Model):
    """Stores analysis results (trend, momentum, etc.)"""
    
    ANALYSIS_TYPES = [
        ('trend', 'Trend Analysis'),
        ('momentum', 'Momentum Analysis'),
        ('volatility', 'Volatility Analysis'),
        ('custom', 'Custom Analysis'),
    ]
    
    symbol = models.ForeignKey(Symbol, on_delete=models.CASCADE, related_name='analysis_results')
    analysis_type = models.CharField(max_length=20, choices=ANALYSIS_TYPES)
    timestamp = models.DateTimeField()
    
    # Analysis data (stored as JSON)
    analysis_data = models.JSONField()
    
    # Metadata
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)
    
    class Meta:
        unique_together = ['symbol', 'analysis_type', 'timestamp']
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.symbol.name} - {self.analysis_type} - {self.timestamp}"


class IndicatorConfiguration(models.Model):
    """Configuration for indicator calculations"""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    
    # Indicator parameters
    sma_periods = models.JSONField(default=list)  # [20, 50, 200]
    ema_periods = models.JSONField(default=list)  # [12, 26]
    rsi_period = models.IntegerField(default=14)
    macd_fast = models.IntegerField(default=12)
    macd_slow = models.IntegerField(default=26)
    macd_signal = models.IntegerField(default=9)
    atr_period = models.IntegerField(default=14)
    bb_period = models.IntegerField(default=20)
    bb_std_dev = models.DecimalField(max_digits=3, decimal_places=1, default=2.0)
    
    # Settings
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['name']
    
    def __str__(self):
        return self.name

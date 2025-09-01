from django.db import models
from django.utils import timezone
from decimal import Decimal


class HistoricalData(models.Model):
    """Historical OHLCV data for S&P 500 futures"""
    
    TIMEFRAME_CHOICES = [
        ('1m', '1 Minute'),
        ('5m', '5 Minutes'),
        ('15m', '15 Minutes'),
        ('30m', '30 Minutes'),
        ('1h', '1 Hour'),
        ('4h', '4 Hours'),
        ('1d', '1 Day'),
    ]
    
    symbol = models.CharField(max_length=20, default='ES', help_text='Future symbol (e.g., ES for E-mini S&P 500)')
    date = models.DateTimeField(help_text='Candle date and time')
    timeframe = models.CharField(max_length=3, choices=TIMEFRAME_CHOICES, default='1m', help_text='Data timeframe')
    open_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Opening price')
    high_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Highest price')
    low_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Lowest price')
    close_price = models.DecimalField(max_digits=10, decimal_places=2, help_text='Closing price')
    volume = models.BigIntegerField(help_text='Transaction volume')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'historical_data'
        indexes = [
            models.Index(fields=['symbol', 'date', 'timeframe']),
            models.Index(fields=['date']),
            models.Index(fields=['symbol', 'timeframe']),
        ]
        unique_together = ['symbol', 'date', 'timeframe']
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.symbol} - {self.date.strftime('%Y-%m-%d %H:%M')} - {self.timeframe} - O:{self.open_price} H:{self.high_price} L:{self.low_price} C:{self.close_price} V:{self.volume}"
    
    @property
    def body_size(self):
        """Candle body size (close - open)"""
        return self.close_price - self.open_price
    
    @property
    def upper_shadow(self):
        """Upper shadow (high - max(open, close))"""
        return self.high_price - max(self.open_price, self.close_price)
    
    @property
    def lower_shadow(self):
        """Lower shadow (min(open, close) - low)"""
        return min(self.open_price, self.close_price) - self.low_price
    
    @property
    def is_bullish(self):
        """True if bullish candle (close > open)"""
        return self.close_price > self.open_price
    
    @property
    def is_bearish(self):
        """True if bearish candle (close < open)"""
        return self.close_price < self.open_price
    
    @property
    def is_doji(self):
        """True if doji candle (open ≈ close)"""
        return abs(self.close_price - self.open_price) < 0.01
    
    @property
    def price_change(self):
        """Price change (close - open)"""
        return self.close_price - self.open_price
    
    @property
    def price_change_percent(self):
        """Price change percentage"""
        if self.open_price != 0:
            return (self.price_change / self.open_price) * 100
        return 0


class DataImportLog(models.Model):
    """Data import logging model"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    file_name = models.CharField(max_length=255, help_text='Imported file name')
    file_path = models.TextField(help_text='File path')
    symbol = models.CharField(max_length=20, help_text='Future symbol')
    timeframe = models.CharField(max_length=3, help_text='Data timeframe')
    total_rows = models.IntegerField(default=0, help_text='Total rows in file')
    imported_rows = models.IntegerField(default=0, help_text='Successfully imported rows')
    skipped_rows = models.IntegerField(default=0, help_text='Skipped rows')
    start_date = models.DateTimeField(null=True, blank=True, help_text='Data start date')
    end_date = models.DateTimeField(null=True, blank=True, help_text='Data end date')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True, help_text='Error message if failed')
    processing_time = models.FloatField(null=True, blank=True, help_text='Processing time in seconds')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'data_import_logs'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.file_name} - {self.symbol} - {self.timeframe} - {self.status}"

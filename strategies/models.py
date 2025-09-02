"""
Models for trading strategies and backtesting
"""

from django.db import models
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
import json


class Strategy(models.Model):
    """Trading strategy model"""
    
    name = models.CharField(max_length=200, help_text='Strategy name')
    description = models.TextField(blank=True, help_text='Strategy description')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='strategies')
    
    # Strategy configuration
    symbol = models.CharField(max_length=20, default='ES', help_text='Trading symbol')
    timeframe = models.CharField(max_length=3, default='5m', help_text='Data timeframe')
    
    # Entry rules (JSON format)
    entry_rules = models.JSONField(default=dict, help_text='Entry conditions')
    
    # Exit rules (JSON format)
    exit_rules = models.JSONField(default=dict, help_text='Exit conditions')
    
    # Risk management
    stop_loss_type = models.CharField(max_length=20, default='percentage', 
                                    choices=[('percentage', 'Percentage'), ('points', 'Points')])
    stop_loss_value = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.5'))
    
    take_profit_type = models.CharField(max_length=20, default='percentage',
                                      choices=[('percentage', 'Percentage'), ('points', 'Points')])
    take_profit_value = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('2.0'))
    
    # Status
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'strategies'
        ordering = ['-created_at']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.symbol} {self.timeframe})"


class BacktestResult(models.Model):
    """Backtest execution results"""
    
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='backtests')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='backtest_results')
    
    # Backtest settings
    start_date = models.DateTimeField(help_text='Backtest start date')
    end_date = models.DateTimeField(help_text='Backtest end date')
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('100000'))
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('4.00'))
    slippage = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.5'))
    
    # Performance metrics
    total_return = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))
    total_return_percent = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0'))
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    max_drawdown = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0'))
    max_drawdown_percent = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0'))
    
    # Trade statistics
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0'))
    
    profit_factor = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0'))
    avg_win = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    avg_loss = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    largest_win = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    largest_loss = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0'))
    
    # Rating and summary
    rating = models.CharField(max_length=20, default='Poor', 
                            choices=[('Poor', 'Poor'), ('Fair', 'Fair'), ('Good', 'Good'), 
                                   ('Very Good', 'Very Good'), ('Excellent', 'Excellent')])
    rating_color = models.CharField(max_length=7, default='#ff6b6b')
    summary_description = models.TextField(blank=True)
    
    # Execution details
    execution_time = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    data_source = models.CharField(max_length=20, default='database', 
                                 choices=[('database', 'Database'), ('parquet', 'Parquet')])
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'backtest_results'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.strategy.name} - {self.total_return_percent}% ({self.rating})"


class Trade(models.Model):
    """Individual trade from backtest"""
    
    backtest = models.ForeignKey(BacktestResult, on_delete=models.CASCADE, related_name='trades')
    
    # Trade details
    action = models.CharField(max_length=10, choices=[('buy', 'Buy'), ('sell', 'Sell')])
    entry_price = models.DecimalField(max_digits=10, decimal_places=2)
    exit_price = models.DecimalField(max_digits=10, decimal_places=2)
    entry_date = models.DateTimeField()
    exit_date = models.DateTimeField()
    quantity = models.IntegerField(default=1)
    
    # P&L calculation
    pnl = models.DecimalField(max_digits=10, decimal_places=2)
    commission = models.DecimalField(max_digits=10, decimal_places=2)
    slippage = models.DecimalField(max_digits=10, decimal_places=4)
    net_pnl = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Trade metadata
    reason = models.CharField(max_length=50, help_text='Exit reason (Take Profit, Stop Loss, etc.)')
    duration = models.BigIntegerField(help_text='Trade duration in milliseconds')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'trades'
        ordering = ['entry_date']
    
    def __str__(self):
        return f"{self.action.upper()} {self.entry_date.strftime('%Y-%m-%d %H:%M')} - P&L: {self.net_pnl}"
    
    @property
    def is_winning(self):
        return self.net_pnl > 0
    
    @property
    def is_losing(self):
        return self.net_pnl < 0
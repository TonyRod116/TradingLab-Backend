from django.db import models
from django.contrib.auth import get_user_model
from decimal import Decimal
from django.core.validators import MinValueValidator, MaxValueValidator
import json

User = get_user_model()

class Strategy(models.Model):
    """Modelo para estrategias de trading"""
    
    STRATEGY_STATUS = [
        ('DRAFT', 'Draft'),
        ('READY', 'Ready'),
        ('RUNNING', 'Running'),
        ('PAUSED', 'Paused'),
        ('STOPPED', 'Stopped'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strategies')
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    symbol = models.CharField(max_length=10)
    timeframe = models.CharField(max_length=10)
    
    # Entry and exit rules as JSON
    entry_rules = models.JSONField(default=list)
    exit_rules = models.JSONField(default=list)
    
    # Risk management
    stop_loss_type = models.CharField(max_length=20, default='percentage')
    stop_loss_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('2.0'))
    take_profit_type = models.CharField(max_length=20, default='percentage')
    take_profit_value = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('4.0'))
    
    # Capital and settings
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('100000.00'))
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=STRATEGY_STATUS, default='DRAFT')
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'name']
    
    def __str__(self):
        return f"{self.name} ({self.symbol})"

class BacktestResult(models.Model):
    """Modelo para resultados de backtests"""
    
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='backtests')
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    initial_capital = models.DecimalField(max_digits=15, decimal_places=2)
    
    # Performance metrics
    total_return = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.0000'))
    annualized_return = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.0000'))
    sharpe_ratio = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.0000'))
    max_drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.0000'))
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal('0.00'))
    profit_factor = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.0000'))
    
    # Trade statistics
    total_trades = models.IntegerField(default=0)
    winning_trades = models.IntegerField(default=0)
    losing_trades = models.IntegerField(default=0)
    
    # Additional metrics
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('4.00'))
    slippage = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.25'))
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Backtest {self.id} - {self.strategy.name}"

class Trade(models.Model):
    """Modelo para trades individuales"""
    
    TRADE_TYPES = [
        ('BUY', 'Buy'),
        ('SELL', 'Sell'),
    ]
    
    backtest = models.ForeignKey(BacktestResult, on_delete=models.CASCADE, related_name='trades')
    trade_type = models.CharField(max_length=4, choices=TRADE_TYPES, default='BUY')
    entry_time = models.DateTimeField(null=True, blank=True)
    exit_time = models.DateTimeField(null=True, blank=True)
    entry_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    exit_price = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    quantity = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.0000'))
    pnl = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    commission = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('4.00'))
    
    class Meta:
        ordering = ['entry_time']
    
    def __str__(self):
        return f"Trade {self.id} - {self.trade_type} {self.quantity} @ {self.entry_price}"

class EquityCurvePoint(models.Model):
    """Modelo para puntos de la curva de equity"""
    
    backtest = models.ForeignKey(BacktestResult, on_delete=models.CASCADE, related_name='equity_curve')
    timestamp = models.DateTimeField(null=True, blank=True)
    equity = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    drawdown = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.0000'))
    
    class Meta:
        ordering = ['timestamp']
    
    def __str__(self):
        return f"Equity {self.equity} @ {self.timestamp}"

class Favorite(models.Model):
    """Modelo para favoritos de usuarios"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='favorites')
    strategy = models.ForeignKey(Strategy, on_delete=models.CASCADE, related_name='favorited_by')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'strategy']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} favorited {self.strategy.name}"
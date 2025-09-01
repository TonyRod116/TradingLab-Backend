from django.db import models
from users.models import User
from django.core.validators import MinValueValidator, MaxValueValidator

class Strategy(models.Model):
    """Trading strategy model"""
    
    STRATEGY_TYPES = [
        ('trend_following', 'Trend Following'),
        ('mean_reversion', 'Mean Reversion'),
        ('breakout', 'Breakout'),
        ('scalping', 'Scalping'),
        ('swing', 'Swing Trading'),
        ('custom', 'Custom'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('active', 'Active'),
        ('paused', 'Paused'),
        ('archived', 'Archived'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strategies')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    strategy_type = models.CharField(max_length=20, choices=STRATEGY_TYPES, default='custom')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Strategy configuration
    symbol = models.CharField(max_length=20, default='ES', help_text='Trading symbol')
    timeframe = models.CharField(max_length=3, default='1m', help_text='Strategy timeframe')
    
    # Risk parameters
    position_size = models.DecimalField(max_digits=5, decimal_places=2, default=1.0,
                                      validators=[MinValueValidator(0.1), MaxValueValidator(100.0)],
                                      help_text='Position size in lots')
    max_positions = models.PositiveIntegerField(default=1, help_text='Max simultaneous positions')
    stop_loss_pips = models.PositiveIntegerField(default=50, help_text='Stop loss in pips')
    take_profit_pips = models.PositiveIntegerField(default=100, help_text='Take profit in pips')
    
    # Strategy rules (JSON)
    rules = models.JSONField(default=list, help_text='List of strategy rules')
    
    # Backtesting configuration
    backtest_enabled = models.BooleanField(default=True)
    backtest_start_date = models.DateTimeField(null=True, blank=True)
    backtest_end_date = models.DateTimeField(null=True, blank=True)
    
    # Performance metrics
    total_trades = models.PositiveIntegerField(default=0)
    winning_trades = models.PositiveIntegerField(default=0)
    losing_trades = models.PositiveIntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    profit_factor = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    max_drawdown = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Strategies'
    
    def __str__(self):
        return f"{self.name} ({self.symbol} {self.timeframe})"
    
    @property
    def is_active(self):
        return self.status == 'active'
    
    def calculate_win_rate(self):
        """Calculate win rate based on winning vs total trades"""
        if self.total_trades > 0:
            return (self.winning_trades / self.total_trades) * 100
        return 0.0

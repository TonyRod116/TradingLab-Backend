from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Strategy(models.Model):
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('csharp', 'C#'),
        ('fsharp', 'F#'),
    ]
    
    STATUS_CHOICES = [
        ('live', 'Live Trading'),
        ('paper', 'Paper Trading'),
        ('backtest', 'Backtest'),
        ('research', 'Research'),
    ]
    
    RISK_LEVEL_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('very_high', 'Very High'),
    ]
    
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='strategies')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    quantconnect_id = models.CharField(max_length=100, unique=True)
    language = models.CharField(max_length=10, choices=LANGUAGE_CHOICES, default='python')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='backtest')
    
    # Performance metrics
    sharpe_ratio = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    max_drawdown = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_trades = models.IntegerField(default=0)
    win_rate = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    total_return = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    
    # Sync information
    last_sync = models.DateTimeField(auto_now=True)
    is_synced = models.BooleanField(default=False)
    
    # Additional metadata
    tags = models.JSONField(default=list, blank=True)
    risk_level = models.CharField(max_length=20, choices=RISK_LEVEL_CHOICES, default='medium')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = 'Strategies'
        ordering = ['-last_sync']
    
    def __str__(self):
        return f"{self.title} - {self.owner.username}"
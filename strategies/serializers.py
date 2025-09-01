from rest_framework import serializers
from .models import Strategy
from users.serializers.common import OwnerSerializer

class StrategySerializer(serializers.ModelSerializer):
    """Serializer for trading strategies"""
    
    user = OwnerSerializer(read_only=True)
    
    # Calculated fields
    is_active = serializers.ReadOnlyField()
    win_rate_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'user', 'name', 'description', 'strategy_type', 'status',
            'symbol', 'timeframe', 'position_size', 'max_positions',
            'stop_loss_type', 'stop_loss_value', 'take_profit_type', 'take_profit_value',
            'round_turn_commissions', 'slippage', 'rules',
            'backtest_enabled', 'backtest_start_date', 'backtest_end_date',
            'total_trades', 'winning_trades', 'losing_trades',
            'win_rate', 'profit_factor', 'max_drawdown',
            'created_at', 'updated_at', 'is_active', 'win_rate_display',
            # Legacy fields
            'stop_loss_pips', 'take_profit_pips'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at',
                           'total_trades', 'winning_trades', 'losing_trades',
                           'win_rate', 'profit_factor', 'max_drawdown']
    
    def get_win_rate_display(self, obj):
        """Format win rate as percentage"""
        return f"{obj.win_rate:.2f}%" if obj.win_rate else "0.00%"
    
    def create(self, validated_data):
        """Create new strategy assigning current user"""
        user = self.context['request'].user
        validated_data['user'] = user
        return super().create(validated_data)

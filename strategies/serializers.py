"""
Serializers for trading strategies and backtesting
"""

from rest_framework import serializers
from decimal import Decimal
from .models import Strategy, BacktestResult, Trade


class TradeSerializer(serializers.ModelSerializer):
    """Serializer for individual trades"""
    
    class Meta:
        model = Trade
        fields = [
            'id', 'action', 'entry_price', 'exit_price', 'entry_date', 'exit_date',
            'quantity', 'pnl', 'commission', 'slippage', 'net_pnl', 'reason', 'duration'
        ]


class BacktestResultSerializer(serializers.ModelSerializer):
    """Serializer for backtest results"""
    
    trades = TradeSerializer(many=True, read_only=True)
    
    class Meta:
        model = BacktestResult
        fields = [
            'id', 'strategy', 'start_date', 'end_date', 'initial_capital',
            'commission', 'slippage', 'total_return', 'total_return_percent',
            'sharpe_ratio', 'max_drawdown', 'max_drawdown_percent',
            'total_trades', 'winning_trades', 'losing_trades', 'win_rate',
            'profit_factor', 'avg_win', 'avg_loss', 'largest_win', 'largest_loss',
            'rating', 'rating_color', 'summary_description', 'execution_time',
            'data_source', 'created_at', 'trades'
        ]


class BacktestResultSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for backtest results (without trades)"""
    
    class Meta:
        model = BacktestResult
        fields = [
            'id', 'strategy', 'start_date', 'end_date', 'initial_capital',
            'commission', 'slippage', 'total_return', 'total_return_percent',
            'sharpe_ratio', 'max_drawdown', 'max_drawdown_percent',
            'total_trades', 'winning_trades', 'losing_trades', 'win_rate',
            'profit_factor', 'avg_win', 'avg_loss', 'largest_win', 'largest_loss',
            'rating', 'rating_color', 'summary_description', 'execution_time',
            'data_source', 'created_at'
        ]


class StrategySerializer(serializers.ModelSerializer):
    """Serializer for trading strategies"""
    
    backtests = BacktestResultSerializer(many=True, read_only=True)
    backtest_count = serializers.SerializerMethodField()
    latest_backtest = serializers.SerializerMethodField()
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'description', 'symbol', 'timeframe', 'entry_rules',
            'exit_rules', 'stop_loss_type', 'stop_loss_value', 'take_profit_type',
            'take_profit_value', 'initial_capital', 'is_active', 'created_at', 'updated_at',
            'backtests', 'backtest_count', 'latest_backtest'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_backtest_count(self, obj):
        return obj.backtests.count()
    
    def get_latest_backtest(self, obj):
        latest = obj.backtests.first()
        if latest:
            return BacktestResultSerializer(latest).data
        return None


class StrategyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for strategy list (without backtests)"""
    
    backtest_count = serializers.SerializerMethodField()
    latest_backtest = serializers.SerializerMethodField()
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'description', 'symbol', 'timeframe', 'entry_rules',
            'exit_rules', 'stop_loss_type', 'stop_loss_value', 'take_profit_type',
            'take_profit_value', 'initial_capital', 'is_active', 'created_at', 'updated_at',
            'backtest_count', 'latest_backtest'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_backtest_count(self, obj):
        return obj.backtests.count()
    
    def get_latest_backtest(self, obj):
        latest = obj.backtests.first()
        if latest:
            return BacktestResultSummarySerializer(latest).data
        return None


class BacktestRequestSerializer(serializers.Serializer):
    """Serializer for backtest requests"""
    
    start_date = serializers.DateTimeField()
    end_date = serializers.DateTimeField()
    initial_capital = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    commission = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal('4.00'))
    slippage = serializers.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.5'))
    
    def validate(self, data):
        if data['start_date'] >= data['end_date']:
            raise serializers.ValidationError("Start date must be before end date")
        return data


class BacktestResponseSerializer(serializers.Serializer):
    """Serializer for backtest response"""
    
    strategy = StrategySerializer(read_only=True)
    settings = BacktestRequestSerializer(read_only=True)
    trades = TradeSerializer(many=True, read_only=True)
    performance = serializers.DictField(read_only=True)
    summary = serializers.DictField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)
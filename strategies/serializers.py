"""
Serializers for trading strategies and backtesting
"""

from rest_framework import serializers
from decimal import Decimal
from .models import Strategy, BacktestResult, Trade, EquityCurvePoint
from .enums import (
    SUPPORTED_SYMBOLS, SUPPORTED_TIMEFRAMES, SUPPORTED_INDICATORS, SUPPORTED_OPERATORS,
    STOP_LOSS_TYPES, TAKE_PROFIT_TYPES, STRATEGY_STATUS, RULE_TYPES, ACTION_TYPES, LOGICAL_OPERATORS
)


class RuleConditionSerializer(serializers.Serializer):
    """Serializer for rule conditions"""
    left_operand = serializers.ChoiceField(choices=SUPPORTED_INDICATORS, help_text='Left operand indicator')
    operator = serializers.ChoiceField(choices=SUPPORTED_OPERATORS, help_text='Comparison operator')
    right_operand = serializers.CharField(help_text='Right operand (indicator or value)')
    logical_operator = serializers.ChoiceField(choices=LOGICAL_OPERATORS, default='and', help_text='Logical operator for multiple conditions')


class RuleSerializer(serializers.Serializer):
    """Serializer for trading rules"""
    name = serializers.CharField(max_length=200, help_text='Rule name')
    rule_type = serializers.ChoiceField(choices=RULE_TYPES, help_text='Type of rule')
    action_type = serializers.ChoiceField(choices=ACTION_TYPES, required=False, help_text='Action type for action rules')
    conditions = RuleConditionSerializer(many=True, required=False, help_text='Rule conditions')
    priority = serializers.IntegerField(default=1, help_text='Rule priority')
    parameters = serializers.JSONField(default=dict, help_text='Additional rule parameters')


class StrategyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating strategies with validation"""
    
    # Override fields to use proper validation
    symbol = serializers.ChoiceField(choices=SUPPORTED_SYMBOLS, help_text='Trading symbol')
    timeframe = serializers.ChoiceField(choices=SUPPORTED_TIMEFRAMES, help_text='Data timeframe')
    stop_loss_type = serializers.ChoiceField(choices=STOP_LOSS_TYPES, help_text='Stop loss type')
    take_profit_type = serializers.ChoiceField(choices=TAKE_PROFIT_TYPES, help_text='Take profit type')
    status = serializers.ChoiceField(choices=STRATEGY_STATUS, default='DRAFT', help_text='Strategy status')
    
    # Entry and exit rules as arrays of rules
    entry_rules = RuleSerializer(many=True, help_text='Entry rules')
    exit_rules = RuleSerializer(many=True, help_text='Exit rules', required=False, allow_empty=True)
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'description', 'symbol', 'timeframe', 'entry_rules', 'exit_rules',
            'stop_loss_type', 'stop_loss_value', 'take_profit_type', 'take_profit_value',
            'initial_capital', 'status'
        ]
        read_only_fields = ['id']
    
    def validate(self, data):
        """Validate strategy data"""
        print(f"🔍 StrategyCreateSerializer.validate - Received data keys: {list(data.keys())}")
        print(f"🔍 StrategyCreateSerializer.validate - Entry rules: {data.get('entry_rules', [])}")
        print(f"🔍 StrategyCreateSerializer.validate - Exit rules: {data.get('exit_rules', [])}")
        print(f"🔍 StrategyCreateSerializer.validate - Exit rules type: {type(data.get('exit_rules', []))}")
        print(f"🔍 StrategyCreateSerializer.validate - Exit rules length: {len(data.get('exit_rules', []))}")
        
        # Check that entry rules exist
        if not data.get('entry_rules'):
            raise serializers.ValidationError("At least one entry rule is required")
        
        # Check that exit rules exist (optional - can use only stop loss and take profit)
        # if not data.get('exit_rules'):
        #     raise serializers.ValidationError("At least one exit rule is required")
        
        # Validate entry rules
        for i, rule in enumerate(data['entry_rules']):
            if rule['rule_type'] == 'condition' and not rule.get('conditions'):
                raise serializers.ValidationError(f"Entry rule {i+1}: Condition rules must have at least one condition")
        
        # Validate exit rules (only if they exist)
        exit_rules = data.get('exit_rules', [])
        if exit_rules:
            for i, rule in enumerate(exit_rules):
                if rule['rule_type'] == 'condition' and not rule.get('conditions'):
                    raise serializers.ValidationError(f"Exit rule {i+1}: Condition rules must have at least one condition")
        
        print(f"🔍 StrategyCreateSerializer.validate - Validation passed!")
        return data


class EquityCurvePointSerializer(serializers.ModelSerializer):
    """Serializer for equity curve points"""
    
    class Meta:
        model = EquityCurvePoint
        fields = [
            'timestamp', 'equity_value', 'drawdown', 'trade'
        ]


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
    equity_curve = EquityCurvePointSerializer(many=True, read_only=True)
    
    class Meta:
        model = BacktestResult
        fields = [
            'id', 'strategy', 'start_date', 'end_date', 'initial_capital',
            'commission', 'slippage', 'total_return', 'total_return_percent',
            'total_trades', 'winning_trades', 'losing_trades', 'win_rate',
            'profit_factor', 'avg_win', 'avg_loss', 'largest_win', 'largest_loss',
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'volatility',
            'max_drawdown', 'max_drawdown_percent', 'recovery_factor',
            'max_consecutive_wins', 'max_consecutive_losses', 'avg_trade_duration',
            'trades_per_month', 'expectancy', 'rating', 'rating_color', 
            'summary_description', 'execution_time', 'data_source', 'created_at', 
            'trades', 'equity_curve'
        ]


class BacktestResultSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for backtest results (without trades)"""
    
    class Meta:
        model = BacktestResult
        fields = [
            'id', 'strategy', 'start_date', 'end_date', 'initial_capital',
            'commission', 'slippage', 'total_return', 'total_return_percent',
            'total_trades', 'winning_trades', 'losing_trades', 'win_rate',
            'profit_factor', 'avg_win', 'avg_loss', 'largest_win', 'largest_loss',
            'sharpe_ratio', 'sortino_ratio', 'calmar_ratio', 'volatility',
            'max_drawdown', 'max_drawdown_percent', 'recovery_factor',
            'max_consecutive_wins', 'max_consecutive_losses', 'avg_trade_duration',
            'trades_per_month', 'expectancy', 'rating', 'rating_color', 
            'summary_description', 'execution_time', 'data_source', 'created_at'
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
            'take_profit_value', 'initial_capital', 'status', 'is_active', 'is_public', 'created_at', 'updated_at',
            'backtests', 'backtest_count', 'latest_backtest'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate(self, data):
        """Ensure required fields have default values if not provided"""
        if 'exit_rules' not in data or data['exit_rules'] is None:
            data['exit_rules'] = {}
        return data
    
    def get_backtest_count(self, obj):
        return obj.backtests.count()
    
    def get_latest_backtest(self, obj):
        latest = obj.backtests.first()
        if latest:
            return BacktestResultSerializer(latest).data
        return None


class StrategySummarySerializer(serializers.ModelSerializer):
    """Serializer for strategy summary with backtest metrics directly included"""
    
    created_by = serializers.CharField(source='user.username', read_only=True)
    
    # Backtest metrics directly in the strategy
    win_rate = serializers.SerializerMethodField()
    total_trades = serializers.SerializerMethodField()
    profit_factor = serializers.SerializerMethodField()
    max_drawdown = serializers.SerializerMethodField()
    sharpe_ratio = serializers.SerializerMethodField()
    total_return = serializers.SerializerMethodField()
    total_return_percent = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    rating_color = serializers.SerializerMethodField()
    
    def get_win_rate(self, obj):
        """Get win_rate from latest backtest as percentage"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.win_rate is not None:
            # Convert to percentage (0.4 -> 40)
            return float(latest_backtest.win_rate) * 100
        return None
    
    def get_total_trades(self, obj):
        """Get total_trades from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.total_trades is not None:
            return latest_backtest.total_trades
        return None
    
    def get_profit_factor(self, obj):
        """Get profit_factor from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.profit_factor is not None:
            return float(latest_backtest.profit_factor)
        return None
    
    def get_max_drawdown(self, obj):
        """Get max_drawdown_percent from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.max_drawdown_percent is not None:
            # max_drawdown_percent is already in percentage, just convert to float
            return float(latest_backtest.max_drawdown_percent)
        return None
    
    def get_sharpe_ratio(self, obj):
        """Get sharpe_ratio from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.sharpe_ratio is not None:
            return float(latest_backtest.sharpe_ratio)
        return None
    
    def get_total_return(self, obj):
        """Get total_return from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.total_return is not None:
            return float(latest_backtest.total_return)
        return None
    
    def get_total_return_percent(self, obj):
        """Get total_return_percent from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.total_return_percent is not None:
            return float(latest_backtest.total_return_percent)
        return None
    
    def get_rating(self, obj):
        """Get rating from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.rating:
            return latest_backtest.rating
        return None
    
    def get_rating_color(self, obj):
        """Get rating_color from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.rating_color:
            return latest_backtest.rating_color
        return None
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'description', 'symbol', 'timeframe', 
            'entry_rules', 'exit_rules', 'stop_loss_type', 'stop_loss_value', 
            'take_profit_type', 'take_profit_value', 'initial_capital', 
            'status', 'is_active', 'is_public', 'created_at', 'updated_at', 'created_by',
            # Backtest metrics
            'win_rate', 'total_trades', 'profit_factor', 'max_drawdown', 
            'sharpe_ratio', 'total_return', 'total_return_percent', 
            'rating', 'rating_color'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class StrategyListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for strategy list with backtest metrics"""
    
    created_by = serializers.CharField(source='user.username', read_only=True)
    backtest_count = serializers.SerializerMethodField()
    latest_backtest = serializers.SerializerMethodField()
    
    # Backtest metrics directly in the strategy
    win_rate = serializers.SerializerMethodField()
    total_trades = serializers.SerializerMethodField()
    profit_factor = serializers.SerializerMethodField()
    max_drawdown = serializers.SerializerMethodField()
    sharpe_ratio = serializers.SerializerMethodField()
    total_return = serializers.SerializerMethodField()
    total_return_percent = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    rating_color = serializers.SerializerMethodField()
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'description', 'symbol', 'timeframe', 'entry_rules',
            'exit_rules', 'stop_loss_type', 'stop_loss_value', 'take_profit_type',
            'take_profit_value', 'initial_capital', 'status', 'is_active', 'is_public', 'created_at', 'updated_at',
            'created_by', 'backtest_count', 'latest_backtest',
            # Backtest metrics
            'win_rate', 'total_trades', 'profit_factor', 'max_drawdown', 
            'sharpe_ratio', 'total_return', 'total_return_percent', 
            'rating', 'rating_color'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_backtest_count(self, obj):
        return obj.backtests.count()
    
    def get_latest_backtest(self, obj):
        latest = obj.backtests.first()
        if latest:
            return BacktestResultSummarySerializer(latest).data
        return None
    
    def get_win_rate(self, obj):
        """Get win_rate from latest backtest as percentage"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.win_rate is not None:
            # Convert to percentage (0.4 -> 40)
            return float(latest_backtest.win_rate) * 100
        return None
    
    def get_total_trades(self, obj):
        """Get total_trades from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.total_trades is not None:
            return latest_backtest.total_trades
        return None
    
    def get_profit_factor(self, obj):
        """Get profit_factor from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.profit_factor is not None:
            return float(latest_backtest.profit_factor)
        return None
    
    def get_max_drawdown(self, obj):
        """Get max_drawdown_percent from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.max_drawdown_percent is not None:
            # max_drawdown_percent is already in percentage, just convert to float
            return float(latest_backtest.max_drawdown_percent)
        return None
    
    def get_sharpe_ratio(self, obj):
        """Get sharpe_ratio from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.sharpe_ratio is not None:
            return float(latest_backtest.sharpe_ratio)
        return None
    
    def get_total_return(self, obj):
        """Get total_return from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.total_return is not None:
            return float(latest_backtest.total_return)
        return None
    
    def get_total_return_percent(self, obj):
        """Get total_return_percent from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.total_return_percent is not None:
            return float(latest_backtest.total_return_percent)
        return None
    
    def get_rating(self, obj):
        """Get rating from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.rating:
            return latest_backtest.rating
        return None
    
    def get_rating_color(self, obj):
        """Get rating_color from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.rating_color:
            return latest_backtest.rating_color
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
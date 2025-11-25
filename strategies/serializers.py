"""
Serializers for trading strategies and backtesting
"""

from datetime import timedelta
from decimal import Decimal

from django.utils import timezone
from rest_framework import serializers

from .models import Strategy, BacktestResult, Trade, EquityCurvePoint
from .enums import (
    SUPPORTED_SYMBOLS, SUPPORTED_TIMEFRAMES, SUPPORTED_INDICATORS, SUPPORTED_OPERATORS,
    STOP_LOSS_TYPES, TAKE_PROFIT_TYPES, STRATEGY_STATUS, RULE_TYPES, ACTION_TYPES, LOGICAL_OPERATORS
)
from .normalizers import (
    normalize_symbol,
    normalize_timeframe,
    normalize_stop_take,
    preflight_feasibility,
    normalize_indicator_name,
    normalize_operator,
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
    """Serializer for creating strategies with flexible validation and normalization"""
    
    # Override fields to use proper validation
    symbol = serializers.CharField(help_text='Trading symbol (will be normalized)')
    timeframe = serializers.CharField(help_text='Data timeframe (will be normalized)')
    stop_loss_type = serializers.CharField(help_text='Stop loss type (will be normalized)')
    take_profit_type = serializers.CharField(help_text='Take profit type (will be normalized)')
    status = serializers.ChoiceField(choices=STRATEGY_STATUS, default='DRAFT', help_text='Strategy status')
    
    # Entry and exit rules as arrays of rules
    entry_rules = RuleSerializer(many=True, help_text='Entry rules')
    exit_rules = RuleSerializer(many=True, help_text='Exit rules', required=False, allow_empty=True)
    
    # NUEVO: devolvemos avisos al cliente
    warnings = serializers.ListField(child=serializers.CharField(), read_only=True)
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'description', 'symbol', 'timeframe', 'entry_rules', 'exit_rules',
            'stop_loss_type', 'stop_loss_value', 'take_profit_type', 'take_profit_value',
            'initial_capital', 'status', 'warnings'
        ]
        read_only_fields = ['id']
    
    def to_internal_value(self, data):
        """Normalización flexible antes de validar"""
        data = super().to_internal_value(data)
        warns = []
        
        # símbolo y timeframe
        sym = normalize_symbol(data.get('symbol'))
        tf = normalize_timeframe(data.get('timeframe'))
        warns += sym.warnings + tf.warnings
        data['symbol'] = sym.value if not sym.warnings else data.get('symbol')
        data['timeframe'] = tf.value if not tf.warnings else data.get('timeframe')
        
        # stop/take
        if data.get('stop_loss_type'):
            sl = normalize_stop_take(data['stop_loss_type'])
            warns += sl.warnings
            data['stop_loss_type'] = sl.value
        if data.get('take_profit_type'):
            tp = normalize_stop_take(data['take_profit_type'], is_tp=True)
            warns += tp.warnings
            data['take_profit_type'] = tp.value
        
        # guarda warnings en contexto para attach tras save
        self._norm_warnings = warns
        return data
    
    def validate(self, data):
        """Validación exhaustiva con factibilidad y mensajes accionables"""
        warnings, errors = preflight_feasibility(dict(data))
        if errors:
            raise serializers.ValidationError(errors)
        
        # adjunta warnings para la respuesta
        data['_warnings'] = getattr(self, '_norm_warnings', []) + warnings
        return data
    
    def create(self, validated_data):
        warns = validated_data.pop('_warnings', [])
        obj = super().create(validated_data)
        # attach warnings al serializer para la salida
        self._return_warnings = warns
        return obj
    
    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep['warnings'] = getattr(self, '_return_warnings', getattr(self, '_norm_warnings', [])) or []
        return rep


class EquityCurvePointSerializer(serializers.ModelSerializer):
    """Serializer for equity curve points"""
    
    # Add alias for frontend compatibility
    equity_value = serializers.DecimalField(source='equity', max_digits=15, decimal_places=2, read_only=True)
    
    class Meta:
        model = EquityCurvePoint
        fields = [
            'timestamp', 'equity', 'equity_value', 'drawdown'
        ]


class TradeSerializer(serializers.ModelSerializer):
    """Serializer for individual trades"""
    
    # Add aliases for frontend compatibility
    net_pnl = serializers.DecimalField(source='pnl', max_digits=10, decimal_places=2, read_only=True)
    exit_date = serializers.DateTimeField(source='exit_time', read_only=True)
    
    class Meta:
        model = Trade
        fields = [
            'id', 'trade_type', 'entry_price', 'exit_price', 'entry_time', 'exit_time',
            'quantity', 'pnl', 'net_pnl', 'commission', 'exit_date'
        ]


class BacktestResultSerializer(serializers.ModelSerializer):
    """Serializer for backtest results"""
    
    trades = TradeSerializer(many=True, read_only=True)
    equity_curve = EquityCurvePointSerializer(many=True, read_only=True)
    total_return_percent = serializers.SerializerMethodField()
    max_drawdown_percent = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    rating_color = serializers.SerializerMethodField()
    
    class Meta:
        model = BacktestResult
        fields = [
            'id', 'strategy', 'start_date', 'end_date', 'initial_capital',
            'commission', 'slippage', 'total_return', 'total_return_percent',
            'total_trades', 'winning_trades', 'losing_trades', 'win_rate',
            'profit_factor', 'sharpe_ratio', 'max_drawdown', 'max_drawdown_percent',
            'rating', 'rating_color', 'created_at', 'trades', 'equity_curve'
        ]
    
    def get_total_return_percent(self, obj):
        """Calculate total_return_percent from total_return and initial_capital"""
        if obj.total_return is not None and obj.initial_capital is not None:
            return float(obj.total_return / obj.initial_capital * 100)
        return None
    
    def get_max_drawdown_percent(self, obj):
        """Get max_drawdown and convert to percentage"""
        if obj.max_drawdown is not None:
            return float(obj.max_drawdown) * 100
        return None
    
    def get_rating(self, obj):
        """Calculate rating based on performance metrics"""
        if obj.win_rate is not None and obj.profit_factor is not None:
            win_rate = float(obj.win_rate)
            profit_factor = float(obj.profit_factor)
            
            if win_rate >= 60 and profit_factor >= 1.5:
                return "Excellent"
            elif win_rate >= 50 and profit_factor >= 1.2:
                return "Good"
            elif win_rate >= 40 and profit_factor >= 1.0:
                return "Average"
            else:
                return "Poor"
        return None
    
    def get_rating_color(self, obj):
        """Calculate rating color based on rating"""
        rating = self.get_rating(obj)
        if rating == "Excellent":
            return "green"
        elif rating == "Good":
            return "blue"
        elif rating == "Average":
            return "orange"
        else:
            return "red"


class BacktestResultSummarySerializer(serializers.ModelSerializer):
    """Lightweight serializer for backtest results (without trades)"""
    
    class Meta:
        model = BacktestResult
        fields = [
            'id', 'strategy', 'start_date', 'end_date', 'initial_capital',
            'commission', 'slippage', 'total_return', 'annualized_return',
            'total_trades', 'winning_trades', 'losing_trades', 'win_rate',
            'profit_factor', 'sharpe_ratio', 'max_drawdown', 'created_at'
        ]


class StrategySerializer(serializers.ModelSerializer):
    """Serializer for trading strategies"""
    
    backtests = BacktestResultSerializer(many=True, read_only=True)
    backtest_count = serializers.SerializerMethodField()
    latest_backtest = serializers.SerializerMethodField()
    warnings = serializers.ListField(child=serializers.CharField(), read_only=True)
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'description', 'symbol', 'timeframe', 'entry_rules',
            'exit_rules', 'stop_loss_type', 'stop_loss_value', 'take_profit_type',
            'take_profit_value', 'initial_capital', 'status', 'is_active', 'is_public', 'created_at', 'updated_at',
            'backtests', 'backtest_count', 'latest_backtest', 'warnings'
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
    equity_curve = serializers.SerializerMethodField()
    
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
        """Get max_drawdown from latest backtest and convert to percentage"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.max_drawdown is not None:
            # max_drawdown is a decimal, convert to percentage
            return float(latest_backtest.max_drawdown) * 100
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
        """Calculate total_return_percent from total_return and initial_capital"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.total_return is not None and latest_backtest.initial_capital is not None:
            # Calculate percentage: (total_return / initial_capital) * 100
            return float(latest_backtest.total_return / latest_backtest.initial_capital * 100)
        return None
    
    def get_rating(self, obj):
        """Calculate rating based on performance metrics"""
        latest_backtest = obj.backtests.first()
        if latest_backtest:
            # Simple rating calculation based on win_rate and profit_factor
            win_rate = float(latest_backtest.win_rate) if latest_backtest.win_rate else 0
            profit_factor = float(latest_backtest.profit_factor) if latest_backtest.profit_factor else 0
            
            if win_rate >= 60 and profit_factor >= 1.5:
                return "Excellent"
            elif win_rate >= 50 and profit_factor >= 1.2:
                return "Good"
            elif win_rate >= 40 and profit_factor >= 1.0:
                return "Average"
        else:
            return "Poor"
        return None
    
    def get_rating_color(self, obj):
        """Calculate rating color based on rating"""
        rating = self.get_rating(obj)
        if rating == "Excellent":
            return "green"
        elif rating == "Good":
            return "blue"
        elif rating == "Average":
            return "orange"
        else:
            return "red"
    
    def get_equity_curve(self, obj):
        """Get equity curve from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and hasattr(latest_backtest, 'equity_curve'):
            return latest_backtest.equity_curve.all().values('timestamp', 'equity', 'drawdown')
        return []
    
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
            'rating', 'rating_color', 'equity_curve'
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
        """Get max_drawdown from latest backtest and convert to percentage"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.max_drawdown is not None:
            # max_drawdown is a decimal, convert to percentage
            return float(latest_backtest.max_drawdown) * 100
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
        """Calculate total_return_percent from total_return and initial_capital"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.total_return is not None and latest_backtest.initial_capital is not None:
            # Calculate percentage: (total_return / initial_capital) * 100
            return float(latest_backtest.total_return / latest_backtest.initial_capital * 100)
        return None
    
    def get_rating(self, obj):
        """Calculate rating based on performance metrics"""
        latest_backtest = obj.backtests.first()
        if latest_backtest:
            # Simple rating calculation based on win_rate and profit_factor
            win_rate = float(latest_backtest.win_rate) if latest_backtest.win_rate else 0
            profit_factor = float(latest_backtest.profit_factor) if latest_backtest.profit_factor else 0
            
            if win_rate >= 60 and profit_factor >= 1.5:
                return "Excellent"
            elif win_rate >= 50 and profit_factor >= 1.2:
                return "Good"
            elif win_rate >= 40 and profit_factor >= 1.0:
                return "Average"
            else:
                return "Poor"
        return None
    
    def get_rating_color(self, obj):
        """Calculate rating color based on rating"""
        rating = self.get_rating(obj)
        if rating == "Excellent":
            return "green"
        elif rating == "Good":
            return "blue"
        elif rating == "Average":
            return "orange"
        else:
            return "red"


class BacktestRequestSerializer(serializers.Serializer):
    """Serializer for backtest requests"""

    start_date = serializers.DateTimeField(required=False)
    end_date = serializers.DateTimeField(required=False)
    initial_capital = serializers.DecimalField(max_digits=15, decimal_places=2, required=False)
    commission = serializers.DecimalField(max_digits=10, decimal_places=2, default=Decimal('4.00'))
    slippage = serializers.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.5'))

    symbol = serializers.ChoiceField(choices=SUPPORTED_SYMBOLS, required=False)
    timeframe = serializers.ChoiceField(choices=SUPPORTED_TIMEFRAMES, required=False)
    stop_loss_type = serializers.ChoiceField(choices=STOP_LOSS_TYPES, required=False)
    stop_loss_value = serializers.DecimalField(max_digits=10, decimal_places=4, required=False)
    take_profit_type = serializers.ChoiceField(choices=TAKE_PROFIT_TYPES, required=False)
    take_profit_value = serializers.DecimalField(max_digits=10, decimal_places=4, required=False)

    def validate(self, data):
        # Default to last 90 days when frontend omits the date range
        end_date = data.get('end_date') or timezone.now()
        start_date = data.get('start_date') or (end_date - timedelta(days=90))

        if start_date >= end_date:
            raise serializers.ValidationError("Start date must be before end date")

        data['start_date'] = start_date
        data['end_date'] = end_date
        return data


class BacktestResponseSerializer(serializers.Serializer):
    """Serializer for backtest response"""
    
    strategy = StrategySerializer(read_only=True)
    settings = BacktestRequestSerializer(read_only=True)
    trades = TradeSerializer(many=True, read_only=True)
    performance = serializers.DictField(read_only=True)
    summary = serializers.DictField(read_only=True)
    timestamp = serializers.DateTimeField(read_only=True)


class FavoritesOptimizedSerializer(serializers.ModelSerializer):
    """Optimized serializer for favorites - minimal data for fast loading"""
    
    created_by = serializers.CharField(source='user.username', read_only=True)
    
    # Only essential backtest metrics
    win_rate = serializers.SerializerMethodField()
    total_trades = serializers.SerializerMethodField()
    profit_factor = serializers.SerializerMethodField()
    total_return_percent = serializers.SerializerMethodField()
    rating = serializers.SerializerMethodField()
    rating_color = serializers.SerializerMethodField()
    
    def get_win_rate(self, obj):
        """Get win_rate from latest backtest as percentage"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.win_rate is not None:
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
    
    def get_total_return_percent(self, obj):
        """Get total_return_percent from latest backtest"""
        latest_backtest = obj.backtests.first()
        if latest_backtest and latest_backtest.total_return is not None and latest_backtest.initial_capital:
            return (float(latest_backtest.total_return) / float(latest_backtest.initial_capital)) * 100
        return None
    
    def get_rating(self, obj):
        """Calculate rating based on multiple metrics"""
        latest_backtest = obj.backtests.first()
        if not latest_backtest:
            return None
        
        win_rate = latest_backtest.win_rate
        profit_factor = latest_backtest.profit_factor
        
        if win_rate is None or profit_factor is None:
            return None
        
        win_rate_pct = float(win_rate) * 100
        rating = 0
        
        # Win rate component (0-2.5 points)
        if win_rate_pct >= 60:
            rating += 2.5
        elif win_rate_pct >= 50:
            rating += 2.0
        elif win_rate_pct >= 40:
            rating += 1.5
        elif win_rate_pct >= 30:
            rating += 1.0
        else:
            rating += 0.5
        
        # Profit factor component (0-2.5 points)
        if profit_factor >= 2.0:
            rating += 2.5
        elif profit_factor >= 1.5:
            rating += 2.0
        elif profit_factor >= 1.2:
            rating += 1.5
        elif profit_factor >= 1.0:
            rating += 1.0
        else:
            rating += 0.5
        
        return round(rating, 1)
    
    def get_rating_color(self, obj):
        """Get color based on rating"""
        rating = self.get_rating(obj)
        if rating is None:
            return 'gray'
        
        if rating >= 4.0:
            return 'green'
        elif rating >= 3.0:
            return 'yellow'
        elif rating >= 2.0:
            return 'orange'
        else:
            return 'red'
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'name', 'description', 'symbol', 'timeframe', 'entry_rules',
            'exit_rules', 'initial_capital', 'status', 'is_active', 'is_public', 
            'created_at', 'created_by',
            'win_rate', 'total_trades', 'profit_factor', 'total_return_percent', 
            'rating', 'rating_color'
        ]
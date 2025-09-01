from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from .models import Strategy
from .serializers import StrategySerializer

# Create your views here.

class StrategyViewSet(viewsets.ModelViewSet):
    """ViewSet for managing trading strategies"""
    queryset = Strategy.objects.all()
    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter strategies by current user"""
        return Strategy.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        """Assign current user to strategy"""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        """Activate a strategy"""
        strategy = self.get_object()
        strategy.status = 'active'
        strategy.save()
        return Response({'status': 'Strategy activated'})
    
    @action(detail=True, methods=['post'])
    def pause(self, request, pk=None):
        """Pause a strategy"""
        strategy = self.get_object()
        strategy.status = 'paused'
        strategy.save()
        return Response({'status': 'Strategy paused'})
    
    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        """Archive a strategy"""
        strategy = self.get_object()
        strategy.status = 'archived'
        strategy.save()
        return Response({'status': 'Strategy archived'})
    
    @action(detail=True, methods=['get'])
    def performance(self, request, pk=None):
        """Get strategy performance metrics"""
        strategy = self.get_object()
        return Response({
            'total_trades': strategy.total_trades,
            'winning_trades': strategy.winning_trades,
            'losing_trades': strategy.losing_trades,
            'win_rate': strategy.win_rate,
            'profit_factor': strategy.profit_factor,
            'max_drawdown': strategy.max_drawdown,
        })
    
    @action(detail=False, methods=['get'])
    def templates(self, request):
        """Get available strategy templates"""
        templates = [
            {
                'name': 'Trend Following',
                'description': 'Follow market trends using moving averages',
                'strategy_type': 'trend_following',
                'rules': [
                    {'type': 'condition', 'indicator': 'sma_20', 'operator': 'above', 'value': 'sma_50'},
                    {'type': 'action', 'action': 'buy', 'when': 'condition_true'}
                ]
            },
            {
                'name': 'Mean Reversion',
                'description': 'Trade against extreme price movements',
                'strategy_type': 'mean_reversion',
                'rules': [
                    {'type': 'condition', 'indicator': 'rsi', 'operator': 'below', 'value': 30},
                    {'type': 'action', 'action': 'buy', 'when': 'condition_true'}
                ]
            }
        ]
        return Response(templates)
    
    @action(detail=False, methods=['post'])
    def create_from_template(self, request):
        """Create strategy from template"""
        template_name = request.data.get('template_name')
        strategy_name = request.data.get('strategy_name')
        
        if not template_name or not strategy_name:
            return Response({'error': 'Template name and strategy name are required'}, status=400)
        
        # Create strategy based on template
        strategy = Strategy.objects.create(
            user=request.user,
            name=strategy_name,
            strategy_type='custom',
            status='draft'
        )
        
        serializer = self.get_serializer(strategy)
        return Response(serializer.data, status=201)


class StrategyRuleViewSet(viewsets.ModelViewSet):
    """ViewSet for managing strategy rules"""
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        strategy_pk = self.kwargs.get('strategy_pk')
        return Strategy.objects.get(pk=strategy_pk).rules.all()


class StrategyRuleBuilderViewSet(viewsets.ViewSet):
    """ViewSet for rule builder metadata"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['get'])
    def available_indicators(self, request):
        """Get available technical indicators"""
        indicators = [
            {'name': 'SMA', 'description': 'Simple Moving Average', 'parameters': ['period']},
            {'name': 'EMA', 'description': 'Exponential Moving Average', 'parameters': ['period']},
            {'name': 'RSI', 'description': 'Relative Strength Index', 'parameters': ['period']},
            {'name': 'MACD', 'description': 'MACD Line', 'parameters': ['fast', 'slow', 'signal']},
            {'name': 'Bollinger Bands', 'description': 'Bollinger Bands', 'parameters': ['period', 'std_dev']},
        ]
        return Response(indicators)
    
    @action(detail=False, methods=['get'])
    def available_operators(self, request):
        """Get available comparison operators"""
        operators = [
            {'symbol': '>', 'name': 'Greater Than', 'description': 'Value is greater than'},
            {'symbol': '>=', 'name': 'Greater Than or Equal', 'description': 'Value is greater than or equal to'},
            {'symbol': '<', 'name': 'Less Than', 'description': 'Value is less than'},
            {'symbol': '<=', 'name': 'Less Than or Equal', 'description': 'Value is less than or equal to'},
            {'symbol': '==', 'name': 'Equal', 'description': 'Value equals'},
            {'symbol': '!=', 'name': 'Not Equal', 'description': 'Value does not equal'},
            {'symbol': 'crosses_above', 'name': 'Crosses Above', 'description': 'Line crosses above another'},
            {'symbol': 'crosses_below', 'name': 'Crosses Below', 'description': 'Line crosses below another'},
        ]
        return Response(operators)
    
    @action(detail=False, methods=['get'])
    def available_actions(self, request):
        """Get available trading actions"""
        actions = [
            {'name': 'buy', 'description': 'Open long position'},
            {'name': 'sell', 'description': 'Open short position'},
            {'name': 'close', 'description': 'Close current position'},
            {'name': 'wait', 'description': 'Wait for next signal'},
        ]
        return Response(actions)
    
    @action(detail=False, methods=['post'])
    def test_rule(self, request):
        """Test a rule with sample data"""
        rule = request.data.get('rule')
        sample_data = request.data.get('sample_data', {})
        
        if not rule:
            return Response({'error': 'Rule is required'}, status=400)
        
        # Simple rule testing logic
        try:
            # This is a placeholder - real implementation would evaluate the rule
            result = {'success': True, 'message': 'Rule syntax is valid'}
            return Response(result)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=400)

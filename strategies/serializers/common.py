from rest_framework import serializers
from users.models import User
from strategies.models import Strategy

class StrategySerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source='owner.username', read_only=True)
    
    class Meta:
        model = Strategy
        fields = [
            'id', 'title', 'description', 'owner', 'created_at',
            'quantconnect_id', 'language', 'status',
            'sharpe_ratio', 'max_drawdown', 'total_trades', 
            'win_rate', 'total_return', 'last_sync', 'is_synced'
        ]
        read_only_fields = ['id', 'owner', 'created_at', 'last_sync', 'is_synced']

class UserProfileSerializer(serializers.ModelSerializer):
    strategies = StrategySerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_image', 'bio', 'created_at', 'strategies']
        read_only_fields = ['id', 'username', 'email', 'created_at']
from rest_framework import serializers
from users.models import User
from strategies.models import Strategy

class StrategySerializer(serializers.ModelSerializer):
    class Meta:
        model = Strategy
        fields = ['id', 'title', 'description', 'created_at']

class UserProfileSerializer(serializers.ModelSerializer):
    strategies = StrategySerializer(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'profile_image', 'bio', 'created_at', 'strategies']
        read_only_fields = ['id', 'username', 'email', 'created_at']
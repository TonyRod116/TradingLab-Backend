from rest_framework import serializers
from users.models import User

class AuthSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirmPassword = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'password', 'confirmPassword']
    
    def validate(self, data):
        if data['password'] != data['confirmPassword']:
            raise serializers.ValidationError({
                'password': 'Passwords do not match'
            })
        return data
    
    def create(self, validated_data):
        validated_data.pop('confirmPassword')
        return User.objects.create_user(**validated_data)


class OwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']
from rest_framework import serializers
# from rest_framework.serializers import ModelSerializer
from ..models import User

class AuthSerializer(serializers.ModelSerializer):
  # To enforce the password and pssword_confirmation fields are READ ONLY (we won't see the password serializing users later), 
  # we override the password class attribute, setting the write_only=True setting

  password = serializers.CharField(write_only=True)
  passwordConfirm = serializers.CharField(write_only=True)

  class Meta:
    model = User
    # fields = ['id', 'username', 'email', 'password', 'password_confirmation', 'bio']
    fields = ['id', 'username', 'email', 'password', 'passwordConfirm', 'bio']

  # def validate_email(self, value):
  #   if 'email.com' in value.lower():
  #     raise serializers.ValidationError("Email must contain .com")
  #   return value

  def validate(self, data):
    if data['password'] != data['passwordConfirm']:
      raise serializers.ValidationError({ 'password': 'Passwords do not match' })
    return data

  def create(self, validated_data):
    validated_data.pop('passwordConfirm')
    print('VD:', validated_data)
    return User.objects.create_user(**validated_data)


class OwnerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username']
from django.shortcuts import render
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken

# Path: /users/sign-up
class SignUpView(APIView):

  def post(self, request):
    serialized_user = AuthSerializer(data=request.data)
    serialized_user.is_valid(raise_exception=True)
    serialized_user.save()

    # Optionally, you can generate an access token on sign up too

    # First, find the user object instance
    user = User.objects.get(pk=serialized_user.data['id'])

    # Use that user object to generate a token
    refresh = RefreshToken.for_user(user)

    # Finally, send the token with your response
    return Response({'access': str(refresh.access_token)}, 201)


class SignInView(APIView):
  def post(self, request):
    # print(request.data)
    return Response({"message": "HIT LOGIN ROUTE"})
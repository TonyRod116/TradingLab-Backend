from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.serializers.common import AuthSerializer, OwnerSerializer, ProfileSerializer, ProfileUpdateSerializer
from users.models import User
from rest_framework_simplejwt.tokens import RefreshToken

class SignUpView(APIView):
    def post(self, request):
        serialized_user = AuthSerializer(data=request.data)
        serialized_user.is_valid(raise_exception=True)
        serialized_user.save()
        
        user = User.objects.get(pk=serialized_user.data['id'])
        refresh = RefreshToken.for_user(user)
        
        return Response({'access': str(refresh.access_token)}, 201)

class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user
        serializer = ProfileSerializer(user)
        return Response(serializer.data)
    
    def put(self, request):
        user = request.user
        serializer = ProfileUpdateSerializer(user, data=request.data, partial=True)
        
        if serializer.is_valid():
            serializer.save()
            profile_serializer = ProfileSerializer(user)
            return Response(profile_serializer.data)
        else:
            return Response(serializer.errors, status=400)

class UserDetailView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            serializer = OwnerSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


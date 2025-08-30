from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from users.serializers.common import AuthSerializer, OwnerSerializer, ProfileSerializer
from users.models import User
from rest_framework_simplejwt.tokens import RefreshToken


class SignUpView(APIView):
    # User registration endpoint
    
    def post(self, request):
        serialized_user = AuthSerializer(data=request.data)
        serialized_user.is_valid(raise_exception=True)
        serialized_user.save()
        
        user = User.objects.get(pk=serialized_user.data['id'])
        refresh = RefreshToken.for_user(user)
        
        return Response({'access': str(refresh.access_token)}, 201)


class SignInView(APIView):
    # User authentication endpoint
    
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        
        if not username or not password:
            return Response({
                'error': 'Both username and password are required'
            }, status=400)
        
        # Find user by username
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            return Response({
                'error': 'No user found with this username'
            }, status=400)
        
        # Verify password
        if not user.check_password(password):
            return Response({
                'error': 'Invalid password'
            }, status=400)
        
        # User authenticated successfully
        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id': user.id,
                'username': user.username,
                'email': user.email
            }
        })


class UserProfileView(APIView):
    # Public user profile endpoint
    
    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
            serializer = ProfileSerializer(user)
            return Response(serializer.data)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)


class EditProfileView(APIView):
    # User profile management endpoint
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Get current user's profile data
        serializer = ProfileSerializer(request.user)
        return Response(serializer.data)
    
    def put(self, request):
        # Update current user's profile
        try:
            user = request.user
            data = request.data.copy()
            
            # Handle profile image separately
            if 'profile_image' in request.FILES:
                # File upload case
                profile_image = request.FILES['profile_image']
                # Save file locally (Cloudinary integration can be added later)
                user.profile_image = f"/media/profile_images/{profile_image.name}"
                # Save file to media directory
                import os
                os.makedirs('media/profile_images', exist_ok=True)
                with open(f'media/profile_images/{profile_image.name}', 'wb+') as destination:
                    for chunk in profile_image.chunks():
                        destination.write(chunk)
            
            elif 'profile_image' in data and data['profile_image'] not in ['', 'not provided', None]:
                # URL case (Cloudinary or other)
                user.profile_image = data['profile_image']
            
            # Update other fields
            if 'bio' in data:
                user.bio = data['bio']
            
            user.save()
            
            serializer = ProfileSerializer(user)
            return Response(serializer.data)
            
        except Exception as e:
            return Response({
                'error': f'Failed to update profile: {str(e)}'
            }, status=400)
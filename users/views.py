from rest_framework.views import APIView
from rest_framework.response import Response
from users.serializers.common import AuthSerializer
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

class SignInView(APIView):
  
    def post(self, request):
        identifier = request.data.get('identifier')  # Puede ser username o email
        password = request.data.get('password')
        
        if not identifier or not password:
            return Response({
                'error': 'Both identifier and password are required'
            }, status=400)
        
        # Buscar usuario por username o email
        try:
            user = User.objects.get(username=identifier)
        except User.DoesNotExist:
            try:
                user = User.objects.get(email=identifier)
            except User.DoesNotExist:
                return Response({
                    'error': 'No user found with this username or email'
                }, status=400)
        
        # Verificar contraseña
        if not user.check_password(password):
            return Response({
                'error': 'Invalid password'
            }, status=400)
        
        # Usuario autenticado correctamente
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


from django.urls import path
from .views import SignUpView, SignInView, UserProfileView, EditProfileView

app_name = 'users'

urlpatterns = [
    # Authentication endpoints
    path('signup/', SignUpView.as_view(), name='user-signup'),
    path('login/', SignInView.as_view(), name='user-login'),
    
    # Profile management endpoints
    path('profile/', EditProfileView.as_view(), name='user-profile'),
    path('profile/<int:user_id>/', UserProfileView.as_view(), name='user-profile-detail'),
]
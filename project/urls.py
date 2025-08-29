from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from users.views import UserProfileView, EditProfileView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('profile/<int:user_id>/', UserProfileView.as_view(), name='user_profile'),
    path('profile/edit/', EditProfileView.as_view(), name='edit_profile'),

    path('users/', include('users.urls')),
    path('strategies/', include('strategies.urls')),
    path('backtests/', include('backtests.urls')),
]
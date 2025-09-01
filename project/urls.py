
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth routes (matching frontend expectations)
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Main routes (matching frontend expectations)
    path('strategies/', include('strategies.urls')),
    path('users/', include('users.urls')),
    path('backtests/', include('backtests.urls')),
    
    # Keep API routes for backward compatibility
    path('api/token/', TokenObtainPairView.as_view(), name='api_token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/strategies/', include('strategies.urls')),
    path('api/users/', include('users.urls')),
    path('api/backtests/', include('backtests.urls')),
]
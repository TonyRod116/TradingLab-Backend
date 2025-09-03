
from django.contrib import admin
from django.urls import path, include
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from quantconnect_views import test_quantconnect_auth, test_project_creation, create_project, run_backtest

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # Auth routes (matching frontend expectations)
    path('auth/login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # Keep API routes for backward compatibility
    path('api/token/', TokenObtainPairView.as_view(), name='api_token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='api_token_refresh'),
    path('api/strategies/', include('strategies.urls')),
    path('api/users/', include('users.urls')),
    path('api/backtests/', include('backtests.urls')),
    path('api/market-data/', include('market_data.urls')),
    
    # QuantConnect API endpoints
    path('api/quantconnect/test-auth/', test_quantconnect_auth, name='quantconnect_test_auth'),
    path('api/quantconnect/test-project/', test_project_creation, name='quantconnect_test_project'),
    path('api/quantconnect/create-project/', create_project, name='quantconnect_create_project'),
    path('api/quantconnect/run-backtest/', run_backtest, name='quantconnect_run_backtest'),
]
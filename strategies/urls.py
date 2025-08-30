from django.urls import path
from .views import StrategyView, StrategyDetailView, QuantConnectSyncView

urlpatterns = [
    path('', StrategyView.as_view(), name='strategy-list'),
    path('<int:pk>/', StrategyDetailView.as_view(), name='strategy-detail'),
    path('sync-quantconnect/', QuantConnectSyncView.as_view(), name='quantconnect-sync'),
]
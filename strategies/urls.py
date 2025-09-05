"""
URLs for trading strategies and backtesting
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StrategyViewSet, BacktestResultViewSet, TradeViewSet, NLToStrategyView, RunBacktestView, QuantConnectBacktestView, QuantConnectProgressView, QuantConnectStrategyStatusView

router = DefaultRouter()
router.register('', StrategyViewSet, basename='strategy')
router.register(r'backtest-results', BacktestResultViewSet, basename='backtest-result')
router.register(r'trades', TradeViewSet, basename='trade')

urlpatterns = [
    # New DSL-based endpoints (MUST be before router)
    path('nl-to-strategy/', NLToStrategyView.as_view(), name='nl-to-strategy'),
    path('run-backtest/', RunBacktestView.as_view(), name='run-backtest'),
    path('quantconnect-backtest/', QuantConnectBacktestView.as_view(), name='quantconnect-backtest'),
    path('quantconnect-progress/', QuantConnectProgressView.as_view(), name='quantconnect-progress'),
    path('<int:strategy_id>/qc-status/', QuantConnectStrategyStatusView.as_view(), name='quantconnect-strategy-status'),
    # Router endpoints (MUST be last)
    path('', include(router.urls)),
]
"""
URLs for trading strategies and backtesting
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StrategyViewSet, BacktestResultViewSet, TradeViewSet, NLToStrategyView, RunBacktestView

router = DefaultRouter()
router.register('', StrategyViewSet, basename='strategy')
router.register(r'backtest-results', BacktestResultViewSet, basename='backtest-result')
router.register(r'trades', TradeViewSet, basename='trade')

urlpatterns = [
    path('', include(router.urls)),
    # New DSL-based endpoints
    path('nl-to-strategy/', NLToStrategyView.as_view(), name='nl-to-strategy'),
    path('run-backtest/', RunBacktestView.as_view(), name='run-backtest'),
]
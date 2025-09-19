"""
URLs for trading strategies and backtesting
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StrategyViewSet, BacktestResultViewSet, TradeViewSet
from .favorites_views import (
    FavoritesListView, ToggleFavoriteView, AddFavoriteView, 
    RemoveFavoriteView, CheckFavoriteView
)

router = DefaultRouter()
router.register('', StrategyViewSet, basename='strategy')
router.register(r'backtest-results', BacktestResultViewSet, basename='backtest-result')
router.register(r'trades', TradeViewSet, basename='trade')

urlpatterns = [
    # Favorites endpoints - these need to be before the router to avoid conflicts
    path('favorites/', FavoritesListView.as_view(), name='favorites-list'),
    path('<int:strategy_id>/toggle-favorite/', ToggleFavoriteView.as_view(), name='toggle-favorite'),
    path('<int:strategy_id>/add-favorite/', AddFavoriteView.as_view(), name='add-favorite'),
    path('<int:strategy_id>/remove-favorite/', RemoveFavoriteView.as_view(), name='remove-favorite'),
    path('<int:strategy_id>/check-favorite/', CheckFavoriteView.as_view(), name='check-favorite'),
    
    path('', include(router.urls)),
]
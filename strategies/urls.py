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
from .optimization_views import (
    GridSearchOptimizationView, WalkForwardOptimizationView,
    AvailableIndicatorsView, StrategyOptimizationView, OptimizationStatusView
)
from .pro_engine_views import (
    ProBacktestView, PortfolioBacktestView, ProIndicatorsView,
    ProEngineStatusView, ProStrategyExamplesView
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
    
    # Optimization endpoints
    path('optimization/grid-search/', GridSearchOptimizationView.as_view(), name='grid-search-optimization'),
    path('optimization/walk-forward/', WalkForwardOptimizationView.as_view(), name='walk-forward-optimization'),
    path('optimization/indicators/', AvailableIndicatorsView.as_view(), name='available-indicators'),
    path('optimization/create-strategy/', StrategyOptimizationView.as_view(), name='create-optimized-strategy'),
    path('optimization/status/', OptimizationStatusView.as_view(), name='optimization-status'),
    
    # Pro Engine endpoints
    path('pro/backtest/', ProBacktestView.as_view(), name='pro-backtest'),
    path('pro/portfolio/', PortfolioBacktestView.as_view(), name='pro-portfolio'),
    path('pro/indicators/', ProIndicatorsView.as_view(), name='pro-indicators'),
    path('pro/status/', ProEngineStatusView.as_view(), name='pro-status'),
    path('pro/examples/', ProStrategyExamplesView.as_view(), name='pro-examples'),
    
    path('', include(router.urls)),
]
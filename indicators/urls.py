"""
URL patterns for Technical Indicators API
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'symbols', views.SymbolViewSet, basename='symbol')
router.register(r'indicator-results', views.IndicatorResultViewSet, basename='indicator-result')
router.register(r'analysis-results', views.AnalysisResultViewSet, basename='analysis-result')
router.register(r'configurations', views.IndicatorConfigurationViewSet, basename='indicator-configuration')

app_name = 'indicators'

urlpatterns = [
    # Include router URLs
    path('api/', include(router.urls)),
    
    # Custom endpoints
    path('api/symbols/<str:name>/indicators/', views.SymbolViewSet.as_view({'get': 'indicators'}), name='symbol-indicators'),
    path('api/indicator-results/calculate/', views.IndicatorResultViewSet.as_view({'post': 'calculate'}), name='calculate-indicators'),
    path('api/indicator-results/latest/', views.IndicatorResultViewSet.as_view({'get': 'latest'}), name='latest-indicators'),
    path('api/analysis-results/trend/', views.AnalysisResultViewSet.as_view({'post': 'analyze_trend'}), name='analyze-trend'),
    path('api/analysis-results/momentum/', views.AnalysisResultViewSet.as_view({'post': 'analyze_momentum'}), name='analyze-momentum'),
]

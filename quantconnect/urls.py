from django.urls import path
from . import views

urlpatterns = [
    path('parse-natural-language/', views.parse_natural_language, name='parse_natural_language'),
    path('strategy-templates/', views.get_strategy_templates, name='strategy_templates'),
    path('favorites/', views.get_favorites, name='get_favorites'),
    path('health/', views.health_check, name='health_check'),
    path('compile-project/', views.compile_project, name='compile_project'),
    path('read-compilation-result/', views.read_compilation_result, name='read_compilation_result'),
    path('run-backtest/', views.run_backtest, name='run_backtest'),
    path('direct/', views.quantconnect_direct, name='quantconnect_direct'),
    path('monitor/', views.QuantConnectMonitorView.as_view(), name='quantconnect_monitor'),
    path('complete-flow/', views.QuantConnectCompleteFlowView.as_view(), name='quantconnect_complete_flow'),
    path('check-progress/', views.check_progress, name='check_progress'),
]

from django.urls import path
from . import views

urlpatterns = [
    # Strategy management
    path('', views.StrategyViewSet.as_view({'get': 'list', 'post': 'create'}), name='strategy-list'),
    path('<int:pk>/', views.StrategyViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='strategy-detail'),
    
    # Strategy actions
    path('<int:pk>/activate/', views.StrategyViewSet.as_view({'post': 'activate'}), name='activate-strategy'),
    path('<int:pk>/pause/', views.StrategyViewSet.as_view({'post': 'pause'}), name='pause-strategy'),
    path('<int:pk>/archive/', views.StrategyViewSet.as_view({'post': 'archive'}), name='archive-strategy'),
    path('<int:pk>/performance/', views.StrategyViewSet.as_view({'get': 'performance'}), name='strategy-performance'),
    
    # Templates
    path('templates/', views.StrategyViewSet.as_view({'get': 'templates'}), name='strategy-templates'),
    path('create-from-template/', views.StrategyViewSet.as_view({'post': 'create_from_template'}), name='create-from-template'),
    
    # Rules management
    path('<int:strategy_pk>/rules/', views.StrategyRuleViewSet.as_view({'get': 'list', 'post': 'create'}), name='strategy-rules-list'),
    path('<int:strategy_pk>/rules/<int:pk>/', views.StrategyRuleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='strategy-rule-detail'),
    
    # Rule Builder
    path('<int:pk>/rule-builder/', views.StrategyRuleBuilderViewSet.as_view({'get': 'available_indicators'}), name='available-indicators'),
    path('<int:pk>/rule-builder/operators/', views.StrategyRuleBuilderViewSet.as_view({'get': 'available_operators'}), name='available-operators'),
    path('<int:pk>/rule-builder/actions/', views.StrategyRuleBuilderViewSet.as_view({'get': 'available_actions'}), name='available-actions'),
    path('<int:pk>/rule-builder/test/', views.StrategyRuleBuilderViewSet.as_view({'post': 'test_rule'}), name='test-rule'),
]

from django.urls import path
from .views import BacktestListCreateView, BacktestDetailView

urlpatterns = [
    path('', BacktestListCreateView.as_view(), name='backtest-list-create'),
    path('<int:pk>/', BacktestDetailView.as_view(), name='backtest-detail'),
]

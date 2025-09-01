from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import HistoricalDataViewSet, DataImportLogViewSet

router = DefaultRouter()
router.register(r'data', HistoricalDataViewSet, basename='historical-data')
router.register(r'imports', DataImportLogViewSet, basename='data-import')

urlpatterns = [
    path('', include(router.urls)),
]

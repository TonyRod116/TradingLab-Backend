from django.shortcuts import render
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from .models import Backtest
from .serializers import BacktestSerializer
from rest_framework.permissions import IsAuthenticatedOrReadOnly


# Create your views here.

class BacktestListCreateView(ListCreateAPIView):
    queryset = Backtest.objects.all()
    serializer_class = BacktestSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

class BacktestDetailView(RetrieveUpdateDestroyAPIView):
    queryset = Backtest.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return PopulatedBacktestSerializer
        return BacktestSerializer
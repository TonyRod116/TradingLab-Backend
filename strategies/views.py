from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from .models import Strategy
from .serializers import StrategySerializer
from .services import QuantConnectService

class StrategyView(generics.ListCreateAPIView):
    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Strategy.objects.filter(owner=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

class StrategyDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = StrategySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Strategy.objects.filter(owner=self.request.user)

class QuantConnectSyncView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        user_id = request.data.get('quantconnect_user_id')
        api_token = request.data.get('quantconnect_api_token')
        
        if not user_id or not api_token:
            return Response(
                {'error': 'User ID and API token are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Test authentication
            qc_service = QuantConnectService(user_id, api_token)
            if not qc_service.test_authentication():
                return Response(
                    {'error': 'Invalid QuantConnect credentials'}, 
                    status=status.HTTP_401_UNAUTHORIZED
                )
            
            # Fetch algorithms
            algorithms = qc_service.get_algorithms()
            
            # Sync strategies
            synced_count = 0
            for algo in algorithms:
                strategy_data = {
                    'title': algo.get('name', 'Unnamed Strategy'),
                    'description': algo.get('description', ''),
                    'quantconnect_id': str(algo.get('id')),
                    'language': algo.get('language', 'python'),
                    'status': 'backtest',  # Default status
                    'owner': request.user
                }
                
                # Try to get performance metrics if available
                try:
                    algo_details = qc_service.get_algorithm_by_id(algo.get('id'))
                    if 'statistics' in algo_details:
                        stats = algo_details['statistics']
                        strategy_data.update({
                            'sharpe_ratio': float(stats.get('Sharpe Ratio', 0)),
                            'max_drawdown': float(stats.get('Maximum Drawdown', 0)),
                            'total_trades': int(stats.get('Total Trades', 0)),
                            'win_rate': float(stats.get('Win Rate', 0)),
                            'total_return': float(stats.get('Total Return', 0))
                        })
                except:
                    pass  # Continue without detailed metrics
                
                # Update or create strategy
                strategy, created = Strategy.objects.update_or_create(
                    quantconnect_id=strategy_data['quantconnect_id'],
                    owner=request.user,
                    defaults=strategy_data
                )
                
                if created or strategy.is_synced:
                    synced_count += 1
            
            return Response({
                'message': 'Strategies synced successfully',
                'synced_count': synced_count,
                'total_algorithms': len(algorithms)
            })
            
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

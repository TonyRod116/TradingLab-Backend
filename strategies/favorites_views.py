from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.shortcuts import get_object_or_404
from .models import Strategy, Favorite
from .serializers import StrategySummarySerializer


class FavoritesListView(APIView):
    """Vista para obtener todas las estrategias favoritas del usuario"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Obtener todas las estrategias favoritas del usuario"""
        try:
            # Obtener todos los favoritos del usuario con la estrategia y su usuario
            # Usar prefetch_related para optimizar las consultas de backtests
            favorites = Favorite.objects.filter(user=request.user).select_related('strategy', 'strategy__user').prefetch_related('strategy__backtests')
            
            # Extraer las estrategias de los favoritos
            strategies = [favorite.strategy for favorite in favorites]
            
            # Reutilizar el serializer que usa la vista de community para obtener los mismos datos
            serializer = StrategySummarySerializer(strategies, many=True, context={'request': request})
            
            return Response({
                'success': True,
                'count': len(serializer.data),
                'results': serializer.data
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ToggleFavoriteView(APIView):
    """Vista para agregar/quitar estrategia de favoritos"""
    permission_classes = [IsAuthenticated]

    def post(self, request, strategy_id):
        """Toggle favorite status for a strategy"""
        try:
            # Obtener la estrategia
            strategy = get_object_or_404(Strategy, id=strategy_id)
            
            # Verificar si ya es favorita
            favorite, created = Favorite.objects.get_or_create(
                user=request.user,
                strategy=strategy
            )
            
            if created:
                # Se agregó a favoritos
                return Response({
                    'success': True,
                    'is_favorited': True,
                    'message': f'Strategy "{strategy.name}" added to favorites'
                })
            else:
                # Ya era favorita, la eliminamos
                favorite.delete()
                return Response({
                    'success': True,
                    'is_favorited': False,
                    'message': f'Strategy "{strategy.name}" removed from favorites'
                })
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AddFavoriteView(APIView):
    """Vista para agregar estrategia a favoritos"""
    permission_classes = [IsAuthenticated]

    def post(self, request, strategy_id):
        """Add strategy to favorites"""
        try:
            # Obtener la estrategia
            strategy = get_object_or_404(Strategy, id=strategy_id)
            
            # Crear o obtener el favorito
            favorite, created = Favorite.objects.get_or_create(
                user=request.user,
                strategy=strategy
            )
            
            if created:
                return Response({
                    'success': True,
                    'is_favorited': True,
                    'message': f'Strategy "{strategy.name}" added to favorites'
                })
            else:
                return Response({
                    'success': True,
                    'is_favorited': True,
                    'message': f'Strategy "{strategy.name}" is already in favorites'
                })
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class RemoveFavoriteView(APIView):
    """Vista para quitar estrategia de favoritos"""
    permission_classes = [IsAuthenticated]

    def delete(self, request, strategy_id):
        """Remove strategy from favorites"""
        try:
            # Obtener la estrategia
            strategy = get_object_or_404(Strategy, id=strategy_id)
            
            # Buscar y eliminar el favorito
            try:
                favorite = Favorite.objects.get(user=request.user, strategy=strategy)
                favorite.delete()
                
                return Response({
                    'success': True,
                    'is_favorited': False,
                    'message': f'Strategy "{strategy.name}" removed from favorites'
                })
                
            except Favorite.DoesNotExist:
                return Response({
                    'success': True,
                    'is_favorited': False,
                    'message': f'Strategy "{strategy.name}" was not in favorites'
                })
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CheckFavoriteView(APIView):
    """Vista para verificar si una estrategia es favorita"""
    permission_classes = [IsAuthenticated]

    def get(self, request, strategy_id):
        """Check if strategy is favorited by user"""
        try:
            # Obtener la estrategia
            strategy = get_object_or_404(Strategy, id=strategy_id)
            
            # Verificar si es favorita
            is_favorited = Favorite.objects.filter(
                user=request.user,
                strategy=strategy
            ).exists()
            
            return Response({
                'success': True,
                'is_favorited': is_favorited,
                'strategy_id': strategy_id,
                'strategy_name': strategy.name
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

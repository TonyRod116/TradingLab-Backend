"""
Optimization Views - Django REST API for advanced optimization features
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
import json

from .models import Strategy
from .optimization_service import OptimizationService
from .serializers import StrategySerializer


class GridSearchOptimizationView(APIView):
    """Grid search optimization endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Perform grid search optimization
        
        Expected payload:
        {
            "strategy_id": 123,
            "param_ranges": {
                "sma_length": [10, 20, 30],
                "rsi_length": [14, 21, 28]
            },
            "start_date": "2023-01-01",
            "end_date": "2023-12-31",
            "initial_capital": 100000
        }
        """
        try:
            data = request.data
            
            # Validate required fields
            strategy_id = data.get('strategy_id')
            param_ranges = data.get('param_ranges', {})
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            initial_capital = data.get('initial_capital', 100000)
            
            if not strategy_id:
                return Response(
                    {"error": "strategy_id is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not param_ranges:
                return Response(
                    {"error": "param_ranges is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get strategy
            try:
                strategy = Strategy.objects.get(id=strategy_id, user=request.user)
            except Strategy.DoesNotExist:
                return Response(
                    {"error": "Strategy not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Parse dates
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_date = datetime.now() - timedelta(days=365)
            
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_date = datetime.now()
            
            # Run optimization
            optimization_service = OptimizationService()
            result = optimization_service.grid_search_optimization(
                strategy=strategy,
                param_ranges=param_ranges,
                start_date=start_date,
                end_date=end_date,
                initial_capital=initial_capital
            )
            
            return Response({
                "success": True,
                "best_params": result.best_params,
                "best_sharpe": result.best_sharpe,
                "optimization_time": result.optimization_time,
                "total_combinations": len(result.all_results),
                "top_results": result.all_results[:10]  # Top 10 results
            })
            
        except Exception as e:
            return Response(
                {"error": f"Optimization failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class WalkForwardOptimizationView(APIView):
    """Walk-forward optimization endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Perform walk-forward optimization
        
        Expected payload:
        {
            "strategy_id": 123,
            "param_ranges": {
                "sma_length": [10, 20, 30],
                "rsi_length": [14, 21, 28]
            },
            "train_months": 6,
            "test_months": 1,
            "step_months": 1,
            "start_date": "2020-01-01",
            "end_date": "2023-12-31"
        }
        """
        try:
            data = request.data
            
            # Validate required fields
            strategy_id = data.get('strategy_id')
            param_ranges = data.get('param_ranges', {})
            train_months = data.get('train_months', 6)
            test_months = data.get('test_months', 1)
            step_months = data.get('step_months', 1)
            start_date = data.get('start_date')
            end_date = data.get('end_date')
            
            if not strategy_id:
                return Response(
                    {"error": "strategy_id is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not param_ranges:
                return Response(
                    {"error": "param_ranges is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get strategy
            try:
                strategy = Strategy.objects.get(id=strategy_id, user=request.user)
            except Strategy.DoesNotExist:
                return Response(
                    {"error": "Strategy not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Parse dates
            if start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
            else:
                start_date = datetime(2020, 1, 1)
            
            if end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
            else:
                end_date = datetime.now()
            
            # Run walk-forward optimization
            optimization_service = OptimizationService()
            result = optimization_service.walk_forward_optimization(
                strategy=strategy,
                param_ranges=param_ranges,
                train_months=train_months,
                test_months=test_months,
                step_months=step_months,
                start_date=start_date,
                end_date=end_date
            )
            
            return Response({
                "success": True,
                "train_results": result.train_results,
                "test_results": result.test_results,
                "best_params": result.best_params,
                "oos_performance": result.oos_performance,
                "total_periods": len(result.test_results)
            })
            
        except Exception as e:
            return Response(
                {"error": f"Walk-forward optimization failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AvailableIndicatorsView(APIView):
    """Get available indicators endpoint"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get list of all available indicators with their parameters"""
        try:
            optimization_service = OptimizationService()
            indicators = optimization_service.get_available_indicators()
            
            return Response({
                "success": True,
                "indicators": indicators,
                "total_count": len(indicators)
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to get indicators: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class StrategyOptimizationView(APIView):
    """Create optimized strategy endpoint"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """
        Create a new strategy with optimized parameters
        
        Expected payload:
        {
            "original_strategy_id": 123,
            "optimized_params": {
                "sma_length": 20,
                "rsi_length": 14
            },
            "strategy_name": "Optimized Strategy"
        }
        """
        try:
            data = request.data
            
            # Validate required fields
            original_strategy_id = data.get('original_strategy_id')
            optimized_params = data.get('optimized_params', {})
            strategy_name = data.get('strategy_name', 'Optimized Strategy')
            
            if not original_strategy_id:
                return Response(
                    {"error": "original_strategy_id is required"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get original strategy
            try:
                original_strategy = Strategy.objects.get(id=original_strategy_id, user=request.user)
            except Strategy.DoesNotExist:
                return Response(
                    {"error": "Original strategy not found"}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create optimized strategy
            optimization_service = OptimizationService()
            optimized_strategy = optimization_service._create_strategy_with_params(
                original_strategy, optimized_params
            )
            
            # Set name and user
            optimized_strategy.name = strategy_name
            optimized_strategy.user = request.user
            optimized_strategy.save()
            
            # Serialize response
            serializer = StrategySerializer(optimized_strategy)
            
            return Response({
                "success": True,
                "message": "Optimized strategy created successfully",
                "strategy": serializer.data
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to create optimized strategy: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class OptimizationStatusView(APIView):
    """Get optimization status endpoint"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Get current optimization status and capabilities"""
        try:
            return Response({
                "success": True,
                "status": "active",
                "capabilities": {
                    "grid_search": True,
                    "walk_forward": True,
                    "parameter_optimization": True,
                    "advanced_indicators": True
                },
                "supported_indicators": [
                    "SMA", "EMA", "RSI", "ATR", "Bollinger Bands", "VWAP",
                    "CCI", "Stochastic", "Williams %R", "OBV", "AD Line",
                    "MACD", "ADX", "Parabolic SAR", "Ichimoku"
                ],
                "max_parameter_combinations": 1000,
                "max_walk_forward_periods": 50
            })
            
        except Exception as e:
            return Response(
                {"error": f"Failed to get optimization status: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

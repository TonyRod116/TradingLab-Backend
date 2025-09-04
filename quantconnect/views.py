from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import re
from datetime import datetime
import sys
import os

# Agregar el directorio padre al path para importar nuestros módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gpt_parser import GPTQuantConnectParser

class QuantConnectView(APIView):
    permission_classes = []  # Sin autenticación requerida para QuantConnect

class ParseNaturalLanguageView(QuantConnectView):
    def post(self, request):
        try:
            description = request.data.get('description', '')
            backtest_params = request.data.get('backtest_params', {})
            
            # Usar el nuevo parser GPT
            parser = GPTQuantConnectParser()
            python_code = parser.parse_strategy_description(description, backtest_params)
            
            if not python_code:
                return Response({
                    'success': False,
                    'error': 'Failed to parse strategy description'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Análisis de complejidad de la estrategia
            strategy_analysis = parser.analyze_strategy_complexity(description)
            
            # Generar project_id único
            project_id = f"strategy_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            return Response({
                'success': True,
                'python_code': python_code,
                'project_id': project_id,
                'strategy_analysis': strategy_analysis,
                'message': 'Strategy parsed successfully using GPT'
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Parsing error: {str(e)}'
            }, status=status.HTTP_400_BAD_REQUEST)

class StrategyTemplatesView(QuantConnectView):
    def get(self, request):
        parser = GPTQuantConnectParser()
        templates = parser.generate_strategy_templates()
        return Response(templates)

class FavoritesView(QuantConnectView):
    def get(self, request):
        # Por ahora devolver lista vacía - se puede implementar con base de datos después
        return Response([])
    
    def post(self, request):
        # Por ahora solo confirmar - se puede implementar con base de datos después
        return Response({'success': True, 'message': 'Added to favorites'})

class HealthCheckView(APIView):
    def get(self, request):
        return Response({
            'status': 'healthy',
            'service': 'QuantConnect Integration',
            'timestamp': datetime.now().isoformat(),
            'version': '1.0.0'
        })

class CompileProjectView(QuantConnectView):
    def post(self, request):
        try:
            project_id = request.data.get('projectId')
            python_code = request.data.get('python_code', '')
            
            if not project_id or not python_code:
                return Response({
                    'success': False,
                    'error': 'projectId and python_code are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Usar nuestro servicio de QuantConnect
            service = QuantConnectService()
            
            # Crear proyecto y compilar
            result = service.create_and_compile_strategy(
                description="Compiled strategy",
                strategy_data={'symbol': 'SPY', 'indicators': ['RSI', 'SMA']},
                python_code=python_code
            )
            
            if result['success']:
                return Response({
                    'success': True,
                    'compile_id': result.get('compileId', f"compile_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                    'status': 'compiled',
                    'project_id': result.get('projectId', project_id)
                })
            else:
                return Response({
                    'success': False,
                    'error': result.get('error', 'Compilation failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Compilation error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class ReadCompilationResultView(QuantConnectView):
    def post(self, request):
        try:
            compile_id = request.data.get('compileId')
            
            if not compile_id:
                return Response({
                    'success': False,
                    'error': 'compileId is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Simular resultado de compilación exitosa
            return Response({
                'success': True,
                'compile_id': compile_id,
                'status': 'completed',
                'python_code': 'print("Compilation successful")',
                'errors': [],
                'warnings': []
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Error reading compilation result: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class RunBacktestView(QuantConnectView):
    def post(self, request):
        try:
            project_id = request.data.get('projectId')
            compile_id = request.data.get('compileId')
            
            if not project_id:
                return Response({
                    'success': False,
                    'error': 'projectId is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Usar nuestro servicio de QuantConnect para ejecutar backtest
            service = QuantConnectService()
            
            # Parámetros por defecto
            initial_capital = request.data.get('initial_capital', 100000)
            start_date = request.data.get('start_date', '2021-01-01')
            end_date = request.data.get('end_date', '2024-01-01')
            benchmark = request.data.get('benchmark', 'SPY')
            
            # Ejecutar backtest
            backtest_result = service.run_backtest(
                project_id=project_id,
                initial_capital=initial_capital,
                start_date=start_date,
                end_date=end_date,
                benchmark=benchmark
            )
            
            if backtest_result['success']:
                return Response({
                    'success': True,
                    'backtest_id': f"backtest_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'status': 'completed',
                    'project_id': project_id,
                    'compile_id': compile_id,
                    'backtest_metrics': backtest_result.get('backtest_metrics', {}),
                    'equity_curve': backtest_result.get('equity_curve', []),
                    'trades': backtest_result.get('trades', [])
                })
            else:
                return Response({
                    'success': False,
                    'error': backtest_result.get('error', 'Backtest failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': f'Backtest error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Asignar las vistas a las funciones para compatibilidad con URLs
parse_natural_language = ParseNaturalLanguageView.as_view()
get_strategy_templates = StrategyTemplatesView.as_view()
get_favorites = FavoritesView.as_view()
health_check = HealthCheckView.as_view()
compile_project = CompileProjectView.as_view()
read_compilation_result = ReadCompilationResultView.as_view()
run_backtest = RunBacktestView.as_view()

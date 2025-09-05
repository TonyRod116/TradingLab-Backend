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

class QuantConnectDirectAPIView(APIView):
    """Vista para operaciones directas con QuantConnect API"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Endpoint principal para operaciones de QuantConnect"""
        action = request.data.get('action')
        
        if action == 'create_project':
            return self._create_project(request)
        elif action == 'create_file':
            return self._create_file(request)
        elif action == 'compile_project':
            return self._compile_project(request)
        elif action == 'check_compilation':
            return self._check_compilation(request)
        elif action == 'run_backtest':
            return self._run_backtest(request)
        elif action == 'check_backtest_status':
            return self._check_backtest_status(request)
        elif action == 'get_backtest_results':
            return self._get_backtest_results(request)
        else:
            return Response({
                'success': False,
                'error': 'Invalid action. Available: create_project, create_file, compile_project, check_compilation, run_backtest, check_backtest_status, get_backtest_results'
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def _create_project(self, request):
        """Crear proyecto en QuantConnect"""
        try:
            from strategies.services.quantconnect_service import QuantConnectService
            
            name = request.data.get('name', f'Strategy {datetime.now().strftime("%Y%m%d_%H%M%S")}')
            language = request.data.get('language', 'Py')
            
            qc_service = QuantConnectService()
            result = qc_service.create_project_direct(name, language)
            
            if result['success']:
                return Response({
                    'success': True,
                    'project_id': result['project_id'],
                    'name': result['name'],
                    'language': result['language']
                })
            else:
                return Response({
                    'success': False,
                    'error': result['error']
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _create_file(self, request):
        """Crear archivo en proyecto QuantConnect"""
        try:
            from strategies.services.quantconnect_service import QuantConnectService
            
            project_id = request.data.get('project_id')
            filename = request.data.get('filename', 'main.py')
            content = request.data.get('content', '')
            
            if not project_id or not content:
                return Response({
                    'success': False,
                    'error': 'project_id and content are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            qc_service = QuantConnectService()
            result = qc_service.create_file_direct(project_id, filename, content)
            
            return Response(result)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _compile_project(self, request):
        """Compilar proyecto QuantConnect"""
        try:
            from strategies.services.quantconnect_service import QuantConnectService
            
            project_id = request.data.get('project_id')
            
            if not project_id:
                return Response({
                    'success': False,
                    'error': 'project_id is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            qc_service = QuantConnectService()
            result = qc_service.compile_project_direct(project_id)
            
            return Response(result)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _check_compilation(self, request):
        """Verificar estado de compilación"""
        try:
            from strategies.services.quantconnect_service import QuantConnectService
            
            project_id = request.data.get('project_id')
            compile_id = request.data.get('compile_id')
            
            if not project_id or not compile_id:
                return Response({
                    'success': False,
                    'error': 'project_id and compile_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            qc_service = QuantConnectService()
            result = qc_service.check_compilation_direct(project_id, compile_id)
            
            return Response(result)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _run_backtest(self, request):
        """Ejecutar backtest"""
        try:
            from strategies.services.quantconnect_service import QuantConnectService
            
            project_id = request.data.get('project_id')
            compile_id = request.data.get('compile_id')
            backtest_name = request.data.get('backtest_name')
            
            if not project_id or not compile_id:
                return Response({
                    'success': False,
                    'error': 'project_id and compile_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            qc_service = QuantConnectService()
            result = qc_service.run_backtest_direct(project_id, compile_id, backtest_name)
            
            return Response(result)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _check_backtest_status(self, request):
        """Verificar estado del backtest"""
        try:
            from strategies.services.quantconnect_service import QuantConnectService
            
            project_id = request.data.get('project_id')
            backtest_id = request.data.get('backtest_id')
            
            if not project_id or not backtest_id:
                return Response({
                    'success': False,
                    'error': 'project_id and backtest_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            qc_service = QuantConnectService()
            result = qc_service.check_backtest_status_direct(project_id, backtest_id)
            
            return Response(result)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _get_backtest_results(self, request):
        """Obtener resultados del backtest"""
        try:
            from strategies.services.quantconnect_service import QuantConnectService
            
            project_id = request.data.get('project_id')
            backtest_id = request.data.get('backtest_id')
            
            if not project_id or not backtest_id:
                return Response({
                    'success': False,
                    'error': 'project_id and backtest_id are required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            qc_service = QuantConnectService()
            result = qc_service.get_backtest_results_direct(project_id, backtest_id)
            
            return Response(result)
                
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class QuantConnectMonitorView(APIView):
    """Vista para monitoreo en tiempo real de QuantConnect"""
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """Monitorear estado de compilación o backtest"""
        monitor_type = request.GET.get('type')  # 'compilation' o 'backtest'
        project_id = request.GET.get('project_id')
        
        if not project_id:
            return Response({
                'success': False,
                'error': 'project_id is required'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            from strategies.services.quantconnect_service import QuantConnectService
            qc_service = QuantConnectService()
            
            if monitor_type == 'compilation':
                compile_id = request.GET.get('compile_id')
                if not compile_id:
                    return Response({
                        'success': False,
                        'error': 'compile_id is required for compilation monitoring'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                result = qc_service.check_compilation_direct(project_id, compile_id)
                
            elif monitor_type == 'backtest':
                backtest_id = request.GET.get('backtest_id')
                if not backtest_id:
                    return Response({
                        'success': False,
                        'error': 'backtest_id is required for backtest monitoring'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                result = qc_service.check_backtest_status_direct(project_id, backtest_id)
                
            else:
                return Response({
                    'success': False,
                    'error': 'type must be "compilation" or "backtest"'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            return Response(result)
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class QuantConnectCompleteFlowView(APIView):
    """Vista para ejecutar el flujo completo de QuantConnect"""
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        """Ejecutar flujo completo: crear proyecto, archivo, compilar y ejecutar backtest"""
        try:
            from strategies.services.quantconnect_service import QuantConnectService
            import time
            
            # Obtener parámetros
            strategy_name = request.data.get('strategy_name', f'Strategy {datetime.now().strftime("%Y%m%d_%H%M%S")}')
            python_code = request.data.get('python_code', '')
            backtest_name = request.data.get('backtest_name', f'Backtest {datetime.now().strftime("%Y%m%d_%H%M%S")}')
            
            if not python_code:
                return Response({
                    'success': False,
                    'error': 'python_code is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            qc_service = QuantConnectService()
            results = {
                'steps': [],
                'project_id': None,
                'compile_id': None,
                'backtest_id': None,
                'final_results': None
            }
            
            # Paso 1: Crear proyecto
            project_result = qc_service.create_project_direct(strategy_name)
            if not project_result['success']:
                return Response({
                    'success': False,
                    'error': f'Failed to create project: {project_result["error"]}',
                    'results': results
                })
            
            project_id = project_result['project_id']
            results['project_id'] = project_id
            results['steps'].append({
                'step': 'create_project',
                'success': True,
                'project_id': project_id
            })
            
            # Paso 2: Crear archivo
            file_result = qc_service.create_file_direct(project_id, 'main.py', python_code)
            if not file_result['success']:
                return Response({
                    'success': False,
                    'error': f'Failed to create file: {file_result["error"]}',
                    'results': results
                })
            
            results['steps'].append({
                'step': 'create_file',
                'success': True
            })
            
            # Paso 3: Compilar proyecto
            compile_result = qc_service.compile_project_direct(project_id)
            if not compile_result['success']:
                return Response({
                    'success': False,
                    'error': f'Failed to compile project: {compile_result["error"]}',
                    'results': results
                })
            
            compile_id = compile_result['compile_id']
            results['compile_id'] = compile_id
            results['steps'].append({
                'step': 'compile_project',
                'success': True,
                'compile_id': compile_id
            })
            
            # Paso 4: Esperar compilación
            max_attempts = 30
            for attempt in range(max_attempts):
                time.sleep(2)  # Esperar 2 segundos
                compilation_check = qc_service.check_compilation_direct(project_id, compile_id)
                
                if compilation_check['success']:
                    if compilation_check['completed']:
                        results['steps'].append({
                            'step': 'compilation_completed',
                            'success': True,
                            'state': compilation_check['state']
                        })
                        break
                    elif compilation_check['failed']:
                        return Response({
                            'success': False,
                            'error': f'Compilation failed: {compilation_check.get("logs", [])}',
                            'results': results
                        })
                    else:
                        results['steps'].append({
                            'step': 'compilation_in_progress',
                            'success': True,
                            'state': compilation_check['state'],
                            'attempt': attempt + 1
                        })
                else:
                    return Response({
                        'success': False,
                        'error': f'Failed to check compilation: {compilation_check["error"]}',
                        'results': results
                    })
            else:
                return Response({
                    'success': False,
                    'error': 'Compilation timeout',
                    'results': results
                })
            
            # Paso 5: Ejecutar backtest
            backtest_result = qc_service.run_backtest_direct(project_id, compile_id, backtest_name)
            if not backtest_result['success']:
                return Response({
                    'success': False,
                    'error': f'Failed to run backtest: {backtest_result["error"]}',
                    'results': results
                })
            
            backtest_id = backtest_result['backtest_id']
            results['backtest_id'] = backtest_id
            results['steps'].append({
                'step': 'backtest_started',
                'success': True,
                'backtest_id': backtest_id,
                'status': backtest_result['status']
            })
            
            # Paso 6: Monitorear backtest
            max_backtest_attempts = 60  # 10 minutos máximo
            for attempt in range(max_backtest_attempts):
                time.sleep(10)  # Esperar 10 segundos
                backtest_check = qc_service.check_backtest_status_direct(project_id, backtest_id)
                
                if backtest_check['success']:
                    if backtest_check['completed']:
                        results['steps'].append({
                            'step': 'backtest_completed',
                            'success': True,
                            'status': backtest_check['status'],
                            'progress': backtest_check['progress']
                        })
                        
                        # Obtener resultados finales
                        final_results = qc_service.get_backtest_results_direct(project_id, backtest_id)
                        if final_results['success']:
                            results['final_results'] = final_results['results']
                        
                        return Response({
                            'success': True,
                            'message': 'Backtest completed successfully',
                            'results': results
                        })
                        
                    elif backtest_check['failed']:
                        return Response({
                            'success': False,
                            'error': f'Backtest failed: {backtest_check["status"]}',
                            'results': results
                        })
                    else:
                        results['steps'].append({
                            'step': 'backtest_in_progress',
                            'success': True,
                            'status': backtest_check['status'],
                            'progress': backtest_check['progress'],
                            'attempt': attempt + 1
                        })
                else:
                    return Response({
                        'success': False,
                        'error': f'Failed to check backtest status: {backtest_check["error"]}',
                        'results': results
                    })
            
            return Response({
                'success': False,
                'error': 'Backtest timeout',
                'results': results
            })
            
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

def _safe_serialize(obj):
    """
    Convierte objetos no serializables a tipos seguros para JSON
    """
    import json
    from decimal import Decimal
    from datetime import datetime, date
    import numpy as np
    
    try:
        # Si ya es serializable, devolverlo
        json.dumps(obj)
        return obj
    except (TypeError, ValueError):
        # Convertir tipos problemáticos
        if isinstance(obj, Decimal):
            return float(obj)
        elif isinstance(obj, (datetime, date)):
            return obj.isoformat()
        elif isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, set):
            return list(obj)
        elif hasattr(obj, '__dict__'):
            # Para objetos personalizados, convertir a dict
            return {k: _safe_serialize(v) for k, v in obj.__dict__.items()}
        else:
            return str(obj)

def _parse_quantconnect_statistics(stats_dict):
    """
    Parsea las estadísticas de QuantConnect que vienen como strings
    """
    parsed_stats = {}
    
    for key, value in stats_dict.items():
        if isinstance(value, str):
            # Remover caracteres no numéricos excepto punto y signo menos
            clean_value = value.replace('%', '').replace('$', '').replace(',', '').strip()
            
            try:
                # Intentar convertir a float
                if clean_value:
                    parsed_stats[key] = float(clean_value)
                else:
                    parsed_stats[key] = 0.0
            except (ValueError, TypeError):
                # Si no se puede convertir, mantener como string
                parsed_stats[key] = value
        else:
            parsed_stats[key] = value
    
    return parsed_stats

@csrf_exempt
def check_progress(request):
    """
    Check the progress of a QuantConnect backtest
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    try:
        import json
        data = json.loads(request.body)
        project_id = data.get('project_id')
        backtest_id = data.get('backtest_id')
        
        if not project_id or not backtest_id:
            return JsonResponse({
                'success': False,
                'error': 'project_id and backtest_id are required'
            }, status=400)
        
        # Import the service
        from strategies.services.quantconnect_service import QuantConnectService
        
        qc_service = QuantConnectService()
        result = qc_service.check_backtest_status_direct(int(project_id), backtest_id)
        
        if result['success']:
            # The result already contains the processed data
            safe_response = {
                'success': True,
                'status': result.get('status', 'Unknown'),
                'progress': float(result.get('progress', 0)) if result.get('progress') is not None else 0.0,
                'backtestId': backtest_id,
                'completed': result.get('completed', False),
                'projectId': int(project_id),
                'name': f'Backtest {backtest_id}',
                'error': result.get('error'),
                'stacktrace': result.get('stacktrace')
            }
            
            # Agregar estadísticas básicas si están disponibles
            if 'statistics' in result:
                stats = result['statistics']
                parsed_stats = _parse_quantconnect_statistics(stats)
                safe_response['statistics'] = {
                    'Total Orders': parsed_stats.get('Total Orders', 0),
                    'Net Profit': parsed_stats.get('Net Profit', 0.0),
                    'Sharpe Ratio': parsed_stats.get('Sharpe Ratio', 0.0),
                    'Drawdown': parsed_stats.get('Drawdown', 0.0),
                    'Win Rate': parsed_stats.get('Win Rate', 0.0),
                    'Loss Rate': parsed_stats.get('Loss Rate', 0.0),
                    'Start Equity': parsed_stats.get('Start Equity', 100000.0),
                    'End Equity': parsed_stats.get('End Equity', 100000.0),
                    'Profit Factor': parsed_stats.get('Profit Factor', 0.0),
                    'Winning Trades': parsed_stats.get('Winning Trades', 0),
                    'Losing Trades': parsed_stats.get('Losing Trades', 0),
                    'Total Trades': parsed_stats.get('Total Trades', 0)
                }
            
            # Agregar estadísticas de runtime si están disponibles
            if 'runtimeStatistics' in result:
                rt_stats = result['runtimeStatistics']
                parsed_rt_stats = _parse_quantconnect_statistics(rt_stats)
                safe_response['runtimeStatistics'] = {
                    'Equity': parsed_rt_stats.get('Equity', 0.0),
                    'Net Profit': parsed_rt_stats.get('Net Profit', 0.0),
                    'Return': parsed_rt_stats.get('Return', 0.0),
                    'Fees': parsed_rt_stats.get('Fees', 0.0)
                }
            
            return JsonResponse(safe_response, safe=False)
        else:
            return JsonResponse({
                'success': False,
                'error': result.get('error', 'Failed to check backtest status')
            }, status=400)
            
    except Exception as e:
        import traceback
        # Log del error completo para debugging
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)

# Asignar las vistas a las funciones para compatibilidad con URLs
parse_natural_language = ParseNaturalLanguageView.as_view()
get_strategy_templates = StrategyTemplatesView.as_view()
get_favorites = FavoritesView.as_view()
health_check = HealthCheckView.as_view()
compile_project = CompileProjectView.as_view()
read_compilation_result = ReadCompilationResultView.as_view()
run_backtest = RunBacktestView.as_view()
quantconnect_direct = QuantConnectDirectAPIView.as_view()
# check_progress ya está definido como función arriba

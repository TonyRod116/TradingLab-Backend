from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import time
from quantconnect_service import QuantConnectService


@csrf_exempt
@require_http_methods(["POST"])
def test_quantconnect_auth(request):
    """
    Test QuantConnect authentication
    """
    try:
        service = QuantConnectService()
        result = service.test_authentication()
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def test_project_creation(request):
    """
    Test QuantConnect project creation
    """
    try:
        service = QuantConnectService()
        result = service.test_project_creation()
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_project(request):
    """
    Create a new QuantConnect project
    """
    try:
        data = json.loads(request.body)
        name = data.get('name', f'Project_{int(time.time())}')
        language = data.get('language', 'Python')
        
        service = QuantConnectService()
        result = service.create_project(name, language)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def run_backtest(request):
    """
    Run a complete backtest workflow
    """
    try:
        data = json.loads(request.body)
        strategy_data = data.get('strategy', {})
        description = data.get('description', '')
        
        service = QuantConnectService()
        result = service.run_complete_workflow(strategy_data, description)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

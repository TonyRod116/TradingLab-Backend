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


@csrf_exempt
@require_http_methods(["POST"])
def parse_natural_language(request):
    """
    Parse natural language strategy description to QuantConnect code
    """
    try:
        data = json.loads(request.body)
        description = data.get('description', '')
        strategy_data = data.get('strategy', {})
        
        if not description:
            return JsonResponse({
                'success': False,
                'error': 'Description is required'
            }, status=400)
        
        service = QuantConnectService()
        result = service.parse_natural_language_strategy(description, strategy_data)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_and_compile_strategy(request):
    """
    Create project, parse strategy, and compile in one step
    """
    try:
        data = json.loads(request.body)
        description = data.get('description', '')
        strategy_data = data.get('strategy', {})
        
        if not description:
            return JsonResponse({
                'success': False,
                'error': 'Description is required'
            }, status=400)
        
        service = QuantConnectService()
        result = service.create_and_compile_strategy(description, strategy_data)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def compile_project(request):
    """
    Create compilation job for a QuantConnect project
    """
    try:
        data = json.loads(request.body)
        project_id = data.get('projectId')
        
        if not project_id:
            return JsonResponse({
                'success': False,
                'error': 'Project ID is required'
            }, status=400)
        
        service = QuantConnectService()
        result = service.create_compilation_job(project_id)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def read_compilation_result(request):
    """
    Read compilation result for a specific project and compile ID
    """
    try:
        data = json.loads(request.body)
        project_id = data.get('projectId')
        compile_id = data.get('compileId')
        
        if not project_id or not compile_id:
            return JsonResponse({
                'success': False,
                'error': 'Project ID and Compile ID are required'
            }, status=400)
        
        service = QuantConnectService()
        result = service.read_compilation_result(project_id, compile_id)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def create_file(request):
    """
    Create a file in a QuantConnect project
    """
    try:
        data = json.loads(request.body)
        project_id = data.get('projectId')
        name = data.get('name')
        content = data.get('content')
        
        if not all([project_id, name, content]):
            return JsonResponse({
                'success': False,
                'error': 'Project ID, name, and content are required'
            }, status=400)
        
        service = QuantConnectService()
        result = service.create_file(project_id, name, content)
        
        return JsonResponse(result)
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Server error: {str(e)}'
        }, status=500)

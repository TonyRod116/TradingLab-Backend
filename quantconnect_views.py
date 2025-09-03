from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
import time


@csrf_exempt
@require_http_methods(["POST"])
def test_quantconnect_auth(request):
    """
    Test QuantConnect authentication - Temporarily disabled
    """
    return JsonResponse({
        'success': False,
        'error': 'QuantConnect service temporarily disabled for maintenance'
    }, status=503)


@csrf_exempt
@require_http_methods(["POST"])
def test_project_creation(request):
    """
    Test QuantConnect project creation - Temporarily disabled
    """
    return JsonResponse({
        'success': False,
        'error': 'QuantConnect service temporarily disabled for maintenance'
    }, status=503)


@csrf_exempt
@require_http_methods(["POST"])
def create_project(request):
    """
    Create QuantConnect project - Temporarily disabled
    """
    return JsonResponse({
        'success': False,
        'error': 'QuantConnect service temporarily disabled for maintenance'
    }, status=503)


@csrf_exempt
@require_http_methods(["POST"])
def run_complete_workflow(request):
    """
    Run complete QuantConnect workflow - Temporarily disabled
    """
    return JsonResponse({
        'success': False,
        'error': 'QuantConnect service temporarily disabled for maintenance'
    }, status=503)


@csrf_exempt
@require_http_methods(["POST"])
def parse_natural_language(request):
    """
    Parse natural language strategy - Temporarily disabled
    """
    return JsonResponse({
        'success': False,
        'error': 'QuantConnect service temporarily disabled for maintenance'
    }, status=503)


@csrf_exempt
@require_http_methods(["POST"])
def create_and_compile_strategy(request):
    """
    Create and compile strategy - Temporarily disabled
    """
    return JsonResponse({
        'success': False,
        'error': 'QuantConnect service temporarily disabled for maintenance'
    }, status=503)


@csrf_exempt
@require_http_methods(["POST"])
def compile_project(request):
    """
    Compile project - Temporarily disabled
    """
    return JsonResponse({
        'success': False,
        'error': 'QuantConnect service temporarily disabled for maintenance'
    }, status=503)


@csrf_exempt
@require_http_methods(["GET"])
def read_compilation_result(request, project_id, compile_id):
    """
    Read compilation result - Temporarily disabled
    """
    return JsonResponse({
        'success': False,
        'error': 'QuantConnect service temporarily disabled for maintenance'
    }, status=503)


@csrf_exempt
@require_http_methods(["POST"])
def create_file(request):
    """
    Create file - Temporarily disabled
    """
    return JsonResponse({
        'success': False,
        'error': 'QuantConnect service temporarily disabled for maintenance'
    }, status=503)

#!/usr/bin/env python3
"""
Script para probar el endpoint community directamente sin servidor
"""

import os
import sys
import django
from datetime import datetime

# Configurar variables de entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
os.environ.setdefault('SECRET_KEY', 'kjbvcdasdcsdwc867456cg3uy4dxgr3467rt76tghjiu')
os.environ.setdefault('USE_SQLITE_LOCAL', 'true')
os.environ.setdefault('DEBUG', 'True')

# Configurar Django
django.setup()

from django.test import RequestFactory, Client
from django.contrib.auth.models import AnonymousUser
from strategies.views import StrategyViewSet
from strategies.models import Strategy
from strategies.serializers import StrategySummarySerializer

def test_endpoint_directly():
    """Probar el endpoint directamente"""
    
    print("🧪 Probando endpoint community directamente...")
    print("=" * 50)
    
    # 1. Verificar configuración de base de datos
    from django.conf import settings
    db_config = settings.DATABASES['default']
    print(f"Base de datos: {db_config['ENGINE']}")
    print(f"Archivo: {db_config['NAME']}")
    
    # 2. Verificar que hay estrategias
    count = Strategy.objects.count()
    print(f"Estrategias en DB: {count}")
    
    # 3. Probar serializer directamente
    print("\nProbando serializer...")
    try:
        strategies = Strategy.objects.all()[:2]
        serializer = StrategySummarySerializer(strategies, many=True)
        print(f"✅ Serializer funciona: {len(serializer.data)} estrategias")
        
        if serializer.data:
            first_strategy = serializer.data[0]
            print(f"Primera estrategia: {first_strategy['name']}")
            print(f"Status: {first_strategy.get('status', 'NO STATUS')}")
    except Exception as e:
        print(f"❌ Error en serializer: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 4. Probar vista directamente
    print("\nProbando vista...")
    try:
        factory = RequestFactory()
        request = factory.get('/api/strategies/community/')
        request.user = AnonymousUser()
        
        view = StrategyViewSet()
        view.request = request
        
        response = view.community(request)
        print(f"✅ Vista funciona: Status {response.status_code}")
        
        if response.status_code == 200:
            print(f"Count: {response.data.get('count', 'N/A')}")
            print(f"Results: {len(response.data.get('results', []))}")
            
            if response.data.get('results'):
                first_result = response.data['results'][0]
                print(f"Primera estrategia: {first_result['name']}")
                print(f"Status: {first_result.get('status', 'NO STATUS')}")
        else:
            print(f"Error: {response.data}")
            
    except Exception as e:
        print(f"❌ Error en vista: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 5. Probar con cliente de prueba
    print("\nProbando con cliente de prueba...")
    try:
        client = Client()
        response = client.get('/api/strategies/community/')
        print(f"✅ Cliente funciona: Status {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Count: {data.get('count', 'N/A')}")
            print(f"Results: {len(data.get('results', []))}")
        else:
            print(f"Error: {response.content}")
            
    except Exception as e:
        print(f"❌ Error en cliente: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ ¡Todas las pruebas pasaron!")
    return True

if __name__ == '__main__':
    try:
        success = test_endpoint_directly()
        
        if success:
            print("\n🎉 ¡El endpoint funciona correctamente!")
            print("El problema debe estar en el servidor o en la configuración de entorno.")
        else:
            print("\n❌ Se encontraron problemas en las pruebas.")
            
    except Exception as e:
        print(f"\n💥 Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

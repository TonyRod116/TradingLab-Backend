#!/usr/bin/env python3
"""
Script para probar el endpoint community directamente
"""

import os
import sys
import django
from datetime import datetime

# Add the project directory to Python path
sys.path.append('/home/tonirod/code/ga/projects/TradingLab-Backend-Clean')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
os.environ.setdefault('SECRET_KEY', 'kjbvcdasdcsdwc867456cg3uy4dxgr3467rt76tghjiu')
os.environ.setdefault('USE_SQLITE_LOCAL', 'true')

django.setup()

from strategies.models import Strategy
from strategies.serializers import StrategySummarySerializer
from strategies.views import StrategyViewSet
from django.test import RequestFactory
from django.contrib.auth.models import AnonymousUser

def test_community_endpoint():
    """Probar el endpoint community directamente"""
    
    print("🧪 Probando endpoint community...")
    
    # 1. Verificar que hay estrategias en la base de datos
    print("\n1. Verificando estrategias en la base de datos...")
    strategies_count = Strategy.objects.count()
    print(f"   - Total de estrategias: {strategies_count}")
    
    if strategies_count == 0:
        print("   ⚠️  No hay estrategias en la base de datos")
        return False
    
    # 2. Verificar que el serializer funciona
    print("\n2. Probando serializer StrategySummarySerializer...")
    try:
        strategies = Strategy.objects.all()[:2]  # Solo las primeras 2
        serializer = StrategySummarySerializer(strategies, many=True)
        print(f"   ✅ Serializer funciona correctamente")
        print(f"   - Datos serializados: {len(serializer.data)} estrategias")
        
        if serializer.data:
            print(f"   - Primera estrategia: {serializer.data[0]['name']}")
            print(f"   - Status: {serializer.data[0].get('status', 'NO STATUS')}")
        
    except Exception as e:
        print(f"   ❌ Error en serializer: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 3. Probar la vista community directamente
    print("\n3. Probando vista community directamente...")
    try:
        # Crear una request simulada
        factory = RequestFactory()
        request = factory.get('/api/strategies/community/')
        request.user = AnonymousUser()
        
        # Crear la vista
        view = StrategyViewSet()
        view.request = request
        
        # Llamar al método community
        response = view.community(request)
        
        print(f"   ✅ Vista community funciona correctamente")
        print(f"   - Status code: {response.status_code}")
        print(f"   - Response data: {response.data}")
        
        if response.status_code == 200:
            print(f"   - Count: {response.data.get('count', 'N/A')}")
            print(f"   - Results: {len(response.data.get('results', []))}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"   ❌ Error en vista community: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_connection():
    """Probar la conexión a la base de datos"""
    
    print("🔍 Verificando conexión a la base de datos...")
    
    try:
        # Verificar que podemos acceder a la tabla strategies
        from django.db import connection
        cursor = connection.cursor()
        
        # Verificar que la tabla existe
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategies';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print("   ✅ Tabla 'strategies' existe")
            
            # Verificar columnas
            cursor.execute("PRAGMA table_info(strategies);")
            columns = cursor.fetchall()
            column_names = [col[1] for col in columns]
            
            print(f"   - Columnas: {column_names}")
            
            if 'status' in column_names:
                print("   ✅ Columna 'status' existe")
            else:
                print("   ❌ Columna 'status' NO existe")
                return False
                
        else:
            print("   ❌ Tabla 'strategies' NO existe")
            return False
            
        return True
        
    except Exception as e:
        print(f"   ❌ Error en conexión a base de datos: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    print("🚀 Probando endpoint community...")
    print("=" * 50)
    
    try:
        # 1. Probar conexión a base de datos
        db_ok = test_database_connection()
        
        if not db_ok:
            print("\n❌ Problema con la base de datos. Abortando.")
            sys.exit(1)
        
        # 2. Probar endpoint community
        endpoint_ok = test_community_endpoint()
        
        if endpoint_ok:
            print("\n✅ ¡Endpoint community funciona correctamente!")
            sys.exit(0)
        else:
            print("\n❌ Problema con el endpoint community.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

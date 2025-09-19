#!/usr/bin/env python3
"""
Script para probar el endpoint de community directamente
"""

import os
import sys
import django

# Configurar variables de entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
os.environ.setdefault('SECRET_KEY', 'kjbvcdasdcsdwc867456cg3uy4dxgr3467rt76tghjiu')
os.environ.setdefault('USE_SQLITE_LOCAL', 'false')
os.environ.setdefault('DEBUG', 'True')
os.environ.setdefault('PGHOST', 'ep-falling-butterfly-a2qb7s68-pooler.eu-central-1.aws.neon.tech')
os.environ.setdefault('PGDATABASE', 'TradingLab_DB')
os.environ.setdefault('PGUSER', 'neondb_owner')
os.environ.setdefault('PGPASSWORD', 'npg_BAiojFUh3O7e')

# Configurar Django
django.setup()

from strategies.models import Strategy
from strategies.serializers import StrategySummarySerializer
from rest_framework.response import Response

def test_community_endpoint():
    """Probar el endpoint de community directamente"""
    
    print("🔍 Probando endpoint de community directamente")
    print("=" * 60)
    
    try:
        # Simular la lógica del endpoint
        strategies = Strategy.objects.filter(is_public=True).prefetch_related('backtests').select_related('user').order_by('-created_at')
        
        print(f"1. Estrategias encontradas en la consulta: {strategies.count()}")
        
        # Mostrar todas las estrategias
        for strategy in strategies:
            print(f"   - ID: {strategy.id}, Nombre: {strategy.name}")
            print(f"     Usuario: {strategy.user.username}")
            print(f"     Público: {strategy.is_public}, Status: {strategy.status}")
            print()
        
        # Serializar
        serializer = StrategySummarySerializer(strategies, many=True)
        
        print(f"2. Estrategias serializadas: {len(serializer.data)}")
        
        # Mostrar las estrategias serializadas
        for i, data in enumerate(serializer.data):
            print(f"   {i+1}. ID: {data.get('id')}, Nombre: {data.get('name')}")
            print(f"      Usuario: {data.get('created_by')}")
            print(f"      Público: {data.get('is_public')}")
            print()
        
        # Crear respuesta como el endpoint
        response_data = {
            'count': len(serializer.data),
            'results': serializer.data
        }
        
        print(f"3. Respuesta del endpoint:")
        print(f"   Count: {response_data['count']}")
        print(f"   Results: {len(response_data['results'])} estrategias")
        
        # Verificar específicamente las estrategias de Marta
        marta_in_results = [r for r in response_data['results'] if r.get('created_by') == 'Marta']
        print(f"4. Estrategias de Marta en la respuesta: {len(marta_in_results)}")
        
        for strategy in marta_in_results:
            print(f"   - {strategy.get('name')} (ID: {strategy.get('id')})")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n✅ Test completado!")

if __name__ == '__main__':
    test_community_endpoint()

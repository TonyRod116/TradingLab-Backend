#!/usr/bin/env python3
"""
Script para debuggear el endpoint de community
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

def debug_community():
    """Debuggear el endpoint de community"""
    
    print("🔍 Debuggeando endpoint de community")
    print("=" * 50)
    
    # 1. Obtener estrategias públicas
    strategies = Strategy.objects.filter(is_public=True).prefetch_related('backtests').select_related('user').order_by('-created_at')
    
    print(f"\n1. Estrategias públicas encontradas: {strategies.count()}")
    
    for strategy in strategies:
        print(f"   - ID: {strategy.id}, Nombre: {strategy.name}")
        print(f"     Usuario: {strategy.user.username}")
        print(f"     Público: {strategy.is_public}, Status: {strategy.status}")
        print(f"     Creado: {strategy.created_at}")
        print()
    
    # 2. Probar serialización
    print("\n2. Probando serialización:")
    try:
        serializer = StrategySummarySerializer(strategies, many=True)
        print(f"   ✅ Serialización exitosa: {len(serializer.data)} estrategias")
        
        # Mostrar las primeras 3 estrategias serializadas
        for i, data in enumerate(serializer.data[:3]):
            print(f"   Estrategia {i+1}:")
            print(f"     - ID: {data.get('id')}")
            print(f"     - Nombre: {data.get('name')}")
            print(f"     - Usuario: {data.get('created_by')}")
            print(f"     - Público: {data.get('is_public')}")
            print()
            
    except Exception as e:
        print(f"   ❌ Error en serialización: {e}")
        import traceback
        traceback.print_exc()
    
    # 3. Verificar específicamente las estrategias de Marta
    print("\n3. Estrategias de Marta:")
    marta_strategies = strategies.filter(user__username='Marta')
    print(f"   Estrategias de Marta encontradas: {marta_strategies.count()}")
    
    for strategy in marta_strategies:
        print(f"   - ID: {strategy.id}, Nombre: {strategy.name}")
        print(f"     Usuario: {strategy.user.username}")
        print(f"     Público: {strategy.is_public}, Status: {strategy.status}")
        
        # Probar serialización individual
        try:
            serializer = StrategySummarySerializer(strategy)
            print(f"     ✅ Serialización OK: {serializer.data.get('name')}")
        except Exception as e:
            print(f"     ❌ Error en serialización: {e}")
        print()
    
    print("\n✅ Debug completado!")

if __name__ == '__main__':
    try:
        debug_community()
    except Exception as e:
        print(f"\n💥 Error durante el debug: {e}")
        import traceback
        traceback.print_exc()




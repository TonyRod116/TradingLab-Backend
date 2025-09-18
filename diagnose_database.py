#!/usr/bin/env python3
"""
Script para diagnosticar problemas de base de datos
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

from django.conf import settings
from django.db import connection
from strategies.models import Strategy

def diagnose_database():
    """Diagnosticar la base de datos"""
    
    print("🔍 Diagnóstico de Base de Datos")
    print("=" * 50)
    
    # 1. Verificar configuración de base de datos
    print("\n1. Configuración de Base de Datos:")
    db_config = settings.DATABASES['default']
    print(f"   - Engine: {db_config['ENGINE']}")
    print(f"   - Name: {db_config['NAME']}")
    print(f"   - Host: {db_config.get('HOST', 'N/A')}")
    print(f"   - Port: {db_config.get('PORT', 'N/A')}")
    
    # 2. Verificar conexión
    print("\n2. Verificando Conexión:")
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            print(f"   ✅ Conexión exitosa: {result}")
    except Exception as e:
        print(f"   ❌ Error de conexión: {e}")
        return False
    
    # 3. Verificar tablas
    print("\n3. Verificando Tablas:")
    try:
        with connection.cursor() as cursor:
            if 'sqlite' in db_config['ENGINE']:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%strategy%';")
            else:
                cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%strategy%';")
            tables = cursor.fetchall()
            print(f"   - Tablas de estrategias: {[table[0] for table in tables]}")
    except Exception as e:
        print(f"   ❌ Error al listar tablas: {e}")
        return False
    
    # 4. Verificar estructura de tabla strategies
    print("\n4. Verificando Estructura de Tabla 'strategies':")
    try:
        with connection.cursor() as cursor:
            if 'sqlite' in db_config['ENGINE']:
                cursor.execute("PRAGMA table_info(strategies);")
                columns = cursor.fetchall()
                print(f"   - Columnas encontradas: {len(columns)}")
                for col in columns:
                    print(f"     * {col[1]} ({col[2]})")  # col[1] es el nombre, col[2] es el tipo
                
                # Verificar específicamente la columna status
                column_names = [col[1] for col in columns]  # col[1] es el nombre de la columna
            else:
                cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'strategies';")
                columns = cursor.fetchall()
                print(f"   - Columnas encontradas: {len(columns)}")
                for col in columns:
                    print(f"     * {col[0]} ({col[1]})")
                
                # Verificar específicamente la columna status
                column_names = [col[0] for col in columns]
            
            if 'status' in column_names:
                print("   ✅ Columna 'status' encontrada")
            else:
                print("   ❌ Columna 'status' NO encontrada")
                return False
    except Exception as e:
        print(f"   ❌ Error al verificar estructura: {e}")
        return False
    
    # 5. Verificar modelo Django
    print("\n5. Verificando Modelo Django:")
    try:
        strategy_fields = [f.name for f in Strategy._meta.fields]
        print(f"   - Campos del modelo: {strategy_fields}")
        
        if 'status' in strategy_fields:
            print("   ✅ Campo 'status' en modelo Django")
        else:
            print("   ❌ Campo 'status' NO en modelo Django")
            return False
    except Exception as e:
        print(f"   ❌ Error al verificar modelo: {e}")
        return False
    
    # 6. Probar consulta simple
    print("\n6. Probando Consulta Simple:")
    try:
        count = Strategy.objects.count()
        print(f"   ✅ Consulta exitosa: {count} estrategias")
        
        # Probar consulta con status
        strategies_with_status = Strategy.objects.filter(status='DRAFT').count()
        print(f"   ✅ Consulta con status exitosa: {strategies_with_status} estrategias DRAFT")
        
    except Exception as e:
        print(f"   ❌ Error en consulta: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # 7. Probar serializer
    print("\n7. Probando Serializer:")
    try:
        from strategies.serializers import StrategySummarySerializer
        strategies = Strategy.objects.all()[:1]
        serializer = StrategySummarySerializer(strategies, many=True)
        print(f"   ✅ Serializer funciona: {len(serializer.data)} estrategias")
        
        if serializer.data and 'status' in serializer.data[0]:
            print(f"   ✅ Campo 'status' en serializer: {serializer.data[0]['status']}")
        else:
            print("   ❌ Campo 'status' NO en serializer")
            return False
            
    except Exception as e:
        print(f"   ❌ Error en serializer: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n✅ ¡Diagnóstico completado exitosamente!")
    return True

if __name__ == '__main__':
    try:
        success = diagnose_database()
        
        if success:
            print("\n🎉 ¡Todo está funcionando correctamente!")
            print("El problema debe estar en el servidor o en la configuración de entorno.")
        else:
            print("\n❌ Se encontraron problemas en el diagnóstico.")
            
    except Exception as e:
        print(f"\n💥 Error durante el diagnóstico: {e}")
        import traceback
        traceback.print_exc()

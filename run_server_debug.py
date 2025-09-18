#!/usr/bin/env python3
"""
Script para ejecutar el servidor con debug de base de datos
"""

import os
import sys
import django
from django.core.management import execute_from_command_line
from django.conf import settings

# Configurar variables de entorno para usar SQLite
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
os.environ.setdefault('SECRET_KEY', 'kjbvcdasdcsdwc867456cg3uy4dxgr3467rt76tghjiu')
os.environ.setdefault('USE_SQLITE_LOCAL', 'true')
os.environ.setdefault('DEBUG', 'True')

# Configurar Django
django.setup()

def debug_database_config():
    """Debug de configuración de base de datos"""
    print("🔍 Configuración de Base de Datos del Servidor:")
    print("=" * 50)
    
    db_config = settings.DATABASES['default']
    print(f"Engine: {db_config['ENGINE']}")
    print(f"Name: {db_config['NAME']}")
    print(f"Host: {db_config.get('HOST', 'N/A')}")
    print(f"Port: {db_config.get('PORT', 'N/A')}")
    print(f"User: {db_config.get('USER', 'N/A')}")
    
    # Verificar si la tabla existe
    from django.db import connection
    try:
        with connection.cursor() as cursor:
            if 'sqlite' in db_config['ENGINE']:
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategies';")
                table_exists = cursor.fetchone()
                print(f"Tabla 'strategies' existe: {table_exists is not None}")
                
                if table_exists:
                    cursor.execute("PRAGMA table_info(strategies);")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]
                    print(f"Columnas: {column_names}")
                    print(f"Columna 'status' existe: {'status' in column_names}")
            else:
                print("Usando PostgreSQL")
    except Exception as e:
        print(f"Error al verificar tabla: {e}")
    
    print("=" * 50)

if __name__ == '__main__':
    # Debug de configuración
    debug_database_config()
    
    # Ejecutar el servidor
    print("🚀 Iniciando servidor...")
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])

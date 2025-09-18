#!/usr/bin/env python3
"""
Script para ejecutar el servidor con SQLite forzado
"""

import os
import sys
import django
from django.core.management import execute_from_command_line

# Configurar variables de entorno para usar SQLite
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
os.environ.setdefault('SECRET_KEY', 'kjbvcdasdcsdwc867456cg3uy4dxgr3467rt76tghjiu')
os.environ.setdefault('USE_SQLITE_LOCAL', 'true')
os.environ.setdefault('DEBUG', 'True')

# Configurar Django
django.setup()

if __name__ == '__main__':
    # Ejecutar el servidor
    execute_from_command_line(['manage.py', 'runserver', '0.0.0.0:8000'])

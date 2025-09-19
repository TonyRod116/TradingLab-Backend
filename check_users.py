#!/usr/bin/env python3
"""
Script para verificar usuarios en la base de datos
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

from django.contrib.auth import get_user_model
from strategies.models import Strategy

User = get_user_model()

def check_users_and_strategies():
    """Verificar usuarios y estrategias en la base de datos"""
    
    print("🔍 Verificando usuarios y estrategias en la base de datos")
    print("=" * 60)
    
    # 1. Verificar USUARIOS
    print("\n1. USUARIOS:")
    users = User.objects.all()
    print(f"   Total usuarios: {users.count()}")
    for user in users:
        print(f"   - ID: {user.id}, Username: {user.username}, Email: {user.email}")
        print(f"     Creado: {user.date_joined}")
        print(f"     Bio: {user.bio}")
        print(f"     Imagen: {user.profile_image}")
        print()
    
    # 2. Verificar ESTRATEGIAS
    print("\n2. ESTRATEGIAS:")
    strategies = Strategy.objects.all()
    print(f"   Total estrategias: {strategies.count()}")
    print(f"   Estrategias públicas: {strategies.filter(is_public=True).count()}")
    print(f"   Estrategias READY: {strategies.filter(status='READY').count()}")
    
    for strategy in strategies:
        print(f"   - ID: {strategy.id}, Nombre: {strategy.name}")
        print(f"     Usuario: {strategy.user.username}")
        print(f"     Público: {strategy.is_public}, Status: {strategy.status}")
        print(f"     Creado: {strategy.created_at}")
        print()
    
    # 3. Buscar específicamente a Marta
    print("\n3. BUSCANDO A MARTA:")
    marta_users = User.objects.filter(username__icontains='marta')
    if marta_users.exists():
        print(f"   ✅ Encontrada Marta: {marta_users.first().username}")
    else:
        print("   ❌ No se encontró usuario con 'marta' en el nombre")
    
    # 4. Buscar estrategias de Marta
    marta_strategies = Strategy.objects.filter(user__username__icontains='marta')
    if marta_strategies.exists():
        print(f"   ✅ Encontradas {marta_strategies.count()} estrategias de Marta")
        for strategy in marta_strategies:
            print(f"     - {strategy.name} ({strategy.symbol})")
    else:
        print("   ❌ No se encontraron estrategias de Marta")
    
    print("\n✅ Verificación completada!")

if __name__ == '__main__':
    try:
        check_users_and_strategies()
    except Exception as e:
        print(f"\n💥 Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()




#!/usr/bin/env python3
"""
Script para verificar datos reales en Neon
"""

import os
import sys
import django
from datetime import datetime

# Configurar variables de entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
os.environ.setdefault('SECRET_KEY', 'kjbvcdasdcsdwc867456cg3uy4dxgr3467rt76tghjiu')
os.environ.setdefault('USE_SQLITE_LOCAL', 'false')  # Usar Neon
os.environ.setdefault('DEBUG', 'True')

# Configurar Django
django.setup()

from django.contrib.auth import get_user_model
from strategies.models import Strategy, BacktestResult, Favorite

User = get_user_model()

def check_neon_data():
    """Verificar datos reales en Neon"""
    
    print("🔍 Verificando datos reales en Neon (PostgreSQL)")
    print("=" * 60)
    
    # 1. Verificar usuarios
    print("\n1. USUARIOS:")
    users = User.objects.all()
    print(f"   Total usuarios: {users.count()}")
    
    for user in users[:5]:  # Mostrar primeros 5
        print(f"   - ID: {user.id}, Username: {user.username}, Email: {user.email}")
        print(f"     Creado: {user.date_joined}")
        if hasattr(user, 'bio'):
            print(f"     Bio: {user.bio}")
        if hasattr(user, 'profile_image'):
            print(f"     Imagen: {user.profile_image}")
    
    # 2. Verificar estrategias
    print("\n2. ESTRATEGIAS:")
    strategies = Strategy.objects.all()
    print(f"   Total estrategias: {strategies.count()}")
    print(f"   Estrategias públicas: {strategies.filter(is_public=True).count()}")
    print(f"   Estrategias READY: {strategies.filter(status='READY').count()}")
    
    for strategy in strategies[:5]:  # Mostrar primeras 5
        print(f"   - ID: {strategy.id}, Nombre: {strategy.name}")
        print(f"     Usuario: {strategy.user.username if strategy.user else 'N/A'}")
        print(f"     Público: {strategy.is_public}, Status: {strategy.status}")
        print(f"     Creado: {strategy.created_at}")
    
    # 3. Verificar backtests
    print("\n3. BACKTESTS:")
    backtests = BacktestResult.objects.all()
    print(f"   Total backtests: {backtests.count()}")
    
    for backtest in backtests[:3]:  # Mostrar primeros 3
        print(f"   - ID: {backtest.id}, Estrategia: {backtest.strategy.name}")
        print(f"     Total Return: {backtest.total_return}")
        print(f"     Win Rate: {backtest.win_rate}")
        print(f"     Total Trades: {backtest.total_trades}")
    
    # 4. Verificar favoritos
    print("\n4. FAVORITOS:")
    favorites = Favorite.objects.all()
    print(f"   Total favoritos: {favorites.count()}")
    
    for favorite in favorites[:3]:  # Mostrar primeros 3
        print(f"   - Usuario: {favorite.user.username}")
        print(f"     Estrategia: {favorite.strategy.name}")
        print(f"     Favorito desde: {favorite.created_at}")
    
    print("\n✅ Verificación completada!")

if __name__ == '__main__':
    try:
        check_neon_data()
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()

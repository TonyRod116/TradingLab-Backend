#!/usr/bin/env python3
"""
Script para probar el endpoint de backtest
"""

import os
import sys
import django
import requests
import json

# Configurar variables de entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
os.environ.setdefault('SECRET_KEY', 'kjbvcdasdcsdwc867456cg3uy4dxgr3467rt76tghjiu')
os.environ.setdefault('DEBUG', 'True')

# Configurar Django
django.setup()

from users.models import User
from strategies.models import Strategy
from rest_framework_simplejwt.tokens import RefreshToken

def get_auth_token():
    """Obtener token de autenticación"""
    try:
        # Buscar usuario existente
        user = User.objects.first()
        if not user:
            print("❌ No hay usuarios disponibles")
            return None
        
        # Generar token
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        
        print(f"✅ Token generado para usuario: {user.username}")
        return access_token
        
    except Exception as e:
        print(f"❌ Error generando token: {e}")
        return None

def test_backtest_endpoint():
    """Probar el endpoint de backtest"""
    
    print("🧪 Probando endpoint de backtest...")
    print("=" * 50)
    
    # 1. Obtener token de autenticación
    print("\n1. Obteniendo token de autenticación...")
    token = get_auth_token()
    if not token:
        return False
    
    # 2. Buscar una estrategia existente
    print("\n2. Buscando estrategia existente...")
    strategy = Strategy.objects.filter(status='READY').first()
    if not strategy:
        print("   ❌ No hay estrategias con status READY")
        # Buscar cualquier estrategia
        strategy = Strategy.objects.first()
        if not strategy:
            print("   ❌ No hay estrategias en la base de datos")
            return False
        print(f"   ⚠️  Usando estrategia con status: {strategy.status}")
    else:
        print(f"   ✅ Estrategia encontrada: {strategy.name} (ID: {strategy.id})")
    
    # 3. Probar endpoint de backtest
    print(f"\n3. Probando endpoint de backtest para estrategia {strategy.id}...")
    url = f"http://localhost:8000/api/strategies/{strategy.id}/backtest/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    backtest_data = {
        "start_date": "2020-01-01T00:00:00Z",
        "end_date": "2024-12-31T23:59:59Z",
        "initial_capital": 100000,
        "commission": 0.0,
        "slippage": 0.0
    }
    
    try:
        response = requests.post(url, json=backtest_data, headers=headers)
        
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200 or response.status_code == 202:
            result = response.json()
            print("   ✅ Backtest iniciado exitosamente!")
            print(f"   - Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"   ❌ Error en la respuesta: {response.status_code}")
            print(f"   - Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error haciendo request: {e}")
        return False

def test_run_backtest_endpoint():
    """Probar el endpoint run_backtest"""
    
    print("\n🧪 Probando endpoint run_backtest...")
    print("=" * 50)
    
    # 1. Obtener token de autenticación
    print("\n1. Obteniendo token de autenticación...")
    token = get_auth_token()
    if not token:
        return False
    
    # 2. Buscar una estrategia existente
    print("\n2. Buscando estrategia existente...")
    strategy = Strategy.objects.filter(status='READY').first()
    if not strategy:
        print("   ❌ No hay estrategias con status READY")
        # Buscar cualquier estrategia
        strategy = Strategy.objects.first()
        if not strategy:
            print("   ❌ No hay estrategias en la base de datos")
            return False
        print(f"   ⚠️  Usando estrategia con status: {strategy.status}")
    else:
        print(f"   ✅ Estrategia encontrada: {strategy.name} (ID: {strategy.id})")
    
    # 3. Probar endpoint run_backtest
    print(f"\n3. Probando endpoint run_backtest para estrategia {strategy.id}...")
    url = f"http://localhost:8000/api/strategies/{strategy.id}/run_backtest/"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}"
    }
    
    backtest_data = {
        "start_date": "2020-01-01T00:00:00Z",
        "end_date": "2024-12-31T23:59:59Z",
        "initial_capital": 100000,
        "commission": 0.0,
        "slippage": 0.0
    }
    
    try:
        response = requests.post(url, json=backtest_data, headers=headers)
        
        print(f"   - Status Code: {response.status_code}")
        print(f"   - Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200 or response.status_code == 202:
            result = response.json()
            print("   ✅ Backtest iniciado exitosamente!")
            print(f"   - Response: {json.dumps(result, indent=2)}")
            return True
        else:
            print(f"   ❌ Error en la respuesta: {response.status_code}")
            print(f"   - Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"   ❌ Error haciendo request: {e}")
        return False

if __name__ == '__main__':
    try:
        print("🚀 Iniciando pruebas de endpoints de backtest...")
        
        # Probar endpoint /backtest/
        success1 = test_backtest_endpoint()
        
        # Probar endpoint /run_backtest/
        success2 = test_run_backtest_endpoint()
        
        if success1 or success2:
            print("\n✅ ¡Al menos un endpoint de backtest funciona!")
        else:
            print("\n❌ Ningún endpoint de backtest funciona.")
            
    except Exception as e:
        print(f"\n💥 Error durante las pruebas: {e}")
        import traceback
        traceback.print_exc()

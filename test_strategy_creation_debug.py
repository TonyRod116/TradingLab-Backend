#!/usr/bin/env python3
"""
Script para probar la creación de estrategias y debuggear el problema
"""

import os
import sys
import django
from datetime import datetime

# Configurar variables de entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
os.environ.setdefault('SECRET_KEY', 'kjbvcdasdcsdwc867456cg3uy4dxgr3467rt76tghjiu')
os.environ.setdefault('DEBUG', 'True')

# Configurar Django
django.setup()

from strategies.models import Strategy
from strategies.serializers import StrategyCreateSerializer
from users.models import User

def test_strategy_creation():
    """Probar la creación de estrategias"""
    
    print("🧪 Probando creación de estrategias...")
    print("=" * 50)
    
    # 1. Verificar que hay usuarios
    print("\n1. Verificando usuarios...")
    users = User.objects.all()
    print(f"   - Usuarios disponibles: {users.count()}")
    if users.exists():
        print(f"   - Primer usuario: {users.first().username}")
        test_user = users.first()
    else:
        print("   ❌ No hay usuarios. Creando usuario de prueba...")
        test_user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        print(f"   ✅ Usuario creado: {test_user.username}")
    
    # 2. Probar serializer
    print("\n2. Probando serializer...")
    test_data = {
        'name': 'Test Strategy Creator Debug',
        'description': 'Test strategy for debugging creator',
        'symbol': 'ES',
        'timeframe': '1h',
        'entry_rules': [
            {
                'name': 'Entry Rule 1',
                'rule_type': 'condition',
                'action_type': 'buy',
                'conditions': [
                    {
                        'left_operand': 'rsi',
                        'operator': 'lt',
                        'right_operand': 'rsi_30',
                        'logical_operator': 'and'
                    }
                ],
                'priority': 1,
                'parameters': {}
            }
        ],
        'exit_rules': [
            {
                'name': 'Exit Rule 1',
                'rule_type': 'condition',
                'action_type': 'sell',
                'conditions': [
                    {
                        'left_operand': 'rsi',
                        'operator': 'gt',
                        'right_operand': 'rsi_70',
                        'logical_operator': 'and'
                    }
                ],
                'priority': 1,
                'parameters': {}
            }
        ],
        'stop_loss_type': 'percentage',
        'stop_loss_value': 1.0,
        'take_profit_type': 'percentage',
        'take_profit_value': 2.0,
        'initial_capital': 10000,
        'status': 'DRAFT'
    }
    
    serializer = StrategyCreateSerializer(data=test_data)
    if serializer.is_valid():
        print("   ✅ Serializer válido")
        print(f"   - Datos validados: {serializer.validated_data['name']}")
    else:
        print("   ❌ Serializer inválido")
        print(f"   - Errores: {serializer.errors}")
        return False
    
    # 3. Crear estrategia
    print("\n3. Creando estrategia...")
    try:
        # Asignar usuario
        strategy_data = serializer.validated_data.copy()
        strategy_data['user'] = test_user
        
        strategy = Strategy.objects.create(**strategy_data)
        print(f"   ✅ Estrategia creada: ID {strategy.id}")
        print(f"   - Nombre: {strategy.name}")
        print(f"   - Status: {strategy.status}")
        print(f"   - Usuario: {strategy.user.username}")
        
        # 4. Verificar que se puede acceder al endpoint de backtest
        print("\n4. Verificando endpoints de backtest...")
        print(f"   - Estrategia ID: {strategy.id}")
        print(f"   - URL backtest: /api/strategies/{strategy.id}/backtest/")
        print(f"   - URL run_backtest: /api/strategies/{strategy.id}/run_backtest/")
        
        # 5. Probar serialización para API
        print("\n5. Probando serialización para API...")
        from strategies.serializers import StrategySerializer
        api_serializer = StrategySerializer(strategy)
        api_data = api_serializer.data
        print(f"   - ID en API: {api_data.get('id')}")
        print(f"   - Nombre en API: {api_data.get('name')}")
        print(f"   - Status en API: {api_data.get('status')}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error creando estrategia: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        success = test_strategy_creation()
        
        if success:
            print("\n✅ ¡Prueba de creación de estrategias exitosa!")
            print("El problema debe estar en el frontend o en la autenticación.")
        else:
            print("\n❌ Se encontraron problemas en la creación de estrategias.")
            
    except Exception as e:
        print(f"\n💥 Error durante la prueba: {e}")
        import traceback
        traceback.print_exc()

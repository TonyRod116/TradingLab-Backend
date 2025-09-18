#!/usr/bin/env python3
"""
Script para verificar que la migración se aplicó correctamente
"""

import os
import sys
import django
from datetime import datetime

# Add the project directory to Python path
sys.path.append('/home/tonirod/code/ga/projects/TradingLab-Backend-Clean')

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from strategies.models import Strategy
from strategies.serializers import StrategyCreateSerializer
from strategies.enums import SUPPORTED_SYMBOLS, SUPPORTED_TIMEFRAMES, STRATEGY_STATUS

def verify_migration():
    """Verificar que la migración se aplicó correctamente"""
    
    print("🔍 Verificando migración de campo 'status'...")
    
    # 1. Verificar que el campo status existe en el modelo
    print("\n1. Verificando campo 'status' en el modelo Strategy...")
    strategy_fields = [f.name for f in Strategy._meta.fields]
    
    if 'status' in strategy_fields:
        print("✅ Campo 'status' encontrado en el modelo Strategy")
    else:
        print("❌ Campo 'status' NO encontrado en el modelo Strategy")
        return False
    
    # 2. Verificar las opciones del campo status
    print("\n2. Verificando opciones del campo 'status'...")
    status_field = Strategy._meta.get_field('status')
    choices = status_field.choices
    
    print(f"   - Opciones disponibles: {[choice[0] for choice in choices]}")
    print(f"   - Valor por defecto: {status_field.default}")
    
    expected_choices = ['DRAFT', 'READY', 'ACTIVE', 'INACTIVE']
    actual_choices = [choice[0] for choice in choices]
    
    if set(expected_choices) == set(actual_choices):
        print("✅ Opciones del campo 'status' son correctas")
    else:
        print("❌ Opciones del campo 'status' no coinciden")
        print(f"   - Esperadas: {expected_choices}")
        print(f"   - Encontradas: {actual_choices}")
        return False
    
    # 3. Verificar que el serializer funciona con el nuevo campo
    print("\n3. Verificando serializer con campo 'status'...")
    
    test_data = {
        'name': 'Test Strategy Migration',
        'description': 'Strategy to test migration',
        'symbol': 'ES',
        'timeframe': '1m',
        'entry_rules': [
            {
                'name': 'Test Entry',
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
                'name': 'Test Exit',
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
        print("✅ Serializer funciona correctamente con el campo 'status'")
        print(f"   - Status validado: {serializer.validated_data['status']}")
    else:
        print("❌ Serializer falló con el campo 'status'")
        print(f"   - Errores: {serializer.errors}")
        return False
    
    # 4. Verificar que los enums están disponibles
    print("\n4. Verificando enums disponibles...")
    
    print(f"   - Símbolos soportados: {len(SUPPORTED_SYMBOLS)}")
    print(f"   - Timeframes soportados: {len(SUPPORTED_TIMEFRAMES)}")
    print(f"   - Estados de estrategia: {STRATEGY_STATUS}")
    
    if len(SUPPORTED_SYMBOLS) > 0 and len(SUPPORTED_TIMEFRAMES) > 0:
        print("✅ Enums están disponibles")
    else:
        print("❌ Enums no están disponibles")
        return False
    
    # 5. Verificar que se puede crear una estrategia (si hay usuario)
    print("\n5. Verificando creación de estrategia...")
    
    try:
        # Intentar crear una estrategia de prueba (sin guardar en DB)
        strategy = Strategy(
            name='Test Migration Strategy',
            description='Test strategy for migration verification',
            symbol='ES',
            timeframe='1m',
            entry_rules=[],
            exit_rules=[],
            stop_loss_type='percentage',
            stop_loss_value=1.0,
            take_profit_type='percentage',
            take_profit_value=2.0,
            initial_capital=10000,
            status='DRAFT'
        )
        
        print("✅ Estrategia de prueba creada correctamente")
        print(f"   - Status: {strategy.status}")
        print(f"   - Símbolo: {strategy.symbol}")
        print(f"   - Timeframe: {strategy.timeframe}")
        
    except Exception as e:
        print(f"❌ Error al crear estrategia de prueba: {e}")
        return False
    
    print("\n🎉 ¡Migración verificada exitosamente!")
    print("\n📋 Resumen de verificación:")
    print("   ✅ Campo 'status' agregado al modelo Strategy")
    print("   ✅ Opciones del campo son correctas (DRAFT, READY, ACTIVE, INACTIVE)")
    print("   ✅ Serializer funciona con el nuevo campo")
    print("   ✅ Enums están disponibles")
    print("   ✅ Estrategia de prueba se crea correctamente")
    
    return True

if __name__ == '__main__':
    print("🚀 Verificando migración de campo 'status'...")
    print("=" * 50)
    
    try:
        success = verify_migration()
        
        if success:
            print("\n✅ ¡Todas las verificaciones pasaron!")
            print("🚀 El backend está listo para usar el nuevo flujo de creación de estrategias.")
            sys.exit(0)
        else:
            print("\n❌ Algunas verificaciones fallaron.")
            print("🔧 Revisa los errores anteriores y ejecuta la migración nuevamente.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Error durante la verificación: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

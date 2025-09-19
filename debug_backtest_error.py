#!/usr/bin/env python3
"""
Script para diagnosticar el error 500 en backtests
"""

import os
import sys
import django
from datetime import datetime
import traceback

# Configurar variables de entorno
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
os.environ.setdefault('SECRET_KEY', 'kjbvcdasdcsdwc867456cg3uy4dxgr3467rt76tghjiu')
os.environ.setdefault('USE_SQLITE_LOCAL', 'true')
os.environ.setdefault('DEBUG', 'True')

# Configurar Django
django.setup()

from django.conf import settings
from strategies.models import Strategy
from strategies.backtest_engine import BacktestEngine
from strategies.serializers import StrategyCreateSerializer
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()

def test_backtest_creation():
    """Probar la creación de una estrategia y backtest paso a paso"""
    
    print("🔍 Diagnóstico de Error 500 en Backtest")
    print("=" * 50)
    
    try:
        # 1. Crear una estrategia de prueba simple
        print("\n1. Creando estrategia de prueba...")
        
        strategy_data = {
            'name': 'test_debug_strategy',
            'description': 'Test strategy for debugging',
            'symbol': 'ES',
            'timeframe': '4h',
            'entry_rules': [
                {
                    'name': 'Entry Rule 1',
                    'rule_type': 'condition',
                    'action_type': 'sell',
                    'conditions': [
                        {
                            'left_operand': 'close',
                            'operator': 'gt',
                            'right_operand': 'vwap_plus_2.0',
                            'logical_operator': 'and'
                        }
                    ],
                    'priority': 1,
                    'parameters': {}
                }
            ],
            'exit_rules': [],
            'stop_loss_type': 'percentage',
            'stop_loss_value': 2.0,
            'take_profit_type': 'percentage',
            'take_profit_value': 3.0,
            'initial_capital': 100000,
            'status': 'READY'
        }
        
        # 2. Probar serializer
        print("\n2. Probando serializer...")
        serializer = StrategyCreateSerializer(data=strategy_data)
        if serializer.is_valid():
            print("   ✅ Serializer válido")
            print(f"   - Datos normalizados: {serializer.validated_data}")
        else:
            print("   ❌ Errores en serializer:")
            for field, errors in serializer.errors.items():
                print(f"     - {field}: {errors}")
            return False
        
        # 3. Crear o obtener usuario
        print("\n3. Creando/obteniendo usuario...")
        try:
            user = User.objects.get(username='test_user')
            print(f"   ✅ Usuario existente: {user.username}")
        except User.DoesNotExist:
            # Usar un email único para evitar conflictos
            import time
            unique_email = f'test_{int(time.time())}@example.com'
            user = User.objects.create_user(
                username=f'test_user_{int(time.time())}',
                email=unique_email,
                password='testpass123'
            )
            print(f"   ✅ Usuario creado: {user.username}")
        
        # 4. Crear estrategia
        print("\n4. Creando estrategia en BD...")
        strategy = serializer.save(user=user)
        print(f"   ✅ Estrategia creada: ID {strategy.id}")
        
        # 5. Probar backtest engine
        print("\n5. Probando BacktestEngine...")
        engine = BacktestEngine()
        
        # 6. Probar run_backtest
        print("\n6. Ejecutando backtest...")
        try:
            result = engine.run_backtest(
                strategy=strategy,
                start_date=datetime(2020, 9, 1),  # Usar fechas dentro del rango de datos
                end_date=datetime(2020, 9, 30),
                initial_capital=Decimal('100000'),
                commission=Decimal('4.00'),
                slippage=Decimal('0.25')
            )
            print(f"   ✅ Backtest exitoso: ID {result.id}")
            print(f"   - Total trades: {result.total_trades}")
            print(f"   - Total return: {result.total_return}")
            
        except Exception as e:
            print(f"   ❌ Error en backtest: {str(e)}")
            print(f"   - Tipo de error: {type(e)}")
            print(f"   - Traceback:")
            traceback.print_exc()
            return False
        
        # 7. Limpiar
        print("\n7. Limpiando estrategia de prueba...")
        strategy.delete()
        print("   ✅ Estrategia eliminada")
        
        print("\n✅ ¡Diagnóstico completado exitosamente!")
        return True
        
    except Exception as e:
        print(f"\n💥 Error durante el diagnóstico: {str(e)}")
        print(f"   - Tipo de error: {type(e)}")
        print(f"   - Traceback:")
        traceback.print_exc()
        return False

def test_vwap_calculation():
    """Probar específicamente el cálculo de VWAP"""
    
    print("\n🔍 Probando cálculo de VWAP...")
    
    try:
        from strategies.backtest_engine import BacktestEngine
        from market_data.parquet_service import ParquetDataService
        
        # Probar ParquetDataService
        parquet_service = ParquetDataService()
        print(f"   - Parquet service disponible: {parquet_service is not None}")
        
        # Probar obtención de datos
        df = parquet_service.get_candles(
            symbol='ES',
            timeframe='4h',
            start_date=datetime(2020, 9, 1),
            end_date=datetime(2020, 9, 10)  # Solo unos días para prueba
        )
        
        print(f"   - Datos obtenidos: {len(df)} filas")
        print(f"   - Columnas: {list(df.columns)}")
        
        # Probar cálculo de VWAP
        engine = BacktestEngine()
        df_with_indicators = engine._ensure_indicators(df, None)
        
        print(f"   - Columnas después de indicadores: {list(df_with_indicators.columns)}")
        
        # Verificar si vwap_plus_2_0 existe
        if 'vwap_plus_2_0' in df_with_indicators.columns:
            print("   ✅ vwap_plus_2_0 calculado correctamente")
        else:
            print("   ❌ vwap_plus_2_0 NO encontrado")
            print(f"   - Columnas VWAP disponibles: {[col for col in df_with_indicators.columns if 'vwap' in col]}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Error en cálculo de VWAP: {str(e)}")
        traceback.print_exc()
        return False

if __name__ == '__main__':
    try:
        print("🚀 Iniciando diagnóstico completo...")
        
        # Test 1: Cálculo de VWAP
        vwap_ok = test_vwap_calculation()
        
        # Test 2: Backtest completo
        backtest_ok = test_backtest_creation()
        
        if vwap_ok and backtest_ok:
            print("\n🎉 ¡Todos los tests pasaron!")
            print("El problema debe estar en el servidor web o en la configuración de entorno.")
        else:
            print("\n❌ Se encontraron problemas en los tests.")
            
    except Exception as e:
        print(f"\n💥 Error fatal: {e}")
        traceback.print_exc()

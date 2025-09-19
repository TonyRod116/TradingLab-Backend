#!/usr/bin/env python3
"""
Script para probar la carga de datos Parquet con fechas específicas
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

from market_data.parquet_service import ParquetDataService

def test_parquet_with_dates():
    """Probar la carga de datos Parquet con fechas específicas"""
    
    print("🔍 Probando carga de datos Parquet con fechas")
    print("=" * 50)
    
    parquet_service = ParquetDataService()
    
    # Probar diferentes rangos de fechas
    test_cases = [
        {
            'name': 'Sin filtros de fecha',
            'start_date': None,
            'end_date': None
        },
        {
            'name': 'Rango completo (2020-08-30 a 2025-08-29)',
            'start_date': datetime(2020, 8, 30),
            'end_date': datetime(2025, 8, 29)
        },
        {
            'name': 'Rango parcial (2020-09-01 a 2020-09-30)',
            'start_date': datetime(2020, 9, 1),
            'end_date': datetime(2020, 9, 30)
        },
        {
            'name': 'Rango muy pequeño (2020-09-01 a 2020-09-02)',
            'start_date': datetime(2020, 9, 1),
            'end_date': datetime(2020, 9, 2)
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        try:
            df = parquet_service.get_candles(
                'ES', '4h',
                start_date=test_case['start_date'],
                end_date=test_case['end_date']
            )
            print(f"   - Datos cargados: {len(df)} filas")
            if len(df) > 0:
                print(f"   - Primera fecha: {df['date'].iloc[0]}")
                print(f"   - Última fecha: {df['date'].iloc[-1]}")
                print(f"   - Columnas: {list(df.columns)}")
        except Exception as e:
            print(f"   - Error: {e}")
    
    return True

if __name__ == '__main__':
    try:
        test_parquet_with_dates()
        print("\n✅ ¡Prueba completada!")
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()





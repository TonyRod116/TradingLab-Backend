#!/usr/bin/env python3
"""
Script para probar la carga de datos Parquet
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

from market_data.timeframe_aggregator import TimeframeAggregator
from market_data.parquet_service import ParquetDataService

def test_parquet_loading():
    """Probar la carga de datos Parquet"""
    
    print("🔍 Probando carga de datos Parquet")
    print("=" * 50)
    
    # 1. Probar TimeframeAggregator directamente
    print("\n1. Probando TimeframeAggregator...")
    aggregator = TimeframeAggregator()
    df = aggregator.load_from_parquet('ES', '4h')
    print(f"   - Datos cargados: {len(df)} filas")
    print(f"   - Columnas: {list(df.columns)}")
    
    if len(df) > 0:
        print(f"   - Primera fecha: {df['date'].iloc[0]}")
        print(f"   - Última fecha: {df['date'].iloc[-1]}")
        print(f"   - Rango de precios: {df['close'].min():.2f} - {df['close'].max():.2f}")
    
    # 2. Probar ParquetDataService
    print("\n2. Probando ParquetDataService...")
    parquet_service = ParquetDataService()
    df_service = parquet_service.get_candles('ES', '4h', 
                                            start_date=datetime(2020, 1, 1),
                                            end_date=datetime(2020, 1, 10))
    print(f"   - Datos del servicio: {len(df_service)} filas")
    print(f"   - Columnas: {list(df_service.columns)}")
    
    if len(df_service) > 0:
        print(f"   - Primera fecha: {df_service['date'].iloc[0]}")
        print(f"   - Última fecha: {df_service['date'].iloc[-1]}")
    
    # 3. Probar diferentes timeframes
    print("\n3. Probando diferentes timeframes...")
    timeframes = ['1m', '5m', '15m', '1h', '4h', '1d']
    for tf in timeframes:
        df_tf = aggregator.load_from_parquet('ES', tf)
        print(f"   - {tf}: {len(df_tf)} filas")
    
    return len(df) > 0

if __name__ == '__main__':
    try:
        success = test_parquet_loading()
        
        if success:
            print("\n✅ ¡Datos Parquet cargados correctamente!")
        else:
            print("\n❌ No se pudieron cargar los datos Parquet")
            
    except Exception as e:
        print(f"\n💥 Error: {e}")
        import traceback
        traceback.print_exc()





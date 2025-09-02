"""
Ejemplo de uso del sistema de optimización con Parquet
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from market_data.timeframe_aggregator import TimeframeAggregator
from market_data.parquet_service import ParquetDataService
from market_data.models import HistoricalData


def example_basic_usage():
    """Ejemplo básico de uso del sistema"""
    print("=== Ejemplo Básico de Uso ===")
    
    # Inicializar servicios
    aggregator = TimeframeAggregator()
    parquet_service = ParquetDataService()
    
    # Verificar archivos disponibles
    print("\n1. Archivos Parquet disponibles:")
    files = aggregator.list_available_files()
    for file_info in files:
        print(f"  - {file_info['symbol']} {file_info['timeframe']}: {file_info.get('rows', 0):,} velas")
    
    # Obtener datos usando el servicio optimizado
    print("\n2. Obteniendo datos optimizados:")
    symbol = 'ES'
    timeframe = '5m'
    
    # Obtener últimos 100 velas
    df = parquet_service.get_candles(
        symbol=symbol,
        timeframe=timeframe,
        limit=100
    )
    
    if not df.empty:
        print(f"  - Obtenidas {len(df)} velas de {timeframe}")
        print(f"  - Rango de fechas: {df['date'].min()} a {df['date'].max()}")
        print(f"  - Último precio: ${df['close'].iloc[-1]:.2f}")
    else:
        print(f"  - No hay datos disponibles para {symbol} {timeframe}")
    
    # Obtener última vela
    print("\n3. Última vela:")
    latest = parquet_service.get_latest_candle(symbol, timeframe)
    if latest:
        print(f"  - Fecha: {latest['date']}")
        print(f"  - OHLC: ${latest['open']:.2f} / ${latest['high']:.2f} / ${latest['low']:.2f} / ${latest['close']:.2f}")
        print(f"  - Volumen: {latest['volume']:,}")
    
    # Verificar disponibilidad de Parquet
    print("\n4. Disponibilidad de Parquet:")
    for tf in ['1m', '5m', '15m', '1h', '4h', '1d']:
        available = parquet_service.is_parquet_available(symbol, tf)
        print(f"  - {tf}: {'✓' if available else '✗'}")


def example_performance_comparison():
    """Ejemplo de comparación de rendimiento"""
    print("\n=== Comparación de Rendimiento ===")
    
    parquet_service = ParquetDataService()
    symbol = 'ES'
    timeframe = '5m'
    
    # Obtener estadísticas de rendimiento
    print("\n1. Estadísticas del sistema:")
    stats = parquet_service.get_performance_stats()
    print(f"  - Total archivos: {stats['total_files']}")
    print(f"  - Tamaño total: {stats['total_size_mb']} MB")
    print(f"  - Total velas: {stats['total_candles']:,}")
    
    # Comparar fuentes de datos
    print("\n2. Comparación de fuentes de datos:")
    for tf in ['1m', '5m', '15m', '1h']:
        summary = parquet_service.get_data_summary(symbol, tf)
        source = summary.get('source', 'unknown')
        candles = summary.get('total_candles', 0)
        print(f"  - {tf}: {source} ({candles:,} velas)")


def example_data_aggregation():
    """Ejemplo de agregación de datos"""
    print("\n=== Ejemplo de Agregación de Datos ===")
    
    aggregator = TimeframeAggregator()
    
    # Obtener datos de 1 minuto de la base de datos
    print("\n1. Obteniendo datos de 1 minuto:")
    queryset = HistoricalData.objects.filter(
        symbol='ES',
        timeframe='1m'
    ).order_by('date')[:1000]  # Últimas 1000 velas
    
    if not queryset.exists():
        print("  - No hay datos de 1 minuto disponibles")
        return
    
    # Convertir a DataFrame
    data = list(queryset.values(
        'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
    ))
    
    df_1m = pd.DataFrame(data)
    df_1m = df_1m.rename(columns={
        'open_price': 'open',
        'high_price': 'high',
        'low_price': 'low',
        'close_price': 'close'
    })
    df_1m['date'] = pd.to_datetime(df_1m['date'])
    df_1m['symbol'] = 'ES'
    
    print(f"  - Obtenidas {len(df_1m)} velas de 1 minuto")
    print(f"  - Rango: {df_1m['date'].min()} a {df_1m['date'].max()}")
    
    # Agregar a diferentes timeframes
    print("\n2. Agregando a diferentes timeframes:")
    for target_tf in ['5m', '15m', '1h']:
        try:
            agg_df = aggregator.aggregate_timeframe(df_1m, target_tf)
            print(f"  - {target_tf}: {len(agg_df)} velas generadas")
            
            if not agg_df.empty:
                print(f"    Rango: {agg_df['date'].min()} a {agg_df['date'].max()}")
        except Exception as e:
            print(f"  - {target_tf}: Error - {e}")


def example_cache_management():
    """Ejemplo de gestión de cache"""
    print("\n=== Gestión de Cache ===")
    
    parquet_service = ParquetDataService()
    symbol = 'ES'
    
    # Calentar cache
    print("\n1. Calentando cache:")
    results = parquet_service.warm_cache(symbol, ['1m', '5m', '15m', '1h'], days_back=7)
    
    for timeframe, result in results.items():
        if result['success']:
            candles = result['candles_cached']
            print(f"  - {timeframe}: {candles:,} velas cacheadas")
        else:
            print(f"  - {timeframe}: Error - {result['error']}")
    
    # Verificar disponibilidad
    print("\n2. Timeframes disponibles:")
    available = parquet_service.get_available_timeframes(symbol)
    for tf in available:
        print(f"  - {tf}: ✓")


if __name__ == "__main__":
    import pandas as pd
    
    try:
        example_basic_usage()
        example_performance_comparison()
        example_data_aggregation()
        example_cache_management()
        
        print("\n=== Ejemplo Completado ===")
        print("El sistema de optimización con Parquet está funcionando correctamente!")
        
    except Exception as e:
        print(f"Error en el ejemplo: {e}")
        import traceback
        traceback.print_exc()

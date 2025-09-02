#!/usr/bin/env python3
"""
Script de configuración inicial para el sistema de optimización con Parquet
"""

import os
import sys
import django
from datetime import datetime, timedelta

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'project.settings')
django.setup()

from django.core.management import call_command
from market_data.models import HistoricalData
from market_data.timeframe_aggregator import TimeframeAggregator
from market_data.parquet_service import ParquetDataService


def check_prerequisites():
    """Verificar prerrequisitos"""
    print("🔍 Verificando prerrequisitos...")
    
    # Verificar directorio de datos
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        print(f"✅ Directorio de datos creado: {data_dir}")
    else:
        print(f"✅ Directorio de datos existe: {data_dir}")
    
    # Verificar datos de 1 minuto
    count_1m = HistoricalData.objects.filter(timeframe='1m').count()
    if count_1m > 0:
        print(f"✅ Datos de 1 minuto disponibles: {count_1m:,} velas")
    else:
        print("❌ No hay datos de 1 minuto disponibles")
        return False
    
    # Verificar símbolos disponibles
    symbols = HistoricalData.objects.values_list('symbol', flat=True).distinct()
    print(f"✅ Símbolos disponibles: {', '.join(symbols)}")
    
    return True


def generate_initial_parquet_files(symbol='ES'):
    """Generar archivos Parquet iniciales"""
    print(f"\n🚀 Generando archivos Parquet para {symbol}...")
    
    try:
        # Generar archivos Parquet
        call_command(
            'generate_parquet_candles',
            symbol=symbol,
            timeframes=['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
            verbosity=2
        )
        print("✅ Archivos Parquet generados exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error generando archivos Parquet: {e}")
        return False


def verify_parquet_files(symbol='ES'):
    """Verificar archivos Parquet generados"""
    print(f"\n🔍 Verificando archivos Parquet para {symbol}...")
    
    aggregator = TimeframeAggregator()
    timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
    
    all_good = True
    for timeframe in timeframes:
        file_info = aggregator.get_file_info(symbol, timeframe)
        if file_info.get('exists'):
            rows = file_info.get('rows', 0)
            size_mb = file_info.get('file_size_mb', 0)
            print(f"✅ {timeframe}: {rows:,} velas ({size_mb:.1f} MB)")
        else:
            print(f"❌ {timeframe}: Archivo no encontrado")
            all_good = False
    
    return all_good


def test_optimized_service(symbol='ES'):
    """Probar el servicio optimizado"""
    print(f"\n🧪 Probando servicio optimizado para {symbol}...")
    
    parquet_service = ParquetDataService()
    
    # Probar diferentes timeframes
    timeframes = ['1m', '5m', '15m', '1h']
    for timeframe in timeframes:
        try:
            # Obtener datos
            df = parquet_service.get_candles(symbol, timeframe, limit=10)
            
            if not df.empty:
                source = 'parquet' if parquet_service.is_parquet_available(symbol, timeframe) else 'database'
                print(f"✅ {timeframe}: {len(df)} velas obtenidas desde {source}")
            else:
                print(f"⚠️  {timeframe}: No hay datos disponibles")
                
        except Exception as e:
            print(f"❌ {timeframe}: Error - {e}")
    
    # Probar última vela
    try:
        latest = parquet_service.get_latest_candle(symbol, '1m')
        if latest:
            print(f"✅ Última vela 1m: ${latest['close']:.2f} a las {latest['date']}")
        else:
            print("⚠️  No se pudo obtener la última vela")
    except Exception as e:
        print(f"❌ Error obteniendo última vela: {e}")


def setup_cron_job():
    """Configurar cron job para actualización automática"""
    print("\n⏰ Configuración de cron job...")
    
    project_path = os.path.dirname(os.path.dirname(__file__))
    cron_command = f"0 6 * * * cd {project_path} && python manage.py update_parquet_candles --symbol ES --days-back 1"
    
    print("Para configurar actualización automática diaria, agrega esta línea a tu crontab:")
    print(f"  {cron_command}")
    print("\nPara editar crontab, ejecuta: crontab -e")


def show_usage_examples():
    """Mostrar ejemplos de uso"""
    print("\n📚 Ejemplos de uso:")
    
    print("\n1. Generar archivos Parquet:")
    print("   python manage.py generate_parquet_candles --symbol ES")
    
    print("\n2. Actualizar incrementalmente:")
    print("   python manage.py update_parquet_candles --symbol ES --days-back 1")
    
    print("\n3. Usar APIs optimizadas:")
    print("   curl 'http://localhost:8000/api/market-data/optimized-data/?symbol=ES&timeframe=5m&limit=100'")
    
    print("\n4. Ver estadísticas de rendimiento:")
    print("   curl 'http://localhost:8000/api/market-data/optimized-data/performance_stats/'")
    
    print("\n5. Ejecutar ejemplo completo:")
    print("   python examples/parquet_usage_example.py")


def main():
    """Función principal"""
    print("🚀 Configuración del Sistema de Optimización con Parquet")
    print("=" * 60)
    
    # Verificar prerrequisitos
    if not check_prerequisites():
        print("\n❌ Prerrequisitos no cumplidos. Abortando configuración.")
        return False
    
    # Obtener símbolo
    symbols = list(HistoricalData.objects.values_list('symbol', flat=True).distinct())
    if not symbols:
        print("❌ No hay símbolos disponibles en la base de datos")
        return False
    
    symbol = symbols[0]  # Usar el primer símbolo disponible
    print(f"\n📊 Usando símbolo: {symbol}")
    
    # Generar archivos Parquet
    if not generate_initial_parquet_files(symbol):
        print("\n❌ Error en la generación de archivos Parquet")
        return False
    
    # Verificar archivos generados
    if not verify_parquet_files(symbol):
        print("\n❌ Algunos archivos Parquet no se generaron correctamente")
        return False
    
    # Probar servicio optimizado
    test_optimized_service(symbol)
    
    # Mostrar configuración de cron
    setup_cron_job()
    
    # Mostrar ejemplos de uso
    show_usage_examples()
    
    print("\n" + "=" * 60)
    print("✅ Configuración completada exitosamente!")
    print("\n🎯 Próximos pasos:")
    print("1. Configura el cron job para actualización automática")
    print("2. Actualiza tu frontend para usar las APIs optimizadas")
    print("3. Monitorea el rendimiento con las estadísticas disponibles")
    print("4. Lee la documentación completa en PARQUET_OPTIMIZATION.md")
    
    return True


if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⏹️  Configuración cancelada por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error durante la configuración: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

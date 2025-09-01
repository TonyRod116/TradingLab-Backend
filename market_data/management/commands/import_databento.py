from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import sys
from pathlib import Path

# Importar directamente desde la aplicación
from market_data.services import DatabentoService


class Command(BaseCommand):
    help = 'Import data from Databento (.dbn) files to Django database'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Path to .dbn file to import'
        )
        
        parser.add_argument(
            '--symbol',
            type=str,
            default='ES',
            help='Future symbol (default: ES)'
        )
        
        parser.add_argument(
            '--timeframe',
            type=str,
            default='1m',
            choices=['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
            help='Data timeframe (default: 1m)'
        )
        
        parser.add_argument(
            '--output-format',
            type=str,
            choices=['csv', 'parquet', 'direct'],
            default='direct',
            help='Intermediate output format (default: direct)'
        )
        
        parser.add_argument(
            '--output-dir',
            type=str,
            default='data',
            help='Output directory for intermediate files (default: data)'
        )
        
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for import (default: 1000)'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Process data without saving to database'
        )
        
        parser.add_argument(
            '--list-files',
            action='store_true',
            help='List available .dbn files in directory'
        )
    
    def handle(self, *args, **options):
        try:
            if options['list_files']:
                self.list_dbn_files()
                return
            
            if not options['file']:
                # Find .dbn files in current directory
                dbn_files = self.find_dbn_files()
                if not dbn_files:
                    raise CommandError('No .dbn files found in current directory')
                
                if len(dbn_files) == 1:
                    file_path = dbn_files[0]
                    self.stdout.write(f"Using found file: {file_path}")
                else:
                    self.stdout.write(".dbn files found:")
                    for i, file_path in enumerate(dbn_files, 1):
                        self.stdout.write(f"  {i}. {file_path}")
                    
                    choice = input("\nSelect file number to import (or 'q' to quit): ")
                    if choice.lower() == 'q':
                        return
                    
                    try:
                        file_index = int(choice) - 1
                        if 0 <= file_index < len(dbn_files):
                            file_path = dbn_files[file_index]
                        else:
                            raise CommandError('Invalid file number')
                    except ValueError:
                        raise CommandError('Invalid input')
            else:
                file_path = options['file']
            
            # Check if file exists
            if not os.path.exists(file_path):
                raise CommandError(f'File not found: {file_path}')
            
            self.stdout.write(f"Processing file: {file_path}")
            self.stdout.write(f"Symbol: {options['symbol']}")
            self.stdout.write(f"Timeframe: {options['timeframe']}")
            self.stdout.write(f"Output format: {options['output_format']}")
            
            if options['dry_run']:
                self.stdout.write("DRY-RUN MODE: Data will not be saved to database")
            
            # Procesar el archivo
            self.process_dbn_file(
                file_path=file_path,
                symbol=options['symbol'],
                timeframe=options['timeframe'],
                output_format=options['output_format'],
                output_dir=options['output_dir'],
                batch_size=options['batch_size'],
                dry_run=options['dry_run']
            )
            
        except Exception as e:
            raise CommandError(f'Error: {str(e)}')
    
    def find_dbn_files(self):
        """Busca archivos .dbn en el directorio actual"""
        current_dir = Path.cwd()
        dbn_files = list(current_dir.glob('*.dbn'))
        return [str(f) for f in dbn_files]
    
    def list_dbn_files(self):
        """Lista archivos .dbn disponibles"""
        dbn_files = self.find_dbn_files()
        if not dbn_files:
            self.stdout.write("No se encontraron archivos .dbn en el directorio actual")
            return
        
        self.stdout.write("Archivos .dbn disponibles:")
        for i, file_path in enumerate(dbn_files, 1):
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            self.stdout.write(f"  {i}. {os.path.basename(file_path)} ({file_size_mb:.1f} MB)")
    
    def process_dbn_file(self, file_path, symbol, timeframe, output_format, output_dir, batch_size, dry_run):
        """Procesa un archivo .dbn"""
        try:
            # Paso 1: Leer el archivo .dbn
            self.stdout.write("Leyendo archivo .dbn...")
            df = DatabentoService.read_dbn_with_python(file_path)
            
            if df.empty:
                raise CommandError("No se pudieron leer datos del archivo .dbn")
            
            self.stdout.write(f"Datos leídos exitosamente. Shape: {df.shape}")
            self.stdout.write(f"Columnas disponibles: {list(df.columns)}")
            
            # Paso 2: Procesar datos OHLCV
            self.stdout.write("Procesando datos OHLCV...")
            df_processed = DatabentoService.process_ohlcv_data(df, symbol, timeframe)
            
            self.stdout.write(f"DataFrame procesado. Shape: {df_processed.shape}")
            self.stdout.write(f"Rango de fechas: {df_processed['date'].min()} a {df_processed['date'].max()}")
            
            # Paso 3: Guardar en formato intermedio si se solicita
            if output_format != 'direct':
                self.stdout.write(f"Guardando en formato {output_format}...")
                if output_format == 'csv':
                    output_file = os.path.join(output_dir, f"{symbol}_{timeframe}_{os.path.basename(file_path).replace('.dbn', '.csv')}")
                    df_processed.to_csv(output_file, index=False)
                    self.stdout.write(f"Archivo CSV guardado: {output_file}")
                elif output_format == 'parquet':
                    output_file = os.path.join(output_dir, f"{symbol}_{timeframe}_{os.path.basename(file_path).replace('.dbn', '.parquet')}")
                    df_processed.to_parquet(output_file, index=False)
                    self.stdout.write(f"Archivo Parquet guardado: {output_file}")
            
            # Paso 4: Importar a Django (si no es dry-run)
            if not dry_run:
                self.stdout.write("Importando datos a la base de datos...")
                result = DatabentoService.import_dataframe_to_django(
                    df_processed, 
                    symbol, 
                    timeframe, 
                    batch_size
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Importación completada exitosamente!\n"
                        f"  - Filas importadas: {result['imported']}\n"
                        f"  - Filas omitidas: {result['skipped']}\n"
                        f"  - Tiempo de procesamiento: {result['processing_time']:.2f} segundos"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"DRY-RUN completado. Datos listos para importar:\n"
                        f"  - Total de filas: {len(df_processed)}\n"
                        f"  - Símbolo: {symbol}\n"
                        f"  - Timeframe: {timeframe}\n"
                        f"  - Rango de fechas: {df_processed['date'].min()} a {df_processed['date'].max()}"
                    )
                )
            
            # Paso 5: Mostrar estadísticas básicas
            self.show_data_statistics(df_processed)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error procesando archivo: {str(e)}")
            )
            raise
    
    def show_data_statistics(self, df):
        """Muestra estadísticas básicas de los datos"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("ESTADÍSTICAS DE LOS DATOS")
        self.stdout.write("="*50)
        
        # Estadísticas de precios
        self.stdout.write(f"Precio más alto: ${df['high'].max():.2f}")
        self.stdout.write(f"Precio más bajo: ${df['low'].min():.2f}")
        self.stdout.write(f"Precio promedio: ${df['close'].mean():.2f}")
        
        # Estadísticas de volumen
        self.stdout.write(f"Volumen total: {df['volume'].sum():,}")
        self.stdout.write(f"Volumen promedio: {df['volume'].mean():.0f}")
        self.stdout.write(f"Volumen máximo: {df['volume'].max():,}")
        
        # Estadísticas de velas
        bullish_count = len(df[df['close'] > df['open']])
        bearish_count = len(df[df['close'] < df['open']])
        doji_count = len(df[abs(df['close'] - df['open']) < 0.01])
        
        self.stdout.write(f"Velas alcistas: {bullish_count}")
        self.stdout.write(f"Velas bajistas: {bearish_count}")
        self.stdout.write(f"Velas doji: {doji_count}")
        
        # Cambio de precio total
        total_change = df['close'].iloc[-1] - df['open'].iloc[0]
        total_change_percent = (total_change / df['open'].iloc[0]) * 100
        
        self.stdout.write(f"Cambio total de precio: ${total_change:.2f} ({total_change_percent:+.2f}%)")
        
        self.stdout.write("="*50)

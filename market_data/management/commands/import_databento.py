from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import sys
from pathlib import Path

# Import directly from the application
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
            
            # Process the file
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
        """Search for .dbn files in current directory"""
        current_dir = Path.cwd()
        dbn_files = list(current_dir.glob('*.dbn'))
        return [str(f) for f in dbn_files]
    
    def list_dbn_files(self):
        """List available .dbn files"""
        dbn_files = self.find_dbn_files()
        if not dbn_files:
            self.stdout.write("No .dbn files found in current directory")
            return
        
        self.stdout.write("Available .dbn files:")
        for i, file_path in enumerate(dbn_files, 1):
            file_size = os.path.getsize(file_path)
            file_size_mb = file_size / (1024 * 1024)
            self.stdout.write(f"  {i}. {os.path.basename(file_path)} ({file_size_mb:.1f} MB)")
    
    def process_dbn_file(self, file_path, symbol, timeframe, output_format, output_dir, batch_size, dry_run):
        """Process a .dbn file"""
        try:
            # Step 1: Read the .dbn file
            self.stdout.write("Reading .dbn file...")
            df = DatabentoService.read_dbn_with_python(file_path)
            
            if df.empty:
                raise CommandError("Could not read data from .dbn file")
            
            self.stdout.write(f"Data read successfully. Shape: {df.shape}")
            self.stdout.write(f"Available columns: {list(df.columns)}")
            
            # Step 2: Process OHLCV data
            self.stdout.write("Processing OHLCV data...")
            df_processed = DatabentoService.process_ohlcv_data(df, symbol, timeframe)
            
            self.stdout.write(f"DataFrame processed. Shape: {df_processed.shape}")
            self.stdout.write(f"Date range: {df_processed['date'].min()} to {df_processed['date'].max()}")
            
            # Step 3: Save in intermediate format if requested
            if output_format != 'direct':
                self.stdout.write(f"Saving in {output_format} format...")
                if output_format == 'csv':
                    output_file = os.path.join(output_dir, f"{symbol}_{timeframe}_{os.path.basename(file_path).replace('.dbn', '.csv')}")
                    df_processed.to_csv(output_file, index=False)
                    self.stdout.write(f"CSV file saved: {output_file}")
                elif output_format == 'parquet':
                    output_file = os.path.join(output_dir, f"{symbol}_{timeframe}_{os.path.basename(file_path).replace('.dbn', '.parquet')}")
                    df_processed.to_parquet(output_file, index=False)
                    self.stdout.write(f"Parquet file saved: {output_file}")
            
            # Step 4: Import to Django (if not dry-run)
            if not dry_run:
                self.stdout.write("Importing data to database...")
                result = DatabentoService.import_dataframe_to_django(
                    df_processed, 
                    symbol, 
                    timeframe, 
                    batch_size
                )
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Import completed successfully!\n"
                        f"  - Imported rows: {result['imported']}\n"
                        f"  - Skipped rows: {result['skipped']}\n"
                        f"  - Processing time: {result['processing_time']:.2f} seconds"
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"DRY-RUN completed. Data ready to import:\n"
                        f"  - Total rows: {len(df_processed)}\n"
                        f"  - Símbolo: {symbol}\n"
                        f"  - Timeframe: {timeframe}\n"
                        f"  - Date range: {df_processed['date'].min()} to {df_processed['date'].max()}"
                    )
                )
            
            # Step 5: Show basic statistics
            self.show_data_statistics(df_processed)
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"Error processing file: {str(e)}")
            )
            raise
    
    def show_data_statistics(self, df):
        """Show basic data statistics"""
        self.stdout.write("\n" + "="*50)
        self.stdout.write("DATA STATISTICS")
        self.stdout.write("="*50)
        
        # Price statistics
        self.stdout.write(f"Highest price: ${df['high'].max():.2f}")
        self.stdout.write(f"Lowest price: ${df['low'].min():.2f}")
        self.stdout.write(f"Average price: ${df['close'].mean():.2f}")
        
        # Volume statistics
        self.stdout.write(f"Total volume: {df['volume'].sum():,}")
        self.stdout.write(f"Average volume: {df['volume'].mean():.0f}")
        self.stdout.write(f"Maximum volume: {df['volume'].max():,}")
        
        # Candle statistics
        bullish_count = len(df[df['close'] > df['open']])
        bearish_count = len(df[df['close'] < df['open']])
        doji_count = len(df[abs(df['close'] - df['open']) < 0.01])
        
        self.stdout.write(f"Bullish candles: {bullish_count}")
        self.stdout.write(f"Bearish candles: {bearish_count}")
        self.stdout.write(f"Doji candles: {doji_count}")
        
        # Total price change
        total_change = df['close'].iloc[-1] - df['open'].iloc[0]
        total_change_percent = (total_change / df['open'].iloc[0]) * 100
        
        self.stdout.write(f"Total price change: ${total_change:.2f} ({total_change_percent:+.2f}%)")
        
        self.stdout.write("="*50)

import os
import time
import pandas as pd
from datetime import datetime
from decimal import Decimal
from django.db import transaction
from django.conf import settings
from .models import HistoricalData, DataImportLog


class DatabentoService:
    """Service for processing Databento (.dbn) files"""
    
    @staticmethod
    def decode_dbn_to_csv(dbn_file_path, output_dir='data'):
        """
        Decode .dbn file to CSV using dbn tool
        
        Args:
            dbn_file_path (str): Path to .dbn file
            output_dir (str): Output directory for CSV
        
        Returns:
            str: Path to generated CSV file
        """
        try:
            # Check if .dbn file exists
            if not os.path.exists(dbn_file_path):
                raise FileNotFoundError(f".dbn file not found: {dbn_file_path}")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output CSV filename
            base_name = os.path.splitext(os.path.basename(dbn_file_path))[0]
            csv_file_path = os.path.join(output_dir, f"{base_name}.csv")
            
            # Command to decode using dbn
            cmd = f"dbn decode {dbn_file_path} --output {csv_file_path}"
            
            print(f"Executing: {cmd}")
            result = os.system(cmd)
            
            if result == 0:
                print(f"File decoded successfully: {csv_file_path}")
                return csv_file_path
            else:
                raise Exception(f"Error decoding .dbn file. Exit code: {result}")
                
        except Exception as e:
            print(f"Error decoding .dbn file: {e}")
            raise
    
    @staticmethod
    def decode_dbn_to_parquet(dbn_file_path, output_dir='data'):
        """
        Decode a .dbn file to Parquet using the dbn tool
        
        Args:
            dbn_file_path (str): Path to .dbn file
            output_dir (str): Output directory for Parquet
        
        Returns:
            str: Path to generated Parquet file
        """
        try:
            # Check if .dbn file exists
            if not os.path.exists(dbn_file_path):
                raise FileNotFoundError(f".dbn file not found: {dbn_file_path}")
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate output Parquet filename
            base_name = os.path.splitext(os.path.basename(dbn_file_path))[0]
            parquet_file_path = os.path.join(output_dir, f"{base_name}.parquet")
            
            # Command to decode using dbn
            cmd = f"dbn decode {dbn_file_path} --output {parquet_file_path}"
            
            print(f"Executing: {cmd}")
            result = os.system(cmd)
            
            if result == 0:
                print(f"File decoded successfully: {parquet_file_path}")
                return parquet_file_path
            else:
                raise Exception(f"Error decoding .dbn file. Exit code: {result}")
                
        except Exception as e:
            print(f"Error decoding .dbn file: {e}")
            raise
    
    @staticmethod
    def read_dbn_with_python(dbn_file_path):
        """
        Read a .dbn file directly with Python using the databento library
        
        Args:
            dbn_file_path (str): Path to .dbn file
        
        Returns:
            pd.DataFrame: DataFrame with OHLCV data
        """
        try:
            import databento as db
            
            # Create Databento client without API key for local files
            client = db.Historical()
            
            # Read the .dbn file
            print(f"Reading .dbn file: {dbn_file_path}")
            data = client.read_dbn(dbn_file_path)
            
            # Convert to DataFrame
            df = data.to_df()
            
            print(f"Data read successfully. Shape: {df.shape}")
            print(f"Available columns: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"Error reading .dbn file with Python: {e}")
            print("Using alternative method...")
            return DatabentoService._read_dbn_alternative(dbn_file_path)
    
    @staticmethod
    def _read_dbn_alternative(dbn_file_path):
        """
        Alternative method to read .dbn files if databento is not available
        
        Args:
            dbn_file_path (str): Path to .dbn file
        
        Returns:
            pd.DataFrame: DataFrame with OHLCV data
        """
        try:
            # Try using subprocess to execute dbn as external command
            import subprocess
            import json
            
            # Command to get file information
            cmd_info = f"dbn info {dbn_file_path} --json"
            result = subprocess.run(cmd_info, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Could not get file information: {result.stderr}")
            
            # Parse file information
            info = json.loads(result.stdout)
            print(f"File information: {info}")
            
            # Decode to temporary CSV
            temp_csv = dbn_file_path.replace('.dbn', '_temp.csv')
            cmd_decode = f"dbn decode {dbn_file_path} --output {temp_csv}"
            
            result = subprocess.run(cmd_decode, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Error decoding file: {result.stderr}")
            
            # Read temporary CSV
            df = pd.read_csv(temp_csv)
            
            # Clean temporary file
            os.remove(temp_csv)
            
            return df
            
        except Exception as e:
            print(f"Error in alternative method: {e}")
            raise
    
    @staticmethod
    def process_ohlcv_data(df, symbol='ES', timeframe='1m'):
        """
        Procesa un DataFrame con datos OHLCV y los prepara para importar
        
        Args:
            df (pd.DataFrame): DataFrame con datos OHLCV
            symbol (str): Símbolo del futuro
            timeframe (str): Data timeframe
        
        Returns:
            pd.DataFrame: Processed and clean DataFrame
        """
        try:
            # Make a copy to not modify the original
            df_processed = df.copy()
            
            # Mapear columnas comunes de Databento
            column_mapping = {
                'ts_event': 'date',
                'ts_init': 'date',
                'open': 'open',
                'high': 'high',
                'low': 'low',
                'close': 'close',
                'volume': 'volume',
                'symbol': 'symbol',
                'exchange': 'exchange'
            }
            
            # Rename columns if necessary
            for old_name, new_name in column_mapping.items():
                if old_name in df_processed.columns and new_name not in df_processed.columns:
                    df_processed = df_processed.rename(columns={old_name: new_name})
            
            # Check required columns
            required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df_processed.columns]
            
            if missing_columns:
                print(f"Available columns: {list(df_processed.columns)}")
                raise ValueError(f"Missing columns: {missing_columns}")
            
            # Convert timestamp to datetime
            if 'date' in df_processed.columns:
                if df_processed['date'].dtype == 'int64':
                    # Timestamp in nanoseconds
                    df_processed['date'] = pd.to_datetime(df_processed['date'], unit='ns')
                elif df_processed['date'].dtype == 'object':
                    # Try to parse as string
                    df_processed['date'] = pd.to_datetime(df_processed['date'])
            
            # Convert prices to float
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                if col in df_processed.columns:
                    df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
            
            # Convert volume to int
            if 'volume' in df_processed.columns:
                df_processed['volume'] = pd.to_numeric(df_processed['volume'], errors='coerce').astype('Int64')
            
            # Add additional columns
            df_processed['symbol'] = symbol
            df_processed['timeframe'] = timeframe
            
            # Limpiar datos
            df_processed = df_processed.dropna(subset=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Sort by date
            df_processed = df_processed.sort_values('date')
            
            # Reset index
            df_processed = df_processed.reset_index(drop=True)
            
            print(f"DataFrame processed successfully. Shape: {df_processed.shape}")
            print(f"Date range: {df_processed['date'].min()} to {df_processed['date'].max()}")
            
            return df_processed
            
        except Exception as e:
            print(f"Error processing OHLCV data: {e}")
            raise
    
    @staticmethod
    def import_dataframe_to_django(df, symbol='ES', timeframe='1m', batch_size=1000):
        """
        Importa un DataFrame a la base de datos Django
        
        Args:
            df (pd.DataFrame): DataFrame con datos OHLCV
            symbol (str): Símbolo del futuro
            timeframe (str): Data timeframe
            batch_size (int): Batch size for import
        
        Returns:
            dict: Import result
        """
        start_time = time.time()
        
        try:
            # Create import log
            import_log = DataImportLog.objects.create(
                file_name=f"DataFrame_{symbol}_{timeframe}",
                file_path="DataFrame in memory",
                symbol=symbol,
                timeframe=timeframe,
                total_rows=len(df),
                status='processing'
            )
            
            imported_count = 0
            skipped_count = 0
            
            # Procesar en lotes
            for i in range(0, len(df), batch_size):
                batch = df.iloc[i:i+batch_size]
                
                with transaction.atomic():
                    for _, row in batch.iterrows():
                        try:
                            # Create or update record
                            historical_data, created = HistoricalData.objects.update_or_create(
                                symbol=row['symbol'],
                                date=row['date'],
                                timeframe=row['timeframe'],
                                defaults={
                                    'open_price': Decimal(str(row['open'])),
                                    'high_price': Decimal(str(row['high'])),
                                    'low_price': Decimal(str(row['low'])),
                                    'close_price': Decimal(str(row['close'])),
                                    'volume': int(row['volume'])
                                }
                            )
                            
                            if created:
                                imported_count += 1
                            else:
                                skipped_count += 1
                                
                        except Exception as e:
                            print(f"Error processing row: {row}, Error: {e}")
                            skipped_count += 1
                            continue
                
                # Update progress
                progress = min(100, (i + batch_size) / len(df) * 100)
                print(f"Progress: {progress:.1f}% - Imported: {imported_count}, Skipped: {skipped_count}")
            
            # Calculate processing time
            processing_time = time.time() - start_time
            
            # Actualizar log de importación
            import_log.imported_rows = imported_count
            import_log.skipped_rows = skipped_count
            import_log.start_date = df['date'].min()
            import_log.end_date = df['date'].max()
            import_log.status = 'completed'
            import_log.processing_time = processing_time
            import_log.save()
            
            result = {
                'success': True,
                'imported': imported_count,
                'skipped': skipped_count,
                'total_rows': len(df),
                'symbol': symbol,
                'timeframe': timeframe,
                'processing_time': processing_time,
                'date_range': {
                    'start': df['date'].min().isoformat(),
                    'end': df['date'].max().isoformat()
                }
            }
            
            print(f"Import completed successfully:")
            print(f"  - Imported rows: {imported_count}")
            print(f"  - Skipped rows: {skipped_count}")
            print(f"  - Processing time: {processing_time:.2f} seconds")
            
            return result
            
        except Exception as e:
            # Update import log with error
            if 'import_log' in locals():
                import_log.status = 'failed'
                import_log.error_message = str(e)
                import_log.processing_time = time.time() - start_time
                import_log.save()
            
            print(f"Error in import: {e}")
            raise
    
    @staticmethod
    def get_data_for_backtest(symbol='ES', timeframe='1m', start_date=None, end_date=None, limit=None):
        """
        Obtiene datos listos para backtesting
        
        Args:
            symbol (str): Símbolo del futuro
            timeframe (str): Data timeframe
            start_date (datetime): Start date
            end_date (datetime): End date
            limit (int): Record limit
        
        Returns:
            pd.DataFrame: DataFrame listo para backtesting
        """
        try:
            queryset = HistoricalData.objects.filter(symbol=symbol, timeframe=timeframe)
            
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
            
            if end_date:
                queryset = queryset.filter(date__lte=end_date)
            
            if limit:
                queryset = queryset[:limit]
            
            # Sort by date
            queryset = queryset.order_by('date')
            
            # Convert to DataFrame
            data = list(queryset.values('date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'))
            df = pd.DataFrame(data)
            
            if df.empty:
                return pd.DataFrame()
            
            # Renombrar columnas para compatibilidad con backtesting
            df = df.rename(columns={
                'open_price': 'open',
                'high_price': 'high',
                'low_price': 'low',
                'close_price': 'close'
            })
            
            # Convert prices to float
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                df[col] = df[col].astype(float)
            
            # Convert volume to int
            df['volume'] = df['volume'].astype(int)
            
            # Establecer fecha como índice
            df = df.set_index('date')
            
            print(f"DataFrame for backtesting created. Shape: {df.shape}")
            print(f"Date range: {df.index.min()} to {df.index.max()}")
            
            return df
            
        except Exception as e:
            print(f"Error getting data for backtesting: {e}")
            raise

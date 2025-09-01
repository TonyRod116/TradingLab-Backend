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
        Decodifica un archivo .dbn a Parquet usando la herramienta dbn
        
        Args:
            dbn_file_path (str): Ruta al archivo .dbn
            output_dir (str): Directorio de salida para el Parquet
        
        Returns:
            str: Ruta al archivo Parquet generado
        """
        try:
            # Verificar que el archivo .dbn existe
            if not os.path.exists(dbn_file_path):
                raise FileNotFoundError(f"Archivo .dbn no encontrado: {dbn_file_path}")
            
            # Crear directorio de salida si no existe
            os.makedirs(output_dir, exist_ok=True)
            
            # Generar nombre del archivo Parquet de salida
            base_name = os.path.splitext(os.path.basename(dbn_file_path))[0]
            parquet_file_path = os.path.join(output_dir, f"{base_name}.parquet")
            
            # Comando para decodificar usando dbn
            cmd = f"dbn decode {dbn_file_path} --output {parquet_file_path}"
            
            print(f"Ejecutando: {cmd}")
            result = os.system(cmd)
            
            if result == 0:
                print(f"Archivo decodificado exitosamente: {parquet_file_path}")
                return parquet_file_path
            else:
                raise Exception(f"Error al decodificar archivo .dbn. Código de salida: {result}")
                
        except Exception as e:
            print(f"Error decodificando archivo .dbn: {e}")
            raise
    
    @staticmethod
    def read_dbn_with_python(dbn_file_path):
        """
        Lee un archivo .dbn directamente con Python usando la librería databento
        
        Args:
            dbn_file_path (str): Ruta al archivo .dbn
        
        Returns:
            pd.DataFrame: DataFrame con los datos OHLCV
        """
        try:
            import databento as db
            
            # Crear cliente de Databento sin API key para archivos locales
            client = db.Historical()
            
            # Leer el archivo .dbn
            print(f"Leyendo archivo .dbn: {dbn_file_path}")
            data = client.read_dbn(dbn_file_path)
            
            # Convertir a DataFrame
            df = data.to_df()
            
            print(f"Datos leídos exitosamente. Shape: {df.shape}")
            print(f"Columnas disponibles: {list(df.columns)}")
            
            return df
            
        except Exception as e:
            print(f"Error leyendo archivo .dbn con Python: {e}")
            print("Usando método alternativo...")
            return DatabentoService._read_dbn_alternative(dbn_file_path)
    
    @staticmethod
    def _read_dbn_alternative(dbn_file_path):
        """
        Método alternativo para leer archivos .dbn si databento no está disponible
        
        Args:
            dbn_file_path (str): Ruta al archivo .dbn
        
        Returns:
            pd.DataFrame: DataFrame con los datos OHLCV
        """
        try:
            # Intentar usar subprocess para ejecutar dbn como comando externo
            import subprocess
            import json
            
            # Comando para obtener información del archivo
            cmd_info = f"dbn info {dbn_file_path} --json"
            result = subprocess.run(cmd_info, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"No se pudo obtener información del archivo: {result.stderr}")
            
            # Parsear información del archivo
            info = json.loads(result.stdout)
            print(f"Información del archivo: {info}")
            
            # Decodificar a CSV temporal
            temp_csv = dbn_file_path.replace('.dbn', '_temp.csv')
            cmd_decode = f"dbn decode {dbn_file_path} --output {temp_csv}"
            
            result = subprocess.run(cmd_decode, shell=True, capture_output=True, text=True)
            
            if result.returncode != 0:
                raise Exception(f"Error decodificando archivo: {result.stderr}")
            
            # Leer CSV temporal
            df = pd.read_csv(temp_csv)
            
            # Limpiar archivo temporal
            os.remove(temp_csv)
            
            return df
            
        except Exception as e:
            print(f"Error en método alternativo: {e}")
            raise
    
    @staticmethod
    def process_ohlcv_data(df, symbol='ES', timeframe='1m'):
        """
        Procesa un DataFrame con datos OHLCV y los prepara para importar
        
        Args:
            df (pd.DataFrame): DataFrame con datos OHLCV
            symbol (str): Símbolo del futuro
            timeframe (str): Timeframe de los datos
        
        Returns:
            pd.DataFrame: DataFrame procesado y limpio
        """
        try:
            # Hacer una copia para no modificar el original
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
            
            # Renombrar columnas si es necesario
            for old_name, new_name in column_mapping.items():
                if old_name in df_processed.columns and new_name not in df_processed.columns:
                    df_processed = df_processed.rename(columns={old_name: new_name})
            
            # Verificar columnas requeridas
            required_columns = ['date', 'open', 'high', 'low', 'close', 'volume']
            missing_columns = [col for col in required_columns if col not in df_processed.columns]
            
            if missing_columns:
                print(f"Columnas disponibles: {list(df_processed.columns)}")
                raise ValueError(f"Columnas faltantes: {missing_columns}")
            
            # Convertir timestamp a datetime
            if 'date' in df_processed.columns:
                if df_processed['date'].dtype == 'int64':
                    # Timestamp en nanosegundos
                    df_processed['date'] = pd.to_datetime(df_processed['date'], unit='ns')
                elif df_processed['date'].dtype == 'object':
                    # Intentar parsear como string
                    df_processed['date'] = pd.to_datetime(df_processed['date'])
            
            # Convertir precios a float
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                if col in df_processed.columns:
                    df_processed[col] = pd.to_numeric(df_processed[col], errors='coerce')
            
            # Convertir volumen a int
            if 'volume' in df_processed.columns:
                df_processed['volume'] = pd.to_numeric(df_processed['volume'], errors='coerce').astype('Int64')
            
            # Agregar columnas adicionales
            df_processed['symbol'] = symbol
            df_processed['timeframe'] = timeframe
            
            # Limpiar datos
            df_processed = df_processed.dropna(subset=['date', 'open', 'high', 'low', 'close', 'volume'])
            
            # Ordenar por fecha
            df_processed = df_processed.sort_values('date')
            
            # Resetear índice
            df_processed = df_processed.reset_index(drop=True)
            
            print(f"DataFrame procesado exitosamente. Shape: {df_processed.shape}")
            print(f"Rango de fechas: {df_processed['date'].min()} a {df_processed['date'].max()}")
            
            return df_processed
            
        except Exception as e:
            print(f"Error procesando datos OHLCV: {e}")
            raise
    
    @staticmethod
    def import_dataframe_to_django(df, symbol='ES', timeframe='1m', batch_size=1000):
        """
        Importa un DataFrame a la base de datos Django
        
        Args:
            df (pd.DataFrame): DataFrame con datos OHLCV
            symbol (str): Símbolo del futuro
            timeframe (str): Timeframe de los datos
            batch_size (int): Tamaño del lote para importación
        
        Returns:
            dict: Resultado de la importación
        """
        start_time = time.time()
        
        try:
            # Crear log de importación
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
                            # Crear o actualizar registro
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
                            print(f"Error procesando fila: {row}, Error: {e}")
                            skipped_count += 1
                            continue
                
                # Actualizar progreso
                progress = min(100, (i + batch_size) / len(df) * 100)
                print(f"Progreso: {progress:.1f}% - Importados: {imported_count}, Omitidos: {skipped_count}")
            
            # Calcular tiempo de procesamiento
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
            
            print(f"Importación completada exitosamente:")
            print(f"  - Filas importadas: {imported_count}")
            print(f"  - Filas omitidas: {skipped_count}")
            print(f"  - Tiempo de procesamiento: {processing_time:.2f} segundos")
            
            return result
            
        except Exception as e:
            # Actualizar log de importación con error
            if 'import_log' in locals():
                import_log.status = 'failed'
                import_log.error_message = str(e)
                import_log.processing_time = time.time() - start_time
                import_log.save()
            
            print(f"Error en la importación: {e}")
            raise
    
    @staticmethod
    def get_data_for_backtest(symbol='ES', timeframe='1m', start_date=None, end_date=None, limit=None):
        """
        Obtiene datos listos para backtesting
        
        Args:
            symbol (str): Símbolo del futuro
            timeframe (str): Timeframe de los datos
            start_date (datetime): Fecha de inicio
            end_date (datetime): Fecha de fin
            limit (int): Límite de registros
        
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
            
            # Ordenar por fecha
            queryset = queryset.order_by('date')
            
            # Convertir a DataFrame
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
            
            # Convertir precios a float
            price_columns = ['open', 'high', 'low', 'close']
            for col in price_columns:
                df[col] = df[col].astype(float)
            
            # Convertir volumen a int
            df['volume'] = df['volume'].astype(int)
            
            # Establecer fecha como índice
            df = df.set_index('date')
            
            print(f"DataFrame para backtesting creado. Shape: {df.shape}")
            print(f"Rango de fechas: {df.index.min()} a {df.index.max()}")
            
            return df
            
        except Exception as e:
            print(f"Error obteniendo datos para backtesting: {e}")
            raise

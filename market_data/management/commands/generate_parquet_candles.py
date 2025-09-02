"""
Django management command to generate Parquet files for all timeframes
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings
import pandas as pd
import os
import time
from datetime import datetime, timedelta

from market_data.models import HistoricalData
from market_data.timeframe_aggregator import TimeframeAggregator


class Command(BaseCommand):
    help = 'Generate Parquet files for all timeframes from 1-minute data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            default='ES',
            help='Symbol to process (default: ES)'
        )
        parser.add_argument(
            '--timeframes',
            nargs='+',
            default=['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
            help='Timeframes to generate (default: all)'
        )
        parser.add_argument(
            '--start-date',
            type=str,
            help='Start date (YYYY-MM-DD format)'
        )
        parser.add_argument(
            '--end-date',
            type=str,
            help='End date (YYYY-MM-DD format)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regeneration even if files exist'
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            help='Directory to store Parquet files'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100000,
            help='Batch size for processing data (default: 100000)'
        )
    
    def handle(self, *args, **options):
        symbol = options['symbol']
        timeframes = options['timeframes']
        start_date = options.get('start_date')
        end_date = options.get('end_date')
        force = options['force']
        data_dir = options.get('data_dir')
        batch_size = options['batch_size']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting Parquet generation for {symbol}')
        )
        
        # Initialize aggregator
        aggregator = TimeframeAggregator(data_dir=data_dir)
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            except ValueError:
                raise CommandError('Invalid start_date format. Use YYYY-MM-DD')
        
        if end_date:
            try:
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
            except ValueError:
                raise CommandError('Invalid end_date format. Use YYYY-MM-DD')
        
        # Check if 1-minute data exists
        queryset = HistoricalData.objects.filter(symbol=symbol, timeframe='1m')
        
        if start_dt:
            queryset = queryset.filter(date__gte=start_dt)
        if end_dt:
            queryset = queryset.filter(date__lte=end_dt)
        
        total_1m_candles = queryset.count()
        
        if total_1m_candles == 0:
            raise CommandError(f'No 1-minute data found for {symbol}')
        
        self.stdout.write(f'Found {total_1m_candles:,} 1-minute candles for {symbol}')
        
        # Check existing files
        existing_files = []
        for timeframe in timeframes:
            file_info = aggregator.get_file_info(symbol, timeframe)
            if file_info.get('exists'):
                existing_files.append(timeframe)
                self.stdout.write(
                    self.style.WARNING(f'File exists for {timeframe}: {file_info.get("rows", 0):,} candles')
                )
        
        if existing_files and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'Files exist for timeframes: {", ".join(existing_files)}. '
                    'Use --force to regenerate.'
                )
            )
            return
        
        # Process data in batches
        start_time = time.time()
        processed_candles = 0
        
        try:
            # Get all 1-minute data
            self.stdout.write('Loading 1-minute data from database...')
            
            # Use raw SQL for better performance with large datasets
            query = f"""
                SELECT date, open_price, high_price, low_price, close_price, volume
                FROM historical_data 
                WHERE symbol = %s AND timeframe = '1m'
            """
            params = [symbol]
            
            if start_dt:
                query += " AND date >= %s"
                params.append(start_dt)
            
            if end_dt:
                query += " AND date <= %s"
                params.append(end_dt)
            
            query += " ORDER BY date"
            
            with connection.cursor() as cursor:
                cursor.execute(query, params)
                columns = [col[0] for col in cursor.description]
                data = cursor.fetchall()
            
            if not data:
                raise CommandError('No data retrieved from database')
            
            # Convert to DataFrame
            df_1m = pd.DataFrame(data, columns=columns)
            
            # Rename columns to match expected format
            df_1m = df_1m.rename(columns={
                'open_price': 'open',
                'high_price': 'high',
                'low_price': 'low',
                'close_price': 'close'
            })
            
            # Convert date to datetime
            df_1m['date'] = pd.to_datetime(df_1m['date'])
            
            # Add symbol column
            df_1m['symbol'] = symbol
            
            self.stdout.write(f'Loaded {len(df_1m):,} 1-minute candles')
            self.stdout.write(f'Date range: {df_1m["date"].min()} to {df_1m["date"].max()}')
            
            # Generate timeframes
            for timeframe in timeframes:
                self.stdout.write(f'\nProcessing {timeframe} timeframe...')
                
                try:
                    if timeframe == '1m':
                        # For 1m, use the data directly (no aggregation needed)
                        agg_df = df_1m.copy()
                        self.stdout.write(f'Using 1m data directly: {len(agg_df):,} candles')
                    else:
                        # Aggregate data for higher timeframes
                        agg_df = aggregator.aggregate_timeframe(df_1m, timeframe)
                    
                    if agg_df.empty:
                        self.stdout.write(
                            self.style.WARNING(f'No data generated for {timeframe}')
                        )
                        continue
                    
                    # Save to Parquet
                    filepath = aggregator.save_to_parquet(agg_df, symbol, timeframe)
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'Generated {len(agg_df):,} {timeframe} candles -> {filepath}'
                        )
                    )
                    
                    processed_candles += len(agg_df)
                    
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error processing {timeframe}: {e}')
                    )
                    continue
            
            # Summary
            processing_time = time.time() - start_time
            
            self.stdout.write('\n' + '='*50)
            self.stdout.write(
                self.style.SUCCESS('Parquet generation completed!')
            )
            self.stdout.write(f'Total processing time: {processing_time:.2f} seconds')
            self.stdout.write(f'Total candles generated: {processed_candles:,}')
            self.stdout.write(f'Average processing speed: {processed_candles/processing_time:.0f} candles/second')
            
            # List generated files
            self.stdout.write('\nGenerated files:')
            for timeframe in timeframes:
                file_info = aggregator.get_file_info(symbol, timeframe)
                if file_info.get('exists'):
                    self.stdout.write(
                        f'  {timeframe}: {file_info.get("rows", 0):,} candles '
                        f'({file_info.get("file_size_mb", 0):.1f} MB)'
                    )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during processing: {e}')
            )
            raise CommandError(f'Processing failed: {e}')
    
    def get_data_summary(self, symbol, timeframe):
        """Get summary of data for a specific symbol and timeframe"""
        queryset = HistoricalData.objects.filter(symbol=symbol, timeframe=timeframe)
        
        if not queryset.exists():
            return None
        
        first_candle = queryset.order_by('date').first()
        last_candle = queryset.order_by('-date').first()
        
        return {
            'count': queryset.count(),
            'start_date': first_candle.date,
            'end_date': last_candle.date,
            'date_range_days': (last_candle.date - first_candle.date).days
        }

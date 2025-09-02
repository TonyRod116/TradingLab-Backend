"""
Django management command to incrementally update Parquet files
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
from market_data.parquet_service import ParquetDataService


class Command(BaseCommand):
    help = 'Incrementally update Parquet files with new data'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--symbol',
            type=str,
            default='ES',
            help='Symbol to update (default: ES)'
        )
        parser.add_argument(
            '--timeframes',
            nargs='+',
            default=['1m', '5m', '15m', '30m', '1h', '4h', '1d'],
            help='Timeframes to update (default: all)'
        )
        parser.add_argument(
            '--days-back',
            type=int,
            default=1,
            help='Number of days back to check for new data (default: 1)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update even if no new data detected'
        )
        parser.add_argument(
            '--data-dir',
            type=str,
            help='Directory containing Parquet files'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )
    
    def handle(self, *args, **options):
        symbol = options['symbol']
        timeframes = options['timeframes']
        days_back = options['days_back']
        force = options['force']
        data_dir = options.get('data_dir')
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS(f'Starting incremental update for {symbol}')
        )
        
        # Initialize services
        aggregator = TimeframeAggregator(data_dir=data_dir)
        parquet_service = ParquetDataService(data_dir=data_dir)
        
        # Calculate date range
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days_back)
        
        self.stdout.write(f'Checking for new data from {start_date.date()} to {end_date.date()}')
        
        # Check if 1-minute data exists in the date range
        new_1m_data = HistoricalData.objects.filter(
            symbol=symbol,
            timeframe='1m',
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        new_1m_count = new_1m_data.count()
        
        if new_1m_count == 0 and not force:
            self.stdout.write(
                self.style.WARNING('No new 1-minute data found in the specified period')
            )
            return
        
        self.stdout.write(f'Found {new_1m_count:,} new 1-minute candles')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))
        
        # Process each timeframe
        total_updated = 0
        start_time = time.time()
        
        for timeframe in timeframes:
            self.stdout.write(f'\nProcessing {timeframe} timeframe...')
            
            try:
                # Check if Parquet file exists
                file_info = aggregator.get_file_info(symbol, timeframe)
                
                if not file_info.get('exists'):
                    self.stdout.write(
                        self.style.WARNING(f'Parquet file not found for {timeframe}, skipping')
                    )
                    continue
                
                # Get existing data from Parquet
                existing_df = aggregator.load_from_parquet(symbol, timeframe)
                
                if existing_df.empty:
                    self.stdout.write(
                        self.style.WARNING(f'Empty Parquet file for {timeframe}, skipping')
                    )
                    continue
                
                # Get the last date in existing data
                last_existing_date = existing_df['date'].max()
                
                # Get new 1-minute data since last update
                new_1m_since_last = new_1m_data.filter(date__gt=last_existing_date)
                new_1m_count_since = new_1m_since_last.count()
                
                if new_1m_count_since == 0 and not force:
                    self.stdout.write(f'No new data since {last_existing_date} for {timeframe}')
                    continue
                
                self.stdout.write(f'Found {new_1m_count_since:,} new 1-minute candles since {last_existing_date}')
                
                if dry_run:
                    self.stdout.write(f'Would update {timeframe} with {new_1m_count_since:,} new candles')
                    continue
                
                # Convert new 1-minute data to DataFrame
                new_1m_data_list = list(new_1m_since_last.values(
                    'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
                ))
                
                if not new_1m_data_list:
                    continue
                
                new_1m_df = pd.DataFrame(new_1m_data_list)
                new_1m_df = new_1m_df.rename(columns={
                    'open_price': 'open',
                    'high_price': 'high',
                    'low_price': 'low',
                    'close_price': 'close'
                })
                new_1m_df['date'] = pd.to_datetime(new_1m_df['date'])
                new_1m_df['symbol'] = symbol
                
                # Process data based on timeframe
                if timeframe == '1m':
                    # For 1m, use the new data directly (no aggregation needed)
                    new_agg_df = new_1m_df.copy()
                    self.stdout.write(f'Using 1m data directly: {len(new_agg_df):,} new candles')
                else:
                    # Aggregate new data to target timeframe
                    new_agg_df = aggregator.aggregate_timeframe(new_1m_df, timeframe)
                
                if new_agg_df.empty:
                    self.stdout.write(f'No data generated for {timeframe}')
                    continue
                
                # Merge with existing data
                # Remove any overlapping periods from existing data
                cutoff_date = new_agg_df['date'].min()
                existing_df_filtered = existing_df[existing_df['date'] < cutoff_date]
                
                # Combine existing and new data
                combined_df = pd.concat([existing_df_filtered, new_agg_df], ignore_index=True)
                combined_df = combined_df.sort_values('date').reset_index(drop=True)
                
                # Save updated data
                filepath = aggregator.save_to_parquet(combined_df, symbol, timeframe)
                
                new_candles = len(new_agg_df)
                total_candles = len(combined_df)
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Updated {timeframe}: +{new_candles:,} candles, total: {total_candles:,} candles'
                    )
                )
                
                total_updated += new_candles
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error updating {timeframe}: {e}')
                )
                continue
        
        # Summary
        processing_time = time.time() - start_time
        
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN COMPLETED - No changes were made')
            )
        else:
            self.stdout.write(
                self.style.SUCCESS('Incremental update completed!')
            )
        
        self.stdout.write(f'Total processing time: {processing_time:.2f} seconds')
        self.stdout.write(f'Total new candles processed: {total_updated:,}')
        
        if total_updated > 0:
            self.stdout.write(f'Average processing speed: {total_updated/processing_time:.0f} candles/second')
        
        # Clear cache for updated timeframes
        if not dry_run and total_updated > 0:
            self.stdout.write('\nClearing cache for updated timeframes...')
            for timeframe in timeframes:
                parquet_service.clear_cache(symbol, timeframe)
            self.stdout.write('Cache cleared')
    
    def get_last_update_time(self, symbol, timeframe):
        """Get the last update time for a symbol and timeframe"""
        try:
            # Check database for latest 1-minute data
            latest_1m = HistoricalData.objects.filter(
                symbol=symbol, timeframe='1m'
            ).order_by('-date').first()
            
            if latest_1m:
                return latest_1m.date
            
            return None
            
        except Exception as e:
            print(f"Error getting last update time: {e}")
            return None

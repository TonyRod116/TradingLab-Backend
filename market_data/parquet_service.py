"""
Parquet Service for optimized data access
Uses pre-calculated Parquet files when available, falls back to database
"""

import pandas as pd
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from django.conf import settings
from django.core.cache import cache

from market_data.models import HistoricalData
from market_data.timeframe_aggregator import TimeframeAggregator


class ParquetDataService:
    """Service for optimized data access using Parquet files"""
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the service
        
        Args:
            data_dir: Directory containing Parquet files
        """
        self.data_dir = data_dir or getattr(settings, 'DATA_DIR', 'data')
        self.aggregator = TimeframeAggregator(data_dir=self.data_dir)
        self.cache_timeout = 300  # 5 minutes cache
    
    def get_candles(self, symbol: str, timeframe: str, 
                   start_date: datetime = None, end_date: datetime = None,
                   limit: int = None, use_cache: bool = True) -> pd.DataFrame:
        """
        Get candle data, using Parquet files when available
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe ('1m', '5m', '15m', '1h', '4h', '1d')
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of records
            use_cache: Whether to use cache
        
        Returns:
            DataFrame with OHLCV data
        """
        # Check cache first
        if use_cache:
            cache_key = f"candles_{symbol}_{timeframe}_{start_date}_{end_date}_{limit}"
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Try to load from Parquet first
        df = self._load_from_parquet(symbol, timeframe, start_date, end_date, limit)
        
        # Fallback to database if Parquet not available
        if df.empty:
            df = self._load_from_database(symbol, timeframe, start_date, end_date, limit)
        
        # Cache the result
        if use_cache and not df.empty:
            cache.set(cache_key, df, self.cache_timeout)
        
        return df
    
    def _load_from_parquet(self, symbol: str, timeframe: str,
                          start_date: datetime = None, end_date: datetime = None,
                          limit: int = None) -> pd.DataFrame:
        """
        Load data from Parquet file
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of records
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            # Load full dataset from Parquet
            df = self.aggregator.load_from_parquet(symbol, timeframe)
            
            if df.empty:
                return df
            
            # Apply date filters
            if start_date:
                # Convert to pandas Timestamp for comparison
                start_ts = pd.Timestamp(start_date)
                df = df[df['date'] >= start_ts]
            
            if end_date:
                # Convert to pandas Timestamp for comparison
                end_ts = pd.Timestamp(end_date)
                df = df[df['date'] <= end_ts]
            
            # Apply limit
            if limit:
                df = df.tail(limit)  # Get most recent records
            
            # Sort by date
            df = df.sort_values('date')
            
            return df
            
        except Exception as e:
            print(f"Error loading from Parquet: {e}")
            return pd.DataFrame()
    
    def _load_from_database(self, symbol: str, timeframe: str,
                           start_date: datetime = None, end_date: datetime = None,
                           limit: int = None) -> pd.DataFrame:
        """
        Load data from database (fallback)
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe
            start_date: Start date filter
            end_date: End date filter
            limit: Maximum number of records
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            queryset = HistoricalData.objects.filter(symbol=symbol, timeframe=timeframe)
            
            if start_date:
                queryset = queryset.filter(date__gte=start_date)
            
            if end_date:
                queryset = queryset.filter(date__lte=end_date)
            
            if limit:
                queryset = queryset.order_by('-date')[:limit]
            else:
                queryset = queryset.order_by('date')
            
            # Convert to DataFrame
            data = list(queryset.values(
                'date', 'open_price', 'high_price', 'low_price', 'close_price', 'volume'
            ))
            
            if not data:
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df = df.rename(columns={
                'open_price': 'open',
                'high_price': 'high',
                'low_price': 'low',
                'close_price': 'close'
            })
            
            df['date'] = pd.to_datetime(df['date'])
            
            return df
            
        except Exception as e:
            print(f"Error loading from database: {e}")
            return pd.DataFrame()
    
    def get_latest_candle(self, symbol: str, timeframe: str) -> Optional[Dict]:
        """
        Get the latest candle for a symbol and timeframe
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe
        
        Returns:
            Dictionary with latest candle data or None
        """
        try:
            # Try Parquet first
            df = self._load_from_parquet(symbol, timeframe, limit=1)
            
            if df.empty:
                # Fallback to database
                latest = HistoricalData.objects.filter(
                    symbol=symbol, timeframe=timeframe
                ).order_by('-date').first()
                
                if latest:
                    return {
                        'date': latest.date,
                        'open': float(latest.open_price),
                        'high': float(latest.high_price),
                        'low': float(latest.low_price),
                        'close': float(latest.close_price),
                        'volume': latest.volume
                    }
                return None
            
            # Return latest from DataFrame
            latest_row = df.iloc[-1]
            return {
                'date': latest_row['date'],
                'open': float(latest_row['open']),
                'high': float(latest_row['high']),
                'low': float(latest_row['low']),
                'close': float(latest_row['close']),
                'volume': int(latest_row['volume'])
            }
            
        except Exception as e:
            print(f"Error getting latest candle: {e}")
            return None
    
    def get_data_summary(self, symbol: str, timeframe: str) -> Dict:
        """
        Get summary statistics for a symbol and timeframe
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe
        
        Returns:
            Dictionary with summary statistics
        """
        try:
            # Try to get info from Parquet file
            file_info = self.aggregator.get_file_info(symbol, timeframe)
            
            if file_info.get('exists'):
                return {
                    'source': 'parquet',
                    'file_size_mb': file_info.get('file_size_mb', 0),
                    'total_candles': file_info.get('rows', 0),
                    'date_range': file_info.get('date_range'),
                    'filepath': file_info.get('filepath')
                }
            
            # Fallback to database
            queryset = HistoricalData.objects.filter(symbol=symbol, timeframe=timeframe)
            
            if not queryset.exists():
                return {'source': 'none', 'total_candles': 0}
            
            first_candle = queryset.order_by('date').first()
            last_candle = queryset.order_by('-date').first()
            
            return {
                'source': 'database',
                'total_candles': queryset.count(),
                'date_range': {
                    'start': first_candle.date.isoformat(),
                    'end': last_candle.date.isoformat()
                }
            }
            
        except Exception as e:
            print(f"Error getting data summary: {e}")
            return {'source': 'error', 'error': str(e)}
    
    def is_parquet_available(self, symbol: str, timeframe: str) -> bool:
        """
        Check if Parquet file is available for a symbol and timeframe
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe
        
        Returns:
            True if Parquet file exists and is accessible
        """
        file_info = self.aggregator.get_file_info(symbol, timeframe)
        return file_info.get('exists', False)
    
    def get_available_timeframes(self, symbol: str) -> List[str]:
        """
        Get list of available timeframes for a symbol
        
        Args:
            symbol: Symbol name
        
        Returns:
            List of available timeframes
        """
        available = []
        
        for timeframe in ['1m', '5m', '15m', '30m', '1h', '4h', '1d']:
            if self.is_parquet_available(symbol, timeframe):
                available.append(timeframe)
        
        return available
    
    def warm_cache(self, symbol: str, timeframes: List[str] = None, 
                  days_back: int = 30) -> Dict:
        """
        Warm up cache with recent data
        
        Args:
            symbol: Symbol name
            timeframes: List of timeframes to cache (default: all)
            days_back: Number of days to cache
        
        Returns:
            Dictionary with cache warming results
        """
        if timeframes is None:
            timeframes = ['1m', '5m', '15m', '30m', '1h', '4h', '1d']
        
        start_date = datetime.now() - timedelta(days=days_back)
        results = {}
        
        for timeframe in timeframes:
            try:
                df = self.get_candles(
                    symbol=symbol,
                    timeframe=timeframe,
                    start_date=start_date,
                    use_cache=True
                )
                
                results[timeframe] = {
                    'success': True,
                    'candles_cached': len(df),
                    'date_range': {
                        'start': df['date'].min().isoformat() if not df.empty else None,
                        'end': df['date'].max().isoformat() if not df.empty else None
                    }
                }
                
            except Exception as e:
                results[timeframe] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    def clear_cache(self, symbol: str = None, timeframe: str = None):
        """
        Clear cache for specific symbol/timeframe or all
        
        Args:
            symbol: Symbol to clear cache for (optional)
            timeframe: Timeframe to clear cache for (optional)
        """
        if symbol and timeframe:
            # Clear specific cache
            cache_key_pattern = f"candles_{symbol}_{timeframe}_*"
            # Note: Django cache doesn't support pattern deletion by default
            # This would need to be implemented based on your cache backend
            print(f"Cache clearing for {symbol} {timeframe} would need custom implementation")
        else:
            # Clear all cache
            cache.clear()
            print("All cache cleared")
    
    def get_performance_stats(self) -> Dict:
        """
        Get performance statistics for the service
        
        Returns:
            Dictionary with performance metrics
        """
        available_files = self.aggregator.list_available_files()
        
        total_size_mb = sum(f.get('file_size_mb', 0) for f in available_files)
        total_candles = sum(f.get('rows', 0) for f in available_files)
        
        return {
            'total_files': len(available_files),
            'total_size_mb': round(total_size_mb, 2),
            'total_candles': total_candles,
            'files': available_files
        }

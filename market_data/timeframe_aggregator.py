"""
Timeframe Aggregator Service
Converts 1-minute OHLCV data to higher timeframes (5m, 15m, 1h, 4h, 1d)
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os
from django.conf import settings


class TimeframeAggregator:
    """Service for aggregating OHLCV data to different timeframes"""
    
    TIMEFRAME_MAPPING = {
        '1m': '1T',    # 1 minute
        '5m': '5T',    # 5 minutes
        '15m': '15T',  # 15 minutes
        '30m': '30T',  # 30 minutes
        '1h': '1H',    # 1 hour
        '4h': '4H',    # 4 hours
        '1d': '1D',    # 1 day
    }
    
    def __init__(self, data_dir: str = None):
        """
        Initialize the aggregator
        
        Args:
            data_dir: Directory to store Parquet files
        """
        self.data_dir = data_dir or getattr(settings, 'DATA_DIR', 'data')
        os.makedirs(self.data_dir, exist_ok=True)
    
    def aggregate_timeframe(self, df: pd.DataFrame, target_timeframe: str) -> pd.DataFrame:
        """
        Aggregate 1-minute data to target timeframe
        
        Args:
            df: DataFrame with 1-minute OHLCV data
            target_timeframe: Target timeframe ('5m', '15m', '1h', '4h', '1d')
        
        Returns:
            DataFrame with aggregated OHLCV data
        """
        if target_timeframe not in self.TIMEFRAME_MAPPING:
            raise ValueError(f"Unsupported timeframe: {target_timeframe}")
        
        if df.empty:
            return pd.DataFrame()
        
        # Ensure date column is datetime and set as index
        df_work = df.copy()
        if 'date' in df_work.columns:
            df_work['date'] = pd.to_datetime(df_work['date'])
            df_work = df_work.set_index('date')
        
        # Ensure we have the required columns
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        missing_cols = [col for col in required_cols if col not in df_work.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Resample to target timeframe
        resample_freq = self.TIMEFRAME_MAPPING[target_timeframe]
        
        # Aggregate OHLCV data
        agg_data = df_work.resample(resample_freq).agg({
            'open': 'first',      # First open price in the period
            'high': 'max',        # Highest price in the period
            'low': 'min',         # Lowest price in the period
            'close': 'last',      # Last close price in the period
            'volume': 'sum'       # Total volume in the period
        })
        
        # Remove rows with NaN values (incomplete periods)
        agg_data = agg_data.dropna()
        
        # Add symbol and timeframe columns if they exist in original data
        if 'symbol' in df_work.columns:
            agg_data['symbol'] = df_work['symbol'].iloc[0]
        if 'timeframe' in df_work.columns:
            agg_data['timeframe'] = target_timeframe
        
        # Reset index to make date a column
        agg_data = agg_data.reset_index()
        
        return agg_data
    
    def aggregate_all_timeframes(self, df_1m: pd.DataFrame, symbol: str = 'ES') -> Dict[str, pd.DataFrame]:
        """
        Aggregate 1-minute data to all supported timeframes
        
        Args:
            df_1m: DataFrame with 1-minute OHLCV data
            symbol: Symbol name
        
        Returns:
            Dictionary with timeframes as keys and aggregated DataFrames as values
        """
        results = {}
        
        # Add symbol to the dataframe if not present
        if 'symbol' not in df_1m.columns:
            df_1m = df_1m.copy()
            df_1m['symbol'] = symbol
        
        # Aggregate to each timeframe
        for timeframe in ['5m', '15m', '30m', '1h', '4h', '1d']:
            try:
                agg_df = self.aggregate_timeframe(df_1m, timeframe)
                results[timeframe] = agg_df
                print(f"Successfully aggregated to {timeframe}: {len(agg_df)} candles")
            except Exception as e:
                print(f"Error aggregating to {timeframe}: {e}")
                results[timeframe] = pd.DataFrame()
        
        return results
    
    def save_to_parquet(self, df: pd.DataFrame, symbol: str, timeframe: str, 
                       filename: str = None) -> str:
        """
        Save DataFrame to Parquet file
        
        Args:
            df: DataFrame to save
            symbol: Symbol name
            timeframe: Timeframe
            filename: Custom filename (optional)
        
        Returns:
            Path to saved file
        """
        if filename is None:
            filename = f"{symbol}_{timeframe}_candles.parquet"
        
        filepath = os.path.join(self.data_dir, filename)
        
        # Ensure data types are optimal for Parquet
        df_optimized = self._optimize_dtypes(df)
        
        # Save to Parquet with compression
        df_optimized.to_parquet(filepath, compression='snappy', index=False)
        
        print(f"Saved {len(df_optimized)} candles to {filepath}")
        return filepath
    
    def load_from_parquet(self, symbol: str, timeframe: str, 
                         filename: str = None) -> pd.DataFrame:
        """
        Load DataFrame from Parquet file
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe
            filename: Custom filename (optional)
        
        Returns:
            DataFrame with OHLCV data
        """
        if filename is None:
            filename = f"{symbol}_{timeframe}_candles.parquet"
        
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return pd.DataFrame()
        
        try:
            df = pd.read_parquet(filepath)
            return df
        except Exception as e:
            print(f"Error loading Parquet file {filepath}: {e}")
            return pd.DataFrame()
    
    def _optimize_dtypes(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Optimize data types for Parquet storage
        
        Args:
            df: DataFrame to optimize
        
        Returns:
            DataFrame with optimized data types
        """
        df_opt = df.copy()
        
        # Optimize numeric columns
        for col in ['open', 'high', 'low', 'close']:
            if col in df_opt.columns:
                df_opt[col] = df_opt[col].astype('float32')
        
        if 'volume' in df_opt.columns:
            df_opt['volume'] = df_opt['volume'].astype('int64')
        
        # Optimize datetime
        if 'date' in df_opt.columns:
            df_opt['date'] = pd.to_datetime(df_opt['date'])
        
        # Optimize string columns
        for col in ['symbol', 'timeframe']:
            if col in df_opt.columns:
                df_opt[col] = df_opt[col].astype('category')
        
        return df_opt
    
    def get_file_info(self, symbol: str, timeframe: str) -> Dict:
        """
        Get information about a Parquet file
        
        Args:
            symbol: Symbol name
            timeframe: Timeframe
        
        Returns:
            Dictionary with file information
        """
        filename = f"{symbol}_{timeframe}_candles.parquet"
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            return {'exists': False}
        
        try:
            # Get file stats
            stat = os.stat(filepath)
            file_size_mb = stat.st_size / (1024 * 1024)
            
            # Get data info
            df = pd.read_parquet(filepath)
            
            return {
                'exists': True,
                'filepath': filepath,
                'file_size_mb': round(file_size_mb, 2),
                'rows': len(df),
                'columns': list(df.columns),
                'date_range': {
                    'start': df['date'].min().isoformat() if 'date' in df.columns else None,
                    'end': df['date'].max().isoformat() if 'date' in df.columns else None
                } if not df.empty else None
            }
        except Exception as e:
            return {'exists': True, 'error': str(e)}
    
    def list_available_files(self) -> List[Dict]:
        """
        List all available Parquet files
        
        Returns:
            List of dictionaries with file information
        """
        files = []
        
        for filename in os.listdir(self.data_dir):
            if filename.endswith('_candles.parquet'):
                # Parse filename: symbol_timeframe_candles.parquet
                parts = filename.replace('_candles.parquet', '').split('_')
                if len(parts) >= 2:
                    symbol = parts[0]
                    timeframe = parts[1]
                    
                    file_info = self.get_file_info(symbol, timeframe)
                    file_info['filename'] = filename
                    file_info['symbol'] = symbol
                    file_info['timeframe'] = timeframe
                    files.append(file_info)
        
        return files

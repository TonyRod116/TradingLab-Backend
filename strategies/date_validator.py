"""
Date validation service for backtesting
Ensures requested date ranges are within available data
"""

from datetime import datetime
from typing import Tuple, Dict, Optional
from market_data.parquet_service import ParquetDataService


class BacktestDateValidator:
    """Validates and adjusts backtest date ranges based on available data"""
    
    def __init__(self):
        self.parquet_service = ParquetDataService()
    
    def get_available_date_range(self, symbol: str, timeframe: str) -> Tuple[Optional[datetime], Optional[datetime]]:
        """
        Get the actual available date range for a symbol/timeframe combination
        
        Args:
            symbol: Trading symbol (e.g., 'ES')
            timeframe: Data timeframe (e.g., '5m', '1h', '1d')
        
        Returns:
            Tuple of (min_date, max_date) or (None, None) if no data available
        """
        try:
            df = self.parquet_service.get_candles(
                symbol=symbol,
                timeframe=timeframe,
                start_date=None,
                end_date=None
            )
            
            if df.empty:
                return None, None
            
            # Get min and max dates from the data
            min_date = df['date'].min()
            max_date = df['date'].max()
            
            return min_date, max_date
            
        except Exception as e:
            print(f"Error getting available date range: {e}")
            return None, None
    
    def validate_and_adjust_dates(
        self, 
        symbol: str, 
        timeframe: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Tuple[datetime, datetime, Dict]:
        """
        Validate dates and adjust to available range if necessary
        
        Args:
            symbol: Trading symbol
            timeframe: Data timeframe
            start_date: Requested start date
            end_date: Requested end date
        
        Returns:
            Tuple of (adjusted_start_date, adjusted_end_date, validation_info)
        """
        original_start = start_date
        original_end = end_date
        
        # Get available data range
        min_date, max_date = self.get_available_date_range(symbol, timeframe)
        
        if min_date is None or max_date is None:
            return start_date, end_date, {
                'valid': False,
                'adjusted': False,
                'error': 'No data available for this symbol/timeframe combination',
                'available_range': None
            }
        
        # Adjust dates if out of range
        adjusted = False
        warnings = []
        
        if start_date < min_date:
            start_date = min_date
            adjusted = True
            warnings.append(f'Start date adjusted to earliest available data: {min_date.strftime("%Y-%m-%d")}')
        
        if end_date > max_date:
            end_date = max_date
            adjusted = True
            warnings.append(f'End date adjusted to latest available data: {max_date.strftime("%Y-%m-%d")}')
        
        if start_date >= end_date:
            return original_start, original_end, {
                'valid': False,
                'adjusted': False,
                'error': 'Start date must be before end date',
                'available_range': (min_date, max_date)
            }
        
        return start_date, end_date, {
            'valid': True,
            'adjusted': adjusted,
            'warnings': warnings if warnings else None,
            'available_range': (min_date, max_date),
            'original_start': original_start,
            'original_end': original_end
        }
    
    def estimate_data_size(
        self, 
        timeframe: str, 
        start_date: datetime, 
        end_date: datetime
    ) -> Dict:
        """
        Estimate the number of data points for a given date range
        
        Args:
            timeframe: Data timeframe
            start_date: Start date
            end_date: End date
        
        Returns:
            Dictionary with estimation info
        """
        # Map timeframes to minutes
        timeframe_minutes = {
            '1m': 1, '2m': 2, '3m': 3, '4m': 4, '5m': 5, '6m': 6, 
            '7m': 7, '8m': 8, '9m': 9, '10m': 10, '12m': 12, '15m': 15,
            '20m': 20, '30m': 30, '45m': 45,
            '1h': 60, '2h': 120, '3h': 180, '4h': 240, '6h': 360, 
            '8h': 480, '12h': 720,
            '1d': 1440, '2d': 2880, '3d': 4320,
            '1w': 10080, '2w': 20160,
            '1M': 43200,  # ~30 days
            '3M': 129600,  # ~90 days
            '1Y': 525600  # ~365 days
        }
        
        minutes = timeframe_minutes.get(timeframe, 5)  # Default to 5m if unknown
        
        # Calculate total time span in minutes
        time_diff = end_date - start_date
        total_minutes = time_diff.total_seconds() / 60
        
        # Estimate number of data points (assuming ~6.5 hours trading per day)
        # ES trades ~23 hours/day, but use conservative estimate
        trading_hours_per_day = 23
        trading_minutes_per_day = trading_hours_per_day * 60
        
        days = time_diff.days
        estimated_rows = int((days * trading_minutes_per_day) / minutes)
        
        # Determine processing time estimate
        if estimated_rows > 200000:
            estimated_time = '3-5 minutes'
            warning_level = 'high'
        elif estimated_rows > 100000:
            estimated_time = '1-2 minutes'
            warning_level = 'medium'
        elif estimated_rows > 50000:
            estimated_time = '30-60 seconds'
            warning_level = 'low'
        else:
            estimated_time = '< 30 seconds'
            warning_level = 'none'
        
        return {
            'estimated_rows': estimated_rows,
            'estimated_time': estimated_time,
            'warning_level': warning_level,
            'timeframe': timeframe,
            'days': days,
            'should_warn': warning_level in ['high', 'medium']
        }


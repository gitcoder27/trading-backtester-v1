"""
Utility functions for timestamp and timezone handling, and data processing.
"""

from __future__ import annotations
import pandas as pd
import numpy as np
from datetime import datetime, date
from typing import Tuple, Optional, List
import logging

from .models import ChartData, CandleData, DataValidationError

logger = logging.getLogger(__name__)


class TimeUtil:
    """Utility class for timestamp and timezone operations."""
    
    @staticmethod
    def to_iso_utc(ts_series: pd.Series) -> pd.Series:
        """Convert timestamp series to ISO UTC format."""
        s = pd.to_datetime(ts_series)
        return s.dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    @staticmethod
    def to_epoch_seconds(ts_series: pd.Series) -> pd.Series:
        """Return integer seconds since epoch, preserving original timezone."""
        s = pd.to_datetime(ts_series)
        # Don't force UTC conversion - this preserves the original timezone
        # The epoch calculation will automatically account for timezone offset
        return (s.astype('int64') // 10**9).astype(int)
    
    @staticmethod
    def handle_timezone_mismatch(
        data_timestamps: pd.Series, 
        start_dt: datetime, 
        end_dt: datetime
    ) -> Tuple[pd.Series, datetime, datetime]:
        """Handle timezone mismatches between data and filter dates."""
        # Handle timezone mismatch: if data is timezone-aware but filter dates are naive
        if data_timestamps.dt.tz is not None:
            # Data has timezone, so localize the filter dates to the same timezone
            data_tz = data_timestamps.dt.tz
            if start_dt.tzinfo is None:
                start_dt = start_dt.tz_localize(data_tz)
            if end_dt.tzinfo is None:
                end_dt = end_dt.tz_localize(data_tz)
        elif start_dt.tzinfo is not None or end_dt.tzinfo is not None:
            # Filter dates have timezone but data doesn't, convert data to timezone-aware
            if start_dt.tzinfo is not None:
                data_timestamps = data_timestamps.dt.tz_localize('UTC').dt.tz_convert(start_dt.tzinfo)
            elif end_dt.tzinfo is not None:
                data_timestamps = data_timestamps.dt.tz_localize('UTC').dt.tz_convert(end_dt.tzinfo)
        
        return data_timestamps, start_dt, end_dt
    
    @staticmethod
    def convert_trades_to_naive_utc(trades_df: pd.DataFrame) -> pd.DataFrame:
        """Convert trade timestamps to naive UTC for consistent filtering."""
        if trades_df.empty:
            return trades_df
            
        trades_copy = trades_df.copy()
        
        # Ensure entry_time is datetime, and convert to naive UTC
        trades_copy['entry_time'] = pd.to_datetime(trades_copy['entry_time'], errors='coerce')
        if hasattr(trades_copy['entry_time'].dt, 'tz') and trades_copy['entry_time'].dt.tz is not None:
            trades_copy['entry_time'] = trades_copy['entry_time'].dt.tz_convert('UTC').dt.tz_localize(None)
        
        return trades_copy
    
    @staticmethod
    def make_datetime_naive(dt: datetime) -> datetime:
        """Convert timezone-aware datetime to naive UTC."""
        if hasattr(dt, 'tzinfo') and dt.tzinfo is not None:
            return dt.tz_convert('UTC').tz_localize(None)
        return dt


class DataProcessor:
    """Data processing utilities for chart data."""
    
    REQUIRED_OHLC_COLUMNS = ['open', 'high', 'low', 'close']
    TIMESTAMP_COLUMN = 'timestamp'
    
    @staticmethod
    def get_data_date_range(data: pd.DataFrame) -> Tuple[date, date]:
        """Get date range from data DataFrame."""
        if DataProcessor.TIMESTAMP_COLUMN in data.columns:
            data_timestamps = pd.to_datetime(data[DataProcessor.TIMESTAMP_COLUMN])
            min_date = data_timestamps.min().date()
            max_date = data_timestamps.max().date()
        elif isinstance(data.index, pd.DatetimeIndex):
            min_date = data.index.min().date()
            max_date = data.index.max().date()
        else:
            # Use current date as fallback
            from datetime import date
            min_date = max_date = date.today()
        
        return min_date, max_date
    
    @staticmethod
    def validate_data_structure(data: pd.DataFrame) -> None:
        """Validate that data has required structure for charting."""
        if data is None or data.empty:
            raise DataValidationError("Data is empty or None")
        
        # Check for timestamp column or datetime index
        has_timestamp_col = DataProcessor.TIMESTAMP_COLUMN in data.columns
        has_datetime_index = isinstance(data.index, pd.DatetimeIndex)
        
        if not has_timestamp_col and not has_datetime_index:
            raise DataValidationError(
                "Data must have either a datetime index or a 'timestamp' column"
            )
        
        # Check for required OHLC columns
        missing_cols = [col for col in DataProcessor.REQUIRED_OHLC_COLUMNS 
                       if col not in data.columns]
        if missing_cols:
            raise DataValidationError(f"Missing required OHLC columns: {missing_cols}")
    
    @staticmethod
    def filter_data_by_date_range(
        data: pd.DataFrame, 
        start_dt: datetime, 
        end_dt: datetime
    ) -> pd.DataFrame:
        """Filter data by date range, handling timezone issues."""
        if DataProcessor.TIMESTAMP_COLUMN in data.columns:
            data_timestamps = pd.to_datetime(data[DataProcessor.TIMESTAMP_COLUMN])
            data_timestamps, start_dt, end_dt = TimeUtil.handle_timezone_mismatch(
                data_timestamps, start_dt, end_dt
            )
            return data[(data_timestamps >= start_dt) & (data_timestamps <= end_dt)].copy()
        else:
            # Fallback to index filtering if data has datetime index
            return data[(data.index >= start_dt) & (data.index <= end_dt)].copy()
    
    @staticmethod
    def filter_trades_by_date_range(
        trades: pd.DataFrame,
        start_dt: datetime,
        end_dt: datetime
    ) -> pd.DataFrame:
        """Filter trades by date range with proper timezone handling."""
        if trades is None or trades.empty:
            return pd.DataFrame()
        
        trades_df = TimeUtil.convert_trades_to_naive_utc(trades)
        
        # Ensure start_dt and end_dt are naive for comparison with naive entry_time
        start_dt_naive = TimeUtil.make_datetime_naive(start_dt)
        end_dt_naive = TimeUtil.make_datetime_naive(end_dt)
        
        return trades_df[
            (trades_df['entry_time'] >= start_dt_naive) &
            (trades_df['entry_time'] <= end_dt_naive.replace(hour=23, minute=59, second=59))
        ]
    
    @staticmethod
    def clean_and_validate_ohlc_data(df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate OHLC data for charting."""
        # Ensure timestamp is properly formatted
        ts_col = DataProcessor.TIMESTAMP_COLUMN
        if not pd.api.types.is_datetime64_any_dtype(df[ts_col]):
            df[ts_col] = pd.to_datetime(df[ts_col])
        
        # Add time column for chart compatibility
        df['time'] = TimeUtil.to_epoch_seconds(df[ts_col])
        df = df.sort_values('time').reset_index(drop=True)
        
        # Drop rows with invalid OHLC or time
        df = df.dropna(subset=DataProcessor.REQUIRED_OHLC_COLUMNS + ['time'])
        
        # Ensure numeric types for OHLC
        for col in DataProcessor.REQUIRED_OHLC_COLUMNS:
            df[col] = pd.to_numeric(df[col], errors='coerce')
        df = df.dropna(subset=DataProcessor.REQUIRED_OHLC_COLUMNS)
        
        # Keep only finite numbers
        df = df[np.isfinite(df[DataProcessor.REQUIRED_OHLC_COLUMNS]).all(axis=1)]
        
        # Filter out rows with inverted highs/lows
        df = df[df['high'] >= df['low']]
        
        # Deduplicate time (keep last)
        df = df.drop_duplicates(subset=['time'], keep='last')
        
        return df
    
    @staticmethod
    def sample_data_for_performance(
        df: pd.DataFrame, 
        max_points: int = 2000
    ) -> Tuple[pd.DataFrame, bool]:
        """Sample data for optimal chart performance."""
        original_len = len(df)
        
        if len(df) <= max_points:
            return df, False
        
        # Sample the data while preserving important points
        step = len(df) // max_points
        # Keep every nth point but always include first and last
        indices = list(range(0, len(df), step))
        if len(df) - 1 not in indices:
            indices.append(len(df) - 1)
        
        sampled_df = df.iloc[indices].copy()
        
        logger.info(f"Sampled data: {len(sampled_df)} of {original_len} points for performance")
        
        return sampled_df, True
    
    @staticmethod
    def convert_to_candlestick_data(df: pd.DataFrame) -> List[CandleData]:
        """Convert DataFrame to candlestick data format."""
        if df.empty:
            return []
        
        # Cast to native Python types for JSON serialization safety
        candles = []
        for _, row in df[['time'] + DataProcessor.REQUIRED_OHLC_COLUMNS].iterrows():
            candles.append(CandleData(
                time=int(row['time']),
                open=float(row['open']),
                high=float(row['high']),
                low=float(row['low']),
                close=float(row['close'])
            ))
        
        return candles
    
    @staticmethod
    def build_overlay_data(
        indicators: Optional[pd.DataFrame],
        indicator_config: List[dict],
        timestamp_col: str = TIMESTAMP_COLUMN
    ) -> List[dict]:
        """Build overlay data from indicators."""
        import logging
        logger = logging.getLogger(__name__)
        logger.setLevel(logging.DEBUG)  # Ensure debug messages are shown
        
        overlays = []
        
        if indicators is None:
            logger.debug("build_overlay_data: indicators is None")
            return overlays
            
        if len(indicator_config) == 0:
            logger.debug("build_overlay_data: indicator_config is empty")
            return overlays
        
        logger.debug(f"build_overlay_data: Processing {len(indicator_config)} indicator configs")
        logger.debug(f"build_overlay_data: Available columns: {list(indicators.columns)}")
        logger.debug(f"build_overlay_data: Indicators shape: {indicators.shape}")
        
        indf = indicators.copy()
        if not pd.api.types.is_datetime64_any_dtype(indf[timestamp_col]):
            indf[timestamp_col] = pd.to_datetime(indf[timestamp_col])
        indf['time'] = TimeUtil.to_epoch_seconds(indf[timestamp_col])
        
        for cfg in indicator_config:
            col = cfg.get('column')
            plot_enabled = cfg.get('plot', True)
            panel = cfg.get('panel', 1)
            
            logger.debug(f"build_overlay_data: Processing indicator '{col}', plot={plot_enabled}, panel={panel}")
            
            if (plot_enabled and 
                col in indf.columns and 
                panel == 1):
                
                color = cfg.get('color', '#cccccc')
                overlay_data = indf[['time', col]].dropna().copy()
                
                logger.debug(f"build_overlay_data: Adding overlay for '{col}' with {len(overlay_data)} data points")
                logger.debug(f"build_overlay_data: First few values: {overlay_data.head()}")
                
                overlays.append({
                    'type': 'Line',
                    'data': [
                        {'time': int(t), 'value': float(v)} 
                        for t, v in zip(overlay_data['time'], overlay_data[col])
                    ],
                    'options': {
                        'color': color,
                        'lineWidth': 1,
                        'priceLineVisible': False,
                        'lastValueVisible': False,
                    },
                    'priceScaleId': 'right',
                })
            else:
                if not plot_enabled:
                    logger.debug(f"build_overlay_data: Skipping '{col}' - plot disabled")
                elif col not in indf.columns:
                    logger.debug(f"build_overlay_data: Skipping '{col}' - column not found")
                elif panel != 1:
                    logger.debug(f"build_overlay_data: Skipping '{col}' - panel {panel} != 1")
        
        logger.debug(f"build_overlay_data: Created {len(overlays)} overlays")
        return overlays

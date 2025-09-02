from __future__ import annotations
import os
import tempfile
import pandas as pd
from backtester.data_loader import load_csv

__all__ = [
    'list_data_files',
    'load_data_from_source',
    'filter_by_date',
]


def list_data_files(data_folder: str = 'data') -> list[str]:
    if not os.path.isdir(data_folder):
        return []
    return [f for f in os.listdir(data_folder) if f.endswith('.csv')]


def load_data_from_source(file_path: str | None, timeframe: str, uploaded_bytes: bytes | None):
    if uploaded_bytes is not None:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.csv') as tmp:
            tmp.write(uploaded_bytes)
            tmp_path = tmp.name
        try:
            df = load_csv(tmp_path, timeframe=timeframe)
        finally:
            try:
                os.remove(tmp_path)  # type: ignore[attr-defined]
            except Exception:
                pass
        return df
    elif file_path is not None:
        return load_csv(file_path, timeframe=timeframe)
    else:
        return None


def filter_by_date(df: pd.DataFrame, start_date, end_date) -> pd.DataFrame:
    """Filter a DataFrame by date range, handling tz-aware/naive safely.
    - If data timestamps are tz-aware and inputs are naive, localize inputs to the same tz.
    - End date is treated as inclusive (end of day) by filtering strictly before next day.
    """
    if 'timestamp' not in df.columns:
        return df
    ts = df['timestamp']
    tz = getattr(ts.dt, 'tz', None)
    # Start date
    if start_date:
        start_dt = pd.to_datetime(start_date)
        if tz is not None and start_dt.tzinfo is None:
            start_dt = start_dt.tz_localize(tz)
        df = df[ts >= start_dt]
        ts = df['timestamp']
    # End date (inclusive end-of-day)
    if end_date:
        end_dt = pd.to_datetime(end_date)
        if tz is not None and end_dt.tzinfo is None:
            end_dt = end_dt.tz_localize(tz)
        end_dt_next = end_dt + pd.Timedelta(days=1)
        df = df[ts < end_dt_next]
    return df

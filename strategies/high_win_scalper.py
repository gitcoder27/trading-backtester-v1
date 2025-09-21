"""Trend-Aligned RSI Midday Scalper (new strategy).

This strategy is inspired by, but distinct from, the existing RSI midday
reversion system. It enforces trend alignment via EMA50/EMA200, uses cross
signals rather than forced entries except when no trade has fired by 13:15, and
holds for ATR-based targets so profitable trades capture ~15–20 points.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Any, Dict

import numpy as np
import pandas as pd

from backtester.strategy_base import StrategyBase


@dataclass
class StrategyParams:
    rsi_period: int = 14
    atr_period: int = 14
    ema_fast: int = 50
    ema_slow: int = 200
    long_reset: float = 25.0
    long_entry: float = 37.0
    short_reset: float = 75.0
    short_entry: float = 63.0
    rsi_neutral: float = 52.0
    target_atr: float = 1.5
    stop_atr: float = 3.2
    min_target_points: float = 12.0
    max_trades_per_day: int = 2
    session_start: str = "09:25"
    session_end: str = "15:05"
    exit_time: str = "15:20"
    force_entry_time: str = "13:15"

    @classmethod
    def from_dict(cls, raw: Dict[str, Any] | None) -> "StrategyParams":
        """
        Create a StrategyParams instance from a plain dictionary, ignoring unknown keys.
        
        If `raw` is None or empty, returns a default StrategyParams constructed with dataclass defaults.
        Otherwise, only keys that match the dataclass fields are kept and passed to the constructor; any extra keys in `raw` are ignored.
        
        Parameters:
            raw (dict | None): Mapping of parameter names to values. Keys not defined on the dataclass will be discarded.
        
        Returns:
            StrategyParams: A new instance populated from the filtered dictionary (or defaults if `raw` is falsy).
        """
        if not raw:
            return cls()
        filtered = {field: raw[field] for field in cls.__dataclass_fields__ if field in raw}
        return cls(**filtered)


class HighWinScalperStrategy(StrategyBase):
    def __init__(self, params: Dict[str, Any] | None = None):
        """
        Initialize the strategy and normalize the provided parameters.
        
        If `params` is a dict, it is converted into a StrategyParams instance via StrategyParams.from_dict.
        If `params` is None, defaults from StrategyParams are used.
        """
        super().__init__(params)
        self.params = StrategyParams.from_dict(params)

    # ---------------------------------------------------------------
    @staticmethod
    def _rsi(series: pd.Series, period: int) -> pd.Series:
        """
        Compute the Relative Strength Index (RSI) for a price series using exponential smoothing.
        
        This implementation calculates price changes, separates gains and losses, computes exponentially weighted
        moving averages of gains and losses with alpha = 1/period, then returns the standard 0–100 RSI values.
        A tiny epsilon is added to avoid division-by-zero when losses are zero.
        
        Parameters:
            series (pd.Series): Time-ordered price series (e.g., close prices).
            period (int): Lookback period for RSI smoothing.
        
        Returns:
            pd.Series: RSI values (0–100) aligned with the input series index.
        """
        delta = series.diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        avg_gain = gains.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = losses.ewm(alpha=1 / period, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _atr(df: pd.DataFrame, period: int) -> pd.Series:
        """
        Compute the Average True Range (ATR) series from OHLC data using an exponential moving average (Wilder-style).
        
        Calculates the True Range (TR) per row as the maximum of:
        - high - low
        - |high - previous close|
        - |low - previous close|
        
        Then smooths TR with an exponential moving average using alpha = 1/period and adjust=False (Wilder smoothing).
        
        Parameters:
            df (pd.DataFrame): Price data containing columns 'high', 'low', and 'close'.
            period (int): Period for ATR smoothing (used as 1/period alpha in EWM).
        
        Returns:
            pd.Series: ATR values aligned with df's index.
        """
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.ewm(alpha=1 / period, adjust=False).mean()

    # ---------------------------------------------------------------
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        """
        Generate entry signals for the strategy and return the input DataFrame augmented with indicators and a 'signal' column.
        
        Computes RSI, ATR, fast and slow EMAs for the provided market data, then iterates rows inside the configured trading session to create directional entry signals (1 for long, -1 for short) using trend alignment (EMA fast vs EMA slow), prior/current RSI thresholds, and a same-bar price direction check (close > open for longs, close < open for shorts). Enforces a per-day trade cap (max_trades_per_day). If no trade was placed for a day by the configured force_entry_time, a single forced trend-following signal is placed at the first row on/after that time (or the day's last row if none after the cutoff). The returned DataFrame contains at least the columns: 'rsi', 'atr', 'ema_fast', 'ema_slow', and 'signal'.
        
        Parameters:
            data (pd.DataFrame): Market data with at minimum 'open', 'high', 'low', 'close', and either a 'timestamp' column or a datetime index. Timestamps are used to enforce session windows and per-day counting.
        
        Returns:
            pd.DataFrame: A copy of the input DataFrame augmented with computed indicator columns and the 'signal' column (0 = no signal, 1 = long, -1 = short).
        """
        df = data.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp']) if 'timestamp' in df.columns else pd.to_datetime(df.index)

        df['rsi'] = self._rsi(df['close'], self.params.rsi_period)
        df['atr'] = self._atr(df, self.params.atr_period)
        df['ema_fast'] = df['close'].ewm(span=self.params.ema_fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.params.ema_slow, adjust=False).mean()

        start_h, start_m = map(int, self.params.session_start.split(':'))
        end_h, end_m = map(int, self.params.session_end.split(':'))
        force_h, force_m = map(int, self.params.force_entry_time.split(':'))
        start_time = time(start_h, start_m)
        end_time = time(end_h, end_m)
        force_time = time(force_h, force_m)

        df['signal'] = 0
        per_day_counts: Dict[pd.Timestamp.date, int] = {}
        prev_day = None

        for idx in range(1, len(df)):
            row = df.iloc[idx]
            ts = row['timestamp']
            if pd.isna(ts) or ts.time() < start_time or ts.time() > end_time:
                continue

            day = ts.date()
            if prev_day is None or day != prev_day:
                per_day_counts[day] = 0
                prev_day = day

            if per_day_counts[day] >= self.params.max_trades_per_day:
                continue

            prev_rsi = df['rsi'].iloc[idx - 1]
            rsi = row['rsi']
            ema_fast = row['ema_fast']
            ema_slow = row['ema_slow']

            if any(np.isnan(v) for v in (rsi, prev_rsi, ema_fast, ema_slow, row['atr'])):
                continue

            trend_long = ema_fast > ema_slow
            trend_short = ema_fast < ema_slow

            signal = 0
            if trend_long and prev_rsi < self.params.long_reset and rsi >= self.params.long_entry and row['close'] > row['open']:
                signal = 1
            elif trend_short and prev_rsi > self.params.short_reset and rsi <= self.params.short_entry and row['close'] < row['open']:
                signal = -1

            if signal != 0:
                df.at[df.index[idx], 'signal'] = signal
                per_day_counts[day] += 1

        # Forced trend-following entry if none triggered by cut-off time
        df['date'] = df['timestamp'].dt.date
        for date, group in df.groupby('date'):
            if per_day_counts.get(date, 0) > 0:
                continue
            candidates = group[group['timestamp'].dt.time >= force_time]
            if candidates.empty:
                candidates = group.iloc[-1:]
            row = candidates.iloc[0]
            idx = row.name
            if row['ema_fast'] > row['ema_slow']:
                df.at[idx, 'signal'] = 1
            elif row['ema_fast'] < row['ema_slow']:
                df.at[idx, 'signal'] = -1
            per_day_counts[date] = 1
        df.drop(columns=['date'], inplace=True)
        return df

    # ---------------------------------------------------------------
    def should_exit(self, position: str, row: pd.Series, entry_price: float):
        """
        Decide whether to exit an open position based on ATR targets/stops, EMA/RSI conditions, and session end.
        
        Checks applied:
        - ATR-based profit target and maximum adverse excursion (stop): target = max(params.target_atr * ATR, params.min_target_points); stop = params.stop_atr * ATR.
        - EMA break: exit if price crosses the fast EMA against the position.
        - RSI neutral threshold: exit long when RSI >= params.rsi_neutral + 5; exit short when RSI <= params.rsi_neutral - 5.
        - Session close: if row['timestamp'] is present and at/after params.exit_time, exit with reason 'session_close'.
        
        Parameters:
            position (str): 'long' or 'short'.
            row (pd.Series): Market row containing at minimum 'close'; may also include 'atr', 'ema_fast', 'rsi', and 'timestamp'.
            entry_price (float): Entry price of the open position.
        
        Returns:
            tuple(bool, str): (should_exit, reason). reason is one of:
                'target', 'stop', 'ema_break', 'rsi_neutral', 'session_close', or '' if no exit.
        """
        atr = float(row.get('atr', 0.0) or 0.0)
        price = float(row['close'])
        mae_limit = self.params.stop_atr * atr
        target = max(self.params.target_atr * atr, self.params.min_target_points)

        if position == 'long':
            if price >= entry_price + target:
                return True, 'target'
            if price <= entry_price - mae_limit:
                return True, 'stop'
            if row.get('ema_fast') is not None and price < row['ema_fast']:
                return True, 'ema_break'
            rsi = row.get('rsi', np.nan)
            if not np.isnan(rsi) and rsi >= self.params.rsi_neutral + 5:
                return True, 'rsi_neutral'
        elif position == 'short':
            if price <= entry_price - target:
                return True, 'target'
            if price >= entry_price + mae_limit:
                return True, 'stop'
            if row.get('ema_fast') is not None and price > row['ema_fast']:
                return True, 'ema_break'
            rsi = row.get('rsi', np.nan)
            if not np.isnan(rsi) and rsi <= self.params.rsi_neutral - 5:
                return True, 'rsi_neutral'

        timestamp = row.get('timestamp')
        if timestamp is not None:
            try:
                ts = pd.to_datetime(timestamp)
                exit_h, exit_m = map(int, self.params.exit_time.split(':'))
                cutoff = ts.replace(hour=exit_h, minute=exit_m, second=0)
                if ts >= cutoff:
                    return True, 'session_close'
            except Exception:
                pass

        return False, ''


__all__ = ['HighWinScalperStrategy']

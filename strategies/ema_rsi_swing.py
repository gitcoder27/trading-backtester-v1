"""EMA/RSI Trend Recovery Scalper (new strategy).

The strategy looks for pullbacks within the dominant trend and aims to capture
~20 NIFTY points per trade while preserving a high win rate.
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
    ema_fast: int = 100
    ema_slow: int = 200
    ema_slope_lookback: int = 12
    rsi_period: int = 14
    rsi_reset: float = 28.0
    rsi_entry: float = 40.0
    atr_period: int = 14
    rsi_neutral: float = 52.0
    target_atr: float = 2.0
    stop_atr: float = 3.5
    pullback_pct: float = 0.0020  # 0.20%
    target_points: float = 20.0
    stop_points: float = 14.0
    max_trades_per_day: int = 2
    session_start: str = "09:30"
    session_end: str = "15:05"
    exit_time: str = "15:20"
    force_entry_time: str = "13:15"

    @classmethod
    def from_dict(cls, raw: Dict[str, Any] | None) -> "StrategyParams":
        if not raw:
            return cls()
        data = {field: raw[field] for field in cls.__dataclass_fields__ if field in raw}
        return cls(**data)


class EMARsiSwingStrategy(StrategyBase):
    def __init__(self, params: Dict[str, Any] | None = None):
        super().__init__(params)
        self.params = StrategyParams.from_dict(params)

    # ---------------------------------------------------------------
    @staticmethod
    def _atr(df: pd.DataFrame, period: int) -> pd.Series:
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        true_range = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return true_range.ewm(alpha=1 / period, adjust=False).mean()

    # ---------------------------------------------------------------
    @staticmethod
    def _ema(series: pd.Series, period: int) -> pd.Series:
        return series.ewm(span=period, adjust=False).mean()

    @staticmethod
    def _rsi(series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        avg_gain = gains.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = losses.ewm(alpha=1 / period, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        return 100 - (100 / (1 + rs))

    # ---------------------------------------------------------------
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        df['timestamp'] = pd.to_datetime(df['timestamp']) if 'timestamp' in df.columns else pd.to_datetime(df.index)

        df['atr'] = self._atr(df, self.params.atr_period)
        df['ema_fast'] = self._ema(df['close'], self.params.ema_fast)
        df['ema_slow'] = self._ema(df['close'], self.params.ema_slow)
        df['ema_slope'] = df['ema_fast'] - df['ema_fast'].shift(self.params.ema_slope_lookback)
        df['rsi'] = self._rsi(df['close'], self.params.rsi_period)

        start_h, start_m = map(int, self.params.session_start.split(':'))
        end_h, end_m = map(int, self.params.session_end.split(':'))
        force_h, force_m = map(int, self.params.force_entry_time.split(':'))
        start_time = time(start_h, start_m)
        end_time = time(end_h, end_m)
        force_time = time(force_h, force_m)

        df['signal'] = 0
        per_day_counts: Dict[pd.Timestamp.date, int] = {}
        prev_day = None
        long_ready = False

        for idx in range(1, len(df)):
            row = df.iloc[idx]
            ts = row['timestamp']
            if pd.isna(ts) or ts.time() < start_time or ts.time() > end_time:
                continue

            day = ts.date()
            if prev_day is None or day != prev_day:
                per_day_counts[day] = 0
                long_ready = False
                prev_day = day

            if per_day_counts[day] >= self.params.max_trades_per_day:
                continue

            ema_fast = row['ema_fast']
            ema_slow = row['ema_slow']
            rsi_prev = df['rsi'].iloc[idx - 1]
            rsi_curr = row['rsi']

            if any(np.isnan(v) for v in (ema_fast, ema_slow, rsi_prev, rsi_curr, row['ema_slope'])):
                continue

            uptrend = ema_fast > ema_slow and row['ema_slope'] > 0

            if uptrend and rsi_prev < self.params.rsi_reset and rsi_curr >= self.params.rsi_entry:
                pullback = (row['ema_fast'] - row['low']) / row['ema_fast'] if row['ema_fast'] else 0
                if 0 < pullback <= self.params.pullback_pct and row['close'] > row['ema_fast'] and row['close'] > row['open']:
                    df.at[df.index[idx], 'signal'] = 1
                    per_day_counts[day] += 1

        # Force a trade if trend persists but no signal by force_time
        df['date'] = df['timestamp'].dt.date
        for date, group in df.groupby('date'):
            if per_day_counts.get(date, 0) > 0:
                continue
            candidates = group[group['timestamp'].dt.time >= force_time]
            if candidates.empty:
                candidates = group.iloc[-1:]
            row = candidates.iloc[0]
            if row['ema_fast'] > row['ema_slow']:
                df.at[row.name, 'signal'] = 1
                per_day_counts[date] = 1
        df.drop(columns=['date'], inplace=True)
        return df

    # ---------------------------------------------------------------
    def should_exit(self, position: str, row: pd.Series, entry_price: float):
        if position != 'long':
            return False, ''

        price = float(row['close'])
        target = max(self.params.target_points, self.params.target_atr * float(row.get('atr', 0.0) or 0.0))
        stop = max(self.params.stop_points, self.params.stop_atr * float(row.get('atr', 0.0) or 0.0))

        if price >= entry_price + target:
            return True, 'target'
        if price <= entry_price - stop:
            return True, 'stop'
        ema_fast = row.get('ema_fast')
        if ema_fast is not None and price < ema_fast:
            return True, 'ema_break'

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


__all__ = ['EMARsiSwingStrategy']

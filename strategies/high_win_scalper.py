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
        if not raw:
            return cls()
        filtered = {field: raw[field] for field in cls.__dataclass_fields__ if field in raw}
        return cls(**filtered)


class HighWinScalperStrategy(StrategyBase):
    def __init__(self, params: Dict[str, Any] | None = None):
        super().__init__(params)
        self.params = StrategyParams.from_dict(params)

    # ---------------------------------------------------------------
    @staticmethod
    def _rsi(series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        avg_gain = gains.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = losses.ewm(alpha=1 / period, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        return 100 - (100 / (1 + rs))

    @staticmethod
    def _atr(df: pd.DataFrame, period: int) -> pd.Series:
        high_low = df['high'] - df['low']
        high_close = (df['high'] - df['close'].shift()).abs()
        low_close = (df['low'] - df['close'].shift()).abs()
        tr = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1)
        return tr.ewm(alpha=1 / period, adjust=False).mean()

    # ---------------------------------------------------------------
    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
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

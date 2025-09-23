"""Trend Recovery Scalper.

This strategy hunts for high-probability mean-reversion trades within the
prevailing intraday trend on NIFTY 1-minute data. It waits for a fast pullback
against the trend, requires momentum confirmation, and then targets a
consistent 15+ point rebound while keeping downside small.
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
    ema_fast: int = 20
    ema_medium: int = 50
    ema_slow: int = 200
    ema_slope_lookback: int = 6
    rsi_period: int = 14
    long_reset: float = 27.0
    long_entry: float = 42.0
    short_reset: float = 73.0
    short_entry: float = 58.0
    rsi_neutral: float = 52.0
    pullback_min: float = 0.0010  # 0.10%
    pullback_max: float = 0.0035  # 0.35%
    target_points: float = 16.0
    stop_points: float = 32.0
    max_trades_per_day: int = 3
    session_start: str = "09:25"
    session_end: str = "15:05"
    exit_time: str = "15:20"

    @classmethod
    def from_dict(cls, raw: Dict[str, Any] | None) -> "StrategyParams":
        if not raw:
            return cls()
        filtered = {field: raw[field] for field in cls.__dataclass_fields__ if field in raw}
        return cls(**filtered)


class TrendRecoveryScalperStrategy(StrategyBase):
    def __init__(self, params: Dict[str, Any] | None = None):
        super().__init__(params)
        self.params = StrategyParams.from_dict(params)

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

        df['ema_fast'] = self._ema(df['close'], self.params.ema_fast)
        df['ema_med'] = self._ema(df['close'], self.params.ema_medium)
        df['ema_slow'] = self._ema(df['close'], self.params.ema_slow)
        df['ema_med_slope'] = df['ema_med'] - df['ema_med'].shift(self.params.ema_slope_lookback)
        df['rsi'] = self._rsi(df['close'], self.params.rsi_period)

        start_h, start_m = map(int, self.params.session_start.split(':'))
        end_h, end_m = map(int, self.params.session_end.split(':'))
        start_time = time(start_h, start_m)
        end_time = time(end_h, end_m)

        df['signal'] = 0
        per_day_counts: Dict[pd.Timestamp.date, int] = {}
        long_ready = False
        short_ready = False
        prev_day = None

        for idx, row in df.iterrows():
            ts = row['timestamp']
            if pd.isna(ts) or ts.time() < start_time or ts.time() > end_time:
                continue

            day = ts.date()
            if prev_day is None or day != prev_day:
                per_day_counts[day] = 0
                long_ready = False
                short_ready = False
                prev_day = day

            if per_day_counts[day] >= self.params.max_trades_per_day:
                continue

            if any(np.isnan(row[c]) for c in ['ema_fast', 'ema_med', 'ema_slow', 'rsi']):
                continue

            uptrend = row['ema_med'] > row['ema_slow'] and row['ema_med_slope'] > 0
            downtrend = row['ema_med'] < row['ema_slow'] and row['ema_med_slope'] < 0

            if uptrend:
                pullback = (row['ema_fast'] - row['low']) / row['ema_fast'] if row['ema_fast'] else 0.0
                if self.params.pullback_min <= pullback <= self.params.pullback_max:
                    if row['rsi'] <= self.params.long_reset:
                        long_ready = True
                if long_ready and row['rsi'] >= self.params.long_entry and row['close'] > row['ema_fast'] and row['close'] > row['open']:
                    df.at[idx, 'signal'] = 1
                    per_day_counts[day] += 1
                    long_ready = False
            elif downtrend:
                pullup = (row['high'] - row['ema_fast']) / row['ema_fast'] if row['ema_fast'] else 0.0
                if self.params.pullback_min <= pullup <= self.params.pullback_max:
                    if row['rsi'] >= self.params.short_reset:
                        short_ready = True
                if short_ready and row['rsi'] <= self.params.short_entry and row['close'] < row['ema_fast'] and row['close'] < row['open']:
                    df.at[idx, 'signal'] = -1
                    per_day_counts[day] += 1
                    short_ready = False

        return df

    # ---------------------------------------------------------------
    def should_exit(self, position: str, row: pd.Series, entry_price: float):
        price = float(row['close'])
        ema_fast = row.get('ema_fast')

        if position == 'long':
            if price >= entry_price + self.params.target_points:
                return True, 'target'
            if price <= entry_price - self.params.stop_points:
                return True, 'stop'
            if ema_fast is not None and price < ema_fast:
                return True, 'ema_break'
            rsi = row.get('rsi', np.nan)
            if not np.isnan(rsi) and rsi >= self.params.rsi_neutral + 5:
                return True, 'rsi_neutral'
        elif position == 'short':
            if price <= entry_price - self.params.target_points:
                return True, 'target'
            if price >= entry_price + self.params.stop_points:
                return True, 'stop'
            if ema_fast is not None and price > ema_fast:
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


__all__ = ['TrendRecoveryScalperStrategy']

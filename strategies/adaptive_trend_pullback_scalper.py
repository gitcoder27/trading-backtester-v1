"""Adaptive Range Reversion Scalper."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import time
from typing import Any, Dict

import numpy as np
import pandas as pd

from backtester.strategy_base import StrategyBase


@dataclass
class StrategyParams:
    bb_length: int = 20
    bb_std: float = 2.0
    rsi_period: int = 14
    rsi_reset_long: float = 32.0
    rsi_trigger_long: float = 38.0
    rsi_reset_short: float = 68.0
    rsi_trigger_short: float = 62.0
    ema_neutral_period: int = 55
    ema_fast_period: int = 21
    ema_slope_lookback: int = 8
    ema_slope_threshold: float = 0.0005
    atr_period: int = 14
    target_points: float = 14.0
    stop_points: float = 8.0
    cooldown_minutes: int = 3
    max_trades_per_day: int = 8
    session_start: str = "09:45"
    session_end: str = "15:00"
    exit_time: str = "15:15"
    band_buffer_pct: float = 0.0

    @classmethod
    def from_dict(cls, raw: Dict[str, Any] | None) -> "StrategyParams":
        if not raw:
            return cls()
        filtered = {field: raw[field] for field in cls.__dataclass_fields__ if field in raw}
        return cls(**filtered)


class AdaptiveTrendPullbackScalperStrategy(StrategyBase):
    """Mean-reversion scalper with adaptive trend neutrality filtering."""

    def __init__(self, params: Dict[str, Any] | None = None):
        super().__init__(params)
        self.params = StrategyParams.from_dict(params)
        self._use_fast_vectorized = False

    @staticmethod
    def get_params_config() -> list[dict[str, Any]]:
        return [
            {
                "name": "arps_target_points",
                "param_key": "target_points",
                "type": "number_input",
                "label": "Target (points)",
                "default": 14.0,
                "min": 4.0,
                "max": 40.0,
                "step": 1.0,
            },
            {
                "name": "arps_stop_points",
                "param_key": "stop_points",
                "type": "number_input",
                "label": "Stop (points)",
                "default": 8.0,
                "min": 4.0,
                "max": 40.0,
                "step": 1.0,
            },
            {
                "name": "arps_max_trades",
                "param_key": "max_trades_per_day",
                "type": "number_input",
                "label": "Max trades per day",
                "default": 8,
                "min": 1,
                "max": 15,
                "step": 1,
            },
            {
                "name": "arps_cooldown",
                "param_key": "cooldown_minutes",
                "type": "number_input",
                "label": "Cooldown minutes",
                "default": 3,
                "min": 0,
                "max": 30,
                "step": 1,
            },
        ]

    @staticmethod
    def _rsi(series: pd.Series, period: int) -> pd.Series:
        delta = series.diff()
        gains = delta.clip(lower=0)
        losses = -delta.clip(upper=0)
        avg_gain = gains.ewm(alpha=1 / period, adjust=False).mean()
        avg_loss = losses.ewm(alpha=1 / period, adjust=False).mean()
        rs = avg_gain / (avg_loss + 1e-9)
        return 100 - (100 / (1 + rs))

    def _compute_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        p = self.params
        close = df['close']
        ma = close.rolling(p.bb_length, min_periods=p.bb_length).mean()
        stdev = close.rolling(p.bb_length, min_periods=p.bb_length).std()
        bb_label = f"{p.bb_length}_{p.bb_std}".replace('.', '_')
        df[f'bb_mid_{bb_label}'] = ma
        df[f'bb_low_{bb_label}'] = ma - p.bb_std * stdev
        df[f'bb_high_{bb_label}'] = ma + p.bb_std * stdev

        df['rsi'] = self._rsi(close, p.rsi_period)
        df['ema_fast'] = close.ewm(span=p.ema_fast_period, adjust=False).mean()
        df['ema_neutral'] = close.ewm(span=p.ema_neutral_period, adjust=False).mean()
        df['ema_neutral_slope'] = df['ema_neutral'] - df['ema_neutral'].shift(p.ema_slope_lookback)
        return df

    def indicator_config(self) -> list[dict[str, Any]]:
        tag = f"{self.params.bb_length}_{self.params.bb_std}".replace('.', '_')
        return [
            {"column": f"bb_high_{tag}", "label": "BB Upper", "plot": True, "color": "#95a5a6", "type": "dash"},
            {"column": f"bb_mid_{tag}", "label": "BB Mid", "plot": True, "color": "#f39c12"},
            {"column": f"bb_low_{tag}", "label": "BB Lower", "plot": True, "color": "#95a5a6", "type": "dash"},
            {"column": "ema_neutral", "label": f"EMA({self.params.ema_neutral_period})", "plot": True, "color": "#2ecc71"},
        ]

    def _trend_is_neutral(self, row: pd.Series) -> bool:
        ema_neutral = row['ema_neutral']
        if ema_neutral == 0 or np.isnan(ema_neutral):
            return False
        diff_pct = abs(row['ema_fast'] - ema_neutral) / ema_neutral
        slope = row.get('ema_neutral_slope', 0.0) or 0.0
        slope_pct = abs(slope) / ema_neutral
        thresh = self.params.ema_slope_threshold
        return diff_pct <= thresh and slope_pct <= thresh

    def generate_signals(self, data: pd.DataFrame) -> pd.DataFrame:
        df = data.copy()
        if 'timestamp' not in df.columns:
            raise ValueError("Data must include timestamp column")
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        df = self._compute_indicators(df)
        df['date'] = df['timestamp'].dt.date
        df['signal'] = 0

        tag = f"{self.params.bb_length}_{self.params.bb_std}".replace('.', '_')
        mid_col = f'bb_mid_{tag}'
        low_col = f'bb_low_{tag}'
        high_col = f'bb_high_{tag}'

        start_h, start_m = map(int, self.params.session_start.split(':'))
        end_h, end_m = map(int, self.params.session_end.split(':'))
        start_time = time(start_h, start_m)
        end_time = time(end_h, end_m)

        for day, day_df in df.groupby('date'):
            trades = 0
            cooldown_end: pd.Timestamp | None = None

            for idx in day_df.index:
                row = df.loc[idx]
                ts = row['timestamp']
                if pd.isna(ts):
                    continue
                current_time = ts.time()
                if current_time < start_time or current_time > end_time:
                    continue
                if trades >= self.params.max_trades_per_day:
                    continue
                if cooldown_end is not None and ts < cooldown_end:
                    continue

                loc = df.index.get_loc(idx)
                if loc == 0:
                    continue
                prev = df.iloc[loc - 1]

                if any(np.isnan(v) for v in (row[mid_col], row[low_col], row[high_col], row['rsi'])):
                    continue
                if not self._trend_is_neutral(row):
                    continue

                signal = 0
                buffer = self.params.band_buffer_pct

                long_setup = (
                    prev['close'] <= prev[low_col] * (1 + buffer)
                    and row['close'] > row[low_col]
                    and prev['rsi'] <= self.params.rsi_reset_long
                    and row['rsi'] >= self.params.rsi_trigger_long
                )
                short_setup = (
                    prev['close'] >= prev[high_col] * (1 - buffer)
                    and row['close'] < row[high_col]
                    and prev['rsi'] >= self.params.rsi_reset_short
                    and row['rsi'] <= self.params.rsi_trigger_short
                )

                if long_setup:
                    signal = 1
                elif short_setup:
                    signal = -1

                if signal != 0:
                    df.at[idx, 'signal'] = signal
                    trades += 1
                    cooldown_end = ts + pd.Timedelta(minutes=self.params.cooldown_minutes)

        df.drop(columns=['date'], inplace=True)
        return df

    def should_exit(self, position: str, row: pd.Series, entry_price: float):
        price = float(row['close'])
        tag = f"{self.params.bb_length}_{self.params.bb_std}".replace('.', '_')
        mid_col = f'bb_mid_{tag}'
        mid_band = row.get(mid_col)

        if position == 'long':
            if mid_band is not None and not np.isnan(mid_band) and price >= mid_band:
                return True, 'mid_band'
            if price >= entry_price + self.params.target_points:
                return True, 'target'
            if price <= entry_price - self.params.stop_points:
                return True, 'stop'
        elif position == 'short':
            if mid_band is not None and not np.isnan(mid_band) and price <= mid_band:
                return True, 'mid_band'
            if price <= entry_price - self.params.target_points:
                return True, 'target'
            if price >= entry_price + self.params.stop_points:
                return True, 'stop'

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


__all__ = ['AdaptiveTrendPullbackScalperStrategy']

"""EMA and Bollinger Band based scalping strategy."""

from __future__ import annotations

import numpy as np
import pandas as pd

from backtester.strategy_base import StrategyBase


class EmaBbandScalper(StrategyBase):
    """Scalping strategy that combines EMA crossovers with Bollinger Bands."""

    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.fast_period = int(p.get('fast_period', 12))
        self.slow_period = int(p.get('slow_period', 26))
        self.bb_period = int(p.get('bb_period', 20))
        self.bb_std_dev = float(p.get('bb_std_dev', 2.0))
        self.swing_lookback = int(p.get('swing_lookback', 5))
        self._signals_df: pd.DataFrame | None = None

    @staticmethod
    def get_params_config():
        return [
            {
                "name": "ebb_fast_period",
                "param_key": "fast_period",
                "type": "number_input",
                "label": "Fast EMA Period",
                "default": 12,
                "min": 2,
                "max": 100,
                "step": 1,
            },
            {
                "name": "ebb_slow_period",
                "param_key": "slow_period",
                "type": "number_input",
                "label": "Slow EMA Period",
                "default": 26,
                "min": 5,
                "max": 200,
                "step": 1,
            },
            {
                "name": "ebb_bb_period",
                "param_key": "bb_period",
                "type": "number_input",
                "label": "Bollinger Band Period",
                "default": 20,
                "min": 5,
                "max": 200,
                "step": 1,
            },
            {
                "name": "ebb_bb_std",
                "param_key": "bb_std_dev",
                "type": "number_input",
                "label": "Bollinger Band Std Dev",
                "default": 2.0,
                "min": 0.5,
                "max": 4.0,
                "step": 0.1,
            },
            {
                "name": "ebb_swing_lookback",
                "param_key": "swing_lookback",
                "type": "number_input",
                "label": "Swing Lookback Bars",
                "default": 5,
                "min": 1,
                "max": 20,
                "step": 1,
            },
        ]

    def indicator_config(self):
        return [
            {
                "column": "ema_fast",
                "label": f"EMA({self.fast_period})",
                "plot": True,
                "panel": 1,
                "color": "green",
            },
            {
                "column": "ema_slow",
                "label": f"EMA({self.slow_period})",
                "plot": True,
                "panel": 1,
                "color": "red",
            },
            {
                "column": "bb_mid",
                "label": f"BB Mid({self.bb_period})",
                "plot": True,
                "panel": 1,
                "color": "orange",
            },
            {
                "column": "bb_upper",
                "label": f"BB Upper({self.bb_period},{self.bb_std_dev})",
                "plot": True,
                "panel": 1,
                "color": "blue",
                "type": "dash",
            },
            {
                "column": "bb_lower",
                "label": f"BB Lower({self.bb_period},{self.bb_std_dev})",
                "plot": True,
                "panel": 1,
                "color": "purple",
                "type": "dash",
            },
        ]

    def generate_signals(self, data):
        df = data.copy()

        if df.empty:
            df['signal'] = []
            self._signals_df = df
            return df

        df['ema_fast'] = df['close'].ewm(span=self.fast_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_period, adjust=False).mean()
        df['bb_mid'] = df['close'].rolling(self.bb_period, min_periods=self.bb_period).mean()
        df['bb_std'] = df['close'].rolling(self.bb_period, min_periods=self.bb_period).std(ddof=0)
        df['bb_upper'] = df['bb_mid'] + self.bb_std_dev * df['bb_std']
        df['bb_lower'] = df['bb_mid'] - self.bb_std_dev * df['bb_std']

        df['bullish_cross_prev'] = (
            (df['ema_fast'].shift(2) <= df['ema_slow'].shift(2))
            & (df['ema_fast'].shift(1) > df['ema_slow'].shift(1))
        )
        df['bearish_cross_prev'] = (
            (df['ema_fast'].shift(2) >= df['ema_slow'].shift(2))
            & (df['ema_fast'].shift(1) < df['ema_slow'].shift(1))
        )

        df['swing_low'] = df['low'].rolling(window=self.swing_lookback, min_periods=1).min().shift(1)
        df['swing_high'] = df['high'].rolling(window=self.swing_lookback, min_periods=1).max().shift(1)

        signals = []
        stops = []
        targets = []
        ema_crossed_above = False
        ema_crossed_below = False

        for idx, row in df.iterrows():
            signal = 0
            stop_price = np.nan
            take_profit = np.nan

            has_bands = not pd.isna(row['bb_mid'])
            ema_ready = not pd.isna(row['ema_fast']) and not pd.isna(row['ema_slow'])

            if ema_ready:
                if bool(row['bullish_cross_prev']):
                    ema_crossed_above = True
                    ema_crossed_below = False
                elif bool(row['bearish_cross_prev']):
                    ema_crossed_below = True
                    ema_crossed_above = False
            else:
                ema_crossed_above = False
                ema_crossed_below = False

            if ema_crossed_above and has_bands:
                pullback = row['low'] <= row['bb_mid']
                bullish_candle = row['close'] > row['open']
                if pullback and bullish_candle:
                    signal = 1
                    stop_price = row['swing_low'] if not pd.isna(row['swing_low']) else row['low']
                    take_profit = row['bb_upper']
                    ema_crossed_above = False

            if signal == 0 and ema_crossed_below and has_bands:
                pullback = row['high'] >= row['bb_mid']
                bearish_candle = row['close'] < row['open']
                if pullback and bearish_candle:
                    signal = -1
                    stop_price = row['swing_high'] if not pd.isna(row['swing_high']) else row['high']
                    take_profit = row['bb_lower']
                    ema_crossed_below = False

            signals.append(signal)
            stops.append(stop_price)
            targets.append(take_profit)

        df['signal'] = signals
        df['stop_loss'] = stops
        df['take_profit'] = targets

        self._signals_df = df
        return df

    def should_exit(self, position, row, entry_price):
        if self._signals_df is None or row.name not in self._signals_df.index:
            return False, ''

        try:
            loc = self._signals_df.index.get_loc(row.name)
        except KeyError:
            return False, ''

        if loc == 0:
            return False, ''

        direction = 1 if position == 'long' else -1
        entry_candidates = self._signals_df.iloc[:loc]
        entry_rows = entry_candidates[entry_candidates['signal'] == direction]

        if entry_rows.empty:
            return False, ''

        entry_row = entry_rows.iloc[-1]
        stop_price = entry_row['stop_loss']
        take_profit = entry_row['take_profit']

        price_high = row.get('high', np.nan)
        price_low = row.get('low', np.nan)

        if position == 'long':
            if not np.isnan(take_profit) and price_high >= take_profit:
                return True, 'take_profit'
            if not np.isnan(stop_price) and price_low <= stop_price:
                return True, 'stop_loss'
        elif position == 'short':
            if not np.isnan(take_profit) and price_low <= take_profit:
                return True, 'take_profit'
            if not np.isnan(stop_price) and price_high >= stop_price:
                return True, 'stop_loss'

        return False, ''

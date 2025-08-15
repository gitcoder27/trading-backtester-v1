"""
This script defines the RSICrossStrategy, a mean reversion strategy based on the Relative Strength Index (RSI).

Strategy Logic:
- This strategy enters trades when the RSI indicates overbought or oversold conditions and then crosses back into the normal range, signaling a potential reversal.
- Long Entry:
  1. The RSI first crosses below the oversold level (20).
  2. A long position is initiated when the RSI crosses back above the oversold level.
- Short Entry:
  1. The RSI first crosses above the overbought level (80).
  2. A short position is taken when the RSI crosses back below the overbought level.
- Exits:
  - Take Profit: The position is closed when the RSI reaches the median level (50).
  - Stop Loss:
    - For a long position, the stop loss is triggered if the RSI crosses back below the oversold level.
    - For a short position, the stop loss is triggered if the RSI crosses back above the overbought level.
"""
from backtester.strategy_base import StrategyBase
import pandas as pd

class RSICrossStrategy(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.rsi_period = params.get('rsi_period', 9) if params else 9
        self.overbought = params.get('overbought', 80) if params else 80
        self.oversold = params.get('oversold', 20) if params else 20
        self.median = 50
        self.debug = params.get('debug', False) if params else False

    @staticmethod
    def get_params_config():
        return [
            {
                "name": "rsi_period", "param_key": "rsi_period", "type": "number_input",
                "label": "RSI Period", "default": 9, "min": 2, "max": 50, "step": 1
            },
            {
                "name": "rsi_overbought", "param_key": "overbought", "type": "number_input",
                "label": "Overbought", "default": 80, "min": 50, "max": 100, "step": 1
            },
            {
                "name": "rsi_oversold", "param_key": "oversold", "type": "number_input",
                "label": "Oversold", "default": 20, "min": 0, "max": 50, "step": 1
            },
        ]

    def indicator_config(self):
        return [
            {"column": "rsi", "label": f"RSI({self.rsi_period})", "plot": True, "color": "blue", "type": "solid", "panel": 2}
        ]

    def compute_rsi(self, series, period):
        # Wilder's RSI
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ma_up = up.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        ma_down = down.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        rsi = 100 - (100 / (1 + ma_up / ma_down))
        return rsi

    def generate_signals(self, data):
        df = data.copy()
        df['rsi'] = self.compute_rsi(df['close'], self.rsi_period)
        df['signal'] = 0
        in_position = False
        last_entry = None
        last_entry_type = None

        for i in range(1, len(df)):
            rsi_prev = df['rsi'].iloc[i-1]
            rsi_cur = df['rsi'].iloc[i]
            # Long Entry
            if not in_position:
                if rsi_prev > self.oversold and rsi_cur <= self.oversold:
                    last_entry = 'below_oversold'
                    last_entry_type = 'long'
                if last_entry == 'below_oversold' and last_entry_type == 'long' and rsi_prev < self.oversold and rsi_cur >= self.oversold:
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                    in_position = True
                    last_entry = None
                    last_entry_type = None
                    if self.debug:
                        print(f"LONG ENTRY at {df['timestamp'].iloc[i]} | RSI: {rsi_cur:.2f}")
            # Short Entry
            if not in_position:
                if rsi_prev < self.overbought and rsi_cur >= self.overbought:
                    last_entry = 'above_overbought'
                    last_entry_type = 'short'
                if last_entry == 'above_overbought' and last_entry_type == 'short' and rsi_prev > self.overbought and rsi_cur <= self.overbought:
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                    in_position = True
                    last_entry = None
                    last_entry_type = None
                    if self.debug:
                        print(f"SHORT ENTRY at {df['timestamp'].iloc[i]} | RSI: {rsi_cur:.2f}")
            # Reset in_position if exited (engine handles exit, but for safety)
            if in_position and df['signal'].iloc[i] == 0:
                in_position = False
        return df

    def should_exit(self, position, row, entry_price):
        rsi = row.rsi
        if position == 'long':
            if rsi <= self.oversold:
                return True, 'RSI SL'
            elif rsi >= self.median:
                return True, 'RSI TP'
        elif position == 'short':
            if rsi >= self.overbought:
                return True, 'RSI SL'
            elif rsi <= self.median:
                return True, 'RSI TP'
        return False, ''

from backtester.strategy_base import StrategyBase
import pandas as pd

class RSICrossStrategy(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.rsi_period = params.get('rsi_period', 9) if params else 9
        self.overbought = params.get('overbought', 80) if params else 80
        self.oversold = params.get('oversold', 20) if params else 20
        self.median = 50
        self.debug = params.get('debug', False) if params else False

    def indicator_config(self):
        return [
            {"column": "rsi", "label": f"RSI({self.rsi_period})", "plot": True, "color": "blue", "type": "solid", "panel": 2}
        ]

    def compute_rsi(self, series, period):
        # Wilder's RSI
        delta = series.diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        ma_up = up.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        ma_down = down.ewm(alpha=1/period, min_periods=period, adjust=False).mean()
        rsi = 100 - (100 / (1 + ma_up / ma_down))
        return rsi

    def generate_signals(self, data):
        df = data.copy()
        df['rsi'] = self.compute_rsi(df['close'], self.rsi_period)
        df['signal'] = 0
        in_position = False
        last_entry = None
        last_entry_type = None

        for i in range(1, len(df)):
            rsi_prev = df['rsi'].iloc[i-1]
            rsi_cur = df['rsi'].iloc[i]
            # Long Entry
            if not in_position:
                if rsi_prev > self.oversold and rsi_cur <= self.oversold:
                    last_entry = 'below_oversold'
                    last_entry_type = 'long'
                if last_entry == 'below_oversold' and last_entry_type == 'long' and rsi_prev < self.oversold and rsi_cur >= self.oversold:
                    df.iloc[i, df.columns.get_loc('signal')] = 1
                    in_position = True
                    last_entry = None
                    last_entry_type = None
                    if self.debug:
                        print(f"LONG ENTRY at {df['timestamp'].iloc[i]} | RSI: {rsi_cur:.2f}")
            # Short Entry
            if not in_position:
                if rsi_prev < self.overbought and rsi_cur >= self.overbought:
                    last_entry = 'above_overbought'
                    last_entry_type = 'short'
                if last_entry == 'above_overbought' and last_entry_type == 'short' and rsi_prev > self.overbought and rsi_cur <= self.overbought:
                    df.iloc[i, df.columns.get_loc('signal')] = -1
                    in_position = True
                    last_entry = None
                    last_entry_type = None
                    if self.debug:
                        print(f"SHORT ENTRY at {df['timestamp'].iloc[i]} | RSI: {rsi_cur:.2f}")
            # Reset in_position if exited (engine handles exit, but for safety)
            if in_position and df['signal'].iloc[i] == 0:
                in_position = False
        return df

    def should_exit(self, position, row, entry_price):
        rsi = row.rsi
        if position == 'long':
            if rsi <= self.oversold:
                return True, 'RSI SL'
            elif rsi >= self.median:
                return True, 'RSI TP'
        elif position == 'short':
            if rsi >= self.overbought:
                return True, 'RSI SL'
            elif rsi <= self.median:
                return True, 'RSI TP'
        return False, ''

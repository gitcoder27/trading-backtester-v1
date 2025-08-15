"""
This script defines the EMA50ScalperStrategy, a long-only scalping strategy that uses the 50-period Exponential Moving Average (EMA).

Strategy Logic:
- This strategy aims to capture upward movements by entering trades when the price shows strength by crossing above the 50 EMA.
- Long Entry: A long position is initiated when the price crosses above the 50 EMA.
- Short Entry: This is a long-only strategy and does not generate short signals.
- Exits:
  - The position is closed if the price closes below the 50 EMA, which serves as a dynamic trailing stop.
  - A fixed profit target of 20 points from the entry price.
"""
import pandas as pd
from backtester.strategy_base import StrategyBase

class EMA50ScalperStrategy(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.ema_period = params.get('ema_period', 50) if params else 50
        self.profit_target_points = params.get('profit_target_points', 20) if params else 20
        # Enable fast vectorized approach
        self._use_fast_vectorized = True

    @staticmethod
    def get_params_config():
        return [
            {
                "name": "ema50_ema_period", "param_key": "ema_period", "type": "number_input",
                "label": "EMA Period", "default": 50, "min": 10, "max": 200, "step": 1
            },
            {
                "name": "ema50_pt", "param_key": "profit_target_points", "type": "number_input",
                "label": "Profit Target (pts)", "default": 20, "min": 1, "max": 400, "step": 1
            },
        ]

    def indicator_config(self):
        return [
            {
                "column": "ema",
                "label": f"EMA({self.ema_period})",
                "plot": True,
                "color": "orange",
                "type": "solid",
                "panel": 1,
            }
        ]

    def generate_signals(self, data):
        """
        Adds 'signal' column to data:
        1 = Long Entry, 0 = No Entry/Flat
        """
        df = data.copy()
        df['ema'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()
        df['prev_close'] = df['close'].shift(1)
        df['prev_ema'] = df['ema'].shift(1)

        # Long Entry: prev_close < prev_ema and close > ema
        long_entry = (df['prev_close'] < df['prev_ema']) & (df['close'] > df['ema'])

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1

        return df

    def should_exit(self, position, row, entry_price):
        """
        Given current position ('long' or 'short'), current row, and entry price,
        return (exit_now: bool, exit_reason: str) for this bar.
        """
        if position == 'long':
            # Exit if price closes below EMA
            if row.close < row.ema:  # Changed from row['close'] < row['ema']
                return True, 'close_below_ema'

            # Exit if profit target is reached
            if row.high >= entry_price + self.profit_target_points:  # Changed from row['high']
                return True, 'profit_target'

        return False, ''

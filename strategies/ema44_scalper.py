"""
This script defines the EMA44ScalperStrategy, which is a scalping strategy based on the 44-period Exponential Moving Average (EMA).

Strategy Logic:
- This strategy uses the 44 EMA as a key level to identify the short-term trend.
- Long Entry: A long trade is initiated when the price crosses above the 44 EMA, suggesting a potential upward move.
- Short Entry: A short trade is taken when the price crosses below the 44 EMA, indicating a potential downward move.
- Exits:
  - A long position is exited if the price closes below the 44 EMA.
  - A short position is exited if the price closes above the 44 EMA.
  - A fixed profit target of 30 points from the entry price.
  - A fixed stop loss of 20 points from the entry price.
"""

import pandas as pd
from backtester.strategy_base import StrategyBase

class EMA44ScalperStrategy(StrategyBase):
    def should_exit(self, position, row, entry_price):
        price = row.close
        ema = row.ema
        if position == 'long':
            if price < ema:
                return True, 'EMA exit'
            elif price >= entry_price + 30:
                return True, 'Target'
            elif price <= entry_price - 20:
                return True, 'Stop Loss'
        elif position == 'short':
            if price > ema:
                return True, 'EMA exit'
            elif price <= entry_price - 30:
                return True, 'Target'
            elif price >= entry_price + 20:
                return True, 'Stop Loss'
        return False, ''
    def __init__(self, params=None):
        super().__init__(params)
        self.ema_period = 44

    def indicator_config(self):
        """
        Returns a list of indicator configs for plotting.
        """
        return [
            {
                "column": "ema",
                "label": f"EMA({self.ema_period})",
                "plot": True,
                "color": "orange",
                "type": "solid"
            }
        ]

    def generate_signals(self, data):
        """
        Adds 'signal' column to data:
        1 = Long Entry, -1 = Short Entry, 0 = No Entry/Flat
        """
        df = data.copy()
        df['ema'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()
        df['prev_close'] = df['close'].shift(1)
        df['prev_ema'] = df['ema'].shift(1)

        # Long Entry: prev_close < prev_ema and close > ema
        long_entry = (df['prev_close'] < df['prev_ema']) & (df['close'] > df['ema'])
        # Short Entry: prev_close > prev_ema and close < ema
        short_entry = (df['prev_close'] > df['prev_ema']) & (df['close'] < df['ema'])

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1

        return df
"""
EMA-10 Scalper (v1) Strategy
Objective: Capture small, quick profits based on price crossing the 10-period EMA.
"""

import pandas as pd
from backtester.strategy_base import StrategyBase

class EMA10ScalperStrategy(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.ema_period = 10
        self.profit_target = 20
        self.stop_loss = 15

    def indicator_config(self):
        """
        Configuration describing which indicators to plot and how.
        Used by the engine to expose indicator columns and by plotting to render overlays.
        """
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

    def should_exit(self, position, row, entry_price):
        price = row.close if hasattr(row, 'close') else row['close']
        ema = row.ema if hasattr(row, 'ema') else row['ema']
        if position == 'long':
            # Exit if price closes below EMA
            if price < ema:
                return True, 'EMA exit'
            # Exit if profit target reached
            if price >= entry_price + self.profit_target:
                return True, 'Target'
            # Exit if stop loss hit
            if price <= entry_price - self.stop_loss:
                return True, 'Stop Loss'
        elif position == 'short':
            # Exit if price closes above EMA
            if price > ema:
                return True, 'EMA exit'
            # Exit if profit target reached
            if price <= entry_price - self.profit_target:
                return True, 'Target'
            # Exit if stop loss hit
            if price >= entry_price + self.stop_loss:
                return True, 'Stop Loss'
        return False, ''
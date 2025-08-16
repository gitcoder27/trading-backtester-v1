"""
This script implements the EMA10ScalperStrategy, a scalping strategy based on the 10-period Exponential Moving Average (EMA).

Strategy Logic:
- The core idea is to trade based on price crossovers of the 10 EMA, which acts as a dynamic support and resistance level.
- Long Entry: A long position is initiated when the price crosses above the 10 EMA, suggesting a potential uptrend.
- Short Entry: A short position is taken when the price crosses below the 10 EMA, indicating a potential downtrend.
- Exits:
  - A long position is exited if the price closes below the 10 EMA.
  - A short position is exited if the price closes above the 10 EMA.
  - A fixed profit target of 20 points from the entry price.
  - A fixed stop loss of 15 points from the entry price.
"""

import pandas as pd
from backtester.strategy_base import StrategyBase

class EMA10ScalperStrategy(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.ema_period = params.get('ema_period', 10) if params else 10
        self.profit_target = params.get('profit_target', 20) if params else 20
        self.stop_loss = params.get('stop_loss', 15) if params else 15
        # Enable fast vectorized approach for simple signal-based strategies
        self._use_fast_vectorized = True

    @staticmethod
    def get_params_config():
        return [
            {
                "name": "ema10_ema_period", "param_key": "ema_period", "type": "number_input",
                "label": "EMA Period", "default": 10, "min": 5, "max": 200, "step": 1
            },
            {
                "name": "ema10_pt", "param_key": "profit_target", "type": "number_input",
                "label": "Profit Target (pts)", "default": 20, "min": 1, "max": 400, "step": 1
            },
            {
                "name": "ema10_sl", "param_key": "stop_loss", "type": "number_input",
                "label": "Stop Loss (pts)", "default": 15, "min": 1, "max": 400, "step": 1
            },
        ]

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
        Optimized signal generation using vectorized operations.
        Adds 'signal' column to data:
        1 = Long Entry, -1 = Short Entry, 0 = No Entry/Flat
        """
        df = data.copy()
        
        # Vectorized EMA calculation
        df['ema'] = df['close'].ewm(span=self.ema_period, adjust=False).mean()
        
        # Vectorized signal calculation using shift operations
        prev_close = df['close'].shift(1)
        prev_ema = df['ema'].shift(1)
        
        # Vectorized conditions
        long_condition = (prev_close < prev_ema) & (df['close'] > df['ema'])
        short_condition = (prev_close > prev_ema) & (df['close'] < df['ema'])
        
        # Create signal column efficiently
        df['signal'] = 0
        df.loc[long_condition, 'signal'] = 1
        df.loc[short_condition, 'signal'] = -1
        
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

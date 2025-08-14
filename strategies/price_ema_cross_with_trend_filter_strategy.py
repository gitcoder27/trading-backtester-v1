"""
This script implements the PriceEMACrossWithTrendFilterStrategy.

Strategy Logic:
- A slow EMA (20-period) is used as a trend filter.
- A fast EMA (5-period) is used for entry signals.
- Long Entry: When the price is above the slow EMA (uptrend), a long position is taken if the price crosses above the fast EMA.
- Short Entry: When the price is below the slow EMA (downtrend), a short position is taken if the price crosses below the fast EMA.
- Exits:
  - A fixed profit target.
  - A fixed stop loss.
"""

import pandas as pd
from backtester.strategy_base import StrategyBase

class PriceEMACrossWithTrendFilterStrategy(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.fast_ema_period = params.get('fast_ema_period', 5) if params else 5
        self.slow_ema_period = params.get('slow_ema_period', 20) if params else 20
        self.rsi_period = params.get('rsi_period', 14) if params else 14
        self.atr_period = params.get('atr_period', 14) if params else 14
        self.atr_multiplier = params.get('atr_multiplier', 2) if params else 2
        self.max_stop_loss_points = params.get('max_stop_loss_points', 35) if params else 35
        self.profit_target = params.get('profit_target', 30) if params else 30

    def indicator_config(self):
        return [
            {
                "column": "ema_fast",
                "label": f"EMA({self.fast_ema_period})",
                "plot": True,
                "color": "blue",
                "type": "solid",
                "panel": 1,
            },
            {
                "column": "ema_slow",
                "label": f"EMA({self.slow_ema_period})",
                "plot": True,
                "color": "red",
                "type": "solid",
                "panel": 1,
            },
            {
                "column": "rsi",
                "label": f"RSI({self.rsi_period})",
                "plot": True,
                "color": "purple",
                "type": "solid",
                "panel": 2,
            },
            {
                "column": "atr",
                "label": f"ATR({self.atr_period})",
                "plot": True,
                "color": "grey",
                "type": "solid",
                "panel": 3,
            }
        ]

    def generate_signals(self, data):
        df = data.copy()
        df['ema_fast'] = df['close'].ewm(span=self.fast_ema_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_ema_period, adjust=False).mean()

        # Calculate RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Calculate ATR
        df['high_low'] = df['high'] - df['low']
        df['high_prev_close'] = (df['high'] - df['close'].shift(1)).abs()
        df['low_prev_close'] = (df['low'] - df['close'].shift(1)).abs()
        df['true_range'] = df[['high_low', 'high_prev_close', 'low_prev_close']].max(axis=1)
        df['atr'] = df['true_range'].rolling(window=self.atr_period).mean()

        df['prev_close'] = df['close'].shift(1)

        df['prev_ema_fast'] = df['ema_fast'].shift(1)
        df['prev_ema_slow'] = df['ema_slow'].shift(1)

        # Uptrend: price is above slow EMA
        uptrend = df['close'] > df['ema_slow']

        # Downtrend: price is below slow EMA
        downtrend = df['close'] < df['ema_slow']

        # Long entry: in uptrend, price crosses above fast EMA, and RSI > 50
        long_entry = uptrend & (df['close'] > df['ema_fast']) & (df['prev_close'] < df['prev_ema_fast']) & (df['rsi'] > 50)

        # Short entry: in downtrend, price crosses below fast EMA, and RSI < 50
        short_entry = downtrend & (df['close'] < df['ema_fast']) & (df['prev_close'] > df['prev_ema_fast']) & (df['rsi'] < 50)

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1

        return df

    def should_exit(self, position, row, entry_price):
        price = row.close
        atr = row.atr

        # Check if ATR is valid
        if pd.isna(atr) or atr == 0:
            return False, ''

        stop_loss_points = min(atr * self.atr_multiplier, self.max_stop_loss_points)

        if position == 'long':
            # Exit if profit target reached
            if price >= entry_price + self.profit_target:
                return True, 'Target'
            # Exit if stop loss hit
            if price <= entry_price - stop_loss_points:
                return True, 'Stop Loss'
        elif position == 'short':
            # Exit if profit target reached
            if price <= entry_price - self.profit_target:
                return True, 'Target'
            # Exit if stop loss hit
            if price >= entry_price + stop_loss_points:
                return True, 'Stop Loss'

        return False, ''

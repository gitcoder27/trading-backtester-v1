import pandas as pd
from backtester.strategy_base import StrategyBase

class EMA50ScalperStrategy(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.ema_period = 50
        self.profit_target_points = 20

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
            if row['close'] < row['ema']:
                return True, 'close_below_ema'

            # Exit if profit target is reached
            if row['high'] >= entry_price + self.profit_target_points:
                return True, 'profit_target'

        return False, ''

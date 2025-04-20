from backtester.strategy_base import StrategyBase
import pandas as pd

class BBandsScalperStrategy(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.length = 20
        self.stddev = 2

    def generate_signals(self, data):
        """
        Adds 'signal' column to data:
        1 = Long Entry, -1 = Short Entry, 0 = No Entry/Flat
        Long: Close crosses up into band from below lower band
        Short: Close crosses down into band from above upper band
        Exit: Flat when price hits SMA20 (midline) or opposite band
        """
        df = data.copy()
        df['mid'] = df['close'].rolling(self.length).mean()
        df['std'] = df['close'].rolling(self.length).std(ddof=0)
        df['upper'] = df['mid'] + self.stddev * df['std']
        df['lower'] = df['mid'] - self.stddev * df['std']
        df['prev_close'] = df['close'].shift(1)
        df['prev_upper'] = df['upper'].shift(1)
        df['prev_lower'] = df['lower'].shift(1)
        df['prev_mid'] = df['mid'].shift(1)

        # Long: prev_close < prev_lower and close > lower
        long_entry = (df['prev_close'] < df['prev_lower']) & (df['close'] > df['lower'])
        # Short: prev_close > prev_upper and close < upper
        short_entry = (df['prev_close'] > df['prev_upper']) & (df['close'] < df['upper'])
        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1
        return df

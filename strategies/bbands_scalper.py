"""
This script defines the BBandsScalperStrategy, a scalping strategy utilizing Bollinger Bands.

Strategy Logic:
- Long Entry: A long position is initiated when the price, after dipping below the lower Bollinger Band, crosses back up above it. This is interpreted as a potential bullish reversal signal.
- Short Entry: A short position is taken when the price, after surging above the upper Bollinger Band, crosses back down below it, signaling a potential bearish reversal.
- Exits:
  - The position is closed if the price touches the middle Bollinger Band (the 20-period SMA).
  - A fixed profit target of 30 points from the entry price.
  - A fixed stop loss of 20 points from the entry price.
"""
from backtester.strategy_base import StrategyBase
import pandas as pd

class BBandsScalperStrategy(StrategyBase):
    def should_exit(self, position, row, entry_price):
        price = row['close']
        mid = row['mid']
        if position == 'long':
            if price < mid:
                return True, 'Mid exit'
            elif price >= entry_price + 30:
                return True, 'Target'
            elif price <= entry_price - 20:
                return True, 'Stop Loss'
        elif position == 'short':
            if price > mid:
                return True, 'Mid exit'
            elif price <= entry_price - 30:
                return True, 'Target'
            elif price >= entry_price + 20:
                return True, 'Stop Loss'
        return False, ''
    def __init__(self, params=None):
        super().__init__(params)
        self.length = 20
        self.stddev = 2
        # Enable fast vectorized approach for simple signal-based logic
        self._use_fast_vectorized = True

    def indicator_config(self):
        """
        Returns a list of indicator configs for plotting.
        """
        return [
            {
                "column": "mid",
                "label": f"BB-Mid({self.length})",
                "plot": True,
                "color": "orange",
                "type": "solid"
            },
            {
                "column": "upper",
                "label": f"BB-Upper({self.length},{self.stddev})",
                "plot": True,
                "color": "green",
                "type": "dash"
            },
            {
                "column": "lower",
                "label": f"BB-Lower({self.length},{self.stddev})",
                "plot": True,
                "color": "red",
                "type": "dash"
            }
        ]

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

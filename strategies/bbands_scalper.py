from backtester.strategy_base import StrategyBase
import pandas as pd

class BBandsScalperStrategy(StrategyBase):
    def should_exit(self, position, row, entry_price):
        price = row['close']
        mid = row['mid']
        if position == 'long':
            if price >= entry_price + 60:
                return True, 'Target'
            elif price <= entry_price - 30:
                return True, 'Stop Loss'
        elif position == 'short':
            if price <= entry_price - 60:
                return True, 'Target'
            elif price >= entry_price + 30:
                return True, 'Stop Loss'
        return False, ''

    def __init__(self, params=None):
        super().__init__(params)
        self.length = 20
        self.stddev = 2

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

        # RSI calculation
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        df['rsi'] = 100 - (100 / (1 + rs))

        # Long: close < lower and rsi < 30
        long_entry = (df['close'] < df['lower']) & (df['rsi'] < 30)
        # Short: close > upper and rsi > 70
        short_entry = (df['close'] > df['upper']) & (df['rsi'] > 70)

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1
        return df

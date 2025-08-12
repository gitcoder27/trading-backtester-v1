"""
This script defines the MeanReversionScalper, a classic mean reversion strategy using Bollinger Bands.

Strategy Logic:
- This strategy enters trades when the price "pierces" one of the outer Bollinger Bands, anticipating a return to the middle band (the moving average).
- Long Entry: A long position is initiated when the price closes below the lower Bollinger Band, after being inside the bands in the previous candle.
- Short Entry: A short position is taken when the price closes above the upper Bollinger Band, after being inside the bands in the previous candle.
- Exits:
  - Take Profit: The position is closed when the price reaches the middle Bollinger Band.
  - Stop Loss: A fixed stop loss of 20 points from the entry price.
"""
from backtester.strategy_base import StrategyBase
import pandas as pd

class MeanReversionScalper(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.bb_length = int(p.get('bb_length', 20))
        self.bb_std = float(p.get('bb_std', 2.0))
        self.stop_loss_points = float(p.get('stop_loss_points', 20))

    def indicator_config(self):
        return [
            {
                "column": f"BBL_{self.bb_length}_{self.bb_std}".replace('.', '_'),
                "label": f"BB-Lower({self.bb_length}, {self.bb_std})",
                "plot": True,
                "color": "red",
                "type": "dash"
            },
            {
                "column": f"BBM_{self.bb_length}_{self.bb_std}".replace('.', '_'),
                "label": f"BB-Mid({self.bb_length}, {self.bb_std})",
                "plot": True,
                "color": "orange",
                "type": "solid"
            },
            {
                "column": f"BBU_{self.bb_length}_{self.bb_std}".replace('.', '_'),
                "label": f"BB-Upper({self.bb_length}, {self.bb_std})",
                "plot": True,
                "color": "green",
                "type": "dash"
            }
        ]

    def generate_signals(self, data):
        df = data.copy()
        # Compute Bollinger Bands without pandas_ta to avoid dependency issues
        close = df['close']
        ma = close.rolling(self.bb_length, min_periods=self.bb_length).mean()
        stdev = close.rolling(self.bb_length, min_periods=self.bb_length).std()

        std_val = self.bb_std
        # Column names must match indicator_config (with '.' replaced by '_')
        col_bbl = f"BBL_{self.bb_length}_{std_val}".replace('.', '_')
        col_bbm = f"BBM_{self.bb_length}_{std_val}".replace('.', '_')
        col_bbu = f"BBU_{self.bb_length}_{std_val}".replace('.', '_')

        df[col_bbm] = ma
        df[col_bbl] = ma - std_val * stdev
        df[col_bbu] = ma + std_val * stdev

        df['prev_close'] = df['close'].shift(1)
        df[f'prev_BBL'] = df[f'BBL_{self.bb_length}_{self.bb_std}'.replace('.', '_')].shift(1)
        df[f'prev_BBU'] = df[f'BBU_{self.bb_length}_{self.bb_std}'.replace('.', '_')].shift(1)

        long_entry = (df['close'] < df[f'BBL_{self.bb_length}_{self.bb_std}'.replace('.', '_')]) & (df['prev_close'] >= df[f'prev_BBL'])
        short_entry = (df['close'] > df[f'BBU_{self.bb_length}_{self.bb_std}'.replace('.', '_')]) & (df['prev_close'] <= df[f'prev_BBU'])

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1

        return df

    def should_exit(self, position, row, entry_price):
        mid_band_col = f"BBM_{self.bb_length}_{self.bb_std}".replace('.', '_')
        mid_band = getattr(row, mid_band_col)
        price = row.close

        if position == 'long':
            if price >= mid_band:
                return True, 'Take Profit (Mid Band)'
            elif price <= entry_price - self.stop_loss_points:
                return True, 'Stop Loss'
        elif position == 'short':
            if price <= mid_band:
                return True, 'Take Profit (Mid Band)'
            elif price >= entry_price + self.stop_loss_points:
                return True, 'Stop Loss'

        return False, ''

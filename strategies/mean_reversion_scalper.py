from backtester.strategy_base import StrategyBase
import pandas as pd
import pandas_ta as ta

class MeanReversionScalper(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        self.bb_length = 20
        self.bb_std = 2.0
        self.stop_loss_points = 20

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
        bbands = ta.bbands(df['close'], length=self.bb_length, std=self.bb_std)
        # Rename columns to be valid identifiers
        bbands.columns = [f"{col.replace('.', '_')}" for col in bbands.columns]
        df = pd.concat([df, bbands], axis=1)

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

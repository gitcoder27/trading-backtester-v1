from backtester.strategy_base import StrategyBase
import pandas as pd

class RangeScalper(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.bb_length = int(p.get('bb_length', 30))
        self.bb_std = float(p.get('bb_std', 2.5))
        self.stoch_k = int(p.get('stoch_k', 21))
        self.stoch_d = int(p.get('stoch_d', 5))
        self.stoch_os = int(p.get('stoch_os', 15))
        self.stoch_ob = int(p.get('stoch_ob', 85))
        self.stop_loss_points = float(p.get('stop_loss_points', 10))

    def indicator_config(self):
        return [
            {"column": "BBL", "label": "BB-Lower", "plot": True, "color": "red"},
            {"column": "BBM", "label": "BB-Mid", "plot": True, "color": "orange"},
            {"column": "BBU", "label": "BB-Upper", "plot": True, "color": "green"},
            {"column": "STOCH_K", "label": "Stoch %K", "plot": False},
            {"column": "STOCH_D", "label": "Stoch %D", "plot": False},
        ]

    def generate_signals(self, data):
        df = data.copy()

        # Bollinger Bands
        df['BBM'] = df['close'].rolling(window=self.bb_length).mean()
        df['BBU'] = df['BBM'] + self.bb_std * df['close'].rolling(window=self.bb_length).std()
        df['BBL'] = df['BBM'] - self.bb_std * df['close'].rolling(window=self.bb_length).std()

        # Stochastic Oscillator
        low_min = df['low'].rolling(window=self.stoch_k).min()
        high_max = df['high'].rolling(window=self.stoch_k).max()
        df['STOCH_K'] = 100 * (df['close'] - low_min) / (high_max - low_min)
        df['STOCH_D'] = df['STOCH_K'].rolling(window=self.stoch_d).mean()

        long_entry = (df['close'] < df['BBL']) & (df['STOCH_K'] < self.stoch_os)
        short_entry = (df['close'] > df['BBU']) & (df['STOCH_K'] > self.stoch_ob)

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1
        return df

    def should_exit(self, position, row, entry_price):
        price = row.close
        if position == 'long':
            if price >= row.BBM:
                return True, 'Take Profit (Mid Band)'
            elif price <= entry_price - self.stop_loss_points:
                return True, 'Stop Loss'
        elif position == 'short':
            if price <= row.BBM:
                return True, 'Take Profit (Mid Band)'
            elif price >= entry_price + self.stop_loss_points:
                return True, 'Stop Loss'
        return False, ''

from backtester.strategy_base import StrategyBase
import pandas as pd

class RsiMomentumScalper(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.rsi_period = int(p.get('rsi_period', 14))
        self.fast_ema_period = int(p.get('fast_ema_period', 9))
        self.slow_ema_period = int(p.get('slow_ema_period', 21))
        self.rsi_buy_threshold = float(p.get('rsi_buy_threshold', 55.0))
        self.rsi_sell_threshold = float(p.get('rsi_sell_threshold', 45.0))
        self.stop_loss_points = float(p.get('stop_loss_points', 10))
        self.take_profit_points = float(p.get('take_profit_points', 20))

    def indicator_config(self):
        return [
            {
                "column": f"rsi_{self.rsi_period}",
                "label": f"RSI({self.rsi_period})",
                "plot": True,
                "color": "purple"
            },
            {
                "column": f"ema_fast",
                "label": f"EMA({self.fast_ema_period})",
                "plot": True,
                "color": "blue"
            },
            {
                "column": f"ema_slow",
                "label": f"EMA({self.slow_ema_period})",
                "plot": True,
                "color": "orange"
            }
        ]

    def generate_signals(self, data):
        df = data.copy()

        # RSI
        delta = df['close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=self.rsi_period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=self.rsi_period).mean()
        rs = gain / loss
        df[f'rsi_{self.rsi_period}'] = 100 - (100 / (1 + rs))

        # EMAs
        df['ema_fast'] = df['close'].ewm(span=self.fast_ema_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_ema_period, adjust=False).mean()

        df['prev_rsi'] = df[f'rsi_{self.rsi_period}'].shift(1)

        long_entry = (df['ema_fast'] > df['ema_slow']) & (df[f'rsi_{self.rsi_period}'] > self.rsi_buy_threshold) & (df['prev_rsi'] <= self.rsi_buy_threshold)
        short_entry = (df['ema_fast'] < df['ema_slow']) & (df[f'rsi_{self.rsi_period}'] < self.rsi_sell_threshold) & (df['prev_rsi'] >= self.rsi_sell_threshold)

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1

        return df

    def should_exit(self, position, row, entry_price):
        price = row.close

        if position == 'long':
            if price >= entry_price + self.take_profit_points:
                return True, 'Take Profit'
            elif price <= entry_price - self.stop_loss_points:
                return True, 'Stop Loss'
        elif position == 'short':
            if price <= entry_price - self.take_profit_points:
                return True, 'Take Profit'
            elif price >= entry_price + self.stop_loss_points:
                return True, 'Stop Loss'

        return False, ''

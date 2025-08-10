from backtester.strategy_base import StrategyBase
import pandas as pd

class TrendScalper(StrategyBase):
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.fast_ema_period = int(p.get('fast_ema', 9))
        self.slow_ema_period = int(p.get('slow_ema', 21))
        self.rsi_period_fast = int(p.get('rsi_period_fast', 14))
        self.rsi_period_slow = int(p.get('rsi_period_slow', 25))
        self.stop_loss_points = float(p.get('stop_loss_points', 6))

    def indicator_config(self):
        return [
            {"column": "ema_fast", "label": f"EMA({self.fast_ema_period})", "plot": True, "color": "blue"},
            {"column": "ema_slow", "label": f"EMA({self.slow_ema_period})", "plot": True, "color": "purple"},
            {"column": "rsi_fast", "label": f"RSI({self.rsi_period_fast})", "plot": False},
            {"column": "rsi_slow", "label": f"RSI({self.rsi_period_slow})", "plot": False},
        ]

    def generate_signals(self, data):
        df = data.copy()
        df['ema_fast'] = df['close'].ewm(span=self.fast_ema_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_ema_period, adjust=False).mean()

        for period, name in [(self.rsi_period_fast, 'rsi_fast'), (self.rsi_period_slow, 'rsi_slow')]:
            delta = df['close'].diff()
            gain = delta.where(delta > 0, 0).rolling(window=period).mean()
            loss = -delta.where(delta < 0, 0).rolling(window=period).mean()
            rs = gain / loss
            df[name] = 100 - (100 / (1 + rs))

        df['prev_ema_fast'] = df['ema_fast'].shift(1)
        df['prev_ema_slow'] = df['ema_slow'].shift(1)

        long_entry = (df['ema_fast'] > df['ema_slow']) & (df['rsi_fast'] > 60) & (df['rsi_slow'] > 50) & (df['close'].between(df['ema_slow'], df['ema_fast']))
        short_entry = (df['ema_fast'] < df['ema_slow']) & (df['rsi_fast'] < 40) & (df['rsi_slow'] < 50) & (df['close'].between(df['ema_fast'], df['ema_slow']))

        df['signal'] = 0
        df.loc[long_entry, 'signal'] = 1
        df.loc[short_entry, 'signal'] = -1
        return df

    def should_exit(self, position, row, entry_price):
        price = row.close

        if position == 'long':
            if price <= entry_price - self.stop_loss_points:
                return True, 'Stop Loss'
            if row.ema_fast < row.ema_slow:
                return True, 'EMA Cross'
            if price >= row.ema_slow:
                return True, 'Take Profit (Slow EMA)'
        elif position == 'short':
            if price >= entry_price + self.stop_loss_points:
                return True, 'Stop Loss'
            if row.ema_fast > row.ema_slow:
                return True, 'EMA Cross'
            if price <= row.ema_slow:
                return True, 'Take Profit (Slow EMA)'

        return False, ''

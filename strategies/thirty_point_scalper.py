from backtester.strategy_base import StrategyBase
import pandas as pd

class ThirtyPointScalperStrategy(StrategyBase):
    """Simple EMA crossover scalper with fixed profit target and stop loss."""
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.ema_fast = int(p.get('ema_fast', 5))
        self.ema_slow = int(p.get('ema_slow', 20))
        self.take_profit = float(p.get('take_profit', 30))  # points
        self.stop_loss = float(p.get('stop_loss', 15))      # points
        self._use_fast_vectorized = False

    def indicator_config(self):
        return [
            {"column": "ema_fast", "label": f"EMA{self.ema_fast}", "plot": True, "color": "blue"},
            {"column": "ema_slow", "label": f"EMA{self.ema_slow}", "plot": True, "color": "red"},
        ]

    def generate_signals(self, data):
        df = data.copy()
        df['ema_fast'] = df['close'].ewm(span=self.ema_fast, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.ema_slow, adjust=False).mean()
        cross_up = (df['ema_fast'] > df['ema_slow']) & (df['ema_fast'].shift() <= df['ema_slow'].shift())
        cross_down = (df['ema_fast'] < df['ema_slow']) & (df['ema_fast'].shift() >= df['ema_slow'].shift())
        df['signal'] = 0
        df.loc[cross_up, 'signal'] = 1
        df.loc[cross_down, 'signal'] = -1
        return df

    def should_exit(self, position, row, entry_price):
        price = row.close
        if position == 'long':
            if price >= entry_price + self.take_profit:
                return True, 'Take Profit'
            if price <= entry_price - self.stop_loss:
                return True, 'Stop Loss'
            if row.ema_fast < row.ema_slow:
                return True, 'EMA Cross Exit'
        elif position == 'short':
            if price <= entry_price - self.take_profit:
                return True, 'Take Profit'
            if price >= entry_price + self.stop_loss:
                return True, 'Stop Loss'
            if row.ema_fast > row.ema_slow:
                return True, 'EMA Cross Exit'
        return False, ''

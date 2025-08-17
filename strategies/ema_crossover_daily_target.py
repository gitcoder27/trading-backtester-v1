from backtester.strategy_base import StrategyBase
import pandas as pd

class EMACrossoverDailyTargetStrategy(StrategyBase):
    """Simple EMA crossover strategy with fixed profit target/stop loss per trade.
    Trades until a daily profit target is reached."""
    def __init__(self, params=None):
        super().__init__(params)
        p = params or {}
        self.fast_period = int(p.get('fast_period', 5))
        self.slow_period = int(p.get('slow_period', 20))
        self.target = float(p.get('target', 10))
        self.stop = float(p.get('stop', 10))

    def indicator_config(self):
        return [
            {"column": "ema_fast", "label": f"EMA{self.fast_period}", "plot": True, "panel": 1, "color": "green"},
            {"column": "ema_slow", "label": f"EMA{self.slow_period}", "plot": True, "panel": 1, "color": "red"},
        ]

    def generate_signals(self, data):
        df = data.copy()
        df['ema_fast'] = df['close'].ewm(span=self.fast_period, adjust=False).mean()
        df['ema_slow'] = df['close'].ewm(span=self.slow_period, adjust=False).mean()
        df['signal'] = 0
        cross_up = (df['ema_fast'].shift(1) <= df['ema_slow'].shift(1)) & (df['ema_fast'] > df['ema_slow'])
        cross_down = (df['ema_fast'].shift(1) >= df['ema_slow'].shift(1)) & (df['ema_fast'] < df['ema_slow'])
        df.loc[cross_up, 'signal'] = 1
        df.loc[cross_down, 'signal'] = -1
        return df

    def should_exit(self, position, row, entry_price):
        price = row.close
        if position == 'long':
            if price >= entry_price + self.target:
                return True, 'Target'
            if price <= entry_price - self.stop:
                return True, 'Stop Loss'
            if row.ema_fast < row.ema_slow:
                return True, 'Cross Down Exit'
        elif position == 'short':
            if price <= entry_price - self.target:
                return True, 'Target'
            if price >= entry_price + self.stop:
                return True, 'Stop Loss'
            if row.ema_fast > row.ema_slow:
                return True, 'Cross Up Exit'
        return False, ''

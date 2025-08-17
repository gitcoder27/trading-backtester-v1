"""EMA crossover strategy with daily profit target."""

import pandas as pd
from backtester.strategy_base import StrategyBase


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

    @staticmethod
    def get_params_config():
        return [
            {
                "name": "ema_cross_fast_period",
                "param_key": "fast_period",
                "type": "number_input",
                "label": "Fast EMA Period",
                "default": 5,
                "min": 1,
                "max": 200,
                "step": 1,
            },
            {
                "name": "ema_cross_slow_period",
                "param_key": "slow_period",
                "type": "number_input",
                "label": "Slow EMA Period",
                "default": 20,
                "min": 1,
                "max": 400,
                "step": 1,
            },
            {
                "name": "ema_cross_target",
                "param_key": "target",
                "type": "number_input",
                "label": "Profit Target (pts)",
                "default": 10,
                "min": 1,
                "max": 400,
                "step": 1,
            },
            {
                "name": "ema_cross_stop",
                "param_key": "stop",
                "type": "number_input",
                "label": "Stop Loss (pts)",
                "default": 10,
                "min": 1,
                "max": 400,
                "step": 1,
            },
        ]

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
